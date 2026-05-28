"""
滑动还原验证码生成器。

生成滑动还原验证码，与 Java 版 StandardConcatImageCaptchaGenerator 对应。

工作原理：
1. 加载一张背景图
2. 在水平方向上选择一个分割点，将背景图上半部分沿该点分割为左右两部分
3. 交换左右两部分的位置
4. 用户需要滑动使图片还原为原始顺序

与滑块验证码不同，滑动还原没有缺口和滑块拼图，
而是将背景图本身打乱，用户需要还原。
"""

import random
import logging

from .base import ImageCaptchaGenerator
from .utils import CaptchaImageUtils
from ..conf import CONCAT

logger = logging.getLogger(__name__)


class StandardConcatImageCaptchaGenerator(ImageCaptchaGenerator):
    """
    标准滑动还原验证码生成器。

    与 Java 版 StandardConcatImageCaptchaGenerator 对应。
    """

    def __init__(self):
        self._resource_manager = None

    def set_resource_manager(self, resource_manager):
        self._resource_manager = resource_manager

    def generate_captcha_image(self, captcha_type=None, background_format="jpeg", template_format="png"):
        """
        生成滑动还原验证码图片。

        流程：
        1. 加载背景图
        2. 在垂直方向选择分割点将图片分为上下两部分
        3. 在上半部分水平方向选择分割点分为左右两部分
        4. 交换上半部分的左右部分
        5. 重新拼接为打乱后的背景图
        6. 构建并返回验证码信息

        Returns:
            dict: 验证码信息字典
        """
        if self._resource_manager is None:
            raise RuntimeError("Resource manager not set")

        # 1. 加载背景图
        bg_data = self._resource_manager.random_get_resource(CONCAT)
        bg_image = CaptchaImageUtils.load_image(bg_data).convert("RGBA")

        # 调整背景图大小
        bg_image = CaptchaImageUtils.resize_image(bg_image, 590, 360)
        bg_width, bg_height = bg_image.size

        # 2. 计算随机分割点
        # 水平分割点（X）：在 1/8 到 4/5 宽度之间
        random_x = random.randint(bg_width // 8, int(bg_width * 4 / 5))
        # 垂直分割点（Y）：在 1/4 到 3/4 高度之间
        random_y = random.randint(bg_height // 4, int(bg_height * 3 / 4))

        # 3. 垂直分割为上下两部分
        top_part, bottom_part = CaptchaImageUtils.split_image(bg_image, random_y, direction="horizontal")

        # 4. 水平分割上半部分为左右两部分
        top_left, top_right = CaptchaImageUtils.split_image(top_part, random_x, direction="vertical")

        # 5. 交换上半部分的左右位置（右+左）
        swapped_top = CaptchaImageUtils.concat_images(top_right, top_left, direction="horizontal")

        # 6. 垂直拼接：交换后的上半部分 + 下半部分
        shuffled_bg = CaptchaImageUtils.concat_images(swapped_top, bottom_part, direction="vertical")

        # 7. 转换为 Base64
        bg_base64 = CaptchaImageUtils.image_to_base64(shuffled_bg, format=background_format)

        # 滑动还原的 templateImage 就是打乱后的背景图的滑块轨道
        # 创建一个与背景同宽的透明图片作为模板
        template_image = CaptchaImageUtils.create_transparent_image(bg_width, bg_height)
        template_base64 = CaptchaImageUtils.image_to_base64(template_image, format=template_format)

        # 8. 构建返回数据
        result = {
            "backgroundImage": bg_base64,
            "templateImage": template_base64,
            "backgroundImageWidth": bg_width,
            "backgroundImageHeight": bg_height,
            "templateImageWidth": bg_width,
            "templateImageHeight": bg_height,
            "randomX": random_x,
            "type": CONCAT,
            "tolerant": 0.05,
            "data": {
                "viewData": {
                    "randomY": random_y,
                },
            },
        }

        return result
