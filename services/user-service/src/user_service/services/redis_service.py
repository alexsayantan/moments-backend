import logging
import redis

from user_service.core.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    """Dedicated Redis service handling connection pooling, key-value operations, and TTL."""

    def __init__(self, redis_url: str | None = None) -> None:
        self._url = redis_url or settings.redis_url
        self._pool: redis.ConnectionPool | None = None
        self._client: redis.Redis | None = None

    @property
    def client(self) -> redis.Redis:
        """Lazy-initialize Redis client with connection pooling."""
        if self._client is None:
            self._pool = redis.ConnectionPool.from_url(
                self._url,
                decode_responses=True,
                max_connections=settings.redis_max_connections,
                socket_timeout=settings.redis_socket_timeout,
                socket_connect_timeout=settings.redis_connect_timeout,
            )
            self._client = redis.Redis(connection_pool=self._pool)
        return self._client

    def ping(self) -> bool:
        """Check if Redis connection is alive."""
        try:
            return bool(self.client.ping())
        except Exception as exc:
            logger.warning("Redis ping failed: %s", exc)
            return False

    def set(self, key: str, value: str, ttl_seconds: int | None = None) -> bool:
        """Store key-value pair with optional TTL."""
        try:
            return bool(self.client.set(name=key, value=value, ex=ttl_seconds))
        except Exception as exc:
            logger.error("Failed to set key '%s' in Redis: %s", key, exc)
            raise

    def get(self, key: str) -> str | None:
        """Retrieve value for key or None if missing or expired."""
        try:
            return self.client.get(name=key)
        except Exception as exc:
            logger.error("Failed to get key '%s' from Redis: %s", key, exc)
            raise

    def delete(self, *keys: str) -> int:
        """Delete one or more keys."""
        if not keys:
            return 0
        try:
            return int(self.client.delete(*keys))
        except Exception as exc:
            logger.error("Failed to delete keys %s from Redis: %s", keys, exc)
            raise

    def exists(self, key: str) -> bool:
        """Check if a key exists."""
        try:
            return bool(self.client.exists(key))
        except Exception as exc:
            logger.error("Failed to check exists for key '%s' in Redis: %s", key, exc)
            raise

    def increment(self, key: str, amount: int = 1) -> int:
        """Increment integer value stored at key."""
        try:
            return int(self.client.incrby(name=key, amount=amount))
        except Exception as exc:
            logger.error("Failed to increment key '%s' in Redis: %s", key, exc)
            raise

    def expire(self, key: str, ttl_seconds: int) -> bool:
        """Set a timeout on key."""
        try:
            return bool(self.client.expire(name=key, time=ttl_seconds))
        except Exception as exc:
            logger.error("Failed to set expire on key '%s' in Redis: %s", key, exc)
            raise

    def get_ttl(self, key: str) -> int:
        """Return the remaining time to live of a key in seconds (-2 if key does not exist, -1 if no TTL)."""
        try:
            return int(self.client.ttl(name=key))
        except Exception as exc:
            logger.error("Failed to get TTL for key '%s' from Redis: %s", key, exc)
            raise

    def close(self) -> None:
        """Close connection pool cleanly."""
        if self._client:
            try:
                self._client.close()
            except Exception as exc:
                logger.warning("Error closing Redis client: %s", exc)
            self._client = None
        if self._pool:
            try:
                self._pool.disconnect()
            except Exception as exc:
                logger.warning("Error disconnecting Redis pool: %s", exc)
            self._pool = None


redis_service = RedisService()


def close_redis_connections() -> None:
    """Dispose of the Redis connection pool cleanly during pod termination."""
    redis_service.close()
