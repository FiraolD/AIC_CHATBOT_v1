import logging
from typing import Optional, Any
from redis import Redis, ConnectionPool
from redis.exceptions import RedisError
import json
from ..core.config import settings

logger = logging.getLogger(__name__)

class CacheManager:
    """Manage Redis caching for performance optimization"""
    
    def __init__(self):
        self.redis_client: Optional[Redis] = None
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://10.1.12.21:6379/0')
            
            pool = ConnectionPool.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True
            )
            self.redis_client = Redis(connection_pool=pool)
            
            # Test connection
            self.redis_client.ping()
            logger.info(f"✅ Redis connected: {redis_url}")
            
        except RedisError as e:
            logger.warning(f"⚠️ Redis connection failed: {e}. Caching disabled.")
            self.redis_client = None
        except Exception as e:
            logger.warning(f"⚠️ Redis initialization error: {e}")
            self.redis_client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if self.redis_client is None:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL (seconds)"""
        if self.redis_client is None:
            return False
        
        try:
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(value)
            )
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if self.redis_client is None:
            return False
        
        try:
            self.redis_client.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache delete error for {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if self.redis_client is None:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                count = self.redis_client.delete(*keys)
                logger.debug(f"Cache CLEAR: {len(keys)} keys matching {pattern}")
                return count
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0


# Singleton instance
cache_manager = CacheManager()
