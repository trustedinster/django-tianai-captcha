"""
Django 天爱验证码配置模块。

所有配置项均通过 Django settings 中的 CAPTCHA 字典进行设置，
未配置的项将使用默认值。
"""

from django.conf import settings

# 验证码类型常量
SLIDER = "SLIDER"
ROTATE = "ROTATE"
CONCAT = "CONCAT"
WORD_IMAGE_CLICK = "WORD_IMAGE_CLICK"

CAPTCHA_TYPES = [SLIDER, ROTATE, CONCAT, WORD_IMAGE_CLICK]

# 默认配置
DEFAULTS = {
    # 缓存 key 前缀
    "PREFIX": "captcha",
    # 验证码过期时间（秒）
    "EXPIRE": {
        "default": 120,
        "WORD_IMAGE_CLICK": 180,
    },
    # 是否加载系统自带资源
    "INIT_DEFAULT_RESOURCE": True,
    # 本地缓存（预生成）是否开启
    "LOCAL_CACHE_ENABLED": False,
    # 预生成缓存数量
    "LOCAL_CACHE_SIZE": 20,
    # 缓存拉取失败后等待时间（秒）
    "LOCAL_CACHE_WAIT_TIME": 5,
    # 缓存检查间隔（秒）
    "LOCAL_CACHE_PERIOD": 2,
    # 字体文件路径列表
    "FONT_PATH": [],
    # 缓存后端: "local" 或 "redis"
    "CACHE_BACKEND": "local",
    # Redis 连接配置（当 CACHE_BACKEND="redis" 时使用）
    "REDIS_URL": "redis://localhost:6379/0",
    # 二次验证配置
    "SECONDARY": {
        "ENABLED": False,
        "EXPIRE": 120,
        "KEY_PREFIX": "captcha:secondary",
    },
    # 默认验证码类型
    "DEFAULT_TYPE": SLIDER,
    # 容错值
    "TOLERANT": 0.02,
    # 是否启用轨迹行为校验
    "TRACK_VALIDATION_ENABLED": True,
    # 轨迹校验参数
    "TRACK_VALIDATION": {
        "MIN_SLIDE_TIME_MS": 300,       # 滑动最短时间（毫秒）
        "MIN_TRACK_COUNT": 10,          # 最少轨迹点数
        "MAX_TRACK_COUNT_MULTIPLIER": 5, # 最大轨迹点数 = bgWidth * multiplier
        "MAX_JUMP_DISTANCE": 50,        # 最大跳跃距离
        "MAX_OVERFLOW_COUNT": 200,       # X 超出背景宽度最大次数
    },
    # 资源配置
    "RESOURCES": {
        SLIDER: [],          # 滑块验证码背景图列表
        ROTATE: [],          # 旋转验证码背景图列表
        CONCAT: [],          # 滑动还原验证码背景图列表
        WORD_IMAGE_CLICK: [], # 文字点选验证码背景图列表
    },
    # 模板配置
    "TEMPLATES": {
        SLIDER: [],          # 自定义滑块模板
        ROTATE: [],          # 自定义旋转模板
    },
}


def get_setting(name):
    """
    获取验证码配置项。

    优先从 Django settings.CAPTCHA 字典中获取，
    未配置则使用 DEFAULTS 中的默认值。

    Args:
        name: 配置项名称

    Returns:
        配置值
    """
    captcha_settings = getattr(settings, "CAPTCHA", {})
    return captcha_settings.get(name, DEFAULTS.get(name))


def get_expire(captcha_type=None):
    """
    获取验证码过期时间。

    Args:
        captcha_type: 验证码类型，为 None 时使用 default

    Returns:
        过期时间（秒）
    """
    expire_config = get_setting("EXPIRE")
    if captcha_type and captcha_type in expire_config:
        return expire_config[captcha_type]
    return expire_config.get("default", 120)


# 全局单例缓存
_captcha_application = None


def get_captcha_application():
    """
    获取全局验证码应用实例（单例模式）。

    Returns:
        ImageCaptchaApplication 实例
    """
    global _captcha_application
    if _captcha_application is None:
        from .application import ImageCaptchaApplication

        _captcha_application = ImageCaptchaApplication()
    return _captcha_application


def reset_captcha_application():
    """重置全局验证码应用实例（主要用于测试和配置变更后）。"""
    global _captcha_application
    _captcha_application = None
