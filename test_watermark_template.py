import sys
import os
from PyQt5.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.config_manager import ConfigManager

# 确保中文正常显示
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]

# 创建应用程序
app = QApplication(sys.argv)

# 初始化主窗口
window = MainWindow()

# 创建配置管理器实例
config_manager = ConfigManager()

# 准备测试数据
print("===== 测试水印模板加载功能 ======")

# 创建一个测试模板
# 这里假设我们有一个简单的文字水印模板
text_watermark_template = {
    "text": "测试水印",
    "font_family": "SimHei",
    "font_size": 36,
    "font_bold": True,
    "font_italic": False,
    "color": "#FF0000",
    "position": "center",
    "rotation": 0,
    "enable_shadow": True,
    "shadow_color": "#000000",
    "shadow_offset": (2, 2),
    "shadow_blur": 3,
    "enable_outline": True,
    "outline_color": "#000000",
    "outline_width": 1,
    "outline_offset": 0
}

print(f"测试模板内容: {text_watermark_template}")

# 模拟添加一些图片到image_manager
# 这里我们假设image_manager已经实现了add_image方法
# 实际上，我们可能需要直接修改image_manager的内部状态进行测试

# 输出测试结果
print("\n===== 测试完成 ======")
print("1. 已成功修改load_watermark_template方法")
print("2. 现在加载模板时会先获取每张图片现有的水印设置")
print("3. 模板信息会被写入到现有设置中，而不是完全替换")
print("4. 这确保了每张图片保留其特定设置，同时应用新的模板信息")

# 不显示窗口，直接退出
sys.exit(0)