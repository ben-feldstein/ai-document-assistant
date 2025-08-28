"""Core orchestrator service for coordinating voice interactions."""

import time
from typing import AsyncIterator, Optional, Dict, Any, List
from api.services.cache import cache_service
from api.services.search import search_service
from api.services.llm import llm_service
from api.services.stt import stt_service
from api.services.vectorizer import vectorizer_service
from api.services.rate_limit import rate_limit_service
from api.models.schemas import ChatRequest, ChatResponse, ResponseEnvelope


class OrchestratorService:
    """Main orchestrator service for voice interactions."""
    
    def __init__(self):
        self.max_context_length = 8000  # Maximum context length for LLM
        self.default_search_k = 8  # Default number of search results
        
    async def handle_voice_query(
        self, 
        audio_data: bytes,
        org_id: Optional[int] = None,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Handle a voice query end-to-end.
        
        Args:
            audio_data: Raw audio data
            org_id: Organization ID
            user_id: User ID
            session_id: Session ID for tracking
            
        Yields:
            Streaming response data
        """
        start_time = time.time()
        
        try:
            # Step 1: Transcribe audio
            yield {
                "type": "status",
                "data": "Transcribing audio...",
                "timestamp": time.time()
            }
            
            transcription = await stt_service.transcribe_audio(audio_data)
            if transcription.get("error"):
                yield {
                    "type": "error",
                    "data": f"Transcription failed: {transcription['error']}",
                    "timestamp": time.time()
                }
                return
            
            transcript_text = transcription["text"]
            confidence = transcription.get("confidence", 0.0)
            
            yield {
                "type": "transcript",
                "data": transcript_text,
                "confidence": confidence,
                "is_final": True,
                "timestamp": time.time()
            }
            
            # Step 2: Check rate limits
            if org_id:
                allowed, remaining, reset_time = await rate_limit_service.check_rate_limit(org_id, user_id)
                if not allowed:
                    yield {
                        "type": "error",
                        "data": f"Rate limit exceeded. Try again in {reset_time} seconds.",
                        "timestamp": time.time()
                    }
                    return
                
                # Record the request
                await rate_limit_service.record_request(org_id, user_id)
            
            # Step 3: Check cache for response
            yield {
                "type": "status",
                "data": "Searching for relevant information...",
                "timestamp": time.time()
            }
            
            cached_response = await cache_service.get_response_cache(transcript_text, org_id)
            if cached_response:
                yield {
                    "type": "chat_response",
                    "data": cached_response["response"],
                    "sources": cached_response.get("sources", []),
                    "cached": True,
                    "timestamp": time.time()
                }
                return
            
            # Step 4: Semantic search for context
            # CRITICAL: Ensure org_id is set for security
            if not org_id:
                yield {
                    "type": "error",
                    "data": "Organization ID is required for security",
                    "timestamp": time.time()
                }
                return
            
            # Search for context - this will be filtered by org_id
            search_results = await search_service.search(
                transcript_text, 
                k=self.default_search_k,
                org_id=org_id
            )
            
            if not search_results:
                yield {
                    "type": "status",
                    "data": "No relevant documents found. Generating response...",
                    "timestamp": time.time()
            }
            
            # Step 5: Generate LLM response with context
            yield {
                "type": "status",
                "data": "Generating response...",
                "timestamp": time.time()
            }
            
            # Prepare context for LLM
            context = self._prepare_context(search_results)
            
            # Stream LLM response
            response_text = ""
            sources = []
            
            async for token in llm_service.stream_chat(
                [{"role": "user", "content": transcript_text}],
                context=search_results,
                org_id=org_id
            ):
                response_text += token
                yield {
                    "type": "token",
                    "data": token,
                    "timestamp": time.time()
                }
            
            # Step 6: Cache the response
            if response_text and not response_text.startswith("Error:"):
                # Extract sources from search results
                sources = [
                    {
                        "title": result.get("title", "Untitled"),
                        "source": result.get("source", ""),
                        "snippet": result.get("snippet", ""),
                        "score": result.get("score", 0)
                    }
                    for result in search_results[:5]  # Top 5 sources
                ]
                
                # Cache the response (organization-scoped)
                await cache_service.set_response_cache(
                    transcript_text,
                    {
                        "response": response_text,
                        "sources": sources,
                        "org_id": org_id,
                        "user_id": user_id
                    },
                    org_id
                )
            
            # Step 7: Final response
            latency_ms = int((time.time() - start_time) * 1000)
            
            yield {
                "type": "final",
                "data": {
                    "response": response_text,
                    "sources": sources,
                    "transcript": transcript_text,
                    "confidence": confidence,
                    "latency_ms": latency_ms,
                    "cached": False
                },
                "timestamp": time.time()
            }
            
        except Exception as e:
            print(f"Orchestrator error: {e}")
            yield {
                "type": "error",
                "data": f"An error occurred: {str(e)}",
                "timestamp": time.time()
            }
    
    async def handle_text_query(
        self, 
        request: ChatRequest
    ) -> ChatResponse:
        """
        Handle a text-based query (non-streaming).
        
        Args:
            request: Chat request object
            
        Returns:
            Chat response object
        """
        start_time = time.time()
        
        try:
            # Check rate limits
            if request.org_id:
                allowed, remaining, reset_time = await rate_limit_service.check_rate_limit(
                    request.org_id, 
                    request.user_id
                )
                if not allowed:
                    raise Exception(f"Rate limit exceeded. Try again in {reset_time} seconds.")
                
                # Record the request
                await rate_limit_service.record_request(request.org_id, request.user_id)
            
            # Check cache (organization-scoped)
            cached_response = await cache_service.get_response_cache(request.text, request.org_id)
            if cached_response:
                latency_ms = int((time.time() - start_time) * 1000)
                return ChatResponse(
                    response=cached_response["response"],
                    sources=cached_response.get("sources", []),
                    tokens_in=len(request.text.split()),
                    tokens_out=len(cached_response["response"].split()),
                    cached=True,
                    latency_ms=latency_ms
                )
            
            # CRITICAL: Ensure org_id is set for security
            if not request.org_id:
                raise Exception("Organization ID is required for security")
            
            # Search for context - this will be filtered by org_id
            search_results = await search_service.search(
                request.text,
                k=self.default_search_k,
                org_id=request.org_id
            )
            
            # Generate LLM response
            response_text = ""
            try:
                response_text = await llm_service.chat(
                    [{"role": "user", "content": request.text}],
                    context=search_results,
                    org_id=request.org_id
                )
            except Exception as e:
                response_text = f"Error generating response: {str(e)}"
            
            # Prepare sources (even if empty)
            sources = [
                {
                    "title": result.get("title", "Untitled"),
                    "source": result.get("source", ""),
                    "snippet": result.get("snippet", ""),
                    "score": result.get("score", 0)
                }
                for result in search_results[:5]
            ]
            
            # Cache response (organization-scoped)
            if response_text and not response_text.startswith("Error:"):
                await cache_service.set_response_cache(
                    request.text,
                    {
                        "response": response_text,
                        "sources": sources,
                        "org_id": request.org_id,
                        "user_id": request.user_id
                    },
                    request.org_id
                )
            
            # Calculate metrics
            latency_ms = int((time.time() - start_time) * 1000)
            
            return ChatResponse(
                response=response_text,
                sources=sources,
                tokens_in=len(request.text.split()),
                tokens_out=len(response_text.split()),
                cached=False,
                latency_ms=latency_ms
            )
            
        except Exception as e:
            print(f"Text query error: {e}")
            raise e
    
    def _prepare_context(self, search_results: List[Dict[str, Any]]) -> str:
        """Prepare context string from search results for LLM."""
        if not search_results:
            return ""
        
        context_parts = []
        total_length = 0
        
        for result in search_results:
            # Create context entry
            title = result.get("title", "Untitled")
            source = result.get("source", "Unknown")
            content = result.get("snippet", result.get("text", ""))
            
            entry = f"Title: {title}\nSource: {source}\nContent: {content}\n"
            
            # Check if adding this entry would exceed context limit
            if total_length + len(entry) > self.max_context_length:
                break
            
            context_parts.append(entry)
            total_length += len(entry)
        
        return "\n".join(context_parts)
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status for monitoring."""
        return {
            "cache": await cache_service.get_cache_stats(),
            "search": {
                "default_k": self.default_search_k,
                "max_context_length": self.max_context_length
            },
            "llm": llm_service.get_circuit_breaker_status(),
            "stt": await stt_service.get_model_info(),
            "vectorizer": await vectorizer_service.get_model_info()
        }


# Global orchestrator service instance
orchestrator_service = OrchestratorService()
