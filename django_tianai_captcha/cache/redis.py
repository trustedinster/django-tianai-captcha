"""
Redis 缓存实现。

基于 Redis 的分布式缓存实现，适合多进程/多实例部署场景。
使用 Django 的 cache framework 或直接连接 Redis。
"""

import json
import logging

from .base import CacheStore

logger = logging.getLogger(__name__)


class RedisCacheStore(CacheStore):
    """
    Redis 缓存实现。

    支持两种 Redis 连接方式：
    1. 使用 Django 的 cache framework（settings.CACHES 配置）
    2. 使用 redis-py 直接连接（通过 REDIS_URL）

    在多进程/多实例部署场景下，推荐使用此实现以确保缓存一致性。
    """

    def __init__(self, redis_url=None):
        """
        初始化 Redis 缓存。

        优先尝试使用 Django cache framework，如果不可用则回退到 redis-py。

        Args:
            redis_url: Redis 连接 URL，如 "redis://localhost:6379/0"
        """
        self._redis_url = redis_url
        self._client = None
        self._django_cache = None

        # 优先尝试 Django cache
        try:
            from django.core.cache import cache

            # 测试连接是否可用
            cache.set("_captcha_test", "1", 1)
            if cache.get("_captcha_test") == "1":
                self._django_cache = cache
                logger.info("Using Django cache framework for captcha storage")
                return
        except Exception:
            pass

        # 回退到 redis-py
        try:
            import redis

            self._client = redis.from_url(self._redis_url or "redis://localhost:6379/0")
            self._client.ping()
            logger.info(f"Using redis-py for captcha storage: {self._redis_url}")
        except ImportError:
            logger.warning(
                "redis-py not installed. Install with: pip install redis"
            )
            raise
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            raise

    def _serialize(self, data):
        """序列化数据为 JSON 字符串。"""
        return json.dumps(data, ensure_ascii=False)

    def _deserialize(self, data_str):
        """反序列化 JSON 字符串为字典。"""
        if data_str is None:
            return None
        if isinstance(data_str, bytes):
            data_str = data_str.decode("utf-8")
        return json.loads(data_str)

    def get_cache(self, key):
        """获取缓存数据。"""
        try:
            if self._django_cache:
                return self._django_cache.get(key)
            else:
                data_str = self._client.get(key)
                return self._deserialize(data_str)
        except Exception as e:
            logger.error(f"Redis get_cache error for key {key}: {e}")
            return None

    def get_and_remove_cache(self, key):
        """获取并删除缓存数据。"""
        try:
            if self._django_cache:
                data = self._django_cache.get(key)
                if data is not None:
                    self._django_cache.delete(key)
                return data
            else:
                pipe = self._client.pipeline()
                pipe.get(key)
                pipe.delete(key)
                results = pipe.execute()
                data_str = results[0]
                return self._deserialize(data_str)
        except Exception as e:
            logger.error(f"Redis get_and_remove_cache error for key {key}: {e}")
            return None

    def set_cache(self, key, data, expire):
        """设置缓存数据。"""
        try:
            if self._django_cache:
                self._django_cache.set(key, data, expire)
                return True
            else:
                self._client.setex(key, expire, self._serialize(data))
                return True
        except Exception as e:
            logger.error(f"Redis set_cache error for key {key}: {e}")
            return False

    def incr(self, key, delta=1, expire=3600):
        """自增计数器。"""
        try:
            if self._django_cache:
                # Django cache 不原生支持 incr with expire
                current = self._django_cache.get(key, 0)
                new_val = current + delta
                self._django_cache.set(key, new_val, expire)
                return new_val
            else:
                pipe = self._client.pipeline()
                pipe.incr(key, delta)
                pipe.expire(key, expire)
                results = pipe.execute()
                return results[0]
        except Exception as e:
            logger.error(f"Redis incr error for key {key}: {e}")
            # key 不存在时创建
            if self._django_cache:
                self._django_cache.set(key, delta, expire)
            else:
                self._client.setex(key, expire, str(delta))
            return delta

    def delete_cache(self, key):
        """删除缓存数据。"""
        try:
            if self._django_cache:
                self._django_cache.delete(key)
                return True
            else:
                self._client.delete(key)
                return True
        except Exception as e:
            logger.error(f"Redis delete_cache error for key {key}: {e}")
            return False

    def exists(self, key):
        """检查缓存 key 是否存在。"""
        try:
            if self._django_cache:
                return self._django_cache.get(key) is not None
            else:
                return self._client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False

    def close(self):
        """关闭 Redis 连接。"""
        if self._client:
            self._client.close()
