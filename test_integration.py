import sys
import os
import logging

# Add project root to path
sys.path.append(os.getcwd())

from libs.core.llm_client import LLMClient
from libs.core.logger import configure_logger

# Configure logging to see what's happening
logger = configure_logger("test_integration")
logging.getLogger("llm_client").setLevel(logging.INFO)

def test_auto_fallback():
    print("\n--- Testing Auto Fallback ---")
    try:
        # Initialize client (should pick up LLM_PROVIDER=auto from .env)
        client = LLMClient()
        
        # Check which providers were loaded
        providers = [name for name, _ in client.providers]
        print(f"Loaded providers: {providers}")
        
        if "OpenAI" in providers:
            print("WARNING: OpenAI provider loaded (unexpected if key is missing)")
        if "Groq" in providers:
            print("SUCCESS: Groq provider loaded")
        if "Gemini" in providers:
            print("SUCCESS: Gemini provider loaded")
            
        if not providers:
            print("FAILURE: No providers loaded!")
            return

        # Test classification
        email_content = """
        Hi John,
        
        We'd like to schedule an interview with you for the Senior Developer position at TechCorp.
        Are you available next Tuesday at 2 PM EST?
        
        Best,
        Recruiting Team
        """
        
        print("\nClassifying test email...")
        result = client.classify_email(email_content)
        print(f"Result: {result}")
        
        if result and "INTERVIEW" in result:
            print("\n✅ Classification SUCCESS")
        else:
            print("\n❌ Classification FAILED or Unexpected Result")

    except Exception as e:
        print(f"\n❌ Test FAILED with error: {e}")

if __name__ == "__main__":
    test_auto_fallback()
