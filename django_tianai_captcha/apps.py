from django.apps import AppConfig


class DjangoTianaiCaptchaConfig(AppConfig):
    """Django 应用配置类。"""

    name = "django_tianai_captcha"
    verbose_name = "Django 天爱验证码"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        """Django 启动时的初始化钩子。"""
        from .conf import get_captcha_application

        # 预初始化验证码应用实例（懒加载）
        get_captcha_application()
