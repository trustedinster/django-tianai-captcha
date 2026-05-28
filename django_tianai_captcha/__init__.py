"""
django-tianai-captcha - 天爱验证码 Django 插件

基于 tianai-captcha Java 项目的 Python/Django 实现，支持多种行为验证码类型：
- SLIDER: 滑块验证码
- ROTATE: 旋转验证码
- CONCAT: 滑动还原验证码
- WORD_IMAGE_CLICK: 文字点选验证码
"""

__version__ = "1.0.0"
__author__ = "tianai-captcha team"

default_app_config = "django_tianai_captcha.apps.DjangoTianaiCaptchaConfig"
