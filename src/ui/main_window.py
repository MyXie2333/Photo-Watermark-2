#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口类 - 实现三栏布局
"""

import os
import logging
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QSplitter, QLabel, QPushButton, QMenuBar, QMenu, 
                             QStatusBar, QAction, QFileDialog, QMessageBox, QScrollArea, QDialog,
                             QProgressDialog, QCheckBox, QApplication)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QDragEnterEvent, QDropEvent, QImage, QColor, QPainter, QPen, QFont
from PIL import Image as PILImage

# 导入自定义模块
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from image_manager import ImageManager
    from ui.image_list_widget import ImageListWidget
    from watermark_renderer import WatermarkRenderer
    from config_manager import get_config_manager
    from ui.text_watermark_widget import TextWatermarkWidget
    from ui.image_watermark_widget import ImageWatermarkWidget
    from watermark_drag_manager import WatermarkDragManager
    from ui.template_manager_dialog import TemplateManagerDialog, StartupSettingsDialog
    from ui.export_dialog import ExportDialog, BatchExportDialog
except ImportError as e:
    print(f"导入错误: {e}")
    print("当前Python路径:", sys.path)
    raise


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化图片管理器
        self.image_manager = ImageManager()
        
        # 初始化配置管理器
        self.config_manager = get_config_manager()
        
        # 初始化水印渲染器
        self.watermark_renderer = WatermarkRenderer(self)
        
        # 当前水印设置（用于UI显示和临时预览）
        self.current_watermark_settings = {}
        
        # 当前模板设置（用于在导入新图片时自动应用）
        self._current_template_type = None
        self._current_template_settings = None
        
        # 初始化缩放相关变量
        self.current_scale = 1.0
        self.compression_scale = 1.0  # 添加压缩比例属性
        
        # 初始化水印类型
        self.watermark_type = "text"  # 默认文本水印
        self.text_watermark_widget = None
        self.image_watermark_widget = None
        self.min_scale = 0.1
        self.max_scale = 5.0
        self.scale_step = 0.1
        
        # 初始化原始图片变量
        self.original_pixmap = None
        
        # 预览更新优化：缓存上一次的预览设置
        self.last_preview_settings = None
        self.last_preview_image = None
        
        # 显示辅助线的标志，默认为True（开）
        self.show_guidelines = True
        
        self.setup_ui()
        
        # 启用窗口级别的拖放功能
        self.setAcceptDrops(True)
        
        # 初始化水印拖拽管理器
        self.drag_manager = WatermarkDragManager(self.preview_widget)
        self.drag_manager.set_watermark_widgets(self.text_watermark_widget, self.image_watermark_widget)
        
        # 设置水印设置回调函数
        self.drag_manager.set_watermark_settings_callback(self._get_current_watermark_settings)
        
        self.setup_connections()
        
        # 显示启动设置对话框
        self.show_startup_settings()
        
    def dragEnterEvent(self, event):
        """窗口级别的拖拽进入事件处理"""
        # 检查拖拽内容是否为文件
        if event.mimeData().hasUrls():
            # 检查文件是否为支持的图片格式
            urls = event.mimeData().urls()
            for url in urls:
                file_path = url.toLocalFile()
                if self.is_supported_image(file_path):
                    event.acceptProposedAction()
                    # 设置拖拽样式
                    self.preview_widget.setProperty("dragEnabled", "true")
                    self.preview_widget.style().unpolish(self.preview_widget)
                    self.preview_widget.style().polish(self.preview_widget)
                    return
        
        event.ignore()
        
    def dropEvent(self, event):
        """窗口级别的拖拽释放事件处理"""
        # 重置拖拽样式
        self.preview_widget.setProperty("dragEnabled", "false")
        self.preview_widget.style().unpolish(self.preview_widget)
        self.preview_widget.style().polish(self.preview_widget)
        
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            file_paths = []
            
            # 收集所有支持的图片文件
            for url in urls:
                file_path = url.toLocalFile()
                if self.is_supported_image(file_path):
                    file_paths.append(file_path)
            
            if file_paths:
                print(f"拖拽导入图片: {file_paths}")
                # 创建进度对话框
                progress_dialog = QProgressDialog("正在导入图片并设置模板...", "取消", 0, len(file_paths) + 1, self)
                progress_dialog.setWindowTitle("请稍等，正在导入图片...")
                progress_dialog.setWindowModality(Qt.WindowModal)
                progress_dialog.show()
                
                # 更新进度
                progress_dialog.setValue(0)
                progress_dialog.setLabelText("正在导入图片...")
                QApplication.processEvents()
                
                result = self.image_manager.load_multiple_images(file_paths)
                
                # 更新进度
                progress_dialog.setValue(len(file_paths))
                progress_dialog.setLabelText("正在设置模板...")
                QApplication.processEvents()
                
                if result is True:
                    # 成功导入新图片
                    count = self.image_manager.get_image_count()
                    self.status_label.setText(f"已导入 {len(file_paths)} 张图片，当前共 {count} 张")
                elif isinstance(result, dict) and result.get("status") == "has_duplicates":
                    # 有重复文件
                    duplicates = result.get("duplicates", [])
                    valid_count = result.get("valid_count", 0)
                    
                    # 显示重复文件警告
                    duplicate_names = [os.path.basename(path) for path in duplicates]
                    duplicate_list = "\n".join([f"• {name}" for name in duplicate_names])
                    
                    msg = QMessageBox(self)
                    msg.setIcon(QMessageBox.Warning)
                    msg.setWindowTitle("重复文件检测")
                    msg.setText(f"检测到 {len(duplicates)} 个重复文件，已跳过导入。")
                    msg.setInformativeText(f"重复文件列表：\n{duplicate_list}")
                    
                    if valid_count > 0:
                        msg.setDetailedText(f"已成功导入 {valid_count} 个新文件。")
                    
                    msg.exec_()
                    
                    if valid_count > 0:
                        count = self.image_manager.get_image_count()
                        self.status_label.setText(f"已导入 {valid_count} 张新图片，跳过 {len(duplicates)} 张重复图片，当前共 {count} 张")
                    else:
                        self.status_label.setText(f"所有拖拽的图片都已存在，未导入新图片")
                else:
                    QMessageBox.warning(self, "导入失败", "没有找到有效的图片文件")
                
                # 完成进度条
                progress_dialog.setValue(len(file_paths) + 1)
            else:
                QMessageBox.warning(self, "导入失败", "拖拽的文件不是支持的图片格式")
        
        event.acceptProposedAction()
        
    def _get_current_watermark_settings(self):
        """获取当前水印设置的内部方法，用于WatermarkDragManager的回调"""
        current_image_path = self.image_manager.get_current_image_path()
        if current_image_path:
            return self.image_manager.get_current_watermark_settings()
        return {}
        
    def on_show_guidelines_changed(self, state):
        """处理显示辅助线复选框状态变化事件"""
        self.show_guidelines = state == Qt.Checked
        # 重新渲染预览，使更改生效
        self.update_preview_with_watermark()
        
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
        
        # 批量导入按钮
        self.import_folder_button = QPushButton("导入文件夹")
        self.import_folder_button.setMinimumHeight(35)
        layout.addWidget(self.import_folder_button)
        
        # 导出按钮
        self.export_current_button = QPushButton("导出此图片")
        self.export_current_button.setMinimumHeight(35)
        layout.addWidget(self.export_current_button)
        
        self.export_all_button = QPushButton("全部导出")
        self.export_all_button.setMinimumHeight(35)
        layout.addWidget(self.export_all_button)
        
        # 模板按钮
        self.template_button = QPushButton("模板")
        self.template_button.setMinimumHeight(35)
        layout.addWidget(self.template_button)
        
        # 图片列表区域
        self.image_list_widget = ImageListWidget()
        layout.addWidget(self.image_list_widget)
        
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
            }
            QLabel[dragEnabled="true"] {
                border: 2px dashed #007acc;
                background-color: #e6f3ff;
            }
        """)
        self.preview_widget.setText("请导入图片进行预览\n\n支持拖拽图片文件到此区域")
        
        # 启用拖拽功能（现在在窗口级别处理）
        # self.preview_widget.setAcceptDrops(True)
        # self.preview_widget.dragEnterEvent = self.dragEnterEvent
        # self.preview_widget.dropEvent = self.dropEvent
        
        # 安装事件过滤器以捕获鼠标事件用于水印拖拽
        # 注意：鼠标事件现在由WatermarkDragManager处理
        self.preview_widget.setMouseTracking(True)
        
        # 预览滚动区域
        self.preview_scroll_area = QScrollArea()
        self.preview_scroll_area.setWidgetResizable(True)
        # 明确设置滚动条策略，确保在内容超出时显示滚动条
        self.preview_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.preview_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.preview_scroll_area.setWidget(self.preview_widget)
        layout.addWidget(self.preview_scroll_area)
        
        # 添加预览提示文本
        self.preview_hint_label = QLabel("鼠标拖动预览图中任意区域调整水印位置，试图放大后拖动预览框滑条调整预览可见区域")
        self.preview_hint_label.setAlignment(Qt.AlignCenter)
        self.preview_hint_label.setStyleSheet("font-size: 10px; color: #333; margin: 5px;")
        layout.addWidget(self.preview_hint_label)

        # 预览控制按钮
        control_layout = QHBoxLayout()
        
        self.prev_button = QPushButton("上一张")
        self.next_button = QPushButton("下一张")
        self.zoom_in_button = QPushButton("视图放大")
        self.zoom_out_button = QPushButton("视图缩小")
        self.fit_button = QPushButton("适应窗口")
        
        # 添加显示辅助线复选框
        self.show_guidelines_checkbox = QCheckBox("显示辅助线")
        self.show_guidelines_checkbox.setChecked(self.show_guidelines)
        self.show_guidelines_checkbox.stateChanged.connect(self.on_show_guidelines_changed)
        
        control_layout.addWidget(self.prev_button)
        control_layout.addWidget(self.next_button)
        control_layout.addWidget(self.zoom_in_button)
        control_layout.addWidget(self.zoom_out_button)
        control_layout.addWidget(self.fit_button)
        control_layout.addWidget(self.show_guidelines_checkbox)
        
        layout.addLayout(control_layout)
        
        # 缩放比例显示（已注释）
        # scale_layout = QHBoxLayout()
        # scale_layout.addStretch()
        
        # self.scale_label = QLabel("缩放比例: 100%")
        # self.scale_label.setStyleSheet("font-size: 12px; color: #666; margin: 5px;")
        # scale_layout.addWidget(self.scale_label)
        
        # scale_layout.addStretch()
        # layout.addLayout(scale_layout)
        
        # 统一显示原图尺寸、水印坐标和预览缩放比例
        info_layout = QHBoxLayout()
        info_layout.addStretch()
        
        self.unified_info_label = QLabel("原图尺寸: 0x0 | 水印坐标: (0, 0) | 预览缩放比例: 1.00")
        self.unified_info_label.setStyleSheet("font-size: 12px; color: #666; margin: 5px;")
        info_layout.addWidget(self.unified_info_label)
        
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # 添加水印位置警告标签
        self.watermark_warning_label = QLabel("注意：水印将超出图片边界！")
        self.watermark_warning_label.setStyleSheet("color: red; font-weight: bold; margin: 5px;")
        self.watermark_warning_label.setVisible(False)  # 默认隐藏
        layout.addWidget(self.watermark_warning_label)
        
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
        
        # 设置默认选中状态
        self.text_watermark_button.setChecked(True)
        self.text_watermark_button.setCheckable(True)
        self.image_watermark_button.setCheckable(True)
        
        # 连接信号
        self.text_watermark_button.clicked.connect(lambda: self.switch_watermark_type("text"))
        self.image_watermark_button.clicked.connect(lambda: self.switch_watermark_type("image"))
        
        watermark_type_layout.addWidget(self.text_watermark_button)
        watermark_type_layout.addWidget(self.image_watermark_button)
        watermark_type_layout.addStretch()
        
        layout.addLayout(watermark_type_layout)
        
        # 字体切换提示标签
        self.font_switch_label = QLabel()
        self.font_switch_label.setStyleSheet("color: red; font-size: 12px; margin: 5px;")
        self.font_switch_label.setVisible(False)
        layout.addWidget(self.font_switch_label)
        
        # 文本水印设置组件
        self.text_watermark_widget = TextWatermarkWidget()
        layout.addWidget(self.text_watermark_widget)
        
        # 图片水印设置组件
        self.image_watermark_widget = ImageWatermarkWidget()
        self.image_watermark_widget.hide()  # 默认隐藏
        layout.addWidget(self.image_watermark_widget)
        
        # 操作按钮
        action_layout = QHBoxLayout()
        layout.addLayout(action_layout)
        
        layout.addStretch()
        
        return panel
        
    def setup_menu_bar(self):
        """设置菜单栏"""
        menu_bar = self.menuBar()
        
        # 导入菜单
        import_menu = menu_bar.addMenu("导入")
        
        self.import_images_action = QAction("导入图片", self)
        self.import_images_action.setShortcut("Ctrl+I")
        import_menu.addAction(self.import_images_action)
        
        self.import_folder_action = QAction("导入文件夹", self)
        self.import_folder_action.setShortcut("Ctrl+Shift+I")
        import_menu.addAction(self.import_folder_action)
        
        # 导出菜单
        export_menu = menu_bar.addMenu("导出")
        
        self.export_current_action = QAction("导出此图片", self)
        self.export_current_action.setShortcut("Ctrl+E")
        export_menu.addAction(self.export_current_action)
        
        self.export_all_action = QAction("全部导出", self)
        self.export_all_action.setShortcut("Ctrl+Shift+E")
        export_menu.addAction(self.export_all_action)
        
        # 模板菜单
        template_menu = menu_bar.addMenu("模板")
        
        self.template_manager_action = QAction("模板管理", self)
        self.template_manager_action.setShortcut("Ctrl+T")
        template_menu.addAction(self.template_manager_action)
        
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
        self.import_folder_button.clicked.connect(self.import_folder)
        self.export_current_button.clicked.connect(self.export_image)
        self.export_all_button.clicked.connect(self.export_all_images)
        self.template_button.clicked.connect(self.show_template_manager)
        
        # 预览控制按钮
        self.prev_button.clicked.connect(self.prev_image)
        self.next_button.clicked.connect(self.next_image)
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.zoom_out_button.clicked.connect(self.zoom_out)
        self.fit_button.clicked.connect(self.fit_to_window)
        
        # 图片列表信号
        self.image_list_widget.image_selected.connect(self.on_image_selected)
        
        # 连接信号
        self.image_manager.images_loaded.connect(self.on_images_loaded)
        self.image_manager.image_changed.connect(self.on_image_changed)
        
        # 跟踪当前图片列表，用于检测新图片添加
        self.current_image_paths = []
        
        # 水印设置信号连接
        self.text_watermark_widget.watermark_changed.connect(self.on_watermark_changed)
        self.text_watermark_widget.font_switch_notification.connect(self.on_font_switch_notification)
        
        # 图片水印设置信号连接
        if self.image_watermark_widget:
            self.image_watermark_widget.watermark_changed.connect(self.on_watermark_changed)
        
        # 水印拖拽管理器回调函数设置
        self.drag_manager.set_position_changed_callback(self.on_watermark_position_changed)
        
        # 菜单动作
        self.import_images_action.triggered.connect(self.import_images)
        self.import_folder_action.triggered.connect(self.import_folder)
        self.export_current_action.triggered.connect(self.export_image)
        self.export_all_action.triggered.connect(self.export_all_images)
        self.template_manager_action.triggered.connect(self.show_template_manager)
        
    def switch_watermark_type(self, watermark_type):
        """切换水印类型"""
        # 更新水印类型和按钮状态
        self.watermark_type = watermark_type
        
        # 通知拖拽管理器水印类型变化
        self.drag_manager.set_watermark_type(watermark_type)
        
        if watermark_type == "text":
            self.text_watermark_button.setChecked(True)
            self.image_watermark_button.setChecked(False)
            self.text_watermark_widget.show()
            self.image_watermark_widget.hide()
        else:
            self.text_watermark_button.setChecked(False)
            self.image_watermark_button.setChecked(True)
            self.text_watermark_widget.hide()
            self.image_watermark_widget.show()
            
        # 更新当前水印设置
        self.update_watermark_settings_from_current_widget()
        
        # 更新预览
        current_image_path = self.image_manager.get_current_image_path()
        if current_image_path:
            self.update_preview_with_watermark()
    
    def update_watermark_settings_from_current_widget(self):
        """从当前选中的水印组件获取水印设置"""
        if self.watermark_type == "text" and self.text_watermark_widget:
            watermark_settings = self.text_watermark_widget.get_watermark_settings()
            watermark_settings['watermark_type'] = 'text'
        elif self.watermark_type == "image" and self.image_watermark_widget:
            watermark_settings = self.image_watermark_widget.get_watermark_settings()
            watermark_settings['watermark_type'] = 'image'
        else:
            watermark_settings = {}
        
        self.current_watermark_settings = watermark_settings
        
        # 更新全局配置
        current_image_path = self.image_manager.get_current_image_path()
        if current_image_path:
            self.image_manager.set_watermark_settings(current_image_path, watermark_settings)
            
            # 需要将QColor对象转换为字符串格式，以便JSON序列化
            config_watermark_settings = watermark_settings.copy()
            if isinstance(config_watermark_settings.get('color'), QColor):
                config_watermark_settings['color'] = config_watermark_settings['color'].name()
            
            # 处理描边颜色
            if isinstance(config_watermark_settings.get('outline_color'), QColor):
                config_watermark_settings['outline_color'] = config_watermark_settings['outline_color'].name()
            
            # 处理阴影颜色
            if isinstance(config_watermark_settings.get('shadow_color'), QColor):
                config_watermark_settings['shadow_color'] = config_watermark_settings['shadow_color'].name()
            
            self.config_manager.set_watermark_defaults(config_watermark_settings)
    
    def on_watermark_changed(self):
        """水印设置发生变化"""
        self.update_watermark_settings_from_current_widget()
        
        # 重置缓存，确保强制重新生成预览
        self.last_preview_settings = None
        self.last_preview_image = None
        
        # 更新预览
        current_image_path = self.image_manager.get_current_image_path()
        if current_image_path:
            self.update_preview_with_watermark()
            
            # 获取当前水印设置并保存到配置文件
            current_settings = self.image_manager.get_current_watermark_settings()
            if current_settings:
                # 添加水印类型信息
                current_settings['type'] = self.watermark_type
                self.config_manager.set_last_watermark_settings(current_settings)
            
    def on_watermark_position_changed(self, x, y):
        """处理水印位置变化信号"""
        print(f"[DEBUG] MainWindow.on_watermark_position_changed: 接收到位置变化回调，坐标=({x}, {y})")
        # 获取当前图片路径
        current_image_path = self.image_manager.get_current_image_path()
        if current_image_path:
            # 获取当前水印设置
            current_watermark_settings = self.image_manager.get_watermark_settings(current_image_path)
            
            # 使用update_position函数统一处理position更新
            print(f"[DEBUG] MainWindow.on_watermark_position_changed: 调用函数: self.update_position")
            self.update_position((x, y), current_watermark_settings)
            
    def on_font_switch_notification(self, message):
        """处理字体切换提示信号"""
        # 显示字体切换提示
        self.font_switch_label.setText(message)
        self.font_switch_label.show()
        
        # 5秒后自动隐藏提示
        QTimer.singleShot(5000, self.font_switch_label.hide)
            
    def update_preview_with_watermark(self):
        """统一的图片预览方法 - 使用当前图片的水印设置进行预览"""
        try:
            # 获取当前图片路径
            current_image_path = self.image_manager.get_current_image_path()
            
            if not current_image_path:
                self.preview_widget.setText("请先导入图片")
                return
            
            # 加载原始图片并保存
            self.original_pixmap = QPixmap(current_image_path)
            if self.original_pixmap.isNull():
                self.preview_widget.setText("无法加载图片")
                return
                
            # 更新水印拖拽管理器的原始图片
            self.drag_manager.set_original_pixmap(self.original_pixmap)
            
            # 检查当前图片是否有保存的缩放比例
            saved_scale = self.image_manager.get_scale_settings(current_image_path)
            if saved_scale is not None:
                # 使用保存的缩放比例
                self.current_scale = saved_scale
            else:
                # 如果没有保存的比例，计算适应窗口比例并保存
                fit_scale = self.calculate_fit_scale()
                if fit_scale != self.current_scale:
                    self.current_scale = fit_scale
                    print(f"首次预览，适应窗口显示，缩放比例: {fit_scale:.2f}")
                    # 保存适应窗口的比例作为初始值
                    self.image_manager.set_scale_settings(current_image_path, fit_scale)
                    
                    # 首次预览非空白图片时，触发中心位置按钮点击
                    if self.image_watermark_widget and not self.original_pixmap.isNull():
                        # 查找中心位置按钮并触发点击
                        for btn in self.image_watermark_widget.position_buttons:
                            if btn.property("position") == (0.5, 0.5):
                                # 确保在UI线程中执行，连续发送两次点击信号
                                btn.clicked.emit(True)
                                print("首次预览，自动设置水印位置为中心 - 第一次点击")
                                # 短暂延迟后再次发送点击信号
                                QTimer.singleShot(10, lambda: btn.clicked.emit(True))
                                print("首次预览，自动设置水印位置为中心 - 第二次点击")
                                # 重置缓存标志，确保强制重新生成预览
                                self.last_preview_settings = None
                                break
            
            # 获取当前图片的水印设置
            current_watermark_settings = self.image_manager.get_current_watermark_settings()
            
            # 创建当前预览设置的哈希键，用于比较是否需要重新渲染
            preview_key = {
                'image_path': current_image_path,
                'scale': self.current_scale,
                'watermark_text': current_watermark_settings.get('text', ''),
                'watermark_font': current_watermark_settings.get('font_family', ''),
                'watermark_size': current_watermark_settings.get('font_size', 0),
                'watermark_color': current_watermark_settings.get('color', QColor(255, 255, 255, 255)).name() if isinstance(current_watermark_settings.get('color'), QColor) else current_watermark_settings.get('color', '#ffffff'),
                'watermark_position': current_watermark_settings.get('position', ''),
                'watermark_x': current_watermark_settings.get('watermark_x', 0),
                'watermark_y': current_watermark_settings.get('watermark_y', 0),
                'watermark_rotation': current_watermark_settings.get('rotation', 0),
                'watermark_opacity': current_watermark_settings.get('opacity', 100),
                'watermark_bold': current_watermark_settings.get('bold', False),
                'watermark_italic': current_watermark_settings.get('italic', False),
                'watermark_underline': current_watermark_settings.get('underline', False),
                'watermark_stroke': current_watermark_settings.get('stroke', False),
                'watermark_stroke_color': current_watermark_settings.get('stroke_color', QColor(0, 0, 0, 255)).name() if isinstance(current_watermark_settings.get('stroke_color'), QColor) else current_watermark_settings.get('stroke_color', '#000000'),
                'watermark_stroke_width': current_watermark_settings.get('stroke_width', 1),
                'watermark_shadow': current_watermark_settings.get('shadow', False),
                'watermark_shadow_color': current_watermark_settings.get('shadow_color', QColor(0, 0, 0, 128)).name() if isinstance(current_watermark_settings.get('shadow_color'), QColor) else current_watermark_settings.get('shadow_color', '#00000080'),
                'watermark_shadow_offset_x': current_watermark_settings.get('shadow_offset_x', 2),
                'watermark_shadow_offset_y': current_watermark_settings.get('shadow_offset_y', 2),
                'watermark_shadow_blur': current_watermark_settings.get('shadow_blur', 3)
            }
            
            # 检查是否与上一次预览设置相同
            if self.last_preview_settings == preview_key and self.last_preview_image is not None:
                print("[DEBUG] 使用缓存的预览图像")
                pixmap = self.last_preview_image
            else:
                print("[DEBUG] 重新生成预览图像")
                # 不管是否有水印文本，都统一使用水印预览流程
                # 如果没有水印文本，水印设置中的text为空，预览图将初始化为原始图片
                preview_result = self.watermark_renderer.preview_watermark(
                    current_image_path, 
                    current_watermark_settings,
                    preview_size=None  # 使用原始图片尺寸
                )
                
                # 解析返回结果
                if isinstance(preview_result, tuple):
                    preview_image, ratio_info = preview_result
                    # 保存比例信息，用于拖拽计算
                    self.preview_ratio_info = ratio_info
                    
                    # 输出原图尺寸、压缩比例和压缩图尺寸
                    if ratio_info:
                        original_width = ratio_info.get('original_width', 0)
                        original_height = ratio_info.get('original_height', 0)
                        compression_scale = ratio_info.get('scale_factor', 1.0)
                        # 更新MainWindow类的compression_scale属性
                        self.compression_scale = compression_scale
                        preview_width = ratio_info.get('preview_width', 0)
                        preview_height = ratio_info.get('preview_height', 0)
                        print(f"[DEBUG] 原图尺寸: {original_width}x{original_height}")
                        # print(f"[DEBUG] 压缩比例: {compression_scale:.4f}")
                        print(f"[DEBUG] 压缩图尺寸: {preview_width}x{preview_height}")
                        
                        # 传递原图尺寸给text_watermark_widget和image_watermark_widget
                        self.text_watermark_widget.set_original_dimensions(original_width, original_height)
                        if self.image_watermark_widget:
                            self.image_watermark_widget.set_original_dimensions(original_width, original_height)
                        
                        # 传递压缩比例给text_watermark_widget和image_watermark_widget
                        self.text_watermark_widget.set_compression_scale(compression_scale)
                        if self.image_watermark_widget:
                            self.image_watermark_widget.set_compression_scale(compression_scale)
                        
                        # 传递压缩比例给watermark_renderer
                        self.watermark_renderer.set_compression_scale(compression_scale)
                else:
                    # 兼容旧版本返回格式
                    preview_image = preview_result
                    self.preview_ratio_info = None
                
                # 转换为QPixmap - 使用更可靠的方法
                # 先将PIL Image转换为RGB模式，然后转换为bytes，再创建QImage
                if preview_image.mode != 'RGB':
                    preview_image = preview_image.convert('RGB')
                
                # 将PIL Image转换为bytes
                import io
                img_byte_arr = io.BytesIO()
                preview_image.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                
                # 从bytes创建QImage，然后转换为QPixmap
                qimage = QImage()
                qimage.loadFromData(img_byte_arr)
                pixmap = QPixmap.fromImage(qimage)
                
                # 缓存预览图像和设置
                self.last_preview_image = pixmap.copy()
                self.last_preview_settings = preview_key.copy()
            
            # 对水印预览图片应用缩放比例 - 基于原始图片尺寸计算
            original_width = self.original_pixmap.width()
            original_height = self.original_pixmap.height()
            
            if self.current_scale != 1.0:
                # 使用原始图片尺寸计算缩放后的尺寸
                scaled_width = int(original_width * self.current_scale)
                scaled_height = int(original_height * self.current_scale)
                
                # 缩放水印预览图片到目标尺寸
                pixmap = pixmap.scaled(scaled_width, scaled_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # 根据设置决定是否绘制坐标格点
            if self.show_guidelines:
                pixmap = self.draw_coordinate_grid(pixmap)
            
            self.preview_widget.setPixmap(pixmap)
            
            # 更新缩放比例显示
            self.update_scale_display()
            
            # 更新水印坐标显示
            self.update_watermark_coordinates()
            
            # 更新图片信息显示
            self.update_image_info_display()
            
            # 检查水印位置是否超出边界
            if 'original_width' in locals() and 'original_height' in locals():
                self.check_watermark_position(current_watermark_settings, original_width, original_height)
            
        except Exception as e:
            print(f"更新预览失败: {e}")
            # 显示错误信息
            self.preview_widget.setText(f"预览失败: {str(e)}")
            
    def draw_coordinate_grid(self, pixmap):
        """在预览图片上绘制坐标格点"""
        # 创建一个新的QPainter对象来绘制格点
        painter = QPainter(pixmap)
        painter.setPen(QPen(QColor(200, 200, 200, 128), 1, Qt.DotLine))
        
        # 获取图片尺寸
        width = pixmap.width()
        height = pixmap.height()
        
        # 获取原始图片尺寸
        original_width = self.original_pixmap.width()
        original_height = self.original_pixmap.height()
        
        # 设置格点间距（根据原始图片大小调整）
        grid_spacing = 50  # 默认间距
        if original_width > 2000 or original_height > 2000:
            grid_spacing = 200
        elif original_width > 1000 or original_height > 1000:
            grid_spacing = 100
        
        # 计算预览图上的格点间距
        preview_grid_spacing_x = int(grid_spacing * width / original_width)
        preview_grid_spacing_y = int(grid_spacing * height / original_height)
        
        # 绘制垂直线
        for x in range(0, width, preview_grid_spacing_x):
            painter.drawLine(x, 0, x, height)
        
        # 绘制水平线
        for y in range(0, height, preview_grid_spacing_y):
            painter.drawLine(0, y, width, y)
        
        # 绘制坐标轴（如果图片中心可见）
        center_x = width // 2
        center_y = height // 2
        
        # 绘制中心十字线（使用更明显的颜色）
        painter.setPen(QPen(QColor(100, 100, 255, 128), 1, Qt.DashLine))
        painter.drawLine(center_x, 0, center_x, height)
        painter.drawLine(0, center_y, width, center_y)
        
        # 绘制坐标标记（每格点间距标记一次）
        painter.setPen(QPen(QColor(50, 50, 50, 200), 1))
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        
        # X轴标记
        for x in range(0, width, preview_grid_spacing_x):
            if x > 0:  # 不在0点标记
                # 计算在原始图片上的坐标
                original_x = int(x * original_width / width)
                painter.drawText(x, height - 5, str(original_x))
        
        # Y轴标记
        for y in range(0, height, preview_grid_spacing_y):
            if y > 0:  # 不在0点标记
                # 计算在原始图片上的坐标
                original_y = int(y * original_height / height)
                painter.drawText(5, y, str(original_y))
        
        # 结束绘制
        painter.end()
        
        return pixmap
            
    def _update_preview_based_on_watermark(self):
        """根据水印设置更新预览"""
        # 现在所有预览都使用统一的update_preview_with_watermark方法
        self.update_preview_with_watermark()
        
    def import_images(self):
        """导入单张或多张图片"""
        file_dialog = QFileDialog()
        file_paths, _ = file_dialog.getOpenFileNames(
            self, 
            "选择图片文件", 
            "", 
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.tiff *.tif)"
        )
        
        if file_paths:
            # 创建进度对话框
            progress_dialog = QProgressDialog("正在导入图片并设置模板...", "取消", 0, len(file_paths) + 1, self)
            progress_dialog.setWindowTitle("请稍等，正在导入图片...")
            progress_dialog.setWindowModality(Qt.WindowModal)
            progress_dialog.show()
            
            # 更新进度
            progress_dialog.setValue(0)
            progress_dialog.setLabelText("正在导入图片...")
            QApplication.processEvents()
            
            result = self.image_manager.load_multiple_images(file_paths)
            
            # 更新进度
            progress_dialog.setValue(len(file_paths))
            progress_dialog.setLabelText("正在设置模板...")
            QApplication.processEvents()
            
            # 处理导入结果
            success = False
            has_duplicates = False
            duplicates = []
            valid_count = 0
            
            if result is True:
                # 成功导入新图片
                success = True
            elif isinstance(result, dict) and result.get("status") == "has_duplicates":
                # 有重复文件
                has_duplicates = True
                duplicates = result.get("duplicates", [])
                valid_count = result.get("valid_count", 0)
                success = result.get("success", False)
            
            # 显示重复文件警告（如果有）
            if has_duplicates:
                # 显示重复文件警告
                duplicate_names = [os.path.basename(path) for path in duplicates]
                duplicate_list = "\n".join([f"• {name}" for name in duplicate_names])
                
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("重复文件检测")
                msg.setText(f"检测到 {len(duplicates)} 个重复文件，已跳过导入。")
                msg.setInformativeText(f"重复文件列表：\n{duplicate_list}")
                
                if valid_count > 0:
                    msg.setDetailedText(f"已成功导入 {valid_count} 个新文件。")
                
                msg.exec_()
            
            # 更新状态栏
            if success or valid_count > 0:
                count = self.image_manager.get_image_count()
                if has_duplicates:
                    self.status_label.setText(f"已导入 {valid_count} 张新图片，跳过 {len(duplicates)} 张重复图片，当前共 {count} 张")
                else:
                    self.status_label.setText(f"已导入 {len(file_paths)} 张图片，当前共 {count} 张")
            elif has_duplicates:
                self.status_label.setText(f"所有选中的图片都已存在，未导入新图片")
            else:
                QMessageBox.warning(self, "导入失败", "没有找到有效的图片文件")
            
            # 完成进度条
            progress_dialog.setValue(len(file_paths) + 1)
                
    def import_folder(self):
        """导入文件夹中的图片"""
        folder_path = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        
        if folder_path:
            # 获取文件夹中的所有文件以设置进度条
            all_files = os.listdir(folder_path)
            
            # 创建进度对话框
            progress_dialog = QProgressDialog("正在导入图片并设置模板...", "取消", 0, len(all_files) + 1, self)
            progress_dialog.setWindowTitle("请稍等，正在导入图片...")
            progress_dialog.setWindowModality(Qt.WindowModal)
            progress_dialog.show()
            
            # 更新进度
            progress_dialog.setValue(0)
            progress_dialog.setLabelText("正在导入图片...")
            QApplication.processEvents()
            
            result = self.image_manager.load_folder_images(folder_path)
            
            # 更新进度
            progress_dialog.setValue(len(all_files))
            progress_dialog.setLabelText("正在设置模板...")
            QApplication.processEvents()
            
            # 处理导入结果
            success = False
            has_duplicates = False
            duplicates = []
            valid_count = 0
            
            if result is True:
                # 成功导入新图片
                success = True
            elif isinstance(result, dict) and result.get("status") == "has_duplicates":
                # 有重复文件
                has_duplicates = True
                duplicates = result.get("duplicates", [])
                valid_count = result.get("valid_count", 0)
                success = result.get("success", False)
            
            # 显示重复文件警告（如果有）
            if has_duplicates:
                # 显示重复文件警告
                duplicate_names = [os.path.basename(path) for path in duplicates]
                duplicate_list = "\n".join([f"• {name}" for name in duplicate_names])
                
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("重复文件检测")
                msg.setText(f"检测到 {len(duplicates)} 个重复文件，已跳过导入。")
                msg.setInformativeText(f"重复文件列表：\n{duplicate_list}")
                
                if valid_count > 0:
                    msg.setDetailedText(f"已成功导入 {valid_count} 个新文件。")
                
                msg.exec_()
            
            # 更新状态栏
            if success or valid_count > 0:
                count = self.image_manager.get_image_count()
                if has_duplicates:
                    self.status_label.setText(f"已导入 {valid_count} 张新图片，跳过 {len(duplicates)} 张重复图片，当前共 {count} 张")
                else:
                    self.status_label.setText(f"已导入文件夹中的图片，当前共 {count} 张")
            elif has_duplicates:
                self.status_label.setText(f"文件夹中的所有图片都已存在，未导入新图片")
            else:
                QMessageBox.warning(self, "导入失败", "文件夹中没有找到有效的图片文件")
            
            # 完成进度条
            progress_dialog.setValue(len(all_files) + 1)
                
    def on_images_loaded(self, image_paths):
        """图片加载完成处理"""
        # 使用累加模式添加图片，不清空现有图片
        self.image_list_widget.add_images(image_paths, clear_existing=False)
        
        # 更新当前图片路径跟踪
        self.current_image_paths = self.image_manager.images.copy()
        
        # 更新预览控制按钮状态
        self.update_preview_controls()
        
        # 如果有图片，默认预览第一张图片
        if image_paths:
            print("图片加载完成，默认预览第一张图片")
            # 设置当前图片为第一张
            self.image_manager.set_current_image(0)
            # 先使用默认缩放比例显示图片，适应窗口操作后置
            self.current_scale = 1.0
            
            # 获取当前图片的水印设置
            current_image_path = self.image_manager.get_current_image_path()
            if current_image_path:
                # 获取当前图片的水印设置
                current_watermark_settings = self.image_manager.get_watermark_settings(current_image_path)
                
                # 如果当前图片没有水印设置，则设置默认的"center"位置
                if not current_watermark_settings:
                    # 检查是否有当前模板设置需要应用
                    if hasattr(self, '_current_template_type') and hasattr(self, '_current_template_settings'):
                        # 应用当前模板到新导入的图片
                        self.load_watermark_template(self._current_template_type, self._current_template_settings)
                    else:
                        # 获取全局默认水印设置
                        global_default_settings = self.config_manager.get_watermark_defaults()
                        # 确保位置设置为"center"
                        global_default_settings["position"] = "center"
                    # 确保颜色是QColor对象而不是字符串
                    if "color" in global_default_settings and isinstance(global_default_settings["color"], str):
                        global_default_settings["color"] = QColor(global_default_settings["color"])
                    # 确保包含所有必要的水印设置字段
                    if "font_family" not in global_default_settings:
                        global_default_settings["font_family"] = "Microsoft YaHei"
                    if "font_size" not in global_default_settings:
                        global_default_settings["font_size"] = 64
                    if "font_bold" not in global_default_settings:
                        global_default_settings["font_bold"] = False
                    if "font_italic" not in global_default_settings:
                        global_default_settings["font_italic"] = False
                    if "rotation" not in global_default_settings:
                        global_default_settings["rotation"] = 0
                    if "enable_shadow" not in global_default_settings:
                        global_default_settings["enable_shadow"] = False
                    if "enable_outline" not in global_default_settings:
                        global_default_settings["enable_outline"] = False
                    if "outline_color" not in global_default_settings:
                        global_default_settings["outline_color"] = (0, 0, 0)
                    if "outline_width" not in global_default_settings:
                        global_default_settings["outline_width"] = 1
                    if "outline_offset" not in global_default_settings:
                        global_default_settings["outline_offset"] = 0
                    if "shadow_color" not in global_default_settings:
                        global_default_settings["shadow_color"] = (0, 0, 0)
                    if "shadow_offset" not in global_default_settings:
                        global_default_settings["shadow_offset"] = (2, 2)
                    if "shadow_blur" not in global_default_settings:
                        global_default_settings["shadow_blur"] = 3
                    # 保存水印设置
                    self.image_manager.set_watermark_settings(current_image_path, global_default_settings)
                    print("新图片导入，自动设置水印位置为'center'")
                else:
                    # 如果已有水印设置，确保位置是坐标元组而不是字符串
                    position = current_watermark_settings.get("position", "center")
                    if isinstance(position, str):
                        # 如果位置是字符串，设置默认的中心位置坐标
                        img_width = self.original_pixmap.width()
                        img_height = self.original_pixmap.height()
                        # 计算文本尺寸（估算）
                        font_size = current_watermark_settings.get("font_size", 24)
                        text = current_watermark_settings.get("text", "")
                        # 简单估算文本宽度：每个字符约为font_size的0.6倍
                        text_width = int(len(text) * font_size * 0.6)
                        text_height = font_size
                        # 计算中心位置坐标
                        coordinates = ((img_width - text_width) // 2, (img_height - text_height) // 2)
                        # 使用update_position函数统一处理position更新
                        self.update_position(coordinates, current_watermark_settings)
                        print(f"将预设位置'{position}'转换为坐标元组: {coordinates}")
            
            # 为导入的图片执行一次load_watermark_template
            # 获取所有图片路径
            all_image_paths = self.image_manager.get_all_image_paths()
            # 为每个新导入的图片执行load_watermark_template
            for i, image_path in enumerate(all_image_paths):
                # 为每个图片执行一次image_selected操作，确保水印设置正确应用
                self.on_image_selected(i)
            
            # 使用基于水印设置的预览方法，避免循环调用
            self._update_preview_based_on_watermark()
            # 适应窗口操作后置，在图片显示后再执行
            QTimer.singleShot(100, self.fit_to_window)
        
    def on_image_selected(self, index):
        """图片列表项被选中"""
        self.image_manager.set_current_image(index)
        
        # 获取当前图片的水印设置并更新对应的水印组件
        current_image_path = self.image_manager.get_current_image_path()
        if current_image_path:
            # 获取当前图片的水印设置
            current_watermark_settings = self.image_manager.get_watermark_settings(current_image_path)
            
            if current_watermark_settings:
                # 根据水印类型更新UI
                watermark_type = current_watermark_settings.get('watermark_type', 'text')
                self.switch_watermark_type(watermark_type)
                
                # 更新对应的水印组件
                if watermark_type == 'text' and self.text_watermark_widget:
                    self.text_watermark_widget.set_watermark_settings(current_watermark_settings)
                elif watermark_type == 'image' and self.image_watermark_widget:
                    self.image_watermark_widget.set_watermark_settings(current_watermark_settings)
            else:
                # 如果没有水印设置，使用默认的文本水印
                self.switch_watermark_type('text')
                global_default_settings = self.config_manager.get_watermark_defaults()
                if "color" in global_default_settings and isinstance(global_default_settings["color"], str):
                    global_default_settings["color"] = QColor(global_default_settings["color"])
                self.text_watermark_widget.set_watermark_settings_with_placeholder_style(global_default_settings)
        
        # 统一使用带水印的预览方法
        self.update_preview_with_watermark()
        
        # 更新缩放比例显示
        self.update_scale_display()
        
        # 重置坐标显示
        # self.mouse_coord_label.setText("鼠标坐标: (0, 0)")
        # 水印坐标显示已在update_preview_with_watermark中更新
        
        # 执行虚拟拖拽操作以确保UI同步
        if self.drag_manager:
            # 重置拖拽管理器状态
            self.drag_manager.reset()
            
            # 获取当前水印设置
            current_watermark_settings = self.image_manager.get_current_watermark_settings()
            if current_watermark_settings:
                # 获取水印位置
                position = current_watermark_settings.get("position", (0, 0))
                if isinstance(position, tuple) and len(position) == 2:
                    # 模拟拖拽开始
                    if self.drag_manager.drag_started_callback:
                        self.drag_manager.drag_started_callback()
                    
                    # 模拟位置变化
                    if self.drag_manager.position_changed_callback:
                        self.drag_manager.position_changed_callback(position[0], position[1])
                    
                    # 模拟拖拽结束
                    if self.drag_manager.drag_stopped_callback:
                        self.drag_manager.drag_stopped_callback()
        
    def on_image_changed(self, index):
        """当前图片改变"""
        # 检查是否有新图片需要添加到缩略图列表
        current_paths = self.image_manager.images
        if len(current_paths) > len(self.current_image_paths):
            # 有新图片添加，更新缩略图列表
            new_paths = [path for path in current_paths if path not in self.current_image_paths]
            if new_paths:
                self.image_list_widget.add_images(new_paths, clear_existing=False)
            self.current_image_paths = current_paths.copy()
        
        # 更新图片列表选中状态
        self.image_list_widget.set_selected_image(index)
        
        # 获取当前图片的水印设置并更新对应的水印组件
        current_image_path = self.image_manager.get_current_image_path()
        if current_image_path:
            # 获取当前图片的水印设置
            current_watermark_settings = self.image_manager.get_watermark_settings(current_image_path)
            
            if current_watermark_settings:
                # 根据水印类型更新UI
                watermark_type = current_watermark_settings.get('watermark_type', 'text')
                self.switch_watermark_type(watermark_type)
                
                # 更新对应的水印组件
                if watermark_type == 'text' and self.text_watermark_widget:
                    self.text_watermark_widget.set_watermark_settings(current_watermark_settings)
                elif watermark_type == 'image' and self.image_watermark_widget:
                    self.image_watermark_widget.set_watermark_settings(current_watermark_settings)
            else:
                # 如果当前图片没有水印设置，使用默认的文本水印
                self.switch_watermark_type('text')
                global_default_settings = self.config_manager.get_watermark_defaults()
                # 将颜色字符串转换为QColor对象
                if "color" in global_default_settings and isinstance(global_default_settings["color"], str):
                    global_default_settings["color"] = QColor(global_default_settings["color"])
                
                # 设置全局默认水印，但显示为灰色占位样式
                self.text_watermark_widget.set_watermark_settings_with_placeholder_style(global_default_settings)
            
            # 获取当前图片的缩放比例设置
            saved_scale = self.image_manager.get_scale_settings(current_image_path)
            if saved_scale is not None:
                # 如果该图片有保存的缩放比例，使用保存的比例
                self.current_scale = saved_scale
                print(f"恢复图片缩放比例: {saved_scale:.2f}")
            else:
                # 如果没有保存的缩放比例，自动运行适应窗口并保存比例
                QTimer.singleShot(100, self.fit_to_window)
                print(f"首次预览，自动运行适应窗口")
        
        # 直接使用基于水印设置的预览方法，避免循环调用
        self._update_preview_based_on_watermark()
        
        # 更新缩放比例显示
        self.update_scale_display()
        
        # 更新状态栏
        count = self.image_manager.get_image_count()
        if count > 0:
            self.status_label.setText(f"当前显示第 {index + 1} 张 / 共 {count} 张")
            
    def update_preview_image(self):
        """更新预览图片 - 支持缩放和适应窗口"""
        print("开始更新预览图片...")
        
        # 获取当前图片路径
        current_path = self.image_manager.get_current_image_path()
        print(f"当前图片路径: {current_path}")
        
        if current_path:
            try:
                # 加载原始图片
                self.original_pixmap = QPixmap(current_path)
                if not self.original_pixmap.isNull():
                    print(f"图片加载成功，原始尺寸: {self.original_pixmap.width()}x{self.original_pixmap.height()}")
                    
                    # 应用当前缩放比例
                    self.apply_scale()
                    
                    self.preview_widget.setText("")
                    print("预览图片设置成功")
                else:
                    print("图片加载失败，QPixmap为空")
                    self.preview_widget.setText("图片加载失败")
                    self.preview_widget.setPixmap(QPixmap())
            except Exception as e:
                print(f"图片加载异常: {e}")
                self.preview_widget.setText("图片加载异常")
                self.preview_widget.setPixmap(QPixmap())
        else:
            print("当前图片路径为空")
            self.preview_widget.setText("请导入图片进行预览")
            self.preview_widget.setPixmap(QPixmap())
            
    def apply_scale(self):
        """应用当前缩放比例"""
        # 重新生成水印预览并应用缩放
        self.update_preview_with_watermark()
        
        # 输出预览缩放比例和预览尺寸
        if hasattr(self, 'original_pixmap') and not self.original_pixmap.isNull():
            original_width = self.original_pixmap.width()
            original_height = self.original_pixmap.height()
            # print(f"[DEBUG] 预览缩放比例: {self.current_scale:.4f}")
            
            # 计算预览尺寸
            preview_width = int(original_width * self.current_scale)
            preview_height = int(original_height * self.current_scale)
            print(f"[DEBUG] 预览尺寸: {preview_width}x{preview_height}")
        
        # 更新缩放比例显示
        self.update_scale_display()
            
    def calculate_fit_scale(self):
        """计算适应窗口的缩放比例"""
        if hasattr(self, 'original_pixmap') and not self.original_pixmap.isNull():
            # 获取预览区域可用尺寸
            available_width = self.preview_scroll_area.width() - 20
            available_height = self.preview_scroll_area.height() - 20
            
            # 计算适应窗口的缩放比例
            width_ratio = available_width / self.original_pixmap.width()
            height_ratio = available_height / self.original_pixmap.height()
            
            # 取较小的比例以确保图片完全显示
            fit_scale = min(width_ratio, height_ratio, 1.0)  # 最大不超过原始尺寸
            
            print(f"计算适应窗口缩放比例: {fit_scale:.2f}")
            return fit_scale
        return 1.0  # 默认缩放比例
    
    def update_scale_display(self):
        """更新缩放比例显示"""
        if hasattr(self, 'scale_label'):
            # 计算总缩放比例 = 压缩比例 * 预览缩放比例
            total_scale = self.current_scale
            
            # 如果有预览比例信息，则乘以压缩比例
            if hasattr(self, 'preview_ratio_info') and self.preview_ratio_info:
                compression_scale = self.preview_ratio_info.get('scale_factor', 1.0)
                total_scale = self.current_scale * compression_scale
            
            scale_percent = int(total_scale * 100)
            # 缩放比例显示已注释
            # self.scale_label.setText(f"缩放比例: {scale_percent}%")
            
            # 更新图片信息显示
            self.update_image_info_display()
    
    def fit_to_window(self):
        """适应窗口显示 - 保存缩放比例"""
        if hasattr(self, 'original_pixmap') and not self.original_pixmap.isNull():
            # 获取预览区域可用尺寸
            available_width = self.preview_scroll_area.width() - 20
            available_height = self.preview_scroll_area.height() - 20
            
            # 计算适应窗口的缩放比例
            width_ratio = available_width / self.original_pixmap.width()
            height_ratio = available_height / self.original_pixmap.height()
            
            # 取较小的比例以确保图片完全显示
            fit_scale = min(width_ratio, height_ratio, 1.0)  # 最大不超过原始尺寸
            
            self.current_scale = fit_scale
            
            # 保存适应窗口的缩放比例
            current_image_path = self.image_manager.get_current_image_path()
            if current_image_path:
                self.image_manager.set_scale_settings(current_image_path, fit_scale)
                print(f"适应窗口显示，保存缩放比例: {fit_scale:.2f}")
            
            # 重新生成水印预览并应用缩放
            self.update_preview_with_watermark()
            # 更新缩放比例显示
            self.update_scale_display()
            
    def zoom_in(self):
        """放大预览"""
        if hasattr(self, 'original_pixmap') and not self.original_pixmap.isNull():
            new_scale = min(self.current_scale + self.scale_step, self.max_scale)
            if new_scale != self.current_scale:
                self.current_scale = new_scale
                
                # 立即保存缩放比例
                current_image_path = self.image_manager.get_current_image_path()
                if current_image_path:
                    self.image_manager.set_scale_settings(current_image_path, self.current_scale)
                    print(f"保存缩放比例: {self.current_scale:.2f}")
                
                self._update_preview_based_on_watermark()
                # 更新缩放比例显示
                self.update_scale_display()
                print(f"放大到: {self.current_scale:.1f}x")
            else:
                print("已达到最大放大倍数")
                
    def zoom_out(self):
        """缩小预览"""
        if hasattr(self, 'original_pixmap') and not self.original_pixmap.isNull():
            new_scale = max(self.current_scale - self.scale_step, self.min_scale)
            if new_scale != self.current_scale:
                self.current_scale = new_scale
                
                # 立即保存缩放比例
                current_image_path = self.image_manager.get_current_image_path()
                if current_image_path:
                    self.image_manager.set_scale_settings(current_image_path, self.current_scale)
                    print(f"保存缩放比例: {self.current_scale:.2f}")
                
                self._update_preview_based_on_watermark()
                # 更新缩放比例显示
                self.update_scale_display()
                print(f"缩小到: {self.current_scale:.1f}x")
            else:
                print("已达到最小缩小倍数")
                
    def reset_zoom(self):
        """重置缩放比例"""
        self.current_scale = 1.0
        
        # 立即保存缩放比例
        current_image_path = self.image_manager.get_current_image_path()
        if current_image_path:
            self.image_manager.set_scale_settings(current_image_path, self.current_scale)
            print(f"重置缩放比例: {self.current_scale:.2f}")
        
        # 重新生成水印预览并应用缩放
        self.update_preview_with_watermark()
        # 更新缩放比例显示
        self.update_scale_display()
        print("重置缩放比例到 1.0x")
        
    def dragEnterEvent(self, event):
        """拖拽进入事件处理"""
        # 检查拖拽内容是否为文件
        if event.mimeData().hasUrls():
            # 检查文件是否为支持的图片格式
            urls = event.mimeData().urls()
            for url in urls:
                file_path = url.toLocalFile()
                if self.is_supported_image(file_path):
                    event.acceptProposedAction()
                    # 设置拖拽样式
                    self.preview_widget.setProperty("dragEnabled", "true")
                    self.preview_widget.style().unpolish(self.preview_widget)
                    self.preview_widget.style().polish(self.preview_widget)
                    return
        
        event.ignore()
        
    def dropEvent(self, event):
        """拖拽释放事件处理"""
        # 重置拖拽样式
        self.preview_widget.setProperty("dragEnabled", "false")
        self.preview_widget.style().unpolish(self.preview_widget)
        self.preview_widget.style().polish(self.preview_widget)
        
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            file_paths = []
            
            # 收集所有支持的图片文件
            for url in urls:
                file_path = url.toLocalFile()
                if self.is_supported_image(file_path):
                    file_paths.append(file_path)
            
            if file_paths:
                print(f"拖拽导入图片: {file_paths}")
                # 创建进度对话框
                progress_dialog = QProgressDialog("正在导入图片并设置模板...", "取消", 0, len(file_paths) + 1, self)
                progress_dialog.setWindowTitle("请稍等，正在导入图片...")
                progress_dialog.setWindowModality(Qt.WindowModal)
                progress_dialog.show()
                
                # 更新进度
                progress_dialog.setValue(0)
                progress_dialog.setLabelText("正在导入图片...")
                QApplication.processEvents()
                
                result = self.image_manager.load_multiple_images(file_paths)
                
                # 更新进度
                progress_dialog.setValue(len(file_paths))
                progress_dialog.setLabelText("正在设置模板...")
                QApplication.processEvents()
                
                if result is True:
                    # 成功导入新图片
                    count = self.image_manager.get_image_count()
                    self.status_label.setText(f"已导入 {len(file_paths)} 张图片，当前共 {count} 张")
                elif isinstance(result, dict) and result.get("status") == "has_duplicates":
                    # 有重复文件
                    duplicates = result.get("duplicates", [])
                    valid_count = result.get("valid_count", 0)
                    
                    # 显示重复文件警告
                    duplicate_names = [os.path.basename(path) for path in duplicates]
                    duplicate_list = "\n".join([f"• {name}" for name in duplicate_names])
                    
                    msg = QMessageBox(self)
                    msg.setIcon(QMessageBox.Warning)
                    msg.setWindowTitle("重复文件检测")
                    msg.setText(f"检测到 {len(duplicates)} 个重复文件，已跳过导入。")
                    msg.setInformativeText(f"重复文件列表：\n{duplicate_list}")
                    
                    if valid_count > 0:
                        msg.setDetailedText(f"已成功导入 {valid_count} 个新文件。")
                    
                    msg.exec_()
                    
                    if valid_count > 0:
                        count = self.image_manager.get_image_count()
                        self.status_label.setText(f"已导入 {valid_count} 张新图片，跳过 {len(duplicates)} 张重复图片，当前共 {count} 张")
                    else:
                        self.status_label.setText(f"所有拖拽的图片都已存在，未导入新图片")
                else:
                    QMessageBox.warning(self, "导入失败", "没有找到有效的图片文件")
                
                # 完成进度条
                progress_dialog.setValue(len(file_paths) + 1)
            else:
                QMessageBox.warning(self, "导入失败", "拖拽的文件不是支持的图片格式")
        
        event.acceptProposedAction()
        
    def is_supported_image(self, file_path):
        """检查文件是否为支持的图片格式"""
        if not os.path.isfile(file_path):
            return False
            
        # 支持的图片格式扩展名
        supported_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        file_ext = os.path.splitext(file_path)[1].lower()
        
        return file_ext in supported_extensions
            
    def update_preview_controls(self):
        """更新预览控制按钮状态"""
        count = self.image_manager.get_image_count()
        enabled = count > 0
        
        self.prev_button.setEnabled(enabled)
        self.next_button.setEnabled(enabled)
        self.zoom_in_button.setEnabled(enabled)
        self.zoom_out_button.setEnabled(enabled)
        self.fit_button.setEnabled(enabled)
        
    def prev_image(self):
        """切换到上一张图片"""
        self.image_manager.prev_image()
        
    def next_image(self):
        """切换到下一张图片"""
        self.image_manager.next_image()
        
    
        
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        # 简化：窗口大小改变时不自动更新预览图片
        # 避免频繁调用导致的性能问题
        pass
        
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于 Photo Watermark 2", 
                         "Photo Watermark 2\n\n"
                         "一个功能强大的图片水印软件\n"
                         "支持文本水印和图片水印\n"
                         "版本 1.0.0")
                         
    

    


        

        
    # def update_mouse_coordinates(self, event):
    #     """更新鼠标坐标显示 - 此方法已不再使用，我们现在使用统一的信息标签"""
    #     pass
            
    def update_watermark_coordinates(self):
        """更新水印坐标显示"""
        if self.original_pixmap and self.image_manager.get_current_image_path():
            # 获取当前图片的水印设置
            current_watermark_settings = self.image_manager.get_current_watermark_settings()
            
            # 文本水印处理
            if current_watermark_settings.get("text"):
                # 优先使用watermark_x和watermark_y
                if "watermark_x" in current_watermark_settings and "watermark_y" in current_watermark_settings:
                    watermark_x = int(current_watermark_settings["watermark_x"])
                    watermark_y = int(current_watermark_settings["watermark_y"])
                    position = current_watermark_settings.get("position", "")
                    # 水印坐标显示已注释
                    # self.watermark_coord_label.setText(f"水印坐标: ({watermark_x}, {watermark_y}), position: {position}")
                # 如果没有watermark_x和watermark_y，则使用position
                elif "position" in current_watermark_settings:
                    position = current_watermark_settings["position"]
                    if isinstance(position, tuple) and len(position) == 2:
                        # 确保水印坐标是基于原图坐标系的整数
                        watermark_x = int(position[0])
                        watermark_y = int(position[1])
                        # 更新watermark_x和watermark_y，以便下次可以直接使用
                        current_watermark_settings["watermark_x"] = watermark_x
                        current_watermark_settings["watermark_y"] = watermark_y
                        # 保存更新后的水印设置
                        current_image_path = self.image_manager.get_current_image_path()
                        if current_image_path:
                            self.image_manager.set_watermark_settings(current_image_path, current_watermark_settings)
                        # 水印坐标显示已注释
                        # self.watermark_coord_label.setText(f"水印坐标: ({watermark_x}, {watermark_y}), position: {position}")
                    else:
                        # 水印坐标显示已注释
                        # self.watermark_coord_label.setText(f"水印坐标: (0, 0), position: {position}")
                        pass
                else:
                    # 水印坐标显示已注释
                    # self.watermark_coord_label.setText("水印坐标: (0, 0)")
                    pass
            # 图片水印处理
            elif current_watermark_settings.get("image_path"):
                # 优先使用watermark_x和watermark_y
                if "watermark_x" in current_watermark_settings and "watermark_y" in current_watermark_settings:
                    watermark_x = int(current_watermark_settings["watermark_x"])
                    watermark_y = int(current_watermark_settings["watermark_y"])
                    position = current_watermark_settings.get("position", "")
                    # 水印坐标显示已注释
                    # self.watermark_coord_label.setText(f"水印坐标: ({watermark_x}, {watermark_y}), position: {position}")
                # 如果没有watermark_x和watermark_y，则使用position
                elif "position" in current_watermark_settings:
                    position = current_watermark_settings["position"]
                    if isinstance(position, tuple) and len(position) == 2:
                        # 确保水印坐标是基于原图坐标系的整数
                        watermark_x = int(position[0]*compression_scale)
                        watermark_y = int(position[1]*compression_scale)
                        # 更新watermark_x和watermark_y，以便下次可以直接使用
                        current_watermark_settings["watermark_x"] = watermark_x
                        current_watermark_settings["watermark_y"] = watermark_y
                        # 保存更新后的水印设置
                        current_image_path = self.image_manager.get_current_image_path()
                        if current_image_path:
                            self.image_manager.set_watermark_settings(current_image_path, current_watermark_settings)
                        # 水印坐标显示已注释
                        # self.watermark_coord_label.setText(f"水印坐标: ({watermark_x}, {watermark_y}), position: {position}")
                    else:
                        # 水印坐标显示已注释
                        # self.watermark_coord_label.setText(f"水印坐标: (0, 0), position: {position}")
                        pass
                else:
                    # 水印坐标显示已注释
                    # self.watermark_coord_label.setText("水印坐标: (0, 0)")
                    pass
            else:
                # 水印坐标显示已注释
                # self.watermark_coord_label.setText("水印坐标: (0, 0)")
                pass
        else:
            # 水印坐标显示已注释
            # self.watermark_coord_label.setText("水印坐标: (0, 0)")
            pass
    
    def update_position(self, new_position, current_watermark_settings=None):
        """
        统一更新position的函数，确保每次position变化时都更新watermark_x和watermark_y
        
        Args:
            new_position: 新的位置，可以是元组(x, y)或相对位置字符串
            current_watermark_settings: 当前水印设置，如果为None则从image_manager获取
        """
        print(f"[DEBUG] MainWindow.update_position: 修改position为 {new_position}")
        # 获取当前图片路径
        current_image_path = self.image_manager.get_current_image_path()
        if not current_image_path:
            return
            
        # 如果没有提供水印设置，则获取当前设置
        if current_watermark_settings is None:
            current_watermark_settings = self.image_manager.get_watermark_settings(current_image_path)
        
        # 检查水印坐标变化是否超过200像素
        if isinstance(new_position, tuple) and len(new_position) == 2:
            # 获取之前的水印位置
            old_x = 0
            old_y = 0
            if "watermark_x" in current_watermark_settings:
                old_x = int(current_watermark_settings["watermark_x"])
            if "watermark_y" in current_watermark_settings:
                old_y = int(current_watermark_settings["watermark_y"])
            
            # 计算坐标变化
            delta_x = abs(int(new_position[0]) - old_x)
            delta_y = abs(int(new_position[1]) - old_y)
            
            # 如果坐标变化超过200像素，打印警告和调用栈
            if delta_x > 200 or delta_y > 200:
                import traceback
                print(f"[WARNING] 水印坐标一次性变化超过200像素! X变化: {delta_x}, Y变化: {delta_y}")
                print(f"[WARNING] 旧坐标: ({old_x}, {old_y}), 新坐标: ({new_position[0]}, {new_position[1]})")
                print("[WARNING] 调用栈回溯:")
                traceback.print_stack()
        
        # 更新position
        current_watermark_settings["position"] = new_position
        
        # 如果新位置是元组格式，提取x和y坐标
        if isinstance(new_position, tuple) and len(new_position) == 2:
            # 注意：这里new_position已经是应用了压缩比例的坐标，不需要再次应用
            current_watermark_settings["position"] = new_position
            
            # 注意：position是水印在原图上的坐标，而watermark_x是水印在压缩图上的坐标
            # 两者的数学关系为：watermark_x = x * self.compression_scale（取整）
            current_watermark_settings["watermark_x"] = int(new_position[0]*self.compression_scale)
            current_watermark_settings["watermark_y"] = int(new_position[1]*self.compression_scale)
            print(f"[DEBUG] MainWindow.update_position: 更新position和坐标: position={new_position}, watermark_x={current_watermark_settings['watermark_x']}, watermark_y={current_watermark_settings['watermark_y']}, compression_scale={self.compression_scale}")
        
        # 保存更新后的水印设置
        self.image_manager.set_watermark_settings(current_image_path, current_watermark_settings)
        
        # 更新文本水印组件
        print(f"[DEBUG] MainWindow.update_position: 调用函数: self.text_watermark_widget.set_watermark_settings")
        self.text_watermark_widget.set_watermark_settings(current_watermark_settings)
        
        # 更新图片水印组件
        if self.watermark_type == "image" and self.image_watermark_widget:
            print(f"[DEBUG] MainWindow.update_position: 调用函数: self.image_watermark_widget.set_watermark_settings")
            self.image_watermark_widget.set_watermark_settings(current_watermark_settings)
            # 更新图片水印组件的坐标输入框
            print(f"[DEBUG] MainWindow.update_position: 调用函数: self.image_watermark_widget.update_coordinate_inputs")
            self.image_watermark_widget.update_coordinate_inputs()
        
        # 更新预览（这会自动调用update_watermark_coordinates）
        print(f"[DEBUG] MainWindow.update_position: 调用函数: self.update_preview_with_watermark")
        self.update_preview_with_watermark()
        
        return current_watermark_settings
            
    def update_image_info_display(self):
        """更新图片信息显示"""
        if self.original_pixmap and self.image_manager.get_current_image_path():
            # 获取原始图片尺寸
            original_width = self.original_pixmap.width()
            original_height = self.original_pixmap.height()
            
            # 获取水印坐标（仅使用position值）
            watermark_x, watermark_y = 0, 0
            current_watermark_settings = self.image_manager.get_current_watermark_settings()
            if current_watermark_settings and "position" in current_watermark_settings and isinstance(current_watermark_settings["position"], tuple) and len(current_watermark_settings["position"]) == 2:
                watermark_x = int(current_watermark_settings["position"][0])
                watermark_y = int(current_watermark_settings["position"][1])
            
            # 更新统一信息标签
            self.unified_info_label.setText(f"原图尺寸: {original_width}x{original_height} | 水印坐标: ({watermark_x}, {watermark_y}) | 预览缩放比例: {self.current_scale:.2f}")
        else:
            # 如果没有图片，重置所有显示
            self.unified_info_label.setText("原图尺寸: 0x0 | 水印坐标: (0, 0) | 预览缩放比例: 1.00")
            # self.preview_size_label.setText("预览尺寸: 0x0")
            # self.compression_ratio_label.setText("压缩比例: 1.00")
            # self.preview_scale_label.setText("预览缩放比例: 1.00")
        

        
    def check_watermark_position(self, watermark_settings, original_width, original_height):
        """检查水印位置是否超出边界，使用PIL/Pillow的ImageDraw.textbbox()函数获取精确的边界框
        
        此方法通过创建一个临时图像并使用PIL/Pillow的ImageDraw.textbbox()函数来获取文本水印的实际边界框，
        或者直接获取图片水印的尺寸，从而更准确地判断水印是否超出图片边界。
        
        Args:
            watermark_settings (dict): 水印设置，包含文本、位置、字体等信息
            original_width (int): 原始图片宽度
            original_height (int): 原始图片高度
        """
        try:
            # 优先使用position坐标，这是原图上的坐标
            position = watermark_settings.get("position", None)
            if isinstance(position, tuple) and len(position) == 2:
                position_x = position[0]
                position_y = position[1]
            else:
                # 如果没有position，则使用watermark_x和watermark_y
                position_x = watermark_settings.get("watermark_x", 0)
                position_y = watermark_settings.get("watermark_y", 0)
                # 将watermark坐标转换为position坐标（除以压缩比例）
                if hasattr(self, 'compression_scale') and self.compression_scale > 0:
                    position_x = position_x / self.compression_scale
                    position_y = position_y / self.compression_scale
            
            # 获取水印文本或图片路径
            text = watermark_settings.get("text", "")
            image_path = watermark_settings.get("image_path", "")
            
            # 检查是否有文本或图片水印
            if not text and not image_path:
                self.watermark_warning_label.setVisible(False)
                return
            
            # 初始化水印尺寸
            watermark_width = 0
            watermark_height = 0
            rotation = watermark_settings.get("rotation", 0)
            
            # 文本水印处理
            if text:
                # 获取字体大小和其他相关设置
                font_size = watermark_settings.get("font_size", 24)
                font_family = watermark_settings.get("font_family", "Arial")
                font_bold = watermark_settings.get("font_bold", False)
                font_italic = watermark_settings.get("font_italic", False)
                
                # 使用PIL/Pillow获取精确的文本边界框
                try:
                    from PIL import Image, ImageDraw, ImageFont
                    
                    # 创建一个足够大的临时图像来绘制文本
                    temp_img = Image.new('RGB', (original_width, original_height), (255, 255, 255))
                    temp_draw = ImageDraw.Draw(temp_img)
                    
                    # 尝试加载字体
                    try:
                        # 使用watermark_renderer中的字体加载逻辑
                        font = self.watermark_renderer._get_font(font_family, font_size, text, font_bold, font_italic)
                    except Exception as e:
                        print(f"加载字体失败: {e}")
                        # 如果加载字体失败，使用默认字体
                        font = ImageFont.load_default()
                    
                    # 获取文本边界框
                    # 使用(0, 0)作为参考点，因为我们只需要文本的尺寸
                    bbox = temp_draw.textbbox((0, 0), text, font=font)
                    
                    # 计算文本宽度和高度
                    watermark_width = bbox[2] - bbox[0]
                    watermark_height = bbox[3] - bbox[1]
                    
                    # 考虑旋转对边界的影响
                    if rotation != 0:
                        import math
                        # 计算旋转后的边界框
                        angle_rad = math.radians(abs(rotation))
                        rotated_width = abs(watermark_width * math.cos(angle_rad)) + abs(watermark_height * math.sin(angle_rad))
                        rotated_height = abs(watermark_width * math.sin(angle_rad)) + abs(watermark_height * math.cos(angle_rad))
                        watermark_width, watermark_height = rotated_width, rotated_height
                    
                except Exception as e:
                    print(f"使用PIL获取文本边界框时出错: {e}")
                    # 如果PIL方法失败，回退到原始的估算方法
                    # 这里我们直接调用_fallback_check_watermark_position来处理文本水印
                    self._fallback_check_watermark_position(
                        watermark_settings, original_width, original_height,
                        text, position_x, position_y, font_size, font_family,
                        font_bold, font_italic, rotation
                    )
                    return
            # 图片水印处理
            elif image_path:
                try:
                    from PIL import Image
                    
                    # 打开图片水印文件
                    watermark_img = Image.open(image_path)
                    
                    # 获取图片水印的原始尺寸
                    watermark_width, watermark_height = watermark_img.size
                    
                    # 考虑透明度和缩放（如果有）
                    opacity = watermark_settings.get("opacity", 1.0)
                    scale = watermark_settings.get("scale", 1.0)
                    
                    # 应用缩放
                    watermark_width = int(watermark_width * scale)
                    watermark_height = int(watermark_height * scale)
                    
                    # 考虑旋转对边界的影响
                    if rotation != 0:
                        import math
                        # 计算旋转后的边界框
                        angle_rad = math.radians(abs(rotation))
                        rotated_width = abs(watermark_width * math.cos(angle_rad)) + abs(watermark_height * math.sin(angle_rad))
                        rotated_height = abs(watermark_width * math.sin(angle_rad)) + abs(watermark_height * math.cos(angle_rad))
                        watermark_width, watermark_height = rotated_width, rotated_height
                    
                    watermark_height=watermark_height//100
                    watermark_width=watermark_width//100
                    print(f"图片水印尺寸: {watermark_width}x{watermark_height} (旋转{rotation}度)")
                except Exception as e:
                    print(f"获取图片水印尺寸时出错: {e}")
                    self.watermark_warning_label.setVisible(False)
                    return
            
            # 计算水印边界框的四个角坐标（基于position坐标）
            left = position_x
            top = position_y
            right = position_x + watermark_width
            bottom = position_y + watermark_height
            
            # 添加安全边距以确保水印完全可见
            safety_margin = 5  # 基本安全边距
            
            # 特别严格地检查右侧和上侧边界
            right_safety_margin = safety_margin + 2  # 右侧增加额外的安全边距
            top_safety_margin = safety_margin + 2    # 上侧增加额外的安全边距
            
            # 定义原图边界加上安全边际
            # 左边界允许超出一点，但右边界和上边界更严格
            image_left = -safety_margin
            image_right = original_width + right_safety_margin
            image_top = -top_safety_margin
            image_bottom = original_height + safety_margin
            
            # 直接检查四个角是否都在原图边界内（考虑安全边际）
            is_out_of_bounds = (
                left < image_left or    # 左边界超出
                right > image_right or  # 右边界超出
                top < image_top or      # 上边界超出
                bottom > image_bottom   # 下边界超出
            )
            
            # 显示或隐藏警告标签
            if is_out_of_bounds and (position_x != 0 or position_y != 0):
                self.watermark_warning_label.setVisible(True)
            else:
                self.watermark_warning_label.setVisible(False)
                
        except Exception as e:
            print(f"检查水印位置时出错: {e}")
            self.watermark_warning_label.setVisible(False)
            
    def _fallback_check_watermark_position(self, watermark_settings, original_width, original_height,
                                          text, position_x, position_y, font_size, font_family,
                                          font_bold, font_italic, rotation):
        """回退的水印位置检查方法，使用估算的文本尺寸或图片尺寸
        
        当PIL/Pillow方法不可用时，使用此方法进行水印位置检查。
        
        Args:
            watermark_settings (dict): 水印设置
            original_width (int): 原始图片宽度
            original_height (int): 原始图片高度
            text (str): 水印文本
            position_x (float): 水印X坐标（position坐标，原图上的坐标）
            position_y (float): 水印Y坐标（position坐标，原图上的坐标）
            font_size (int): 字体大小
            font_family (str): 字体名称
            font_bold (bool): 是否粗体
            font_italic (bool): 是否斜体
            rotation (int): 旋转角度
        """
        try:
            # 检查是文本水印还是图片水印
            image_path = watermark_settings.get("image_path", "")
            
            # 初始化水印尺寸
            watermark_width = 0
            watermark_height = 0
            
            # 文本水印处理
            if text and not image_path:
                # 更精确地估算文本尺寸
                # 考虑到不同字体和样式的影响
                char_count = len(text)
                
                # 基于字体大小估算文本宽度和高度
                # 对于中文字体，每个字符大约占用font_size像素宽度
                # 对于英文字体，平均字符宽度约为font_size * 0.6
                if self._contains_chinese(text):
                    # 中文文本使用更保守的估算，确保足够的空间
                    watermark_width = char_count * font_size * 1.5  # 增加50%的宽度以确保安全
                else:
                    # 英文文本使用更紧凑的估算
                    watermark_width = char_count * font_size  # 稍微增加英文文本的宽度估算
                
                # 文本高度估算，增加额外的空间以确保安全
                watermark_height = font_size * 2  # 增加行间距的估算
                
                # 考虑粗体和斜体对尺寸的影响
                if font_bold:
                    watermark_width *= 1.05  # 增加粗体对宽度的影响
                    watermark_height *= 1.05  # 增加粗体对高度的影响
                
                if font_italic:
                    watermark_width *= 1.05  # 增加斜体对宽度的影响
            # 图片水印处理
            elif image_path:
                # 估算图片水印尺寸
                # 从watermark_settings中获取图片相关设置
                scale = watermark_settings.get("scale", 1.0)
                
                # 假设图片水印的原始尺寸（如果无法加载图片时的粗略估算）
                # 使用一个合理的默认尺寸作为估算基础
                default_width = 200
                default_height = 200
                
                # 应用缩放
                watermark_width = default_width * scale
                watermark_height = default_height * scale
            
            # 考虑旋转对边界的影响
            if rotation != 0:
                import math
                # 计算旋转后的边界框
                angle_rad = math.radians(abs(rotation))
                rotated_width = abs(watermark_width * math.cos(angle_rad)) + abs(watermark_height * math.sin(angle_rad))
                rotated_height = abs(watermark_width * math.sin(angle_rad)) + abs(watermark_height * math.cos(angle_rad))
                watermark_width, watermark_height = rotated_width, rotated_height
            
            # 计算水印边界（基于position坐标）
            left_bound = position_x
            right_bound = position_x + watermark_width
            top_bound = position_y
            bottom_bound = position_y + watermark_height
            
            # 更严格的边界检查，特别是右侧和上侧
            # 添加额外的安全边距以确保水印完全可见
            safety_margin = 5  # 像素安全边距
            
            # 特别严格地检查右侧边界，因为用户特别提到了右侧边界检测应该更严格
            right_safety_margin = safety_margin + 2  # 右侧增加额外的安全边距
            top_safety_margin = safety_margin + 2    # 上侧增加额外的安全边距
            
            # 检查是否超出边界
            if (left_bound < -safety_margin or 
                right_bound > original_width + right_safety_margin or 
                top_bound < -top_safety_margin or 
                bottom_bound > original_height + safety_margin) and \
                (position_x != 0 or position_y != 0):
                self.watermark_warning_label.setVisible(True)
            else:
                self.watermark_warning_label.setVisible(False)
        except Exception as e:
            print(f"回退检查水印位置时出错: {e}")
            self.watermark_warning_label.setVisible(False)
            
    def _contains_chinese(self, text):
        """检查文本是否包含中文字符"""
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False
    
    def _export_single_image(self, image_path, watermark_settings, output_path, export_settings):
        """
        封装单个图片的导出核心逻辑（无UI交互）
        
        Args:
            image_path (str): 原始图片路径
            watermark_settings (dict): 水印设置
            output_path (str): 输出文件路径
            export_settings (dict): 导出设置
            
        Returns:
            bool: 导出是否成功
            str: 错误信息（如果失败）
        """
        try:
            # 加载原始图片
            original_image = PILImage.open(image_path)
            
            # 根据水印类型选择渲染方法
            watermark_type = watermark_settings.get('watermark_type', 'text')
            if watermark_type == 'text':
                # 渲染文本水印
                watermarked_image = self.watermark_renderer.render_text_watermark(original_image, watermark_settings, is_preview=False)
            elif watermark_type == 'image':
                # 渲染图片水印
                watermarked_image = self.watermark_renderer.render_image_watermark(original_image, watermark_settings, is_preview=False)
            else:
                # 默认使用文本水印
                watermarked_image = self.watermark_renderer.render_text_watermark(original_image, watermark_settings, is_preview=False)
            
            # 根据导出设置调整图片尺寸（现在是对已经渲染了水印的图片进行整体缩放）
            resize_option = export_settings.get('resize_option', 0)
            if resize_option == 1:  # 按宽度调整
                new_width = export_settings.get('resize_value', 800)
                # 计算保持宽高比的高度
                width_percent = (new_width / float(watermarked_image.size[0]))
                new_height = int(float(watermarked_image.size[1]) * float(width_percent))
                watermarked_image = watermarked_image.resize((new_width, new_height), PILImage.LANCZOS)
            elif resize_option == 2:  # 按高度调整
                new_height = export_settings.get('resize_value', 600)
                # 计算保持宽高比的宽度
                height_percent = (new_height / float(watermarked_image.size[1]))
                new_width = int(float(watermarked_image.size[0]) * float(height_percent))
                watermarked_image = watermarked_image.resize((new_width, new_height), PILImage.LANCZOS)
            elif resize_option == 3:  # 按百分比调整
                percent = export_settings.get('percent_value', 100) / 100.0
                new_width = int(watermarked_image.size[0] * percent)
                new_height = int(watermarked_image.size[1] * percent)
                watermarked_image = watermarked_image.resize((new_width, new_height), PILImage.LANCZOS)
            elif resize_option == 4:  # 自定义尺寸
                new_width = export_settings.get('custom_width', 800)
                new_height = export_settings.get('custom_height', 600)
                # 直接调整到指定尺寸，不保持宽高比
                watermarked_image = watermarked_image.resize((new_width, new_height), PILImage.LANCZOS)
            
            # 准备保存参数
            save_params = {}
            file_ext = os.path.splitext(output_path)[1].lower()
            
            # 如果是JPEG格式，添加质量设置
            if file_ext in ['.jpg', '.jpeg'] and 'quality' in export_settings:
                save_params['quality'] = export_settings['quality']
                save_params['optimize'] = True
            elif file_ext == '.png':
                save_params['optimize'] = True
            
            # 处理RGBA模式转换：如果是JPEG格式但图片是RGBA模式（含透明度），需要转换为RGB
            file_ext = os.path.splitext(output_path)[1].lower()
            if file_ext in ['.jpg', '.jpeg'] and watermarked_image.mode == 'RGBA':
                # 创建一个白色背景的RGB图像
                background = PILImage.new('RGB', watermarked_image.size, (255, 255, 255))
                # 将RGBA图像粘贴到白色背景上，使用alpha通道作为蒙版
                background.paste(watermarked_image, mask=watermarked_image.split()[3])  # 3是alpha通道
                watermarked_image = background
            
            # 保存渲染后的图片
            watermarked_image.save(output_path, **save_params)
            return True, ""
        except Exception as e:
            error_msg = str(e)
            logging.error(f"导出图片 {image_path} 失败: {error_msg}")
            return False, error_msg
            
    def export_image(self):
        """导出当前图片，应用水印效果"""
        # 获取当前图片路径
        current_image_path = self.image_manager.get_current_image_path()
        if not current_image_path:
            QMessageBox.warning(self, "警告", "请先选择要导出的图片")
            return
        
        # 获取当前图片的水印设置
        watermark_settings = self.image_manager.get_watermark_settings(current_image_path)
        
        # 显示导出对话框
        export_dialog = ExportDialog(current_image_path, self)
        
        # 连接导出确认信号
        export_dialog.export_confirmed.connect(lambda settings: self._process_export_image(
            current_image_path, watermark_settings, settings))
        
        # 显示对话框
        export_dialog.exec_()
    
    def _process_export_image(self, image_path, watermark_settings, export_settings):
        """处理图片导出
        
        Args:
            image_path (str): 原始图片路径
            watermark_settings (dict): 水印设置
            export_settings (dict): 导出设置
        """
        # 添加标记，用于记录用户是否已经确认过使用原文件夹
        self._confirmed_original_folder_export = False
        # 获取当前图片所在目录
        current_dir = os.path.dirname(image_path)
        
        # 获取用户文档目录作为默认导出目录
        import pathlib
        documents_dir = str(pathlib.Path.home() / "Documents")
        
        # 获取输出文件名
        # 从export_settings直接获取用户设置的命名规则
        naming_rule = export_settings.get('naming_rule', 'original')
        prefix_suffix = export_settings.get('prefix_suffix', '')
        custom_name = export_settings.get('custom_name', '')
        
        # 根据用户设置的命名规则构建输出文件名
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        original_extension = os.path.splitext(image_path)[1]
        
        # 获取用户选择的格式选项
        format_option = export_settings.get('format_option', 0)
        
        # 根据选择的格式确定扩展名
        if format_option == 0:  # 保留原格式
            extension = original_extension
        elif format_option == 1:  # 导出为JPEG
            extension = '.jpg'
        elif format_option == 2:  # 导出为PNG
            extension = '.png'
        else:
            extension = original_extension
        
        if naming_rule == 'original':
            output_filename = f"{base_name}{extension}"
        elif naming_rule == 'prefix':
            output_filename = f"{prefix_suffix}{base_name}{extension}"
        elif naming_rule == 'suffix':
            output_filename = f"{base_name}{prefix_suffix}{extension}"
        elif naming_rule == 'custom':
            # 确保自定义文件名包含扩展名
            if not any(custom_name.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']):
                output_filename = f"{custom_name}{extension}"
            else:
                output_filename = custom_name
        else:
            # 默认使用原始文件名
            output_filename = f"{base_name}{extension}"
        
        # 打开文件夹选择对话框，让用户选择输出文件夹
        output_dir = QFileDialog.getExistingDirectory(
            self, "选择输出文件夹", documents_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if not output_dir:
            return  # 用户取消了选择
        
        # 检查用户选择的文件夹是否是原图片所在文件夹
        if os.path.normpath(output_dir) == os.path.normpath(current_dir):
            # 创建自定义按钮的对话框
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("警告")
            msg_box.setText("为防止覆盖原图，默认禁止导出到原文件夹。")
            msg_box.setInformativeText("请选择您要执行的操作：")
            
            # 添加自定义按钮
            retry_button = msg_box.addButton("重新选择文件夹", QMessageBox.ActionRole)
            continue_button = msg_box.addButton("继续使用原文件夹", QMessageBox.ActionRole)
            
            # 添加关闭按钮，使其可以通过点击右上角的叉来关闭
            close_button = msg_box.addButton("取消", QMessageBox.RejectRole)
            
            # 设置默认按钮
            msg_box.setDefaultButton(retry_button)
            
            # 显示对话框
            msg_box.exec_()
            
            # 检查用户是否点击了关闭按钮
            if msg_box.clickedButton() == close_button:
                return  # 用户关闭了对话框
            
            if msg_box.clickedButton() == retry_button:
                # 用户选择重新选择文件夹
                output_dir = QFileDialog.getExistingDirectory(
                    self, "选择输出文件夹", documents_dir,
                    QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
                )
                
                if not output_dir:
                    return  # 用户取消了选择
                
                # 如果用户选择了非原文件夹，清除标记
                if os.path.normpath(output_dir) != os.path.normpath(current_dir):
                    self._confirmed_original_folder_export = False
                
                # 再次检查是否是原文件夹
                if os.path.normpath(output_dir) == os.path.normpath(current_dir):
                    # 创建自定义按钮的对话框
                    msg_box = QMessageBox(self)
                    msg_box.setIcon(QMessageBox.Warning)
                    msg_box.setWindowTitle("再次确认")
                    msg_box.setText("您仍然选择了原文件夹。")
                    msg_box.setInformativeText("确定要导出到原文件夹吗？这可能会覆盖原图。")
                    
                    # 添加自定义按钮
                    retry_button = msg_box.addButton("重新选择文件夹", QMessageBox.ActionRole)
                    continue_button = msg_box.addButton("继续使用原文件夹", QMessageBox.ActionRole)
                    
                    # 设置默认按钮
                    msg_box.setDefaultButton(retry_button)
                    
                    # 显示对话框
                    msg_box.exec_()
                    
                    if msg_box.clickedButton() == retry_button:
                        # 用户选择重新选择文件夹
                        output_dir = QFileDialog.getExistingDirectory(
                            self, "选择输出文件夹", documents_dir,
                            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
                        )
                        
                        if not output_dir:
                            return  # 用户取消了选择
                        
                        # 再次检查是否是原文件夹
                        if os.path.normpath(output_dir) == os.path.normpath(current_dir):
                            # 第三次确认
                            reply = QMessageBox.question(
                                self, 
                                "最终确认", 
                                "您再次选择了原文件夹。确定要导出到原文件夹吗？这可能会覆盖原图。",
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No
                            )
                            
                            if reply == QMessageBox.No:
                                return  # 用户取消导出
                            else:
                                self._confirmed_original_folder_export = True  # 设置标记，用户已确认使用原文件夹
                    else:
                        # 用户选择继续使用原文件夹
                        self._confirmed_original_folder_export = True  # 设置标记，用户已确认使用原文件夹
                        pass  # 继续执行导出
            else:
                # 用户选择继续使用原文件夹，需要二次确认
                reply = QMessageBox.question(
                    self, 
                    "确认覆盖", 
                    "您确定要导出到原文件夹吗？这可能会覆盖原图。",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return  # 用户取消导出
                
                self._confirmed_original_folder_export = True  # 设置标记，用户已确认使用原文件夹
        
        # 构建完整的输出文件路径
        output_path = os.path.join(output_dir, output_filename)
        
        # 根据用户选择的格式构建文件过滤器
        if format_option == 0:  # 保留原格式
            file_filter = "图片文件 (*.jpg *.jpeg *.png *.bmp);;所有文件 (*)"
        elif format_option == 1:  # 导出为JPEG
            file_filter = "JPEG图片 (*.jpg *.jpeg);;所有文件 (*)"
        elif format_option == 2:  # 导出为PNG
            file_filter = "PNG图片 (*.png);;所有文件 (*)"
        else:
            file_filter = "图片文件 (*.jpg *.jpeg *.png *.bmp);;所有文件 (*)"
        
        # 打开文件保存对话框，预填充用户设置的文件名和格式
        file_name, _ = QFileDialog.getSaveFileName(
            self, "导出图片", 
            output_path,
            file_filter
        )
        
        if not file_name:
            return  # 用户取消了保存
            
        # 如果用户选择了特定格式，确保文件扩展名正确
        if format_option != 0:  # 不是保留原格式
            # 获取文件基本名（不含扩展名）
            base_name = os.path.splitext(os.path.basename(file_name))[0]
            # 确保使用正确的扩展名
            if format_option == 1:  # JPEG
                if not file_name.lower().endswith(('.jpg', '.jpeg')):
                    file_name = os.path.join(os.path.dirname(file_name), f"{base_name}.jpg")
            elif format_option == 2:  # PNG
                if not file_name.lower().endswith('.png'):
                    file_name = os.path.join(os.path.dirname(file_name), f"{base_name}.png")
        
        # 再次检查最终选择的路径是否在原文件夹中
        if os.path.normpath(os.path.dirname(file_name)) == os.path.normpath(current_dir) and not self._confirmed_original_folder_export:
            # 创建自定义按钮的对话框
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("警告")
            msg_box.setText("为防止覆盖原图，默认禁止导出到原文件夹。")
            msg_box.setInformativeText("请选择您要执行的操作：")
            
            # 添加自定义按钮
            retry_button = msg_box.addButton("重新选择文件夹", QMessageBox.ActionRole)
            continue_button = msg_box.addButton("继续使用原文件夹", QMessageBox.ActionRole)
            
            # 添加关闭按钮，使其可以通过点击右上角的叉来关闭
            close_button = msg_box.addButton("关闭", QMessageBox.RejectRole)
            
            # 设置默认按钮
            msg_box.setDefaultButton(retry_button)
            
            # 显示对话框
            msg_box.exec_()
            
            # 检查用户是否点击了关闭按钮
            if msg_box.clickedButton() == close_button:
                return  # 用户关闭了对话框
            
            if msg_box.clickedButton() == retry_button:
                # 用户选择重新选择文件夹
                new_dir = QFileDialog.getExistingDirectory(
                    self, "选择输出文件夹", documents_dir,
                    QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
                )
                
                if not new_dir:
                    return  # 用户取消了选择
                
                # 如果用户选择了非原文件夹，清除标记
                if os.path.normpath(new_dir) != os.path.normpath(current_dir):
                    self._confirmed_original_folder_export = False
                
                # 从export_settings直接获取用户设置的命名规则
                naming_rule = export_settings.get('naming_rule', 'original')
                prefix_suffix = export_settings.get('prefix_suffix', '')
                custom_name = export_settings.get('custom_name', '')
                
                # 根据用户设置的命名规则构建输出文件名
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                original_extension = os.path.splitext(image_path)[1]
                
                # 获取用户选择的格式选项
                format_option = export_settings.get('format_option', 0)
                
                # 根据选择的格式确定扩展名
                if format_option == 0:  # 保留原格式
                    extension = original_extension
                elif format_option == 1:  # 导出为JPEG
                    extension = '.jpg'
                elif format_option == 2:  # 导出为PNG
                    extension = '.png'
                else:
                    extension = original_extension
                
                if naming_rule == 'original':
                    output_filename = f"{base_name}{extension}"
                elif naming_rule == 'prefix':
                    output_filename = f"{prefix_suffix}{base_name}{extension}"
                elif naming_rule == 'suffix':
                    output_filename = f"{base_name}{prefix_suffix}{extension}"
                elif naming_rule == 'custom':
                    # 确保自定义文件名包含扩展名
                    if not any(custom_name.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']):
                        output_filename = f"{custom_name}{extension}"
                    else:
                        output_filename = custom_name
                else:
                    # 默认使用原始文件名
                    output_filename = f"{base_name}{extension}"
                
                # 构建新的输出文件路径，使用用户设置的命名规则
                new_file_name = os.path.join(new_dir, output_filename)
                
                # 再次打开文件保存对话框，预填充用户设置的文件名
                file_name, _ = QFileDialog.getSaveFileName(
                    self, "导出图片", 
                    new_file_name,
                    "图片文件 (*.jpg *.jpeg *.png *.bmp);;所有文件 (*)"
                )
                
                if not file_name:
                    return  # 用户取消了保存
                
                # 再次检查最终选择的路径是否在原文件夹中
                if os.path.normpath(os.path.dirname(file_name)) == os.path.normpath(current_dir):
                    # 创建自定义按钮的对话框
                    msg_box = QMessageBox(self)
                    msg_box.setIcon(QMessageBox.Warning)
                    msg_box.setWindowTitle("再次确认")
                    msg_box.setText("您仍然选择了原文件夹。")
                    msg_box.setInformativeText("确定要导出到原文件夹吗？这可能会覆盖原图。")
                    
                    # 添加自定义按钮
                    retry_button = msg_box.addButton("重新选择文件夹", QMessageBox.ActionRole)
                    continue_button = msg_box.addButton("继续使用原文件夹", QMessageBox.ActionRole)
                    
                    # 设置默认按钮
                    msg_box.setDefaultButton(retry_button)
                    
                    # 显示对话框
                    msg_box.exec_()
                    
                    if msg_box.clickedButton() == retry_button:
                        # 用户选择重新选择文件夹
                        new_dir = QFileDialog.getExistingDirectory(
                            self, "选择输出文件夹", documents_dir,
                            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
                        )
                        
                        if not new_dir:
                            return  # 用户取消了选择
                        
                        # 如果用户选择了非原文件夹，清除标记
                        if os.path.normpath(new_dir) != os.path.normpath(current_dir):
                            self._confirmed_original_folder_export = False
                        
                        # 从export_settings直接获取用户设置的命名规则
                        naming_rule = export_settings.get('naming_rule', 'original')
                        prefix_suffix = export_settings.get('prefix_suffix', '')
                        custom_name = export_settings.get('custom_name', '')
                        
                        # 根据用户设置的命名规则构建输出文件名
                        base_name = os.path.splitext(os.path.basename(image_path))[0]
                        extension = os.path.splitext(image_path)[1]
                        
                        if naming_rule == 'original':
                            output_filename = f"{base_name}{extension}"
                        elif naming_rule == 'prefix':
                            output_filename = f"{prefix_suffix}{base_name}{extension}"
                        elif naming_rule == 'suffix':
                            output_filename = f"{base_name}{prefix_suffix}{extension}"
                        elif naming_rule == 'custom':
                            # 确保自定义文件名包含扩展名
                            if not any(custom_name.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']):
                                output_filename = f"{custom_name}{extension}"
                            else:
                                output_filename = custom_name
                        else:
                            # 默认使用原始文件名
                            output_filename = f"{base_name}{extension}"
                        
                        # 构建新的输出文件路径，使用用户设置的命名规则
                        new_file_name = os.path.join(new_dir, output_filename)
                        
                        # 再次打开文件保存对话框，预填充用户设置的文件名
                        file_name, _ = QFileDialog.getSaveFileName(
                            self, "导出图片", 
                            new_file_name,
                            "图片文件 (*.jpg *.jpeg *.png *.bmp);;所有文件 (*)"
                        )
                        
                        if not file_name:
                            return  # 用户取消了保存
                        
                        # 再次检查最终选择的路径是否在原文件夹中
                        if os.path.normpath(os.path.dirname(file_name)) == os.path.normpath(current_dir):
                            # 第三次确认
                            reply = QMessageBox.question(
                                self, 
                                "最终确认", 
                                "您再次选择了原文件夹。确定要导出到原文件夹吗？这可能会覆盖原图。",
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No
                            )
                            
                            if reply == QMessageBox.No:
                                return  # 用户取消导出
                    else:
                        # 用户选择继续使用原文件夹
                        self._confirmed_original_folder_export = True  # 设置标记，用户已确认使用原文件夹
                        pass  # 继续执行导出
            else:
                # 用户选择继续使用原文件夹，需要二次确认
                reply = QMessageBox.question(
                    self, 
                    "确认覆盖", 
                    "您确定要导出到原文件夹吗？这可能会覆盖原图。",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return  # 用户取消导出
        
        try:
            # 调用封装的单个图片导出函数
            success, error_msg = self._export_single_image(image_path, watermark_settings, file_name, export_settings)
            
            if success:
                # 显示导出成功提示
                QMessageBox.information(self, "成功", f"图片已成功导出到:\n{file_name}")
            else:
                QMessageBox.critical(self, "错误", f"导出图片时出错:\n{error_msg}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出图片时出错:\n{str(e)}")
            logging.error(f"导出图片失败: {str(e)}")
    
    def export_all_images(self):
        """批量导出所有图片，应用水印效果"""
        # 获取所有图片路径
        all_image_paths = self.image_manager.get_all_image_paths()
        if not all_image_paths:
            QMessageBox.warning(self, "警告", "没有可导出的图片")
            return
        
        # 显示批量导出对话框
        batch_export_dialog = BatchExportDialog(all_image_paths, self)
        
        # 连接导出确认信号
        batch_export_dialog.export_confirmed.connect(lambda settings: self._process_batch_export(
            all_image_paths, settings))
        
        # 显示对话框
        batch_export_dialog.exec_()
    
    def _process_batch_export(self, all_image_paths, export_settings):
        """处理批量图片导出
        
        Args:
            all_image_paths (list): 所有图片路径列表
            export_settings (dict): 导出设置
        """
        # 获取用户文档目录作为默认导出目录
        import pathlib
        documents_dir = str(pathlib.Path.home() / "Documents")
        
        # 打开文件夹选择对话框，让用户选择输出文件夹
        output_dir = QFileDialog.getExistingDirectory(
            self, "选择输出文件夹", documents_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if not output_dir:
            return  # 用户取消了选择
        
        # 检查是否有图片的原文件夹与输出文件夹相同
        original_dirs = set(os.path.dirname(path) for path in all_image_paths)
        if os.path.normpath(output_dir) in [os.path.normpath(dir) for dir in original_dirs]:
            # 创建自定义按钮的对话框
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("警告")
            msg_box.setText("为防止覆盖原图，默认禁止导出到原文件夹。")
            msg_box.setInformativeText("请选择您要执行的操作：")
            
            # 添加自定义按钮
            retry_button = msg_box.addButton("重新选择文件夹", QMessageBox.ActionRole)
            continue_button = msg_box.addButton("继续使用原文件夹", QMessageBox.ActionRole)
            
            # 添加关闭按钮，使其可以通过点击右上角的叉来关闭
            close_button = msg_box.addButton("关闭", QMessageBox.RejectRole)
            
            # 设置默认按钮
            msg_box.setDefaultButton(retry_button)
            
            # 显示对话框
            msg_box.exec_()
            
            # 检查用户是否点击了关闭按钮
            if msg_box.clickedButton() == close_button:
                return  # 用户关闭了对话框
            
            if msg_box.clickedButton() == retry_button:
                # 用户选择重新选择文件夹
                output_dir = QFileDialog.getExistingDirectory(
                    self, "选择输出文件夹", documents_dir,
                    QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
                )
                
                if not output_dir:
                    return  # 用户取消了选择
                
                # 再次检查是否是原文件夹
                if os.path.normpath(output_dir) in [os.path.normpath(dir) for dir in original_dirs]:
                    # 创建自定义按钮的对话框
                    msg_box = QMessageBox(self)
                    msg_box.setIcon(QMessageBox.Warning)
                    msg_box.setWindowTitle("再次确认")
                    msg_box.setText("您仍然选择了原文件夹。")
                    msg_box.setInformativeText("确定要导出到原文件夹吗？这可能会覆盖原图。")
                    
                    # 添加自定义按钮
                    retry_button = msg_box.addButton("重新选择文件夹", QMessageBox.ActionRole)
                    continue_button = msg_box.addButton("继续使用原文件夹", QMessageBox.ActionRole)
                    
                    # 设置默认按钮
                    msg_box.setDefaultButton(retry_button)
                    
                    # 显示对话框
                    msg_box.exec_()
                    
                    if msg_box.clickedButton() == retry_button:
                        # 用户选择重新选择文件夹
                        output_dir = QFileDialog.getExistingDirectory(
                            self, "选择输出文件夹", documents_dir,
                            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
                        )
                        
                        if not output_dir:
                            return  # 用户取消了选择
                        
                        # 再次检查是否是原文件夹
                        if os.path.normpath(output_dir) in [os.path.normpath(dir) for dir in original_dirs]:
                            # 第三次确认
                            reply = QMessageBox.question(
                                self, 
                                "最终确认", 
                                "您再次选择了原文件夹。确定要导出到原文件夹吗？这可能会覆盖原图。",
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No
                            )
                            
                            if reply == QMessageBox.No:
                                return  # 用户取消导出
                    else:
                        # 用户选择继续使用原文件夹
                        pass  # 继续执行导出
            else:
                # 用户选择继续使用原文件夹，需要二次确认
                reply = QMessageBox.question(
                    self, 
                    "确认覆盖", 
                    "您确定要导出到原文件夹吗？这可能会覆盖原图。",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return  # 用户取消导出
        
        # 创建进度对话框
        progress_dialog = QProgressDialog("正在导出图片...", "取消", 0, len(all_image_paths), self)
        progress_dialog.setWindowTitle("请稍等，正在导出图片...")
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.show()
        
        # 成功导出的图片计数
        success_count = 0
        failed_images = []
        
        # 逐个导出图片
        for i, image_path in enumerate(all_image_paths):
            # 更新进度对话框
            progress_dialog.setValue(i)
            progress_dialog.setLabelText(f"正在导出: {os.path.basename(image_path)}")
            
            # 检查是否用户取消了操作
            if progress_dialog.wasCanceled():
                break
            
            # 获取当前图片的水印设置
            watermark_settings = self.image_manager.get_watermark_settings(image_path)
            
            # 构建输出文件名
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            original_extension = os.path.splitext(image_path)[1]
            
            # 获取用户选择的格式选项
            format_option = export_settings.get('format_option', 0)
            
            # 根据选择的格式确定扩展名
            if format_option == 0:  # 保留原格式
                extension = original_extension
            elif format_option == 1:  # 导出为JPEG
                extension = '.jpg'
            elif format_option == 2:  # 导出为PNG
                extension = '.png'
            else:
                extension = original_extension
            
            # 根据导出设置生成文件名
            naming_rule = export_settings.get('naming_rule', 'original')
            if naming_rule == 'original':  # 保留原文件名
                output_file_name = f"{base_name}{extension}"
            elif naming_rule == 'prefix':  # 添加自定义前缀
                prefix = export_settings.get('prefix_suffix', 'wm_')
                output_file_name = f"{prefix}{base_name}{extension}"
            elif naming_rule == 'suffix':  # 添加自定义后缀
                suffix = export_settings.get('prefix_suffix', '_watermarked')
                output_file_name = f"{base_name}{suffix}{extension}"
            else:
                output_file_name = f"{base_name}{extension}"
            
            output_path = os.path.join(output_dir, output_file_name)
            
            try:
                # 调用封装的单个图片导出函数
                success, error_msg = self._export_single_image(image_path, watermark_settings, output_path, export_settings)
                if success:
                    success_count += 1
                else:
                    failed_images.append(os.path.basename(image_path))
            except Exception as e:
                failed_images.append(os.path.basename(image_path))
                logging.error(f"导出图片 {image_path} 失败: {str(e)}")
        
        # 关闭进度对话框
        progress_dialog.close()
        
        # 显示导出结果
        if failed_images:
            result_msg = f"成功导出 {success_count} 张图片。\n失败 {len(failed_images)} 张图片:\n" + "\n".join(failed_images[:5])
            if len(failed_images) > 5:
                result_msg += f"\n...以及其他 {len(failed_images) - 5} 张图片"
            QMessageBox.warning(self, "导出完成", result_msg)
        else:
            QMessageBox.information(self, "导出完成", f"所有图片已成功导出到:\n{output_dir}")

    def show_startup_settings(self):
        """显示启动设置对话框"""
        # 显示启动设置对话框
        startup_dialog = StartupSettingsDialog(self.config_manager, self)
        if startup_dialog.exec_() == QDialog.Accepted:
            selected_option = startup_dialog.get_selected_option()
            if selected_option == "load_last":
                # 加载上一次的水印设置
                last_settings = self.config_manager.get_last_watermark_settings()
                if last_settings:
                    self.load_watermark_template(last_settings.get('type', 'text'), last_settings)
            elif selected_option == "load_default":
                # 加载默认模板
                default_template = self.config_manager.get_default_template()
                if default_template and "settings" in default_template:
                    # 直接使用从get_default_template返回的settings
                    self.load_watermark_template(default_template['type'], default_template['settings'])
            elif selected_option == "template_manager":
                # 用户选择了模板管理，打开模板管理对话框
                self.show_template_manager()
        else:
            # 用户取消了对话框，检查是否需要显示启动设置对话框
            if self.config_manager.get_load_last_settings():
                # 加载上一次的水印设置
                last_settings = self.config_manager.get_last_watermark_settings()
                if last_settings:
                    self.load_watermark_template(last_settings.get('type', 'text'), last_settings)
            else:
                # 加载默认模板
                default_template = self.config_manager.get_default_template()
                if default_template and "settings" in default_template:
                    # 直接使用从get_default_template返回的settings
                    self.load_watermark_template(default_template['type'], default_template['settings'])

    def show_template_manager(self):
        """显示模板管理对话框"""
        # 获取当前水印设置
        current_watermark_settings = self.get_current_watermark_settings_for_template()
        
        # 创建模板管理对话框
        template_dialog = TemplateManagerDialog(
            self.config_manager,
            self, 
            self.watermark_type, 
            current_watermark_settings
        )
        template_dialog.exec_()

    def get_current_watermark_settings_for_template(self):
        """获取当前水印设置，用于保存模板"""
        if self.watermark_type == "text" and self.text_watermark_widget:
            watermark_settings = self.text_watermark_widget.get_watermark_settings()
            watermark_settings['watermark_type'] = 'text'
        elif self.watermark_type == "image" and self.image_watermark_widget:
            watermark_settings = self.image_watermark_widget.get_watermark_settings()
            watermark_settings['watermark_type'] = 'image'
        else:
            watermark_settings = {}
        
        # 需要将QColor对象转换为字符串格式，以便JSON序列化
        if watermark_settings:
            # 处理主颜色
            if isinstance(watermark_settings.get('color'), QColor):
                watermark_settings['color'] = watermark_settings['color'].name()
            
            # 处理描边颜色
            if isinstance(watermark_settings.get('outline_color'), QColor):
                watermark_settings['outline_color'] = watermark_settings['outline_color'].name()
            
            # 处理阴影颜色
            if isinstance(watermark_settings.get('shadow_color'), QColor):
                watermark_settings['shadow_color'] = watermark_settings['shadow_color'].name()
        
        return watermark_settings

    def load_watermark_template(self, template_type, template_settings):
        """加载水印模板"""
        # 创建并显示模态提示对话框
        progress_dialog = QProgressDialog("正在进行模板水印渲染...", None, 0, 0, self)
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setWindowTitle("请稍候")
        progress_dialog.show()
        
        try:
            # 处理事件队列，确保对话框显示
            QApplication.processEvents()
            
            # 保存当前模板信息，以便在导入新图片时重新应用
            self._current_template_type = template_type
            self._current_template_settings = template_settings
            
            # 切换到对应的水印类型
            self.switch_watermark_type(template_type)
            
            # 应用模板设置到UI控件
            if template_type == "text" and self.text_watermark_widget:
                self.text_watermark_widget.set_watermark_settings(template_settings)
            elif template_type == "image" and self.image_watermark_widget:
                self.image_watermark_widget.set_watermark_settings(template_settings)
            
            # 为所有图片应用模板设置
            all_image_paths = self.image_manager.get_all_image_paths()
            for i, image_path in enumerate(all_image_paths):
                # 获取该图片当前的水印设置
                current_watermark_settings = self.image_manager.get_watermark_settings(image_path)
                
                # 如果没有当前设置，创建一个空字典
                if not current_watermark_settings:
                    current_watermark_settings = {}
                
                # 创建模板设置的深拷贝，确保不会修改原始模板
                import copy
                template_settings_copy = copy.deepcopy(template_settings)
                
                # 将模板设置的所有键值对写入到当前设置中
                for key, value in template_settings_copy.items():
                    current_watermark_settings[key] = value
                
                # 确保位置信息正确处理
                if "position" in current_watermark_settings:
                    # 如果position是预定义的字符串位置（如"center"），保持不变
                    # 如果是坐标列表，则确保是元组格式
                    if isinstance(current_watermark_settings["position"], list):
                        current_watermark_settings["position"] = tuple(current_watermark_settings["position"])
                
                # 为图片设置更新后的水印设置
                self.image_manager.set_watermark_settings(image_path, current_watermark_settings)
                # 重置水印位置初始化标志，确保水印位置会被重新计算
                self.image_manager.set_watermark_position_initialized(image_path, False)
                
                print(f"已将模板信息写入到图片 {os.path.basename(image_path)} 的水印设置中")
                
                # 为每个图片执行一次image_selected操作，确保水印设置正确应用
                self.on_image_selected(i)
            
            # 更新当前图片的水印设置
            self.update_watermark_settings_from_current_widget()
            
            # 重置预览缓存，强制重新生成预览图像
            self.last_preview_settings = None
            self.last_preview_image = None
            
            # 更新预览
            current_image_path = self.image_manager.get_current_image_path()
            if current_image_path:
                self.update_preview_with_watermark()
            
            # 保存当前水印设置
            self.config_manager.set_last_watermark_settings(template_settings)
        finally:
            # 关闭进度对话框
            progress_dialog.close()