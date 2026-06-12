#!/usr/bin/env python3
"""
Ollama LLM client for the generative game engine.
Single place for endpoint handling, streaming, retries and fallbacks.
"""

import json
import time
from typing import Callable, Dict, List, Optional

import requests


class OllamaClient:
    """
    Thin client around the Ollama /api/chat endpoint.

    All calls retry once on failure. Narrative calls degrade to an
    in-fiction fallback string so the game never surfaces raw errors
    to the player.
    """

    # In-fiction fallbacks when Ollama is unreachable or errors out
    NETWORK_FALLBACK = (
        "The world around you seems to pause. You take a moment to "
        "collect yourself and continue your investigation."
    )
    GENERIC_FALLBACK = "Something feels wrong. You steady yourself and push forward."
    EMPTY_FALLBACK = "You pause, thinking..."

    def __init__(self, endpoint: str = "http://localhost:11434",
                 model: str = "mistral", timeout: int = 120):
        self.endpoint = endpoint
        self.model = model
        self.timeout = timeout

    def chat(
        self,
        messages: List[Dict],
        system_prompt: Optional[str] = None,
        max_tokens: int = 200,
        temperature: float = 0.5,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> str:
        """
        Streaming chat call. Returns the full narrative text, or an
        in-fiction fallback string if Ollama is unavailable.

        Args:
            messages: Chat history (role/content dicts)
            system_prompt: Optional system prompt
            max_tokens: num_predict for the model
            temperature: Sampling temperature
            on_chunk: Optional callback receiving streamed text chunks
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "temperature": temperature,
            "num_predict": max_tokens,
        }
        if system_prompt:
            payload["system"] = system_prompt

        for attempt in range(2):
            try:
                response = requests.post(
                    f"{self.endpoint}/api/chat",
                    json=payload,
                    timeout=self.timeout,
                    stream=True,
                )
                response.raise_for_status()

                full_response = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            text = chunk.get("message", {}).get("content", "")
                            full_response += text
                            if on_chunk and text:
                                on_chunk(text)
                        except json.JSONDecodeError:
                            continue

                return full_response.strip() if full_response.strip() else self.EMPTY_FALLBACK

            except (requests.Timeout, requests.ConnectionError):
                if attempt == 0:
                    time.sleep(0.5)
                    continue
                return self.NETWORK_FALLBACK
            except Exception:
                if attempt == 0:
                    continue
                return self.GENERIC_FALLBACK

        return self.EMPTY_FALLBACK

    def chat_with_tools(
        self,
        messages: List[Dict],
        tools: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 300,
    ) -> Dict:
        """
        Non-streaming chat call with tool calling support.

        Returns:
            Dict with "narrative" and "tool_calls" keys, or
            {"narrative": "", "tool_calls": [], "fallback": True} on failure
            so the caller can fall back to tag-based parsing.
        """
        for attempt in range(2):
            try:
                response = requests.post(
                    f"{self.endpoint}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "tools": tools,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                        },
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()
                message = data.get("message", {})

                return {
                    "narrative": message.get("content", ""),
                    "tool_calls": message.get("tool_calls", []),
                }
            except (requests.Timeout, requests.ConnectionError):
                if attempt == 0:
                    time.sleep(0.5)
                    continue
                break
            except Exception:
                if attempt == 0:
                    continue
                break

        # Caller falls back to the tag-based system
        return {"narrative": "", "tool_calls": [], "fallback": True}
