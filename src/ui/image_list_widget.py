#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片列表组件 - 显示图片缩略图列表
使用QListWidget实现，提供更好的性能和稳定性
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QFrame, QListWidget, 
                             QListWidgetItem, QAbstractItemView)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QIcon


class ImageListWidget(QWidget):
    """图片列表组件 - 使用QListWidget实现"""
    
    image_selected = pyqtSignal(int)  # 图片选择信号
    
    def __init__(self):
        super().__init__()
        self.image_paths = []
        self.current_selected = -1
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 使用QListWidget替代自定义布局
        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.IconMode)
        self.list_widget.setIconSize(QSize(80, 80))
        self.list_widget.setResizeMode(QListWidget.Adjust)
        self.list_widget.setMovement(QListWidget.Static)
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_widget.setSpacing(5)
        self.list_widget.setGridSize(QSize(100, 100))
        
        # 设置样式
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            QListWidget::item {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 5px;
                margin: 2px;
                background-color: white;
            }
            QListWidget::item:hover {
                border: 1px solid #0078d4;
                background-color: #f0f8ff;
            }
            QListWidget::item:selected {
                border: 2px solid #0078d4;
                background-color: #e1f5fe;
            }
        """)
        
        # 连接信号
        self.list_widget.itemSelectionChanged.connect(self.on_selection_changed)
        
        layout.addWidget(self.list_widget)
        
    def add_images(self, image_paths, clear_existing=False):
        """添加图片到列表
        
        Args:
            image_paths: 图片路径列表
            clear_existing: 是否清空现有图片，默认为False（累加模式）
        """
        if clear_existing:
            self.clear_images()
        
        # 批量添加图片
        for image_path in image_paths:
            if image_path not in self.image_paths:  # 避免重复添加
                self.add_single_image(image_path)
        
        # 刷新列表显示
        self.list_widget.update()
        
    def add_single_image(self, image_path):
        """添加单个图片"""
        # 创建缩略图
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            # 缩放缩略图
            thumbnail = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon = QIcon(thumbnail)
            
            # 创建列表项
            item = QListWidgetItem()
            item.setIcon(icon)
            
            # 获取文件名
            filename = image_path.split('/')[-1].split('\\')[-1]
            item.setText(filename)
            item.setToolTip(filename)
            
            # 设置数据
            item.setData(Qt.UserRole, image_path)
            
            # 添加到列表
            self.list_widget.addItem(item)
            self.image_paths.append(image_path)
            
    def clear_images(self):
        """清空图片列表"""
        self.list_widget.clear()
        self.image_paths = []
        self.current_selected = -1
        
    def on_selection_changed(self):
        """处理选择变化"""
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            item = selected_items[0]
            index = self.list_widget.row(item)
            if index != self.current_selected:
                self.current_selected = index
                self.image_selected.emit(index)
        else:
            self.current_selected = -1
            
    def set_selected_image(self, index):
        """设置选中的图片"""
        if 0 <= index < self.list_widget.count():
            # 暂时断开信号避免递归
            self.list_widget.itemSelectionChanged.disconnect(self.on_selection_changed)
            
            # 清除当前选择
            self.list_widget.clearSelection()
            
            # 设置新选择
            item = self.list_widget.item(index)
            if item:
                item.setSelected(True)
                self.list_widget.scrollToItem(item)
                self.current_selected = index
            
            # 重新连接信号
            self.list_widget.itemSelectionChanged.connect(self.on_selection_changed)
            
    def get_selected_index(self):
        """获取当前选中的索引"""
        return self.current_selected
    
    def get_image_path(self, index):
        """获取指定索引的图片路径"""
        if 0 <= index < len(self.image_paths):
            return self.image_paths[index]
        return None
    
    def count(self):
        """获取图片数量"""
        return self.list_widget.count()


if __name__ == "__main__":
    # 测试代码
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    widget = ImageListWidget()
    widget.resize(300, 400)
    widget.show()
    
    # 添加测试图片
    test_images = [
        "test_photos/MARBLES.bmp",
        "test_photos/test1.jpg",
        "test_photos/test2.jpg",
        "test_photos/test3.png"
    ]
    widget.add_images(test_images)
    
    sys.exit(app.exec_())