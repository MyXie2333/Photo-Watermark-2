#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件管理器 - 负责应用程序配置的持久化存储
"""

import os
import json
import logging
import shutil
from pathlib import Path
from PyQt5.QtGui import QColor


class ConfigManager:
    """配置文件管理器类"""
    
    def __init__(self, config_file=None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        if config_file is None:
            # 使用用户配置目录
            config_dir = Path.home() / ".photo_watermark2"
            config_dir.mkdir(exist_ok=True)
            self.config_file = config_dir / "settings.json"
        else:
            self.config_file = Path(config_file)
        
        # 确保配置文件目录存在
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 设置模板目录
        app_dir = Path(__file__).parent.parent
        self.template_dir = app_dir / "template"
        
        # 确保模板目录存在
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # 默认配置
        self.default_config = {
            "version": "1.0.0",
            "image_scale_settings": {},  # 图片缩放比例设置
            "window_geometry": None,    # 窗口几何信息
            "recent_files": [],          # 最近打开的文件
            "watermark_defaults": {      # 水印默认设置
                "text": "",  # 空字符串，不显示默认水印文本
                "font_family": "Microsoft YaHei",  # 使用支持中文的字体
                "font_size": 32,
                "color": "#0000FF",
                "opacity": 80
            },
            "watermark_templates": {     # 水印模板
                "text": {},              # 文字水印模板
                "image": {}              # 图片水印模板
            },
            "last_watermark_settings": None,  # 上一次关闭时的水印设置
            "default_template": None,    # 默认模板 (格式: {"type": "text|image", "name": "模板名"})
            "load_last_settings": True   # 是否加载上一次关闭时的设置
        }
        
        self.config = self.default_config.copy()
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        try:
            if self.config_file.exists():
                try:
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        loaded_config = json.load(f)
                        
                    # 合并配置，确保新字段有默认值
                    self.config = self._merge_configs(self.default_config, loaded_config)
                    logging.info(f"配置文件加载成功: {self.config_file}")
                except json.JSONDecodeError as e:
                    logging.error(f"配置文件格式错误: {e}")
                    # 配置文件格式错误，创建新的默认配置文件
                    self.config = self.default_config.copy()
                    self.save_config()
                    logging.info(f"创建新的默认配置文件: {self.config_file}")
            else:
                # 配置文件不存在，使用默认配置
                self.save_config()
                logging.info(f"创建默认配置文件: {self.config_file}")
                
        except Exception as e:
            logging.error(f"配置文件加载失败: {e}")
            # 使用默认配置
            self.config = self.default_config.copy()
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logging.info(f"配置文件保存成功: {self.config_file}")
            return True
        except Exception as e:
            logging.error(f"配置文件保存失败: {e}")
            return False
    
    def _merge_configs(self, default, loaded):
        """合并配置，确保所有字段都存在"""
        merged = default.copy()
        
        for key, value in loaded.items():
            if key in merged:
                if isinstance(merged[key], dict) and isinstance(value, dict):
                    # 递归合并字典
                    merged[key] = self._merge_configs(merged[key], value)
                else:
                    merged[key] = value
        
        return merged
    
    def get_image_scale(self, image_path):
        """
        获取图片的缩放比例
        
        Args:
            image_path: 图片路径
            
        Returns:
            float: 缩放比例，如果不存在则返回None
        """
        # 使用绝对路径作为key
        abs_path = str(Path(image_path).resolve())
        return self.config["image_scale_settings"].get(abs_path)
    
    def set_image_scale(self, image_path, scale):
        """
        设置图片的缩放比例
        
        Args:
            image_path: 图片路径
            scale: 缩放比例
            
        Returns:
            bool: 是否保存成功
        """
        # 使用绝对路径作为key
        abs_path = str(Path(image_path).resolve())
        self.config["image_scale_settings"][abs_path] = scale
        return self.save_config()
    
    def remove_image_scale(self, image_path):
        """
        移除图片的缩放比例设置
        
        Args:
            image_path: 图片路径
            
        Returns:
            bool: 是否移除成功
        """
        abs_path = str(Path(image_path).resolve())
        if abs_path in self.config["image_scale_settings"]:
            del self.config["image_scale_settings"][abs_path]
            return self.save_config()
        return True
    
    def clear_all_scales(self):
        """清除所有图片的缩放比例设置"""
        self.config["image_scale_settings"] = {}
        return self.save_config()
    
    def get_window_geometry(self):
        """获取窗口几何信息"""
        return self.config.get("window_geometry")
    
    def set_window_geometry(self, geometry):
        """设置窗口几何信息"""
        self.config["window_geometry"] = geometry
        return self.save_config()
    
    def add_recent_file(self, file_path):
        """添加最近打开的文件"""
        abs_path = str(Path(file_path).resolve())
        
        # 移除重复项
        if abs_path in self.config["recent_files"]:
            self.config["recent_files"].remove(abs_path)
        
        # 添加到开头
        self.config["recent_files"].insert(0, abs_path)
        
        # 限制最近文件数量
        self.config["recent_files"] = self.config["recent_files"][:10]
        
        return self.save_config()
    
    def get_recent_files(self):
        """获取最近打开的文件列表"""
        return self.config["recent_files"]
    
    def get_watermark_defaults(self):
        """获取水印默认设置"""
        defaults = self.config["watermark_defaults"].copy()
        if defaults and "color" in defaults:
            # 确保颜色是QColor对象
            color = defaults["color"]
            if isinstance(color, str):
                # 如果是字符串，转换为QColor对象
                defaults["color"] = QColor(color)
            elif isinstance(color, (tuple, list)) and len(color) >= 3:
                # 如果是元组或列表，转换为QColor对象
                defaults["color"] = QColor(color[0], color[1], color[2])
        
        return defaults
    
    def set_watermark_defaults(self, defaults):
        """设置水印默认设置"""
        # 需要将QColor对象转换为字符串格式，以便JSON序列化
        if defaults and isinstance(defaults.get('color'), QColor):
            # 创建副本以避免修改原始设置
            defaults_copy = defaults.copy()
            defaults_copy['color'] = defaults_copy['color'].name()
            self.config["watermark_defaults"] = defaults_copy
        else:
            self.config["watermark_defaults"] = defaults
        
        return self.save_config()
    
    def save_watermark_template(self, template_type, template_name, template_settings):
        """
        保存水印模板
        
        Args:
            template_type: 模板类型，"text"或"image"
            template_name: 模板名称
            template_settings: 模板设置
            
        Returns:
            bool: 是否保存成功
        """
        if template_type not in ["text", "image"]:
            return False
        
        # 需要将QColor对象转换为字符串格式，以便JSON序列化
        if template_settings:
            # 创建副本以避免修改原始设置
            settings_copy = template_settings.copy()
            
            # 处理主颜色
            if isinstance(settings_copy.get('color'), QColor):
                settings_copy['color'] = settings_copy['color'].name()
            
            # 处理描边颜色
            if isinstance(settings_copy.get('outline_color'), QColor):
                settings_copy['outline_color'] = settings_copy['outline_color'].name()
            
            # 处理阴影颜色
            if isinstance(settings_copy.get('shadow_color'), QColor):
                settings_copy['shadow_color'] = settings_copy['shadow_color'].name()
            
            template_settings = settings_copy
        
        # 确保模板字典存在
        if "watermark_templates" not in self.config:
            self.config["watermark_templates"] = {"text": {}, "image": {}}
        
        # 保存模板
        self.config["watermark_templates"][template_type][template_name] = template_settings
        
        # 获取当前模板总数
        text_templates = self.config["watermark_templates"]["text"]
        image_templates = self.config["watermark_templates"]["image"]
        total_templates = len(text_templates) + len(image_templates)
        
        # 如果这是第一个模板，自动设置为默认模板
        if self.config["default_template"] is None:
            self.config["default_template"] = {"type": template_type, "name": template_name}
        # 如果只有一个模板，且没有默认模板，自动设置为默认模板
        elif total_templates == 1 and self.config["default_template"] is None:
            self.config["default_template"] = {"type": template_type, "name": template_name}
        
        return self.save_config()
    
    def load_watermark_template(self, template_type, template_name):
        """
        加载水印模板
        
        Args:
            template_type: 模板类型，"text"或"image"
            template_name: 模板名称
            
        Returns:
            dict: 模板设置，如果不存在则返回None
        """
        if template_type not in ["text", "image"]:
            return None
        
        try:
            template_settings = self.config["watermark_templates"][template_type].get(template_name)
            if template_settings and "color" in template_settings:
                # 确保颜色是QColor对象
                color = template_settings["color"]
                if isinstance(color, str):
                    # 如果是字符串，转换为QColor对象
                    template_settings["color"] = QColor(color)
                elif isinstance(color, (tuple, list)) and len(color) >= 3:
                    # 如果是元组或列表，转换为QColor对象
                    template_settings["color"] = QColor(color[0], color[1], color[2])
            
            # 同样处理描边颜色和阴影颜色
            if template_settings and "outline_color" in template_settings:
                outline_color = template_settings["outline_color"]
                if isinstance(outline_color, (tuple, list)) and len(outline_color) >= 3:
                    template_settings["outline_color"] = QColor(outline_color[0], outline_color[1], outline_color[2])
            
            if template_settings and "shadow_color" in template_settings:
                shadow_color = template_settings["shadow_color"]
                if isinstance(shadow_color, (tuple, list)) and len(shadow_color) >= 3:
                    template_settings["shadow_color"] = QColor(shadow_color[0], shadow_color[1], shadow_color[2])
            
            return template_settings
        except KeyError:
            return None
    
    def delete_watermark_template(self, template_type, template_name):
        """
        删除水印模板
        
        Args:
            template_type: 模板类型，"text"或"image"
            template_name: 模板名称
            
        Returns:
            bool: 是否删除成功
        """
        if template_type not in ["text", "image"]:
            return False
        
        try:
            if template_name in self.config["watermark_templates"][template_type]:
                del self.config["watermark_templates"][template_type][template_name]
                
                # 如果删除的是默认模板，清除默认模板设置
                if (self.config["default_template"] and 
                    self.config["default_template"]["type"] == template_type and 
                    self.config["default_template"]["name"] == template_name):
                    self.config["default_template"] = None
                
                return self.save_config()
            return False
        except KeyError:
            return False
    
    def get_all_watermark_templates(self):
        """
        获取所有水印模板
        
        Returns:
            dict: 所有水印模板，格式为 {"text": {...}, "image": {...}}
        """
        return self.config.get("watermark_templates", {"text": {}, "image": {}})
    
    def get_template_names(self, template_type):
        """
        获取指定类型的所有模板名称
        
        Args:
            template_type: 模板类型，"text"或"image"
            
        Returns:
            list: 模板名称列表
        """
        if template_type not in ["text", "image"]:
            return []
        
        try:
            return list(self.config["watermark_templates"][template_type].keys())
        except KeyError:
            return []
    
    def set_default_template(self, template_type, template_name):
        """
        设置默认模板
        
        Args:
            template_type: 模板类型，"text"或"image"
            template_name: 模板名称
            
        Returns:
            bool: 是否设置成功
        """
        if template_type not in ["text", "image"]:
            return False
        
        try:
            if template_name in self.config["watermark_templates"][template_type]:
                self.config["default_template"] = {"type": template_type, "name": template_name}
                return self.save_config()
            return False
        except KeyError:
            return False
    
    def get_default_template(self):
        """
        获取默认模板
        
        Returns:
            dict: 默认模板信息，格式为 {"type": "text|image", "name": "模板名", "settings": {...}}
                 如果没有默认模板则返回None
        """
        if not self.config["default_template"]:
            return None
        
        template_type = self.config["default_template"]["type"]
        template_name = self.config["default_template"]["name"]
        
        template_settings = self.load_watermark_template(template_type, template_name)
        if template_settings:
            return {
                "type": template_type,
                "name": template_name,
                "settings": template_settings
            }
        return None
    
    def set_last_watermark_settings(self, watermark_settings):
        """
        设置上一次关闭时的水印设置
        
        Args:
            watermark_settings: 水印设置
            
        Returns:
            bool: 是否保存成功
        """
        # 需要将QColor对象转换为字符串格式，以便JSON序列化
        if watermark_settings and isinstance(watermark_settings.get('color'), QColor):
            # 创建副本以避免修改原始设置
            settings_copy = watermark_settings.copy()
            settings_copy['color'] = settings_copy['color'].name()
            self.config["last_watermark_settings"] = settings_copy
        else:
            self.config["last_watermark_settings"] = watermark_settings
        
        return self.save_config()
    
    def get_last_watermark_settings(self):
        """
        获取上一次关闭时的水印设置
        
        Returns:
            dict: 上一次关闭时的水印设置，如果不存在则返回None
        """
        last_settings = self.config.get("last_watermark_settings")
        if last_settings and "color" in last_settings:
            # 确保颜色是QColor对象
            color = last_settings["color"]
            if isinstance(color, str):
                # 如果是字符串，转换为QColor对象
                last_settings["color"] = QColor(color)
            elif isinstance(color, (tuple, list)) and len(color) >= 3:
                # 如果是元组或列表，转换为QColor对象
                last_settings["color"] = QColor(color[0], color[1], color[2])
        
        # 同样处理描边颜色和阴影颜色
        if last_settings and "outline_color" in last_settings:
            outline_color = last_settings["outline_color"]
            if isinstance(outline_color, (tuple, list)) and len(outline_color) >= 3:
                last_settings["outline_color"] = QColor(outline_color[0], outline_color[1], outline_color[2])
        
        if last_settings and "shadow_color" in last_settings:
            shadow_color = last_settings["shadow_color"]
            if isinstance(shadow_color, (tuple, list)) and len(shadow_color) >= 3:
                last_settings["shadow_color"] = QColor(shadow_color[0], shadow_color[1], shadow_color[2])
        
        return last_settings
    
    def set_load_last_settings(self, load_last):
        """
        设置是否加载上一次关闭时的设置
        
        Args:
            load_last: 是否加载上一次关闭时的设置
            
        Returns:
            bool: 是否保存成功
        """
        self.config["load_last_settings"] = load_last
        return self.save_config()
    
    def get_load_last_settings(self):
        """
        获取是否加载上一次关闭时的设置
        
        Returns:
            bool: 是否加载上一次关闭时的设置
        """
        return self.config.get("load_last_settings", True)
    
    def set_template_directory(self, directory):
        """
        设置模板目录
        
        Args:
            directory: 新的模板目录路径
            
        Returns:
            bool: 是否设置成功
        """
        try:
            new_dir = Path(directory)
            if not new_dir.exists():
                new_dir.mkdir(parents=True, exist_ok=True)
            
            # 如果目录更改，需要将现有模板复制到新目录
            if new_dir != self.template_dir:
                # 复制所有模板文件到新目录
                for template_type in ["text", "image"]:
                    type_dir = self.template_dir / template_type
                    if type_dir.exists():
                        new_type_dir = new_dir / template_type
                        new_type_dir.mkdir(parents=True, exist_ok=True)
                        
                        # 复制所有模板文件
                        for template_file in type_dir.glob("*.json"):
                            shutil.copy2(template_file, new_type_dir)
            
            self.template_dir = new_dir
            return True
        except Exception as e:
            logging.error(f"设置模板目录失败: {e}")
            return False
    
    def get_template_directory(self):
        """
        获取模板目录
        
        Returns:
            str: 模板目录路径
        """
        return str(self.template_dir)
    
    def save_watermark_template_to_file(self, template_type, template_name, template_settings):
        """
        将水印模板保存到文件
        
        Args:
            template_type: 模板类型，"text"或"image"
            template_name: 模板名称
            template_settings: 模板设置
            
        Returns:
            bool: 是否保存成功
        """
        if template_type not in ["text", "image"]:
            return False
        
        try:
            # 创建类型子目录
            type_dir = self.template_dir / template_type
            type_dir.mkdir(parents=True, exist_ok=True)
            
            # 需要将QColor对象转换为字符串格式，以便JSON序列化
            if template_settings:
                # 创建副本以避免修改原始设置
                settings_copy = template_settings.copy()
                
                # 处理主颜色
                if isinstance(settings_copy.get('color'), QColor):
                    settings_copy['color'] = settings_copy['color'].name()
                
                # 处理描边颜色
                if isinstance(settings_copy.get('outline_color'), QColor):
                    settings_copy['outline_color'] = settings_copy['outline_color'].name()
                
                # 处理阴影颜色
                if isinstance(settings_copy.get('shadow_color'), QColor):
                    settings_copy['shadow_color'] = settings_copy['shadow_color'].name()
                
                template_settings = settings_copy
            
            # 保存到文件
            template_file = type_dir / f"{template_name}.json"
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template_settings, f, indent=2, ensure_ascii=False)
            
            # 同时保存到配置文件中（为了兼容性）
            self.save_watermark_template(template_type, template_name, template_settings)
            
            return True
        except Exception as e:
            logging.error(f"保存模板文件失败: {e}")
            return False
    
    def load_watermark_template_from_file(self, template_type, template_name):
        """
        从文件加载水印模板
        
        Args:
            template_type: 模板类型，"text"或"image"
            template_name: 模板名称
            
        Returns:
            dict: 模板设置，如果不存在则返回None
        """
        if template_type not in ["text", "image"]:
            return None
        
        try:
            # 从文件加载
            type_dir = self.template_dir / template_type
            template_file = type_dir / f"{template_name}.json"
            
            if template_file.exists():
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_settings = json.load(f)
                
                # 处理主颜色
                if template_settings and "color" in template_settings:
                    color = template_settings["color"]
                    if isinstance(color, str):
                        # 如果是字符串，转换为QColor对象
                        template_settings["color"] = QColor(color)
                    elif isinstance(color, (tuple, list)) and len(color) >= 3:
                        # 如果是元组或列表，转换为QColor对象
                        template_settings["color"] = QColor(color[0], color[1], color[2])
                
                # 处理描边颜色
                if template_settings and "outline_color" in template_settings:
                    outline_color = template_settings["outline_color"]
                    if isinstance(outline_color, str):
                        # 如果是字符串，转换为QColor对象
                        template_settings["outline_color"] = QColor(outline_color)
                    elif isinstance(outline_color, (tuple, list)) and len(outline_color) >= 3:
                        # 如果是元组或列表，转换为QColor对象
                        template_settings["outline_color"] = QColor(outline_color[0], outline_color[1], outline_color[2])
                
                # 处理阴影颜色
                if template_settings and "shadow_color" in template_settings:
                    shadow_color = template_settings["shadow_color"]
                    if isinstance(shadow_color, str):
                        # 如果是字符串，转换为QColor对象
                        template_settings["shadow_color"] = QColor(shadow_color)
                    elif isinstance(shadow_color, (tuple, list)) and len(shadow_color) >= 3:
                        # 如果是元组或列表，转换为QColor对象
                        template_settings["shadow_color"] = QColor(shadow_color[0], shadow_color[1], shadow_color[2])
                
                return template_settings
            return None
        except Exception as e:
            logging.error(f"加载模板文件失败: {e}")
            return None
    
    def delete_watermark_template_file(self, template_type, template_name):
        """
        删除水印模板文件
        
        Args:
            template_type: 模板类型，"text"或"image"
            template_name: 模板名称
            
        Returns:
            dict: 删除结果，包含成功状态和是否需要选择新默认模板的信息
        """
        if template_type not in ["text", "image"]:
            return {"success": False, "need_select_default": False}
        
        try:
            # 检查是否是默认模板
            is_default_template = (self.config["default_template"] and 
                                  self.config["default_template"]["type"] == template_type and 
                                  self.config["default_template"]["name"] == template_name)
            
            # 删除文件
            type_dir = self.template_dir / template_type
            template_file = type_dir / f"{template_name}.json"
            
            if template_file.exists():
                template_file.unlink()
            
            # 同时从配置文件中删除（为了兼容性）
            self.delete_watermark_template(template_type, template_name)
            
            # 获取删除后的模板列表
            remaining_templates = self.get_all_template_files(template_type)
            
            # 如果删除的是默认模板，需要处理默认模板设置
            result = {"success": True, "need_select_default": False}
            
            if is_default_template:
                # 如果删除的是默认模板
                if len(remaining_templates) == 0:
                    # 没有剩余模板，清除默认模板设置
                    self.config["default_template"] = None
                    result["need_select_default"] = False
                elif len(remaining_templates) == 1:
                    # 只有一个剩余模板，自动设置为默认模板
                    self.config["default_template"] = {"type": template_type, "name": remaining_templates[0]}
                    result["need_select_default"] = False
                else:
                    # 有多个剩余模板，需要用户选择
                    self.config["default_template"] = None
                    result["need_select_default"] = True
                    result["remaining_templates"] = remaining_templates
                    result["template_type"] = template_type
                
                # 保存配置
                self.save_config()
            else:
                # 如果删除的不是默认模板，检查是否只剩下一个模板
                if len(remaining_templates) == 1 and self.config["default_template"] is None:
                    # 只有一个模板且没有默认模板，自动设置为默认模板
                    self.config["default_template"] = {"type": template_type, "name": remaining_templates[0]}
                    self.save_config()
            
            return result
        except Exception as e:
            logging.error(f"删除模板文件失败: {e}")
            return {"success": False, "need_select_default": False}
    
    def get_all_template_files(self, template_type):
        """
        获取指定类型的所有模板文件
        
        Args:
            template_type: 模板类型，"text"或"image"
            
        Returns:
            list: 模板名称列表
        """
        if template_type not in ["text", "image"]:
            return []
        
        try:
            type_dir = self.template_dir / template_type
            if not type_dir.exists():
                return []
            
            # 获取所有.json文件，去除扩展名
            template_files = []
            for template_file in type_dir.glob("*.json"):
                template_files.append(template_file.stem)
            
            return template_files
        except Exception as e:
            logging.error(f"获取模板文件列表失败: {e}")
            return []
    
    def migrate_templates_to_files(self):
        """
        将配置文件中的模板迁移到文件系统中
        
        Returns:
            bool: 是否迁移成功
        """
        try:
            # 获取配置文件中的所有模板
            all_templates = self.get_all_watermark_templates()
            
            # 迁移文字水印模板
            for template_name, template_settings in all_templates.get("text", {}).items():
                self.save_watermark_template_to_file("text", template_name, template_settings)
            
            # 迁移图片水印模板
            for template_name, template_settings in all_templates.get("image", {}).items():
                self.save_watermark_template_to_file("image", template_name, template_settings)
            
            return True
        except Exception as e:
            logging.error(f"迁移模板到文件失败: {e}")
            return False


# 全局配置管理器实例
_config_manager = None


def get_config_manager(config_file=None):
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_file)
    return _config_manager


if __name__ == "__main__":
    # 测试代码
    config = get_config_manager()
    
    # 测试缩放比例设置
    test_image = "/path/to/test/image.jpg"
    config.set_image_scale(test_image, 1.5)
    
    scale = config.get_image_scale(test_image)
    print(f"测试图片缩放比例: {scale}")
    
    # 测试窗口几何信息
    config.set_window_geometry({"x": 100, "y": 100, "width": 800, "height": 600})
    geometry = config.get_window_geometry()
    print(f"窗口几何信息: {geometry}")
    
    print("配置文件管理器测试完成")