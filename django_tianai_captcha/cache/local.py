"""
本地内存缓存实现。

基于 Python 字典 + 时间戳实现的本地缓存，适合单进程部署场景。
在多进程部署场景下，建议使用 RedisCacheStore。
"""

import time
import threading

from .base import CacheStore


class LocalCacheStore(CacheStore):
    """
    本地内存缓存实现。

    使用线程安全的字典存储缓存数据，每个条目包含过期时间戳。
    使用后台线程定期清理过期的缓存条目。

    注意：此实现仅适用于单进程部署，在多进程/多实例部署场景下，
    不同进程之间的缓存不共享，建议使用 RedisCacheStore。
    """

    def __init__(self, cleanup_interval=60):
        """
        初始化本地缓存。

        Args:
            cleanup_interval: 过期缓存清理间隔（秒），默认 60 秒
        """
        self._store = {}
        self._lock = threading.Lock()
        self._cleanup_interval = cleanup_interval
        self._running = True

        # 启动清理线程
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True,
            name="captcha-cache-cleanup",
        )
        self._cleanup_thread.start()

    def _cleanup_loop(self):
        """后台定期清理过期的缓存条目。"""
        while self._running:
            try:
                time.sleep(self._cleanup_interval)
                self._cleanup_expired()
            except Exception:
                pass

    def _cleanup_expired(self):
        """清理所有过期的缓存条目。"""
        now = time.time()
        with self._lock:
            expired_keys = [
                k for k, v in self._store.items()
                if v.get("_expire_at", 0) < now
            ]
            for k in expired_keys:
                del self._store[k]

    def _is_expired(self, entry):
        """检查缓存条目是否已过期。"""
        expire_at = entry.get("_expire_at", 0)
        return expire_at > 0 and time.time() > expire_at

    def get_cache(self, key):
        """获取缓存数据（数据保留）。"""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if self._is_expired(entry):
                del self._store[key]
                return None
            # 返回数据的副本，避免外部修改影响缓存
            return {k: v for k, v in entry.items() if not k.startswith("_")}

    def get_and_remove_cache(self, key):
        """获取并删除缓存数据（一次性读取）。"""
        with self._lock:
            entry = self._store.pop(key, None)
            if entry is None:
                return None
            if self._is_expired(entry):
                return None
            return {k: v for k, v in entry.items() if not k.startswith("_")}

    def set_cache(self, key, data, expire):
        """设置缓存数据。"""
        with self._lock:
            entry = dict(data)
            entry["_expire_at"] = time.time() + expire if expire > 0 else 0
            self._store[key] = entry
        return True

    def incr(self, key, delta=1, expire=3600):
        """自增计数器。"""
        with self._lock:
            entry = self._store.get(key)
            if entry is None or self._is_expired(entry):
                self._store[key] = {
                    "_incr": delta,
                    "_expire_at": time.time() + expire,
                }
                return delta
            else:
                current = entry.get("_incr", 0)
                new_val = current + delta
                entry["_incr"] = new_val
                entry["_expire_at"] = time.time() + expire
                return new_val

    def delete_cache(self, key):
        """删除缓存数据。"""
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def exists(self, key):
        """检查缓存 key 是否存在。"""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return False
            if self._is_expired(entry):
                del self._store[key]
                return False
            return True

    def close(self):
        """关闭缓存，停止清理线程。"""
        self._running = False
        self._store.clear()
