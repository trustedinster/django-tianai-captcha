"""
滑块验证码生成器。

生成滑块拼图验证码，与 Java 版 StandardSliderImageCaptchaGenerator 对应。

工作原理：
1. 从资源库中随机选择一张背景图和一个模板
2. 在背景图上随机位置生成一个缺口（使用模板 fixed 图片）
3. 从背景图缺口位置裁剪出滑块图片（使用模板 mask 图片）
4. 在滑块图片上叠加模板 active 图片（装饰效果）
5. 返回带有缺口的背景图和滑块图片

前端用户需要将滑块拖动到缺口位置完成验证。
"""

import random
import logging

from .base import ImageCaptchaGenerator
from .utils import CaptchaImageUtils
from ..conf import SLIDER

logger = logging.getLogger(__name__)


class StandardSliderImageCaptchaGenerator(ImageCaptchaGenerator):
    """
    标准滑块验证码生成器。

    与 Java 版 StandardSliderImageCaptchaGenerator 对应。
    """

    def __init__(self):
        self._resource_manager = None

    def set_resource_manager(self, resource_manager):
        self._resource_manager = resource_manager

    def generate_captcha_image(self, captcha_type=None, background_format="jpeg", template_format="png"):
        """
        生成滑块验证码图片。

        流程：
        1. 加载背景图和模板（active, fixed, mask）
        2. 计算随机缺口位置 (randomX, randomY)
        3. 使用 mask 模板从背景图裁剪出滑块区域
        4. 将 fixed 模板叠加到背景图上形成缺口
        5. 将 active 模板叠加到裁剪出的滑块上
        6. 构建并返回验证码信息

        Returns:
            dict: 验证码信息字典
        """
        if self._resource_manager is None:
            raise RuntimeError("Resource manager not set")

        # 1. 加载背景图
        bg_data = self._resource_manager.random_get_resource(SLIDER)
        bg_image = CaptchaImageUtils.load_image(bg_data).convert("RGBA")

        # 调整背景图大小（与 Java 版保持一致 590x360）
        bg_image = CaptchaImageUtils.resize_image(bg_image, 590, 360)
        bg_width, bg_height = bg_image.size

        # 2. 加载模板
        template = self._resource_manager.random_get_template(SLIDER)

        # 加载模板图片
        active_img = CaptchaImageUtils.load_image(template["active"]).convert("RGBA")
        fixed_img = CaptchaImageUtils.load_image(template["fixed"]).convert("RGBA")

        fixed_width, fixed_height = fixed_img.size

        # 3. 计算随机位置
        # randomX: 缺口 X 坐标，确保在有效范围内
        random_x = random.randint(fixed_width + 5, bg_width - fixed_width - 10)
        # randomY: 缺口 Y 坐标，垂直居中附近
        random_y = random.randint(5, bg_height - fixed_height - 5)

        # 4. 使用 fixed 模板从背景图裁剪出滑块区域
        cut_image = CaptchaImageUtils.cut_image_by_mask(bg_image, fixed_img, random_x, random_y)

        # 5. 将 fixed 模板叠加到背景图上形成缺口
        bg_image = CaptchaImageUtils.overlay_image(bg_image, fixed_img, random_x, random_y)

        # 6. 将 active 模板叠加到裁剪出的滑块上（装饰效果）
        slider_piece = CaptchaImageUtils.overlay_image(cut_image, active_img, 0, 0)

        # 7. 创建滑块图片矩阵
        # 滑块图片与背景图同高，宽度为模板宽度
        slider_image = CaptchaImageUtils.create_transparent_image(fixed_width, bg_height)
        slider_image = CaptchaImageUtils.overlay_image(slider_image, slider_piece, 0, random_y)

        # 8. 转换为 Base64
        bg_base64 = CaptchaImageUtils.image_to_base64(bg_image, format=background_format)
        slider_base64 = CaptchaImageUtils.image_to_base64(slider_image, format=template_format)

        # 9. 构建返回数据
        result = {
            "backgroundImage": bg_base64,
            "templateImage": slider_base64,
            "backgroundImageWidth": bg_width,
            "backgroundImageHeight": bg_height,
            "templateImageWidth": fixed_width,
            "templateImageHeight": bg_height,
            "randomX": random_x,
            "type": SLIDER,
            "tolerant": 0.02,
            "data": {
                "y": random_y,
            },
        }

        return result
