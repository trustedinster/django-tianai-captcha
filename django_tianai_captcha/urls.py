"""
Django URL 配置。

提供验证码 API 接口的 URL 路由，与 Java 版默认接口路径保持一致，
可无缝对接 tianai-captcha-web-sdk 前端。

默认路由：
- /captcha/generate - 生成验证码
- /captcha/check    - 校验验证码
- /captcha/verify   - 二次验证
"""

from django.urls import path

from . import views

app_name = "django_tianai_captcha"

# 默认 URL 模式，与 Java 版接口路径保持一致
urlpatterns = [
    path("generate", views.generate_captcha, name="generate"),
    path("check", views.check_captcha, name="check"),
    path("verify", views.verify_captcha, name="verify"),
]
