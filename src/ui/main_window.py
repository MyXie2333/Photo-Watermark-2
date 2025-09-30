#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口类 - 实现三栏布局
"""

import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QSplitter, QLabel, QPushButton, QMenuBar, QMenu, 
                             QStatusBar, QAction, QFileDialog, QMessageBox, QScrollArea)
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
    from config_manager import ConfigManager
    from ui.text_watermark_widget import TextWatermarkWidget
    from ui.image_watermark_widget import ImageWatermarkWidget
    from watermark_drag_manager import WatermarkDragManager
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
        self.config_manager = ConfigManager()
        
        # 初始化水印渲染器
        self.watermark_renderer = WatermarkRenderer()
        
        # 当前水印设置（用于UI显示和临时预览）
        self.current_watermark_settings = {}
        
        # 初始化缩放相关变量
        self.current_scale = 1.0
        
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
        
        self.setup_ui()
        
        # 初始化水印拖拽管理器
        self.drag_manager = WatermarkDragManager(self.preview_widget)
        self.drag_manager.set_watermark_widgets(self.text_watermark_widget, self.image_watermark_widget)
        
        # 设置水印设置回调函数
        self.drag_manager.set_watermark_settings_callback(self._get_current_watermark_settings)
        
        self.setup_connections()
        
    def _get_current_watermark_settings(self):
        """
        获取当前水印设置的内部方法，用于WatermarkDragManager的回调
        """
        current_image_path = self.image_manager.get_current_image_path()
        if current_image_path:
            return self.image_manager.get_current_watermark_settings()
        return {}
        
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
        
        # 启用拖拽功能
        self.preview_widget.setAcceptDrops(True)
        self.preview_widget.dragEnterEvent = self.dragEnterEvent
        self.preview_widget.dropEvent = self.dropEvent
        
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
        
        # 缩放比例显示
        scale_layout = QHBoxLayout()
        scale_layout.addStretch()
        
        self.scale_label = QLabel("缩放比例: 100%")
        self.scale_label.setStyleSheet("font-size: 12px; color: #666; margin: 5px;")
        scale_layout.addWidget(self.scale_label)
        
        scale_layout.addStretch()
        layout.addLayout(scale_layout)
        
        # 坐标显示区域
        coord_layout = QHBoxLayout()
        coord_layout.addStretch()
        
        self.mouse_coord_label = QLabel("鼠标坐标: (0, 0)")
        self.mouse_coord_label.setStyleSheet("font-size: 12px; color: #666; margin: 5px;")
        coord_layout.addWidget(self.mouse_coord_label)
        
        coord_layout.addSpacing(20)
        
        self.watermark_coord_label = QLabel("水印坐标: (0, 0)")
        self.watermark_coord_label.setStyleSheet("font-size: 12px; color: #666; margin: 5px;")
        coord_layout.addWidget(self.watermark_coord_label)
        
        coord_layout.addStretch()
        layout.addLayout(coord_layout)
        
        # 图片信息显示区域
        image_info_layout = QHBoxLayout()
        image_info_layout.addStretch()
        
        self.original_size_label = QLabel("原图尺寸: 0x0")
        self.original_size_label.setStyleSheet("font-size: 12px; color: #666; margin: 5px;")
        image_info_layout.addWidget(self.original_size_label)
        
        image_info_layout.addSpacing(20)
        
        self.compressed_size_label = QLabel("压缩尺寸: 0x0")
        self.compressed_size_label.setStyleSheet("font-size: 12px; color: #666; margin: 5px;")
        image_info_layout.addWidget(self.compressed_size_label)
        
        image_info_layout.addSpacing(20)
        
        self.preview_size_label = QLabel("预览尺寸: 0x0")
        self.preview_size_label.setStyleSheet("font-size: 12px; color: #666; margin: 5px;")
        image_info_layout.addWidget(self.preview_size_label)
        
        image_info_layout.addSpacing(20)
        
        self.compression_ratio_label = QLabel("压缩比例: 1.00")
        self.compression_ratio_label.setStyleSheet("font-size: 12px; color: #666; margin: 5px;")
        image_info_layout.addWidget(self.compression_ratio_label)
        
        image_info_layout.addSpacing(20)
        
        self.preview_scale_label = QLabel("预览缩放比例: 1.00")
        self.preview_scale_label.setStyleSheet("font-size: 12px; color: #666; margin: 5px;")
        image_info_layout.addWidget(self.preview_scale_label)
        
        image_info_layout.addStretch()
        layout.addLayout(image_info_layout)
        
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
        self.import_folder_button.clicked.connect(self.import_folder)
        
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
        self.text_watermark_widget.set_default_watermark.connect(self.on_set_default_watermark)
        self.text_watermark_widget.font_switch_notification.connect(self.on_font_switch_notification)
        
        # 图片水印设置信号连接
        if self.image_watermark_widget:
            self.image_watermark_widget.watermark_changed.connect(self.on_watermark_changed)
            self.image_watermark_widget.set_default_watermark.connect(self.on_set_default_watermark)
        
        # 水印拖拽管理器回调函数设置
        self.drag_manager.set_position_changed_callback(self.on_watermark_position_changed)
        
        # 菜单动作
        self.open_action.triggered.connect(self.import_images)
        self.open_folder_action.triggered.connect(self.import_folder)
        self.export_action.triggered.connect(self.export_image)
        self.exit_action.triggered.connect(self.close)
        self.about_action.triggered.connect(self.show_about)
        
        # 视图菜单
        self.zoom_in_action.triggered.connect(self.zoom_in)
        self.zoom_out_action.triggered.connect(self.zoom_out)
        self.fit_action.triggered.connect(self.fit_to_window)
        
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
            
            self.config_manager.set_watermark_defaults(config_watermark_settings)
    
    def on_watermark_changed(self):
        """水印设置发生变化"""
        self.update_watermark_settings_from_current_widget()
        
        # 更新预览
        current_image_path = self.image_manager.get_current_image_path()
        if current_image_path:
            self.update_preview_with_watermark()
            
    def on_watermark_position_changed(self, x, y):
        """处理水印位置变化信号"""
        # 获取当前图片路径
        current_image_path = self.image_manager.get_current_image_path()
        if current_image_path:
            # 获取当前水印设置
            current_watermark_settings = self.image_manager.get_watermark_settings(current_image_path)
            
            # 使用update_position函数统一处理position更新
            self.update_position((x, y), current_watermark_settings)
            
    def on_set_default_watermark(self):
        """为当前图片设置默认水印"""
        current_image_path = self.image_manager.get_current_image_path()
        if current_image_path:
            # 获取当前图片的水印设置
            current_watermark_settings = self.image_manager.get_watermark_settings(current_image_path)
            
            # 如果当前图片没有水印设置，则为其设置默认水印
            if not current_watermark_settings:
                # 获取全局默认水印设置
                global_default_settings = self.config_manager.get_watermark_defaults()
                
                # 将颜色字符串转换为QColor对象
                if "color" in global_default_settings and isinstance(global_default_settings["color"], str):
                    global_default_settings["color"] = QColor(global_default_settings["color"])
                
                # 为当前图片设置默认水印
                self.image_manager.set_watermark_settings(current_image_path, global_default_settings)
                
                # 更新文本水印组件显示当前图片的水印设置（正常样式）
                self.text_watermark_widget.set_watermark_settings(global_default_settings)
                
                # 更新预览
                self.update_preview_with_watermark()
                
                print(f"为图片设置默认水印: {current_image_path}")
                
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
            if self.current_scale != 1.0:
                # 使用原始图片尺寸计算缩放后的尺寸
                original_width = self.original_pixmap.width()
                original_height = self.original_pixmap.height()
                scaled_width = int(original_width * self.current_scale)
                scaled_height = int(original_height * self.current_scale)
                
                # 缩放水印预览图片到目标尺寸
                pixmap = pixmap.scaled(scaled_width, scaled_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # 在预览图片上绘制坐标格点
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
            result = self.image_manager.load_multiple_images(file_paths)
            
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
                    self.status_label.setText(f"所有选中的图片都已存在，未导入新图片")
            else:
                QMessageBox.warning(self, "导入失败", "没有找到有效的图片文件")
                
    def import_folder(self):
        """导入文件夹中的图片"""
        folder_path = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        
        if folder_path:
            result = self.image_manager.load_folder_images(folder_path)
            
            if result is True:
                # 成功导入新图片
                count = self.image_manager.get_image_count()
                self.status_label.setText(f"已导入文件夹中的图片，当前共 {count} 张")
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
                    self.status_label.setText(f"文件夹中的所有图片都已存在，未导入新图片")
            else:
                QMessageBox.warning(self, "导入失败", "文件夹中没有找到有效的图片文件")
                
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
                        global_default_settings["font_size"] = 24
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
        self.mouse_coord_label.setText("鼠标坐标: (0, 0)")
        # 水印坐标显示已在update_preview_with_watermark中更新
        
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
            self.scale_label.setText(f"缩放比例: {scale_percent}%")
            
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
                result = self.image_manager.load_multiple_images(file_paths)
                
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
                         
    

    


        

        
    def update_mouse_coordinates(self, event):
        """更新鼠标坐标显示"""
        if self.original_pixmap and self.image_manager.get_current_image_path():
            # 获取鼠标在预览图上的位置
            mouse_x = event.pos().x()
            mouse_y = event.pos().y()
            
            # 获取预览图片的实际尺寸
            if hasattr(self, 'preview_widget') and self.preview_widget.pixmap():
                preview_pixmap = self.preview_widget.pixmap()
                display_width = preview_pixmap.width()
                display_height = preview_pixmap.height()
                
                # 获取原始图片尺寸
                original_width = self.original_pixmap.width()
                original_height = self.original_pixmap.height()
                
                # 计算鼠标在原始图片上的坐标
                if display_width > 0 and display_height > 0:
                    # 计算预览图相对于原始图片的缩放比例
                    preview_scale_x = original_width / display_width
                    preview_scale_y = original_height / display_height
                    
                    # 计算鼠标在原始图片上的坐标，直接存储为整数
                    original_x = int(mouse_x * preview_scale_x)
                    original_y = int(mouse_y * preview_scale_y)
                    
                    # 更新鼠标坐标显示
                    self.mouse_coord_label.setText(f"鼠标坐标: ({original_x}, {original_y})")
                else:
                    self.mouse_coord_label.setText("鼠标坐标: (0, 0)")
            else:
                self.mouse_coord_label.setText("鼠标坐标: (0, 0)")
        else:
            self.mouse_coord_label.setText("鼠标坐标: (0, 0)")
            
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
                    self.watermark_coord_label.setText(f"水印坐标: ({watermark_x}, {watermark_y})")
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
                        # 水印位置已经是基于原图坐标系的整数，直接显示
                        self.watermark_coord_label.setText(f"水印坐标: ({watermark_x}, {watermark_y})")
                    else:
                        self.watermark_coord_label.setText("水印坐标: (0, 0)")
                else:
                    self.watermark_coord_label.setText("水印坐标: (0, 0)")
            # 图片水印处理
            elif current_watermark_settings.get("image_path"):
                # 优先使用watermark_x和watermark_y
                if "watermark_x" in current_watermark_settings and "watermark_y" in current_watermark_settings:
                    watermark_x = int(current_watermark_settings["watermark_x"])
                    watermark_y = int(current_watermark_settings["watermark_y"])
                    self.watermark_coord_label.setText(f"水印坐标: ({watermark_x}, {watermark_y})")
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
                        # 水印位置已经是基于原图坐标系的整数，直接显示
                        self.watermark_coord_label.setText(f"水印坐标: ({watermark_x}, {watermark_y})")
                    else:
                        self.watermark_coord_label.setText("水印坐标: (0, 0)")
                else:
                    self.watermark_coord_label.setText("水印坐标: (0, 0)")
            else:
                self.watermark_coord_label.setText("水印坐标: (0, 0)")
        else:
            self.watermark_coord_label.setText("水印坐标: (0, 0)")
    
    def update_position(self, new_position, current_watermark_settings=None):
        """
        统一更新position的函数，确保每次position变化时都更新watermark_x和watermark_y
        
        Args:
            new_position: 新的位置，可以是元组(x, y)或相对位置字符串
            current_watermark_settings: 当前水印设置，如果为None则从image_manager获取
        """
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
            current_watermark_settings["watermark_x"] = int(new_position[0])
            current_watermark_settings["watermark_y"] = int(new_position[1])
            print(f"[DEBUG] 更新position和坐标: position={new_position}, watermark_x={current_watermark_settings['watermark_x']}, watermark_y={current_watermark_settings['watermark_y']}")
        
        # 保存更新后的水印设置
        self.image_manager.set_watermark_settings(current_image_path, current_watermark_settings)
        
        # 更新文本水印组件
        self.text_watermark_widget.set_watermark_settings(current_watermark_settings)
        
        # 更新预览（这会自动调用update_watermark_coordinates）
        self.update_preview_with_watermark()
        
        return current_watermark_settings
            
    def update_image_info_display(self):
        """更新图片信息显示"""
        if self.original_pixmap and self.image_manager.get_current_image_path():
            # 获取原始图片尺寸
            original_width = self.original_pixmap.width()
            original_height = self.original_pixmap.height()
            
            # 更新原图尺寸显示
            self.original_size_label.setText(f"原图尺寸: {original_width}x{original_height}")
            
            # 获取压缩比例和压缩尺寸
            compression_scale = 1.0
            compressed_width = original_width
            compressed_height = original_height
            
            if hasattr(self, 'preview_ratio_info') and self.preview_ratio_info:
                compression_scale = self.preview_ratio_info.get('scale_factor', 1.0)
                compressed_width = self.preview_ratio_info.get('preview_width', original_width)
                compressed_height = self.preview_ratio_info.get('preview_height', original_height)
            
            # 更新压缩尺寸显示
            self.compressed_size_label.setText(f"压缩尺寸: {compressed_width}x{compressed_height}")
            
            # 计算预览尺寸（考虑预览缩放比例）
            preview_width = int(original_width * self.current_scale)
            preview_height = int(original_height * self.current_scale)
            
            # 更新预览尺寸显示
            self.preview_size_label.setText(f"预览尺寸: {preview_width}x{preview_height}")
            
            # 更新压缩比例显示
            self.compression_ratio_label.setText(f"压缩比例: {compression_scale:.2f}")
            
            # 更新预览缩放比例显示
            self.preview_scale_label.setText(f"预览缩放比例: {self.current_scale:.2f}")
        else:
            # 如果没有图片，重置所有显示
            self.original_size_label.setText("原图尺寸: 0x0")
            self.compressed_size_label.setText("压缩尺寸: 0x0")
            self.preview_size_label.setText("预览尺寸: 0x0")
            self.compression_ratio_label.setText("压缩比例: 1.00")
            self.preview_scale_label.setText("预览缩放比例: 1.00")
        

        
    def check_watermark_position(self, watermark_settings, original_width, original_height):
        """检查水印位置是否超出边界，使用PIL/Pillow的ImageDraw.textbbox()函数获取精确的边界框
        
        此方法通过创建一个临时图像并使用PIL/Pillow的ImageDraw.textbbox()函数来获取文本水印的实际边界框，
        从而更准确地判断水印是否超出图片边界。这种方法比估算文本尺寸更加精确，考虑了字体、大小、
        样式（粗体、斜体）和旋转对水印尺寸的实际影响。
        
        Args:
            watermark_settings (dict): 水印设置，包含文本、位置、字体等信息
            original_width (int): 原始图片宽度
            original_height (int): 原始图片高度
        """
        try:
            # 获取水印文本
            text = watermark_settings.get("text", "")
            if not text:
                self.watermark_warning_label.setVisible(False)
                return
            
            # 获取水印位置
            watermark_x = watermark_settings.get("watermark_x", 0)
            watermark_y = watermark_settings.get("watermark_y", 0)
            
            # 获取字体大小和其他相关设置
            font_size = watermark_settings.get("font_size", 24)
            font_family = watermark_settings.get("font_family", "Arial")
            font_bold = watermark_settings.get("font_bold", False)
            font_italic = watermark_settings.get("font_italic", False)
            rotation = watermark_settings.get("rotation", 0)
            
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
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # 考虑旋转对边界的影响
                if rotation != 0:
                    import math
                    # 计算旋转后的边界框
                    angle_rad = math.radians(abs(rotation))
                    rotated_width = abs(text_width * math.cos(angle_rad)) + abs(text_height * math.sin(angle_rad))
                    rotated_height = abs(text_width * math.sin(angle_rad)) + abs(text_height * math.cos(angle_rad))
                    text_width, text_height = rotated_width, rotated_height
                
                # 计算水印边界框的四个角坐标（基于水印中心点）
                # 水印中心点是(watermark_x, watermark_y)，边界框的左上角是(bbox[0], bbox[1])
                # 我们需要计算边界框的四个角在图像上的实际坐标
                left = watermark_x-25
                top = watermark_y
                right = watermark_x + text_width
                bottom = watermark_y + text_height
                
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
                if is_out_of_bounds and (watermark_x != 0 or watermark_y != 0):
                    self.watermark_warning_label.setVisible(True)
                else:
                    self.watermark_warning_label.setVisible(False)
                    
            except Exception as e:
                print(f"使用PIL获取文本边界框时出错: {e}")
                # 如果PIL方法失败，回退到原始的估算方法
                self._fallback_check_watermark_position(
                    watermark_settings, original_width, original_height,
                    text, watermark_x, watermark_y, font_size, font_family,
                    font_bold, font_italic, rotation
                )
                
        except Exception as e:
            print(f"检查水印位置时出错: {e}")
            self.watermark_warning_label.setVisible(False)
            
    def _fallback_check_watermark_position(self, watermark_settings, original_width, original_height,
                                          text, watermark_x, watermark_y, font_size, font_family,
                                          font_bold, font_italic, rotation):
        """回退的水印位置检查方法，使用估算的文本尺寸
        
        当PIL/Pillow的textbbox方法不可用时，使用此方法进行水印位置检查。
        
        Args:
            watermark_settings (dict): 水印设置
            original_width (int): 原始图片宽度
            original_height (int): 原始图片高度
            text (str): 水印文本
            watermark_x (int): 水印X坐标
            watermark_y (int): 水印Y坐标
            font_size (int): 字体大小
            font_family (str): 字体名称
            font_bold (bool): 是否粗体
            font_italic (bool): 是否斜体
            rotation (int): 旋转角度
        """
        # 更精确地估算文本尺寸
        # 考虑到不同字体和样式的影响
        char_count = len(text)
        
        # 基于字体大小估算文本宽度和高度
        # 对于中文字体，每个字符大约占用font_size像素宽度
        # 对于英文字体，平均字符宽度约为font_size * 0.6
        if self._contains_chinese(text):
            # 中文文本使用更保守的估算，确保足够的空间
            text_width = char_count * font_size * 1.5  # 增加50%的宽度以确保安全
        else:
            # 英文文本使用更紧凑的估算
            text_width = char_count * font_size  # 稍微增加英文文本的宽度估算
        
        # 文本高度估算，增加额外的空间以确保安全
        text_height = font_size * 2  # 增加行间距的估算
        
        # 考虑粗体和斜体对尺寸的影响
        if font_bold:
            text_width *= 1.05  # 增加粗体对宽度的影响
            text_height *= 1.05  # 增加粗体对高度的影响
        
        if font_italic:
            text_width *= 1.05  # 增加斜体对宽度的影响
                
        # 考虑旋转对边界的影响
        if rotation != 0:
            import math
            # 计算旋转后的边界框
            angle_rad = math.radians(abs(rotation))
            rotated_width = abs(text_width * math.cos(angle_rad)) + abs(text_height * math.sin(angle_rad))
            rotated_height = abs(text_width * math.sin(angle_rad)) + abs(text_height * math.cos(angle_rad))
            text_width, text_height = rotated_width, rotated_height
        
        # 计算水印边界（基于水印中心点）
        left_bound = watermark_x - text_width*0.2
        right_bound = watermark_x + text_width
        top_bound = watermark_y - text_height*0.2
        bottom_bound = watermark_y + text_height
        
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
            (watermark_x != 0 or watermark_y != 0):
            self.watermark_warning_label.setVisible(True)
        else:
            self.watermark_warning_label.setVisible(False)
            
    def _contains_chinese(self, text):
        """检查文本是否包含中文字符"""
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False
    
    def export_image(self):
        """导出当前图片，应用水印效果"""
        # 获取当前图片路径
        current_image_path = self.image_manager.get_current_image_path()
        if not current_image_path:
            QMessageBox.warning(self, "警告", "请先选择要导出的图片")
            return
        
        # 获取当前图片的水印设置
        watermark_settings = self.image_manager.get_watermark_settings(current_image_path)
        
        # 打开文件保存对话框
        file_name, _ = QFileDialog.getSaveFileName(
            self, "导出图片", 
            os.path.join(os.path.dirname(current_image_path), 
                        f"{os.path.splitext(os.path.basename(current_image_path))[0]}_watermark{os.path.splitext(current_image_path)[1]}"),
            "图片文件 (*.jpg *.jpeg *.png *.bmp);;所有文件 (*)"
        )
        
        if not file_name:
            return  # 用户取消了保存
        
        try:
            # 加载原始图片
            original_image = PILImage.open(current_image_path)
            
            # 根据水印类型选择渲染方法
            watermark_type = watermark_settings.get('watermark_type', 'text')
            if watermark_type == 'text':
                # 渲染文本水印
                watermarked_image = self.watermark_renderer.render_text_watermark(original_image, watermark_settings)
            elif watermark_type == 'image':
                # 渲染图片水印
                watermarked_image = self.watermark_renderer.render_image_watermark(original_image, watermark_settings)
            else:
                # 默认使用文本水印
                watermarked_image = self.watermark_renderer.render_text_watermark(original_image, watermark_settings)
            
            # 保存渲染后的图片
            watermarked_image.save(file_name)
            
            # 显示导出成功提示
            QMessageBox.information(self, "成功", f"图片已成功导出到:\n{file_name}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出图片时出错:\n{str(e)}")
            logging.error(f"导出图片失败: {str(e)}")


if __name__ == "__main__":
    # 测试代码
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())