#!/usr/bin/env python3
"""
LLM client for the generative game engine.

Provider-agnostic: talks to a local Ollama server OR any OpenAI-compatible
chat-completions API (Groq, OpenAI, Together, ...). Single place for endpoint
handling, streaming, retries and in-fiction fallbacks so the game never
surfaces raw errors to the player.

Configured via environment (see resolve_llm_config): a local dev machine keeps
using Ollama unchanged; production points at a hosted API by setting
LLM_PROVIDER=openai + LLM_BASE_URL + LLM_API_KEY + LLM_MODEL.
"""

import json
import logging
import os
import time
from typing import Callable, Dict, List, Optional

import threading
import requests

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Backend pool — spreads load across multiple LLM endpoints (e.g. a CUDA box
# + the Mac) with least-busy routing and brief failover. Set LLM_ENDPOINTS to
# a comma-separated list to enable; otherwise it's a single-endpoint no-op.
#   LLM_ENDPOINTS=http://192.168.1.50:11434,http://127.0.0.1:11434
#   LLM_MAX_PARALLEL=2   (concurrent calls allowed per endpoint)
# ---------------------------------------------------------------------------
_POOL_LOCK = threading.Lock()
_POOL = None


def _build_pool() -> list:
    cfg = resolve_llm_config()
    raw = os.environ.get("LLM_ENDPOINTS", "").strip()
    default_parallel = "2" if cfg["provider"] == "ollama" else "32"
    max_parallel = int(os.environ.get("LLM_MAX_PARALLEL", default_parallel))
    entries = ([e.strip() for e in raw.split(",") if e.strip()]
               if raw else [cfg["base_url"]])
    pool = []
    for entry in entries:
        # "url@model" lets each backend run a different model (calibrate the
        # fast box vs the slow one); bare "url" uses the global LLM_MODEL.
        if "@" in entry.split("//", 1)[-1]:
            url, _, model = entry.rpartition("@")
        else:
            url, model = entry, None
        pool.append({"url": url.strip().rstrip("/"), "model": model or None,
                     "inflight": 0, "max": max_parallel, "down_until": 0.0})
    return pool


def _pool() -> list:
    global _POOL
    if _POOL is None:
        _POOL = _build_pool()
    return _POOL


def _acquire_endpoint(exclude=None):
    """Pick the least-busy healthy endpoint and mark one call in-flight."""
    now = time.time()
    with _POOL_LOCK:
        pool = _pool()
        candidates = [e for e in pool
                      if e["down_until"] <= now and e["url"] != exclude] or \
                     [e for e in pool if e["url"] != exclude] or pool
        ep = min(candidates, key=lambda e: e["inflight"])
        ep["inflight"] += 1
        return ep


def _release_endpoint(ep, ok: bool):
    with _POOL_LOCK:
        ep["inflight"] = max(0, ep["inflight"] - 1)
        if not ok:
            ep["down_until"] = time.time() + 30  # brief cooldown on failure


def resolve_llm_config() -> Dict:
    """Read LLM settings from the environment, defaulting to local Ollama."""
    provider = os.environ.get("LLM_PROVIDER", "ollama").lower()
    if provider in ("openai", "groq"):
        return {
            "provider": "openai",
            "base_url": os.environ.get("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
            "api_key": os.environ.get("LLM_API_KEY", ""),
            "model": os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile"),
        }
    return {
        "provider": "ollama",
        "base_url": os.environ.get("LLM_BASE_URL",
                                   os.environ.get("OLLAMA_ENDPOINT", "http://localhost:11434")),
        "api_key": "",
        "model": os.environ.get("LLM_MODEL", "mistral"),
    }


class LLMClient:
    """
    Unified chat client. `provider` is "ollama" or "openai".

    All calls retry once on failure and degrade to an in-fiction fallback
    string rather than raising to the player.
    """

    NETWORK_FALLBACK = (
        "The world around you seems to pause. You take a moment to "
        "collect yourself and continue your investigation."
    )
    GENERIC_FALLBACK = "Something feels wrong. You steady yourself and push forward."
    EMPTY_FALLBACK = "You pause, thinking..."

    def __init__(self, endpoint: str = None, model: str = None, timeout: int = 120,
                 provider: str = None, api_key: str = None):
        cfg = resolve_llm_config()
        self.provider = provider or cfg["provider"]
        self.endpoint = (endpoint or cfg["base_url"]).rstrip("/")
        self.model = model or cfg["model"]
        self.api_key = api_key if api_key is not None else cfg["api_key"]
        self.timeout = timeout

    # -- shared helpers -----------------------------------------------------

    def _headers(self) -> Dict:
        h = {"Content-Type": "application/json"}
        if self.provider == "openai" and self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def _url(self, ollama_path: str, openai_path: str) -> str:
        return self.endpoint + (openai_path if self.provider == "openai" else ollama_path)

    # -- streaming chat -----------------------------------------------------

    def chat(
        self,
        messages: List[Dict],
        system_prompt: Optional[str] = None,
        max_tokens: int = 400,
        temperature: float = 0.5,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Streaming chat. Returns full text, or an in-fiction fallback."""
        msgs = list(messages)
        if system_prompt:
            if self.provider == "openai":
                msgs = [{"role": "system", "content": system_prompt}] + msgs
            # ollama takes system as a top-level field (added to payload below)

        if self.provider == "openai":
            payload = {
                "model": self.model, "messages": msgs, "stream": True,
                "temperature": temperature, "max_tokens": max_tokens,
            }
        else:
            payload = {
                "model": self.model, "messages": msgs, "stream": True,
                "keep_alive": "30m",
                "options": {
                    "temperature": temperature, "num_predict": max_tokens,
                    "repeat_penalty": 1.18, "repeat_last_n": 256,
                },
            }
            if system_prompt:
                payload["system"] = system_prompt

        path = "/chat/completions" if self.provider == "openai" else "/api/chat"
        tried = None
        attempts = max(2, len(_pool()))
        for attempt in range(attempts):
            ep = _acquire_endpoint(exclude=tried if attempt else None)
            payload["model"] = ep.get("model") or self.model
            try:
                response = requests.post(ep["url"] + path, json=payload,
                                         headers=self._headers(),
                                         timeout=self.timeout, stream=True)
                response.raise_for_status()
                full = self._consume_stream(response, on_chunk)
                _release_endpoint(ep, True)
                return full.strip() if full.strip() else self.EMPTY_FALLBACK
            except (requests.Timeout, requests.ConnectionError):
                _release_endpoint(ep, False)
                tried = ep["url"]
                logger.warning("LLM chat network error on %s (attempt %d)", ep["url"], attempt)
                if attempt < attempts - 1:
                    continue
                return self.NETWORK_FALLBACK
            except Exception:
                _release_endpoint(ep, False)
                tried = ep["url"]
                logger.warning("LLM chat unexpected error on %s (attempt %d)", ep["url"], attempt, exc_info=True)
                if attempt < attempts - 1:
                    continue
                return self.GENERIC_FALLBACK
        return self.EMPTY_FALLBACK

    def _consume_stream(self, response, on_chunk) -> str:
        """Parse a streamed response for either provider into full text."""
        full = ""
        for line in response.iter_lines():
            if not line:
                continue
            if self.provider == "openai":
                # SSE: lines like "data: {json}" ending with "data: [DONE]"
                if isinstance(line, bytes):
                    line = line.decode("utf-8", "ignore")
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                    text = (obj.get("choices") or [{}])[0].get("delta", {}).get("content", "") or ""
                except json.JSONDecodeError:
                    continue
            else:
                try:
                    obj = json.loads(line)
                    text = obj.get("message", {}).get("content", "")
                except json.JSONDecodeError:
                    continue
            if text:
                full += text
                if on_chunk:
                    on_chunk(text)
        return full

    # -- non-streaming tool calls ------------------------------------------

    def chat_with_tools(
        self,
        messages: List[Dict],
        tools: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 400,
    ) -> Dict:
        """Non-streaming tool-calling call. Falls back to tag parsing on error."""
        if self.provider == "openai":
            payload = {
                "model": self.model, "messages": messages, "tools": tools,
                "stream": False, "temperature": temperature, "max_tokens": max_tokens,
            }
        else:
            payload = {
                "model": self.model, "messages": messages, "tools": tools,
                "stream": False, "keep_alive": "30m",
                "options": {"temperature": temperature, "num_predict": max_tokens},
            }
        path = "/chat/completions" if self.provider == "openai" else "/api/chat"
        tried = None
        attempts = max(2, len(_pool()))
        for attempt in range(attempts):
            ep = _acquire_endpoint(exclude=tried if attempt else None)
            payload["model"] = ep.get("model") or self.model
            try:
                response = requests.post(ep["url"] + path, json=payload,
                                         headers=self._headers(), timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                if self.provider == "openai":
                    msg = (data.get("choices") or [{}])[0].get("message", {})
                else:
                    msg = data.get("message", {})
                _release_endpoint(ep, True)
                return {"narrative": msg.get("content", "") or "",
                        "tool_calls": msg.get("tool_calls", []) or []}
            except (requests.Timeout, requests.ConnectionError):
                _release_endpoint(ep, False)
                tried = ep["url"]
                if attempt < attempts - 1:
                    continue
                break
            except Exception:
                _release_endpoint(ep, False)
                tried = ep["url"]
                logger.warning("LLM tool-call error on %s", ep["url"], exc_info=True)
                if attempt < attempts - 1:
                    continue
                break
        return {"narrative": "", "tool_calls": [], "fallback": True}


# Back-compat: the engine imports OllamaClient. It now resolves the provider
# from the environment, so the name is historical.
OllamaClient = LLMClient
