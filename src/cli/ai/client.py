"""Client for OpenAI."""
import openai

# Use new core configuration
import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from core.config import settings


class AsyncChatGPTClient:
    """Async client for ChatGPT."""
    
    def __init__(self, api_key: str = None):
        self.client = openai.AsyncOpenAI(api_key=api_key or settings.openai_api_key)

    async def handle_request(self, prompt: str) -> str:
        """Handle a request to ChatGPT."""
        completion = await self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
