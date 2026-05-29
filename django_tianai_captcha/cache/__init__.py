"""
缓存模块初始化。

提供验证码缓存存储的工厂方法，支持本地缓存和 Redis 缓存两种后端。
"""

from .base import CacheStore
from .local import LocalCacheStore
from .redis import RedisCacheStore


def get_cache_store():
    """
    根据配置获取缓存存储实例。

    Returns:
        CacheStore 实例
    """
    from ..conf import get_setting

    backend = get_setting("CACHE_BACKEND")
    if backend == "redis":
        redis_url = get_setting("REDIS_URL")
        return RedisCacheStore(redis_url)
    else:
        return LocalCacheStore()


__all__ = [
    "CacheStore",
    "LocalCacheStore",
    "RedisCacheStore",
    "get_cache_store",
]
