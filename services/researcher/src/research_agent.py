from tavily import TavilyClient
from libs.core.config import BaseConfig, get_config
from libs.core.logger import configure_logger
from libs.core.llm_client import LLMClient

logger = configure_logger("research_agent")

class ResearchConfig(BaseConfig):
    SERVICE_NAME: str = "researcher"
    GOOGLE_API_KEY: str = ""
    TAVILY_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    LLM_PROVIDER: str = "auto"

config = get_config(ResearchConfig)

class ResearchAgent:
    def __init__(self):
        if not config.TAVILY_API_KEY:
            logger.error("TAVILY_API_KEY is required")
            raise ValueError("TAVILY_API_KEY is required")
            
        self.tavily = TavilyClient(api_key=config.TAVILY_API_KEY)
        self.llm = LLMClient()
        logger.info("Research Agent initialized with LLMClient + Tavily.")

    def research_company(self, company_name: str) -> str:
        logger.info(f"Researching company: {company_name}...")
        
        # 1. Search Tavily
        try:
            search_result = self.tavily.search(
                query=f"{company_name} recent news mission interview process",
                search_depth="advanced",
                max_results=5
            )
            context = "\n".join([r['content'] for r in search_result['results']])
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return "Research failed due to search error."

        # 2. Synthesize with LLM
        prompt = f"""You are a career intelligence analyst. 
Based on the following search results, write a 3-paragraph briefing about {company_name}.
Include:
1. Company Mission/What they do
2. Recent News/Developments
3. Interview Process/Culture (if available)

Search Results:
{context}

Return ONLY the briefing text.
"""
        try:
            return self.llm.generate_text(prompt)
        except Exception as e:
            logger.error(f"LLM synthesis failed: {e}")
            return "Research failed due to LLM error."
