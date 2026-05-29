# django-tianai-captcha

天爱验证码(TAC) Django 插件 - 支持滑块、旋转、滑动还原、文字点选等多种行为验证码

## 简介

django-tianai-captcha 是 [tianai-captcha](https://github.com/dromara/tianai-captcha) 的 Django 版本实现，
支持多种行为验证码类型，可无缝对接 tianai-captcha-web-sdk 前端。

### 支持的验证码类型

- **SLIDER** - 滑块验证码
- **ROTATE** - 旋转验证码
- **CONCAT** - 滑动还原验证码
- **WORD_IMAGE_CLICK** - 文字点选验证码

## 安装

```bash
pip install django-tianai-captcha

# 如果需要 Redis 缓存后端
pip install django-tianai-captcha[redis]
```

## 快速开始

### 1. 添加应用到 INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    ...
    'django_tianai_captcha',
]
```

### 2. 配置 URL

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    ...
    path('captcha/', include('django_tianai_captcha.urls')),
]
```

### 3. 配置（可选）

```python
# settings.py
CAPTCHA = {
    # 缓存 key 前缀
    "PREFIX": "captcha",

    # 验证码过期时间（秒）
    "EXPIRE": {
        "default": 120,
        "WORD_IMAGE_CLICK": 180,
    },

    # 是否加载系统自带资源
    "INIT_DEFAULT_RESOURCE": True,

    # 缓存后端: "local" 或 "redis"
    "CACHE_BACKEND": "local",

    # Redis 连接配置（当 CACHE_BACKEND="redis" 时使用）
    "REDIS_URL": "redis://localhost:6379/0",

    # 默认验证码类型
    "DEFAULT_TYPE": "SLIDER",

    # 容错值
    "TOLERANT": 0.02,

    # 是否启用轨迹行为校验
    "TRACK_VALIDATION_ENABLED": True,

    # 二次验证配置
    "SECONDARY": {
        "ENABLED": False,
        "EXPIRE": 120,
        "KEY_PREFIX": "captcha:secondary",
    },

    # 频率限制
    "RATE_LIMIT": {
        "ENABLED": True,
        "RATE": 10,       # 每分钟最大请求数
        "PERIOD": 60,     # 统计周期（秒）
    },
}
```

### 4. 使用 API

#### 生成验证码

```
GET /captcha/generate
GET /captcha/generate?type=SLIDER
GET /captcha/generate?type=ROTATE
GET /captcha/generate?type=CONCAT
GET /captcha/generate?type=WORD_IMAGE_CLICK
```

#### 校验验证码

```
POST /captcha/check
Content-Type: application/json

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
            {"x": 1.5, "y": 0.2, "t": 16, "type": "MOVE"}
        ]
    }
}
```

#### 二次验证

```
POST /captcha/verify
Content-Type: application/json

{
    "token": "二次验证token"
}
```

### 5. 前端对接

使用 tianai-captcha-web-sdk 对接前端：

```html
<div id="captcha-box"></div>
<script src="load.min.js"></script>
<script>
function showCaptcha() {
    const config = {
        requestCaptchaDataUrl: "/captcha/generate",
        validCaptchaUrl: "/captcha/check",
        bindEl: "#captcha-box",
        validSuccess: (res, c, tac) => {
            tac.destroyWindow();
            console.log("验证成功", res);
        },
        validFail: (res, c, tac) => {
            tac.reloadCaptcha();
        }
    };
    window.initTAC("./tac", config).then(tac => {
        tac.init();
    });
}
</script>
```

### 6. 在代码中使用

```python
from django_tianai_captcha.conf import get_captcha_application

app = get_captcha_application()

# 生成验证码
result = app.generate_captcha("SLIDER")

# 校验验证码
result = app.matching(captcha_id, track_data)

# 二次验证
is_valid = app.secondary_verification(token)
```

## 项目结构

```
django_tianai_captcha/
├── __init__.py              # 包初始化
├── apps.py                  # Django 应用配置
├── conf.py                  # 配置模块
├── application.py           # 核心应用类
├── views.py                 # Django 视图
├── urls.py                  # URL 路由
├── middleware.py             # 中间件
├── models.py                # 数据模型
├── forms.py                 # 表单 Widget
├── admin.py                 # Admin 配置
├── cache/                   # 缓存层
│   ├── base.py              # 缓存接口
│   ├── local.py             # 本地内存缓存
│   └── redis.py             # Redis 缓存
├── generator/               # 生成器层
│   ├── base.py              # 生成器接口
│   ├── multi.py             # 多类型分发器
│   ├── slider.py            # 滑块生成器
│   ├── rotate.py            # 旋转生成器
│   ├── concat.py            # 滑动还原生成器
│   ├── word_click.py        # 文字点选生成器
│   └── utils.py             # 图像处理工具
├── validator/               # 验证器层
│   ├── simple.py            # 简单位置校验
│   └── track.py             # 轨迹行为校验
├── resource/                # 资源管理层
│   ├── store.py             # 资源存储
│   ├── manager.py           # 资源管理器
│   └── provider.py          # 资源提供者
├── resources/               # 内置资源文件
│   └── META-INF/cut-image/  # 背景图、模板、字体
├── templates/               # Django 模板
└── static/                  # 静态文件
```

## 许可证

MulanPSL-2.0
