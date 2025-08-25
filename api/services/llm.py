"""LLM service for OpenAI API integration with fallback and circuit breaker."""

import asyncio
import time
from typing import AsyncIterator, Optional, Dict, Any, List
import openai
from openai import AsyncOpenAI
import pybreaker
from api.utils.config import get_openai_config, settings


class LLMService:
    """Service for LLM interactions with fallback and circuit breaker."""
    
    def __init__(self):
        self.config = get_openai_config()
        self.client: Optional[AsyncOpenAI] = None
        self.primary_model = settings.openai_model
        self.fallback_model = "gpt-3.5-turbo"  # Cheaper fallback
        self.max_tokens = settings.openai_max_tokens
        self.timeout = settings.openai_timeout
        
        # Circuit breaker for primary model
        self.primary_breaker = pybreaker.CircuitBreaker(
            fail_max=3,
            reset_timeout=60,
            exclude=[openai.AuthenticationError, openai.RateLimitError]
        )
        
        # Circuit breaker for fallback model
        self.fallback_breaker = pybreaker.CircuitBreaker(
            fail_max=2,
            reset_timeout=30,
            exclude=[openai.AuthenticationError, openai.RateLimitError]
        )
    
    async def connect(self):
        """Initialize OpenAI client."""
        if not self.client and self.config["api_key"]:
            self.client = AsyncOpenAI(
                api_key=self.config["api_key"],
                base_url=self.config["base_url"],
                timeout=self.timeout
            )
    
    async def disconnect(self):
        """Close OpenAI client."""
        if self.client:
            await self.client.close()
            self.client = None
    
    async def stream_chat(
        self, 
        messages: List[Dict[str, str]], 
        context: Optional[List[Dict[str, Any]]] = None,
        org_id: Optional[int] = None
    ) -> AsyncIterator[str]:
        """
        Stream chat completion with context from search results.
        
        Args:
            messages: List of message dictionaries
            context: List of search results to include as context
            org_id: Organization ID for logging
            
        Yields:
            Token strings as they arrive
        """
        start_time = time.time()
        
        try:
            # Ensure we're connected
            if not self.client:
                await self.connect()
            
            # Build system message with context
            system_message = self._build_system_message(context)
            all_messages = [{"role": "system", "content": system_message}] + messages
            
            # Try primary model first
            try:
                async for token in self._stream_with_model(
                    all_messages, 
                    self.primary_model,
                    self.primary_breaker
                ):
                    yield token
                return
                
            except (pybreaker.CircuitBreakerError, Exception) as e:
                print(f"Primary model failed: {e}")
                
                # Try fallback model if enabled
                if settings.enable_fallback_llm:
                    try:
                        async for token in self._stream_with_model(
                            all_messages, 
                            self.fallback_model,
                            self.fallback_breaker
                        ):
                            yield token
                        return
                        
                    except Exception as fallback_error:
                        print(f"Fallback model also failed: {fallback_error}")
                        yield f"Error: Unable to generate response. Please try again later."
                        return
                else:
                    yield f"Error: Unable to generate response. Please try again later."
                    return
                    
        finally:
            # Log the interaction
            latency_ms = int((time.time() - start_time) * 1000)
            await self._log_interaction(messages, context, latency_ms, org_id)
    
    async def _stream_with_model(
        self, 
        messages: List[Dict[str, str]], 
        model: str,
        breaker: pybreaker.CircuitBreaker
    ) -> AsyncIterator[str]:
        """Stream completion with a specific model using circuit breaker."""
        
        @breaker
        async def _make_request():
            if not self.client:
                await self.connect()
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=0.7,
                stream=True
            )
            
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        async for token in _make_request():
            yield token
    
    def _build_system_message(self, context: Optional[List[Dict[str, Any]]] = None) -> str:
        """Build system message with context from search results."""
        base_message = """You are an AI document assistant that helps users understand and interact with their private documents. 
        Always provide accurate, helpful information based on the context provided from their uploaded documents.
        
        Guidelines:
        - Be concise but comprehensive
        - Cite specific sources from their documents when possible
        - If you're unsure about something, say so
        - Focus on practical insights and actionable information
        - Use clear, professional language
        - Respect the privacy and confidentiality of their documents
        - Only reference information from the documents they've uploaded"""
        
        if context:
            context_text = "\n\nRelevant context:\n"
            for i, result in enumerate(context[:5], 1):  # Limit to top 5 results
                context_text += f"{i}. {result.get('title', 'Untitled')}\n"
                context_text += f"   Source: {result.get('source', 'Unknown')}\n"
                context_text += f"   Content: {result.get('snippet', result.get('text', ''))[:300]}...\n\n"
            
            base_message += context_text
        
        return base_message
    
    async def _log_interaction(
        self, 
        messages: List[Dict[str, str]], 
        context: Optional[List[Dict[str, Any]]], 
        latency_ms: int,
        org_id: Optional[int]
    ):
        """Log the interaction for analytics."""
        # This would typically save to the database
        # For now, just print to console
        input_text = messages[-1]["content"] if messages else ""
        tokens_in = len(input_text.split())  # Rough token count
        tokens_out = 0  # Would need to count actual tokens
        
        print(f"LLM Interaction - Input: {input_text[:100]}..., Latency: {latency_ms}ms, Org: {org_id}")
    
    async def get_models(self) -> List[Dict[str, Any]]:
        """Get available models from OpenAI."""
        try:
            if not self.client:
                await self.connect()
            
            models = await self.client.models.list()
            return [
                {
                    "id": model.id,
                    "created": model.created,
                    "owned_by": model.owned_by
                }
                for model in models.data
            ]
        except Exception as e:
            print(f"Error fetching models: {e}")
            return []
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics (if available)."""
        # This would typically query OpenAI's usage API
        # For now, return placeholder data
        return {
            "total_tokens": 0,
            "total_requests": 0,
            "primary_model_calls": 0,
            "fallback_model_calls": 0,
            "circuit_breaker_trips": {
                "primary": self.primary_breaker.fail_counter,
                "fallback": self.fallback_breaker.fail_counter
            }
        }
    
    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get circuit breaker status for monitoring."""
        return {
            "primary": {
                "state": self.primary_breaker.current_state,
                "fail_counter": self.primary_breaker.fail_counter,
                "last_failure_time": getattr(self.primary_breaker, 'last_failure_time', None)
            },
            "fallback": {
                "state": self.fallback_breaker.current_state,
                "fail_counter": self.fallback_breaker.fail_counter,
                "last_failure_time": getattr(self.fallback_breaker, 'last_failure_time', None)
            }
        }


# Global LLM service instance
llm_service = LLMService()
