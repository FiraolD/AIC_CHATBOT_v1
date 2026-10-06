import os
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

async def test_connection():
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ No API key found! Check your .env file location and format.")
        return
    
    print(f"✅ API key found (first 8 chars): {api_key[:8]}...")
    
    try:
        client = AsyncOpenAI(api_key=api_key)
        
        # Test the connection
        response = await client.models.list()
        print("✅ Successfully connected to OpenAI!")
        print(f"Available models: {[model.id for model in response.data[:5]]}")
        
        # Test chat completion
        chat_response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        print(f"💬 Test response: {chat_response.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())