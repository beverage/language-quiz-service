import openai
from core.config import settings


class OpenAIClient:
    """Async client for OpenAI."""

    def __init__(self, api_key: str = None):
        self.client = openai.AsyncOpenAI(api_key=api_key or settings.openai_api_key)

    async def handle_request(self, prompt: str) -> str:
        """Send a chat completion request to OpenAI and return the content string."""
        response = await self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
