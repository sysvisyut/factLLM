from app.core.config import settings
from app.services.llm.base import LLMProvider
from app.services.llm.offline_provider import OfflineHeuristicProvider
from app.services.llm.gemini_provider import GeminiLLMProvider


def get_llm_provider(provider_name: str = None) -> LLMProvider:
    name = (provider_name or settings.LLM_PROVIDER).lower()
    if name == "gemini":
        return GeminiLLMProvider()
    # Default to offline deterministic provider
    return OfflineHeuristicProvider()
