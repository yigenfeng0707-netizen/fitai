"""
Qwen LLM client via Alibaba Cloud DashScope (OpenAI-compatible interface).

Supports chat completion with function calling / tool use.
"""
import logging
from typing import Optional
from openai import AsyncOpenAI

from backend.config import settings

logger = logging.getLogger(__name__)


class QwenClient:
    """Qwen LLM client via DashScope compatible mode."""

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.DASHSCOPE_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.model = settings.QWEN_MODEL

    async def chat(self, messages: list[dict], tools: Optional[list[dict]] = None,
                   temperature: Optional[float] = None) -> dict:
        """
        Send chat completion request to Qwen.

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

        try:
            response = await self.client.chat.completions.create(**kwargs)
            return response
        except Exception as e:
            logger.exception("Qwen API call failed")
            raise

    async def chat_stream(self, messages: list[dict], tools: Optional[list[dict]] = None,
                          temperature: Optional[float] = None):
        """Streaming version of chat for real-time output."""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or settings.AGENT_TEMPERATURE,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        async for chunk in await self.client.chat.completions.create(**kwargs):
            yield chunk
