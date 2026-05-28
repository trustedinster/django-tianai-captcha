"""
旋转验证码生成器。

生成旋转验证码，与 Java 版 StandardRotateImageCaptchaGenerator 对应。

工作原理：
1. 从资源库中随机选择一张背景图和一个模板
2. 在背景图中心位置生成一个圆形缺口
3. 从中心裁剪出圆形区域作为旋转图片
4. 将裁剪出的图片旋转一定角度
5. 用户需要旋转图片使缺口对齐

前端用户需要旋转滑块使图片恢复正确角度完成验证。
"""

import random
import math
import logging

from .base import ImageCaptchaGenerator
from .utils import CaptchaImageUtils
from ..conf import ROTATE

logger = logging.getLogger(__name__)


class StandardRotateImageCaptchaGenerator(ImageCaptchaGenerator):
    """
    标准旋转验证码生成器。

    与 Java 版 StandardRotateImageCaptchaGenerator 对应。
    """

    def __init__(self):
        self._resource_manager = None

    def set_resource_manager(self, resource_manager):
        self._resource_manager = resource_manager

    def generate_captcha_image(self, captcha_type=None, background_format="jpeg", template_format="png"):
        """
        生成旋转验证码图片。

        流程：
        1. 加载背景图和模板（active, fixed, mask）
        2. 计算中心位置
        3. 使用 mask 模板从背景图中心裁剪出旋转区域
        4. 将 fixed 模板叠加到背景图上形成缺口
        5. 计算随机旋转角度
        6. 创建旋转后的图片
        7. 构建并返回验证码信息

        Returns:
            dict: 验证码信息字典
        """
        if self._resource_manager is None:
            raise RuntimeError("Resource manager not set")

        # 1. 加载背景图
        bg_data = self._resource_manager.random_get_resource(ROTATE)
        bg_image = CaptchaImageUtils.load_image(bg_data).convert("RGBA")

        # 调整背景图大小
        bg_image = CaptchaImageUtils.resize_image(bg_image, 590, 360)
        bg_width, bg_height = bg_image.size

        # 2. 加载模板
        template = self._resource_manager.random_get_template(ROTATE)

        active_img = CaptchaImageUtils.load_image(template["active"]).convert("RGBA")
        fixed_img = CaptchaImageUtils.load_image(template["fixed"]).convert("RGBA")

        fixed_width, fixed_height = fixed_img.size

        # 3. 计算中心位置
        center_x = bg_width // 2 - fixed_width // 2
        center_y = bg_height // 2 - fixed_height // 2

        # 4. 从背景图中心裁剪
        cut_image = CaptchaImageUtils.cut_image_by_mask(bg_image, fixed_img, center_x, center_y)

        # 5. 将 fixed 模板叠加到背景图上
        bg_image = CaptchaImageUtils.overlay_image(bg_image, fixed_img, center_x, center_y)

        # 6. 将 active 模板叠加到裁剪图上
        cut_image = CaptchaImageUtils.overlay_image(cut_image, active_img, 0, 0)

        # 7. 计算随机旋转角度
        # 随机 X 偏移量，对应旋转角度
        random_x = random.randint(20, bg_width - 20)
        degree = 360 - (random_x / (bg_width / 360))

        # 8. 创建旋转后的图片
        # 旋转后的图片放在中心位置
        rotate_image = CaptchaImageUtils.center_overlay_and_rotate_image(
            CaptchaImageUtils.create_transparent_image(fixed_width, fixed_height),
            cut_image,
            0, 0,
            degree,
        )

        # 9. 转换为 Base64
        bg_base64 = CaptchaImageUtils.image_to_base64(bg_image, format=background_format)
        rotate_base64 = CaptchaImageUtils.image_to_base64(rotate_image, format=template_format)

        # 10. 构建返回数据
        result = {
            "backgroundImage": bg_base64,
            "templateImage": rotate_base64,
            "backgroundImageWidth": bg_width,
            "backgroundImageHeight": bg_height,
            "templateImageWidth": fixed_width,
            "templateImageHeight": fixed_height,
            "randomX": random_x,
            "type": ROTATE,
            "tolerant": 0.03,
            "data": {
                "degree": degree,
            },
        }

        return result
