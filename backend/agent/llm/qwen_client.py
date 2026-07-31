"""
Qwen LLM client via Alibaba Cloud (OpenAI-compatible interface).

Supports:
- Configurable Base URL (token-plan / standard DashScope / any OpenAI-compatible endpoint)
- Automatic fallback to secondary LLM provider when primary fails
- Chat completion with function calling / tool use
- Streaming chat
"""
import logging
from typing import Optional
from openai import AsyncOpenAI

from backend.config import settings

logger = logging.getLogger(__name__)


class QwenClient:
    """
    LLM client with primary + fallback support.

    Primary:   Configured via LLM_BASE_URL + DASHSCOPE_API_KEY + QWEN_MODEL
    Fallback:  Configured via LLM_FALLBACK_* (optional, auto-switch on failure)
    """

    def __init__(self):
        # Primary client
        self.client = AsyncOpenAI(
            api_key=settings.DASHSCOPE_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
        self.model = settings.QWEN_MODEL

        # Fallback client (optional)
        self._fallback_client: AsyncOpenAI | None = None
        self._fallback_model: str = ""
        if (
            settings.LLM_FALLBACK_ENABLED
            and settings.LLM_FALLBACK_API_KEY
            and settings.LLM_FALLBACK_BASE_URL
        ):
            self._fallback_client = AsyncOpenAI(
                api_key=settings.LLM_FALLBACK_API_KEY,
                base_url=settings.LLM_FALLBACK_BASE_URL,
            )
            self._fallback_model = settings.LLM_FALLBACK_MODEL or "sensenova-6.7-flash-lite"
            logger.info(
                "LLM fallback enabled: primary=%s @ %s, fallback=%s @ %s",
                self.model, settings.LLM_BASE_URL,
                self._fallback_model, settings.LLM_FALLBACK_BASE_URL,
            )

    async def chat(self, messages: list[dict], tools: Optional[list[dict]] = None,
                   temperature: Optional[float] = None) -> dict:
        """
        Send chat completion request. Tries primary first, falls back on failure.

        Args:
            messages: OpenAI-format message list
            tools: Optional list of tool definitions (OpenAI function format)
            temperature: Override default temperature

        Returns:
            Raw response object from the API
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or settings.AGENT_TEMPERATURE,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        # Try primary
        try:
            response = await self.client.chat.completions.create(**kwargs)
            return response
        except Exception as primary_err:
            logger.warning("Primary LLM call failed: %s", primary_err)

            # Try fallback
            if self._fallback_client:
                logger.info("Falling back to secondary LLM: %s", self._fallback_model)
                fallback_kwargs = {
                    "model": self._fallback_model,
                    "messages": messages,
                    "temperature": temperature or settings.AGENT_TEMPERATURE,
                }
                if tools:
                    fallback_kwargs["tools"] = tools
                    fallback_kwargs["tool_choice"] = "auto"
                try:
                    response = await self._fallback_client.chat.completions.create(**fallback_kwargs)
                    return response
                except Exception as fallback_err:
                    logger.error("Fallback LLM also failed: %s", fallback_err)
                    raise
            else:
                raise

    async def chat_stream(self, messages: list[dict], tools: Optional[list[dict]] = None,
                          temperature: Optional[float] = None):
        """Streaming version of chat for real-time output. Falls back on initial error."""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or settings.AGENT_TEMPERATURE,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        # Try primary
        try:
            async for chunk in await self.client.chat.completions.create(**kwargs):
                yield chunk
        except Exception as primary_err:
            logger.warning("Primary LLM stream failed: %s", primary_err)

            # Try fallback
            if self._fallback_client:
                logger.info("Falling back to secondary LLM (stream): %s", self._fallback_model)
                fallback_kwargs = {
                    "model": self._fallback_model,
                    "messages": messages,
                    "temperature": temperature or settings.AGENT_TEMPERATURE,
                    "stream": True,
                }
                if tools:
                    fallback_kwargs["tools"] = tools
                    fallback_kwargs["tool_choice"] = "auto"
                async for chunk in await self._fallback_client.chat.completions.create(**fallback_kwargs):
                    yield chunk
            else:
                raise
