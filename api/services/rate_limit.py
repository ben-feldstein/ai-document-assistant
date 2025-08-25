"""Rate limiting service using Redis sliding window implementation."""

import time
from typing import Optional, Tuple
import redis.asyncio as redis
from api.utils.config import get_redis_url, settings


class RateLimitService:
    """Rate limiting service using Redis sliding window."""
    
    def __init__(self):
        self.redis_url = get_redis_url()
        self.redis: Optional[redis.Redis] = None
        
    async def connect(self):
        """Connect to Redis."""
        if not self.redis:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            self.redis = None
    
    async def check_rate_limit(
        self, 
        org_id: int, 
        user_id: Optional[int] = None,
        rpm: Optional[int] = None,
        burst: Optional[int] = None
    ) -> Tuple[bool, int, int]:
        """
        Check if request is within rate limits.
        
        Returns:
            Tuple of (allowed, remaining_requests, reset_time)
        """
        await self.connect()
        
        # Get rate limit config for org
        if rpm is None or burst is None:
            org_rpm, org_burst = await self._get_org_rate_limits(org_id)
            rpm = rpm or org_rpm
            burst = burst or org_burst
        
        # Create key for this org/user combination
        key = f"rate_limit:{org_id}"
        if user_id:
            key += f":{user_id}"
        
        current_time = int(time.time())
        window_start = current_time - 60  # 1 minute window
        
        # Get current requests in window
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)  # Remove expired entries
        pipe.zcard(key)  # Count remaining entries
        pipe.zrange(key, 0, -1)  # Get all timestamps
        pipe.expire(key, 120)  # Set expiry
        
        results = await pipe.execute()
        current_requests = results[1]
        timestamps = results[2]
        
        # Check if we're within burst limit
        if current_requests >= burst:
            # Check if we can remove old requests to make room
            if timestamps and current_time - int(timestamps[0]) >= 60:
                # Oldest request is more than 1 minute old, allow
                pass
            else:
                # Still within burst limit, deny
                return False, 0, 60 - (current_time - int(timestamps[0]) if timestamps else 0)
        
        # Check if we're within RPM limit
        if current_requests >= rpm:
            # Check if we can remove old requests to make room
            if timestamps and current_time - int(timestamps[0]) >= 60:
                # Oldest request is more than 1 minute old, allow
                pass
            else:
                # Still within RPM limit, deny
                return False, 0, 60 - (current_time - int(timestamps[0]) if timestamps else 0)
        
        # Allow request
        remaining = max(0, rpm - current_requests)
        reset_time = 60 - (current_time - window_start)
        
        return True, remaining, reset_time
    
    async def record_request(
        self, 
        org_id: int, 
        user_id: Optional[int] = None
    ) -> bool:
        """Record a request for rate limiting."""
        await self.connect()
        
        key = f"rate_limit:{org_id}"
        if user_id:
            key += f":{user_id}"
        
        current_time = int(time.time())
        
        # Add current timestamp to sorted set
        await self.redis.zadd(key, {str(current_time): current_time})
        await self.redis.expire(key, 120)  # 2 minute expiry
        
        return True
    
    async def _get_org_rate_limits(self, org_id: int) -> Tuple[int, int]:
        """Get rate limit configuration for an organization."""
        # This would typically query the database
        # For now, return defaults
        return settings.default_rpm, settings.default_burst
    
    async def set_org_rate_limits(self, org_id: int, rpm: int, burst: int) -> bool:
        """Set rate limit configuration for an organization."""
        # This would typically update the database
        # For now, just return success
        return True
    
    async def get_rate_limit_stats(self, org_id: int) -> dict:
        """Get rate limiting statistics for an organization."""
        await self.connect()
        
        key = f"rate_limit:{org_id}"
        current_time = int(time.time())
        window_start = current_time - 60
        
        # Get current requests in window
        await self.redis.zremrangebyscore(key, 0, window_start)
        current_requests = await self.redis.zcard(key)
        
        org_rpm, org_burst = await self._get_org_rate_limits(org_id)
        
        return {
            "org_id": org_id,
            "current_requests": current_requests,
            "rpm_limit": org_rpm,
            "burst_limit": org_burst,
            "remaining": max(0, org_rpm - current_requests),
            "window_start": window_start,
            "window_end": current_time
        }


# Global rate limit service instance
rate_limit_service = RateLimitService()
