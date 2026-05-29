# django-tianai-captcha

天爱验证码(TAC) Django 插件 - 支持滑块、旋转、滑动还原、文字点选等多种行为验证码

## 简介

django-tianai-captcha 是天爱验证码的 Django 版本实现，支持多种行为验证码类型。
内置 tianai-captcha-web-sdk 前端 JS，安装即用，无需额外构建前端资源。

### 支持的验证码类型

| 类型 | 说明 | 容错值 |
|------|------|--------|
| **SLIDER** | 滑块验证码 | 0.02 |
| **ROTATE** | 旋转验证码 | 0.03 |
| **CONCAT** | 滑动还原验证码 | 0.05 |
| **WORD_IMAGE_CLICK** | 文字点选验证码 | 0.08 |

## 安装

```bash
pip install django-tianai-captcha

# 如果需要 Redis 缓存后端
pip install django-tianai-captcha[redis]
```

或使用 uv：

```bash
uv pip install django-tianai-captcha
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

支持 GET 和 POST 两种请求方式（前端 SDK 默认使用 POST）：

```
GET  /captcha/generate
GET  /captcha/generate?type=SLIDER
POST /captcha/generate  {"type": "ROTATE"}
POST /captcha/generate  {"type": "CONCAT"}
POST /captcha/generate  {"type": "WORD_IMAGE_CLICK"}
```

返回数据格式：

```json
{
    "code": 200,
    "msg": "success",
    "data": {
        "id": "SLIDER_xxxxx",
        "type": "SLIDER",
        "backgroundImage": "data:image/jpeg;base64,...",
        "templateImage": "data:image/png;base64,...",
        "backgroundImageWidth": 590,
        "backgroundImageHeight": 360,
        "templateImageWidth": 110,
        "templateImageHeight": 360,
        "data": {}
    }
}
```

#### 校验验证码

```
POST /captcha/check
Content-Type: application/json
```

请求体支持 `"data"` 和 `"track"` 两种 key（兼容处理，优先读取 `"data"`）：

```json
{
    "id": "验证码ID",
    "data": {
        "bgImageWidth": 590,
        "bgImageHeight": 360,
        "templateImageWidth": 110,
        "templateImageHeight": 360,
        "startTime": 1234567890,
        "stopTime": 1234567900,
        "trackList": [
            {"x": 0.0, "y": 0.0, "t": 0, "type": "down"},
            {"x": 1.5, "y": 0.2, "t": 16, "type": "move"},
            {"x": 50.0, "y": 0.5, "t": 500, "type": "up"}
        ]
    }
}
```

文字点选验证码的点击轨迹类型为 `"click"`：

```json
{
    "id": "验证码ID",
    "data": {
        "bgImageWidth": 590,
        "bgImageHeight": 360,
        "trackList": [
            {"x": 150, "y": 200, "t": 500, "type": "click"},
            {"x": 300, "y": 100, "t": 1200, "type": "click"},
            {"x": 450, "y": 250, "t": 2000, "type": "click"},
            {"x": 100, "y": 300, "t": 2800, "type": "click"}
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

本包内置了 tianai-captcha-web-sdk 前端资源（JS/CSS），安装后可直接在页面中使用，无需额外下载或构建。

#### 在模板中引入 SDK

```html
{% load static %}
<link rel="stylesheet" href="{% static 'django_tianai_captcha/tac/css/tac.css' %}">
<script src="{% static 'django_tianai_captcha/tac/js/tac.min.js' %}"></script>
```

#### 初始化验证码

```html
<div id="captcha-box"></div>
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
    const style = {};
    const tac = new window.TAC(config, style);
    tac.init();
}
</script>
```

#### 使用 Django Form Widget

本包提供了 Django Form Widget，可直接在表单中使用：

```python
from django_tianai_captcha.forms import CaptchaWidget

class MyForm(forms.Form):
    captcha = forms.CharField(widget=CaptchaWidget(captcha_type='SLIDER'))
```

Widget 会自动渲染验证码 HTML 并加载内置 SDK。

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

## Demo 测试平台

项目内置了 Django Demo 项目，可用于快速测试验证码效果：

```bash
# 安装依赖
uv pip install django pillow

# 运行 Demo 服务器
cd demo
python manage.py runserver 0.0.0.0:8000
```

访问 `http://localhost:8000/` 即可测试各类验证码。

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
├── static/                  # 内置前端 SDK
│   └── django_tianai_captcha/tac/
│       ├── js/tac.min.js    # tianai-captcha-web-sdk
│       ├── css/tac.css      # SDK 样式
│       └── images/icon.png  # SDK 图标
└── templates/               # Django 模板
    └── django_tianai_captcha/
        └── widget.html      # Form Widget 模板
```

## 内置前端资源

本包内置了 tianai-captcha-web-sdk 的构建产物，位于 `static/django_tianai_captcha/tac/` 目录下：

| 文件 | 说明 |
|------|------|
| `js/tac.min.js` | 验证码 SDK（约 42KB） |
| `css/tac.css` | SDK 样式表（约 7KB） |
| `images/icon.png` | 刷新按钮图标 |

通过 Django 的 `{% static %}` 模板标签引用即可，无需手动下载或构建。

## 许可证

MulanPSL-2.0
