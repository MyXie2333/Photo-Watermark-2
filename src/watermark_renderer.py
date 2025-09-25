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
        font_bold = watermark_settings.get("font_bold", False)
        font_italic = watermark_settings.get("font_italic", False)
        color = watermark_settings.get("color", QColor(255, 255, 255))
        opacity = watermark_settings.get("opacity", 80) / 100.0
        position = watermark_settings.get("position", "center")
        rotation = watermark_settings.get("rotation", 0)
        
        # 创建绘图对象
        draw = ImageDraw.Draw(watermarked_image, 'RGBA')
        
        # 获取字体（传递文本内容用于智能字体选择）
        font = self._get_font(font_family, font_size, text, font_bold, font_italic)
        
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
    
    def _get_font(self, font_family, font_size, text="", bold=False, italic=False):
        """获取字体对象
        
        Args:
            font_family: 字体名称
            font_size: 字体大小
            text: 要渲染的文本内容（用于检测是否需要中文字体支持）
            bold: 是否粗体
            italic: 是否斜体
        """
        font_key = f"{font_family}_{font_size}_{bold}_{italic}"
        
        if font_key in self.font_cache:
            return self.font_cache[font_key]
            
        # 检测是否需要中文字体支持
        needs_chinese_font = self._contains_chinese(text)
        
        # 智能字体选择逻辑
        if needs_chinese_font:
            # 如果文本包含中文（包括同时包含中英文字符的情况），直接使用中文字体
            # 这样可以确保中文字符正确显示，同时英文字符也能正常显示
            font = self._get_chinese_font(font_size, bold, italic)
            self.font_cache[font_key] = font
            return font
        else:
            # 如果文本不包含中文，使用用户选择的字体
            # 首先尝试加载带样式的字体
            font = self._get_english_font(font_family, font_size, bold, italic)
            if font:
                self.font_cache[font_key] = font
                return font
            
            # 如果加载带样式的字体失败，尝试加载常规字体
            try:
                font = ImageFont.truetype(font_family, font_size, encoding="utf-8")
                self.font_cache[font_key] = font
                return font
            except OSError:
                # 如果用户指定的字体不存在，回退到默认字体
                return ImageFont.load_default()
    
    def _contains_chinese(self, text):
        """检测文本是否包含中文字符"""
        if not text:
            return False
        
        # 中文字符的Unicode范围
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False
    
    def _font_supports_chinese(self, font):
        """检查字体是否支持中文"""
        try:
            # 尝试渲染一个中文字符来测试字体支持
            test_text = "中文测试"
            # 使用getbbox方法检查字体是否能处理中文
            bbox = font.getbbox(test_text)
            return bbox[2] > 0 and bbox[3] > 0  # 如果宽度和高度都大于0，说明字体支持中文
        except:
            return False
    
    def _validate_font_size(self, font, font_size, text=""):
        """验证字体是否支持指定大小
        
        Args:
            font: 字体对象
            font_size: 字体大小
            text: 测试文本
            
        Returns:
            bool: 字体是否支持指定大小
        """
        try:
            # 简化验证逻辑：主要检查字体大小是否在合理范围内
            if font_size < 1 or font_size > 1000:
                return False
                
            # 对于大多数字体，只要大小在合理范围内就认为支持
            # 避免过于严格的验证导致所有字体都回退到默认字体
            return True
            
        except Exception:
            return False
    
    def _get_fallback_font(self, font_size):
        """获取回退字体，确保支持指定大小
        
        Args:
            font_size: 字体大小
            
        Returns:
            PIL字体对象
        """
        # 尝试加载系统默认字体
        try:
            # 首先尝试加载Arial字体
            font = ImageFont.truetype("arial.ttf", font_size, encoding="utf-8")
            if self._validate_font_size(font, font_size):
                return font
        except:
            pass
            
        # 尝试加载Times New Roman
        try:
            font = ImageFont.truetype("times.ttf", font_size, encoding="utf-8")
            if self._validate_font_size(font, font_size):
                return font
        except:
            pass
            
        # 最终回退到PIL默认字体，但调整大小
        try:
            # 使用默认字体但确保大小支持
            default_font = ImageFont.load_default()
            # 对于默认字体，我们只能使用固定大小，但可以缩放
            if hasattr(default_font, 'size'):
                # 如果默认字体有大小属性，尝试调整
                return default_font
            else:
                # 创建新的默认字体
                return ImageFont.load_default()
        except:
            # 最终回退
            return ImageFont.load_default()
    
    def _get_chinese_font(self, font_size, bold=False, italic=False):
        """获取支持中文的字体
        
        Args:
            font_size: 字体大小
            bold: 是否粗体
            italic: 是否斜体
        """
        # 中文字体优先级列表
        chinese_fonts = [
            "Microsoft YaHei",  # 微软雅黑
            "SimHei",           # 黑体
            "SimSun",           # 宋体
            "KaiTi",            # 楷体
            "FangSong",         # 仿宋
            "Arial Unicode MS", # Arial Unicode
        ]
        
        # 常见字体文件路径
        font_paths = [
            "C:/Windows/Fonts/",
            "/usr/share/fonts/",
            "/Library/Fonts/"
        ]
        
        # 中文字体文件映射（支持粗体和斜体变体）
        chinese_font_files = {
            "Microsoft YaHei": ["msyh.ttc", "msyh.ttf", "msyhbd.ttc", "msyhbd.ttf"],
            "SimHei": ["simhei.ttf"],
            "SimSun": ["simsun.ttc", "simsunb.ttf"],
            "KaiTi": ["simkai.ttf"],
            "FangSong": ["simfang.ttf"],
            "Arial Unicode MS": ["arialuni.ttf"]
        }
        
        # 按优先级尝试加载中文字体
        for font_name in chinese_fonts:
            try:
                # 首先尝试直接加载带样式的系统字体
                if bold and italic:
                    try:
                        font = ImageFont.truetype(f"{font_name} Bold Italic", font_size, encoding="utf-8")
                        if self._font_supports_chinese(font):
                            return font
                    except:
                        pass
                if bold:
                    try:
                        font = ImageFont.truetype(f"{font_name} Bold", font_size, encoding="utf-8")
                        if self._font_supports_chinese(font):
                            return font
                    except:
                        pass
                if italic:
                    try:
                        font = ImageFont.truetype(f"{font_name} Italic", font_size, encoding="utf-8")
                        if self._font_supports_chinese(font):
                            return font
                    except:
                        pass
                # 最后尝试常规字体
                font = ImageFont.truetype(font_name, font_size, encoding="utf-8")
                if self._font_supports_chinese(font):
                    return font
            except OSError:
                # 如果直接加载失败，尝试通过字体文件路径加载
                if font_name in chinese_font_files:
                    for font_file in chinese_font_files[font_name]:
                        for font_path in font_paths:
                            full_path = os.path.join(font_path, font_file)
                            if os.path.exists(full_path):
                                try:
                                    font = ImageFont.truetype(full_path, font_size, encoding="utf-8")
                                    if self._font_supports_chinese(font):
                                        return font
                                except:
                                    continue
        
        # 如果所有中文字体都加载失败，尝试加载Arial
        try:
            return ImageFont.truetype("arial.ttf", font_size, encoding="utf-8")
        except:
            # 最终回退到默认字体
            return ImageFont.load_default()
    
    def _get_english_font(self, font_family, font_size, bold=False, italic=False):
        """获取英文字体
        
        Args:
            font_family: 字体名称
            font_size: 字体大小
            bold: 是否粗体
            italic: 是否斜体
        """
        # 常见字体文件路径
        font_paths = [
            "C:/Windows/Fonts/",
            "/usr/share/fonts/",
            "/Library/Fonts/"
        ]
        
        # 构建字体变体名称（按优先级排序）
        font_variants = []
        if bold and italic:
            font_variants.extend([
                f"{font_family} Bold Italic",
                f"{font_family}-BoldItalic",
                f"{font_family} BoldItalic",
                f"{font_family}BI"
            ])
        elif bold:
            font_variants.extend([
                f"{font_family} Bold",
                f"{font_family}-Bold",
                f"{font_family}Bold",
                f"{font_family}B"
            ])
        elif italic:
            font_variants.extend([
                f"{font_family} Italic",
                f"{font_family}-Italic",
                f"{font_family}Italic",
                f"{font_family}I"
            ])
        font_variants.append(font_family)  # 常规字体
        
        # 常见英文字体文件映射（支持粗体和斜体变体）
        english_font_files = {
            "Arial": ["arial.ttf", "arialbd.ttf", "arialbi.ttf", "ariali.ttf"],
            "Times New Roman": ["times.ttf", "timesbd.ttf", "timesbi.ttf", "timesi.ttf"],
            "Courier New": ["cour.ttf", "courbd.ttf", "courbi.ttf", "couri.ttf"],
            "Verdana": ["verdana.ttf", "verdanab.ttf", "verdanaz.ttf", "verdanai.ttf"],
            "Georgia": ["georgia.ttf", "georgiab.ttf", "georgiaz.ttf", "georgiai.ttf"],
            "Tahoma": ["tahoma.ttf", "tahomabd.ttf"],
            "Trebuchet MS": ["trebuc.ttf", "trebucbd.ttf", "trebucit.ttf", "trebucbi.ttf"],
            "Comic Sans MS": ["comic.ttf", "comicbd.ttf"],
            "Impact": ["impact.ttf"],
            "Lucida Console": ["lucon.ttf"],
            "Palatino Linotype": ["pala.ttf", "palab.ttf", "palabi.ttf", "palai.ttf"]
        }
        
        # 首先尝试直接加载系统字体
        for font_variant in font_variants:
            try:
                font = ImageFont.truetype(font_variant, font_size, encoding="utf-8")
                # 验证字体是否成功加载
                if font:
                    return font
            except OSError:
                continue
        
        # 如果直接加载失败，尝试通过字体文件路径加载
        if font_family in english_font_files:
            # 根据粗体和斜体状态选择对应的字体文件
            font_files = []
            if bold and italic:
                # 优先尝试粗斜体文件
                font_files = [f for f in english_font_files[font_family] if 'bi' in f.lower() or 'bolditalic' in f.lower()]
                # 如果没有找到粗斜体，尝试组合粗体和斜体
                if not font_files:
                    font_files = [f for f in english_font_files[font_family] if 'bd' in f.lower() or 'bold' in f.lower()]
                    font_files.extend([f for f in english_font_files[font_family] if 'i' in f.lower() or 'italic' in f.lower()])
            elif bold:
                font_files = [f for f in english_font_files[font_family] if 'bd' in f.lower() or 'bold' in f.lower()]
            elif italic:
                font_files = [f for f in english_font_files[font_family] if 'i' in f.lower() or 'italic' in f.lower()]
            
            # 如果没有找到特定样式文件，使用常规字体文件
            if not font_files:
                font_files = [f for f in english_font_files[font_family] if not any(keyword in f.lower() for keyword in ['bd', 'bold', 'bi', 'italic', 'i'])]
            
            # 如果没有常规字体文件，使用所有可用文件
            if not font_files:
                font_files = english_font_files[font_family]
            
            for font_file in font_files:
                for font_path in font_paths:
                    full_path = os.path.join(font_path, font_file)
                    if os.path.exists(full_path):
                        try:
                            font = ImageFont.truetype(full_path, font_size, encoding="utf-8")
                            if font:
                                return font
                        except:
                            continue
        
        # 如果指定字体加载失败，尝试加载Arial
        if font_family != "Arial":
            try:
                # 根据粗体和斜体状态加载对应的Arial变体
                if bold and italic:
                    return ImageFont.truetype("arialbi.ttf", font_size, encoding="utf-8")
                elif bold:
                    return ImageFont.truetype("arialbd.ttf", font_size, encoding="utf-8")
                elif italic:
                    return ImageFont.truetype("ariali.ttf", font_size, encoding="utf-8")
                else:
                    return ImageFont.truetype("arial.ttf", font_size, encoding="utf-8")
            except:
                pass
        
        # 最终回退到默认字体
        return ImageFont.load_default()
    
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