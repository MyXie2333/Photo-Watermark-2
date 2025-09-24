#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片管理模块 - 负责图片的导入、存储和管理
"""

import os
from PIL import Image, ImageOps
from PyQt5.QtCore import QObject, pyqtSignal
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
        
    def load_single_image(self, file_path):
        """加载单张图片"""
        if not self._validate_image_format(file_path):
            return False
            
        self.images = [file_path]
        self.current_index = 0
        self.images_loaded.emit(self.images)
        return True
        
    def load_multiple_images(self, file_paths):
        """加载多张图片"""
        valid_paths = []
        for file_path in file_paths:
            if self._validate_image_format(file_path):
                valid_paths.append(file_path)
                
        if valid_paths:
            self.images = valid_paths
            self.current_index = 0
            self.images_loaded.emit(self.images)
            return True
        return False
        
    def load_folder_images(self, folder_path):
        """加载文件夹中的所有图片"""
        if not os.path.isdir(folder_path):
            return False
            
        valid_paths = []
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path) and self._validate_image_format(file_path):
                valid_paths.append(file_path)
                
        if valid_paths:
            self.images = valid_paths
            self.current_index = 0
            self.images_loaded.emit(self.images)
            return True
        return False
        
    def _validate_image_format(self, file_path):
        """验证图片格式"""
        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        _, ext = os.path.splitext(file_path)
        return ext.lower() in valid_extensions and os.path.isfile(file_path)
        
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
        """清空所有图片"""
        self.images = []
        self.current_index = -1
        self.images_loaded.emit([])


if __name__ == "__main__":
    # 测试代码
    manager = ImageManager()
    print("ImageManager 测试完成")