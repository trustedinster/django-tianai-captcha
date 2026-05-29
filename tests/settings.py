"""
Django 测试配置。
"""

SECRET_KEY = "test-secret-key-for-django-tianai-captcha"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django_tianai_captcha",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

ROOT_URLCONF = "tests.urls"

CAPTCHA = {
    "PREFIX": "test_captcha",
    "EXPIRE": {
        "default": 60,
    },
    "INIT_DEFAULT_RESOURCE": True,
    "CACHE_BACKEND": "local",
    "DEFAULT_TYPE": "SLIDER",
    "TOLERANT": 0.02,
    "TRACK_VALIDATION_ENABLED": False,
    "SECONDARY": {
        "ENABLED": False,
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
