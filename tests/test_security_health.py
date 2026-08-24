from backend.core.security import RateLimiter, hash_token, valid_bearer
from backend.platform.health import HealthMonitor


def test_rate_limiter_blocks_after_limit():
    limiter = RateLimiter(limit=2, window=60)
    assert limiter.allow("x")
    assert limiter.allow("x")
    assert not limiter.allow("x")


def test_auth_disabled_by_default():
    assert valid_bearer(None, None)


def test_hash_is_deterministic():
    assert hash_token("abc") == hash_token("abc")
    assert hash_token("abc") != hash_token("def")


def test_health_monitor():
    monitor = HealthMonitor()
    monitor.request()
    monitor.request(error=True)
    data = monitor.snapshot()
    assert data["counters"]["requests"] == 2
    assert data["counters"]["errors"] == 1
