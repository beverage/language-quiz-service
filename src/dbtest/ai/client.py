from os import environ

import traceback
import openai

client = openai.AsyncOpenAI(api_key=environ.get("OPENAI_API_KEY"))

class AsyncChatGPTClient:
    def __init__(self, model: str="gpt-3.5-turbo", role: str="user"):
        self.model = model
        self.role = role

    async def generate_response(self, prompt: str):
        try:
            completion = await client.chat.completions.create(model = self.model,
            messages = [
                { "role": self.role, "content": prompt },
            ])

            if completion.choices and len(completion.choices) > 0:
                return completion.choices[0].message.content

            raise openai.APIStatusError(message="No completion choices found.", response=None, body=None)
        except Exception as e:
            return f"str({e}): {traceback.format_exc()}"

    async def handle_request(self, prompt: str):
        return await self.generate_response(prompt)
