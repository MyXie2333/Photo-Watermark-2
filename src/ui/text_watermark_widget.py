#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本水印设置组件
"""

from ast import comprehension
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QPushButton, QSlider, 
                             QSpinBox, QGroupBox, QGridLayout, QCheckBox, QColorDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QFontDatabase
from PIL import Image, ImageDraw, ImageFont, ImageEnhance


class TextWatermarkWidget(QWidget):
    """文本水印设置组件"""
    
    # 信号：水印设置发生变化
    watermark_changed = pyqtSignal()
    set_default_watermark = pyqtSignal()
    # 信号：字体切换提示
    font_switch_notification = pyqtSignal(str)  # 参数为提示信息
    
    def __init__(self):
        super().__init__()
        
        # 默认水印设置
        self.watermark_text = ""  # 空字符串，不显示默认水印文本
        self.font_family = "Microsoft YaHei"  # 使用支持中文的字体
        self.font_size = 64 
        self.font_bold = False  # 粗体
        self.font_italic = False  # 斜体
        self.font_color = QColor(0, 0, 255)  # 白色
        self.opacity = 80  # 透明度百分比
        self.position = (0.5, 0.5)  # 位置
        self.watermark_x = 0  # 水印X坐标
        self.watermark_y = 0  # 水印Y坐标
        self.rotation = 0  # 旋转角度
        self.enable_shadow = False
        self.enable_outline = False
        # 阴影和描边详细设置
        self.outline_color = QColor(0, 0, 0)  # 描边颜色默认为黑色
        self.outline_width = 1  # 描边宽度默认为1
        self.outline_offset = (0, 0)  # 描边偏移默认为(0,0)
        self.shadow_color = QColor(0, 0, 0)  # 阴影颜色默认为黑色
        self.shadow_offset = (3, 3)  # 阴影偏移默认为(3,3)
        self.shadow_blur = 3  # 阴影模糊半径默认为3
        
        # 原图尺寸和压缩比例
        self.original_width = 0
        self.original_height = 0
        self.compression_scale = 1.0  # 默认压缩比例为1.0（无压缩）
        
        self.setup_ui()
        self.setup_connections()
        
        # 初始化坐标输入框的值
        self.update_coordinate_inputs()
        
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        
        # 文本设置组
        text_group = QGroupBox("文本设置")
        text_layout = QGridLayout(text_group)
        
        # 水印文本
        text_layout.addWidget(QLabel("水印文本:"), 0, 0)
        
        # 创建水印文本输入框和清除按钮的布局
        text_input_layout = QHBoxLayout()
        self.text_input = QLineEdit(self.watermark_text)
        self.text_input.setPlaceholderText("请输入水印文本")
        # 设置初始样式：灰色文本
        self.text_input.setStyleSheet("""
            QLineEdit {
                color: #999;
                font-style: italic;
            }
            QLineEdit:focus {
                color: #000;
                font-style: normal;
            }
        """)
        text_input_layout.addWidget(self.text_input)
        
        # 添加清除按钮（小叉）
        self.clear_button = QPushButton("×")
        self.clear_button.setFixedSize(30, 30)
        self.clear_button.setToolTip("清空水印文本")
        self.clear_button.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                color: #666;
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                color: #333;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        text_input_layout.addWidget(self.clear_button)
        
        text_layout.addLayout(text_input_layout, 0, 1)
        
        # 字体设置
        text_layout.addWidget(QLabel("字体:"), 1, 0)
        self.font_combo = QComboBox()
        self.font_combo.setEditable(False)  # 禁用直接输入，只能通过选单选择
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
        
        # 字体样式（粗体、斜体）
        text_layout.addWidget(QLabel("字体样式:"), 3, 0)
        font_style_layout = QHBoxLayout()
        
        self.bold_checkbox = QCheckBox("粗体")
        self.bold_checkbox.setChecked(False)
        font_style_layout.addWidget(self.bold_checkbox)
        
        self.italic_checkbox = QCheckBox("斜体")
        self.italic_checkbox.setChecked(False)
        font_style_layout.addWidget(self.italic_checkbox)
        
        # 添加小号倾斜提示
        hint_label = QLabel("部分字体不支持加粗或斜体")
        hint_label.setStyleSheet("color: #888; font-size: 10px; font-style: italic;")
        hint_label.setFixedWidth(150)
        font_style_layout.addWidget(hint_label)
        
        font_style_layout.addStretch()
        text_layout.addLayout(font_style_layout, 3, 1)
        
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
        self.rotation_slider = QSlider(Qt.Horizontal)
        self.rotation_slider.setRange(-180, 180)
        self.rotation_slider.setValue(self.rotation)
        self.rotation_spin = QSpinBox()
        self.rotation_spin.setRange(-180, 180)
        self.rotation_spin.setValue(self.rotation)
        rotation_layout.addWidget(self.rotation_slider)
        rotation_layout.addWidget(self.rotation_spin)
        rotation_layout.addWidget(QLabel("°"))
        rotation_layout.addStretch()
        style_layout.addLayout(rotation_layout, 2, 1)
        
        layout.addWidget(style_group)
        
        # 位置设置组
        position_group = QGroupBox("位置设置")
        position_layout = QGridLayout(position_group)
        
        # 九宫格定位
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
        
        for i, (label, pos_value) in enumerate(positions):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("position", pos_value)
            if pos_value == self.position:
                btn.setChecked(True)
            
            # 添加到网格布局
            row = i // 3
            col = i % 3
            position_layout.addWidget(btn, row, col)
            # 存储按钮引用，命名格式为 pos_x_y_btn，其中x和y是位置坐标
            setattr(self, f"pos_{pos_value[0]}_{pos_value[1]}_btn", btn)
            # 按钮点击事件
            btn.clicked.connect(self.on_position_changed)
        
        # 添加手动坐标输入
        coord_input_layout = QHBoxLayout()
        coord_input_layout.addWidget(QLabel("手动坐标:"))
        
        # X坐标输入
        coord_input_layout.addWidget(QLabel("X:"))
        self.coord_x_spin = QSpinBox()
        self.coord_x_spin.setRange(0, 9999)
        self.coord_x_spin.setValue(0)
        coord_input_layout.addWidget(self.coord_x_spin)
        
        # Y坐标输入
        coord_input_layout.addWidget(QLabel("Y:"))
        self.coord_y_spin = QSpinBox()
        self.coord_y_spin.setRange(0, 9999)
        self.coord_y_spin.setValue(0)
        coord_input_layout.addWidget(self.coord_y_spin)
        
        # 应用坐标按钮
        self.apply_coord_button = QPushButton("应用坐标")
        self.apply_coord_button.setToolTip("输入坐标后点击应用水印位置")
        coord_input_layout.addWidget(self.apply_coord_button)
        
        coord_input_layout.addStretch()
        
        # 将坐标输入布局添加到位置设置组的第4行（九宫格下方）
        position_layout.addLayout(coord_input_layout, 4, 0, 1, 3)
        
        layout.addWidget(position_group)
        
        # 效果设置组
        effect_group = QGroupBox("效果设置")
        effect_layout = QGridLayout(effect_group)
        
        # 基础效果开关
        effect_switch_layout = QHBoxLayout()
        self.shadow_checkbox = QCheckBox("阴影效果")
        self.shadow_checkbox.setChecked(self.enable_shadow)
        effect_switch_layout.addWidget(self.shadow_checkbox)
        
        self.outline_checkbox = QCheckBox("描边效果")
        self.outline_checkbox.setChecked(self.enable_outline)
        effect_switch_layout.addWidget(self.outline_checkbox)
        effect_switch_layout.addStretch()
        
        effect_layout.addLayout(effect_switch_layout, 0, 0, 1, 2)
        
        # 描边详细设置
        outline_settings_layout = QHBoxLayout()
        outline_settings_layout.addWidget(QLabel("描边颜色:"))
        self.outline_color_button = QPushButton()
        self.outline_color_button.setFixedSize(40, 24)
        self.update_outline_color_button()
        outline_settings_layout.addWidget(self.outline_color_button)
        
        outline_settings_layout.addWidget(QLabel("描边粗细:"))
        self.outline_width_spin = QSpinBox()
        self.outline_width_spin.setRange(1, 10)
        self.outline_width_spin.setValue(self.outline_width)
        outline_settings_layout.addWidget(self.outline_width_spin)
        outline_settings_layout.addWidget(QLabel("px"))
        outline_settings_layout.addStretch()
        
        # 描边偏移设置
        outline_offset_layout = QHBoxLayout()
        outline_offset_layout.addWidget(QLabel("描边偏移:"))
        outline_offset_layout.addWidget(QLabel("X:"))
        self.outline_offset_x_spin = QSpinBox()
        self.outline_offset_x_spin.setRange(-10, 10)
        self.outline_offset_x_spin.setValue(self.outline_offset[0])
        outline_offset_layout.addWidget(self.outline_offset_x_spin)
        outline_offset_layout.addWidget(QLabel("Y:"))
        self.outline_offset_y_spin = QSpinBox()
        self.outline_offset_y_spin.setRange(-10, 10)
        self.outline_offset_y_spin.setValue(self.outline_offset[1])
        outline_offset_layout.addWidget(self.outline_offset_y_spin)
        outline_offset_layout.addStretch()
        
        effect_layout.addLayout(outline_settings_layout, 1, 0, 1, 2)
        effect_layout.addLayout(outline_offset_layout, 2, 0, 1, 2)
        
        # 阴影详细设置
        shadow_color_layout = QHBoxLayout()
        shadow_color_layout.addWidget(QLabel("阴影颜色:"))
        self.shadow_color_button = QPushButton()
        self.shadow_color_button.setFixedSize(40, 24)
        self.update_shadow_color_button()
        shadow_color_layout.addWidget(self.shadow_color_button)
        shadow_color_layout.addStretch()
        
        shadow_offset_layout = QHBoxLayout()
        shadow_offset_layout.addWidget(QLabel("阴影偏移:"))
        shadow_offset_layout.addWidget(QLabel("X:"))
        self.shadow_offset_x_spin = QSpinBox()
        self.shadow_offset_x_spin.setRange(0, 20)
        self.shadow_offset_x_spin.setValue(self.shadow_offset[0])
        shadow_offset_layout.addWidget(self.shadow_offset_x_spin)
        shadow_offset_layout.addWidget(QLabel("Y:"))
        self.shadow_offset_y_spin = QSpinBox()
        self.shadow_offset_y_spin.setRange(0, 20)
        self.shadow_offset_y_spin.setValue(self.shadow_offset[1])
        shadow_offset_layout.addWidget(self.shadow_offset_y_spin)
        shadow_offset_layout.addStretch()
        
        shadow_blur_layout = QHBoxLayout()
        shadow_blur_layout.addWidget(QLabel("阴影模糊:"))
        self.shadow_blur_spin = QSpinBox()
        self.shadow_blur_spin.setRange(0, 10)
        self.shadow_blur_spin.setValue(self.shadow_blur)
        shadow_blur_layout.addWidget(self.shadow_blur_spin)
        shadow_blur_layout.addWidget(QLabel("px"))
        shadow_blur_layout.addStretch()
        
        effect_layout.addLayout(shadow_color_layout, 3, 0, 1, 2)
        effect_layout.addLayout(shadow_offset_layout, 4, 0)
        effect_layout.addLayout(shadow_blur_layout, 4, 1)
        
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
        """加载系统字体 - 只显示在字体文件映射中存在的字体"""
        # 定义支持的字体列表（基于watermark_renderer.py中的字体文件映射）
        supported_chinese_fonts = [
            "Microsoft YaHei",  # 微软雅黑
            "SimHei",           # 黑体
            "KaiTi",            # 楷体
            "FangSong",         # 仿宋
            "Arial Unicode MS"  # 回退字体
        ]
        
        # 创建英文字体名称到中文字体名称的映射
        font_name_mapping = {
            "Microsoft YaHei": "微软雅黑",
            "SimHei": "黑体",
            "KaiTi": "楷体",
            "FangSong": "仿宋",
            "Arial Unicode MS": "Arial Unicode MS"
        }
        
        supported_english_fonts = [
            "Arial", "Times New Roman", "Courier New", "Verdana", 
            "Georgia", "Tahoma", "Trebuchet MS", "Comic Sans MS"
        ]
        
        # 检查字体是否在系统中实际存在
        available_fonts = []
        
        # 检查中文字体
        for font_name in supported_chinese_fonts:
            if self._check_font_exists(font_name):
                available_fonts.append(font_name)
        
        # 检查英文字体
        for font_name in supported_english_fonts:
            if self._check_font_exists(font_name):
                available_fonts.append(font_name)
        
        # 清空下拉菜单
        self.font_combo.clear()
        
        # 添加可用的中文字体
        chinese_fonts = [f for f in available_fonts if f in supported_chinese_fonts]
        for font in chinese_fonts:
            # 同时显示英文名称和中文名称
            display_name = f"{font} - {font_name_mapping.get(font, '')}"
            self.font_combo.addItem(display_name)
            # 存储实际的字体名称，用于后续使用
            self.font_combo.setItemData(self.font_combo.count() - 1, font, Qt.UserRole)
        
        # 添加分隔线（如果已经有中文字体）
        if chinese_fonts:
            self.font_combo.insertSeparator(len(chinese_fonts))
        
        # 添加可用的英文字体
        english_fonts = [f for f in available_fonts if f in supported_english_fonts]
        for font in english_fonts:
            self.font_combo.addItem(font)
        
        # 设置默认字体（优先使用中文字体）
        if chinese_fonts:
            # 优先使用微软雅黑，如果没有则使用第一个中文字体
            if "Microsoft YaHei" in chinese_fonts:
                self.font_combo.setCurrentText("Microsoft YaHei")
                self.font_family = "Microsoft YaHei"
            else:
                self.font_combo.setCurrentText(chinese_fonts[0])
                self.font_family = chinese_fonts[0]
        elif english_fonts:
            # 如果没有中文字体，使用第一个英文字体
            self.font_combo.setCurrentText(english_fonts[0])
            self.font_family = english_fonts[0]
        else:
            # 如果没有可用字体，使用默认字体
            self.font_combo.addItem("Arial")
            self.font_combo.setCurrentText("Arial")
            self.font_family = "Arial"
    
    def _check_font_exists(self, font_name):
        """检查字体是否在系统中实际存在"""
        try:
            # 尝试加载字体来检查是否存在
            from PIL import ImageFont
            font = ImageFont.truetype(font_name, 12, encoding="utf-8")
            return True
        except:
            # 如果直接加载失败，尝试通过字体文件映射检查
            return self._check_font_by_file_mapping(font_name)
    
    def _check_font_by_file_mapping(self, font_name):
        """通过字体文件映射检查字体是否存在"""
        import os
        
        # 字体文件映射（与watermark_renderer.py保持一致）
        # 注意：即使某些字体没有专门的粗体/斜体文件，PIL也会通过特性模拟来实现粗体和斜体效果
        chinese_font_files = {
            "Microsoft YaHei": {
                "regular": ["msyh.ttc", "msyh.ttf"],
                "bold": ["msyhbd.ttc", "msyhbd.ttf"],
                "light": ["msyhl.ttc"]
            },
            "SimHei": {
                "regular": ["simhei.ttf"]
                # 黑体没有专门的粗体文件，但PIL会通过特性模拟实现粗体效果
            },
            "KaiTi": {
                "regular": ["simkai.ttf", "STKAITI.TTF"]
                # 楷体没有专门的粗体文件，但PIL会通过特性模拟实现粗体效果
            },
            "FangSong": {
                "regular": ["simfang.ttf"]
                # 仿宋没有专门的粗体文件，但PIL会通过特性模拟实现粗体效果
            },
            "Arial Unicode MS": {
                "regular": ["arialuni.ttf"]
            }
        }
        
        english_font_files = {
            "Arial": ["arial.ttf", "arialbd.ttf", "arialbi.ttf", "ariali.ttf"],
            "Times New Roman": ["times.ttf", "timesbd.ttf", "timesbi.ttf", "timesi.ttf"],
            "Courier New": ["cour.ttf", "courbd.ttf", "courbi.ttf", "couri.ttf"],
            "Verdana": ["verdana.ttf", "verdanab.ttf", "verdanaz.ttf", "verdanai.ttf"],
            "Georgia": ["georgia.ttf", "georgiab.ttf", "georgiaz.ttf", "georgiai.ttf"],
            "Tahoma": ["tahoma.ttf", "tahomabd.ttf"],
            "Trebuchet MS": ["trebuc.ttf", "trebucbd.ttf", "trebucit.ttf", "trebucbi.ttf"],
            "Comic Sans MS": ["comic.ttf", "comicbd.ttf"]
        }
        
        # 常见字体文件路径
        font_paths = [
            "C:/Windows/Fonts/",
            "/usr/share/fonts/",
            "/Library/Fonts/"
        ]
        
        # 检查中文字体
        if font_name in chinese_font_files:
            # 遍历所有字体变体
            for variant_files in chinese_font_files[font_name].values():
                for font_file in variant_files:
                    for font_path in font_paths:
                        full_path = os.path.join(font_path, font_file)
                        if os.path.exists(full_path):
                            return True
        
        # 检查英文字体
        if font_name in english_font_files:
            for font_file in english_font_files[font_name]:
                for font_path in font_paths:
                    full_path = os.path.join(font_path, font_file)
                    if os.path.exists(full_path):
                        return True
        
        return False
        
    def setup_connections(self):
        """设置信号连接"""
        # 文本设置
        self.text_input.textChanged.connect(self.on_text_changed)
        self.font_combo.currentIndexChanged.connect(self.on_font_changed)
        self.font_size_spin.valueChanged.connect(self.on_font_size_changed)
        self.bold_checkbox.stateChanged.connect(self.on_bold_changed)
        self.italic_checkbox.stateChanged.connect(self.on_italic_changed)
        self.clear_button.clicked.connect(self.on_clear_clicked)
        self.text_input.installEventFilter(self)
        
        # 样式设置
        self.color_button.clicked.connect(self.on_color_clicked)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        self.rotation_slider.valueChanged.connect(self.on_rotation_changed)
        self.rotation_spin.valueChanged.connect(self.on_rotation_changed)
        
        # 位置设置
        # 位置按钮的点击事件已在创建按钮时连接
        # 手动坐标输入应用按钮
        self.apply_coord_button.clicked.connect(self.on_apply_coord_clicked)
        
        # 效果设置
        self.shadow_checkbox.stateChanged.connect(self.on_shadow_changed)
        self.outline_checkbox.stateChanged.connect(self.on_outline_changed)
        self.outline_color_button.clicked.connect(self.on_outline_color_clicked)
        self.outline_width_spin.valueChanged.connect(self.on_outline_width_changed)
        self.outline_offset_x_spin.valueChanged.connect(self.on_outline_offset_changed)
        self.outline_offset_y_spin.valueChanged.connect(self.on_outline_offset_changed)
        self.shadow_color_button.clicked.connect(self.on_shadow_color_clicked)
        self.shadow_offset_x_spin.valueChanged.connect(self.on_shadow_offset_changed)
        self.shadow_offset_y_spin.valueChanged.connect(self.on_shadow_offset_changed)
        self.shadow_blur_spin.valueChanged.connect(self.on_shadow_blur_changed)
        
        # 按钮
        self.preview_button.clicked.connect(self.on_preview_clicked)
        self.apply_button.clicked.connect(self.on_apply_clicked)
        
    def eventFilter(self, obj, event):
        """事件过滤器处理焦点事件"""
        if obj == self.text_input:
            if event.type() == event.FocusIn:
                # 获得焦点时检查当前是否显示的是全局默认水印（灰色样式）
                if self.text_input.styleSheet() and "color: #999" in self.text_input.styleSheet():
                    # 通知主窗口需要为当前图片设置默认水印
                    self.set_default_watermark.emit()
                # 设置正常样式
                self.text_input.setStyleSheet("""
                    QLineEdit {
                        color: #000;
                        font-style: normal;
                    }
                """)
            elif event.type() == event.FocusOut:
                # 失去焦点时，如果文本为空则恢复灰色样式
                if self.text_input.text() == "":
                    self.text_input.setStyleSheet("""
                        QLineEdit {
                            color: #999;
                            font-style: italic;
                        }
                    """)
        return super().eventFilter(obj, event)
        
    def on_clear_clicked(self):
        """清除按钮点击 - 清空水印文本"""
        self.text_input.clear()
        self.watermark_text = ""
        
        # 清空文本后显示灰色占位样式
        self.text_input.setStyleSheet("""
            QLineEdit {
                color: #999;
                font-style: italic;
            }
        """)
        
        self.watermark_changed.emit()
        
    def on_text_changed(self, text):
        """文本内容变化"""
        self.watermark_text = text
        
        # 根据文本内容更新样式
        if self.watermark_text == "":
            # 文本为空时显示灰色占位样式
            self.text_input.setStyleSheet("""
                QLineEdit {
                    color: #999;
                    font-style: italic;
                }
            """)
        else:
            # 文本不为空时显示正常样式
            self.text_input.setStyleSheet("""
                QLineEdit {
                    color: #000;
                    font-style: normal;
                }
            """)
            
            # 检测文本是否包含中文字符，如果需要则自动切换到中文字体
            self._auto_switch_chinese_font(text)
        
        self.watermark_changed.emit()
        
    def on_font_changed(self, index):
        """字体变化"""
        if index >= 0:
            # 获取实际的字体名称
            actual_font_name = self.font_combo.itemData(index, Qt.UserRole)
            if actual_font_name is not None:
                self.font_family = actual_font_name
            else:
                # 对于英文字体，直接使用显示文本
                self.font_family = self.font_combo.itemText(index)
            
            # 检查新选择的字体是否支持中文，并根据需要自动切换
            self._auto_switch_chinese_font(self.watermark_text)
            
        self.watermark_changed.emit()
        
    def on_font_size_changed(self, size):
        """字体大小变化"""
        self.font_size = size
        self.watermark_changed.emit()
        
    def on_bold_changed(self, state):
        """粗体变化"""
        self.font_bold = (state == Qt.Checked)
        self.watermark_changed.emit()
        
    def on_italic_changed(self, state):
        """斜体变化"""
        self.font_italic = (state == Qt.Checked)
        self.watermark_changed.emit()
    
    def _contains_chinese(self, text):
        """检测文本是否包含中文字符"""
        if not text:
            return False
        
        # 中文字符的Unicode范围
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False
    
    def _auto_switch_chinese_font(self, text):
        """根据文本内容自动切换到中文字体"""
        if not text:
            return
            
        # 检测文本是否包含中文字符
        if self._contains_chinese(text):
            # 如果文本包含中文，检查当前字体是否已经是中文字体
            current_index = self.font_combo.currentIndex()
            current_font = self.font_combo.itemData(current_index, Qt.UserRole) if current_index >= 0 else ""
            
            # 获取下拉菜单中所有可用的中文字体
            chinese_fonts = []
            chinese_font_display_names = []
            chinese_keywords = ['yahei', 'simhei', 'kaiti', 'fangsong', 
                               '黑体', '楷体', '仿宋', '微软雅黑', '华文', '方正']
            
            # 从下拉菜单中检测所有中文字体
            for i in range(self.font_combo.count()):
                item_text = self.font_combo.itemText(i)
                if not item_text.startswith("---"):  # 跳过分隔线
                    item_lower = item_text.lower()
                    if any(keyword in item_lower for keyword in chinese_keywords):
                        chinese_font_display_names.append(item_text)
                        # 获取实际的字体名称
                        actual_font = self.font_combo.itemData(i, Qt.UserRole)
                        if actual_font:
                            chinese_fonts.append(actual_font)
            
            # 关键修复：如果当前字体已经是中文字体，不要改变字体
            if current_font in chinese_fonts:
                return  # 保持当前字体不变
            
            # 只有当当前字体不是中文字体时，才自动切换到中文字体
            # 优先尝试微软雅黑
            if "Microsoft YaHei" in chinese_fonts:
                # 查找并选择显示名称
                for i in range(self.font_combo.count()):
                    if self.font_combo.itemData(i, Qt.UserRole) == "Microsoft YaHei":
                        self.font_combo.setCurrentIndex(i)
                        self.font_family = "Microsoft YaHei"
                        # 发出字体切换提示信号
                        self.font_switch_notification.emit("当前字体不支持中文显示，已为您切换至中文字体")
                        break
            elif chinese_fonts:
                # 按优先级选择：微软雅黑 > 黑体 > 楷体 > 仿宋 > 其他
                priority_order = ["SimHei", "KaiTi", "FangSong"]
                found = False
                for font in priority_order:
                    if font in chinese_fonts:
                        # 查找并选择显示名称
                        for i in range(self.font_combo.count()):
                            if self.font_combo.itemData(i, Qt.UserRole) == font:
                                self.font_combo.setCurrentIndex(i)
                                self.font_family = font
                                # 发出字体切换提示信号
                                self.font_switch_notification.emit("当前字体不支持中文显示，已为您切换至中文字体")
                                break
                        break
                    else:
                        # 如果没有优先级字体，使用第一个可用的中文字体
                        self.font_combo.setCurrentText(chinese_fonts[0])
                        self.font_family = chinese_fonts[0]
                        # 发出字体切换提示信号
                        self.font_switch_notification.emit("当前字体不支持中文显示，已为您切换至中文字体")
        
    def on_color_clicked(self):
        """颜色按钮点击"""
        # 确保font_color是QColor对象
        initial_color = self.font_color
        if not isinstance(initial_color, QColor):
            if isinstance(initial_color, (tuple, list)) and len(initial_color) >= 3:
                initial_color = QColor(initial_color[0], initial_color[1], initial_color[2])
            elif isinstance(initial_color, str):
                initial_color = QColor(initial_color)
            else:
                initial_color = QColor(0, 0, 255)  # 默认蓝色
                print(f"[DEBUG CLR] 警告：font_color类型错误 {type(self.font_color)}，使用默认颜色")
        
        # 打开颜色选择对话框
        color = QColorDialog.getColor(initial_color, self, "选择水印颜色")
        
        if color.isValid():
            self.font_color = color
            self.update_color_button()
            self.watermark_changed.emit()
        
    def update_color_button(self):
        """更新颜色按钮样式"""
        # 确保颜色是QColor对象
        def ensure_qcolor(color):
            if isinstance(color, QColor):
                return color
            elif isinstance(color, tuple) and len(color) >= 3:
                return QColor(color[0], color[1], color[2])
            elif isinstance(color, str):
                return QColor(color)
            else:
                return QColor(0, 0, 0)  # 默认黑色
        
        font_color = ensure_qcolor(self.font_color)
        color_style = f"background-color: rgba({font_color.red()}, {font_color.green()}, {font_color.blue()}, {self.opacity * 255 // 100});"
        self.color_button.setStyleSheet(color_style)
    
    def update_outline_color_button(self):
        """更新描边颜色按钮的背景色"""
        # 确保颜色是QColor对象
        def ensure_qcolor(color):
            if isinstance(color, QColor):
                return color
            elif isinstance(color, tuple) and len(color) >= 3:
                return QColor(color[0], color[1], color[2])
            elif isinstance(color, str):
                return QColor(color)
            else:
                return QColor(0, 0, 0)  # 默认黑色
        
        color = ensure_qcolor(self.outline_color)
        self.outline_color_button.setStyleSheet(f"background-color: rgb({color.red()}, {color.green()}, {color.blue()}); border: 1px solid #ccc;")
        
    def update_shadow_color_button(self):
        """更新阴影颜色按钮的背景色"""
        # 确保颜色是QColor对象
        def ensure_qcolor(color):
            if isinstance(color, QColor):
                return color
            elif isinstance(color, tuple) and len(color) >= 3:
                return QColor(color[0], color[1], color[2])
            elif isinstance(color, str):
                return QColor(color)
            else:
                return QColor(0, 0, 0)  # 默认黑色
        
        color = ensure_qcolor(self.shadow_color)
        self.shadow_color_button.setStyleSheet(f"background-color: rgb({color.red()}, {color.green()}, {color.blue()}); border: 1px solid #ccc;")
        
    def on_opacity_changed(self, value):
        """透明度变化"""
        self.opacity = value
        self.opacity_label.setText(f"{value}%")
        self.update_color_button()
        self.watermark_changed.emit()
        
    def on_rotation_changed(self, value):
        """旋转角度变化"""
        self.rotation = value
        
        # 同步滑块和输入框的值
        sender = self.sender()
        if sender == self.rotation_slider:
            # 如果是滑块触发的，更新输入框的值
            self.rotation_spin.setValue(value)
        elif sender == self.rotation_spin:
            # 如果是输入框触发的，更新滑块的值
            self.rotation_slider.setValue(value)
            
        self.watermark_changed.emit()
        
    def on_position_changed(self):
        """
        处理水印位置变化事件
        
        当用户点击九宫格位置按钮时，计算水印在原图上的精确坐标位置。
        优化点：
        1. 支持原图尺寸获取，确保水印位置计算基于原图而非预览图
        2. 使用PIL精确计算文本边界框，考虑字体、大小、粗体、斜体等因素
        3. 考虑文本旋转对边界框的影响，确保旋转后的文本也能正确定位
        4. 优化九宫格定位算法，使水印位于对应格子的合适位置
        5. 添加动态边距计算，边距大小根据图片尺寸自适应调整
        6. 改进错误处理，确保在各种异常情况下仍能提供合理的默认位置
        
        处理流程：
        1. 取消其他位置按钮的选中状态
        2. 获取原图尺寸（优先使用传递的尺寸，否则从图片文件读取）
        3. 使用PIL精确计算文本边界框
        4. 考虑旋转因素调整文本尺寸
        5. 根据九宫格位置计算水印坐标，考虑文本尺寸和边距
        6. 调用update_position更新水印位置
        """
        # 获取发送信号的对象（被点击的位置按钮）
        sender = self.sender()
        if sender.isChecked():
            # 取消其他位置按钮的选中状态，确保只有一个按钮被选中
            for attr_name in dir(self):
                # 查找所有位置按钮（以pos_开头，以_btn结尾的属性）
                if attr_name.startswith("pos_") and attr_name.endswith("_btn"):
                    btn = getattr(self, attr_name)
                    # 如果不是当前点击的按钮，则取消其选中状态
                    if btn != sender:
                        btn.setChecked(False)
            
            # 获取按钮的位置属性（相对位置元组）
            position_tuple = sender.property("position")
            if position_tuple:
                # 获取当前图片的原始尺寸
                try:
                    # 首先尝试使用传递的原图尺寸（如果存在）
                    if hasattr(self, 'original_width') and hasattr(self, 'original_height'):
                        img_width = self.original_width
                        img_height = self.original_height
                        print(f"[DEBUG] 使用传递的原图尺寸: {img_width}x{img_height}")
                    else:
                        # 如果没有传递的尺寸，回退到原来的获取方式
                        # 尝试从主窗口获取当前图片路径
                        main_window = self.parent()
                        if hasattr(main_window, 'image_manager'):
                            current_image_path = main_window.image_manager.get_current_image_path()
                            if current_image_path:
                                # 使用PIL打开图片获取原始尺寸
                                from PIL import Image
                                with Image.open(current_image_path) as img:
                                    img_width, img_height = img.size
                            else:
                                # 如果获取原图尺寸失败，回退到原来的相对位置处理方式
                                raise Exception("无法获取图片路径")
                        else:
                            # 如果获取原图尺寸失败，回退到原来的相对位置处理方式
                            raise Exception("无法访问主窗口的image_manager")
                    
                    # 获取按钮文本以确定位置（如"左上"、"上中"等）
                    position_str = sender.text()
                    
                    # 根据按钮文本计算水印在原图上的坐标，使水印位于九宫格的中心位置
                    # 将图片划分为3x3的网格，每个网格的宽高
                    grid_width = img_width // 3
                    grid_height = img_height // 3
                    
                    # 计算文本尺寸（估算）- 用于更精确的定位
                    font_size = self.font_size
                    text = self.watermark_text
                    # 简单估算文本宽度：每个字符约为font_size的1倍宽度
                    text_width = int(len(text) * (font_size+1)) if text else font_size * 3
                    text_height = font_size

                    try:
                        from PIL import Image, ImageDraw, ImageFont
                        
                        # 创建一个足够大的临时图像来绘制文本，用于计算文本边界框
                        temp_img = Image.new('RGB', (img_width, img_height), (255, 255, 255))
                        temp_draw = ImageDraw.Draw(temp_img)
                        
                        # 尝试加载字体
                        try:
                            # 获取主窗口的watermark_renderer实例
                            main_window = self.parent()
                            if hasattr(main_window, 'watermark_renderer'):
                                # 使用watermark_renderer中的字体加载逻辑，确保字体一致性
                                font = main_window.watermark_renderer._get_font(self.font_family, font_size, text, self.font_bold, self.font_italic)
                            else:
                                # 如果无法获取watermark_renderer，尝试加载指定字体
                                try:
                                    font = ImageFont.truetype(self.font_family, font_size)
                                except:
                                    # 如果指定字体加载失败，尝试使用系统默认字体
                                    try:
                                        font = ImageFont.truetype("arial.ttf", font_size)
                                    except:
                                        # 如果系统默认字体也加载失败，使用PIL默认字体
                                        font = ImageFont.load_default()
                        except Exception as e:
                            print(f"[DEBUG] 加载字体失败: {e}")
                            # 如果加载字体失败，使用默认字体
                            font = ImageFont.load_default()
                        
                        # 获取文本边界框，用于精确计算文本尺寸
                        # 使用(0, 0)作为参考点，因为我们只需要文本的尺寸
                        try:
                            # 确保文本是字符串类型，避免编码问题
                            text_str = str(text) if text is not None else ""
                            bbox = temp_draw.textbbox((0, 0), text_str, font=font)
                        except Exception as text_error:
                            print(f"[DEBUG] 文本边界框计算失败: {text_error}")
                            # 使用默认边界框
                            bbox = (0, 0, text_width, text_height)
                        

                        # 从边界框中提取文本的左右上下边界
                        text_r=bbox[2]  # 文本右边界
                        text_l=bbox[0]  # 文本左边界
                        text_t=bbox[1]  # 文本上边界
                        text_b=bbox[3]  # 文本下边界
                        print(f"text_l={text_l},text_r={text_r},text_t={text_t},text_b={text_b}")
                    
                        # 考虑旋转对边界的影响
                        rotation = self.rotation
                        if rotation != 0:
                            import math
                            # 计算旋转后的边界框
                            angle_rad = math.radians(abs(rotation))
                            rotated_width = abs(text_width * math.cos(angle_rad)) + abs(text_height * math.sin(angle_rad))
                            rotated_height = abs(text_width * math.sin(angle_rad)) + abs(text_height * math.cos(angle_rad))
                            text_width, text_height = rotated_width, rotated_height
                        
                        
                    except Exception as e:
                        print(f"[DEBUG] 使用PIL获取文本边界框时出错: {e}")
                        # 设置默认值
                        text_r = text_width
                        text_l = 0
                        text_t = 0
                        text_b = text_height

                    # 根据九宫格位置计算水印坐标，使水印文本位于对应格子的合适位置
                    # 优化了文本在格子中的定位，考虑了文本宽度和高度的影响
                    # 计算动态边距，根据图片尺寸自适应调整，最小为5像素
                    margin=max(min(img_height,img_width)//50,5)
                    if position_str == "左上":
                        # 左上格子的位置，考虑边距和文本高度
                        x = margin-25
                        y= margin-text_height//2
                    elif position_str == "上中":
                        # 上中格子的位置，水平居中，考虑边距和文本高度
                        x = img_width // 2 -  text_width//2
                        y= margin-text_height//2
                    elif position_str == "右上":
                        # 右上格子的位置，考虑边距和文本宽度
                        x= img_width-text_width-margin
                        y= margin-text_height//2
                    elif position_str == "左中":
                        # 左中格子的位置，垂直居中，考虑边距
                        x= margin-25
                        y= img_height // 2 - text_height
                    elif position_str == "中心":
                        # 中心格子的位置，完全居中
                        x = img_width // 2 -  text_width//2
                        y= img_height // 2 - text_height
                    elif position_str == "右中":
                        # 右中格子的位置，垂直居中，考虑边距和文本宽度
                        x= img_width-text_width-margin
                        y= img_height // 2 - text_height
                    elif position_str == "左下":
                        # 左下格子的位置，考虑边距和文本高度
                        x = margin-25
                        y= img_height-margin-text_height-text_height//2
                    elif position_str == "下中":
                        # 下中格子的位置，水平居中，考虑边距和文本高度
                        x = img_width // 2 -  text_width//2
                        y= img_height-margin-text_height-text_height//2
                    elif position_str == "右下":
                        # 右下格子的位置，考虑边距、文本宽度和高度
                        x= img_width-text_width-margin
                        y= img_height-margin-text_height-text_height//2
                    else:
                        # 默认使用中心位置
                        x= img_width // 2 -  text_width//2
                        y= img_height // 2
                    
                
                    # text_width = text_r-text_l
                    # text_height = text_b-text_t
                    # x=x+(text_width*self.compression_scale)//2
                    # y=y+(text_height*self.compression_scale)//2
                    # 使用update_position函数统一处理position更新，确保坐标一致性
                    self.update_position((x, y))
                    return
                except Exception as e:
                    print(f"[DEBUG] 获取图片尺寸或计算坐标失败: {e}")
                
                # 如果前两种方案都失败，直接报错
                print(f"[ERROR] 无法获取图片尺寸，无法计算水印位置")
                return
            else:
                # 如果没有位置属性，默认使用左上角位置
                self.update_position((20, 20))
                
            # 不再需要手动触发水印变化信号，因为update_position函数已经触发了
        
    def update_position(self, new_position):
        """
        统一更新position的函数，确保每次position变化时都更新watermark_x和watermark_y
        
        Args:
            new_position: 新的位置，可以是元组(x, y)或相对位置字符串
        """
        print(f"[DEBUG] TextWatermarkWidget.update_position: 修改position为 {new_position}")
        
        # 如果新位置是元组格式，检查是否是相对位置（0-1之间的值）
        if isinstance(new_position, tuple) and len(new_position) == 2:
            x_ratio, y_ratio = new_position[0], new_position[1]
            
            # 检查是否是相对位置（0-1之间的值）
            if 0 <= x_ratio <= 1 and 0 <= y_ratio <= 1:
                print(f"[BRANCH] TextWatermarkWidget.update_position: 处理相对位置（0-1之间的值），x_ratio={x_ratio}, y_ratio={y_ratio}")
                
                # 获取图片尺寸
                img_width = self.original_width
                img_height = self.original_height
                
                # 计算文本尺寸
                try:
                    from PIL import Image, ImageDraw, ImageFont
                    
                    # 创建一个足够大的临时图像来绘制文本，用于计算文本边界框
                    temp_img = Image.new('RGB', (img_width, img_height), (255, 255, 255))
                    temp_draw = ImageDraw.Draw(temp_img)
                    
                    # 尝试加载字体
                    try:
                        # 获取主窗口的watermark_renderer实例
                        main_window = self.parent()
                        if hasattr(main_window, 'watermark_renderer'):
                            # 使用watermark_renderer中的字体加载逻辑，确保字体一致性
                            font = main_window.watermark_renderer._get_font(self.font_family, self.font_size, self.watermark_text, self.font_bold, self.font_italic)
                        else:
                            # 如果无法获取watermark_renderer，尝试加载指定字体
                            try:
                                font = ImageFont.truetype(self.font_family, self.font_size)
                            except:
                                # 如果指定字体加载失败，尝试使用系统默认字体
                                try:
                                    font = ImageFont.truetype("arial.ttf", self.font_size)
                                except:
                                    # 如果系统默认字体也加载失败，使用PIL默认字体
                                    font = ImageFont.load_default()
                    except Exception as e:
                        print(f"[DEBUG] 加载字体失败: {e}")
                        # 如果加载字体失败，使用默认字体
                        font = ImageFont.load_default()
                    
                    # 获取文本边界框，用于精确计算文本尺寸
                    try:
                        # 确保文本是字符串类型，避免编码问题
                        text_str = str(self.watermark_text) if self.watermark_text is not None else ""
                        bbox = temp_draw.textbbox((0, 0), text_str, font=font)
                    except Exception as text_error:
                        print(f"[DEBUG] 文本边界框计算失败: {text_error}")
                        # 使用默认边界框
                        text_width = self.font_size * 3 if self.watermark_text else self.font_size
                        text_height = self.font_size
                        bbox = (0, 0, text_width, text_height)
                    
                    # 从边界框中提取文本的宽度和高度
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    
                    # 考虑旋转对边界的影响
                    if self.rotation != 0:
                        import math
                        # 计算旋转后的边界框
                        angle_rad = math.radians(abs(self.rotation))
                        rotated_width = abs(text_width * math.cos(angle_rad)) + abs(text_height * math.sin(angle_rad))
                        rotated_height = abs(text_width * math.sin(angle_rad)) + abs(text_height * math.cos(angle_rad))
                        text_width, text_height = rotated_width, rotated_height
                    
                except Exception as e:
                    print(f"[DEBUG] 使用PIL获取文本边界框时出错: {e}")
                    # 设置默认值
                    text_width = self.font_size * 3 if self.watermark_text else self.font_size
                    text_height = self.font_size
                
                # 计算绝对位置，直接转换为整数
                x = int(round(img_width * x_ratio - text_width / 2))
                y = int(round(img_height * y_ratio - text_height / 2))
                print(f"[DEBUG] TextWatermarkWidget.update_position: 计算绝对位置为 ({x}, {y})")
                
                # 如果有压缩比例，应用压缩比例并确保结果为整数
                if hasattr(self, 'compression_scale') and self.compression_scale is not None:
                    # x = int(round(x * self.compression_scale))
                    # y = int(round(y * self.compression_scale))
                    print(f"[DEBUG] TextWatermarkWidget.update_position: 应用压缩比例 {self.compression_scale:.4f} 到水印坐标: ({x}, {y})")
                
                # 更新position为绝对坐标
                self.position = (x, y)
                
                # 注意：position是水印在原图上的坐标，而watermark_x是水印在压缩图上的坐标
                # 两者的数学关系为：watermark_x = x * self.compression_scale（取整）
                self.watermark_x = int(x*self.compression_scale)
                self.watermark_y = int(y*self.compression_scale)
                print(f"[DEBUG] TextWatermarkWidget.update_position: 更新position和坐标: position={self.position}, watermark_x={self.watermark_x}, watermark_y={self.watermark_y}")
            else:
                # 处理绝对坐标
                print(f"[BRANCH] TextWatermarkWidget.update_position: 处理绝对坐标，x_ratio={x_ratio}, y_ratio={y_ratio}")
                # 这些坐标已经是绝对坐标，直接使用
                x = int(round(new_position[0]))
                y = int(round(new_position[1]))
                
                # 如果有压缩比例，应用压缩比例并确保结果为整数
                if hasattr(self, 'compression_scale') and self.compression_scale is not None:
                    # x = int(round(x * self.compression_scale))
                    # y = int(round(y * self.compression_scale))
                    print(f"[DEBUG] TextWatermarkWidget.update_position: 应用压缩比例 {self.compression_scale:.4f} 到水印坐标: ({x}, {y})")
                
                # 更新position和坐标
                self.position = (x, y)
                
                # 注意：position是水印在原图上的坐标，而watermark_x是水印在压缩图上的坐标
                # 两者的数学关系为：watermark_x = x * self.compression_scale（取整）
                self.watermark_x = int(x*self.compression_scale)
                self.watermark_y = int(y*self.compression_scale)
                print(f"[DEBUG] TextWatermarkWidget.update_position: 更新position和坐标: position={self.position}, watermark_x={self.watermark_x}, watermark_y={self.watermark_y}")
        elif isinstance(new_position, list) and len(new_position) == 2:
            # 处理列表格式的位置（从JSON文件加载的可能是列表而不是元组）
            print(f"[BRANCH] TextWatermarkWidget.update_position: 处理列表格式的位置，new_position={new_position}")
            # 将列表转换为元组，然后按照元组的逻辑处理
            self.update_position(tuple(new_position))
        else:
            # 处理预定义的位置字符串
            print(f"[BRANCH] TextWatermarkWidget.update_position: 处理预定义的位置字符串，position='{new_position}'")
            # 更新position
            self.position = new_position
        
        # 触发水印变化信号，这将更新预览和坐标显示
        print(f"[DEBUG] TextWatermarkWidget.update_position: 调用函数: self.watermark_changed.emit")
        self.watermark_changed.emit()
        
        # 更新坐标输入框的值
        self.update_coordinate_inputs()
    
    def update_coordinate_inputs(self):
        """更新坐标输入框的值，使其与当前水印位置保持同步"""
        # 如果position是元组格式（绝对坐标），则更新输入框的值
        if isinstance(self.position, tuple) and len(self.position) == 2:
            x, y = self.position
            # 检查是否是绝对坐标（非相对位置）
            if not (0 <= x <= 1 and 0 <= y <= 1):
                self.coord_x_spin.setValue(int(x))
                self.coord_y_spin.setValue(int(y))
    
    def on_apply_coord_clicked(self):
        """处理手动坐标输入应用按钮点击事件"""
        # 获取输入的坐标值
        x = self.coord_x_spin.value()
        y = self.coord_y_spin.value()
        
        # 更新position为绝对坐标
        self.position = (x, y)
        
        # 更新watermark_x和watermark_y为压缩图坐标
        # position是水印在原图上的坐标，watermark_x是水印在压缩图上的坐标
        # 关系: watermark_x = x * self.compression_scale (取整)
        self.watermark_x = int(x * self.compression_scale)
        self.watermark_y = int(y * self.compression_scale)
        
        # 更新UI状态
        self.update_position((x, y))
        
        # 触发水印变化信号，更新预览
        self.watermark_changed.emit()
        
        # 调用render方法立即更新水印渲染
        if hasattr(self, 'parent') and self.parent():
            main_window = self.parent()
            if hasattr(main_window, 'update_preview_with_watermark'):
                print(f"[DEBUG] TextWatermarkWidget.on_apply_coord_clicked: 调用render方法更新水印渲染")
                main_window.update_preview_with_watermark()
    
    def on_shadow_changed(self, state):
        """阴影效果变化"""
        self.enable_shadow = (state == Qt.Checked)
        self.watermark_changed.emit()
        
    def on_outline_changed(self, state):
        """描边效果变化"""
        self.enable_outline = (state == Qt.Checked)
        self.watermark_changed.emit()
        
    def on_outline_color_clicked(self):
        """描边颜色按钮点击"""
        color = QColorDialog.getColor(self.outline_color, self, "选择描边颜色")
        if color.isValid():
            self.outline_color = color
            self.update_outline_color_button()
            self.watermark_changed.emit()
    
    def on_outline_width_changed(self, value):
        """描边宽度变化"""
        self.outline_width = value
        self.watermark_changed.emit()
    
    def on_shadow_color_clicked(self):
        """阴影颜色按钮点击"""
        color = QColorDialog.getColor(self.shadow_color, self, "选择阴影颜色")
        if color.isValid():
            self.shadow_color = color
            self.update_shadow_color_button()
            self.watermark_changed.emit()
    
    def on_outline_offset_changed(self):
        """描边偏移变化"""
        self.outline_offset = (self.outline_offset_x_spin.value(), self.outline_offset_y_spin.value())
        self.watermark_changed.emit()
        
    def on_shadow_offset_changed(self):
        """阴影偏移变化"""
        self.shadow_offset = (self.shadow_offset_x_spin.value(), self.shadow_offset_y_spin.value())
        self.watermark_changed.emit()
    
    def on_shadow_blur_changed(self, value):
        """阴影模糊半径变化"""
        self.shadow_blur = value
        self.watermark_changed.emit()
        
    def on_preview_clicked(self):
        """预览按钮点击"""
        self.watermark_changed.emit()
        
    def on_apply_clicked(self):
        """应用按钮点击"""
        self.watermark_changed.emit()
        
    def get_watermark_settings(self):
        """获取水印设置"""
        # 确保颜色是QColor对象
        def ensure_qcolor(color):
            if isinstance(color, QColor):
                return color
            elif isinstance(color, tuple) and len(color) >= 3:
                return QColor(color[0], color[1], color[2])
            elif isinstance(color, str):
                return QColor(color)
            else:
                return QColor(0, 0, 0)  # 默认黑色
        
        font_color = ensure_qcolor(self.font_color)
        outline_color = ensure_qcolor(self.outline_color)
        shadow_color = ensure_qcolor(self.shadow_color)
        
        return {
            "text": self.watermark_text,
            "font_family": self.font_family,
            "font_size": self.font_size,
            "font_bold": self.font_bold,
            "font_italic": self.font_italic,
            "color": (font_color.red(), font_color.green(), font_color.blue()),
            "opacity": self.opacity,
            "position": self.position,
            "watermark_x": self.watermark_x,
            "watermark_y": self.watermark_y,
            "rotation": self.rotation,
            "enable_shadow": self.enable_shadow,
            "enable_outline": self.enable_outline,
            "outline_color": (outline_color.red(), outline_color.green(), outline_color.blue()),
            "outline_width": self.outline_width,
            "outline_offset": self.outline_offset,
            "shadow_color": (shadow_color.red(), shadow_color.green(), shadow_color.blue()),
            "shadow_offset": self.shadow_offset,
            "shadow_blur": self.shadow_blur
        }
    
    def set_watermark_settings(self, settings):
        """设置水印设置并更新UI（用于图片特定水印）"""
        if not settings:
            return
            
        # 阻止信号发射，避免触发水印变化信号
        self.blockSignals(True)
        
        try:
            # 更新文本设置
            if "text" in settings:
                self.watermark_text = settings["text"]
                self.text_input.setText(self.watermark_text)
                
                # 根据文本内容更新样式
                if self.watermark_text == "":
                    # 文本为空时显示灰色占位样式
                    self.text_input.setStyleSheet("""
                        QLineEdit {
                            color: #999;
                            font-style: italic;
                        }
                    """)
                else:
                    # 文本不为空时显示正常样式
                    self.text_input.setStyleSheet("""
                        QLineEdit {
                            color: #000;
                            font-style: normal;
                        }
                    """)
            
            # 更新字体设置
            if "font_family" in settings:
                self.font_family = settings["font_family"]
                # 查找匹配的实际字体名称
                found = False
                for i in range(self.font_combo.count()):
                    if self.font_combo.itemData(i, Qt.UserRole) == self.font_family:
                        self.font_combo.setCurrentIndex(i)
                        found = True
                        break
                # 如果没有找到，尝试使用文本匹配
                if not found:
                    index = self.font_combo.findText(self.font_family)
                    if index >= 0:
                        self.font_combo.setCurrentIndex(index)
            
            if "font_size" in settings:
                self.font_size = settings["font_size"]
                self.font_size_spin.setValue(self.font_size)
            
            # 更新颜色和透明度
            if "color" in settings:
                if isinstance(settings["color"], (tuple, list)) and len(settings["color"]) >= 3:
                    # 如果是RGB元组或列表，转换为QColor
                    self.font_color = QColor(settings["color"][0], settings["color"][1], settings["color"][2])
                elif isinstance(settings["color"], str):
                    # 如果是字符串，尝试从字符串创建QColor
                    self.font_color = QColor(settings["color"])
                elif isinstance(settings["color"], QColor):
                    # 如果已经是QColor对象，直接使用
                    self.font_color = settings["color"]
                else:
                    # 其他情况，使用默认颜色
                    self.font_color = QColor(0, 0, 255)  # 默认蓝色
                    print(f"[DEBUG CLR] 警告：无法识别的颜色类型 {type(settings['color'])}，使用默认颜色")
                self.update_color_button()
            
            if "opacity" in settings:
                self.opacity = settings["opacity"]
                self.opacity_slider.setValue(self.opacity)
                self.opacity_label.setText(f"{self.opacity}%")
            
            # 更新旋转角度
            if "rotation" in settings:
                self.rotation = settings["rotation"]
                self.rotation_spin.setValue(self.rotation)
            
            # 更新位置
            if "position" in settings:
                # 检查position是否是列表或元组格式
                if isinstance(settings["position"], (list, tuple)) and len(settings["position"]) == 2:
                    # 如果是列表或元组，检查是否是相对位置（0-1之间的值）
                    x, y = settings["position"]
                    if 0 <= x <= 1 and 0 <= y <= 1:
                        # 是相对位置，直接使用
                        print(f"[DEBUG] TextWatermarkWidget.set_watermark_settings: 检测到相对位置 {settings['position']}")
                        self.update_position(settings["position"])
                    else:
                        # 是绝对位置，直接使用
                        print(f"[DEBUG] TextWatermarkWidget.set_watermark_settings: 检测到绝对位置 {settings['position']}")
                        self.update_position(settings["position"])
                else:
                    # 如果不是列表或元组，可能是字符串或其他格式，直接使用
                    print(f"[DEBUG] TextWatermarkWidget.set_watermark_settings: 检测到非列表/元组位置 {settings['position']}")
                    self.update_position(settings["position"])
                
                # 更新位置按钮状态
                for attr_name in dir(self):
                    if attr_name.startswith("pos_") and attr_name.endswith("_btn"):
                        btn = getattr(self, attr_name)
                        btn_pos = btn.property("position")
                        # 检查是否为元组位置（九宫格位置）
                        if isinstance(btn_pos, tuple) and isinstance(self.position, tuple):
                            # 比较元组位置（允许一定的误差）
                            if abs(btn_pos[0] - self.position[0]) < 0.01 and abs(btn_pos[1] - self.position[1]) < 0.01:
                                btn.setChecked(True)
                            else:
                                btn.setChecked(False)
                        else:
                            # 如果不是元组位置，直接比较
                            btn.setChecked(btn_pos == self.position)
            
            # 更新watermark_x和watermark_y（如果position中没有提供这些值）
            if "watermark_x" in settings and "watermark_y" not in settings:
                self.watermark_x = settings["watermark_x"]
            
            if "watermark_y" in settings and "watermark_x" not in settings:
                self.watermark_y = settings["watermark_y"]
            
            # 更新效果设置
            if "enable_shadow" in settings:
                self.enable_shadow = settings["enable_shadow"]
                self.shadow_checkbox.setChecked(self.enable_shadow)
            
            if "enable_outline" in settings:
                self.enable_outline = settings["enable_outline"]
                self.outline_checkbox.setChecked(self.enable_outline)
            
            # 更新效果详细设置
            if "outline_color" in settings:
                if isinstance(settings["outline_color"], (tuple, list)) and len(settings["outline_color"]) >= 3:
                    # 如果是RGB元组或列表，转换为QColor
                    self.outline_color = QColor(settings["outline_color"][0], settings["outline_color"][1], settings["outline_color"][2])
                elif isinstance(settings["outline_color"], str):
                    # 如果是字符串，尝试从字符串创建QColor
                    self.outline_color = QColor(settings["outline_color"])
                elif isinstance(settings["outline_color"], QColor):
                    # 如果已经是QColor对象，直接使用
                    self.outline_color = settings["outline_color"]
                else:
                    # 其他情况，使用默认颜色
                    self.outline_color = QColor(0, 0, 0)  # 默认黑色
                    print(f"[DEBUG CLR] 警告：无法识别的outline_color类型 {type(settings['outline_color'])}，使用默认颜色")
                self.update_outline_color_button()
            
            if "outline_width" in settings:
                self.outline_width = settings["outline_width"]
                if self.outline_width is None:
                    self.outline_width_spin.setValue(0)  # 0表示自动
                else:
                    self.outline_width_spin.setValue(self.outline_width)
            
            if "shadow_color" in settings:
                if isinstance(settings["shadow_color"], (tuple, list)) and len(settings["shadow_color"]) >= 3:
                    # 如果是RGB元组或列表，转换为QColor
                    self.shadow_color = QColor(settings["shadow_color"][0], settings["shadow_color"][1], settings["shadow_color"][2])
                elif isinstance(settings["shadow_color"], str):
                    # 如果是字符串，尝试从字符串创建QColor
                    self.shadow_color = QColor(settings["shadow_color"])
                elif isinstance(settings["shadow_color"], QColor):
                    # 如果已经是QColor对象，直接使用
                    self.shadow_color = settings["shadow_color"]
                else:
                    # 其他情况，使用默认颜色
                    self.shadow_color = QColor(0, 0, 0)  # 默认黑色
                    print(f"[DEBUG CLR] 警告：无法识别的shadow_color类型 {type(settings['shadow_color'])}，使用默认颜色")
                self.update_shadow_color_button()
            
            if "shadow_offset" in settings:
                self.shadow_offset = settings["shadow_offset"]
                self.shadow_offset_x_spin.setValue(self.shadow_offset[0])
                self.shadow_offset_y_spin.setValue(self.shadow_offset[1])
            
            if "shadow_blur" in settings:
                self.shadow_blur = settings["shadow_blur"]
                self.shadow_blur_spin.setValue(self.shadow_blur)
                
        finally:
            # 恢复信号发射
            self.blockSignals(False)
    
    def set_watermark_settings_with_placeholder_style(self, settings):
        """设置水印设置并更新UI（用于全局默认水印，显示为灰色占位样式）"""
        if not settings:
            return
            
        # 阻止信号发射，避免触发水印变化信号
        self.blockSignals(True)
        
        try:
            # 更新文本设置
            if "text" in settings:
                self.watermark_text = settings["text"]
                self.text_input.setText(self.watermark_text)
                
                # 对于全局默认水印，始终显示灰色占位样式
                self.text_input.setStyleSheet("""
                    QLineEdit {
                        color: #999;
                        font-style: italic;
                    }
                """)
            
            # 更新字体设置
            if "font_family" in settings:
                self.font_family = settings["font_family"]
                # 查找匹配的实际字体名称
                found = False
                for i in range(self.font_combo.count()):
                    if self.font_combo.itemData(i, Qt.UserRole) == self.font_family:
                        self.font_combo.setCurrentIndex(i)
                        found = True
                        break
                # 如果没有找到，尝试使用文本匹配
                if not found:
                    index = self.font_combo.findText(self.font_family)
                    if index >= 0:
                        self.font_combo.setCurrentIndex(index)
            
            if "font_size" in settings:
                self.font_size = settings["font_size"]
                self.font_size_spin.setValue(self.font_size)
            
            # 更新颜色和透明度
            if "color" in settings:
                if isinstance(settings["color"], (tuple, list)) and len(settings["color"]) >= 3:
                    # 如果是RGB元组或列表，转换为QColor
                    self.font_color = QColor(settings["color"][0], settings["color"][1], settings["color"][2])
                elif isinstance(settings["color"], str):
                    # 如果是字符串，尝试从字符串创建QColor
                    self.font_color = QColor(settings["color"])
                elif isinstance(settings["color"], QColor):
                    # 如果已经是QColor对象，直接使用
                    self.font_color = settings["color"]
                else:
                    # 其他情况，使用默认颜色
                    self.font_color = QColor(0, 0, 255)  # 默认蓝色
                    print(f"[DEBUG CLR] 警告：无法识别的颜色类型 {type(settings['color'])}，使用默认颜色")
                self.update_color_button()
            
            if "opacity" in settings:
                self.opacity = settings["opacity"]
                self.opacity_slider.setValue(self.opacity)
                self.opacity_label.setText(f"{self.opacity}%")
            
            # 更新旋转角度
            if "rotation" in settings:
                self.rotation = settings["rotation"]
                self.rotation_spin.setValue(self.rotation)
            
            # 更新位置
            if "position" in settings:
                # 使用update_position函数统一处理position更新
                self.update_position(settings["position"])
                # 更新位置按钮状态
                for attr_name in dir(self):
                    if attr_name.startswith("pos_") and attr_name.endswith("_btn"):
                        btn = getattr(self, attr_name)
                        btn_pos = btn.property("position")
                        # 检查是否为元组位置（九宫格位置）
                        if isinstance(btn_pos, tuple) and isinstance(self.position, tuple):
                            # 比较元组位置（允许一定的误差）
                            if abs(btn_pos[0] - self.position[0]) < 0.01 and abs(btn_pos[1] - self.position[1]) < 0.01:
                                btn.setChecked(True)
                            else:
                                btn.setChecked(False)
                        else:
                            # 如果不是元组位置，直接比较
                            btn.setChecked(btn_pos == self.position)
            
            # 更新效果设置
            if "enable_shadow" in settings:
                self.enable_shadow = settings["enable_shadow"]
                self.shadow_checkbox.setChecked(self.enable_shadow)
            
            if "enable_outline" in settings:
                self.enable_outline = settings["enable_outline"]
                self.outline_checkbox.setChecked(self.enable_outline)
                
        finally:
            # 恢复信号发射
            self.blockSignals(False)

    def set_original_dimensions(self, width, height):
        """
        设置原图尺寸
        
        Args:
            width (int): 原图宽度
            height (int): 原图高度
        """
        self.original_width = width
        self.original_height = height
        print(f"[DEBUG] TextWatermarkWidget接收到原图尺寸: {width}x{height}")
    
    def set_compression_scale(self, scale):
        """
        设置压缩比例
        
        Args:
            scale (float): 压缩比例，用于将原图坐标转换为预览图坐标
            
        Note:
            position是水印在原图上的坐标，而watermark_x是水印在压缩图上的坐标
            两者的数学关系为：watermark_x = x * self.compression_scale（取整）
        """
        self.compression_scale = scale
        print(f"[DEBUG] TextWatermarkWidget接收到压缩比例: {scale:.4f}")