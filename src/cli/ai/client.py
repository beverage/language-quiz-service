"""Client for OpenAI."""

import openai

from src.core.config import settings


class AsyncChatGPTClient:
    """Async client for ChatGPT."""

    def __init__(self, api_key: str = None):
        self.client = openai.AsyncOpenAI(api_key=api_key or settings.openai_api_key)

    async def handle_request(self, prompt: str) -> str:
        """Handle a request to ChatGPT."""
        completion = await self.client.chat.completions.create(
            model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
