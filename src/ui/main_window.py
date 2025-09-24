#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口类 - 实现三栏布局
"""

import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QSplitter, QLabel, QPushButton, QMenuBar, QMenu, 
                             QStatusBar, QAction, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """设置用户界面"""
        # 设置窗口属性
        self.setWindowTitle("Photo Watermark 2")
        self.setMinimumSize(1200, 800)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧面板 - 图片列表
        self.left_panel = self.create_left_panel()
        
        # 中央面板 - 预览区域
        self.center_panel = self.create_center_panel()
        
        # 右侧面板 - 设置面板
        self.right_panel = self.create_right_panel()
        
        # 添加面板到分割器
        splitter.addWidget(self.left_panel)
        splitter.addWidget(self.center_panel)
        splitter.addWidget(self.right_panel)
        
        # 设置分割器比例
        splitter.setSizes([200, 600, 400])
        
        # 添加分割器到主布局
        main_layout.addWidget(splitter)
        
        # 设置菜单栏
        self.setup_menu_bar()
        
        # 设置状态栏
        self.setup_status_bar()
        
    def create_left_panel(self):
        """创建左侧图片列表面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 标题
        title_label = QLabel("图片列表")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin: 10px;")
        layout.addWidget(title_label)
        
        # 导入按钮
        self.import_button = QPushButton("导入图片")
        self.import_button.setMinimumHeight(35)
        layout.addWidget(self.import_button)
        
        # 图片列表区域
        self.image_list_widget = QWidget()
        self.image_list_layout = QVBoxLayout(self.image_list_widget)
        
        # 添加占位文本
        placeholder = QLabel("暂无图片")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("color: #999; font-style: italic;")
        self.image_list_layout.addWidget(placeholder)
        
        layout.addWidget(self.image_list_widget)
        layout.addStretch()
        
        return panel
        
    def create_center_panel(self):
        """创建中央预览面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 标题
        title_label = QLabel("预览区域")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin: 10px;")
        layout.addWidget(title_label)
        
        # 预览区域
        self.preview_widget = QLabel()
        self.preview_widget.setAlignment(Qt.AlignCenter)
        self.preview_widget.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                background-color: #f8f9fa;
                min-height: 400px;
            }
        """)
        self.preview_widget.setText("请导入图片进行预览")
        layout.addWidget(self.preview_widget)
        
        # 预览控制按钮
        control_layout = QHBoxLayout()
        
        self.prev_button = QPushButton("上一张")
        self.next_button = QPushButton("下一张")
        self.zoom_in_button = QPushButton("视图放大")
        self.zoom_out_button = QPushButton("视图缩小")
        self.fit_button = QPushButton("适应窗口")
        
        control_layout.addWidget(self.prev_button)
        control_layout.addWidget(self.next_button)
        control_layout.addWidget(self.zoom_in_button)
        control_layout.addWidget(self.zoom_out_button)
        control_layout.addWidget(self.fit_button)
        
        layout.addLayout(control_layout)
        
        return panel
        
    def create_right_panel(self):
        """创建右侧设置面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 标题
        title_label = QLabel("水印设置")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin: 10px;")
        layout.addWidget(title_label)
        
        # 水印类型选择
        watermark_type_layout = QHBoxLayout()
        watermark_type_layout.addWidget(QLabel("水印类型:"))
        
        self.text_watermark_button = QPushButton("文本水印")
        self.image_watermark_button = QPushButton("图片水印")
        
        watermark_type_layout.addWidget(self.text_watermark_button)
        watermark_type_layout.addWidget(self.image_watermark_button)
        watermark_type_layout.addStretch()
        
        layout.addLayout(watermark_type_layout)
        
        # 设置区域占位
        settings_placeholder = QLabel("水印设置区域")
        settings_placeholder.setAlignment(Qt.AlignCenter)
        settings_placeholder.setStyleSheet("""
            QLabel {
                border: 1px solid #ddd;
                background-color: #f0f0f0;
                min-height: 300px;
                color: #666;
            }
        """)
        layout.addWidget(settings_placeholder)
        
        # 操作按钮
        action_layout = QHBoxLayout()
        
        self.preview_button = QPushButton("预览效果")
        self.apply_button = QPushButton("应用水印")
        self.export_button = QPushButton("导出图片")
        
        action_layout.addWidget(self.preview_button)
        action_layout.addWidget(self.apply_button)
        action_layout.addWidget(self.export_button)
        
        layout.addLayout(action_layout)
        layout.addStretch()
        
        return panel
        
    def setup_menu_bar(self):
        """设置菜单栏"""
        menu_bar = self.menuBar()
        
        # 文件菜单
        file_menu = menu_bar.addMenu("文件")
        
        self.open_action = QAction("打开图片", self)
        self.open_action.setShortcut("Ctrl+O")
        file_menu.addAction(self.open_action)
        
        self.open_folder_action = QAction("打开文件夹", self)
        self.open_folder_action.setShortcut("Ctrl+Shift+O")
        file_menu.addAction(self.open_folder_action)
        
        file_menu.addSeparator()
        
        self.export_action = QAction("导出图片", self)
        self.export_action.setShortcut("Ctrl+E")
        file_menu.addAction(self.export_action)
        
        file_menu.addSeparator()
        
        self.exit_action = QAction("退出", self)
        self.exit_action.setShortcut("Ctrl+Q")
        file_menu.addAction(self.exit_action)
        
        # 编辑菜单
        edit_menu = menu_bar.addMenu("编辑")
        
        self.undo_action = QAction("撤销", self)
        self.undo_action.setShortcut("Ctrl+Z")
        edit_menu.addAction(self.undo_action)
        
        self.redo_action = QAction("重做", self)
        self.redo_action.setShortcut("Ctrl+Y")
        edit_menu.addAction(self.redo_action)
        
        # 视图菜单
        view_menu = menu_bar.addMenu("视图")
        
        self.zoom_in_action = QAction("视图放大", self)
        self.zoom_in_action.setShortcut("Ctrl++")
        view_menu.addAction(self.zoom_in_action)
        
        self.zoom_out_action = QAction("视图缩小", self)
        self.zoom_out_action.setShortcut("Ctrl+-")
        view_menu.addAction(self.zoom_out_action)
        
        self.fit_action = QAction("适应窗口", self)
        self.fit_action.setShortcut("Ctrl+0")
        view_menu.addAction(self.fit_action)
        
        # 帮助菜单
        help_menu = menu_bar.addMenu("帮助")
        
        self.about_action = QAction("关于", self)
        help_menu.addAction(self.about_action)
        
    def setup_status_bar(self):
        """设置状态栏"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # 状态信息
        self.status_label = QLabel("就绪")
        status_bar.addWidget(self.status_label)
        
        # 进度信息
        self.progress_label = QLabel("")
        status_bar.addPermanentWidget(self.progress_label)
        
    def setup_connections(self):
        """设置信号连接"""
        # 导入按钮
        self.import_button.clicked.connect(self.import_images)
        
        # 菜单动作
        self.open_action.triggered.connect(self.import_images)
        self.exit_action.triggered.connect(self.close)
        self.about_action.triggered.connect(self.show_about)
        
    def import_images(self):
        """导入图片"""
        file_dialog = QFileDialog()
        file_paths, _ = file_dialog.getOpenFileNames(
            self, 
            "选择图片文件", 
            "", 
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.tiff *.tif)"
        )
        
        if file_paths:
            self.status_label.setText(f"已选择 {len(file_paths)} 张图片")
            QMessageBox.information(self, "导入成功", f"成功导入 {len(file_paths)} 张图片")
        
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于 Photo Watermark 2", 
                         "Photo Watermark 2\n\n"
                         "一个功能强大的图片水印软件\n"
                         "支持文本水印和图片水印\n"
                         "版本 1.0.0")


if __name__ == "__main__":
    # 测试代码
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())