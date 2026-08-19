import os
import json
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("REDIS_HOST", "redis")
PORT = int(os.getenv("REDIS_PORT", 6379))

redis_client = redis.Redis(host=HOST, port=PORT, db=0, decode_responses=True)

async def redis_movies_save(list_movies):
    result = [movie.model_dump(mode="json") for movie in list_movies]
    await redis_client.setex("movies", 30, json.dumps(result))

async def redis_movies_get():
    value = await redis_client.get("movies")
    
    if value is None:
        return None
    
    return json.loads(value)


async def redis_movies_delete():
    await redis_client.delete("movies")