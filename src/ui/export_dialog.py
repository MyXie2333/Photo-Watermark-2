"""
导出对话框模块
提供图片导出时的命名规则、图片质量和尺寸调整选项
"""

import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                            QSlider, QSpinBox, QRadioButton, QButtonGroup, QGroupBox,
                            QDialogButtonBox, QLineEdit, QCheckBox, QFormLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap

class ExportDialog(QDialog):
    """导出对话框类，提供图片导出时的各种选项"""
    
    # 信号：导出参数已确认
    export_confirmed = pyqtSignal(dict)
    
    def __init__(self, image_path, parent=None):
        """
        初始化导出对话框
        
        Args:
            image_path (str): 要导出的图片路径
            parent: 父窗口
        """
        super().__init__(parent)
        self.image_path = image_path
        self.original_name = os.path.splitext(os.path.basename(image_path))[0]
        self.original_extension = os.path.splitext(image_path)[1].lower()
        
        self.setWindowTitle("导出设置")
        self.setMinimumWidth(400)
        self.setup_ui()
        
    def setup_ui(self):
        """设置对话框UI"""
        main_layout = QVBoxLayout()
        
        # 文件命名规则组
        naming_group = QGroupBox("文件命名规则")
        naming_layout = QVBoxLayout()
        
        # 命名规则选择
        self.naming_combo = QComboBox()
        self.naming_combo.addItem("保留原文件名", "original")
        self.naming_combo.addItem("添加自定义前缀", "prefix")
        self.naming_combo.addItem("添加自定义后缀", "suffix")
        self.naming_combo.currentIndexChanged.connect(self.update_naming_options)
        
        naming_layout.addWidget(QLabel("命名规则:"))
        naming_layout.addWidget(self.naming_combo)
        
        # 前缀/后缀输入框
        self.prefix_suffix_layout = QHBoxLayout()
        self.prefix_suffix_label = QLabel("前缀:")
        self.prefix_suffix_input = QLineEdit("wm_")
        self.prefix_suffix_layout.addWidget(self.prefix_suffix_label)
        self.prefix_suffix_layout.addWidget(self.prefix_suffix_input)
        
        naming_layout.addLayout(self.prefix_suffix_layout)
        
        # 文件名预览
        self.filename_preview = QLabel()
        self.filename_preview.setStyleSheet("background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc;")
        naming_layout.addWidget(QLabel("文件名预览:"))
        naming_layout.addWidget(self.filename_preview)
        
        naming_group.setLayout(naming_layout)
        main_layout.addWidget(naming_group)
        
        # 图片质量组（对所有格式，但仅对JPEG格式有效）
        quality_group = QGroupBox("JPEG图片质量")
        quality_layout = QVBoxLayout()
        
        # 质量滑块
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(0, 100)
        self.quality_slider.setValue(95)  # 默认高质量
        self.quality_slider.setTickPosition(QSlider.TicksBelow)
        self.quality_slider.setTickInterval(10)
        self.quality_slider.valueChanged.connect(self.update_quality_label)
        
        # 质量数值显示
        self.quality_layout = QHBoxLayout()
        self.quality_label = QLabel("95")
        self.quality_layout.addWidget(QLabel("低质量"))
        self.quality_layout.addWidget(self.quality_slider)
        self.quality_layout.addWidget(self.quality_label)
        self.quality_layout.addWidget(QLabel("高质量"))
        
        quality_layout.addLayout(self.quality_layout)
        quality_group.setLayout(quality_layout)
        
        # 如果不是JPEG格式，禁用质量调节
        if self.original_extension not in ['.jpg', '.jpeg']:
            self.quality_slider.setEnabled(False)
            self.quality_label.setEnabled(False)
            # 添加提示文本
            quality_hint = QLabel("(仅对JPEG格式有效)")
            quality_hint.setStyleSheet("color: gray; font-style: italic;")
            quality_layout.addWidget(quality_hint)
        
        main_layout.addWidget(quality_group)
        
        # 图片尺寸调整组
        size_group = QGroupBox("图片尺寸调整")
        size_layout = QVBoxLayout()
        
        # 尺寸调整选项
        self.size_option_group = QButtonGroup(self)
        
        self.no_resize_radio = QRadioButton("保持原始尺寸")
        self.no_resize_radio.setChecked(True)
        self.size_option_group.addButton(self.no_resize_radio, 0)
        
        self.width_resize_radio = QRadioButton("按宽度调整")
        self.size_option_group.addButton(self.width_resize_radio, 1)
        
        self.height_resize_radio = QRadioButton("按高度调整")
        self.size_option_group.addButton(self.height_resize_radio, 2)
        
        self.percent_resize_radio = QRadioButton("按百分比调整")
        self.size_option_group.addButton(self.percent_resize_radio, 3)
        
        size_layout.addWidget(self.no_resize_radio)
        size_layout.addWidget(self.width_resize_radio)
        size_layout.addWidget(self.height_resize_radio)
        size_layout.addWidget(self.percent_resize_radio)
        
        # 尺寸调整值
        self.resize_value_layout = QHBoxLayout()
        self.resize_value_label = QLabel("")
        self.resize_value_spin = QSpinBox()
        self.resize_value_spin.setRange(1, 10000)
        self.resize_value_spin.setValue(800)
        self.resize_value_spin.setEnabled(False)
        
        self.resize_value_layout.addWidget(self.resize_value_label)
        self.resize_value_layout.addWidget(self.resize_value_spin)
        self.resize_value_layout.addWidget(QLabel("像素"))
        
        # 百分比调整值
        self.percent_value_layout = QHBoxLayout()
        self.percent_value_label = QLabel("")
        self.percent_value_spin = QSpinBox()
        self.percent_value_spin.setRange(1, 200)
        self.percent_value_spin.setValue(100)
        self.percent_value_spin.setEnabled(False)
        
        self.percent_value_layout.addWidget(self.percent_value_label)
        self.percent_value_layout.addWidget(self.percent_value_spin)
        self.percent_value_layout.addWidget(QLabel("%"))
        
        size_layout.addLayout(self.resize_value_layout)
        size_layout.addLayout(self.percent_value_layout)
        
        # 连接信号
        self.no_resize_radio.toggled.connect(lambda: self.update_resize_options(0))
        self.width_resize_radio.toggled.connect(lambda: self.update_resize_options(1))
        self.height_resize_radio.toggled.connect(lambda: self.update_resize_options(2))
        self.percent_resize_radio.toggled.connect(lambda: self.update_resize_options(3))
        
        size_group.setLayout(size_layout)
        main_layout.addWidget(size_group)
        
        # 对话框按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
        
        self.setLayout(main_layout)
        
        # 初始化UI状态
        self.update_naming_options()
        self.update_filename_preview()
    
    def update_naming_options(self):
        """更新命名选项的显示状态"""
        option = self.naming_combo.currentData()
        
        if option == "original":
            self.prefix_suffix_label.setEnabled(False)
            self.prefix_suffix_input.setEnabled(False)
        elif option == "prefix":
            self.prefix_suffix_label.setText("前缀:")
            self.prefix_suffix_label.setEnabled(True)
            self.prefix_suffix_input.setEnabled(True)
            # 设置前缀的默认值
            if self.prefix_suffix_input.text() == "_watermarked":
                self.prefix_suffix_input.setText("wm_")
        elif option == "suffix":
            self.prefix_suffix_label.setText("后缀:")
            self.prefix_suffix_label.setEnabled(True)
            self.prefix_suffix_input.setEnabled(True)
            # 设置后缀的默认值
            if self.prefix_suffix_input.text() == "wm_":
                self.prefix_suffix_input.setText("_watermarked")
        
        self.update_filename_preview()
    
    def update_filename_preview(self):
        """更新文件名预览"""
        option = self.naming_combo.currentData()
        
        if option == "original":
            filename = f"{self.original_name}{self.original_extension}"
        elif option == "prefix":
            prefix = self.prefix_suffix_input.text()
            filename = f"{prefix}{self.original_name}{self.original_extension}"
        elif option == "suffix":
            suffix = self.prefix_suffix_input.text()
            filename = f"{self.original_name}{suffix}{self.original_extension}"
        
        self.filename_preview.setText(filename)
    
    def update_quality_label(self, value):
        """更新质量标签"""
        self.quality_label.setText(str(value))
    
    def update_resize_options(self, option):
        """更新尺寸调整选项的显示状态"""
        if option == 0:  # 不调整
            self.resize_value_label.setText("")
            self.resize_value_spin.setEnabled(False)
            self.percent_value_label.setText("")
            self.percent_value_spin.setEnabled(False)
        elif option == 1:  # 按宽度
            self.resize_value_label.setText("宽度:")
            self.resize_value_spin.setEnabled(True)
            self.percent_value_label.setText("")
            self.percent_value_spin.setEnabled(False)
        elif option == 2:  # 按高度
            self.resize_value_label.setText("高度:")
            self.resize_value_spin.setEnabled(True)
            self.percent_value_label.setText("")
            self.percent_value_spin.setEnabled(False)
        elif option == 3:  # 按百分比
            self.resize_value_label.setText("")
            self.resize_value_spin.setEnabled(False)
            self.percent_value_label.setText("缩放比例:")
            self.percent_value_spin.setEnabled(True)
    
    def get_export_settings(self):
        """获取导出设置"""
        settings = {
            'naming_rule': self.naming_combo.currentData(),
            'prefix_suffix': self.prefix_suffix_input.text(),
            'resize_option': self.size_option_group.checkedId(),
            'resize_value': self.resize_value_spin.value() if self.resize_value_spin.isEnabled() else None,
            'percent_value': self.percent_value_spin.value() if self.percent_value_spin.isEnabled() else None,
            'quality': self.quality_slider.value(),
        }
        
        return settings
    
    def get_output_filename(self):
        """获取输出文件名"""
        option = self.naming_combo.currentData()
        
        if option == "original":
            filename = f"{self.original_name}{self.original_extension}"
        elif option == "prefix":
            prefix = self.prefix_suffix_input.text()
            filename = f"{prefix}{self.original_name}{self.original_extension}"
        elif option == "suffix":
            suffix = self.prefix_suffix_input.text()
            filename = f"{self.original_name}{suffix}{self.original_extension}"
        
        return filename
    
    def accept(self):
        """确认对话框"""
        # 发送导出确认信号
        self.export_confirmed.emit(self.get_export_settings())
        super().accept()


