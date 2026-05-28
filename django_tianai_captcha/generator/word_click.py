"""
文字点选验证码生成器。

生成文字点选验证码，与 Java 版 StandardWordClickImageCaptchaGenerator 对应。

工作原理：
1. 加载一张背景图
2. 随机选择若干汉字作为需要点击的目标文字
3. 在背景图上随机位置绘制这些文字（带旋转和颜色）
4. 同时绘制一些干扰文字
5. 生成提示图片，显示需要按顺序点击的汉字
6. 用户需要按照提示顺序依次点击背景图上对应的文字

前端用户需要按照提示图片中汉字的顺序，依次点击背景图上对应的文字位置。
"""

import random
import os
import logging

from .base import ImageCaptchaGenerator
from .utils import CaptchaImageUtils
from ..conf import WORD_IMAGE_CLICK

logger = logging.getLogger(__name__)

# 常用汉字表
COMMON_CHINESE_CHARS = [
    "的", "一", "是", "了", "不", "在", "人", "有", "我", "他",
    "这", "中", "大", "来", "上", "国", "个", "到", "说", "们",
    "为", "子", "和", "你", "地", "出", "会", "也", "时", "能",
    "对", "下", "那", "要", "看", "天", "得", "里", "去", "么",
    "起", "都", "把", "好", "还", "多", "没", "为", "又", "可",
    "家", "学", "只", "以", "主", "当", "样", "事", "想", "没",
    "用", "她", "生", "那", "样", "知", "已", "给", "明", "几",
    "定", "做", "种", "理", "花", "小", "目", "点", "心", "然",
    "山", "水", "风", "云", "月", "星", "春", "夏", "秋", "冬",
    "东", "南", "西", "北", "红", "绿", "蓝", "黄", "白", "黑",
    "猫", "狗", "鸟", "鱼", "树", "草", "石", "火", "雨", "雪",
    "快", "乐", "安", "平", "高", "低", "长", "短", "新", "旧",
]


