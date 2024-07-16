from os import environ

import traceback
import logging
import backoff
import openai

client = openai.AsyncOpenAI(api_key=environ.get("OPENAI_API_KEY"))

logging.getLogger("backoff").setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

class AsyncChatGPTClient:
    def __init__(self, model: str="gpt-3.5-turbo", role: str="user"):
        self.model = model
        self.role = role

    @backoff.on_exception(backoff.expo, openai.RateLimitError)
    async def completions_with_backoff(self, **kwargs):
        return await client.chat.completions.create(**kwargs) # pylint: disable=broad-exception-caught disable=missing-kwoa

    async def generate_response(self, prompt: str):
        try:
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
