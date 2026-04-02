import json
import google.generativeai as genai
from groq import Groq
from openai import OpenAI
from libs.core.config import BaseConfig, get_config
from libs.core.logger import configure_logger

logger = configure_logger("llm_client")

class LLMConfig(BaseConfig):
    SERVICE_NAME: str = "classifier"
    GOOGLE_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    LLM_PROVIDER: str = "openai"  # "openai", "groq", "gemini", or "auto"

config = get_config(LLMConfig)

# Abstract Base Class
class LLMProvider:
    def classify(self, email_content: str) -> str:
        raise NotImplementedError
    
    def generate(self, prompt: str) -> str:
        raise NotImplementedError

# OpenAI Provider (Primary - Most Reliable)
class OpenAIProvider(LLMProvider):
    def __init__(self):
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"  # Fast, cheap, reliable
        logger.info(f"OpenAI Provider initialized with model: {self.model}")
    
    def classify(self, email_content: str) -> str:
        prompt = f"""Analyze the following email snippet and determine if it is a career-related event.
Return ONLY a JSON object with:
- event_type: "INTERVIEW", "OFFER", "REJECTION", or "OTHER"
- company: Company name (if applicable)
- confidence: 0.0 to 1.0
- summary: Brief summary

Email Snippet:
{email_content}
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI inference failed: {e}")
            raise

    def generate(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise

# Groq Provider (Fast & High Quota, but Cloudflare issues in Docker)
class GroqProvider(LLMProvider):
    def __init__(self):
        if not config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required")
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.model = "llama3-70b-8192"  # Standard stable model
        logger.info(f"Groq Provider initialized with model: {self.model}")
    
    def classify(self, email_content: str) -> str:
        prompt = f"""Analyze the following email snippet and determine if it is a career-related event.
Return ONLY a JSON object with:
- event_type: "INTERVIEW", "OFFER", "REJECTION", or "OTHER"
- company: Company name (if applicable)
- confidence: 0.0 to 1.0
- summary: Brief summary

Email Snippet:
{email_content}
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq inference failed: {e}")
            raise

    def generate(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq generation failed: {e}")
            raise

# Gemini Provider (Fallback - Quota Limited but supports multi-key rotation)
class GeminiProvider(LLMProvider):
    def __init__(self):
        # Support comma-separated keys: KEY1,KEY2,KEY3
        if not config.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is required")
        
        self.api_keys = [k.strip() for k in config.GOOGLE_API_KEY.split(',') if k.strip()]
        self.current_key_index = 0
        
        logger.info(f"Gemini Provider initialized with {len(self.api_keys)} API key(s)")
        
        # Initialize with first key
        genai.configure(api_key=self.api_keys[0])
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def _rotate_key(self):
        """Rotate to next API key on quota exhaustion"""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        new_key = self.api_keys[self.current_key_index]
        genai.configure(api_key=new_key)
        logger.info(f"Rotated to API key #{self.current_key_index + 1}/{len(self.api_keys)}")
    
    def classify(self, email_content: str) -> str:
        prompt = f"""Analyze the following email snippet and determine if it is a career-related event.
Return a JSON object with:
- event_type: "INTERVIEW", "OFFER", "REJECTION", or "OTHER"
- company: Company name (if applicable)
- confidence: 0.0 to 1.0
- summary: Brief summary

Email Snippet:
{email_content}
"""
        return self.generate(prompt, json_mode=True)

    def generate(self, prompt: str, json_mode: bool = False) -> str:
        # Try all keys before giving up
        attempts = 0
        max_attempts = len(self.api_keys)
        
        generation_config = {"response_mime_type": "application/json"} if json_mode else {}

        while attempts < max_attempts:
            try:
                response = self.model.generate_content(
                    prompt, 
                    generation_config=generation_config
                )
                return response.text
            except Exception as e:
                error_str = str(e)
                # Check if quota exceeded or rate limit
                if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                    attempts += 1
                    if attempts < max_attempts:
                        logger.warning(f"Quota exceeded on key #{self.current_key_index + 1}, rotating...")
                        self._rotate_key()
                        continue
                    else:
                        logger.error(f"All {max_attempts} API keys exhausted")
                        raise
                else:
                    # Non-quota error, don't rotate
                    logger.error(f"Gemini inference failed: {e}")
                    raise

# Mock Provider (Testing Only)
class MockProvider(LLMProvider):
    def __init__(self):
        logger.info("Mock Provider initialized (testing mode)")
    
    def classify(self, email_content: str) -> str:
        return json.dumps({
            "event_type": "INTERVIEW",
            "company": "MockCorp",
            "confidence": 0.95,
            "summary": "Mock classification for testing"
        })

    def generate(self, prompt: str) -> str:
        return "Mock generated content based on prompt."

# Main Client with Auto-Fallback
class LLMClient:
    def __init__(self):
        self.providers = []
        
        # Initialize providers based on config
        if config.LLM_PROVIDER == "openai" and config.OPENAI_API_KEY:
            try:
                self.providers.append(("OpenAI", OpenAIProvider()))
            except Exception as e:
                logger.warning(f"Failed to init OpenAI: {e}")
        
        if config.LLM_PROVIDER == "groq" and config.GROQ_API_KEY:
            try:
                self.providers.append(("Groq", GroqProvider()))
            except Exception as e:
                logger.warning(f"Failed to init Groq: {e}")
        
        if config.LLM_PROVIDER == "gemini" and config.GOOGLE_API_KEY:
            try:
                self.providers.append(("Gemini", GeminiProvider()))
            except Exception as e:
                logger.warning(f"Failed to init Gemini: {e}")
        
        # Auto mode: try OpenAI first, then Groq, then Gemini
        if config.LLM_PROVIDER == "auto":
            if config.OPENAI_API_KEY:
                try:
                    self.providers.append(("OpenAI", OpenAIProvider()))
                except Exception as e:
                    logger.warning(f"Failed to init OpenAI: {e}")
            if config.GROQ_API_KEY:
                try:
                    self.providers.append(("Groq", GroqProvider()))
                except Exception as e:
                    logger.warning(f"Failed to init Groq: {e}")
            if config.GOOGLE_API_KEY:
                try:
                    self.providers.append(("Gemini", GeminiProvider()))
                except Exception as e:
                    logger.warning(f"Failed to init Gemini: {e}")
        
        if config.LLM_PROVIDER == "mock":
            self.providers.append(("Mock", MockProvider()))
        
        if not self.providers:
            logger.error("No LLM providers available!")
            raise ValueError("At least one LLM provider must be configured")
        
        logger.info(f"Initialized {len(self.providers)} provider(s): {[name for name, _ in self.providers]}")
    
    def classify_email(self, email_content: str) -> str:
        last_error = None
        
        for provider_name, provider in self.providers:
            try:
                logger.info(f"Attempting classification with {provider_name}...")
                result = provider.classify(email_content)
                logger.info(f"Successfully classified with {provider_name}")
                return result
            except Exception as e:
                logger.warning(f"{provider_name} failed: {e}")
                last_error = e
                continue
        
        # All providers failed
        logger.error(f"All providers failed. Last error: {last_error}")
        return None

    def generate_text(self, prompt: str) -> str:
        last_error = None
        
        for provider_name, provider in self.providers:
            try:
                logger.info(f"Attempting generation with {provider_name}...")
                result = provider.generate(prompt)
                logger.info(f"Successfully generated with {provider_name}")
                return result
            except Exception as e:
                logger.warning(f"{provider_name} failed: {e}")
                last_error = e
                continue
        
        logger.error(f"All providers failed generation. Last error: {last_error}")
        return None
