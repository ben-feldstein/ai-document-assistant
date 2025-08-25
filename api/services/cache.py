"""Redis cache service for response, embedding, and search caching."""

import hashlib
import json
import pickle
from typing import Optional, Any, Dict, List
import redis.asyncio as redis
from api.utils.config import get_redis_url, settings


class CacheService:
    """Redis-based caching service for various data types."""
    
    def __init__(self):
        self.redis_url = get_redis_url()
        self.redis: Optional[redis.Redis] = None
        
    async def connect(self):
        """Connect to Redis."""
        if not self.redis:
            self.redis = redis.from_url(self.redis_url, decode_responses=False)
            await self.redis.ping()
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            self.redis = None
    
    def _hash_key(self, data: str) -> str:
        """Generate a hash for cache keys."""
        return hashlib.sha256(data.encode()).hexdigest()
    
    async def get_response_cache(self, query: str, org_id: int) -> Optional[Dict[str, Any]]:
        """Get cached response for a query within an organization."""
        await self.connect()
        key = f"response_cache:{org_id}:{self._hash_key(query)}"
        data = await self.redis.get(key)
        if data:
            return pickle.loads(data)
        return None
    
    async def set_response_cache(self, query: str, response: Dict[str, Any], org_id: int, ttl: Optional[int] = None) -> bool:
        """Cache a response for a query within an organization."""
        await self.connect()
        key = f"response_cache:{org_id}:{self._hash_key(query)}"
        ttl = ttl or settings.response_cache_ttl
        data = pickle.dumps(response)
        return await self.redis.setex(key, ttl, data)
    
    async def get_embedding_cache(self, text: str) -> Optional[List[float]]:
        """Get cached embedding for text."""
        await self.connect()
        key = f"embedding_cache:{self._hash_key(text)}"
        data = await self.redis.get(key)
        if data:
            return pickle.loads(data)
        return None
    
    async def set_embedding_cache(self, text: str, embedding: List[float]) -> bool:
        """Cache an embedding for text (no TTL for embeddings)."""
        await self.connect()
        key = f"embedding_cache:{self._hash_key(text)}"
        data = pickle.dumps(embedding)
        return await self.redis.set(key, data)
    
    async def get_search_cache(self, query: str, org_id: int) -> Optional[List[int]]:
        """Get cached search results for a query within an organization."""
        await self.connect()
        key = f"search_cache:{org_id}:{self._hash_key(query)}"
        data = await self.redis.get(key)
        if data:
            return pickle.loads(data)
        return None
    
    async def set_search_cache(self, query: str, doc_ids: List[int], org_id: int, ttl: Optional[int] = None) -> bool:
        """Cache search results for a query within an organization."""
        await self.connect()
        key = f"search_cache:{org_id}:{self._hash_key(query)}"
        ttl = ttl or settings.search_cache_ttl
        data = pickle.dumps(doc_ids)
        return await self.redis.setex(key, ttl, data)
    
    async def invalidate_cache(self, pattern: str) -> int:
        """Invalidate cache keys matching a pattern."""
        await self.connect()
        keys = await self.redis.keys(pattern)
        if keys:
            return await self.redis.delete(*keys)
        return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        await self.connect()
        info = await self.redis.info()
        return {
            "used_memory": info.get("used_memory_human", "N/A"),
            "connected_clients": info.get("connected_clients", 0),
            "total_commands_processed": info.get("total_commands_processed", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
        }
    
    async def clear_all_caches(self) -> bool:
        """Clear all caches (use with caution!)."""
        await self.connect()
        return await self.redis.flushdb()


# Global cache service instance
cache_service = CacheService()
