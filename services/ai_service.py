import asyncio
import os

import aiohttp
from aiolimiter import AsyncLimiter

from config import pricing

DEFAULT_MAX_TOKENS = 256
DEFAULT_TEMPERATURE = 0.7


class AIService:
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        self.limiter = AsyncLimiter(3000, 60)

    def compute_cost(self, base_model, prompt_tokens, completion_tokens):
        prompt_price_per_1k = pricing[base_model]["prompt_tokens"]
        completion_price_per_1k = pricing[base_model]["completion_tokens"]

        cost = (prompt_price_per_1k * prompt_tokens / 1000) + (
            completion_price_per_1k * completion_tokens / 1000
        )
        return cost

    async def generate_chat_completion(self, system_message, prompt, model, **kwargs):
        kwargs["max_tokens"] = kwargs.get("max_tokens", DEFAULT_MAX_TOKENS)
        kwargs["temperature"] = kwargs.get("temperature", DEFAULT_TEMPERATURE)
        await self.limiter.acquire()
        return await self.__generate_chat_completion(system_message, prompt, model, **kwargs)

    async def __generate_chat_completion(
        self,
        system_message: str,
        prompt: str,
        model: str,
        **kwargs,
    ) -> tuple[str, float]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            **kwargs,
        }

        url = "https://api.openai.com/v1/chat/completions"

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 429:
                    await asyncio.sleep(2)
                    return await self.__generate_chat_completion(
                        system_message, prompt, model, **kwargs
                    )

                response_data = await response.json()

        completion = response_data["choices"][0]["message"]["content"].strip()  # type: ignore

        prompt_tokens = response_data["usage"]["prompt_tokens"]  # type: ignore
        completion_tokens = response_data["usage"]["completion_tokens"]  # type: ignore

        cost = self.compute_cost(model, prompt_tokens, completion_tokens)

        return completion, cost
