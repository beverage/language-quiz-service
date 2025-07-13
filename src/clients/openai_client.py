from openai import AsyncOpenAI
from src.core.config import settings


class OpenAIClient:
    """Async client for OpenAI."""

    def __init__(self, api_key: str = None):
        self.client = AsyncOpenAI(api_key=api_key or settings.openai_api_key)

    async def handle_request(self, prompt: str) -> str:
        """Send a chat completion request to OpenAI and return the content string."""
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        raw_content = response.choices[0].message.content
        return self._clean_response(raw_content)

    def _clean_response(self, raw_content: str) -> str:
        """Clean LLM response by removing markdown code blocks."""
        if not raw_content:
            return raw_content

        cleaned = raw_content.strip()

        # Remove markdown code blocks if present
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]  # Remove ```json
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]  # Remove ```

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]  # Remove ```

        return cleaned.strip()
