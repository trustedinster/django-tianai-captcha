"""
资源管理器模块。

负责资源的加载和检索，协调 ResourceStore 和 ResourceProvider 的交互。
"""

import os
import logging

from .store import LocalMemoryResourceStore
from .provider import Resource, load_resource

logger = logging.getLogger(__name__)


class DefaultImageCaptchaResourceManager:
    """
    默认验证码资源管理器。

    协调 ResourceStore 和 ResourceProvider 的工作：
    - 通过 ResourceStore 管理资源的元数据
    - 通过 ResourceProvider 加载资源的实际数据

    与 Java 版 DefaultImageCaptchaResourceManager 对应。
    """

    def __init__(self, resource_store=None):
        """
        初始化资源管理器。

        Args:
            resource_store: ResourceStore 实例，默认使用 LocalMemoryResourceStore
        """
        self._resource_store = resource_store or LocalMemoryResourceStore()
        self._resource_store.init(self)

    def random_get_resource(self, captcha_type, tag=None):
        """
        随机获取一个背景资源并加载。

        Args:
            captcha_type: 验证码类型
            tag: 资源标签

        Returns:
            bytes: 背景图片的原始数据

        Raises:
            ValueError: 没有可用的资源
        """
        resources = self._resource_store.random_get_resource_by_type_and_tag(
            captcha_type, tag, quantity=1
        )
        if not resources:
            raise ValueError(f"No resource available for type: {captcha_type}, tag: {tag}")

        return load_resource(resources[0])

    def random_get_template(self, captcha_type, tag=None):
        """
        随机获取一个模板资源字典。

        Args:
            captcha_type: 验证码类型
            tag: 模板标签

        Returns:
            dict: 模板字典，包含 active, fixed, mask 等键

        Raises:
            ValueError: 没有可用的模板
        """
        templates = self._resource_store.random_get_template_by_type_and_tag(
            captcha_type, tag, quantity=1
        )
        if not templates:
            raise ValueError(f"No template available for type: {captcha_type}, tag: {tag}")

        template = templates[0]

        # 加载模板中的图片资源
        result = {}
        for key, resource in template.items():
            if isinstance(resource, Resource):
                result[key] = load_resource(resource)
            else:
                result[key] = resource

        return result

    def add_resource(self, captcha_type, resource):
        """
        添加背景资源。

        Args:
            captcha_type: 验证码类型
            resource: Resource 实例
        """
        self._resource_store.add_resource(captcha_type, resource)

    def add_template(self, captcha_type, template_dict, tag=None):
        """
        添加模板资源。

        Args:
            captcha_type: 验证码类型
            template_dict: 模板字典
            tag: 模板标签
        """
        self._resource_store.add_template(captcha_type, template_dict, tag)

    def add_font(self, resource):
        """
        添加字体资源。

        Args:
            resource: 字体 Resource 实例
        """
        self._resource_store.add_font(resource)

    @property
    def resource_store(self):
        return self._resource_store


class DefaultBuiltInResources:
    """
    系统自带默认资源初始化器。

    加载插件自带的背景图片和模板，与 Java 版 DefaultBuiltInResources 对应。
    """

    PATH_PREFIX = "META-INF/cut-image"

    @classmethod
    def init(cls, resource_store):
        """
        初始化默认资源。

        加载自带的背景图片和滑块/旋转模板到资源存储中。

        Args:
            resource_store: ResourceStore 实例
        """
        from ..conf import SLIDER, ROTATE, CONCAT, WORD_IMAGE_CLICK

        # 扫描资源目录，自动注册所有背景图片
        resource_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "resources", "META-INF", "cut-image", "resource"
        )
        image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
        image_files = sorted([
            f for f in os.listdir(resource_dir)
            if f.lower().endswith(image_extensions)
        ])

        if not image_files:
            logger.warning("No background images found in %s", resource_dir)
        else:
            for filename in image_files:
                resource_image = f"META-INF/cut-image/resource/{filename}"
                for captcha_type in [SLIDER, ROTATE, CONCAT, WORD_IMAGE_CLICK]:
                    resource = Resource(type="classpath", data=resource_image)
                    resource_store.add_resource(captcha_type, resource)
            logger.info("Registered %d background images for each captcha type", len(image_files))

        # 添加滑块模板
        for template_name in ["slider_1", "slider_2"]:
            active = Resource(type="classpath", data=f"META-INF/cut-image/template/{template_name}/active.png")
            fixed = Resource(type="classpath", data=f"META-INF/cut-image/template/{template_name}/fixed.png")
            template_dict = {
                "active": active,
                "fixed": fixed,
            }
            resource_store.add_template(SLIDER, template_dict)

        # 添加旋转模板
        active = Resource(type="classpath", data="META-INF/cut-image/template/rotate_1/active.png")
        fixed = Resource(type="classpath", data="META-INF/cut-image/template/rotate_1/fixed.png")
        template_dict = {
            "active": active,
            "fixed": fixed,
        }
        resource_store.add_template(ROTATE, template_dict)

        # 添加默认字体
        font_resource = Resource(type="classpath", data="META-INF/cut-image/template/fonts/SIMSUN.TTC")
        resource_store.add_font(font_resource)

        logger.info("Default built-in resources initialized")
