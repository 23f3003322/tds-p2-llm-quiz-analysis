"""
LLM Client - Pydantic AI Integration
Provides unified interface to LLM services through AIPipe with Pydantic AI
"""

import httpx
import os
from typing import Optional, Dict, Any, List, Type, TypeVar
from datetime import datetime
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel

from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import TaskProcessingError

logger = get_logger(__name__)

T = TypeVar('T', bound=BaseModel)


class LLMClient:
    """
    Unified LLM Client supporting both Pydantic AI agents and direct API calls
    Provides structured outputs with automatic validation
    """
    
    def __init__(
        self,
        api_token: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None
    ):
        """
        Initialize LLM Client with Pydantic AI support
        
        Args:
            api_token: AIPipe token (defaults to settings)
            base_url: AIPipe base URL (defaults to settings)
            model: Model name (defaults to settings)
            temperature: Generation temperature (defaults to settings)
            max_tokens: Maximum tokens (defaults to settings)
            timeout: Request timeout (defaults to settings)
        """
        self.api_token = api_token or settings.AIPIPE_TOKEN
        self.base_url = base_url or settings.AIPIPE_BASE_URL
        self.model = model or settings.LLM_DEFAULT_MODEL
        self.temperature = temperature or settings.LLM_TEMPERATURE
        self.max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        self.timeout = timeout or settings.LLM_TIMEOUT
        
        if not self.api_token:
            logger.error("❌ AIPIPE_TOKEN not configured")
            raise ValueError("AIPIPE_TOKEN is required. Set it in .env file.")
        
        # Set environment variables for Pydantic AI OpenAIChatModel
        # It reads from OPENAI_API_KEY and OPENAI_BASE_URL
        os.environ['OPENAI_API_KEY'] = self.api_token
        os.environ['OPENAI_BASE_URL'] = self.base_url
        
        # Create HTTP client for direct API calls
        self._http_client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
        )
        
        # Create OpenAIChatModel for Pydantic AI
        # It will read API key and base URL from environment variables
        try:
            self._pydantic_model = OpenAIChatModel(self.model)
            logger.debug("✓ Pydantic AI model initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Pydantic AI model: {e}")
            raise
        
        logger.info(f"✅ LLM Client initialized | Model: {self.model} | Base: {self.base_url}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def close(self):
        """Close HTTP clients"""
        try:
            await self._http_client.aclose()
            logger.debug("HTTP client closed")
        except Exception as e:
            logger.debug(f"Error closing HTTP client: {e}")
    
    def create_agent(
        self,
        output_type: Type[T],
        system_prompt: Optional[str] = None,
        retries: int = 2
    ) -> Agent[None, T]:
        """
        Create a Pydantic AI agent for structured outputs
        
        Args:
            output_type: Pydantic model for output validation
            system_prompt: Optional system instructions
            retries: Number of retries on validation failure
            
        Returns:
            Agent: Configured Pydantic AI agent
        """
        logger.debug(f"Creating Pydantic AI agent | Output: {output_type.__name__}")
        
        return Agent(
            model=self._pydantic_model,
            output_type=output_type,
            system_prompt=system_prompt,
            retries=retries
        )
    
    async def run_agent(
        self,
        agent: Agent[None, T],
        prompt: str,
        message_history: Optional[List[Dict[str, str]]] = None
    ) -> T:
        """
        Run a Pydantic AI agent with a prompt
        
        Args:
            agent: Pydantic AI agent
            prompt: User prompt
            message_history: Optional previous messages
            
        Returns:
            Validated output of type T
            
        Raises:
            TaskProcessingError: If agent run fails
        """
        logger.info(f"🤖 Running Pydantic AI agent | Prompt: {prompt[:100]}...")
        
        try:
            start_time = datetime.now()
            
            result = await agent.run(prompt, message_history=message_history)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Agent completed | Time: {elapsed:.2f}s")
            
            # Extract data from result - try different attribute names
            output_data = None
            if hasattr(result, 'data'):
                output_data = result.data
            elif hasattr(result, 'output'):
                output_data = result.output
            elif hasattr(result, 'result'):
                output_data = result.result
            else:
                # The result itself might be the data
                output_data = result
            
            logger.debug(f"Output type: {type(output_data).__name__}")
            
            return output_data
            
        except Exception as e:
            logger.error(f"❌ Agent run failed: {str(e)}", exc_info=True)
            raise TaskProcessingError(f"LLM agent failed: {str(e)}")
    
    async def structured_output(
        self,
        prompt: str,
        output_type: Type[T],
        system_prompt: Optional[str] = None
    ) -> T:
        """
        Get structured output in one call (creates agent and runs it)
        
        Args:
            prompt: User prompt
            output_type: Pydantic model for output
            system_prompt: Optional system instructions
            
        Returns:
            Validated output of type T
        """
        agent = self.create_agent(output_type, system_prompt)
        return await self.run_agent(agent, prompt)
    
    # Fallback methods for simple prompts (without Pydantic validation)
    async def simple_prompt(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Simple prompt without structured output
        Use for free-form text generation
        
        Args:
            prompt: User prompt
            system: Optional system message
            temperature: Override default temperature
            max_tokens: Override default max tokens
            
        Returns:
            str: LLM response text
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        return await self._direct_chat(messages, temperature, max_tokens)
    
    async def _direct_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Direct API call without Pydantic AI (for simple cases)
        
        Args:
            messages: List of message dicts
            temperature: Temperature override
            max_tokens: Max tokens override
            
        Returns:
            str: Response text
        """
        temperature = temperature if temperature is not None else self.temperature
        max_tokens = max_tokens or self.max_tokens
        
        logger.info(f"🤖 Direct LLM call | Messages: {len(messages)}")
        
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            start_time = datetime.now()
            response = await self._http_client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            response.raise_for_status()
            
            data = response.json()
            content = data['choices'][0]['message']['content']
            
            usage = data.get('usage', {})
            if usage:
                logger.info(
                    f"✅ LLM response | Time: {elapsed:.2f}s | "
                    f"Tokens: {usage.get('total_tokens', 'N/A')}"
                )
            else:
                logger.info(f"✅ LLM response | Time: {elapsed:.2f}s")
            
            return content
            
        except httpx.HTTPStatusError as e:
            error_text = e.response.text
            logger.error(f"❌ LLM HTTP error {e.response.status_code}: {error_text}")
            raise TaskProcessingError(f"LLM API error: {error_text}")
        
        except httpx.TimeoutException:
            logger.error(f"⏱️  LLM request timeout after {self.timeout}s")
            raise TaskProcessingError("LLM request timeout")
        
        except Exception as e:
            logger.error(f"❌ LLM request failed: {str(e)}", exc_info=True)
            raise TaskProcessingError(f"LLM request failed: {str(e)}")


# Singleton instance for convenience
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """
    Get or create singleton LLM client instance
    
    Returns:
        LLMClient: Configured LLM client
        
    Raises:
        ValueError: If LLM not configured
    """
    global _llm_client
    
    if _llm_client is None:
        if not settings.is_llm_configured():
            logger.error("❌ LLM not configured - AIPIPE_TOKEN missing")
            raise ValueError(
                "LLM not configured. Set AIPIPE_TOKEN in .env file.\n"
                "Get your token from: https://aipipe.org/login"
            )
        
        _llm_client = LLMClient()
        logger.info("LLM client singleton created")
    
    return _llm_client


async def close_llm_client():
    """Close the singleton LLM client"""
    global _llm_client
    if _llm_client:
        await _llm_client.close()
        _llm_client = None
        logger.info("LLM client closed")
