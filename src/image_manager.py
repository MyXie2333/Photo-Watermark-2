#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片管理模块 - 负责图片的导入、存储和管理
"""

import os
from PIL import Image, ImageOps
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPixmap


class ImageManager(QObject):
    """图片管理器类"""
    
    # 信号定义
    images_loaded = pyqtSignal(list)  # 图片加载完成信号
    image_changed = pyqtSignal(int)   # 当前图片改变信号
    
    def __init__(self):
        super().__init__()
        self.images = []  # 存储图片路径列表
        self.current_index = -1  # 当前显示的图片索引
        self.thumbnail_size = (100, 100)  # 缩略图尺寸
        self.watermark_settings = {}  # 存储每张图片的水印设置，key为图片路径
        self.scale_settings = {}  # 存储每张图片的缩放比例设置，key为图片路径
        self.watermark_position_initialized = {}  # 存储每张图片的水印位置初始化标志，key为图片路径
        
    def load_single_image(self, file_path):
        """加载单张图片"""
        if not self._validate_image_format(file_path):
            return False
            
        # 检查文件是否已存在
        if self._is_duplicate_file(file_path):
            return "duplicate"
            
        # 如果是第一次导入，清空列表；否则累加
        if not self.images:
            self.images = [file_path]
            self.current_index = 0
            self.images_loaded.emit(self.images)
        else:
            self.images.append(file_path)
            self.current_index = len(self.images) - 1
            self.image_changed.emit(self.current_index)
        return True
        
    def load_multiple_images(self, file_paths):
        """加载多张图片"""
        valid_paths = []
        duplicate_paths = []
        
        for file_path in file_paths:
            if self._validate_image_format(file_path):
                if self._is_duplicate_file(file_path):
                    duplicate_paths.append(file_path)
                else:
                    valid_paths.append(file_path)
                
        if not valid_paths and not duplicate_paths:
            return False
            
        # 如果有重复文件，返回重复文件列表
        if duplicate_paths:
            return {"status": "has_duplicates", "duplicates": duplicate_paths, "valid_count": len(valid_paths)}
        
        # 添加新图片
        if valid_paths:
            if not self.images:
                self.images = valid_paths
                self.current_index = 0
                self.images_loaded.emit(self.images)
            else:
                original_count = len(self.images)
                self.images.extend(valid_paths)
                self.current_index = original_count
                self.image_changed.emit(self.current_index)
            return True
        return False
        
    def load_folder_images(self, folder_path):
        """加载文件夹中的所有图片"""
        if not os.path.isdir(folder_path):
            return False
            
        valid_paths = []
        duplicate_paths = []
        
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path) and self._validate_image_format(file_path):
                if self._is_duplicate_file(file_path):
                    duplicate_paths.append(file_path)
                else:
                    valid_paths.append(file_path)
                
        if not valid_paths and not duplicate_paths:
            return False
            
        # 如果有重复文件，返回重复文件列表
        if duplicate_paths:
            return {"status": "has_duplicates", "duplicates": duplicate_paths, "valid_count": len(valid_paths)}
        
        # 添加新图片
        if valid_paths:
            if not self.images:
                self.images = valid_paths
                self.current_index = 0
                self.images_loaded.emit(self.images)
            else:
                original_count = len(self.images)
                self.images.extend(valid_paths)
                self.current_index = original_count
                self.image_changed.emit(self.current_index)
            return True
        return False
        
    def _validate_image_format(self, file_path):
        """验证图片格式"""
        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        _, ext = os.path.splitext(file_path)
        return ext.lower() in valid_extensions and os.path.isfile(file_path)
        
    def _is_duplicate_file(self, file_path):
        """检查文件是否已存在"""
        # 使用绝对路径进行比较，避免路径格式差异
        abs_path = os.path.abspath(file_path)
        for existing_path in self.images:
            if os.path.abspath(existing_path) == abs_path:
                return True
        return False
        
    def get_current_image_path(self):
        """获取当前图片路径"""
        if 0 <= self.current_index < len(self.images):
            return self.images[self.current_index]
        return None
        
    def get_current_image_pixmap(self):
        """获取当前图片的QPixmap"""
        path = self.get_current_image_path()
        if path:
            return QPixmap(path)
        return None
        
    def get_thumbnail_pixmap(self, image_path):
        """获取图片的缩略图"""
        try:
            pixmap = QPixmap(image_path)
            return pixmap.scaled(*self.thumbnail_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        except:
            return None
        
    def next_image(self):
        """切换到下一张图片"""
        if len(self.images) > 0:
            self.current_index = (self.current_index + 1) % len(self.images)
            self.image_changed.emit(self.current_index)
            return True
        return False
        
    def prev_image(self):
        """切换到上一张图片"""
        if len(self.images) > 0:
            self.current_index = (self.current_index - 1) % len(self.images)
            self.image_changed.emit(self.current_index)
            return True
        return False
        
    def set_current_image(self, index):
        """设置当前显示的图片"""
        if 0 <= index < len(self.images):
            self.current_index = index
            self.image_changed.emit(self.current_index)
            return True
        return False
        
    def get_image_count(self):
        """获取图片数量"""
        return len(self.images)
        
    def clear_images(self):
        """清空图片列表"""
        self.images = []
        self.current_index = -1
        self.watermark_settings = {}
        self.watermark_position_initialized = {}
        # 注意：缩放比例设置保存在配置文件中，不清除
        self.images_loaded.emit([])
        
    def set_watermark_settings(self, image_path, settings):
        """设置指定图片的水印设置"""
        if image_path in self.images:
            self.watermark_settings[image_path] = settings
            return True
        return False
        
    def get_watermark_settings(self, image_path):
        """获取指定图片的水印设置"""
        if image_path in self.images:
            return self.watermark_settings.get(image_path, {})
        return {}
        
    def get_current_watermark_settings(self):
        """获取当前图片的水印设置"""
        current_path = self.get_current_image_path()
        if current_path:
            return self.get_watermark_settings(current_path)
        return None
    
    def set_scale_settings(self, image_path, scale):
        """设置指定图片的缩放比例"""
        if image_path:
            self.scale_settings[image_path] = scale
    
    def get_scale_settings(self, image_path):
        """获取指定图片的缩放比例"""
        if image_path:
            return self.scale_settings.get(image_path)
        return None
    
    def get_current_scale_settings(self):
        """获取当前图片的缩放比例"""
        current_path = self.get_current_image_path()
        if current_path:
            return self.scale_settings.get(current_path)
        return None
    
    def set_watermark_position_initialized(self, image_path, initialized=True):
        """设置指定图片的水印位置初始化标志"""
        if image_path:
            self.watermark_position_initialized[image_path] = initialized
    
    def get_watermark_position_initialized(self, image_path):
        """获取指定图片的水印位置初始化标志"""
        if image_path:
            return self.watermark_position_initialized.get(image_path, False)
        return False
    
    def get_current_watermark_position_initialized(self):
        """获取当前图片的水印位置初始化标志"""
        current_path = self.get_current_image_path()
        if current_path:
            return self.get_watermark_position_initialized(current_path)
        return False


if __name__ == "__main__":
    # 测试代码
    manager = ImageManager()
    print("ImageManager 测试完成")