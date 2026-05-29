"""
验证码应用核心模块。

负责验证码的生成和校验流程编排，是对外提供的主要接口。
设计参考 Java 版 ImageCaptchaApplication 和 DefaultImageCaptchaApplication。
"""

import uuid
import time
import logging

from .conf import (
    get_setting,
    get_expire,
    SLIDER,
    CAPTCHA_TYPES,
)

logger = logging.getLogger(__name__)


class ApiResponse:
    """统一的 API 响应格式，与 Java 版保持一致。"""

    SUCCESS_CODE = 200
    ERROR_CODE = 500
    CHECK_ERROR_CODE = 400

    def __init__(self, code, msg="", data=None):
        self.code = code
        self.msg = msg
        self.data = data

    @property
    def is_success(self):
        return self.code == self.SUCCESS_CODE

    def to_dict(self):
        result = {"code": self.code, "msg": self.msg}
        if self.data is not None:
            result["data"] = self.data
        return result

    @classmethod
    def of_success(cls, data=None, msg="success"):
        return cls(cls.SUCCESS_CODE, msg, data)

    @classmethod
    def of_error(cls, msg="error"):
        return cls(cls.ERROR_CODE, msg)

    @classmethod
    def of_check_error(cls, msg="check error"):
        return cls(cls.CHECK_ERROR_CODE, msg)


class ImageCaptchaVO:
    """
    验证码视图对象，与 Java 版 ImageCaptchaVO 对应。

    该对象用于返回给前端的验证码数据，包含验证码 ID、图片数据等信息，
    但不包含验证码的正确答案（答案仅缓存在服务端）。
    """

    def __init__(
        self,
        id=None,
        type=None,
        backgroundImage=None,
        templateImage=None,
        backgroundImageTag=None,
        templateImageTag=None,
        backgroundImageWidth=None,
        backgroundImageHeight=None,
        templateImageWidth=None,
        templateImageHeight=None,
        data=None,
    ):
        self.id = id
        self.type = type
        self.backgroundImage = backgroundImage
        self.templateImage = templateImage
        self.backgroundImageTag = backgroundImageTag
        self.templateImageTag = templateImageTag
        self.backgroundImageWidth = backgroundImageWidth
        self.backgroundImageHeight = backgroundImageHeight
        self.templateImageWidth = templateImageWidth
        self.templateImageHeight = templateImageHeight
        self.data = data

    def to_dict(self):
        result = {
            "id": self.id,
            "type": self.type,
            "backgroundImage": self.backgroundImage,
            "templateImage": self.templateImage,
        }
        if self.backgroundImageTag is not None:
            result["backgroundImageTag"] = self.backgroundImageTag
        if self.templateImageTag is not None:
            result["templateImageTag"] = self.templateImageTag
        if self.backgroundImageWidth is not None:
            result["backgroundImageWidth"] = self.backgroundImageWidth
        if self.backgroundImageHeight is not None:
            result["backgroundImageHeight"] = self.backgroundImageHeight
        if self.templateImageWidth is not None:
            result["templateImageWidth"] = self.templateImageWidth
        if self.templateImageHeight is not None:
            result["templateImageHeight"] = self.templateImageHeight
        if self.data is not None:
            result["data"] = self.data
        return result


