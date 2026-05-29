"""
缓存存储基类。

定义缓存存储的接口规范，与 Java 版 CacheStore 对应。
所有缓存实现必须继承此基类并实现所有抽象方法。
"""

from abc import ABC, abstractmethod


class CacheStore(ABC):
    """
    验证码缓存存储接口。

    提供验证码校验数据的缓存功能，支持设置过期时间。
    支持两种读取模式：
    - get_cache: 普通读取（数据保留）
    - get_and_remove_cache: 一次性读取（数据删除，用于验证码的一次性校验）
    """

    @abstractmethod
    def get_cache(self, key):
        """
        获取缓存数据。

        Args:
            key: 缓存 key

        Returns:
            缓存的数据字典，如果 key 不存在返回 None
        """
        pass

    @abstractmethod
    def get_and_remove_cache(self, key):
        """
        获取并删除缓存数据（一次性读取）。

        验证码校验使用此方法，确保同一验证码只能校验一次，
        防止重放攻击。

        Args:
            key: 缓存 key

        Returns:
            缓存的数据字典，如果 key 不存在返回 None
        """
        pass

    @abstractmethod
    def set_cache(self, key, data, expire):
        """
        设置缓存数据。

        Args:
            key: 缓存 key
            data: 要缓存的数据字典
            expire: 过期时间（秒）

        Returns:
            bool: 是否设置成功
        """
        pass

    @abstractmethod
    def incr(self, key, delta=1, expire=3600):
        """
        自增计数器。

        用于限制验证码请求频率等场景。

        Args:
            key: 缓存 key
            delta: 自增量，默认为 1
            expire: 过期时间（秒）

        Returns:
            int: 自增后的值
        """
        pass

    @abstractmethod
    def delete_cache(self, key):
        """
        删除缓存数据。

        Args:
            key: 缓存 key

        Returns:
            bool: 是否删除成功
        """
        pass

    @abstractmethod
    def exists(self, key):
        """
        检查缓存 key 是否存在。

        Args:
            key: 缓存 key

        Returns:
            bool: key 是否存在
        """
        pass
