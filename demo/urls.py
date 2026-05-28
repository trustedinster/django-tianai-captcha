"""
Django 天爱验证码演示平台 URL 配置。
"""

from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    # 首页
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    # 验证码 API
    path('api/captcha/', include('django_tianai_captcha.urls')),
]
