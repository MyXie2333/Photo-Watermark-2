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
    set_default_watermark = pyqtSignal()
    # 信号：字体切换提示
    font_switch_notification = pyqtSignal(str)  # 参数为提示信息
    
    def __init__(self):
        super().__init__()
        
        # 默认水印设置
        self.watermark_text = ""  # 空字符串，不显示默认水印文本
        self.font_family = "Microsoft YaHei"  # 使用支持中文的字体
        self.font_size = 24
        self.font_bold = False  # 粗体
        self.font_italic = False  # 斜体
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
        """加载系统字体 - 只显示在字体文件映射中存在的字体"""
        # 定义支持的字体列表（基于watermark_renderer.py中的字体文件映射）
        supported_chinese_fonts = [
            "Microsoft YaHei",  # 微软雅黑
            "SimHei",           # 黑体
            "SimSun",           # 宋体
            "KaiTi",            # 楷体
            "FangSong",         # 仿宋
            "Arial Unicode MS"  # 回退字体
        ]
        
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
            self.font_combo.addItem(font)
        
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
        chinese_font_files = {
            "Microsoft YaHei": ["msyh.ttc", "msyh.ttf", "msyhbd.ttc", "msyhbd.ttf", "msyhl.ttc"],
            "SimHei": ["simhei.ttf"],
            "SimSun": ["simsun.ttc", "simsunb.ttf", "SimsunExtG.ttf"],
            "KaiTi": ["simkai.ttf", "STKAITI.TTF"],
            "FangSong": ["simfang.ttf"],
            "Arial Unicode MS": ["arialuni.ttf"]
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
            for font_file in chinese_font_files[font_name]:
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
        self.font_combo.currentTextChanged.connect(self.on_font_changed)
        self.font_size_spin.valueChanged.connect(self.on_font_size_changed)
        self.bold_checkbox.stateChanged.connect(self.on_bold_changed)
        self.italic_checkbox.stateChanged.connect(self.on_italic_changed)
        self.clear_button.clicked.connect(self.on_clear_clicked)
        self.text_input.textChanged.connect(self.on_text_changed)
        self.text_input.installEventFilter(self)
        
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
        
    def on_font_changed(self, font):
        """字体变化"""
        self.font_family = font
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
            current_font = self.font_combo.currentText()
            
            # 获取下拉菜单中所有可用的中文字体
            chinese_fonts = []
            chinese_keywords = ['yahei', 'simhei', 'simsun', 'kaiti', 'fangsong', 
                               '黑体', '宋体', '楷体', '仿宋', '微软雅黑', '华文', '方正']
            
            # 从下拉菜单中检测所有中文字体
            for i in range(self.font_combo.count()):
                item_text = self.font_combo.itemText(i)
                if not item_text.startswith("---"):  # 跳过分隔线
                    item_lower = item_text.lower()
                    if any(keyword in item_lower for keyword in chinese_keywords):
                        chinese_fonts.append(item_text)
            
            # 关键修复：如果当前字体已经是中文字体，不要改变字体
            if current_font in chinese_fonts:
                return  # 保持当前字体不变
            
            # 只有当当前字体不是中文字体时，才自动切换到中文字体
            if current_font not in chinese_fonts:
                # 优先尝试微软雅黑
                if "Microsoft YaHei" in chinese_fonts:
                    self.font_combo.setCurrentText("Microsoft YaHei")
                    self.font_family = "Microsoft YaHei"
                    # 发出字体切换提示信号
                    self.font_switch_notification.emit("当前字体不支持中文显示，已为您切换至中文字体")
                # 如果微软雅黑不可用，尝试其他中文字体
                elif chinese_fonts:
                    # 按优先级选择：微软雅黑 > 黑体 > 宋体 > 楷体 > 仿宋 > 其他
                    priority_order = ["Microsoft YaHei", "SimHei", "SimSun", "KaiTi", "FangSong"]
                    for font in priority_order:
                        if font in chinese_fonts:
                            self.font_combo.setCurrentText(font)
                            self.font_family = font
                            # 发出字体切换提示信号
                            self.font_switch_notification.emit("当前字体不支持中文显示，已为您切换至中文字体")
                            break
                    else:
                        # 如果没有优先级字体，使用第一个可用的中文字体
                        self.font_combo.setCurrentText(chinese_fonts[0])
                        self.font_family = chinese_fonts[0]
                        # 发出字体切换提示信号
                        self.font_switch_notification.emit("当前字体不支持中文显示，已为您切换至中文字体")
        
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
            "font_bold": self.font_bold,
            "font_italic": self.font_italic,
            "color": self.font_color,
            "opacity": self.opacity,
            "position": self.position,
            "rotation": self.rotation,
            "enable_shadow": self.enable_shadow,
            "enable_outline": self.enable_outline
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
                index = self.font_combo.findText(self.font_family)
                if index >= 0:
                    self.font_combo.setCurrentIndex(index)
                else:
                    self.font_combo.setCurrentText(self.font_family)
            
            if "font_size" in settings:
                self.font_size = settings["font_size"]
                self.font_size_spin.setValue(self.font_size)
            
            # 更新颜色和透明度
            if "color" in settings:
                self.font_color = settings["color"]
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
                self.position = settings["position"]
                # 更新位置按钮状态
                for attr_name in dir(self):
                    if attr_name.startswith("pos_") and attr_name.endswith("_btn"):
                        btn = getattr(self, attr_name)
                        btn_pos = btn.property("position")
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
                index = self.font_combo.findText(self.font_family)
                if index >= 0:
                    self.font_combo.setCurrentIndex(index)
                else:
                    self.font_combo.setCurrentText(self.font_family)
            
            if "font_size" in settings:
                self.font_size = settings["font_size"]
                self.font_size_spin.setValue(self.font_size)
            
            # 更新颜色和透明度
            if "color" in settings:
                self.font_color = settings["color"]
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
                self.position = settings["position"]
                # 更新位置按钮状态
                for attr_name in dir(self):
                    if attr_name.startswith("pos_") and attr_name.endswith("_btn"):
                        btn = getattr(self, attr_name)
                        btn_pos = btn.property("position")
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