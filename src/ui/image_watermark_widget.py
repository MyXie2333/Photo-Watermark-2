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
            "position": (0.5, 0.5),  # 使用二元组表示中心位置
            "watermark_x": 0,
            "watermark_y": 0,
            "keep_aspect_ratio": True,
            "rotation": 0  # 旋转角度
        }
        
        self.setup_ui()
        
        # 初始化坐标输入框的值
        self.update_coordinate_inputs()
    
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
        
        # 旋转角度设置
        settings_layout.addWidget(QLabel("旋转角度:"), 2, 0)
        rotation_layout = QHBoxLayout()
        self.rotation_slider = QSlider(Qt.Horizontal)
        self.rotation_slider.setRange(-180, 180)
        self.rotation_slider.setValue(0)
        self.rotation_slider.valueChanged.connect(self.on_rotation_changed)
        rotation_layout.addWidget(self.rotation_slider)
        self.rotation_spinbox = QSpinBox()
        self.rotation_spinbox.setRange(-180, 180)
        self.rotation_spinbox.setValue(0)
        self.rotation_spinbox.valueChanged.connect(self.on_rotation_spinbox_changed)
        rotation_layout.addWidget(self.rotation_spinbox)
        rotation_layout.addWidget(QLabel("°"))
        rotation_layout.addStretch()
        settings_layout.addLayout(rotation_layout, 2, 1)
        
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
        
        # 手动坐标输入
        coord_group = QGroupBox("手动坐标输入")
        coord_layout = QGridLayout(coord_group)
        
        # X坐标输入
        coord_layout.addWidget(QLabel("X坐标:"), 0, 0)
        self.x_coord_input = QSpinBox()
        self.x_coord_input.setRange(0, 9999)
        self.x_coord_input.setValue(0)
        coord_layout.addWidget(self.x_coord_input, 0, 1)
        
        # Y坐标输入
        coord_layout.addWidget(QLabel("Y坐标:"), 1, 0)
        self.y_coord_input = QSpinBox()
        self.y_coord_input.setRange(0, 9999)
        self.y_coord_input.setValue(0)
        coord_layout.addWidget(self.y_coord_input, 1, 1)
        
        # 应用按钮
        self.apply_coord_button = QPushButton("应用坐标")
        self.apply_coord_button.clicked.connect(self.on_apply_coord_clicked)
        coord_layout.addWidget(self.apply_coord_button, 2, 0, 1, 2)
        
        layout.addWidget(coord_group)
        
        # 保持纵横比
        aspect_ratio_layout = QHBoxLayout()
        self.aspect_ratio_checkbox = QPushButton("保持纵横比")
        self.aspect_ratio_checkbox.setCheckable(True)
        self.aspect_ratio_checkbox.setChecked(True)
        self.aspect_ratio_checkbox.clicked.connect(self.on_aspect_ratio_changed)
        aspect_ratio_layout.addWidget(self.aspect_ratio_checkbox)
        aspect_ratio_layout.addStretch()
        settings_layout.addLayout(aspect_ratio_layout, 4, 0, 1, 2)
        
        layout.addWidget(settings_group)
        
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
                        # 使用新的update_position方法处理位置变化
                        print(f"[DEBUG] ImageWatermarkWidget.select_watermark_image: 调用函数: self.update_position((0.5, 0.5))")
                        self.update_position((0.5, 0.5))
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
    
    def on_rotation_changed(self, value):
        """旋转角度滑块变化时的处理"""
        self.rotation_spinbox.blockSignals(True)
        self.rotation_spinbox.setValue(value)
        self.rotation_spinbox.blockSignals(False)
        self.watermark_settings["rotation"] = value
        self.update_watermark_settings()
    
    def on_rotation_spinbox_changed(self, value):
        """旋转角度输入框变化时的处理"""
        self.rotation_slider.blockSignals(True)
        self.rotation_slider.setValue(value)
        self.rotation_slider.blockSignals(False)
        self.watermark_settings["rotation"] = value
        self.update_watermark_settings()
    
    def on_position_changed(self):
        """位置按钮点击时的处理"""
        # 获取触发信号的按钮
        sender = self.sender()
        
        if sender:
            pos_value = sender.property("position")
            print(f"[DEBUG] ImageWatermarkWidget.on_position_changed: 修改position为 {pos_value}")
            
            # 手动设置按钮为选中状态
            sender.setChecked(True)
            # 直接使用元组位置，不再转换为字符串
            print(f"[DEBUG] ImageWatermarkWidget.on_position_changed: 调用函数: self.update_position({pos_value})")
            self.update_position(pos_value)
            # 取消其他按钮的选中状态
            for other_btn in self.position_buttons:
                if other_btn != sender:
                    other_btn.setChecked(False)
    
    def on_apply_coord_clicked(self):
        """手动坐标输入应用按钮点击时的处理"""
        # 获取输入的坐标值
        x = self.x_coord_input.value()
        y = self.y_coord_input.value()
        
        print(f"[DEBUG] ImageWatermarkWidget.on_apply_coord_clicked: 应用手动坐标 ({x}, {y})")
        
        # 更新position为绝对坐标
        self.watermark_settings["position"] = (x, y)
        
        # 计算并设置watermark_x和watermark_y（压缩图坐标）
        if hasattr(self, 'compression_scale') and self.compression_scale is not None:
            print(f"[DEBUG] ImageWatermarkWidget.on_apply_coord_clicked: 应用压缩比例 {self.compression_scale:.4f} 到水印坐标: ({x}, {y})")
            self.watermark_settings["watermark_x"] = int(x * self.compression_scale)
            self.watermark_settings["watermark_y"] = int(y * self.compression_scale)
        else:
            self.watermark_settings["watermark_x"] = x
            self.watermark_settings["watermark_y"] = y
        
        print(f"[DEBUG] ImageWatermarkWidget.on_apply_coord_clicked: 更新position和坐标: position={self.watermark_settings['position']}, watermark_x={self.watermark_settings['watermark_x']}, watermark_y={self.watermark_settings['watermark_y']}")
        
        # 取消所有位置按钮的选中状态
        for btn in self.position_buttons:
            btn.setChecked(False)
        
        # 更新UI状态
        self.update_position((x, y))
        
        # 触发水印变化信号，更新预览
        self.watermark_changed.emit()
        
        # 调用render方法立即更新水印渲染
        if hasattr(self, 'parent') and self.parent():
            main_window = self.parent()
            if hasattr(main_window, 'update_preview_with_watermark'):
                print(f"[DEBUG] ImageWatermarkWidget.on_apply_coord_clicked: 调用render方法更新水印渲染")
                main_window.update_preview_with_watermark()
        
        # 更新水印设置中的watermark_x和watermark_y
        if hasattr(self, 'parent') and self.parent() and hasattr(self.parent(), 'image_manager'):
            current_image_path = self.parent().image_manager.get_current_image_path()
            if current_image_path:
                current_watermark_settings = self.parent().image_manager.get_watermark_settings(current_image_path)
                if current_watermark_settings is not None:
                    current_watermark_settings["position"] = self.watermark_settings["position"]
                    current_watermark_settings["watermark_x"] = self.watermark_settings["watermark_x"]
                    current_watermark_settings["watermark_y"] = self.watermark_settings["watermark_y"]
                    self.parent().image_manager.set_watermark_settings(current_image_path, current_watermark_settings)
                    print(f"[DEBUG] ImageWatermarkWidget.on_apply_coord_clicked: 更新current_watermark_settings中的坐标: position={current_watermark_settings['position']}, watermark_x={current_watermark_settings['watermark_x']}, watermark_y={current_watermark_settings['watermark_y']}")
                else:
                    print("[DEBUG] ImageWatermarkWidget.on_apply_coord_clicked: current_watermark_settings为None，无法更新坐标")
            else:
                print("[DEBUG] ImageWatermarkWidget.on_apply_coord_clicked: 没有当前图片路径，无法更新坐标")
        else:
            print("[DEBUG] ImageWatermarkWidget.on_apply_coord_clicked: 无法访问image_manager，无法更新坐标")
    
    def update_position(self, new_position):
        """
        统一更新position的函数，确保每次position变化时都更新watermark_x和watermark_y
        使用与TextWatermarkWidget相同的逻辑来处理坐标
        
        Args:
            new_position: 新的位置，可以是元组(x, y)或相对位置字符串
            
        注意：position是水印在原图上的坐标，watermark_x是水印在压缩图上的坐标
        关系：watermark_x = x * self.compression_scale（取整）
        """
        print(f"[DEBUG] ImageWatermarkWidget.update_position: 修改position为 {new_position}")
        
        # 如果新位置是元组格式，检查是否是相对位置（0-1之间的值）
        if isinstance(new_position, tuple) and len(new_position) == 2:
            x_ratio, y_ratio = new_position[0], new_position[1]
            
            # 检查是否是相对位置（0-1之间的值）
            if 0 <= x_ratio <= 1 and 0 <= y_ratio <= 1:
                print(f"[BRANCH] ImageWatermarkWidget.update_position: 处理相对位置（0-1之间的值），x_ratio={x_ratio}, y_ratio={y_ratio}")
                
                # 获取图片尺寸
                img_width = self.original_width
                img_height = self.original_height
                
                # 计算图片水印尺寸
                scale = self.watermark_settings["scale"] / 100.0
                watermark_width = int(self.original_watermark_size[0] * scale)
                watermark_height = int(self.original_watermark_size[1] * scale)
                
                # 计算绝对位置，直接转换为整数
                x = int(round(img_width * x_ratio ))
                y = int(round(img_height * y_ratio ))
                print(f"[DEBUG] ImageWatermarkWidget.update_position: 计算绝对位置为 ({x}, {y})")
                
                # 如果有压缩比例，应用压缩比例并确保结果为整数
                if hasattr(self, 'compression_scale') and self.compression_scale is not None:
                    print(f"[DEBUG] ImageWatermarkWidget.update_position: 应用压缩比例 {self.compression_scale:.4f} 到水印坐标: ({x}, {y})")
                
                # 更新position为绝对坐标
                self.watermark_settings["position"] = (x, y)
                # 注意：position是水印在原图上的坐标，watermark_x是水印在压缩图上的坐标
                # 关系：watermark_x = x * self.compression_scale（取整）
                self.watermark_settings["watermark_x"] = int(x * self.compression_scale)
                self.watermark_settings["watermark_y"] = int(y * self.compression_scale)
                print(f"[DEBUG] ImageWatermarkWidget.update_position: 更新position和坐标: position={self.watermark_settings['position']}, watermark_x={self.watermark_settings['watermark_x']}, watermark_y={self.watermark_settings['watermark_y']}")
            else:
                # 处理绝对坐标
                print(f"[BRANCH] ImageWatermarkWidget.update_position: 处理绝对坐标，x_ratio={x_ratio}, y_ratio={y_ratio}")
                # 这些坐标已经是绝对坐标，直接使用
                x = int(round(new_position[0]))
                y = int(round(new_position[1]))
                
                # 如果有压缩比例，应用压缩比例并确保结果为整数
                if hasattr(self, 'compression_scale') and self.compression_scale is not None:
                    print(f"[DEBUG] ImageWatermarkWidget.update_position: 应用压缩比例 {self.compression_scale:.4f} 到水印坐标: ({x}, {y})")
                
                # 更新position和坐标
                # 注意：position是水印在原图上的坐标，watermark_x是水印在压缩图上的坐标
                # 关系：watermark_x = x * self.compression_scale（取整）
                self.watermark_settings["position"] = (x, y)
                self.watermark_settings["watermark_x"] = int(x * self.compression_scale)
                self.watermark_settings["watermark_y"] = int(y * self.compression_scale)
                print(f"[DEBUG] ImageWatermarkWidget.update_position: 更新position和坐标: position={self.watermark_settings['position']}, watermark_x={self.watermark_settings['watermark_x']}, watermark_y={self.watermark_settings['watermark_y']}")
        else:
            # 处理预定义的位置字符串
            print(f"[BRANCH] ImageWatermarkWidget.update_position: 处理预定义的位置字符串，position='{new_position}'")
            # 更新position
            self.watermark_settings["position"] = new_position
        
        # 如果有父窗口（主窗口），则更新主窗口中的current_watermark_settings
        if hasattr(self, 'parent') and self.parent():
            main_window = self.parent()
            if hasattr(main_window, 'image_manager'):
                current_image_path = main_window.image_manager.get_current_image_path()
                if current_image_path:
                    current_watermark_settings = main_window.image_manager.get_watermark_settings(current_image_path)
                    if current_watermark_settings:
                        current_watermark_settings["position"] = self.watermark_settings["position"]
                        current_watermark_settings["watermark_x"] = self.watermark_settings["watermark_x"]
                        current_watermark_settings["watermark_y"] = self.watermark_settings["watermark_y"]
                        main_window.image_manager.set_watermark_settings(current_image_path, current_watermark_settings)
        
        # 触发水印变化信号，这将更新预览和坐标显示
        print(f"[DEBUG] ImageWatermarkWidget.update_position: 调用函数: self.watermark_changed.emit")
        self.watermark_changed.emit()
        
        # 更新坐标输入框的值
        self.update_coordinate_inputs()

    def calculate_watermark_coordinates(self):
        """
        根据位置预设和图片尺寸计算水印坐标
        现在使用update_position方法来处理坐标计算，保持与TextWatermarkWidget的一致性
        """
        if self.original_width <= 0 or self.original_height <= 0:
            print("[DEBUG] 图片尺寸未设置，无法计算水印坐标")
            return
        
        if not self.watermark_path:
            print("[DEBUG] 水印图片未选择，无法计算水印坐标")
            return
        
        # 获取当前位置
        position = self.watermark_settings["position"]
        
        # 如果是字符串位置，直接调用update_position
        if isinstance(position, str):
            print(f"[DEBUG] ImageWatermarkWidget.calculate_watermark_coordinates: 将字符串位置{position}转换为对应的二元组")
            # 将字符串位置转换为对应的二元组
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
            if position in position_map:
                self.update_position(position_map[position])
            else:
                # 默认使用中心位置
                print(f"[DEBUG] ImageWatermarkWidget.calculate_watermark_coordinates: 使用默认中心位置")
                self.update_position((0.5, 0.5))
        else:
            # 如果是元组位置，检查坐标类型
            if isinstance(position, tuple) and len(position) == 2:
                x, y = position
                
                # 检查是否是绝对坐标（大于1的值）
                if x > 1 or y > 1:
                    # 绝对坐标保持不动，直接调用update_position
                    print(f"[DEBUG] ImageWatermarkWidget.calculate_watermark_coordinates: 检测到绝对坐标({x}, {y})，保持不动")
                    self.update_position(position)
                else:
                    # 相对坐标（0-1之间的值），转换为绝对坐标
                    # 获取图片尺寸
                    img_width = self.original_width
                    img_height = self.original_height
                    
                    # 计算图片水印尺寸
                    scale = self.watermark_settings["scale"] / 100.0
                    watermark_width = int(self.original_watermark_size[0] * scale)
                    watermark_height = int(self.original_watermark_size[1] * scale)
                    
                    # 计算绝对位置，直接转换为整数
                    abs_x = int(round(img_width * x - watermark_width / 2))
                    abs_y = int(round(img_height * y - watermark_height / 2))
                    
                    print(f"[DEBUG] ImageWatermarkWidget.calculate_watermark_coordinates: 将相对坐标({x}, {y})转换为绝对坐标({abs_x}, {abs_y})")
                    self.update_position((abs_x, abs_y))
            else:
                # 默认使用中心位置
                print(f"[DEBUG] ImageWatermarkWidget.calculate_watermark_coordinates: 使用默认中心位置")
                self.update_position((int(img_width*0.5), int(img_height*0.5)))
    
    def set_compression_scale(self, scale):
        """设置压缩比例，用于预览
        
        Args:
            scale: 压缩比例，用于将原图坐标转换为预览图坐标
            
        注意：position是水印在原图上的坐标，watermark_x是水印在压缩图上的坐标
        关系：watermark_x = x * self.compression_scale（取整）
        """
        self.compression_scale = scale

    def on_aspect_ratio_changed(self, checked):
        """保持纵横比选项变化时的处理"""
        self.watermark_settings["keep_aspect_ratio"] = checked
        # 重新计算坐标
        self.calculate_watermark_coordinates()
        self.update_watermark_settings()
    
    def on_scale_changed(self, value):
        """缩放滑块变化时的处理"""
        # print(f"[DEBUG] ImageWatermarkWidget.on_scale_changed: 缩放比例设置为{value}%")
        self.scale_spinbox.blockSignals(True)
        self.scale_spinbox.setValue(value)
        self.scale_spinbox.blockSignals(False)
        self.watermark_settings["scale"] = value
        # # 重新计算坐标
        # self.calculate_watermark_coordinates()
        self.update_watermark_settings()
        # 调用WatermarkRenderer.render_image_watermark更新水印渲染
        # if hasattr(self, 'parent') and self.parent():
        #     main_window = self.parent()
        #     if hasattr(main_window, 'watermark_renderer') and hasattr(main_window, 'image_manager'):
        #         current_image_path = main_window.image_manager.get_current_image_path()
        #         if current_image_path:
        #             try:
        #                 from PIL import Image
        #                 original_image = Image.open(current_image_path)
        #                 main_window.watermark_renderer.render_image_watermark(original_image, self.watermark_settings, is_preview=True)
        #             except Exception as e:
        #                 print(f"[DEBUG] ImageWatermarkWidget.on_scale_changed: 调用render_image_watermark失败: {e}")
    
    def on_scale_spinbox_changed(self, value):
        """缩放输入框变化时的处理"""
        self.scale_slider.blockSignals(True)
        self.scale_slider.setValue(value)
        self.scale_slider.blockSignals(False)
        self.watermark_settings["scale"] = value
        # 重新计算坐标
        # self.calculate_watermark_coordinates()
        self.update_watermark_settings()
    
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
        
        if "rotation" in settings:
            self.rotation_slider.blockSignals(True)
            self.rotation_spinbox.blockSignals(True)
            self.rotation_slider.setValue(settings["rotation"])
            self.rotation_spinbox.setValue(settings["rotation"])
            self.rotation_slider.blockSignals(False)
            self.rotation_spinbox.blockSignals(False)
        
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
            
            position_value = settings["position"]
            # 检查position是字符串位置名称还是具体坐标列表
            if isinstance(position_value, str) and position_value in position_map:
                target_pos = position_map[position_value]
                # 找到对应的按钮并选中
                for btn in self.position_buttons:
                    if btn.property("position") == target_pos:
                        btn.setChecked(True)
                        break
            elif isinstance(position_value, list) and len(position_value) == 2:
                # 如果是具体坐标列表，直接使用这些坐标值
                # 先取消所有位置按钮的选中状态
                for btn in self.position_buttons:
                    btn.setChecked(False)
                # 然后设置自定义位置
                self.watermark_x = position_value[0]
                self.watermark_y = position_value[1]
                # 更新坐标输入框
                self.update_coordinate_inputs()
        
        if "keep_aspect_ratio" in settings:
            self.aspect_ratio_checkbox.setChecked(settings["keep_aspect_ratio"])
        
        # 更新坐标输入框
        self.update_coordinate_inputs()
    
    def set_original_dimensions(self, width, height):
        """设置原始图片尺寸，用于位置计算"""
        self.original_width = width
        self.original_height = height
    
    def update_coordinate_inputs(self):
        """更新坐标输入框的值，使其与当前水印位置同步"""
        position = self.watermark_settings.get("position", (0, 0))
        
        # 检查position是否为绝对坐标元组
        if isinstance(position, tuple) and len(position) == 2:
            x, y = position
            
            # 检查是否是绝对坐标（大于1的值）
            if x > 1 or y > 1:
                # 更新坐标输入框的值
                self.x_coord_input.blockSignals(True)
                self.y_coord_input.blockSignals(True)
                self.x_coord_input.setValue(int(x))
                self.y_coord_input.setValue(int(y))
                self.x_coord_input.blockSignals(False)
                self.y_coord_input.blockSignals(False)
                print(f"[DEBUG] ImageWatermarkWidget.update_coordinate_inputs: 更新坐标输入框为 ({int(x)}, {int(y)})")

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = ImageWatermarkWidget()
    window.show()
    sys.exit(app.exec_())