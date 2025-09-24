#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片列表组件 - 显示图片缩略图列表
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap


class ImageListItem(QFrame):
    """单个图片列表项"""
    
    clicked = pyqtSignal(int)  # 点击信号
    
    def __init__(self, image_path, index, thumbnail_size=(80, 80)):
        super().__init__()
        self.image_path = image_path
        self.index = index
        self.thumbnail_size = thumbnail_size
        self.is_selected = False
        
        self.setup_ui()
        self.setup_style()
        
    def setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 缩略图
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(*self.thumbnail_size)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setStyleSheet("border: 1px solid #ddd;")
        
        # 加载缩略图
        pixmap = QPixmap(self.image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                self.thumbnail_size[0] - 10, 
                self.thumbnail_size[1] - 10,
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.thumbnail_label.setPixmap(scaled_pixmap)
        else:
            self.thumbnail_label.setText("加载失败")
        
        # 文件名
        filename = self.image_path.split('/')[-1].split('\\')[-1]
        self.name_label = QLabel(filename)
        self.name_label.setStyleSheet("font-size: 10px;")
        self.name_label.setWordWrap(True)
        
        layout.addWidget(self.thumbnail_label)
        layout.addWidget(self.name_label)
        layout.addStretch()
        
        # 设置点击事件
        self.setCursor(Qt.PointingHandCursor)
        
    def setup_style(self):
        """设置样式"""
        self.setStyleSheet("""
            ImageListItem {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: white;
                margin: 2px;
            }
            ImageListItem:hover {
                border: 1px solid #0078d4;
                background-color: #f0f8ff;
            }
            ImageListItem[selected="true"] {
                border: 2px solid #0078d4;
                background-color: #e1f5fe;
            }
        """)
        
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.index)
            event.accept()
        else:
            super().mousePressEvent(event)
            
    def set_selected(self, selected):
        """设置选中状态"""
        self.is_selected = selected
        if selected:
            self.setProperty("selected", "true")
        else:
            self.setProperty("selected", "false")
        self.style().unpolish(self)
        self.style().polish(self)


class ImageListWidget(QWidget):
    """图片列表组件"""
    
    image_selected = pyqtSignal(int)  # 图片选择信号
    
    def __init__(self):
        super().__init__()
        self.image_items = []
        self.current_selected = -1
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 滚动区域内容
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(5, 5, 5, 5)
        self.scroll_layout.setSpacing(5)
        self.scroll_layout.addStretch()
        
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)
        
    def add_images(self, image_paths):
        """添加图片到列表"""
        self.clear_images()
        
        for i, image_path in enumerate(image_paths):
            item = ImageListItem(image_path, i)
            item.clicked.connect(self.on_item_clicked)
            self.image_items.append(item)
            self.scroll_layout.insertWidget(i, item)
            
    def clear_images(self):
        """清空图片列表"""
        for item in self.image_items:
            item.deleteLater()
        self.image_items = []
        self.current_selected = -1
        
    def on_item_clicked(self, index):
        """处理项目点击"""
        if 0 <= index < len(self.image_items):
            # 取消之前的选择
            if self.current_selected >= 0:
                self.image_items[self.current_selected].set_selected(False)
                
            # 设置新的选择
            self.image_items[index].set_selected(True)
            self.current_selected = index
            
            # 发射信号
            self.image_selected.emit(index)
            
    def set_selected_image(self, index):
        """设置选中的图片"""
        if 0 <= index < len(self.image_items):
            self.on_item_clicked(index)
            
    def get_selected_index(self):
        """获取当前选中的索引"""
        return self.current_selected


if __name__ == "__main__":
    # 测试代码
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    widget = ImageListWidget()
    widget.show()
    sys.exit(app.exec_())