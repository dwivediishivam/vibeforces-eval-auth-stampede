"""Auth key fetcher. Fetches JWT signing keys from KMS, caches in Redis."""
import time
import threading
from kms_stub import kms_fetch_keys


class FakeRedis:
    def __init__(self):
        self._store = {}
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if expires_at < time.monotonic():
                del self._store[key]
                return None
            return value

    def setex(self, key, ttl, value):
        with self._lock:
            self._store[key] = (value, time.monotonic() + ttl)


redis = FakeRedis()
KEY_CACHE_KEY = "jwt:signing_keys"
TTL_SECONDS = 7 * 24 * 3600


def get_signing_keys():
    cached = redis.get(KEY_CACHE_KEY)
    if cached is not None:
        return cached
    # BUG: stampede. Every concurrent miss makes its own KMS fetch.
    keys = kms_fetch_keys()
    redis.setex(KEY_CACHE_KEY, TTL_SECONDS, keys)
    return keys
