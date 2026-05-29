"""
Django 视图模块。

提供验证码生成和校验的 HTTP API 接口，
与 Java 版默认接口规范保持一致，可无缝对接 tianai-captcha-web-sdk 前端。

接口规范：
- GET/POST /captcha/generate  - 生成验证码（SDK 使用 POST）
- POST     /captcha/check    - 校验验证码
- POST     /captcha/verify   - 二次验证
"""

import json
import logging

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from .conf import get_captcha_application, CAPTCHA_TYPES, SLIDER

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def generate_captcha(request):
    """
    生成验证码接口。

    与 Java 版默认生成接口规范对应，可无缝对接 tianai-captcha-web-sdk。
    tianai-captcha-web-sdk 使用 POST 方法请求此接口。

    Query Parameters (GET) / Request Body (POST):
        type (str, optional): 验证码类型，默认使用配置的 DEFAULT_TYPE

    Returns:
        JsonResponse: 验证码数据，包含：
            - code: 状态码（200=成功）
            - msg: 消息
            - data: ImageCaptchaVO 数据
                - id: 验证码 ID
                - type: 验证码类型
                - backgroundImage: 背景图片 Base64
                - templateImage: 模板图片 Base64
                - backgroundImageWidth/Height: 背景图尺寸
                - templateImageWidth/Height: 模板图尺寸
    """
    # 兼容 GET 和 POST 两种方式获取 type 参数
    if request.method == "POST":
        try:
            body = json.loads(request.body) if request.body else {}
        except (json.JSONDecodeError, ValueError):
            body = {}
        captcha_type = body.get("type", request.GET.get("type", None))
    else:
        captcha_type = request.GET.get("type", None)

    # 验证类型参数
    if captcha_type and captcha_type not in CAPTCHA_TYPES:
        return JsonResponse({
            "code": 400,
            "msg": f"Unsupported captcha type: {captcha_type}",
        }, status=400)

    app = get_captcha_application()
    result = app.generate_captcha(captcha_type)

    return JsonResponse(result.to_dict())


@csrf_exempt
@require_http_methods(["POST"])
def check_captcha(request):
    """
    校验验证码接口。

    与 Java 版默认校验接口规范对应，可无缝对接 tianai-captcha-web-sdk。

    Request Body (JSON):
        {
            "id": "验证码ID",
            "track": {
                "bgImageWidth": 590,
                "bgImageHeight": 360,
                "templateImageWidth": 50,
                "templateImageHeight": 360,
                "startTime": 1234567890,
                "stopTime": 1234567900,
                "trackList": [
                    {"x": 0.0, "y": 0.0, "t": 0, "type": "MOVE"},
                    {"x": 1.5, "y": 0.2, "t": 16, "type": "MOVE"},
                    ...
                ],
                "data": null
            }
        }

    Returns:
        JsonResponse: 校验结果，包含：
            - code: 状态码（200=成功，400=校验失败）
            - msg: 消息
            - data: 校验成功时包含 token（开启二次验证时）
    """
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({
            "code": 400,
            "msg": "Invalid request body",
        }, status=400)

    captcha_id = body.get("id")
    # tianai-captcha-web-sdk 发送的轨迹数据 key 为 "data"，
    # Java 版 MatchParam 使用 "track" 作为 key。
    # 此处兼容两种 key 名称，优先使用 "data"（SDK 默认），回退到 "track"（Java 规范）。
    # 注意：使用 isinstance 检查而非 truthy 检查，因为空字典 {} 是 falsy 但可能是有效数据
    track_data = body.get("data") if isinstance(body.get("data"), dict) else body.get("track")

    if not captcha_id:
        return JsonResponse({
            "code": 400,
            "msg": "Missing captcha id",
        }, status=400)

    if not track_data:
        return JsonResponse({
            "code": 400,
            "msg": "Missing track data",
        }, status=400)

    app = get_captcha_application()
    result = app.matching(captcha_id, track_data)

    return JsonResponse(result.to_dict())


@csrf_exempt
@require_http_methods(["POST"])
def verify_captcha(request):
    """
    二次验证接口。

    用于在业务接口中验证客户端传来的 token 是否合法。
    只有开启二次验证功能时此接口才有意义。

    Request Body (JSON):
        {
            "token": "二次验证token"
        }

    Returns:
        JsonResponse: 验证结果
    """
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({
            "code": 400,
            "msg": "Invalid request body",
        }, status=400)

    token = body.get("token")
    if not token:
        return JsonResponse({
            "code": 400,
            "msg": "Missing token",
        }, status=400)

    app = get_captcha_application()
    is_valid = app.secondary_verification(token)

    if is_valid:
        return JsonResponse({
            "code": 200,
            "msg": "success",
        })
    else:
        return JsonResponse({
            "code": 400,
            "msg": "Invalid or expired token",
        }, status=400)
