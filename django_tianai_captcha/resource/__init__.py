"""
资源管理模块初始化。

提供验证码资源的存储和管理功能，包括背景图片、模板图片和字体等资源。
"""

from .store import ResourceStore, LocalMemoryResourceStore
from .manager import DefaultImageCaptchaResourceManager, DefaultBuiltInResources
from .provider import Resource, ResourceProvider, ClassPathResourceProvider, FileResourceProvider, URLResourceProvider

__all__ = [
    "ResourceStore",
    "LocalMemoryResourceStore",
    "DefaultImageCaptchaResourceManager",
    "DefaultBuiltInResources",
    "Resource",
    "ResourceProvider",
    "ClassPathResourceProvider",
    "FileResourceProvider",
    "URLResourceProvider",
]
