#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片水印设置组件
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QFileDialog, QSlider, QSpinBox,
                            QGroupBox, QGridLayout, QDoubleSpinBox, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
import os
from PIL import Image as PILImage
import io

class ImageWatermarkWidget(QWidget):
    """图片水印设置组件"""
    watermark_changed = pyqtSignal()  # 水印设置变更信号
    set_default_watermark = pyqtSignal()  # 设置默认水印信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.watermark_path = ""
        self.original_watermark_size = (0, 0)  # 原始水印尺寸
        self.compression_scale = 1.0  # 压缩比例，用于预览
        self.original_width = 0
        self.original_height = 0
        
        # 初始化水印设置
        self.watermark_settings = {
            "type": "image",
            "image_path": "",
            "scale": 50,  # 缩放百分比
            "opacity": 80,  # 透明度百分比
            "position": "center",
            "watermark_x": 0,
            "watermark_y": 0,
            "keep_aspect_ratio": True
        }
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI组件"""
        layout = QVBoxLayout(self)
        
        # 选择图片按钮
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("水印图片:"))
        self.select_button = QPushButton("选择图片")
        self.select_button.clicked.connect(self.select_watermark_image)
        select_layout.addWidget(self.select_button)
        self.image_path_label = QLabel("未选择图片")
        self.image_path_label.setStyleSheet("color: #666; font-size: 12px;")
        self.image_path_label.setWordWrap(True)
        select_layout.addWidget(self.image_path_label, 1)
        layout.addLayout(select_layout)
        
        # 预览水印图片
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(100)
        self.preview_label.setStyleSheet("border: 1px solid #ddd; background-color: #f9f9f9;")
        self.preview_label.setText("水印预览")
        layout.addWidget(self.preview_label)
        
        # 水印设置组
        settings_group = QGroupBox("水印设置")
        settings_layout = QGridLayout(settings_group)
        
        # 缩放设置
        settings_layout.addWidget(QLabel("缩放比例:"), 0, 0)
        scale_layout = QHBoxLayout()
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setRange(10, 200)
        self.scale_slider.setValue(50)
        self.scale_slider.valueChanged.connect(self.on_scale_changed)
        scale_layout.addWidget(self.scale_slider)
        self.scale_spinbox = QSpinBox()
        self.scale_spinbox.setRange(10, 200)
        self.scale_spinbox.setSuffix("%")
        self.scale_spinbox.setValue(50)
        self.scale_spinbox.valueChanged.connect(self.on_scale_spinbox_changed)
        scale_layout.addWidget(self.scale_spinbox)
        settings_layout.addLayout(scale_layout, 0, 1)
        
        # 透明度设置
        settings_layout.addWidget(QLabel("透明度:"), 1, 0)
        opacity_layout = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(80)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        opacity_layout.addWidget(self.opacity_slider)
        self.opacity_spinbox = QSpinBox()
        self.opacity_spinbox.setRange(10, 100)
        self.opacity_spinbox.setSuffix("%")
        self.opacity_spinbox.setValue(80)
        self.opacity_spinbox.valueChanged.connect(self.on_opacity_spinbox_changed)
        opacity_layout.addWidget(self.opacity_spinbox)
        settings_layout.addLayout(opacity_layout, 1, 1)
        
        # 九宫格位置设置
        position_group = QGroupBox("位置设置")
        position_layout = QGridLayout(position_group)
        
        # 九宫格位置定义 - 使用元组形式表示相对位置
        positions = [
            ("左上", (0.1, 0.1)),     # 左上角
            ("上中", (0.5, 0.1)),     # 上中
            ("右上", (0.9, 0.1)),     # 右上角
            ("左中", (0.1, 0.5)),     # 左中
            ("中心", (0.5, 0.5)),     # 中心
            ("右中", (0.9, 0.5)),     # 右中
            ("左下", (0.1, 0.9)),     # 左下角
            ("下中", (0.5, 0.9)),     # 下中
            ("右下", (0.9, 0.9))      # 右下角
        ]
        
        self.position_buttons = []
        
        for i, (label, pos_value) in enumerate(positions):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("position", pos_value)
            # 默认选择中心位置
            if pos_value == (0.5, 0.5):
                btn.setChecked(True)
                self.watermark_settings["position"] = "center"
            
            # 添加到网格布局
            row = i // 3
            col = i % 3
            position_layout.addWidget(btn, row, col)
            self.position_buttons.append(btn)
            # 按钮点击事件
            btn.clicked.connect(self.on_position_changed)
        
        layout.addWidget(position_group)
        
        # 保持纵横比
        aspect_ratio_layout = QHBoxLayout()
        self.aspect_ratio_checkbox = QPushButton("保持纵横比")
        self.aspect_ratio_checkbox.setCheckable(True)
        self.aspect_ratio_checkbox.setChecked(True)
        self.aspect_ratio_checkbox.clicked.connect(self.on_aspect_ratio_changed)
        aspect_ratio_layout.addWidget(self.aspect_ratio_checkbox)
        aspect_ratio_layout.addStretch()
        settings_layout.addLayout(aspect_ratio_layout, 3, 0, 1, 2)
        
        layout.addWidget(settings_group)
        
        # 操作按钮
        action_layout = QHBoxLayout()
        self.set_default_button = QPushButton("设为默认")
        self.set_default_button.clicked.connect(self.on_set_default)
        action_layout.addWidget(self.set_default_button)
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        layout.addStretch()
    
    def select_watermark_image(self):
        """选择水印图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择水印图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)")
        
        if file_path:
            self.watermark_path = file_path
            self.watermark_settings["image_path"] = file_path
            
            # 更新UI显示
            self.image_path_label.setText(os.path.basename(file_path))
            
            # 加载并显示预览
            try:
                # 加载原图并获取尺寸
                with PILImage.open(file_path) as img:
                    self.original_watermark_size = img.size
                    
                # 创建预览图片（缩放到适合的尺寸）
                preview_size = (150, 100)
                pixmap = QPixmap(file_path)
                scaled_pixmap = pixmap.scaled(
                    preview_size[0], preview_size[1], 
                    Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
                self.preview_label.setText("")
                
                # 更新水印设置
                self.update_watermark_settings()
                
                # 自动设置中心位置
                for btn in self.position_buttons:
                    if btn.property("position") == (0.5, 0.5):
                        btn.setChecked(True)
                        # 直接设置位置并计算坐标，不通过sender()
                        self.watermark_settings["position"] = "center"
                        print(f"[DEBUG] ImageWatermarkWidget.select_watermark_image: 选择水印图片后，修改position为 'center'")
                        print(f"[DEBUG] ImageWatermarkWidget.select_watermark_image: 调用函数: self.calculate_watermark_coordinates")
                        self.calculate_watermark_coordinates()
                        print(f"[DEBUG] ImageWatermarkWidget.select_watermark_image: 调用函数: self.update_watermark_settings")
                        self.update_watermark_settings()
                        # 取消其他按钮的选中状态
                        for other_btn in self.position_buttons:
                            if other_btn != btn:
                                other_btn.setChecked(False)
                        break
            except Exception as e:
                self.preview_label.setText(f"加载失败: {str(e)}")
    

    
    def on_opacity_changed(self, value):
        """透明度滑块变化时的处理"""
        self.opacity_spinbox.blockSignals(True)
        self.opacity_spinbox.setValue(value)
        self.opacity_spinbox.blockSignals(False)
        self.watermark_settings["opacity"] = value
        self.update_watermark_settings()
    
    def on_opacity_spinbox_changed(self, value):
        """透明度输入框变化时的处理"""
        self.opacity_slider.blockSignals(True)
        self.opacity_slider.setValue(value)
        self.opacity_slider.blockSignals(False)
        self.watermark_settings["opacity"] = value
        self.update_watermark_settings()
    
    def on_position_changed(self):
        """位置按钮点击时的处理"""
        # 获取触发信号的按钮
        sender = self.sender()
        
        if sender:
            pos_value = sender.property("position")
            print(f"[DEBUG] ImageWatermarkWidget.on_position_changed: 修改position为 {pos_value}")
            
            # 将元组位置转换为字符串位置
            position_map = {
                (0.1, 0.1): "top-left",
                (0.5, 0.1): "top-center",
                (0.9, 0.1): "top-right",
                (0.1, 0.5): "middle-left",
                (0.5, 0.5): "center",
                (0.9, 0.5): "middle-right",
                (0.1, 0.9): "bottom-left",
                (0.5, 0.9): "bottom-center",
                (0.9, 0.9): "bottom-right"
            }
            
            if pos_value in position_map:
                # 手动设置按钮为选中状态
                sender.setChecked(True)
                self.watermark_settings["position"] = position_map[pos_value]
                # 计算水印坐标
                print(f"[DEBUG] ImageWatermarkWidget.on_position_changed: 调用函数: self.calculate_watermark_coordinates")
                self.calculate_watermark_coordinates()
                print(f"[DEBUG] ImageWatermarkWidget.on_position_changed: 调用函数: self.update_watermark_settings")
                self.update_watermark_settings()
                # 取消其他按钮的选中状态
                for other_btn in self.position_buttons:
                    if other_btn != sender:
                        other_btn.setChecked(False)
    
    def calculate_watermark_coordinates(self):
        """根据位置预设和图片尺寸计算水印坐标"""
        if self.original_width <= 0 or self.original_height <= 0:
            print("[DEBUG] 图片尺寸未设置，无法计算水印坐标")
            return
        
        if not self.watermark_path:
            print("[DEBUG] 水印图片未选择，无法计算水印坐标")
            return
        
        position = self.watermark_settings["position"]
        scale = self.watermark_settings["scale"] / 100.0
        
        # 计算水印图片的实际尺寸
        watermark_width = int(self.original_watermark_size[0] * scale)
        watermark_height = int(self.original_watermark_size[1] * scale)
        
        # 根据位置预设计算坐标
        if position == "top-left":
            x = 0
            y = 0
        elif position == "top-center":
            x = (self.original_width - watermark_width) // 2
            y = 0
        elif position == "top-right":
            x = self.original_width - watermark_width
            y = 0
        elif position == "middle-left":
            x = 0
            y = (self.original_height - watermark_height) // 2
        elif position == "center":
            x = (self.original_width - watermark_width) // 2
            y = (self.original_height - watermark_height) // 2
        elif position == "middle-right":
            x = self.original_width - watermark_width
            y = (self.original_height - watermark_height) // 2
        elif position == "bottom-left":
            x = 0
            y = self.original_height - watermark_height
        elif position == "bottom-center":
            x = (self.original_width - watermark_width) // 2
            y = self.original_height - watermark_height
        elif position == "bottom-right":
            x = self.original_width - watermark_width
            y = self.original_height - watermark_height
        else:
            x = 0
            y = 0
            
        # 更新水印坐标
        self.watermark_settings["watermark_x"] = x
        self.watermark_settings["watermark_y"] = y
        
        # 如果有父窗口（主窗口），则更新主窗口中的current_watermark_settings
        if hasattr(self, 'parent') and self.parent():
            main_window = self.parent()
            if hasattr(main_window, 'image_manager'):
                current_image_path = main_window.image_manager.get_current_image_path()
                if current_image_path:
                    current_watermark_settings = main_window.image_manager.get_watermark_settings(current_image_path)
                    if current_watermark_settings:
                        current_watermark_settings["watermark_x"] = x
                        current_watermark_settings["watermark_y"] = y
                        main_window.image_manager.set_watermark_settings(current_image_path, current_watermark_settings)
        
        print(f"[DEBUG] ImageWatermarkWidget.calculate_watermark_coordinates: 计算图片水印坐标: position={position}, 图片尺寸={self.original_width}x{self.original_height}, 水印尺寸={watermark_width}x{watermark_height}, 坐标=({x}, {y})")
        print(f"[DEBUG] ImageWatermarkWidget.calculate_watermark_coordinates: 修改watermark_x为 {x}, watermark_y为 {y}")
    
    def on_aspect_ratio_changed(self, checked):
        """保持纵横比选项变化时的处理"""
        self.watermark_settings["keep_aspect_ratio"] = checked
        # 重新计算坐标
        self.calculate_watermark_coordinates()
        self.update_watermark_settings()
    
    def on_scale_changed(self, value):
        """缩放滑块变化时的处理"""
        self.scale_spinbox.blockSignals(True)
        self.scale_spinbox.setValue(value)
        self.scale_spinbox.blockSignals(False)
        self.watermark_settings["scale"] = value
        # 重新计算坐标
        self.calculate_watermark_coordinates()
        self.update_watermark_settings()
    
    def on_scale_spinbox_changed(self, value):
        """缩放输入框变化时的处理"""
        self.scale_slider.blockSignals(True)
        self.scale_slider.setValue(value)
        self.scale_slider.blockSignals(False)
        self.watermark_settings["scale"] = value
        # 重新计算坐标
        self.calculate_watermark_coordinates()
        self.update_watermark_settings()
    
    def on_set_default(self):
        """设置为默认水印"""
        self.set_default_watermark.emit()
    
    def update_watermark_settings(self):
        """更新水印设置并发出信号"""
        self.watermark_changed.emit()
    
    def get_watermark_settings(self):
        """获取当前水印设置"""
        return self.watermark_settings.copy()
    
    def set_watermark_settings(self, settings):
        """设置水印参数"""
        if not settings:
            return
        
        # 更新内部设置
        self.watermark_settings.update(settings)
        
        # 更新UI控件
        if "image_path" in settings and settings["image_path"]:
            self.watermark_path = settings["image_path"]
            self.image_path_label.setText(os.path.basename(settings["image_path"]))
            
            # 更新预览
            try:
                # 加载原图并获取尺寸
                with PILImage.open(settings["image_path"]) as img:
                    self.original_watermark_size = img.size
                    
                # 创建预览图片
                preview_size = (150, 100)
                pixmap = QPixmap(settings["image_path"])
                scaled_pixmap = pixmap.scaled(
                    preview_size[0], preview_size[1], 
                    Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
                self.preview_label.setText("")
            except:
                pass
        
        if "scale" in settings:
            self.scale_slider.blockSignals(True)
            self.scale_spinbox.blockSignals(True)
            self.scale_slider.setValue(settings["scale"])
            self.scale_spinbox.setValue(settings["scale"])
            self.scale_slider.blockSignals(False)
            self.scale_spinbox.blockSignals(False)
        
        if "opacity" in settings:
            self.opacity_slider.blockSignals(True)
            self.opacity_spinbox.blockSignals(True)
            self.opacity_slider.setValue(settings["opacity"])
            self.opacity_spinbox.setValue(settings["opacity"])
            self.opacity_slider.blockSignals(False)
            self.opacity_spinbox.blockSignals(False)
        
        if "position" in settings:
            # 将字符串位置转换为元组位置
            position_map = {
                "top-left": (0.1, 0.1),
                "top-center": (0.5, 0.1),
                "top-right": (0.9, 0.1),
                "middle-left": (0.1, 0.5),
                "center": (0.5, 0.5),
                "middle-right": (0.9, 0.5),
                "bottom-left": (0.1, 0.9),
                "bottom-center": (0.5, 0.9),
                "bottom-right": (0.9, 0.9)
            }
            
            if settings["position"] in position_map:
                target_pos = position_map[settings["position"]]
                # 找到对应的按钮并选中
                for btn in self.position_buttons:
                    if btn.property("position") == target_pos:
                        btn.setChecked(True)
                        break
        
        if "keep_aspect_ratio" in settings:
            self.aspect_ratio_checkbox.setChecked(settings["keep_aspect_ratio"])
    
    def set_original_dimensions(self, width, height):
        """设置原始图片尺寸，用于位置计算"""
        self.original_width = width
        self.original_height = height
    
    def set_compression_scale(self, scale):
        """设置压缩比例，用于预览"""
        self.compression_scale = scale

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = ImageWatermarkWidget()
    window.show()
    sys.exit(app.exec_())