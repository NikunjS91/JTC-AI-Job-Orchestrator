from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
print(f"Testing Groq API with key: {api_key[:10]}...")

try:
    client = Groq(api_key=api_key)
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Say 'Hello, Groq works!' if you can read this."}],
        temperature=0.1,
        max_tokens=50
    )
    
    print(f"\n✅ SUCCESS!")
    print(f"Response: {response.choices[0].message.content}")
    print(f"\nGroq API is working correctly!")
    
except Exception as e:
    print(f"\n❌ FAILED!")
    print(f"Error: {e}")
    print(f"\nThis might be:")
    print("1. Invalid API key")
    print("2. Network/firewall blocking Groq")
    print("3. Groq service is down")
