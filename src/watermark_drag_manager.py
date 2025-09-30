#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水印拖拽管理器 - 负责处理文本水印和图片水印的共用拖拽功能
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QCursor
import math

class WatermarkDragManager:
    """水印拖拽管理器 - 处理文本水印和图片水印的共用拖拽功能"""
    
    def __init__(self, preview_widget):
        """
        初始化水印拖拽管理器
        
        Args:
            preview_widget: 预览区域的QLabel控件
        """
        
        # 拖拽相关变量
        self.is_dragging = False
        self.drag_start_pos = None
        self.watermark_offset = None
        self.preview_widget = preview_widget
        
        # 水印类型和设置引用
        self.watermark_type = "text"  # 默认文本水印
        self.original_pixmap = None  # 原始图片
        self.image_watermark_widget = None  # 图片水印控件引用
        self.text_watermark_widget = None  # 文本水印控件引用
        
        # 水印设置获取回调函数
        self.get_watermark_settings_callback = None
        self.position_changed_callback = None
        self.drag_started_callback = None
        self.drag_stopped_callback = None
        
        # 设置鼠标追踪并绑定事件
        self.preview_widget.setMouseTracking(True)
        
        # 保存原始事件处理器
        self.original_mouse_press_event = self.preview_widget.mousePressEvent
        self.original_mouse_move_event = self.preview_widget.mouseMoveEvent
        self.original_mouse_release_event = self.preview_widget.mouseReleaseEvent
        
        # 绑定自定义事件处理器
        self.preview_widget.mousePressEvent = self.on_mouse_press
        self.preview_widget.mouseMoveEvent = self.on_mouse_move
        self.preview_widget.mouseReleaseEvent = self.on_mouse_release
        
    def set_watermark_settings_callback(self, callback):
        """
        设置获取水印设置的回调函数
        
        Args:
            callback: 一个无参数函数，返回当前水印设置字典
        """
        self.get_watermark_settings_callback = callback
        
    def set_position_changed_callback(self, callback):
        """
        设置位置变化的回调函数
        
        Args:
            callback: 接收x和y坐标的函数
        """
        self.position_changed_callback = callback
        
    def set_drag_started_callback(self, callback):
        """
        设置拖拽开始的回调函数
        
        Args:
            callback: 无参数函数
        """
        self.drag_started_callback = callback
        
    def set_drag_stopped_callback(self, callback):
        """
        设置拖拽结束的回调函数
        
        Args:
            callback: 无参数函数
        """
        self.drag_stopped_callback = callback
    
    def set_watermark_type(self, watermark_type):
        """设置当前水印类型"""
        self.watermark_type = watermark_type
    
    def set_original_pixmap(self, pixmap):
        """设置原始图片"""
        self.original_pixmap = pixmap
    
    def set_watermark_widgets(self, text_widget, image_widget):
        """设置水印控件引用"""
        self.text_watermark_widget = text_widget
        self.image_watermark_widget = image_widget
    
    def on_mouse_press(self, event):
        """处理鼠标按下事件"""
        if (event.button() == Qt.LeftButton and 
            self.original_pixmap and 
            self.preview_widget):
            
            # 获取当前水印设置（需要从外部传入或通过回调获取）
            # 注意：实际使用时需要从image_manager获取当前水印设置
            # 这里为了演示，假设可以通过回调获取
            current_watermark_settings = self._get_current_watermark_settings()
            
            # 获取压缩比例
            compression_scale = current_watermark_settings.get("compression_scale", 1.0) if current_watermark_settings else 1.0
            print(f"[DEBUG] WatermarkDragManager.on_mouse_press: 获取压缩比例 compression_scale = {compression_scale}")
            
            # 当有文本水印或图片水印时都允许拖拽
            if current_watermark_settings and (
                current_watermark_settings.get("text") or 
                current_watermark_settings.get("image_path")
            ):
                self.is_dragging = True
                self.drag_start_pos = event.pos()
                
                # 获取水印位置 - 直接使用position
                if "position" in current_watermark_settings and isinstance(current_watermark_settings["position"], tuple):
                    watermark_position = current_watermark_settings["position"]
                    print(f"[DEBUG] WatermarkDragManager.on_mouse_press: 使用position元组作为水印位置: {watermark_position}")
                else:
                    # 默认位置（图片中心）
                    watermark_position = (
                        self.original_pixmap.width() // 2, 
                        self.original_pixmap.height() // 2
                    )
                    print(f"[DEBUG] WatermarkDragManager.on_mouse_press: 使用默认位置（图片中心）作为水印位置: {watermark_position}")
                
                # 保存水印偏移量
                self.watermark_offset = watermark_position
                
                # 调用拖拽开始回调
                if self.drag_started_callback:
                    self.drag_started_callback()
                
                # 更改鼠标样式为手型
                self.preview_widget.setCursor(Qt.ClosedHandCursor)
    
    def on_mouse_move(self, event):
        """处理鼠标移动事件"""
        if self.is_dragging and self.drag_start_pos and self.watermark_offset:
            # 获取当前水印设置，确保watermark_offset初始化为水印原来的位置
            current_watermark_settings = self._get_current_watermark_settings()
            
            # 获取压缩比例
            compression_scale = current_watermark_settings.get("compression_scale", 1.0) if current_watermark_settings else 1.0
            print(f"[DEBUG] WatermarkDragManager.on_mouse_move: 获取压缩比例 compression_scale = {compression_scale}")
            
            if current_watermark_settings:
                # 获取水印位置 - 直接使用position
                if "position" in current_watermark_settings and isinstance(current_watermark_settings["position"], tuple):
                    original_position = current_watermark_settings["position"]
                    print(f"[DEBUG] WatermarkDragManager.on_mouse_move: 使用position元组作为原始位置: {original_position}")
                else:
                    # 默认位置（图片中心）
                    original_position = (
                        self.original_pixmap.width() // 2, 
                        self.original_pixmap.height() // 2
                    )
                    print(f"[DEBUG] WatermarkDragManager.on_mouse_move: 使用默认位置（图片中心）作为原始位置: {original_position}")
                
                # 更新水印偏移量为原始位置
                self.watermark_offset = original_position
                print(f"[DEBUG] WatermarkDragManager.on_mouse_move: 初始化watermark_offset为水印原始位置: {original_position}")
            
            # 计算鼠标移动距离
            delta_x = event.pos().x() - self.drag_start_pos.x()
            delta_y = event.pos().y() - self.drag_start_pos.y()
            
            # 获取原始图片尺寸
            original_width = self.original_pixmap.width()
            original_height = self.original_pixmap.height()
            
            # 获取当前预览图片的实际尺寸（考虑缩放比例）
            if self.preview_widget.pixmap():
                preview_pixmap = self.preview_widget.pixmap()
                display_width = preview_pixmap.width()
                display_height = preview_pixmap.height()
                
                # 计算预览图相对于原始图片的缩放比例
                preview_scale_x = original_width / display_width if display_width > 0 else 1.0
                preview_scale_y = original_height / display_height if display_height > 0 else 1.0
                
                # 将鼠标移动距离转换为原始图片上的移动距离
                original_delta_x = delta_x * preview_scale_x
                original_delta_y = delta_y * preview_scale_y
                
                # 计算新的水印位置
                new_x = int(round(self.watermark_offset[0] + original_delta_x))
                new_y = int(round(self.watermark_offset[1] + original_delta_y))
            else:
                # 如果无法获取预览图片尺寸，直接使用鼠标移动距离
                new_x = int(round(self.watermark_offset[0] + delta_x))
                new_y = int(round(self.watermark_offset[1] + delta_y))
            
            # 获取水印尺寸，用于计算允许的边界范围
            watermark_width, watermark_height = self._calculate_watermark_size()
            
            # 允许水印超出边界一个水印的长度/宽度
            # min_x = -watermark_width
            # min_y = -watermark_height
            # max_x = original_width + watermark_width
            # max_y = original_height + watermark_height
            
            # # 确保水印不会超出允许的边界范围
            # new_x = max(min_x, min(new_x, max_x))
            # new_y = max(min_y, min(new_y, max_y))
            
            # 计算应用压缩比例后的watermark_x和watermark_y
            watermark_x = int(round(new_x * compression_scale))
            watermark_y = int(round(new_y * compression_scale))
            print(f"[DEBUG] WatermarkDragManager.on_mouse_move: 计算watermark_x和watermark_y: ({watermark_x}, {watermark_y}) = ({new_x}, {new_y}) * {compression_scale}")
            
            # 更新水印设置中的watermark_x和watermark_y
            if current_watermark_settings:
                current_watermark_settings["watermark_x"] = watermark_x
                current_watermark_settings["watermark_y"] = watermark_y
                print(f"[DEBUG] WatermarkDragManager.on_mouse_move: 更新watermark_x={watermark_x}, watermark_y={watermark_y}")
            
            # 调用位置变化回调
            if self.position_changed_callback:
                print(f"[DEBUG] WatermarkDragManager.on_mouse_move: 调用位置变化回调，新位置=({new_x}, {new_y})")
                print(f"[DEBUG] WatermarkDragManager.on_mouse_move: 调用函数: self.position_changed_callback")
                self.position_changed_callback(new_x, new_y)
            
            # 更新拖拽起始位置和水印偏移量
            self.drag_start_pos = event.pos()
            self.watermark_offset = (new_x, new_y)
        elif not self.is_dragging and self.original_pixmap and self.preview_widget:
            # 检查鼠标是否在预览区域内
            preview_rect = self.preview_widget.rect()
            if preview_rect.contains(event.pos()):
                self.preview_widget.setCursor(Qt.OpenHandCursor)
            else:
                self.preview_widget.unsetCursor()
        else:
            # 恢复默认光标
            self.preview_widget.unsetCursor()
    
    def on_mouse_release(self, event):
        """处理鼠标释放事件"""
        if event.button() == Qt.LeftButton and self.is_dragging:
            self.is_dragging = False
            self.drag_start_pos = None
            
            # 调用拖拽结束回调
            if self.drag_stopped_callback:
                self.drag_stopped_callback()
            
            # 恢复默认光标
            self.preview_widget.unsetCursor()
    
    def _calculate_watermark_size(self):
        """计算水印尺寸"""
        watermark_width = 0
        watermark_height = 0
        
        # 检查是否为图片水印并获取水印尺寸
        if self.watermark_type == "image" and self.image_watermark_widget:
            watermark_settings = self.image_watermark_widget.get_watermark_settings()
            if (hasattr(self.image_watermark_widget, 'original_watermark_size') and 
                self.image_watermark_widget.original_watermark_size != (0, 0)):
                scale = watermark_settings.get("scale", 100) / 100.0
                watermark_width = int(self.image_watermark_widget.original_watermark_size[0] * scale)
                watermark_height = int(self.image_watermark_widget.original_watermark_size[1] * scale)
        
        # 检查是否为文本水印并估算文本尺寸
        elif self.watermark_type == "text" and self.text_watermark_widget:
            text_watermark_settings = self.text_watermark_widget.get_watermark_settings()
            text = text_watermark_settings.get("text", "")
            font_size = text_watermark_settings.get("font_size", 24)
            font_bold = text_watermark_settings.get("font_bold", False)
            font_italic = text_watermark_settings.get("font_italic", False)
            rotation = text_watermark_settings.get("rotation", 0)
            
            # 估算文本宽度和高度
            char_count = len(text)
            if self._contains_chinese(text):
                # 中文文本使用更保守的估算
                text_width = char_count * font_size * 1.5
            else:
                # 英文文本使用更紧凑的估算
                text_width = char_count * font_size
            
            text_height = font_size * 2  # 增加行间距的估算
            
            # 考虑粗体和斜体对尺寸的影响
            if font_bold:
                text_width *= 1.05
                text_height *= 1.05
            
            if font_italic:
                text_width *= 1.05
            
            # 考虑旋转对边界的影响
            if rotation != 0:
                angle_rad = math.radians(abs(rotation))
                rotated_width = abs(text_width * math.cos(angle_rad)) + abs(text_height * math.sin(angle_rad))
                rotated_height = abs(text_width * math.sin(angle_rad)) + abs(text_height * math.cos(angle_rad))
                text_width, text_height = rotated_width, rotated_height
            
            watermark_width = int(text_width)
            watermark_height = int(text_height)
        
        return watermark_width, watermark_height
    
    def _contains_chinese(self, text):
        """检查文本是否包含中文字符"""
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False
    
    def _get_current_watermark_settings(self):
        """
        获取当前水印设置
        """
        # 如果设置了回调函数，使用回调函数获取水印设置
        if self.get_watermark_settings_callback:
            try:
                return self.get_watermark_settings_callback()
            except Exception as e:
                print(f"[ERROR] 获取水印设置失败: {e}")
                return {}
        
        # 否则返回空字典
        return {}
    
    def reset(self):
        """重置拖拽状态"""
        self.is_dragging = False
        self.drag_start_pos = None
        self.watermark_offset = None
        
        # 恢复默认光标
        if self.preview_widget:
            self.preview_widget.unsetCursor()