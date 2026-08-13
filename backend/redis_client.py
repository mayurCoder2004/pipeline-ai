import os

import redis.asyncio as redis
from kombu.utils.url import safequote


# ============================================================
# Redis Configuration
# ============================================================

redis_host = safequote(
    os.environ.get(
        "REDIS_HOST",
        "localhost",
    )
)

redis_client = redis.Redis(
    host=redis_host,
    port=6379,
    db=0,
)


# ============================================================
# Set Redis Key
# ============================================================

async def add_key_value_redis(
    key,
    value,
    expire=None,
):
    """
    Store a key-value pair in Redis.

    Args:
        key: Redis key.
        value: Value to store.
        expire: Optional expiration time in seconds.
    """

    await redis_client.set(
        key,
        value,
    )

    if expire:
        await redis_client.expire(
            key,
            expire,
        )


# ============================================================
# Get Redis Value
# ============================================================

async def get_value_redis(key):
    """
    Retrieve a value from Redis.
    """

    return await redis_client.get(key)


# ============================================================
# Delete Redis Key
# ============================================================

async def delete_key_redis(key):
    """
    Delete a key from Redis.
    """

    await redis_client.delete(key)


# ============================================================
# Close Redis Connection
# ============================================================

async def close_redis():
    """
    Gracefully close the Redis connection pool.

    This prevents the async Redis client from being
    garbage-collected after the event loop has already
    been closed.
    """

    await redis_client.aclose()