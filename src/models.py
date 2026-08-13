import os
import json
import asyncio
import time
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

DEEPINFRA_API_KEY = os.environ.get("DEEPINFRA_API_KEY")

client = AsyncOpenAI(
    api_key=DEEPINFRA_API_KEY,
    base_url="https://api.deepinfra.com/v1/openai"
)

# Models dictionary maps our short names to the DeepInfra model IDs
MODELS = {
    "qwen": "Qwen/Qwen2.5-72B-Instruct",
    "deepseek": "deepseek-ai/DeepSeek-V3",
    "llama": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "mistral": "mistralai/Mistral-Nemo-Instruct-2407"
}

async def generate_response(model_name: str, messages: list, temperature: float = 0.0, max_tokens: int = 1000, response_format=None, retries: int = 2):
    model_id = MODELS.get(model_name, model_name)
    
    for attempt in range(retries + 1):
        try:
            kwargs = {
                "model": model_id,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if response_format:
                kwargs["response_format"] = {"type": response_format}
                
            start_time = time.perf_counter()
            response = await client.chat.completions.create(**kwargs)
            latency = time.perf_counter() - start_time
            
            # Extract tokens safely
            prompt_tokens = response.usage.prompt_tokens if hasattr(response, 'usage') and hasattr(response.usage, 'prompt_tokens') else None
            completion_tokens = response.usage.completion_tokens if hasattr(response, 'usage') and hasattr(response.usage, 'completion_tokens') else None
            
            return {
                "content": response.choices[0].message.content,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "latency": latency
            }
        except Exception as e:
            if attempt == retries:
                print(f"Failed after {retries} retries for model {model_name}. Error: {e}")
                return None
            print(f"Attempt {attempt+1} failed for {model_name}, retrying... Error: {e}")
            await asyncio.sleep(2 ** attempt) # Exponential backoff
