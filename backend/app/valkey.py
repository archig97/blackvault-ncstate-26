import os
from redis import Redis

def get_client() -> Redis:
    host = os.getenv("VALKEY_HOST", "localhost")
    port = int(os.getenv("VALKEY_PORT", "6379"))
    return Redis(host=host, port=port, decode_responses=True)
