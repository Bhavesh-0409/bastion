import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class LLMProxy:
    """Proxy layer for LLM requests"""
    
    def __init__(self, llm_endpoint: str, security_check_fn):
        self.llm_endpoint = llm_endpoint
        self.security_check = security_check_fn
    
    async def send_prompt(self, prompt: str, model: str) -> Optional[str]:
        """
        Send prompt to LLM after security validation.
        Returns response or None if blocked.
        """
        logger.info(f"LLMProxy: Processing prompt for model {model}")
        
        # TODO: Call self.security_check(prompt, model)
        # TODO: Forward to self.llm_endpoint if safe
        # TODO: Log blocked prompts
        
        return "Response placeholder"

# Factory function
def create_llm_proxy(endpoint: str) -> LLMProxy:
    """Create LLM proxy with default security check"""
    def default_check(prompt: str, model: str):
        # TODO: Integrate with rule_engine + classifier
        return True
    
    return LLMProxy(endpoint, default_check)
