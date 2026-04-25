"""KMS stub — rate-limited at 50 rps. Returns 429 when exceeded."""
import threading
import time


_lock = threading.Lock()
_window_start = 0.0
_calls_in_window = 0
_rate_limit_per_sec = 50

call_count = 0


class KmsRateLimited(Exception):
    pass


def kms_fetch_keys():
    global _window_start, _calls_in_window, call_count
    with _lock:
        now = time.monotonic()
        if now - _window_start >= 1.0:
            _window_start = now
            _calls_in_window = 0
        _calls_in_window += 1
        call_count += 1
        if _calls_in_window > _rate_limit_per_sec:
            raise KmsRateLimited("KMS rate limit exceeded (50 rps)")
    time.sleep(0.05)
    return {"kid_1": "secret_material"}


def reset():
    global _window_start, _calls_in_window, call_count
    with _lock:
        _window_start = 0.0
        _calls_in_window = 0
        call_count = 0
