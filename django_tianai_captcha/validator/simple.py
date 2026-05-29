"""
简单验证码校验器。

基于百分比的位置校验，与 Java 版 SimpleImageCaptchaValidator 对应。

校验原理：
- 滑块/旋转/滑动还原验证码：比较用户滑动位置与正确位置的百分比差值是否在容错范围内
- 文字点选验证码：比较用户点击位置与目标文字位置的百分比差值是否在容错范围内
"""

import logging

from ..conf import SLIDER, ROTATE, CONCAT, WORD_IMAGE_CLICK

logger = logging.getLogger(__name__)


class SimpleImageCaptchaValidator:
    """
    简单验证码校验器。

    与 Java 版 SimpleImageCaptchaValidator 对应。

    校验方式：
    - SLIDER/CONCAT: 计算用户滑动的百分比位置与正确位置的差值
    - ROTATE: 计算用户旋转的百分比与正确百分比的差值
    - WORD_IMAGE_CLICK: 逐一比较用户点击位置与目标文字位置的差值

    所有比较都允许一定的容错值（tolerant）。
    """

    DEFAULT_TOLERANT = 0.02

    def generate_valid_data(self, captcha_info):
        """
        根据验证码信息生成校验数据。

        校验数据是验证码的正确答案，缓存在服务端用于后续校验。
        该数据不会返回给前端。

        Args:
            captcha_info: 验证码生成器返回的信息字典

        Returns:
            dict: 校验数据字典
        """
        captcha_type = captcha_info.get("type", SLIDER)
        random_x = captcha_info.get("randomX", 0)
        bg_width = captcha_info.get("backgroundImageWidth", 590)
        tolerant = captcha_info.get("tolerant", self.DEFAULT_TOLERANT)

        if captcha_type in (SLIDER, ROTATE, CONCAT):
            # 滑块/旋转/滑动还原：存储百分比
            percentage = random_x / bg_width if bg_width > 0 else 0
            return {
                "percentage": percentage,
                "tolerant": tolerant,
                "type": captcha_type,
            }

        elif captcha_type == WORD_IMAGE_CLICK:
            # 文字点选：存储每个目标文字的百分比位置
            click_definitions = captcha_info.get("data", {}).get("clickDefinitions", [])
            check_order = []
            for defn in click_definitions:
                check_order.append({
                    "x": defn["x"],
                    "y": defn["y"],
                    "tip": defn["tip"],
                    "order": defn["order"],
                })
            # 按点击顺序排序
            check_order.sort(key=lambda d: d["order"])

            return {
                "clickOrder": check_order,
                "tolerant": tolerant,
                "type": captcha_type,
            }

        return {}

    def valid(self, track_data, valid_data, captcha_type=None):
        """
        校验验证码。

        Args:
            track_data: 前端传来的轨迹数据
            valid_data: 服务端缓存的校验数据
            captcha_type: 验证码类型

        Returns:
            bool: 校验是否通过
        """
        if not valid_data:
            return False

        captcha_type = valid_data.get("type", captcha_type)

        if captcha_type in (SLIDER, ROTATE, CONCAT):
            return self._valid_slider_type(track_data, valid_data)
        elif captcha_type == WORD_IMAGE_CLICK:
            return self._valid_click_type(track_data, valid_data)

        return False

    def _valid_slider_type(self, track_data, valid_data):
        """
        校验滑块类验证码（滑块、旋转、滑动还原）。

        计算用户滑动位置的百分比与正确百分比的差值，
        如果在容错范围内则校验通过。

        Args:
            track_data: 轨迹数据
            valid_data: 校验数据

        Returns:
            bool: 是否校验通过
        """
        percentage = valid_data.get("percentage", 0)
        tolerant = valid_data.get("tolerant", self.DEFAULT_TOLERANT)

        # 从轨迹数据获取滑动位置
        bg_width = track_data.get("bgImageWidth", 590)
        template_width = track_data.get("templateImageWidth", 0)

        track_list = track_data.get("trackList", [])
        if not track_list:
            return False

        # 获取滑动轨迹的最终 X 位置
        last_track = track_list[-1]
        first_track = track_list[0]

        # 计算滑动距离
        slide_x = last_track.get("x", 0) - first_track.get("x", 0)

        # 计算百分比
        calc_percentage = slide_x / bg_width if bg_width > 0 else 0

        # 检查是否在容错范围内
        return self._check_percentage(calc_percentage, percentage, tolerant)

    def _valid_click_type(self, track_data, valid_data):
        """
        校验文字点选验证码。

        逐一比较用户点击位置与目标文字位置的差值。

        Args:
            track_data: 轨迹数据
            valid_data: 校验数据

        Returns:
            bool: 是否校验通过
        """
        click_order = valid_data.get("clickOrder", [])
        tolerant = valid_data.get("tolerant", 0.05)

        # 获取背景图尺寸
        bg_width = track_data.get("bgImageWidth", 590)
        bg_height = track_data.get("bgImageHeight", 360)

        # 获取点击轨迹（类型为 CLICK 的轨迹，不区分大小写）
        track_list = track_data.get("trackList", [])
        click_tracks = [t for t in track_list if t.get("type", "").upper() == "CLICK"]

        if len(click_tracks) != len(click_order):
            return False

        # 逐一校验
        for i, track in enumerate(click_tracks):
            if i >= len(click_order):
                return False

            expected = click_order[i]
            # 计算用户点击位置的百分比
            click_x = track.get("x", 0) / bg_width if bg_width > 0 else 0
            click_y = track.get("y", 0) / bg_height if bg_height > 0 else 0

            # 检查 X 和 Y 是否都在容错范围内
            if not self._check_percentage(click_x, expected["x"], tolerant):
                return False
            if not self._check_percentage(click_y, expected["y"], tolerant):
                return False

        return True

    @staticmethod
    def calc_percentage(pos, max_pos):
        """计算百分比。"""
        return pos / max_pos if max_pos > 0 else 0

    @staticmethod
    def _check_percentage(new_val, ori_val, tolerant):
        """
        检查百分比是否在容错范围内。

        Args:
            new_val: 用户操作的百分比值
            ori_val: 正确的百分比值
            tolerant: 容错值

        Returns:
            bool: 是否通过
        """
        return (ori_val - tolerant) <= new_val <= (ori_val + tolerant)
