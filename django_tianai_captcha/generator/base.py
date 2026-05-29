"""
验证码生成器基类。

定义验证码生成的接口规范，所有具体的生成器都需要继承此基类。
"""

from abc import ABC, abstractmethod


class ImageCaptchaGenerator(ABC):
    """
    验证码生成器接口。

    与 Java 版 ImageCaptchaGenerator 对应。
    每种验证码类型（滑块、旋转、滑动还原、文字点选）都需要实现此接口。
    """

    @abstractmethod
    def generate_captcha_image(self, captcha_type=None, background_format="jpeg", template_format="png"):
        """
        生成验证码图片。

        Args:
            captcha_type: 验证码类型（部分生成器可忽略此参数）
            background_format: 背景图片输出格式
            template_format: 模板图片输出格式

        Returns:
            dict: 验证码信息字典，包含：
                - backgroundImage: 背景图片 base64
                - templateImage: 模板图片 base64
                - backgroundImageWidth: 背景图片宽度
                - backgroundImageHeight: 背景图片高度
                - templateImageWidth: 模板图片宽度
                - templateImageHeight: 模板图片高度
                - randomX: 滑块/旋转的正确位置（用于验证，不返回给前端）
                - type: 验证码类型
                - tolerant: 容错值
                - data: 扩展数据
        """
        pass

    @abstractmethod
    def set_resource_manager(self, resource_manager):
        """设置资源管理器。"""
        pass
