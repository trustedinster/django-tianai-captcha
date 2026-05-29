"""
资源提供者和资源模型。

定义资源的加载方式和数据模型，支持从文件系统、Python 包内和 URL 加载资源。
"""

import uuid
import io
import os
import logging

logger = logging.getLogger(__name__)


class Resource:
    """
    资源数据模型。

    表示一个验证码资源（背景图片、模板图片或字体文件），
    通过 type 和 data 描述资源的加载方式。

    与 Java 版 Resource 对应。

    Attributes:
        id: 资源唯一标识
        type: 资源提供者类型（classpath/file/url）
        data: 资源路径或 URL
        tag: 资源标签（用于分类过滤）
        tip: 提示文本
        extra: 扩展数据
    """

    def __init__(self, type=None, data=None, tag=None, tip=None, extra=None, id=None):
        self.id = id or uuid.uuid4().hex[:8]
        self.type = type or "file"
        self.data = data
        self.tag = tag
        self.tip = tip
        self.extra = extra

    def __repr__(self):
        return f"Resource(id={self.id}, type={self.type}, data={self.data}, tag={self.tag})"


class ResourceProvider:
    """
    资源提供者基类。

    定义资源加载的接口规范，每种加载方式（文件系统、包内、URL）
    都需要实现此接口。
    """

    SUPPORTED_TYPES = []

    @classmethod
    def supports(cls, resource_type):
        """检查是否支持指定的资源类型。"""
        return resource_type in cls.SUPPORTED_TYPES

    def load(self, resource):
        """
        加载资源。

        Args:
            resource: Resource 实例

        Returns:
            bytes: 资源的原始二进制数据
        """
        raise NotImplementedError


class ClassPathResourceProvider(ResourceProvider):
    """
    Python 包内资源提供者。

    从 Python 包的目录中加载资源文件，类似 Java 的 classpath 加载方式。
    data 格式为相对于包根目录的路径，如 "META-INF/cut-image/resource/1.jpg"。
    """

    SUPPORTED_TYPES = ["classpath"]

    def load(self, resource):
        """从包目录加载资源。"""
        # 包内资源的基础目录
        base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources")
        file_path = os.path.join(base_dir, resource.data)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Classpath resource not found: {file_path}")

        with open(file_path, "rb") as f:
            return f.read()


class FileResourceProvider(ResourceProvider):
    """
    文件系统资源提供者。

    从本地文件系统加载资源文件，data 为文件的绝对路径或相对路径。
    """

    SUPPORTED_TYPES = ["file"]

    def load(self, resource):
        """从文件系统加载资源。"""
        if not os.path.exists(resource.data):
            raise FileNotFoundError(f"File resource not found: {resource.data}")

        with open(resource.data, "rb") as f:
            return f.read()


class URLResourceProvider(ResourceProvider):
    """
    URL 资源提供者。

    从网络 URL 加载资源文件。
    """

    SUPPORTED_TYPES = ["url"]

    def load(self, resource):
        """从 URL 加载资源。"""
        import urllib.request

        try:
            with urllib.request.urlopen(resource.data, timeout=10) as resp:
                return resp.read()
        except Exception as e:
            raise IOError(f"Failed to load URL resource: {resource.data}, error: {e}")


# 资源提供者注册表
_PROVIDERS = {
    "classpath": ClassPathResourceProvider(),
    "file": FileResourceProvider(),
    "url": URLResourceProvider(),
}


def get_provider(resource_type):
    """
    获取指定类型的资源提供者。

    Args:
        resource_type: 资源类型

    Returns:
        ResourceProvider 实例

    Raises:
        ValueError: 不支持的资源类型
    """
    provider = _PROVIDERS.get(resource_type)
    if provider is None:
        raise ValueError(f"Unsupported resource type: {resource_type}, "
                         f"supported types: {list(_PROVIDERS.keys())}")
    return provider


def load_resource(resource):
    """
    加载资源数据。

    根据资源的 type 属性自动选择合适的 ResourceProvider 进行加载。

    Args:
        resource: Resource 实例

    Returns:
        bytes: 资源的原始二进制数据
    """
    provider = get_provider(resource.type)
    return provider.load(resource)
