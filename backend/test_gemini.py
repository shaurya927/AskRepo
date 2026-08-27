import asyncio
from app.services.ai.gateway import GeminiProvider
import os

async def test():
    key = os.getenv("GEMINI_API_KEY")
    provider = GeminiProvider(api_key=key)
    try:
        res = await provider.generate("hello", "you are a bot")
        print("Success:", res)
    except Exception as e:
        print("Exception:", type(e).__name__, str(e))

asyncio.run(test())