class StandardWordClickImageCaptchaGenerator(ImageCaptchaGenerator):
    """
    标准文字点选验证码生成器。

    与 Java 版 StandardWordClickImageCaptchaGenerator 对应。

    配置参数：
    - click_img_width: 单个文字图片宽度，默认 100
    - check_click_count: 需要点击的文字数量，默认 4
    - interference_count: 干扰文字数量，默认 2
    """

    def __init__(self):
        self._resource_manager = None
        self._click_img_width = 100
        self._check_click_count = 4
        self._interference_count = 2
        self._font_path = None

    def set_resource_manager(self, resource_manager):
        self._resource_manager = resource_manager

    def _get_font_path(self):
        """获取字体文件路径。"""
        if self._font_path:
            return self._font_path

        # 尝试从资源管理器获取字体
        if self._resource_manager:
            fonts = self._resource_manager.resource_store.get_fonts()
            if fonts:
                from ..resource.provider import load_resource
                font_data = load_resource(fonts[0])
                # 将字体写入临时文件
                import tempfile
                temp_font = tempfile.NamedTemporaryFile(suffix=".ttf", delete=False)
                temp_font.write(font_data)
                temp_font.close()
                self._font_path = temp_font.name
                return self._font_path

        # 使用系统默认字体
        default_paths = [
            "/usr/share/fonts/truetype/chinese/NotoSansSC[wght].ttf",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        ]
        for path in default_paths:
            if os.path.exists(path):
                self._font_path = path
                return path

        return None

    def generate_captcha_image(self, captcha_type=None, background_format="jpeg", template_format="png"):
        """
        生成文字点选验证码图片。

        流程：
        1. 加载背景图
        2. 随机选择需要点击的目标文字和干扰文字
        3. 在背景图上随机位置绘制所有文字（目标+干扰）
        4. 记录目标文字的位置信息
        5. 生成提示图片
        6. 构建并返回验证码信息

        Returns:
            dict: 验证码信息字典
        """
        if self._resource_manager is None:
            raise RuntimeError("Resource manager not set")

        # 1. 加载背景图
        bg_data = self._resource_manager.random_get_resource(WORD_IMAGE_CLICK)
        bg_image = CaptchaImageUtils.load_image(bg_data).convert("RGBA")

        # 调整背景图大小
        bg_image = CaptchaImageUtils.resize_image(bg_image, 590, 360)
        bg_width, bg_height = bg_image.size

        font_path = self._get_font_path()

        # 2. 选择随机文字
        total_count = self._check_click_count + self._interference_count
        selected_chars = random.sample(COMMON_CHINESE_CHARS, total_count)
        check_chars = selected_chars[:self._check_click_count]
        interference_chars = selected_chars[self._check_click_count:]

        # 3. 在背景图上绘制文字
        click_definitions = []
        img_size = self._click_img_width
        font_size = 30

        # 所有文字（目标+干扰）
        all_chars = list(check_chars) + list(interference_chars)
        random.shuffle(all_chars)

        # 计算文字位置，避免重叠
        positions = self._generate_non_overlapping_positions(
            bg_width, bg_height, img_size, len(all_chars)
        )

        for i, char in enumerate(all_chars):
            if i >= len(positions):
                break

            x, y = positions[i]
            color = CaptchaImageUtils.get_random_color()
            angle = random.randint(0, 85)

            # 绘制文字图片
            word_img = CaptchaImageUtils.draw_word_image(
                char, img_size, img_size,
                font_path=font_path,
                font_size=font_size,
                color=color,
                angle=angle,
            )

            # 叠加到背景图
            bg_image = CaptchaImageUtils.overlay_image(bg_image, word_img, x, y)

            # 记录目标文字的位置信息
            is_check = char in check_chars
            if is_check:
                # 计算中心点
                center_x = x + img_size // 2
                center_y = y + img_size // 2

                # 计算百分比位置（用于验证）
                percent_x = center_x / bg_width
                percent_y = center_y / bg_height

                click_definitions.append({
                    "tip": char,
                    "x": percent_x,
                    "y": percent_y,
                    "order": check_chars.index(char),
                })

        # 4. 添加干扰圆和干扰线
        from PIL import ImageDraw
        draw = ImageDraw.Draw(bg_image)
        CaptchaImageUtils.draw_oval(draw, bg_width, bg_height, count=3)

        # 5. 生成提示图片
        tip_base64 = CaptchaImageUtils.gen_tip_image(
            check_chars, font_path=font_path
        )

        # 6. 转换为 Base64
        bg_base64 = CaptchaImageUtils.image_to_base64(bg_image, format=background_format)

        # 7. 构建返回数据
        # 对 click_definitions 按点击顺序排序
        click_definitions.sort(key=lambda d: d["order"])

        result = {
            "backgroundImage": bg_base64,
            "templateImage": tip_base64,
            "backgroundImageWidth": bg_width,
            "backgroundImageHeight": bg_height,
            "templateImageWidth": len(check_chars) * 48,
            "templateImageHeight": 40,
            "type": WORD_IMAGE_CLICK,
            "tolerant": 0.05,
            "data": {
                "clickDefinitions": click_definitions,
            },
        }

        return result

    def _generate_non_overlapping_positions(self, bg_width, bg_height, img_size, count):
        """
        生成不重叠的随机位置。

        Args:
            bg_width: 背景图宽度
            bg_height: 背景图高度
            img_size: 文字图片大小
            count: 需要的位置数量

        Returns:
            list: [(x, y), ...] 位置列表
        """
        positions = []
        max_attempts = 1000
        margin = 10

        for _ in range(count):
            for attempt in range(max_attempts):
                x = random.randint(margin, bg_width - img_size - margin)
                y = random.randint(margin, bg_height - img_size - margin)

                # 检查是否与已有位置重叠
                overlap = False
                for px, py in positions:
                    if (abs(x - px) < img_size + margin and
                            abs(y - py) < img_size + margin):
                        overlap = True
                        break

                if not overlap:
                    positions.append((x, y))
                    break

        return positions
