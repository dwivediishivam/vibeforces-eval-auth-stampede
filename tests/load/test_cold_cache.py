"""Failing load test — proves the cache stampede.

Agent must edit auth/keys.py so this passes. Acceptable solutions:
  - request coalescing (single-flight) around the kms_fetch call
  - distributed lock + double-checked-locking pattern
  - jittered TTL alone is NOT sufficient
"""
import threading
import time

import kms_stub
from auth.keys import get_signing_keys, redis


def test_p99_under_500ms():
    redis._store.clear()
    kms_stub.reset()
    latencies = []
    errors = []
    lat_lock = threading.Lock()

    def worker():
        start = time.monotonic()
        try:
            get_signing_keys()
        except Exception as exc:
            errors.append(repr(exc))
        end = time.monotonic()
        with lat_lock:
            latencies.append(end - start)

    threads = [threading.Thread(target=worker) for _ in range(300)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"{len(errors)} requests errored: {errors[:3]}"
    latencies.sort()
    p99 = latencies[int(len(latencies) * 0.99) - 1]
    assert p99 < 0.5, f"p99 latency {p99*1000:.0f}ms exceeded 500ms"
    assert kms_stub.call_count <= 5, (
        f"KMS hit {kms_stub.call_count} times — request coalescing not in place"
    )
