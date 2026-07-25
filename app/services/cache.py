import time

_cache = {}
CACHE_TTL_SECONDS = 300


def get_cached(key: str):
    entry = _cache.get(key)
    if entry and (time.time() - entry["timestamp"]) < CACHE_TTL_SECONDS:
        return entry["data"]
    return None


def set_cached(key: str, data):
    _cache[key] = {"data": data, "timestamp": time.time()}