class BatchExportDialog(QDialog):
    """批量导出对话框类，提供批量导出时的各种选项"""
    
    # 信号：导出参数已确认
    export_confirmed = pyqtSignal(dict)
    
    def __init__(self, image_paths, parent=None):
        """
        初始化批量导出对话框
        
        Args:
            image_paths (list): 要导出的图片路径列表
            parent: 父窗口
        """
        super().__init__(parent)
        self.image_paths = image_paths
        
        self.setWindowTitle("批量导出设置")
        self.setMinimumWidth(400)
        self.setup_ui()
        
    def setup_ui(self):
        """设置对话框UI"""
        main_layout = QVBoxLayout()
        
        # 文件命名规则组
        naming_group = QGroupBox("文件命名规则")
        naming_layout = QVBoxLayout()
        
        # 命名规则选择
        self.naming_combo = QComboBox()
        self.naming_combo.addItem("保留原文件名", "original")
        self.naming_combo.addItem("添加自定义前缀", "prefix")
        self.naming_combo.addItem("添加自定义后缀", "suffix")
        self.naming_combo.currentIndexChanged.connect(self.update_naming_options)
        
        naming_layout.addWidget(QLabel("命名规则:"))
        naming_layout.addWidget(self.naming_combo)
        
        # 前缀/后缀输入框
        self.prefix_suffix_layout = QHBoxLayout()
        self.prefix_suffix_label = QLabel("前缀:")
        self.prefix_suffix_input = QLineEdit("wm_")
        self.prefix_suffix_layout.addWidget(self.prefix_suffix_label)
        self.prefix_suffix_layout.addWidget(self.prefix_suffix_input)
        
        naming_layout.addLayout(self.prefix_suffix_layout)
        
        # 文件名预览
        self.filename_preview = QLabel()
        self.filename_preview.setStyleSheet("background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc;")
        naming_layout.addWidget(QLabel("文件名预览:"))
        naming_layout.addWidget(self.filename_preview)
        
        naming_group.setLayout(naming_layout)
        main_layout.addWidget(naming_group)
        
        # 图片质量组（对所有格式，但仅对JPEG格式有效）
        quality_group = QGroupBox("JPEG图片质量")
        quality_layout = QVBoxLayout()
        
        # 质量滑块
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(0, 100)
        self.quality_slider.setValue(95)  # 默认高质量
        self.quality_slider.setTickPosition(QSlider.TicksBelow)
        self.quality_slider.setTickInterval(10)
        self.quality_slider.valueChanged.connect(self.update_quality_label)
        
        # 质量数值显示
        self.quality_layout = QHBoxLayout()
        self.quality_label = QLabel("95")
        self.quality_layout.addWidget(QLabel("低质量"))
        self.quality_layout.addWidget(self.quality_slider)
        self.quality_layout.addWidget(self.quality_label)
        self.quality_layout.addWidget(QLabel("高质量"))
        
        quality_layout.addLayout(self.quality_layout)
        
        # 添加提示文本
        quality_hint = QLabel("(仅对JPEG格式有效)")
        quality_hint.setStyleSheet("color: gray; font-style: italic;")
        quality_layout.addWidget(quality_hint)
        
        quality_group.setLayout(quality_layout)
        main_layout.addWidget(quality_group)
        
        # 图片尺寸调整组
        size_group = QGroupBox("图片尺寸调整")
        size_layout = QVBoxLayout()
        
        # 尺寸调整选项
        self.size_option_group = QButtonGroup(self)
        
        self.no_resize_radio = QRadioButton("保持原始尺寸")
        self.no_resize_radio.setChecked(True)
        self.size_option_group.addButton(self.no_resize_radio, 0)
        
        self.width_resize_radio = QRadioButton("按宽度调整")
        self.size_option_group.addButton(self.width_resize_radio, 1)
        
        self.height_resize_radio = QRadioButton("按高度调整")
        self.size_option_group.addButton(self.height_resize_radio, 2)
        
        self.percent_resize_radio = QRadioButton("按百分比调整")
        self.size_option_group.addButton(self.percent_resize_radio, 3)
        
        size_layout.addWidget(self.no_resize_radio)
        size_layout.addWidget(self.width_resize_radio)
        size_layout.addWidget(self.height_resize_radio)
        size_layout.addWidget(self.percent_resize_radio)
        
        # 尺寸调整值
        self.resize_value_layout = QHBoxLayout()
        self.resize_value_label = QLabel("")
        self.resize_value_spin = QSpinBox()
        self.resize_value_spin.setRange(1, 10000)
        self.resize_value_spin.setValue(800)
        self.resize_value_spin.setEnabled(False)
        
        self.resize_value_layout.addWidget(self.resize_value_label)
        self.resize_value_layout.addWidget(self.resize_value_spin)
        self.resize_value_layout.addWidget(QLabel("像素"))
        
        # 百分比调整值
        self.percent_value_layout = QHBoxLayout()
        self.percent_value_label = QLabel("")
        self.percent_value_spin = QSpinBox()
        self.percent_value_spin.setRange(1, 200)
        self.percent_value_spin.setValue(100)
        self.percent_value_spin.setEnabled(False)
        
        self.percent_value_layout.addWidget(self.percent_value_label)
        self.percent_value_layout.addWidget(self.percent_value_spin)
        self.percent_value_layout.addWidget(QLabel("%"))
        
        size_layout.addLayout(self.resize_value_layout)
        size_layout.addLayout(self.percent_value_layout)
        
        # 连接信号
        self.no_resize_radio.toggled.connect(lambda: self.update_resize_options(0))
        self.width_resize_radio.toggled.connect(lambda: self.update_resize_options(1))
        self.height_resize_radio.toggled.connect(lambda: self.update_resize_options(2))
        self.percent_resize_radio.toggled.connect(lambda: self.update_resize_options(3))
        
        size_group.setLayout(size_layout)
        main_layout.addWidget(size_group)
        
        # 对话框按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
        
        self.setLayout(main_layout)
        
        # 初始化UI状态
        self.update_naming_options()
        self.update_filename_preview()
    
    def update_naming_options(self):
        """更新命名选项的显示状态"""
        option = self.naming_combo.currentData()
        
        if option == "original":
            self.prefix_suffix_label.setEnabled(False)
            self.prefix_suffix_input.setEnabled(False)
        elif option == "prefix":
            self.prefix_suffix_label.setText("前缀:")
            self.prefix_suffix_label.setEnabled(True)
            self.prefix_suffix_input.setEnabled(True)
            # 设置前缀的默认值
            if self.prefix_suffix_input.text() == "_watermarked":
                self.prefix_suffix_input.setText("wm_")
        elif option == "suffix":
            self.prefix_suffix_label.setText("后缀:")
            self.prefix_suffix_label.setEnabled(True)
            self.prefix_suffix_input.setEnabled(True)
            # 设置后缀的默认值
            if self.prefix_suffix_input.text() == "wm_":
                self.prefix_suffix_input.setText("_watermarked")
        
        self.update_filename_preview()
    
    def update_filename_preview(self):
        """更新文件名预览"""
        if not self.image_paths:
            return
            
        # 使用第一张图片作为预览
        first_image = self.image_paths[0]
        original_name = os.path.splitext(os.path.basename(first_image))[0]
        original_extension = os.path.splitext(first_image)[1].lower()
        
        option = self.naming_combo.currentData()
        
        if option == "original":
            filename = f"{original_name}{original_extension}"
        elif option == "prefix":
            prefix = self.prefix_suffix_input.text()
            filename = f"{prefix}{original_name}{original_extension}"
        elif option == "suffix":
            suffix = self.prefix_suffix_input.text()
            filename = f"{original_name}{suffix}{original_extension}"
        
        self.filename_preview.setText(filename)
    
    def update_quality_label(self, value):
        """更新质量标签"""
        self.quality_label.setText(str(value))
    
    def update_resize_options(self, option):
        """更新尺寸调整选项的显示状态"""
        if option == 0:  # 不调整
            self.resize_value_label.setText("")
            self.resize_value_spin.setEnabled(False)
            self.percent_value_label.setText("")
            self.percent_value_spin.setEnabled(False)
        elif option == 1:  # 按宽度
            self.resize_value_label.setText("宽度:")
            self.resize_value_spin.setEnabled(True)
            self.percent_value_label.setText("")
            self.percent_value_spin.setEnabled(False)
        elif option == 2:  # 按高度
            self.resize_value_label.setText("高度:")
            self.resize_value_spin.setEnabled(True)
            self.percent_value_label.setText("")
            self.percent_value_spin.setEnabled(False)
        elif option == 3:  # 按百分比
            self.resize_value_label.setText("")
            self.resize_value_spin.setEnabled(False)
            self.percent_value_label.setText("缩放比例:")
            self.percent_value_spin.setEnabled(True)
    
    def get_export_settings(self):
        """获取导出设置"""
        settings = {
            'naming_rule': self.naming_combo.currentData(),
            'prefix_suffix': self.prefix_suffix_input.text(),
            'resize_option': self.size_option_group.checkedId(),
            'resize_value': self.resize_value_spin.value() if self.resize_value_spin.isEnabled() else None,
            'percent_value': self.percent_value_spin.value() if self.percent_value_spin.isEnabled() else None,
            'quality': self.quality_slider.value(),
        }
        
        return settings
    
    def get_output_filename(self, image_path):
        """获取输出文件名"""
        original_name = os.path.splitext(os.path.basename(image_path))[0]
        original_extension = os.path.splitext(image_path)[1].lower()
        
        option = self.naming_combo.currentData()
        
        if option == "original":
            filename = f"{original_name}{original_extension}"
        elif option == "prefix":
            prefix = self.prefix_suffix_input.text()
            filename = f"{prefix}{original_name}{original_extension}"
        elif option == "suffix":
            suffix = self.prefix_suffix_input.text()
            filename = f"{original_name}{suffix}{original_extension}"
        
        return filename
    
    def accept(self):
        """确认对话框"""
        # 发送导出确认信号
        self.export_confirmed.emit(self.get_export_settings())
        super().accept()