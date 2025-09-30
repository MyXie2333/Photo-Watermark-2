#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水印模板管理对话框
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QTabWidget, QListWidget, QListWidgetItem, QMessageBox, 
                            QInputDialog, QWidget, QRadioButton, QButtonGroup, QSpacerItem,
                            QSizePolicy, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from config_manager import get_config_manager


class TemplateManagerDialog(QDialog):
    """水印模板管理对话框"""
    
    def __init__(self, config_manager, parent=None, current_watermark_type=None, current_watermark_settings=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.current_watermark_type = current_watermark_type
        self.current_watermark_settings = current_watermark_settings
        self.init_ui()
        self.load_templates()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("水印模板管理")
        self.setMinimumSize(600, 400)
        
        # 主布局
        layout = QVBoxLayout(self)
        
        # 启动设置区域
        startup_group = QFrame()
        startup_group.setFrameShape(QFrame.StyledPanel)
        startup_layout = QVBoxLayout(startup_group)
        
        startup_label = QLabel("程序启动时加载设置：")
        startup_layout.addWidget(startup_label)
        
        # 单选按钮组
        self.startup_button_group = QButtonGroup(self)
        
        self.load_last_radio = QRadioButton("加载上一次关闭时的设置")
        self.load_default_radio = QRadioButton("加载默认模板")
        
        self.startup_button_group.addButton(self.load_last_radio)
        self.startup_button_group.addButton(self.load_default_radio)
        
        startup_layout.addWidget(self.load_last_radio)
        startup_layout.addWidget(self.load_default_radio)
        
        # 根据当前设置选择单选按钮
        if self.config_manager.get_load_last_settings():
            self.load_last_radio.setChecked(True)
        else:
            self.load_default_radio.setChecked(True)
        
        layout.addWidget(startup_group)
        
        # 模板管理区域
        template_group = QFrame()
        template_group.setFrameShape(QFrame.StyledPanel)
        template_layout = QVBoxLayout(template_group)
        
        # 标签页
        self.tab_widget = QTabWidget()
        self.text_template_tab = QWidget()
        self.image_template_tab = QWidget()
        
        self.tab_widget.addTab(self.text_template_tab, "文字水印模板")
        self.tab_widget.addTab(self.image_template_tab, "图片水印模板")
        
        # 文字水印模板页
        text_layout = QVBoxLayout(self.text_template_tab)
        self.text_template_list = QListWidget()
        text_layout.addWidget(self.text_template_list)
        
        # 文字水印模板按钮
        text_btn_layout = QHBoxLayout()
        self.save_text_btn = QPushButton("保存当前为文字模板")
        self.load_text_btn = QPushButton("加载选中的文字模板")
        self.delete_text_btn = QPushButton("删除选中的文字模板")
        self.set_default_text_btn = QPushButton("设为默认文字模板")
        
        text_btn_layout.addWidget(self.save_text_btn)
        text_btn_layout.addWidget(self.load_text_btn)
        text_btn_layout.addWidget(self.delete_text_btn)
        text_btn_layout.addWidget(self.set_default_text_btn)
        
        text_layout.addLayout(text_btn_layout)
        
        # 图片水印模板页
        image_layout = QVBoxLayout(self.image_template_tab)
        self.image_template_list = QListWidget()
        image_layout.addWidget(self.image_template_list)
        
        # 图片水印模板按钮
        image_btn_layout = QHBoxLayout()
        self.save_image_btn = QPushButton("保存当前为图片模板")
        self.load_image_btn = QPushButton("加载选中的图片模板")
        self.delete_image_btn = QPushButton("删除选中的图片模板")
        self.set_default_image_btn = QPushButton("设为默认图片模板")
        
        image_btn_layout.addWidget(self.save_image_btn)
        image_btn_layout.addWidget(self.load_image_btn)
        image_btn_layout.addWidget(self.delete_image_btn)
        image_btn_layout.addWidget(self.set_default_image_btn)
        
        image_layout.addLayout(image_btn_layout)
        
        template_layout.addWidget(self.tab_widget)
        layout.addWidget(template_group)
        
        # 底部按钮
        bottom_layout = QHBoxLayout()
        
        # 添加弹性空间
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        bottom_layout.addItem(spacer)
        
        # 关闭按钮
        self.close_btn = QPushButton("关闭")
        bottom_layout.addWidget(self.close_btn)
        
        layout.addLayout(bottom_layout)
        
        # 连接信号
        self.load_last_radio.toggled.connect(self.on_startup_option_changed)
        self.save_text_btn.clicked.connect(self.save_text_template)
        self.load_text_btn.clicked.connect(self.load_text_template)
        self.delete_text_btn.clicked.connect(self.delete_text_template)
        self.set_default_text_btn.clicked.connect(self.set_default_text_template)
        
        self.save_image_btn.clicked.connect(self.save_image_template)
        self.load_image_btn.clicked.connect(self.load_image_template)
        self.delete_image_btn.clicked.connect(self.delete_image_template)
        self.set_default_image_btn.clicked.connect(self.set_default_image_template)
        
        self.close_btn.clicked.connect(self.accept)
    
    def load_templates(self):
        """加载模板列表"""
        # 加载文字水印模板
        self.text_template_list.clear()
        text_templates = self.config_manager.get_template_names("text")
        for template_name in text_templates:
            item = QListWidgetItem(template_name)
            # 检查是否是默认模板
            default_template = self.config_manager.get_default_template()
            if default_template and default_template["type"] == "text" and default_template["name"] == template_name:
                item.setText(f"{template_name} (默认)")
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            self.text_template_list.addItem(item)
        
        # 加载图片水印模板
        self.image_template_list.clear()
        image_templates = self.config_manager.get_template_names("image")
        for template_name in image_templates:
            item = QListWidgetItem(template_name)
            # 检查是否是默认模板
            default_template = self.config_manager.get_default_template()
            if default_template and default_template["type"] == "image" and default_template["name"] == template_name:
                item.setText(f"{template_name} (默认)")
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            self.image_template_list.addItem(item)
    
    def on_startup_option_changed(self):
        """启动选项改变时的处理"""
        load_last = self.load_last_radio.isChecked()
        self.config_manager.set_load_last_settings(load_last)
    
    def save_text_template(self):
        """保存文字水印模板"""
        if not self.current_watermark_settings:
            QMessageBox.warning(self, "警告", "没有可保存的水印设置")
            return
        
        template_name, ok = QInputDialog.getText(
            self, "保存模板", "请输入模板名称:", text="新建文字模板"
        )
        
        if ok and template_name:
            # 需要将QColor对象转换为字符串格式，以便JSON序列化
            template_settings = self.current_watermark_settings.copy()
            if isinstance(template_settings.get('color'), QColor):
                template_settings['color'] = template_settings['color'].name()
            
            success = self.config_manager.save_watermark_template(
                "text", template_name, template_settings
            )
            
            if success:
                QMessageBox.information(self, "成功", "模板保存成功")
                self.load_templates()
            else:
                QMessageBox.critical(self, "错误", "模板保存失败")
    
    def save_image_template(self):
        """保存图片水印模板"""
        if not self.current_watermark_settings:
            QMessageBox.warning(self, "警告", "没有可保存的水印设置")
            return
        
        template_name, ok = QInputDialog.getText(
            self, "保存模板", "请输入模板名称:", text="新建图片模板"
        )
        
        if ok and template_name:
            # 需要将QColor对象转换为字符串格式，以便JSON序列化
            template_settings = self.current_watermark_settings.copy()
            if isinstance(template_settings.get('color'), QColor):
                template_settings['color'] = template_settings['color'].name()
            
            success = self.config_manager.save_watermark_template(
                "image", template_name, template_settings
            )
            
            if success:
                QMessageBox.information(self, "成功", "模板保存成功")
                self.load_templates()
            else:
                QMessageBox.critical(self, "错误", "模板保存失败")
    
    def load_text_template(self):
        """加载文字水印模板"""
        current_item = self.text_template_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择一个模板")
            return
        
        template_name = current_item.text().replace(" (默认)", "")
        template_settings = self.config_manager.load_watermark_template("text", template_name)
        
        if template_settings:
            # 发送信号给父窗口，让它加载模板
            if self.parent():
                self.parent().load_watermark_template("text", template_settings)
            QMessageBox.information(self, "成功", "模板加载成功")
        else:
            QMessageBox.critical(self, "错误", "模板加载失败")
    
    def load_image_template(self):
        """加载图片水印模板"""
        current_item = self.image_template_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择一个模板")
            return
        
        template_name = current_item.text().replace(" (默认)", "")
        template_settings = self.config_manager.load_watermark_template("image", template_name)
        
        if template_settings:
            # 发送信号给父窗口，让它加载模板
            if self.parent():
                self.parent().load_watermark_template("image", template_settings)
            QMessageBox.information(self, "成功", "模板加载成功")
        else:
            QMessageBox.critical(self, "错误", "模板加载失败")
    
    def delete_text_template(self):
        """删除文字水印模板"""
        current_item = self.text_template_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择一个模板")
            return
        
        template_name = current_item.text().replace(" (默认)", "")
        
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除模板 '{template_name}' 吗?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.config_manager.delete_watermark_template("text", template_name)
            
            if success:
                QMessageBox.information(self, "成功", "模板删除成功")
                self.load_templates()
            else:
                QMessageBox.critical(self, "错误", "模板删除失败")
    
    def delete_image_template(self):
        """删除图片水印模板"""
        current_item = self.image_template_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择一个模板")
            return
        
        template_name = current_item.text().replace(" (默认)", "")
        
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除模板 '{template_name}' 吗?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.config_manager.delete_watermark_template("image", template_name)
            
            if success:
                QMessageBox.information(self, "成功", "模板删除成功")
                self.load_templates()
            else:
                QMessageBox.critical(self, "错误", "模板删除失败")
    
    def set_default_text_template(self):
        """设置默认文字水印模板"""
        current_item = self.text_template_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择一个模板")
            return
        
        template_name = current_item.text().replace(" (默认)", "")
        success = self.config_manager.set_default_template("text", template_name)
        
        if success:
            QMessageBox.information(self, "成功", "默认模板设置成功")
            self.load_templates()
        else:
            QMessageBox.critical(self, "错误", "默认模板设置失败")
    
    def set_default_image_template(self):
        """设置默认图片水印模板"""
        current_item = self.image_template_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择一个模板")
            return
        
        template_name = current_item.text().replace(" (默认)", "")
        success = self.config_manager.set_default_template("image", template_name)
        
        if success:
            QMessageBox.information(self, "成功", "默认模板设置成功")
            self.load_templates()
        else:
            QMessageBox.critical(self, "错误", "默认模板设置失败")


class StartupSettingsDialog(QDialog):
    """启动设置对话框"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("启动设置")
        self.setMinimumSize(400, 200)
        
        # 主布局
        layout = QVBoxLayout(self)
        
        # 提示信息
        info_label = QLabel("是否为您加载上一次关闭时的水印设置？")
        layout.addWidget(info_label)
        
        # 单选按钮组
        self.button_group = QButtonGroup(self)
        
        self.load_last_radio = QRadioButton("继续上次的设置")
        self.load_default_radio = QRadioButton("加载默认模板")
        self.template_manager_radio = QRadioButton("模板管理")
        
        self.button_group.addButton(self.load_last_radio)
        self.button_group.addButton(self.load_default_radio)
        self.button_group.addButton(self.template_manager_radio)
        
        layout.addWidget(self.load_last_radio)
        layout.addWidget(self.load_default_radio)
        layout.addWidget(self.template_manager_radio)
        
        # 检查是否有上一次关闭时的设置
        last_settings = self.config_manager.get_last_watermark_settings()
        if not last_settings:
            # 如果没有上一次的设置，禁用"继续上次的设置"选项并修改文本
            self.load_last_radio.setEnabled(False)
            self.load_last_radio.setText("继续上次的设置（首次启动程序，无相关记录）")
            # 默认选择"加载默认模板"
            self.load_default_radio.setChecked(True)
        else:
            # 根据当前设置选择单选按钮
            if self.config_manager.get_load_last_settings():
                self.load_last_radio.setChecked(True)
            else:
                self.load_default_radio.setChecked(True)
        
        # 按钮布局
        btn_layout = QHBoxLayout()
        
        self.ok_btn = QPushButton("确定")
        self.cancel_btn = QPushButton("取消")
        
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
        
        # 连接信号
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.template_manager_radio.toggled.connect(self.on_template_manager_selected)
    
    def on_template_manager_selected(self, checked):
        """模板管理选项被选中时的处理"""
        if checked:
            # 打开模板管理对话框
            template_dialog = TemplateManagerDialog(self.config_manager, self.parent())
            template_dialog.exec_()
            # 取消选中模板管理选项
            self.load_last_radio.setChecked(self.config_manager.get_load_last_settings())
    
    def get_selected_option(self):
        """获取选中的选项"""
        if self.load_last_radio.isChecked():
            return "load_last"
        elif self.load_default_radio.isChecked():
            return "load_default"
        else:
            return "template_manager"
    
    def accept(self):
        """确定按钮点击事件"""
        # 保存设置
        load_last = self.load_last_radio.isChecked() and self.load_last_radio.isEnabled()
        self.config_manager.set_load_last_settings(load_last)
        
        super().accept()