class ImageCaptchaApplication:
    """
    验证码应用主类。

    负责编排验证码生成和校验的完整流程：
    - 生成验证码：调用生成器生成图片 -> 调用验证器生成校验数据 -> 缓存校验数据 -> 返回 VO
    - 校验验证码：从缓存获取校验数据 -> 调用验证器校验 -> 返回校验结果

    对应 Java 版的 DefaultImageCaptchaApplication。
    """

    def __init__(self):
        from .cache import get_cache_store
        from .generator import MultiImageCaptchaGenerator
        from .validator import SimpleImageCaptchaValidator
        from .resource import DefaultImageCaptchaResourceManager, LocalMemoryResourceStore

        # 初始化资源管理器
        self._resource_store = LocalMemoryResourceStore()
        self._resource_manager = DefaultImageCaptchaResourceManager(self._resource_store)

        # 初始化生成器
        self._generator = MultiImageCaptchaGenerator(self._resource_manager)

        # 初始化验证器
        self._validator = SimpleImageCaptchaValidator()

        # 初始化缓存
        self._cache_store = get_cache_store()

        # 缓存前缀
        self._prefix = get_setting("PREFIX")

        # 初始化默认资源
        if get_setting("INIT_DEFAULT_RESOURCE"):
            self._init_default_resources()

        # 初始化字体
        self._init_fonts()

        logger.info("ImageCaptchaApplication initialized successfully")

    def _init_default_resources(self):
        """初始化系统自带的默认资源（背景图和模板）。"""
        from .resource import DefaultBuiltInResources

        DefaultBuiltInResources.init(self._resource_store)

    def _init_fonts(self):
        """初始化字体文件。"""
        font_paths = get_setting("FONT_PATH")
        if not font_paths:
            return

        from .resource import Resource

        for font_path in font_paths:
            try:
                resource = Resource(type="file", data=font_path)
                self._resource_manager.add_font(resource)
                logger.info(f"Font loaded: {font_path}")
            except Exception as e:
                logger.warning(f"Failed to load font {font_path}: {e}")

    def _generate_id(self, captcha_type):
        """
        生成验证码唯一标识。

        格式为 TYPE_UUID，与 Java 版保持一致。

        Args:
            captcha_type: 验证码类型

        Returns:
            格式化的 ID 字符串
        """
        return f"{captcha_type}_{uuid.uuid4().hex}"

    def _get_cache_key(self, captcha_id):
        """
        获取缓存 key。

        Args:
            captcha_id: 验证码 ID

        Returns:
            带前缀的缓存 key
        """
        return f"{self._prefix}:{captcha_id}"

    def generate_captcha(self, captcha_type=None):
        """
        生成验证码。

        流程：
        1. 确定验证码类型
        2. 调用生成器生成图片
        3. 调用验证器生成校验数据
        4. 将校验数据存入缓存
        5. 构建并返回 ImageCaptchaVO

        Args:
            captcha_type: 验证码类型，为 None 时使用默认类型

        Returns:
            ApiResponse[ImageCaptchaVO]
        """
        if captcha_type is None:
            captcha_type = get_setting("DEFAULT_TYPE")

        if captcha_type not in CAPTCHA_TYPES:
            return ApiResponse.of_error(f"Unsupported captcha type: {captcha_type}")

        try:
            # 1. 生成验证码 ID
            captcha_id = self._generate_id(captcha_type)

            # 2. 调用生成器生成验证码图片
            captcha_info = self._generator.generate_captcha_image(captcha_type)
            if captcha_info is None:
                return ApiResponse.of_error("Failed to generate captcha image")

            # 3. 调用验证器生成校验数据
            valid_data = self._validator.generate_valid_data(captcha_info)

            # 4. 将校验数据存入缓存
            cache_key = self._get_cache_key(captcha_id)
            expire = get_expire(captcha_type)
            self._cache_store.set_cache(cache_key, {
                "valid_data": valid_data,
                "type": captcha_type,
            }, expire)

            # 5. 构建 VO（不包含答案）
            vo = ImageCaptchaVO(
                id=captcha_id,
                type=captcha_type,
                backgroundImage=captcha_info.get("backgroundImage"),
                templateImage=captcha_info.get("templateImage"),
                backgroundImageTag=captcha_info.get("backgroundImageTag"),
                templateImageTag=captcha_info.get("templateImageTag"),
                backgroundImageWidth=captcha_info.get("backgroundImageWidth"),
                backgroundImageHeight=captcha_info.get("backgroundImageHeight"),
                templateImageWidth=captcha_info.get("templateImageWidth"),
                templateImageHeight=captcha_info.get("templateImageHeight"),
                data=captcha_info.get("data"),
            )

            return ApiResponse.of_success(vo.to_dict())

        except Exception as e:
            logger.exception(f"Error generating captcha: {e}")
            return ApiResponse.of_error(str(e))

    def matching(self, captcha_id, track_data):
        """
        校验验证码。

        流程：
        1. 从缓存获取校验数据（一次性读取并删除）
        2. 调用验证器校验轨迹数据
        3. 返回校验结果

        Args:
            captcha_id: 验证码 ID
            track_data: 前端传来的轨迹数据（ImageCaptchaTrack）

        Returns:
            ApiResponse
        """
        try:
            # 1. 从缓存获取校验数据
            cache_key = self._get_cache_key(captcha_id)
            cached = self._cache_store.get_and_remove_cache(cache_key)
            if cached is None:
                return ApiResponse.of_check_error("验证码已过期或不存在")

            valid_data = cached.get("valid_data", {})
            captcha_type = cached.get("type", SLIDER)

            # 2. 参数校验
            if not track_data:
                return ApiResponse.of_check_error("轨迹数据不能为空")

            # 3. 基础校验
            result = self._validator.valid(track_data, valid_data, captcha_type)
            if not result:
                return ApiResponse.of_check_error("验证码校验失败")

            # 4. 轨迹行为校验（可选）
            if get_setting("TRACK_VALIDATION_ENABLED"):
                from .validator import BasicCaptchaTrackValidator

                track_validator = BasicCaptchaTrackValidator()
                track_result = track_validator.valid(track_data, captcha_type)
                if not track_result:
                    return ApiResponse.of_check_error("轨迹行为异常，请重新验证")

            # 5. 二次验证（可选）
            secondary_config = get_setting("SECONDARY")
            token = None
            if secondary_config and secondary_config.get("ENABLED"):
                token = uuid.uuid4().hex
                secondary_key = f"{secondary_config['KEY_PREFIX']}:{token}"
                self._cache_store.set_cache(
                    secondary_key,
                    {"captcha_id": captcha_id, "type": captcha_type},
                    secondary_config.get("EXPIRE", 120),
                )

            response_data = {}
            if token:
                response_data["token"] = token

            return ApiResponse.of_success(response_data)

        except Exception as e:
            logger.exception(f"Error matching captcha: {e}")
            return ApiResponse.of_error(str(e))

    def secondary_verification(self, token):
        """
        二次验证。

        用于在业务接口中验证客户端传来的 token 是否合法。

        Args:
            token: 客户端传来的二次验证 token

        Returns:
            bool: token 是否有效
        """
        secondary_config = get_setting("SECONDARY")
        if not secondary_config or not secondary_config.get("ENABLED"):
            return False

        secondary_key = f"{secondary_config['KEY_PREFIX']}:{token}"
        cached = self._cache_store.get_and_remove_cache(secondary_key)
        return cached is not None

    def get_captcha_type_by_id(self, captcha_id):
        """
        通过验证码 ID 获取验证码类型。

        ID 格式为 TYPE_UUID，因此取下划线前的部分即为类型。

        Args:
            captcha_id: 验证码 ID

        Returns:
            验证码类型字符串
        """
        if captcha_id and "_" in captcha_id:
            return captcha_id.split("_", 1)[0]
        return None

    @property
    def resource_store(self):
        return self._resource_store

    @property
    def generator(self):
        return self._generator

    @property
    def validator(self):
        return self._validator

    @property
    def cache_store(self):
        return self._cache_store
