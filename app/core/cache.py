import json
from typing import Any, Optional, Union
from datetime import timedelta
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

from app.core.config import settings
from app.core.logging import logger

_redis_client: Optional[redis.Redis] = None
_connection_pool: Optional[ConnectionPool] = None


async def get_redis_client() -> Optional[redis.Redis]:
    global _redis_client, _connection_pool
    
    if not settings.REDIS_URL:
        return None
    
    if _redis_client is None:
        try:
            _connection_pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                max_connections=20
            )
            _redis_client = redis.Redis(connection_pool=_connection_pool)
            await _redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            _redis_client = None
    
    return _redis_client


async def close_redis() -> None:
    global _redis_client, _connection_pool
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
    if _connection_pool:
        await _connection_pool.disconnect()
        _connection_pool = None
    logger.info("Redis connection closed")


class CacheService:
    def __init__(self, prefix: str = None):
        self.prefix = prefix or settings.CACHE_PREFIX
        self.default_ttl = settings.CACHE_TTL
    
    def _make_key(self, key: str) -> str:
        return f"{self.prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        client = await get_redis_client()
        if client is None:
            return None
        
        try:
            value = await client.get(self._make_key(key))
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        client = await get_redis_client()
        if client is None:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            await client.set(
                self._make_key(key),
                json.dumps(value, default=str),
                ex=ttl
            )
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        client = await get_redis_client()
        if client is None:
            return False
        
        try:
            await client.delete(self._make_key(key))
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        client = await get_redis_client()
        if client is None:
            return 0
        
        try:
            full_pattern = self._make_key(pattern)
            keys = await client.keys(full_pattern)
            if keys:
                return await client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        client = await get_redis_client()
        if client is None:
            return False
        
        try:
            return await client.exists(self._make_key(key)) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def incr(self, key: str, amount: int = 1) -> Optional[int]:
        client = await get_redis_client()
        if client is None:
            return None
        
        try:
            return await client.incrby(self._make_key(key), amount)
        except Exception as e:
            logger.error(f"Cache incr error for key {key}: {e}")
            return None
    
    async def expire(self, key: str, ttl: int) -> bool:
        client = await get_redis_client()
        if client is None:
            return False
        
        try:
            return await client.expire(self._make_key(key), ttl)
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False
    
    async def get_ttl(self, key: str) -> int:
        client = await get_redis_client()
        if client is None:
            return -2
        
        try:
            return await client.ttl(self._make_key(key))
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return -2
    
    async def hget(self, name: str, key: str) -> Optional[str]:
        client = await get_redis_client()
        if client is None:
            return None
        
        try:
            return await client.hget(self._make_key(name), key)
        except Exception as e:
            logger.error(f"Cache hget error for {name}.{key}: {e}")
            return None
    
    async def hset(self, name: str, key: str, value: Any) -> bool:
        client = await get_redis_client()
        if client is None:
            return False
        
        try:
            await client.hset(
                self._make_key(name), 
                key, 
                json.dumps(value, default=str) if not isinstance(value, str) else value
            )
            return True
        except Exception as e:
            logger.error(f"Cache hset error for {name}.{key}: {e}")
            return False
    
    async def hgetall(self, name: str) -> dict:
        client = await get_redis_client()
        if client is None:
            return {}
        
        try:
            return await client.hgetall(self._make_key(name))
        except Exception as e:
            logger.error(f"Cache hgetall error for {name}: {e}")
            return {}
    
    async def get_stats(self) -> dict:
        client = await get_redis_client()
        if client is None:
            return {"status": "disconnected"}
        
        try:
            info = await client.info("memory")
            return {
                "status": "connected",
                "used_memory": info.get("used_memory_human", "N/A"),
                "peak_memory": info.get("used_memory_peak_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


cache = CacheService()
