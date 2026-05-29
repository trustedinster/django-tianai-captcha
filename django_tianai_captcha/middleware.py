"""
Django 中间件模块。

提供验证码相关的中间件功能，包括：
- 频率限制中间件：防止恶意频繁请求验证码
"""

import time
import logging

from django.http import JsonResponse
from django.conf import settings

from .conf import get_setting

logger = logging.getLogger(__name__)


class CaptchaRateLimitMiddleware:
    """
    验证码请求频率限制中间件。

    基于 IP 地址限制验证码接口的请求频率，防止恶意刷接口。

    配置示例（在 Django settings 中）：
        CAPTCHA = {
            ...
            "RATE_LIMIT": {
                "ENABLED": True,
                "RATE": 10,          # 每分钟最大请求数
                "PERIOD": 60,        # 统计周期（秒）
            },
        }
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self._request_counts = {}  # {ip: {"count": N, "reset_at": timestamp}}

    def __call__(self, request):
        # 仅对验证码接口进行频率限制
        if request.path.startswith("/captcha/"):
            rate_config = get_setting("RATE_LIMIT")
            if rate_config and rate_config.get("ENABLED", False):
                if not self._check_rate_limit(request, rate_config):
                    return JsonResponse({
                        "code": 429,
                        "msg": "请求过于频繁，请稍后再试",
                    }, status=429)

        response = self.get_response(request)
        return response

    def _check_rate_limit(self, request, rate_config):
        """
        检查请求频率是否超过限制。

        Args:
            request: Django 请求对象
            rate_config: 频率限制配置

        Returns:
            bool: 是否允许请求
        """
        ip = self._get_client_ip(request)
        now = time.time()

        max_rate = rate_config.get("RATE", 10)
        period = rate_config.get("PERIOD", 60)

        if ip not in self._request_counts:
            self._request_counts[ip] = {
                "count": 1,
                "reset_at": now + period,
            }
            return True

        entry = self._request_counts[ip]

        # 检查是否需要重置计数
        if now > entry["reset_at"]:
            entry["count"] = 1
            entry["reset_at"] = now + period
            return True

        # 增加计数并检查
        entry["count"] += 1
        if entry["count"] > max_rate:
            return False

        return True

    @staticmethod
    def _get_client_ip(request):
        """获取客户端 IP 地址。"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "0.0.0.0")
        return ip
