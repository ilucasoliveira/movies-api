import os
import json
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("REDIS_HOST", "redis")
PORT = int(os.getenv("REDIS_PORT", 6379))

redis_client = redis.Redis(host=HOST, port=PORT, db=0, decode_responses=True)

async def cache_save(key, data, ttl=30):
    await redis_client.setex(key, ttl, json.dumps(data))

async def cache_get(key):
    value = await redis_client.get(key)
    if value is None:
        return None
    return json.loads(value)

async def cache_delete(key):
    await redis_client.delete(key)