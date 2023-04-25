import aiohttp
import openai
import requests

from config import config, pricing


class AIService:

    def __init__(self):
        self.api_key = config["openai_api_key"]

    def compute_cost(self, base_model, n_tokens):
        
        price_per_1k_tokens = pricing[base_model]
        cost = price_per_1k_tokens * n_tokens / 1000
        return cost
        

    
    async def generate_chat_completion(self, system_message : str, 
                            prompt : str, 
                            model : str = "gpt-3.5-turbo",
                            max_tokens : int = 256, 
                            temperature : float = 0.7) -> tuple[str, float]:

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        url = "https://api.openai.com/v1/chat/completions"

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status != 200:
                    raise Exception(f"OpenAI API returned status code {response.status}")
                response_data = await response.json()   
                      
        completion = response_data["choices"][0]["message"]["content"].strip() # type: ignore

        n_tokens = response_data["usage"]["total_tokens"] # type: ignore

        cost = self.compute_cost(model, n_tokens)

        return completion, cost
        


