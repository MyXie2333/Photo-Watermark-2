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
from PyQt5.QtGui import QIcon, QPixmap, QDragEnterEvent, QDropEvent, QImage

# 导入自定义模块
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from image_manager import ImageManager
    from ui.image_list_widget import ImageListWidget
    from watermark_renderer import WatermarkRenderer
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
        
        # 初始化水印渲染器
        self.watermark_renderer = WatermarkRenderer()
        
        # 当前水印设置（用于UI显示和临时预览）
        self.current_watermark_settings = {}
        
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
                min-height: 400px;
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
        
        # 预览滚动区域
        self.preview_scroll_area = QScrollArea()
        self.preview_scroll_area.setWidgetResizable(True)
        self.preview_scroll_area.setWidget(self.preview_widget)
        layout.addWidget(self.preview_scroll_area)
        
        # 初始化缩放相关变量
        self.current_scale = 1.0
        self.min_scale = 0.1
        self.max_scale = 5.0
        self.scale_step = 0.1
        self.user_has_zoomed = False  # 标记用户是否手动调整过缩放
        
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
        
        # 文本水印设置组件
        from ui.text_watermark_widget import TextWatermarkWidget
        self.text_watermark_widget = TextWatermarkWidget()
        layout.addWidget(self.text_watermark_widget)
        
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
        
        # 菜单动作
        self.open_action.triggered.connect(self.import_images)
        self.open_folder_action.triggered.connect(self.import_folder)
        self.exit_action.triggered.connect(self.close)
        self.about_action.triggered.connect(self.show_about)
        
        # 视图菜单
        self.zoom_in_action.triggered.connect(self.zoom_in)
        self.zoom_out_action.triggered.connect(self.zoom_out)
        self.fit_action.triggered.connect(self.fit_to_window)
        
    def on_watermark_changed(self):
        """水印设置发生变化"""
        # 获取当前水印设置
        watermark_settings = self.text_watermark_widget.get_watermark_settings()
        
        # 如果有当前图片，将水印设置应用到当前图片
        current_image_path = self.image_manager.get_current_image_path()
        if current_image_path:
            # 将水印设置保存到当前图片
            self.image_manager.set_watermark_settings(current_image_path, watermark_settings)
            
            # 更新预览
            self.update_preview_with_watermark()
            
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
            
            # 如果是第一次加载图片且用户没有手动缩放，则适应窗口
            if not self.user_has_zoomed:
                fit_scale = self.calculate_fit_scale()
                if fit_scale != self.current_scale:
                    self.current_scale = fit_scale
                    print(f"首次预览，适应窗口显示，缩放比例: {fit_scale:.2f}")
            
            # 获取当前图片的水印设置
            current_watermark_settings = self.image_manager.get_current_watermark_settings()
            
            # 检查是否有水印文本
            if current_watermark_settings.get("text"):
                # 有水印文本，生成带水印的预览
                preview_image = self.watermark_renderer.preview_watermark(
                    current_image_path, 
                    current_watermark_settings,
                    preview_size=(800, 600)  # 预览尺寸
                )
                
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
            else:
                # 没有水印文本，直接使用原始图片
                pixmap = self.original_pixmap
            
            # 应用当前缩放比例
            if self.current_scale != 1.0:
                scaled_size = pixmap.size() * self.current_scale
                pixmap = pixmap.scaled(scaled_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            self.preview_widget.setPixmap(pixmap)
            
        except Exception as e:
            print(f"更新预览失败: {e}")
            # 显示错误信息
            self.preview_widget.setText(f"预览失败: {str(e)}")
            
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
            # 使用基于水印设置的预览方法，避免循环调用
            self._update_preview_based_on_watermark()
            # 适应窗口操作后置，在图片显示后再执行
            QTimer.singleShot(100, self.fit_to_window)
        
    def on_image_selected(self, index):
        """图片列表项被选中"""
        self.image_manager.set_current_image(index)
        
        # 统一使用带水印的预览方法
        self.update_preview_with_watermark()
        
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
        
        # 获取当前图片的水印设置并更新文本水印组件
        current_image_path = self.image_manager.get_current_image_path()
        if current_image_path:
            # 获取当前图片的水印设置
            current_watermark_settings = self.image_manager.get_watermark_settings(current_image_path)
            
            # 更新文本水印组件显示当前图片的水印设置
            if current_watermark_settings:
                self.text_watermark_widget.set_watermark_settings(current_watermark_settings)
            else:
                # 如果当前图片没有水印设置，使用默认设置
                default_settings = self.text_watermark_widget.get_watermark_settings()
                self.text_watermark_widget.set_watermark_settings(default_settings)
        
        # 直接使用基于水印设置的预览方法，避免循环调用
        self._update_preview_based_on_watermark()
        
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
        if hasattr(self, 'original_pixmap') and not self.original_pixmap.isNull():
            # 计算缩放后的尺寸
            scaled_width = int(self.original_pixmap.width() * self.current_scale)
            scaled_height = int(self.original_pixmap.height() * self.current_scale)
            
            # 缩放图片
            scaled_pixmap = self.original_pixmap.scaled(
                scaled_width, 
                scaled_height, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            self.preview_widget.setPixmap(scaled_pixmap)
            print(f"应用缩放: {self.current_scale:.1f}x, 显示尺寸: {scaled_width}x{scaled_height}")
        else:
            # 如果没有original_pixmap，尝试重新加载当前图片
            self._update_preview_based_on_watermark()
            
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
    
    def fit_to_window(self):
        """适应窗口显示"""
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
            self.user_has_zoomed = False  # 重置缩放标记，允许下次切换图片时适应窗口
            self._update_preview_based_on_watermark()
            print(f"适应窗口显示，缩放比例: {fit_scale:.2f}")
            
    def zoom_in(self):
        """放大预览"""
        if hasattr(self, 'original_pixmap') and not self.original_pixmap.isNull():
            new_scale = min(self.current_scale + self.scale_step, self.max_scale)
            if new_scale != self.current_scale:
                self.current_scale = new_scale
                self.user_has_zoomed = True  # 标记用户已手动缩放
                self._update_preview_based_on_watermark()
                print(f"放大到: {self.current_scale:.1f}x")
            else:
                print("已达到最大放大倍数")
                
    def zoom_out(self):
        """缩小预览"""
        if hasattr(self, 'original_pixmap') and not self.original_pixmap.isNull():
            new_scale = max(self.current_scale - self.scale_step, self.min_scale)
            if new_scale != self.current_scale:
                self.current_scale = new_scale
                self.user_has_zoomed = True  # 标记用户已手动缩放
                self._update_preview_based_on_watermark()
                print(f"缩小到: {self.current_scale:.1f}x")
            else:
                print("已达到最小缩小倍数")
                
    def reset_zoom(self):
        """重置缩放比例"""
        self.current_scale = 1.0
        self.user_has_zoomed = True  # 标记用户已手动缩放
        self.apply_scale()
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
        
    # 缩放功能已经在前面定义，这里移除重复定义
        
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


if __name__ == "__main__":
    # 测试代码
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())