#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件管理器 - 负责应用程序配置的持久化存储
"""

import os
import json
import logging
from pathlib import Path


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
        
        # 默认配置
        self.default_config = {
            "version": "1.0.0",
            "image_scale_settings": {},  # 图片缩放比例设置
            "window_geometry": None,    # 窗口几何信息
            "recent_files": [],          # 最近打开的文件
            "watermark_defaults": {      # 水印默认设置
                "text": "",  # 空字符串，不显示默认水印文本
                "font_family": "Microsoft YaHei",  # 使用支持中文的字体
                "font_size": 24,
                "color": "#FFFFFF",
                "opacity": 80
            }
        }
        
        self.config = self.default_config.copy()
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    
                # 合并配置，确保新字段有默认值
                self.config = self._merge_configs(self.default_config, loaded_config)
                logging.info(f"配置文件加载成功: {self.config_file}")
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
        return self.config["watermark_defaults"].copy()
    
    def set_watermark_defaults(self, defaults):
        """设置水印默认设置"""
        self.config["watermark_defaults"] = defaults
        return self.save_config()


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