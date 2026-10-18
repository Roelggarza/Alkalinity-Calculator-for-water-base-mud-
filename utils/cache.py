"""Redis-backed caching with graceful fallback.

REDIS_URL comes from the environment (Railway injects it). When Redis is
unavailable the functions just compute directly — the app never depends on it.

Used for:
  * caching dosing recommendations (shared across users/instances), and
  * counting failed sign-in attempts for the login gate.
"""
import hashlib
import json
import os

_client = None


def get_client():
    global _client
    url = os.environ.get("REDIS_URL")
    if not url:
        return None
    if _client is None:
        import redis
        _client = redis.Redis.from_url(url, socket_connect_timeout=3,
                                       socket_timeout=3)
    return _client


def _safe(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception:
        return None


def cached_recommendation(inp: dict) -> dict:
    """Dosing recommendation, cached 1h by input hash when Redis is up."""
    from utils.dosing import full_recommendation
    client = get_client()
    key = "dose:" + hashlib.sha256(
        json.dumps(inp, sort_keys=True, default=str).encode()).hexdigest()
    if client:
        hit = _safe(client.get, key)
        if hit:
            return json.loads(hit)
    rec = full_recommendation(inp)
    if client:
        _safe(client.setex, key, 3600, json.dumps(rec, default=str))
    return rec


def record_failed_login() -> int:
    """Increment failed-login counter (1h window). Returns current count."""
    client = get_client()
    if not client:
        return 0
    n = _safe(client.incr, "login:failed") or 0
    _safe(client.expire, "login:failed", 3600)
    return int(n)


def reset_failed_logins():
    client = get_client()
    if client:
        _safe(client.delete, "login:failed")
