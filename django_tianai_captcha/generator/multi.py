"""
多类型验证码生成器。

根据验证码类型分发到对应的具体生成器，与 Java 版 MultiImageCaptchaGenerator 对应。
"""

import logging

from .base import ImageCaptchaGenerator
from .slider import StandardSliderImageCaptchaGenerator
from .rotate import StandardRotateImageCaptchaGenerator
from .concat import StandardConcatImageCaptchaGenerator
from .word_click import StandardWordClickImageCaptchaGenerator
from ..conf import SLIDER, ROTATE, CONCAT, WORD_IMAGE_CLICK

logger = logging.getLogger(__name__)


class MultiImageCaptchaGenerator(ImageCaptchaGenerator):
    """
    多类型验证码生成器。

    根据验证码类型选择对应的生成器进行生成。
    支持的验证码类型：
    - SLIDER: 滑块验证码
    - ROTATE: 旋转验证码
    - CONCAT: 滑动还原验证码
    - WORD_IMAGE_CLICK: 文字点选验证码

    与 Java 版 MultiImageCaptchaGenerator 对应。
    """

    def __init__(self, resource_manager=None):
        """
        初始化多类型生成器。

        Args:
            resource_manager: 资源管理器
        """
        self._resource_manager = resource_manager
        self._generators = {}
        self._init_generators()

    def _init_generators(self):
        """注册所有验证码类型的生成器。"""
        generator_classes = {
            SLIDER: StandardSliderImageCaptchaGenerator,
            ROTATE: StandardRotateImageCaptchaGenerator,
            CONCAT: StandardConcatImageCaptchaGenerator,
            WORD_IMAGE_CLICK: StandardWordClickImageCaptchaGenerator,
        }

        for captcha_type, generator_class in generator_classes.items():
            generator = generator_class()
            if self._resource_manager:
                generator.set_resource_manager(self._resource_manager)
            self._generators[captcha_type] = generator

    def generate_captcha_image(self, captcha_type=None, background_format="jpeg", template_format="png"):
        """
        根据类型生成验证码图片。

        Args:
            captcha_type: 验证码类型
            background_format: 背景图片格式
            template_format: 模板图片格式

        Returns:
            dict: 验证码信息字典

        Raises:
            ValueError: 不支持的验证码类型
        """
        if captcha_type is None:
            captcha_type = SLIDER

        generator = self._generators.get(captcha_type)
        if generator is None:
            raise ValueError(f"Unsupported captcha type: {captcha_type}")

        return generator.generate_captcha_image(
            background_format=background_format,
            template_format=template_format,
        )

    def set_resource_manager(self, resource_manager):
        """设置资源管理器，同时更新所有子生成器。"""
        self._resource_manager = resource_manager
        for generator in self._generators.values():
            generator.set_resource_manager(resource_manager)
