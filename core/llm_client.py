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
    # These keep a turn playable when the model hiccups. They are also how a
    # dead configuration hides: a retired model name returns 404, the engine
    # swallows it, and every turn comes back as the same canned sentence with
    # HTTP 200. That is exactly what happened in production — the deployed
    # LLM_MODEL had been retired by the provider and nobody noticed, because
    # /api/health never calls the model. So the fallbacks now keep a counter,
    # and /api/health reports it.
    GENERIC_FALLBACK = "Something feels wrong. You steady yourself and push forward."
    EMPTY_FALLBACK = "You pause, thinking..."

    # Process-wide, deliberately: it answers "is the model answering at all",
    # which is not a per-session question.
    degraded_turns = 0
    last_error = None

    @classmethod
    def _degrade(cls, why: str, fallback: str) -> str:
        cls.degraded_turns += 1
        cls.last_error = why
        logger.error("LLM degraded turn (%s): %s", cls.degraded_turns, why)
        return fallback

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
            payload.update(self._reasoning_options())
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
                if full.strip():
                    return full.strip()
                return self._degrade('empty completion', self.EMPTY_FALLBACK)
            except (requests.Timeout, requests.ConnectionError):
                _release_endpoint(ep, False)
                tried = ep["url"]
                logger.warning("LLM chat network error on %s (attempt %d)", ep["url"], attempt)
                if attempt < attempts - 1:
                    continue
                return self.NETWORK_FALLBACK
            except Exception as exc:
                _release_endpoint(ep, False)
                tried = ep["url"]
                logger.warning("LLM chat unexpected error on %s (attempt %d)", ep["url"], attempt, exc_info=True)
                if attempt < attempts - 1:
                    continue
                return self._degrade(str(exc)[:200], self.GENERIC_FALLBACK)
        return self._degrade('all endpoints failed', self.EMPTY_FALLBACK)

    # Reasoning models spend the completion budget thinking before they write.
    # Measured on Groq with gpt-oss-120b and this game's ~2000-token system
    # prompt: at the engine's 150-token cap the model produced 664 characters
    # of reasoning and ZERO characters of narration, so every turn degraded to
    # the in-fiction fallback and the game had no Keeper. Asking for low effort
    # yields the same narration in 48 completion tokens instead of 281.
    #
    # Sent only to models known to accept it; other providers reject unknown
    # fields outright.
    REASONING_MODELS = ("gpt-oss", "o1", "o3", "o4", "qwen3", "deepseek-r")

    def _reasoning_options(self) -> dict:
        model = (self.model or "").lower()
        if any(tag in model for tag in self.REASONING_MODELS):
            return {"reasoning_effort": "low"}
        return {}

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
            payload.update(self._reasoning_options())
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
