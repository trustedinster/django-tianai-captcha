"""
验证码校验器模块初始化。

提供验证码校验功能，包括基础位置校验和轨迹行为校验。
"""

from .simple import SimpleImageCaptchaValidator
from .track import BasicCaptchaTrackValidator

__all__ = [
    "SimpleImageCaptchaValidator",
    "BasicCaptchaTrackValidator",
]
