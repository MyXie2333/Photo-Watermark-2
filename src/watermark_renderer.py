#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水印渲染引擎
"""

from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import os
from PyQt5.QtGui import QColor


class WatermarkRenderer:
    """水印渲染器"""
    
    def __init__(self):
        self.font_cache = {}
        
    def render_text_watermark(self, image, watermark_settings):
        """
        渲染文本水印到图片上
        
        Args:
            image: PIL Image对象
            watermark_settings: 水印设置字典
            
        Returns:
            PIL Image对象（带水印的图片）
        """
        if not watermark_settings.get("text"):
            return image
            
        # 创建图片副本
        watermarked_image = image.copy()
        
        # 获取水印设置
        text = watermark_settings["text"]
        font_family = watermark_settings.get("font_family", "Arial")
        font_size = watermark_settings.get("font_size", 24)
        color = watermark_settings.get("color", QColor(255, 255, 255))
        opacity = watermark_settings.get("opacity", 80) / 100.0
        position = watermark_settings.get("position", "center")
        rotation = watermark_settings.get("rotation", 0)
        
        # 创建绘图对象
        draw = ImageDraw.Draw(watermarked_image, 'RGBA')
        
        # 获取字体
        font = self._get_font(font_family, font_size)
        
        # 计算文本尺寸
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 计算水印位置
        img_width, img_height = watermarked_image.size
        x, y = self._calculate_position(position, img_width, img_height, text_width, text_height)
        
        # 设置颜色和透明度
        rgba_color = (color.red(), color.green(), color.blue(), int(255 * opacity))
        
        # 绘制文本水印
        draw.text((x, y), text, font=font, fill=rgba_color)
        
        # 如果需要旋转
        if rotation != 0:
            watermarked_image = watermarked_image.rotate(-rotation, expand=True)
            # 重新计算尺寸
            img_width, img_height = watermarked_image.size
            
        return watermarked_image
    
    def _get_font(self, font_family, font_size):
        """获取字体对象"""
        font_key = f"{font_family}_{font_size}"
        
        if font_key in self.font_cache:
            return self.font_cache[font_key]
            
        # 尝试加载字体
        try:
            # 首先尝试系统字体
            font = ImageFont.truetype(font_family, font_size, encoding="utf-8")
        except OSError:
            try:
                # 尝试常见字体路径
                font_paths = [
                    "C:/Windows/Fonts/",
                    "/usr/share/fonts/",
                    "/Library/Fonts/"
                ]
                
                # 构建可能的字体文件名
                font_files = [
                    f"{font_family}.ttf",
                    f"{font_family}.ttc",
                    f"{font_family.lower()}.ttf",
                    f"{font_family.replace(' ', '')}.ttf"
                ]
                
                # 添加中文字体文件
                chinese_font_files = [
                    "simhei.ttf",  # 黑体
                    "simsun.ttc",  # 宋体
                    "msyh.ttc",   # 微软雅黑
                    "simkai.ttf",  # 楷体
                    "simfang.ttf"  # 仿宋
                ]
                
                font_found = False
                for font_path in font_paths:
                    # 首先尝试用户指定的字体
                    for font_file in font_files:
                        full_path = os.path.join(font_path, font_file)
                        if os.path.exists(full_path):
                            font = ImageFont.truetype(full_path, font_size, encoding="utf-8")
                            font_found = True
                            break
                    
                    # 如果用户指定字体没找到，尝试中文字体
                    if not font_found:
                        for chinese_font in chinese_font_files:
                            full_path = os.path.join(font_path, chinese_font)
                            if os.path.exists(full_path):
                                font = ImageFont.truetype(full_path, font_size, encoding="utf-8")
                                font_found = True
                                break
                    
                    if font_found:
                        break
                
                if not font_found:
                    # 使用支持中文的默认字体
                    try:
                        # 尝试加载支持中文的字体
                        font = ImageFont.truetype("arial.ttf", font_size, encoding="utf-8")
                    except:
                        # 最终回退到默认字体
                        font = ImageFont.load_default()
                    
            except Exception:
                # 最终回退到默认字体
                font = ImageFont.load_default()
        
        self.font_cache[font_key] = font
        return font
    
    def _calculate_position(self, position, img_width, img_height, text_width, text_height):
        """计算水印位置"""
        margin = 20  # 边距
        
        if position == "top-left":
            x = margin
            y = margin
        elif position == "top-center":
            x = (img_width - text_width) // 2
            y = margin
        elif position == "top-right":
            x = img_width - text_width - margin
            y = margin
        elif position == "middle-left":
            x = margin
            y = (img_height - text_height) // 2
        elif position == "center":
            x = (img_width - text_width) // 2
            y = (img_height - text_height) // 2
        elif position == "middle-right":
            x = img_width - text_width - margin
            y = (img_height - text_height) // 2
        elif position == "bottom-left":
            x = margin
            y = img_height - text_height - margin
        elif position == "bottom-center":
            x = (img_width - text_width) // 2
            y = img_height - text_height - margin
        elif position == "bottom-right":
            x = img_width - text_width - margin
            y = img_height - text_height - margin
        else:
            x = margin
            y = margin
            
        return x, y
    
    def preview_watermark(self, image_path, watermark_settings, preview_size=(400, 300)):
        """
        预览水印效果
        
        Args:
            image_path: 图片路径
            watermark_settings: 水印设置
            preview_size: 预览尺寸
            
        Returns:
            PIL Image对象（预览图片）
        """
        try:
            # 加载原始图片
            original_image = Image.open(image_path)
            
            # 调整图片大小用于预览
            original_image.thumbnail(preview_size, Image.Resampling.LANCZOS)
            
            # 应用水印
            watermarked_image = self.render_text_watermark(original_image, watermark_settings)
            
            return watermarked_image
            
        except Exception as e:
            print(f"预览水印失败: {e}")
            # 创建错误预览图片
            error_image = Image.new('RGB', preview_size, (255, 255, 255))
            draw = ImageDraw.Draw(error_image)
            draw.text((10, 10), f"预览失败: {str(e)}", fill=(255, 0, 0))
            return error_image