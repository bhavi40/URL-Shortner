import redis.asyncio as redis
from app.core.config import settings
from app.core.logging import logger

class CacheService:
    """
    Redis cache service for URL lookups.
    Cache-aside pattern:
    1. Check Redis first
    2. On miss → query DB → store in Redis
    3. Return URL
    """

    def __init__(self):
        self.redis = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=2,    # fail fast if Redis is down
            socket_timeout=2,
            retry_on_timeout=True,
        )

    def _key(self, short_code: str) -> str:
        """Redis key format: redirect:xK9mPq"""
        return f"redirect:{short_code}"

    async def get_url(self, short_code: str) -> str | None:
        """Get original URL from cache."""
        try:
            url = await self.redis.get(self._key(short_code))
            if url:
                logger.debug(f"Cache HIT for {short_code}")
                return url
            logger.debug(f"Cache MISS for {short_code}")
            return None
        except Exception as e:
            # Never let Redis failure break redirects
            logger.warning(f"Redis get failed for {short_code}: {e}")
            return None

    async def set_url(
        self,
        short_code: str,
        original_url: str,
        ttl: int = None
    ) -> None:
        """Store URL in cache with TTL."""
        try:
            await self.redis.setex(
                self._key(short_code),
                ttl or settings.REDIS_CACHE_TTL,
                original_url
            )
            logger.debug(f"Cached {short_code} for {ttl or settings.REDIS_CACHE_TTL}s")
        except Exception as e:
            # Never let Redis failure break redirects
            logger.warning(f"Redis set failed for {short_code}: {e}")

    async def invalidate_url(self, short_code: str) -> None:
        """Remove URL from cache — called when link is deleted."""
        try:
            await self.redis.delete(self._key(short_code))
            logger.info(f"Cache invalidated for {short_code}")
        except Exception as e:
            logger.warning(f"Redis delete failed for {short_code}: {e}")

    async def get_cache_stats(self) -> dict:
        """Get Redis stats for monitoring."""
        try:
            info = await self.redis.info("stats")
            return {
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": round(
                    info.get("keyspace_hits", 0) /
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1) * 100,
                    2
                )
            }
        except Exception as e:
            logger.warning(f"Redis stats failed: {e}")
            return {}

    async def close(self):
        await self.redis.aclose()

# Global instance
cache_service = CacheService()