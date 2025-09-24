#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Photo Watermark 2 - 主程序入口
Windows图形化水印软件
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

# 添加src目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow

class PhotoWatermarkApp:
    """应用程序主类"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.main_window = None
        
        # 设置应用程序属性
        self.app.setApplicationName("Photo Watermark 2")
        self.app.setApplicationVersion("1.0.0")
        self.app.setOrganizationName("PhotoWatermark")
        
    def setup_ui(self):
        """设置用户界面"""
        try:
            self.main_window = MainWindow()
            self.main_window.show()
            return True
        except Exception as e:
            QMessageBox.critical(None, "启动错误", f"应用程序启动失败:\n{str(e)}")
            return False
    
    def run(self):
        """运行应用程序"""
        if self.setup_ui():
            return self.app.exec_()
        else:
            return 1

def main():
    """主函数"""
    # 设置高DPI支持
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # 创建应用程序实例
    app = PhotoWatermarkApp()
    
    # 运行应用程序
    exit_code = app.run()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()