"""
资源存储模块。

提供验证码资源的存储抽象和本地内存实现。
"""

import random
import threading

from .provider import Resource


class ResourceStore:
    """
    资源存储接口。

    管理验证码所需的各类资源，包括背景图片、模板图片和字体。
    支持按类型和标签进行资源检索，与 Java 版 ResourceStore 对应。
    """

    def init(self, resource_manager):
        """初始化资源存储。"""
        pass

    def random_get_resource_by_type_and_tag(self, captcha_type, tag=None, quantity=1):
        """
        随机获取指定类型和标签的背景资源。

        Args:
            captcha_type: 验证码类型
            tag: 资源标签，为 None 时不做标签过滤
            quantity: 获取数量

        Returns:
            Resource 列表
        """
        return []

    def random_get_template_by_type_and_tag(self, captcha_type, tag=None, quantity=1):
        """
        随机获取指定类型和标签的模板资源。

        Args:
            captcha_type: 验证码类型
            tag: 模板标签
            quantity: 获取数量

        Returns:
            资源字典列表，每个字典包含模板的各个组件
        """
        return []


class LocalMemoryResourceStore(ResourceStore):
    """
    本地内存资源存储实现。

    使用线程安全的字典存储资源数据，适合资源数量有限的场景。
    与 Java 版 LocalMemoryResourceStore 对应。
    """

    def __init__(self):
        self._resources = {}  # type -> {tag -> [Resource]}
        self._templates = {}  # type -> {tag -> [dict]}
        self._fonts = []      # [Resource]
        self._lock = threading.Lock()

    def init(self, resource_manager):
        """初始化资源存储。"""
        pass

    def add_resource(self, captcha_type, resource):
        """
        添加背景资源。

        Args:
            captcha_type: 验证码类型
            resource: Resource 实例
        """
        with self._lock:
            if captcha_type not in self._resources:
                self._resources[captcha_type] = {}
            tag = resource.tag or "default"
            if tag not in self._resources[captcha_type]:
                self._resources[captcha_type][tag] = []
            self._resources[captcha_type][tag].append(resource)

    def add_template(self, captcha_type, template_dict, tag=None):
        """
        添加模板资源。

        Args:
            captcha_type: 验证码类型
            template_dict: 模板字典，包含 active, fixed, mask 等键
            tag: 模板标签
        """
        with self._lock:
            if captcha_type not in self._templates:
                self._templates[captcha_type] = {}
            tag = tag or "default"
            if tag not in self._templates[captcha_type]:
                self._templates[captcha_type][tag] = []
            self._templates[captcha_type][tag].append(template_dict)

    def add_font(self, resource):
        """
        添加字体资源。

        Args:
            resource: 字体 Resource 实例
        """
        with self._lock:
            self._fonts.append(resource)

    def random_get_resource_by_type_and_tag(self, captcha_type, tag=None, quantity=1):
        """随机获取指定类型和标签的背景资源。"""
        with self._lock:
            type_resources = self._resources.get(captcha_type, {})
            if not type_resources:
                return []

            # 如果指定了标签，从该标签下取
            if tag:
                resources = type_resources.get(tag, [])
            else:
                # 从所有标签下合并取
                resources = []
                for tag_resources in type_resources.values():
                    resources.extend(tag_resources)

            if not resources:
                return []

            # 随机选取
            quantity = min(quantity, len(resources))
            return random.sample(resources, quantity)

    def random_get_template_by_type_and_tag(self, captcha_type, tag=None, quantity=1):
        """随机获取指定类型和标签的模板资源。"""
        with self._lock:
            type_templates = self._templates.get(captcha_type, {})
            if not type_templates:
                return []

            if tag:
                templates = type_templates.get(tag, [])
            else:
                templates = []
                for tag_templates in type_templates.values():
                    templates.extend(tag_templates)

            if not templates:
                return []

            quantity = min(quantity, len(templates))
            return random.sample(templates, quantity)

    def get_fonts(self):
        """获取所有字体资源。"""
        with self._lock:
            return list(self._fonts)

    def clear(self):
        """清空所有资源。"""
        with self._lock:
            self._resources.clear()
            self._templates.clear()
            self._fonts.clear()
