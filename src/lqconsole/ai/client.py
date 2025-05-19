from os import environ

import traceback
import logging
import backoff
import openai

logging.getLogger("backoff").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

class AsyncChatGPTClient:

    def __init__(self, model: str="gpt-4o", role: str="user", api_key: str=None):
        self.api_key = environ.get("OPENAI_API_KEY") if api_key is None else api_key
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
        self.role = role

    @backoff.on_exception(backoff.expo, openai.RateLimitError)
    async def completions_with_backoff(self, **kwargs):
        return await self.client.chat.completions.create(**kwargs) # pylint: disable=broad-exception-caught disable=missing-kwoa

    async def generate_response(self, prompt: str):
        try:
            if hasattr(self, 'api_key') is False:
                raise ValueError("Missing API key.")

            completion = await self.completions_with_backoff(
                model = self.model,
                messages = [{ "role": self.role, "content": prompt }])

            if completion.choices and len(completion.choices) > 0:
                return completion.choices[0].message.content

            raise openai.APIStatusError(message="No completion choices found.", response=None, body=None)
        except Exception as e: # pylint: disable=broad-exception-caught
            return f"str({e}): {traceback.format_exc()}"

    async def handle_request(self, prompt: str):
        return await self.generate_response(prompt)
