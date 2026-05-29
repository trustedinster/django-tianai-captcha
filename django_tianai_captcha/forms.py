"""
Django 表单和 Widget 模块。

提供验证码表单 Widget，方便在 Django 表单中集成验证码功能。
"""

from django import forms
from django.utils.safestring import mark_safe


class CaptchaWidget(forms.Widget):
    """
    验证码 Widget。

    在 Django 表单中渲染验证码组件，自动集成前端 SDK。

    使用方式：
        class MyForm(forms.Form):
            captcha = forms.CharField(widget=CaptchaWidget())

    模板中使用：
        {{ form.captcha }}
    """

    template_name = "django_tianai_captcha/widget.html"

    def __init__(self, attrs=None, captcha_type=None):
        """
        初始化验证码 Widget。

        Args:
            attrs: HTML 属性
            captcha_type: 验证码类型
        """
        self.captcha_type = captcha_type
        super().__init__(attrs=attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["captcha_type"] = self.captcha_type or "SLIDER"
        return context

    class Media:
        js = ("django_tianai_captcha/js/captcha.js",)
        css = {"all": ("django_tianai_captcha/css/captcha.css",)}
