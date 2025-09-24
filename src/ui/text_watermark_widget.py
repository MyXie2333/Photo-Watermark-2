#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本水印设置组件
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QPushButton, QSlider, 
                             QSpinBox, QGroupBox, QGridLayout, QCheckBox, QColorDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QFontDatabase


class TextWatermarkWidget(QWidget):
    """文本水印设置组件"""
    
    # 信号：水印设置发生变化
    watermark_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # 默认水印设置
        self.watermark_text = "Watermark"
        self.font_family = "Arial"
        self.font_size = 24
        self.font_color = QColor(255, 255, 255)  # 白色
        self.opacity = 80  # 透明度百分比
        self.position = "center"  # 位置
        self.rotation = 0  # 旋转角度
        self.enable_shadow = False
        self.enable_outline = False
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        
        # 文本设置组
        text_group = QGroupBox("文本设置")
        text_layout = QGridLayout(text_group)
        
        # 水印文本
        text_layout.addWidget(QLabel("水印文本:"), 0, 0)
        self.text_input = QLineEdit(self.watermark_text)
        self.text_input.setPlaceholderText("请输入水印文本")
        text_layout.addWidget(self.text_input, 0, 1)
        
        # 字体设置
        text_layout.addWidget(QLabel("字体:"), 1, 0)
        self.font_combo = QComboBox()
        self.font_combo.setEditable(True)
        self.load_fonts()
        text_layout.addWidget(self.font_combo, 1, 1)
        
        # 字体大小
        text_layout.addWidget(QLabel("字体大小:"), 2, 0)
        font_size_layout = QHBoxLayout()
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 200)
        self.font_size_spin.setValue(self.font_size)
        font_size_layout.addWidget(self.font_size_spin)
        font_size_layout.addWidget(QLabel("px"))
        font_size_layout.addStretch()
        text_layout.addLayout(font_size_layout, 2, 1)
        
        layout.addWidget(text_group)
        
        # 样式设置组
        style_group = QGroupBox("样式设置")
        style_layout = QGridLayout(style_group)
        
        # 颜色选择
        style_layout.addWidget(QLabel("颜色:"), 0, 0)
        self.color_button = QPushButton()
        self.color_button.setFixedSize(60, 30)
        self.update_color_button()
        style_layout.addWidget(self.color_button, 0, 1)
        
        # 透明度
        style_layout.addWidget(QLabel("透明度:"), 1, 0)
        opacity_layout = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(self.opacity)
        opacity_layout.addWidget(self.opacity_slider)
        self.opacity_label = QLabel(f"{self.opacity}%")
        opacity_layout.addWidget(self.opacity_label)
        style_layout.addLayout(opacity_layout, 1, 1)
        
        # 旋转角度
        style_layout.addWidget(QLabel("旋转角度:"), 2, 0)
        rotation_layout = QHBoxLayout()
        self.rotation_spin = QSpinBox()
        self.rotation_spin.setRange(-180, 180)
        self.rotation_spin.setValue(self.rotation)
        rotation_layout.addWidget(self.rotation_spin)
        rotation_layout.addWidget(QLabel("°"))
        rotation_layout.addStretch()
        style_layout.addLayout(rotation_layout, 2, 1)
        
        layout.addWidget(style_group)
        
        # 位置设置组
        position_group = QGroupBox("位置设置")
        position_layout = QGridLayout(position_group)
        
        # 九宫格定位
        positions = [
            ("左上", "top-left"), ("上中", "top-center"), ("右上", "top-right"),
            ("左中", "middle-left"), ("中心", "center"), ("右中", "middle-right"),
            ("左下", "bottom-left"), ("下中", "bottom-center"), ("右下", "bottom-right")
        ]
        
        for i, (label, pos) in enumerate(positions):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("position", pos)
            if pos == self.position:
                btn.setChecked(True)
            
            row = i // 3
            col = i % 3
            position_layout.addWidget(btn, row, col)
            
            # 存储按钮引用
            setattr(self, f"pos_{pos.replace('-', '_')}_btn", btn)
        
        layout.addWidget(position_group)
        
        # 效果设置组
        effect_group = QGroupBox("效果设置")
        effect_layout = QHBoxLayout(effect_group)
        
        self.shadow_checkbox = QCheckBox("阴影效果")
        self.shadow_checkbox.setChecked(self.enable_shadow)
        effect_layout.addWidget(self.shadow_checkbox)
        
        self.outline_checkbox = QCheckBox("描边效果")
        self.outline_checkbox.setChecked(self.enable_outline)
        effect_layout.addWidget(self.outline_checkbox)
        
        effect_layout.addStretch()
        layout.addWidget(effect_group)
        
        # 预览和应用按钮
        button_layout = QHBoxLayout()
        
        self.preview_button = QPushButton("预览效果")
        self.apply_button = QPushButton("应用水印")
        
        button_layout.addWidget(self.preview_button)
        button_layout.addWidget(self.apply_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
    def load_fonts(self):
        """加载系统字体"""
        font_db = QFontDatabase()
        fonts = font_db.families()
        
        # 添加常用字体
        common_fonts = ["Arial", "Times New Roman", "Microsoft YaHei", "SimHei", 
                       "SimSun", "KaiTi", "FangSong", "Courier New", "Verdana"]
        
        for font in common_fonts:
            if font in fonts:
                self.font_combo.addItem(font)
        
        # 设置默认字体
        self.font_combo.setCurrentText(self.font_family)
        
    def setup_connections(self):
        """设置信号连接"""
        # 文本设置
        self.text_input.textChanged.connect(self.on_text_changed)
        self.font_combo.currentTextChanged.connect(self.on_font_changed)
        self.font_size_spin.valueChanged.connect(self.on_font_size_changed)
        
        # 样式设置
        self.color_button.clicked.connect(self.on_color_clicked)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        self.rotation_spin.valueChanged.connect(self.on_rotation_changed)
        
        # 位置设置
        for attr_name in dir(self):
            if attr_name.startswith("pos_") and attr_name.endswith("_btn"):
                btn = getattr(self, attr_name)
                btn.clicked.connect(self.on_position_changed)
        
        # 效果设置
        self.shadow_checkbox.stateChanged.connect(self.on_shadow_changed)
        self.outline_checkbox.stateChanged.connect(self.on_outline_changed)
        
        # 按钮
        self.preview_button.clicked.connect(self.on_preview_clicked)
        self.apply_button.clicked.connect(self.on_apply_clicked)
        
    def on_text_changed(self, text):
        """文本内容变化"""
        self.watermark_text = text
        self.watermark_changed.emit()
        
    def on_font_changed(self, font):
        """字体变化"""
        self.font_family = font
        self.watermark_changed.emit()
        
    def on_font_size_changed(self, size):
        """字体大小变化"""
        self.font_size = size
        self.watermark_changed.emit()
        
    def on_color_clicked(self):
        """颜色按钮点击"""
        # 打开颜色选择对话框
        color = QColorDialog.getColor(self.font_color, self, "选择水印颜色")
        
        if color.isValid():
            self.font_color = color
            self.update_color_button()
            self.watermark_changed.emit()
        
    def update_color_button(self):
        """更新颜色按钮样式"""
        color_style = f"background-color: rgba({self.font_color.red()}, {self.font_color.green()}, {self.font_color.blue()}, {self.opacity * 255 // 100});"
        self.color_button.setStyleSheet(color_style)
        
    def on_opacity_changed(self, value):
        """透明度变化"""
        self.opacity = value
        self.opacity_label.setText(f"{value}%")
        self.update_color_button()
        self.watermark_changed.emit()
        
    def on_rotation_changed(self, value):
        """旋转角度变化"""
        self.rotation = value
        self.watermark_changed.emit()
        
    def on_position_changed(self):
        """位置变化"""
        sender = self.sender()
        if sender.isChecked():
            # 取消其他按钮的选中状态
            for attr_name in dir(self):
                if attr_name.startswith("pos_") and attr_name.endswith("_btn"):
                    btn = getattr(self, attr_name)
                    if btn != sender:
                        btn.setChecked(False)
            
            self.position = sender.property("position")
            self.watermark_changed.emit()
        
    def on_shadow_changed(self, state):
        """阴影效果变化"""
        self.enable_shadow = (state == Qt.Checked)
        self.watermark_changed.emit()
        
    def on_outline_changed(self, state):
        """描边效果变化"""
        self.enable_outline = (state == Qt.Checked)
        self.watermark_changed.emit()
        
    def on_preview_clicked(self):
        """预览按钮点击"""
        self.watermark_changed.emit()
        
    def on_apply_clicked(self):
        """应用按钮点击"""
        self.watermark_changed.emit()
        
    def get_watermark_settings(self):
        """获取水印设置"""
        return {
            "text": self.watermark_text,
            "font_family": self.font_family,
            "font_size": self.font_size,
            "color": self.font_color,
            "opacity": self.opacity,
            "position": self.position,
            "rotation": self.rotation,
            "enable_shadow": self.enable_shadow,
            "enable_outline": self.enable_outline
        }