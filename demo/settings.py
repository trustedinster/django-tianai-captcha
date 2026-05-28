"""
Django 天爱验证码演示平台配置。
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 将父目录加入 Python 路径，以便导入 django_tianai_captcha
sys.path.insert(0, os.path.dirname(BASE_DIR))

SECRET_KEY = 'django-tianai-captcha-demo-secret-key-change-in-production'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django_tianai_captcha',
]

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'demo.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'demo', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [],
        },
    },
]

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'demo', 'static'),
]

# 验证码配置
CAPTCHA = {
    "PREFIX": "captcha",
    "EXPIRE": {
        "default": 120,
        "WORD_IMAGE_CLICK": 180,
    },
    "INIT_DEFAULT_RESOURCE": True,
    "CACHE_BACKEND": "local",
    "DEFAULT_TYPE": "SLIDER",
    "TOLERANT": 0.02,
    "TRACK_VALIDATION_ENABLED": False,  # 演示环境关闭轨迹校验
    "SECONDARY": {
        "ENABLED": False,
    },
    "RATE_LIMIT": {
        "ENABLED": False,
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
