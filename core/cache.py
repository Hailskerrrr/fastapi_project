from redis.asyncio import Redis
from core.config import settings
import json

redis = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)

async def get_cached_data(key: str):
    data = await redis.get(key)
    return json.loads(data) if data else None

async def set_cached_data(key: str, value: any, expire: int = 3600):
    await redis.set(key, json.dumps(value), ex=expire)

async def delete_cached_data(key: str):
    await redis.delete(key)

async def clear_cache_pattern(pattern: str) -> None:
    """Очистка кэша по паттерну"""
    keys = await redis.keys(pattern)
    if keys:
        await redis.delete(*keys) 