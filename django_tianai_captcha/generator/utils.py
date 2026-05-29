"""
验证码图片处理工具类。

提供验证码图片生成的核心图像操作方法，包括：
- 图片裁剪与合成
- 模板叠加
- 旋转操作
- 滑动还原图片分割与拼接
- 文字绘制与干扰线生成

与 Java 版 CaptchaImageUtils 对应，使用 Pillow 库实现。
"""

import io
import math
import random

from PIL import Image, ImageDraw, ImageFont, ImageFilter


class CaptchaImageUtils:
    """
    验证码图片处理工具类。

    所有方法均为静态方法，提供各种图像操作功能。
    """

    @staticmethod
    def load_image(data):
        """
        从二进制数据加载图片。

        Args:
            data: 图片的二进制数据

        Returns:
            PIL.Image.Image 对象
        """
        return Image.open(io.BytesIO(data))

    @staticmethod
    def image_to_base64(image, format="JPEG", quality=85):
        """
        将图片转换为 Base64 编码字符串。

        Args:
            image: PIL.Image.Image 对象
            format: 输出格式（JPEG/PNG）
            quality: JPEG 压缩质量

        Returns:
            str: Base64 编码的图片数据（含 data:image 前缀）
        """
        buffer = io.BytesIO()
        if format.upper() == "JPEG":
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            image.save(buffer, format=format, quality=quality)
        else:
            image.save(buffer, format=format)

        import base64
        b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

        mime_type = "image/jpeg" if format.upper() == "JPEG" else "image/png"
        return f"data:{mime_type};base64,{b64_str}"

    @staticmethod
    def create_transparent_image(width, height):
        """
        创建透明图片。

        Args:
            width: 宽度
            height: 高度

        Returns:
            PIL.Image.Image (RGBA 模式)
        """
        return Image.new("RGBA", (width, height), (0, 0, 0, 0))

    @staticmethod
    def overlay_image(base_image, overlay, x, y):
        """
        将 overlay 图片叠加到 base_image 的指定位置。

        Args:
            base_image: 底图 (RGBA 模式)
            overlay: 叠加图 (RGBA 模式)
            x: X 坐标
            y: Y 坐标

        Returns:
            PIL.Image.Image: 叠加后的图片
        """
        if base_image.mode != "RGBA":
            base_image = base_image.convert("RGBA")
        if overlay.mode != "RGBA":
            overlay = overlay.convert("RGBA")

        # 创建底图的副本
        result = base_image.copy()

        # 创建一个与底图同样大小的透明图层
        temp = Image.new("RGBA", result.size, (0, 0, 0, 0))
        temp.paste(overlay, (int(x), int(y)))
        result = Image.alpha_composite(result, temp)

        return result

    @staticmethod
    def cut_image_by_mask(source_image, mask_image, x, y):
        """
        使用模板遮罩从源图片中裁剪图像。

        根据模板图片的 alpha 通道（透明度）从源图片中提取对应区域的像素。
        alpha 值大于阈值（100）的像素被提取，其余像素设为透明。

        与 Java 版 cutImage 方法对应。

        Args:
            source_image: 源图片 (RGBA)
            mask_image: 模板遮罩图片 (RGBA)
            x: 裁剪起始 X 坐标
            y: 裁剪起始 Y 坐标

        Returns:
            PIL.Image.Image: 裁剪出的图片 (RGBA)，大小与 mask_image 相同
        """
        if source_image.mode != "RGBA":
            source_image = source_image.convert("RGBA")
        if mask_image.mode != "RGBA":
            mask_image = mask_image.convert("RGBA")

        mask_w, mask_h = mask_image.size
        src_w, src_h = source_image.size

        # 创建结果图片
        result = Image.new("RGBA", (mask_w, mask_h), (0, 0, 0, 0))
        result_pixels = result.load()
        source_pixels = source_image.load()
        mask_pixels = mask_image.load()

        alpha_threshold = 100

        for py in range(mask_h):
            for px in range(mask_w):
                sx = int(x) + px
                sy = int(y) + py

                # 边界检查
                if 0 <= sx < src_w and 0 <= sy < src_h:
                    mask_pixel = mask_pixels[px, py]
                    # 使用模板的 alpha 通道作为遮罩
                    mask_alpha = mask_pixel[3] if len(mask_pixel) > 3 else 255

                    if mask_alpha > alpha_threshold:
                        src_pixel = source_pixels[sx, sy]
                        result_pixels[px, py] = src_pixel[:3] + (mask_alpha,)
                    else:
                        result_pixels[px, py] = (0, 0, 0, 0)
                else:
                    result_pixels[px, py] = (0, 0, 0, 0)

        return result

    @staticmethod
    def rotate_image(image, degrees):
        """
        旋转图片（以中心为旋转点）。

        Args:
            image: PIL.Image.Image 对象
            degrees: 旋转角度（顺时针为正）

        Returns:
            PIL.Image.Image: 旋转后的图片（保持原始大小）
        """
        return image.rotate(-degrees, resample=Image.BICUBIC, expand=False, center=(image.width // 2, image.height // 2))

    @staticmethod
    def center_overlay_and_rotate_image(base_image, overlay, x, y, degrees):
        """
        将 overlay 放置在 base_image 的指定位置，并旋转 overlay。

        Args:
            base_image: 底图 (RGBA)
            overlay: 叠加图 (RGBA)
            x: X 坐标
            y: Y 坐标
            degrees: 旋转角度

        Returns:
            PIL.Image.Image: 叠加并旋转后的图片
        """
        # 旋转 overlay
        rotated = overlay.rotate(-degrees, resample=Image.BICUBIC, expand=True)

        if base_image.mode != "RGBA":
            base_image = base_image.convert("RGBA")
        if rotated.mode != "RGBA":
            rotated = rotated.convert("RGBA")

        result = base_image.copy()

        # 创建透明图层用于叠加
        temp = Image.new("RGBA", result.size, (0, 0, 0, 0))

        # 计算居中偏移
        offset_x = int(x) - (rotated.width - overlay.width) // 2
        offset_y = int(y) - (rotated.height - overlay.height) // 2

        temp.paste(rotated, (offset_x, offset_y))
        result = Image.alpha_composite(result, temp)

        return result

    @staticmethod
    def center_overlay_and_rotate_image_inplace(base_image, overlay, degrees):
        """
        将 overlay 旋转后居中放置到 base_image 上（原地修改 base_image）。

        与 Java 版 CaptchaImageUtils.centerOverlayAndRotateImage 对应：
        1. 先旋转 overlay（expand=True，保持完整图像）
        2. 将旋转后的 overlay 居中放置到 base_image 上

        Args:
            base_image: 底图 (RGBA)，会被原地修改
            overlay: 叠加图 (RGBA)
            degrees: 旋转角度

        Returns:
            PIL.Image.Image: 修改后的 base_image
        """
        # 旋转 overlay（expand=True 保持旋转后完整图像不裁剪）
        rotated = overlay.rotate(-degrees, resample=Image.BICUBIC, expand=True)

        if rotated.mode != "RGBA":
            rotated = rotated.convert("RGBA")

        # 计算居中位置
        bw, bh = base_image.size
        cw, ch = rotated.size
        paste_x = bw // 2 - cw // 2
        paste_y = bh // 2 - ch // 2

        # 创建临时透明图层用于叠加
        temp = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        temp.paste(rotated, (paste_x, paste_y))

        # 使用 alpha_composite 合成后返回
        result = Image.alpha_composite(base_image, temp)
        return result

    @staticmethod
    def split_image(image, position, direction="horizontal"):
        """
        分割图片。

        Args:
            image: 源图片
            position: 分割位置（像素）
            direction: 分割方向（"horizontal" 水平，"vertical" 垂直）

        Returns:
            tuple: (上半部分, 下半部分) 或 (左半部分, 右半部分)
        """
        w, h = image.size
        if direction == "horizontal":
            # 水平分割：上下
            part1 = image.crop((0, 0, w, position))
            part2 = image.crop((0, position, w, h))
        else:
            # 垂直分割：左右
            part1 = image.crop((0, 0, position, h))
            part2 = image.crop((position, 0, w, h))
        return part1, part2

    @staticmethod
    def concat_images(img1, img2, direction="horizontal"):
        """
        拼接两张图片。

        Args:
            img1: 第一张图片
            img2: 第二张图片
            direction: 拼接方向（"horizontal" 水平，"vertical" 垂直）

        Returns:
            PIL.Image.Image: 拼接后的图片
        """
        if direction == "horizontal":
            # 水平拼接
            total_width = img1.width + img2.width
            max_height = max(img1.height, img2.height)
            result = Image.new(img1.mode, (total_width, max_height))
            result.paste(img1, (0, 0))
            result.paste(img2, (img1.width, 0))
        else:
            # 垂直拼接
            max_width = max(img1.width, img2.width)
            total_height = img1.height + img2.height
            result = Image.new(img1.mode, (max_width, total_height))
            result.paste(img1, (0, 0))
            result.paste(img2, (0, img1.height))

        return result

    @staticmethod
    def draw_word_image(word, width, height, font_path=None, font_size=30, color=None, angle=None):
        """
        绘制带旋转的文字图片。

        用于文字点选验证码，在透明背景上绘制旋转的汉字。

        Args:
            word: 要绘制的文字
            width: 图片宽度
            height: 图片高度
            font_path: 字体文件路径
            font_size: 字体大小
            color: 字体颜色 (R, G, B)
            angle: 旋转角度（度），为 None 时随机生成

        Returns:
            PIL.Image.Image: 带文字的透明图片 (RGBA)
        """
        result = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(result)

        if color is None:
            color = CaptchaImageUtils.get_random_color()
        if angle is None:
            angle = random.randint(0, 85)

        # 加载字体
        try:
            if font_path:
                font = ImageFont.truetype(font_path, font_size)
            else:
                font = ImageFont.truetype("/usr/share/fonts/truetype/chinese/NotoSansSC[wght].ttf", font_size)
        except Exception:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", font_size)
            except Exception:
                font = ImageFont.load_default()

        # 计算文字位置（居中）
        bbox = draw.textbbox((0, 0), word, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        text_x = (width - text_w) // 2
        text_y = (height - text_h) // 2

        # 先在临时图片上绘制文字
        temp = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp)
        temp_draw.text((text_x, text_y), word, fill=color + (255,), font=font)

        # 旋转文字
        rotated = temp.rotate(-angle, resample=Image.BICUBIC, expand=False,
                               center=(width // 2, height // 2))

        # 叠加到结果
        result = Image.alpha_composite(result, rotated)

        return result

    @staticmethod
    def gen_tip_image(words, font_path=None, font_size=24, width=None, height=40):
        """
        生成提示图片。

        用于文字点选验证码，显示需要点击的汉字。

        Args:
            words: 要显示的汉字列表
            font_path: 字体路径
            font_size: 字体大小
            width: 图片宽度
            height: 图片高度

        Returns:
            str: 提示图片的 Base64 编码
        """
        text = "".join(words)
        if width is None:
            width = len(words) * font_size * 2

        result = Image.new("RGBA", (width, height), (255, 255, 255, 255))
        draw = ImageDraw.Draw(result)

        # 加载字体
        try:
            if font_path:
                font = ImageFont.truetype(font_path, font_size)
            else:
                font = ImageFont.truetype("/usr/share/fonts/truetype/chinese/NotoSansSC[wght].ttf", font_size)
        except Exception:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", font_size)
            except Exception:
                font = ImageFont.load_default()

        # 绘制文字
        total_text_w = 0
        for word in words:
            bbox = draw.textbbox((0, 0), word, font=font)
            total_text_w += bbox[2] - bbox[0]

        start_x = (width - total_text_w) // 2
        current_x = start_x

        for word in words:
            color = CaptchaImageUtils.get_random_color()
            bbox = draw.textbbox((0, 0), word, font=font)
            text_w = bbox[2] - bbox[0]
            text_y = (height - (bbox[3] - bbox[1])) // 2
            draw.text((current_x, text_y), word, fill=color + (255,), font=font)
            current_x += text_w

        # 添加干扰线
        for _ in range(2):
            CaptchaImageUtils.draw_bessel_line(draw, width, height)

        # 添加干扰点
        for _ in range(5):
            px = random.randint(0, width)
            py = random.randint(0, height)
            draw.point((px, py), fill=CaptchaImageUtils.get_random_color() + (255,))

        return CaptchaImageUtils.image_to_base64(result, format="PNG")

    @staticmethod
    def draw_bessel_line(draw, width, height):
        """
        绘制贝塞尔曲线干扰线。

        Args:
            draw: ImageDraw 对象
            width: 画布宽度
            height: 画布高度
        """
        color = CaptchaImageUtils.get_random_color() + (255,)

        # 随机控制点
        points = [(random.randint(0, width), random.randint(0, height)) for _ in range(4)]

        # 简化为多段直线模拟贝塞尔曲线
        segments = 20
        prev_point = points[0]
        for i in range(1, segments + 1):
            t = i / segments
            # 三阶贝塞尔
            x = ((1 - t) ** 3 * points[0][0] +
                 3 * (1 - t) ** 2 * t * points[1][0] +
                 3 * (1 - t) * t ** 2 * points[2][0] +
                 t ** 3 * points[3][0])
            y = ((1 - t) ** 3 * points[0][1] +
                 3 * (1 - t) ** 2 * t * points[1][1] +
                 3 * (1 - t) * t ** 2 * points[2][1] +
                 t ** 3 * points[3][1])
            curr_point = (int(x), int(y))
            draw.line([prev_point, curr_point], fill=color, width=1)
            prev_point = curr_point

    @staticmethod
    def get_random_color():
        """
        生成随机颜色。

        Returns:
            tuple: (R, G, B) 颜色值
        """
        return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    @staticmethod
    def draw_oval(draw, width, height, count=3):
        """
        绘制随机干扰圆。

        Args:
            draw: ImageDraw 对象
            width: 画布宽度
            height: 画布高度
            count: 干扰圆数量
        """
        for _ in range(count):
            color = CaptchaImageUtils.get_random_color() + (random.randint(30, 100),)
            x = random.randint(0, width)
            y = random.randint(0, height)
            rx = random.randint(5, 30)
            ry = random.randint(5, 30)
            draw.ellipse([x - rx, y - ry, x + rx, y + ry], outline=color)

    @staticmethod
    def resize_image(image, width, height):
        """
        调整图片大小。

        Args:
            image: PIL.Image.Image 对象
            width: 目标宽度
            height: 目标高度

        Returns:
            PIL.Image.Image: 调整大小后的图片
        """
        return image.resize((width, height), Image.LANCZOS)
