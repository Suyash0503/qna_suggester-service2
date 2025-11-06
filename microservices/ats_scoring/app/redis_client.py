
# def get_redis_client():
#     return redis.Redis(
#         host=os.getenv("REDIS_HOST", "localhost"),
#         port=int(os.getenv("REDIS_PORT", 6379)),
#         password=os.getenv("REDIS_PASS", None),
#         decode_responses=True
#     )

import os
import redis
from dotenv import load_dotenv

load_dotenv()

class MockRedis:
    """In-memory fallback if Redis is unavailable."""
    def __init__(self):
        self.store = {}
        print("Using MockRedis (no Redis connection)")

    def set(self, key, value):
        self.store[key] = value

    def get(self, key):
        return self.store.get(key)

def get_redis_client():
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", 6379))
    password = os.getenv("REDIS_PASSWORD", None)

    try:
        client = redis.Redis(
            host=host,
            port=port,
            password=password,
            decode_responses=True,
            socket_timeout=3
        )
        client.ping()
        print(f"Connected to Redis at {host}:{port}")
        return client
    except Exception as e:
        print(f"Redis connection failed: {e}")
        return MockRedis()
