"""
轨迹行为校验器。

基于用户鼠标/触摸轨迹的行为特征校验，与 Java 版 BasicCaptchaTrackValidator 对应。

校验原理：
通过分析用户操作轨迹的行为特征来判断是否为真人操作，
主要包括以下 7 项检查：
1. 滑动时间必须大于 300ms
2. 轨迹点数量在合理范围内
3. 起始点坐标接近原点
4. Y 坐标不能全部相同（机器人特征）
5. 相邻轨迹点之间不能有大幅跳跃
6. 减速特征：最后 30% 的平均速度应慢于前 70%
7. X 超出背景宽度的次数不能太多
"""

import logging

from ..conf import SLIDER, CONCAT, get_setting

logger = logging.getLogger(__name__)


class BasicCaptchaTrackValidator:
    """
    轨迹行为校验器。

    与 Java 版 BasicCaptchaTrackValidator 对应。
    用于检测机器人自动化操作的痕迹，保障验证码的安全性。

    仅对滑块类验证码（SLIDER, CONCAT）进行轨迹校验，
    文字点选验证码不适用此校验。
    """

    def valid(self, track_data, captcha_type=None):
        """
        校验轨迹数据的行为特征。

        Args:
            track_data: 前端传来的轨迹数据，包含：
                - bgImageWidth: 背景图宽度
                - bgImageHeight: 背景图高度
                - startTime: 开始时间
                - stopTime: 结束时间
                - trackList: 轨迹点列表，每个点包含 x, y, t, type
            captcha_type: 验证码类型

        Returns:
            bool: 轨迹是否正常
        """
        # 仅对滑块类验证码进行轨迹校验
        if captcha_type not in (SLIDER, CONCAT):
            return True

        track_config = get_setting("TRACK_VALIDATION")
        if not track_config:
            return True

        track_list = track_data.get("trackList", [])
        if not track_list:
            return False

        bg_width = track_data.get("bgImageWidth", 590)
        start_time = track_data.get("startTime", 0)
        stop_time = track_data.get("stopTime", 0)

        # 过滤非移动轨迹
        move_tracks = [t for t in track_list if t.get("type") in ("MOVE", "move", None)]
        if not move_tracks:
            move_tracks = track_list

        # 1. 滑动时间检查
        slide_time = stop_time - start_time
        min_time = track_config.get("MIN_SLIDE_TIME_MS", 300)
        if slide_time < min_time:
            logger.debug(f"Track check failed: slide time {slide_time}ms < {min_time}ms")
            return False

        # 2. 轨迹点数量检查
        track_count = len(move_tracks)
        min_count = track_config.get("MIN_TRACK_COUNT", 10)
        max_count = bg_width * track_config.get("MAX_TRACK_COUNT_MULTIPLIER", 5)
        if track_count < min_count or track_count > max_count:
            logger.debug(f"Track check failed: track count {track_count} not in [{min_count}, {max_count}]")
            return False

        # 3. 起始点检查
        first_track = move_tracks[0]
        first_x = first_track.get("x", 0)
        first_y = first_track.get("y", 0)
        if abs(first_x) > 10 or abs(first_y) > 10:
            logger.debug(f"Track check failed: first point ({first_x}, {first_y}) not near origin")
            return False

        # 4. Y 坐标变化检查（机器人通常 Y 不变）
        y_values = [t.get("y", 0) for t in move_tracks]
        if len(set(y_values)) <= 1:
            logger.debug("Track check failed: all Y values are the same (bot behavior)")
            return False

        # 5. 跳跃检查
        max_jump = track_config.get("MAX_JUMP_DISTANCE", 50)
        for i in range(1, len(move_tracks)):
            prev = move_tracks[i - 1]
            curr = move_tracks[i]
            dx = abs(curr.get("x", 0) - prev.get("x", 0))
            dy = abs(curr.get("y", 0) - prev.get("y", 0))
            if dx > max_jump or dy > max_jump:
                logger.debug(f"Track check failed: jump too large dx={dx}, dy={dy}")
                return False

        # 6. 减速特征检查
        if not self._check_deceleration(move_tracks):
            logger.debug("Track check failed: no deceleration pattern detected")
            return False

        # 7. X 超出范围检查
        max_overflow = track_config.get("MAX_OVERFLOW_COUNT", 200)
        overflow_count = sum(1 for t in move_tracks if t.get("x", 0) > bg_width)
        if overflow_count > max_overflow:
            logger.debug(f"Track check failed: X overflow count {overflow_count} > {max_overflow}")
            return False

        return True

    def _check_deceleration(self, move_tracks):
        """
        检查减速特征。

        真人操作时，滑动末段速度通常会减慢（减速特征）。
        比较前 70% 和后 30% 的平均速度。

        Args:
            move_tracks: 移动轨迹点列表

        Returns:
            bool: 是否有减速特征
        """
        if len(move_tracks) < 5:
            return True

        # 计算分割点
        split_index = int(len(move_tracks) * 0.7)

        if split_index < 2 or split_index >= len(move_tracks) - 1:
            return True

        # 计算前 70% 的平均速度
        first_part = move_tracks[:split_index]
        second_part = move_tracks[split_index:]

        first_avg_speed = self._calc_avg_speed(first_part)
        second_avg_speed = self._calc_avg_speed(second_part)

        # 后 30% 的速度应该比前 70% 慢
        if first_avg_speed > 0 and second_avg_speed > first_avg_speed * 2:
            return False

        return True

    @staticmethod
    def _calc_avg_speed(tracks):
        """
        计算轨迹段的平均速度。

        Args:
            tracks: 轨迹点列表

        Returns:
            float: 平均速度（像素/毫秒）
        """
        if len(tracks) < 2:
            return 0

        total_distance = 0
        total_time = 0

        for i in range(1, len(tracks)):
            prev = tracks[i - 1]
            curr = tracks[i]

            dx = abs(curr.get("x", 0) - prev.get("x", 0))
            dy = abs(curr.get("y", 0) - prev.get("y", 0))
            dt = abs(curr.get("t", 0) - prev.get("t", 0))

            distance = (dx ** 2 + dy ** 2) ** 0.5
            total_distance += distance
            total_time += dt

        return total_distance / total_time if total_time > 0 else 0
