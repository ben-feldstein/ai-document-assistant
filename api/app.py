"""Main FastAPI application for the AI Voice Policy Assistant."""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

from api.routes import auth, chat, ws_audio, corpus, admin
from api.models.db import create_tables
from api.services.cache import cache_service
from api.services.llm import llm_service
from api.services.stt import stt_service
from api.services.vectorizer import vectorizer_service
from api.utils.config import settings


# Prometheus metrics
http_requests_total = Counter(
    'http_requests_total', 
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

websocket_connections_active = Gauge(
    'websocket_connections_active',
    'Number of active WebSocket connections'
)

cache_hits_total = Counter(
    'cache_hits_total',
    'Total number of cache hits'
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total number of cache misses'
)

llm_response_time_seconds = Histogram(
    'llm_response_time_seconds',
    'LLM response time in seconds'
)

embeddings_generated_total = Counter(
    'embeddings_generated_total',
    'Total number of embeddings generated'
)


# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("Starting AI Voice Policy Assistant...")
    
    # Create database tables
    try:
        create_tables()
        print("Database tables created successfully")
    except Exception as e:
        print(f"Warning: Could not create database tables: {e}")
    
    # Initialize services
    try:
        await cache_service.connect()
        print("Cache service connected")
    except Exception as e:
        print(f"Warning: Could not connect to cache: {e}")
    
    try:
        await llm_service.connect()
        print("LLM service connected")
    except Exception as e:
        print(f"Warning: Could not connect to LLM service: {e}")
    
    yield
    
    # Shutdown
    print("Shutting down AI Voice Policy Assistant...")
    
    try:
        await cache_service.disconnect()
        print("Cache service disconnected")
    except Exception as e:
        print(f"Warning: Error disconnecting cache service: {e}")
    
    try:
        await llm_service.disconnect()
        print("LLM service disconnected")
    except Exception as e:
        print(f"Warning: Error disconnecting LLM service: {e}")
    
    try:
        await stt_service.close()
        print("STT service closed")
    except Exception as e:
        print(f"Warning: Error closing STT service: {e}")
    
    try:
        await vectorizer_service.close()
        print("Vectorizer service closed")
    except Exception as e:
        print(f"Warning: Error closing vectorizer service: {e}")


# Create FastAPI app
app = FastAPI(
    title="AI Voice Policy Assistant",
    description="AI-powered voice assistant for policy and regulatory document queries",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# Middleware to track HTTP metrics
@app.middleware("http")
async def track_http_metrics(request: Request, call_next):
    start_time = time.time()
    
    # Get response
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Record metrics
    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=500,
        content={
            "ok": False,
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred"
        }
    )


# Include routers
app.include_router(
    auth.router, 
    prefix="/auth", 
    tags=["Authentication"]
)

app.include_router(
    chat.router, 
    prefix="/chat", 
    tags=["Chat"]
)

app.include_router(
    ws_audio.router, 
    prefix="/ws", 
    tags=["WebSocket Audio"]
)

app.include_router(
    corpus.router, 
    prefix="/corpus", 
    tags=["Corpus Management"]
)

app.include_router(
    admin.router, 
    prefix="/admin", 
    tags=["Administration"]
)


# Health check endpoint
@app.get("/healthz", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    try:
        # Check basic service health
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0",
            "services": {}
        }
        
        # Check cache service
        try:
            cache_stats = await cache_service.get_cache_stats()
            health_status["services"]["cache"] = "healthy"
        except Exception:
            health_status["services"]["cache"] = "unhealthy"
        
        # Check LLM service
        try:
            llm_status = llm_service.get_circuit_breaker_status()
            if llm_status["primary"]["state"] == "closed":
                health_status["services"]["llm"] = "healthy"
            else:
                health_status["services"]["llm"] = "degraded"
        except Exception:
            health_status["services"]["llm"] = "unhealthy"
        
        # Check STT service
        try:
            stt_info = await stt_service.get_model_info()
            if stt_info.get("model_loaded", False):
                health_status["services"]["stt"] = "healthy"
            else:
                health_status["services"]["stt"] = "loading"
        except Exception:
            health_status["services"]["stt"] = "unhealthy"
        
        # Check vectorizer service
        try:
            vectorizer_info = await vectorizer_service.get_model_info()
            if vectorizer_info.get("model_loaded", False):
                health_status["services"]["vectorizer"] = "healthy"
            else:
                health_status["services"]["vectorizer"] = "loading"
        except Exception:
            health_status["services"]["vectorizer"] = "unhealthy"
        
        # Overall health status
        unhealthy_services = [
            status for status in health_status["services"].values() 
            if status == "unhealthy"
        ]
        
        if unhealthy_services:
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": time.time(),
            "version": "1.0.0",
            "error": str(e),
            "services": {}
        }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "ok": True,
        "data": {
                    "name": "AI Document Assistant",
        "version": "1.0.0",
        "description": "AI-powered assistant for intelligent document interaction and analysis",
            "endpoints": {
                "health": "/healthz",
                "auth": "/auth",
                "chat": "/chat",
                "voice": "/ws/audio",
                "corpus": "/corpus",
                "admin": "/admin"
            }
        }
    }


# Metrics endpoint for Prometheus
@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint."""
    try:
        # Get additional service metrics
        cache_stats = await cache_service.get_cache_stats()
        llm_status = llm_service.get_circuit_breaker_status()
        
        # Update custom metrics
        cache_connections = cache_stats.get("connected_clients", 0)
        websocket_connections_active.set(cache_connections)
        
        # Return Prometheus-formatted metrics
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching metrics: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
