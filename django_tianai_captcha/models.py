"""
Django 模型模块。

提供验证码相关的数据库模型（如需持久化存储）。
默认使用缓存存储验证码数据，此模块为扩展用途。
"""

from django.db import models


class CaptchaRecord(models.Model):
    """
    验证码记录模型。

    用于持久化存储验证码记录，可选使用。
    默认情况下验证码数据仅存储在缓存中，此模型用于需要持久化记录的场景。
    """

    captcha_id = models.CharField(max_length=128, unique=True, verbose_name="验证码ID")
    captcha_type = models.CharField(max_length=32, verbose_name="验证码类型")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP地址")
    is_valid = models.BooleanField(default=False, verbose_name="是否校验通过")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    validated_at = models.DateTimeField(null=True, blank=True, verbose_name="校验时间")

    class Meta:
        app_label = "django_tianai_captcha"
        verbose_name = "验证码记录"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.captcha_type}:{self.captcha_id}"
