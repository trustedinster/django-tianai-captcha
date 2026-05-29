"""
滑动还原验证码生成器。

生成滑动还原验证码，与 Java 版 StandardConcatImageCaptchaGenerator 对应。

工作原理：
1. 加载一张背景图
2. 在垂直方向上选择一个分割点，将背景图分为上方大块和下方小条
3. 在上方大块水平方向上选择一个分割点分为左右两部分
4. 交换上方大块的左右部分
5. 重新拼接为打乱后的背景图
6. 用户需要滑动使图片还原为原始顺序

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

        流程（与 Java 版保持一致）：
        1. 加载背景图
        2. 在垂直方向选择分割点，将图片分为上方大块和下方小条
           - Java 版 splitImage(randomY, true, bgImage) 中 direction=true 表示水平切割
           - splitImageArr[0] 是上方大块 (height - randomY 高度)
           - splitImageArr[1] 是下方小条 (randomY 高度)
        3. 在上方大块水平方向选择分割点分为左右两部分
        4. 交换上方大块的左右部分（右+左）
        5. 垂直拼接：交换后的上方大块 + 下方小条
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
        # 与 Java 版保持一致
        # spacingY = bgImage.getHeight() / 4
        # randomY = randomInt(spacingY, bgImage.getHeight() - spacingY)
        spacing_y = bg_height // 4
        random_y = random.randint(spacing_y, bg_height - spacing_y)

        # spacingX = bgImage.getWidth() / 8
        # randomX = randomInt(spacingX, bgImage.getWidth() - bgImage.getWidth() / 5)
        spacing_x = bg_width // 8
        random_x = random.randint(spacing_x, bg_width - bg_width // 5)

        # 3. 垂直分割为上方大块和下方小条
        # Java版: splitImage(randomY, true, bgImage) → [topBigPart, bottomSmallStrip]
        # topBigPart 高度 = bg_height - random_y
        # bottomSmallStrip 高度 = random_y
        top_big_part = bg_image.crop((0, 0, bg_width, bg_height - random_y))
        bottom_strip = bg_image.crop((0, bg_height - random_y, bg_width, bg_height))

        # 4. 水平分割上方大块为左右两部分
        # Java版: splitImage(randomX, false, topBigPart) → [leftPart, rightPart]
        # direction=false 表示垂直切割（左右切）
        top_left = top_big_part.crop((0, 0, random_x, top_big_part.height))
        top_right = top_big_part.crop((random_x, 0, top_big_part.width, top_big_part.height))

        # 5. 交换上方大块的左右位置（右+左）
        # Java版: concatImage(true, totalWidth, height, rightPart, leftPart)
        # direction=true 表示水平拼接
        swapped_top = CaptchaImageUtils.concat_images(top_right, top_left, direction="horizontal")

        # 6. 垂直拼接：交换后的上方大块 + 下方小条
        # Java版: concatImage(false, width, totalHeight, sliderImage, bottomPart)
        shuffled_bg = CaptchaImageUtils.concat_images(swapped_top, bottom_strip, direction="vertical")

        # 7. 转换为 Base64
        bg_base64 = CaptchaImageUtils.image_to_base64(shuffled_bg, format=background_format)

        # 8. 构建返回数据
        # 前端 concat.js 读取 data.data.randomY:
        #   var height = ((backgroundImageHeight - data.data.data.randomY) / backgroundImageHeight) * 180;
        # 所以 randomY 必须放在 data.randomY 路径下
        result = {
            "backgroundImage": bg_base64,
            "templateImage": None,
            "backgroundImageWidth": bg_width,
            "backgroundImageHeight": bg_height,
            "templateImageWidth": None,
            "templateImageHeight": None,
            "randomX": random_x,
            "type": CONCAT,
            "tolerant": 0.05,
            "data": {
                "randomY": random_y,
            },
        }

        return result
