"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# Authentication Schemas
class UserCreate(BaseModel):
    """Schema for user registration."""
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    org_name: str = Field(..., description="Organization name")


class UserLogin(BaseModel):
    """Schema for user login."""
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh."""
    refresh_token: str


# Chat and Voice Schemas
class ChatRequest(BaseModel):
    """Schema for chat API requests."""
    text: str = Field(..., description="Input text for the AI assistant")
    org_id: Optional[int] = None
    user_id: Optional[int] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Schema for chat API responses."""
    response: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    tokens_in: int
    tokens_out: int
    cached: bool = False
    latency_ms: int


class AudioChunk(BaseModel):
    """Schema for audio data chunks."""
    data: bytes
    format: str = "pcm"  # pcm, opus, wav
    sample_rate: int = 16000
    channels: int = 1


class TranscriptResponse(BaseModel):
    """Schema for speech-to-text responses."""
    type: str = Field(..., description="partial_transcript, final_transcript, or error")
    data: str
    confidence: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Corpus Management Schemas
class DocumentCreate(BaseModel):
    """Schema for document creation."""
    source: str = Field(..., description="Document source URL or file path")
    uri: Optional[str] = None
    title: str = Field(..., description="Document title")
    text: str = Field(..., description="Document content")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    org_id: Optional[int] = None


class DocumentResponse(BaseModel):
    """Schema for document responses."""
    id: int
    source: str
    uri: Optional[str]
    title: str
    text: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class SearchRequest(BaseModel):
    """Schema for semantic search requests."""
    query: str = Field(..., description="Search query")
    k: int = Field(default=10, ge=1, le=50, description="Number of results")
    org_id: Optional[int] = None
    filters: Optional[Dict[str, Any]] = None


class SearchResult(BaseModel):
    """Schema for search results."""
    id: int
    score: float
    snippet: str
    metadata: Dict[str, Any]
    doc_id: int
    title: str


class SearchResponse(BaseModel):
    """Schema for search responses."""
    results: List[SearchResult]
    total: int
    query: str
    latency_ms: int


# Admin and Control Schemas
class RateLimitUpdate(BaseModel):
    """Schema for updating rate limits."""
    org_id: int
    rpm: int = Field(..., ge=1, le=1000)
    burst: int = Field(..., ge=1, le=100)


class FeatureFlagUpdate(BaseModel):
    """Schema for updating feature flags."""
    name: str
    enabled: bool
    description: Optional[str] = None


# Response Envelope
class ResponseEnvelope(BaseModel):
    """Standard response envelope for all API responses."""
    ok: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None


# WebSocket Message Schemas
class WSMessage(BaseModel):
    """Schema for WebSocket messages."""
    type: str = Field(..., description="Message type")
    data: Any
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WSAudioMessage(WSMessage):
    """Schema for WebSocket audio messages."""
    type: str = "audio_chunk"
    data: bytes
    format: str = "pcm"
    sample_rate: int = 16000


class WSTranscriptMessage(WSMessage):
    """Schema for WebSocket transcript messages."""
    type: str = "transcript"
    data: str
    confidence: Optional[float] = None
    is_final: bool = False


class WSChatMessage(WSMessage):
    """Schema for WebSocket chat messages."""
    type: str = "chat_response"
    data: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    cached: bool = False


class WSErrorMessage(WSMessage):
    """Schema for WebSocket error messages."""
    type: str = "error"
    data: str
    code: Optional[str] = None


# Health Check Schema
class HealthResponse(BaseModel):
    """Schema for health check responses."""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]  # Service name -> status
