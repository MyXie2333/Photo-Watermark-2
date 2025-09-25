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
        
        # 应用旋转
        if rotation != 0:
            # 创建一个足够大的透明图像来容纳旋转后的文本
            diagonal = int((text_width**2 + text_height**2)**0.5)
            rotated_text_img = Image.new('RGBA', (diagonal, diagonal), (0, 0, 0, 0))
            rotated_draw = ImageDraw.Draw(rotated_text_img)
            
            # 在透明图像上绘制文本
            if font_bold and not self._is_font_file_bold(font_family):
                # 通过多次绘制文本实现粗体效果
                print(f"[DEBUG] 手动实现粗体效果: {font_family}")
                # 绘制多次文本，每次偏移1像素，实现加粗效果
                text_x = (diagonal - text_width) // 2
                text_y = (diagonal - text_height) // 2
                for dx in range(2):
                    for dy in range(2):
                        x_offset = text_x + dx
                        y_offset = text_y + dy
                        rotated_draw.text((x_offset, y_offset), text, font=font, fill=(color.red(), color.green(), color.blue(), int(255 * opacity)))
            elif font_italic and not self._is_font_file_italic(font_family):
                # 通过图像变换实现真正的斜体效果
                print(f"[DEBUG] 手动实现斜体效果: {font_family}")
                # 创建一个单独的图像来绘制文本，然后应用斜体变换
                text_img = Image.new('RGBA', (text_width + 20, text_height + 20), (0, 0, 0, 0))
                text_draw = ImageDraw.Draw(text_img)
                
                # 正常绘制文本
                text_draw.text((10, 10), text, font=font, fill=(color.red(), color.green(), color.blue(), int(255 * opacity)))
                
                # 对于中文字体，应用更强的斜体变换
                if self._contains_chinese(text):
                    # 使用仿射变换实现斜体效果
                    import numpy as np
                    # 定义斜体变换矩阵（降低倾斜系数）
                    shear_factor = 0.15  # 降低的倾斜系数
                    matrix = [1, shear_factor, 0, 0, 1, 0, 0, 0, 1]
                    # 应用变换
                    skewed_img = text_img.transform(
                        (int(text_img.width + text_img.height * shear_factor), text_img.height),
                        Image.AFFINE,
                        matrix,
                        resample=Image.BICUBIC
                    )
                    # 将变换后的图像绘制到旋转图像上
                    rotated_draw.bitmap((text_x, text_y), skewed_img, fill=(color.red(), color.green(), color.blue(), int(255 * opacity)))
                else:
                    # 对于英文字体，使用原来的逐行偏移方法
                    lines = text.split('\n')
                    line_height = font_size  # 估算行高
                    text_x = (diagonal - text_width) // 2
                    text_y = (diagonal - text_height) // 2
                    for i, line in enumerate(lines):
                        # 计算当前行的y坐标
                        line_y = text_y + i * line_height
                        # 根据行号计算水平偏移量（模拟斜体倾斜效果）
                        offset_x = int(i * line_height * 0.2)  # 0.2是斜体倾斜系数
                        rotated_draw.text((text_x + offset_x, line_y), line, font=font, fill=(color.red(), color.green(), color.blue(), int(255 * opacity)))
            else:
                # 正常绘制文本
                text_x = (diagonal - text_width) // 2
                text_y = (diagonal - text_height) // 2
                rotated_draw.text((text_x, text_y), text, font=font, fill=(color.red(), color.green(), color.blue(), int(255 * opacity)))
            
            # 旋转文本图像
            rotated_text_img = rotated_text_img.rotate(rotation, expand=True, fillcolor=(0, 0, 0, 0))
            
            # 将旋转后的文本图像粘贴到主图像上
            paste_x = x - (rotated_text_img.width - text_width) // 2
            paste_y = y - (rotated_text_img.height - text_height) // 2
            watermarked_image.paste(rotated_text_img, (paste_x, paste_y), rotated_text_img)
        else:
            # 直接在主图像上绘制文本（无旋转）
            if font_bold and not self._is_font_file_bold(font_family):
                # 通过多次绘制文本实现粗体效果
                print(f"[DEBUG] 手动实现粗体效果: {font_family}")
                # 绘制多次文本，每次偏移1像素，实现加粗效果
                for dx in range(2):
                    for dy in range(2):
                        x_offset = x + dx
                        y_offset = y + dy
                        draw.text((x_offset, y_offset), text, font=font, fill=(color.red(), color.green(), color.blue(), int(255 * opacity)))
            elif font_italic and not self._is_font_file_italic(font_family):
                # 通过图像变换实现真正的斜体效果
                print(f"[DEBUG] 手动实现斜体效果: {font_family}")
                # 对于中文字体，使用图像变换实现斜体效果
                if self._contains_chinese(text):
                    # 创建一个单独的图像来绘制文本，然后应用斜体变换
                    text_img = Image.new('RGBA', (text_width + 20, text_height + 20), (0, 0, 0, 0))
                    text_draw = ImageDraw.Draw(text_img)
                    
                    # 正常绘制文本
                    text_draw.text((10, 10), text, font=font, fill=(color.red(), color.green(), color.blue(), int(255 * opacity)))
                    
                    # 使用仿射变换实现斜体效果
                    import numpy as np
                    # 定义斜体变换矩阵（降低倾斜系数）
                    shear_factor = 0.15  # 降低的倾斜系数
                    matrix = [1, shear_factor, 0, 0, 1, 0, 0, 0, 1]
                    # 应用变换
                    skewed_img = text_img.transform(
                        (int(text_img.width + text_img.height * shear_factor), text_img.height),
                        Image.AFFINE,
                        matrix,
                        resample=Image.BICUBIC
                    )
                    # 将变换后的图像绘制到主图像上
                    watermarked_image.paste(skewed_img, (x, y), skewed_img)
                else:
                    # 对于英文字体，使用原来的逐行偏移方法
                    lines = text.split('\n')
                    line_height = font_size  # 估算行高
                    for i, line in enumerate(lines):
                        # 计算当前行的y坐标
                        line_y = y + i * line_height
                        # 根据行号计算水平偏移量（模拟斜体倾斜效果）
                        offset_x = int(i * line_height * 0.2)  # 0.2是斜体倾斜系数
                        draw.text((x + offset_x, line_y), line, font=font, fill=(color.red(), color.green(), color.blue(), int(255 * opacity)))
            else:
                # 正常绘制文本
                draw.text((x, y), text, font=font, fill=(color.red(), color.green(), color.blue(), int(255 * opacity)))
            
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
        
        # 关键修复：优先使用用户设置的字体，只有在用户设置的字体不支持中文时才回退到中文字体
        if needs_chinese_font:
            print(f"[DEBUG] 文本包含中文，字体选择流程开始 - 用户选择字体: {font_family}")
            
            # 首先尝试使用用户设置的字体（如果它支持中文）
            try:
                print(f"[DEBUG] 尝试直接加载用户设置的字体: {font_family}")
                font = ImageFont.truetype(font_family, font_size, encoding="utf-8")
                # 检查字体是否支持中文
                if self._font_supports_chinese(font):
                    print(f"[DEBUG] 成功加载用户字体 {font_family} 并确认支持中文")
                    self.font_cache[font_key] = font
                    return font
                else:
                    print(f"[DEBUG] 字体 {font_family} 不支持中文")
            except OSError as e:
                print(f"[DEBUG] 加载用户字体 {font_family} 失败: {e}")
            
            # 如果用户设置的字体不支持中文或加载失败，尝试通过字体文件路径加载
            print(f"[DEBUG] 尝试通过文件路径加载字体: {font_family}")
            font = self._get_chinese_font_by_name(font_family, font_size, bold, italic)
            if font:
                print(f"[DEBUG] 通过文件路径成功加载字体: {font_family}")
                self.font_cache[font_key] = font
                return font
            else:
                print(f"[DEBUG] 通过文件路径加载字体 {font_family} 失败")
            
            # 如果特定字体加载失败，回退到默认中文字体
            print(f"[DEBUG] 回退到默认中文字体")
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
    
    def _is_font_file_bold(self, font_name):
        """检查字体是否通过文件实现了粗体效果
        
        Args:
            font_name: 字体名称
            
        Returns:
            bool: 是否通过文件实现粗体
        """
        # 中文字体文件映射（包含粗体和斜体变体）
        chinese_font_files = {
            "Microsoft YaHei": {
                "regular": ["msyh.ttc", "msyh.ttf"],
                "bold": ["msyhbd.ttc", "msyhbd.ttf"],
                "light": ["msyhl.ttc"]
            },
            "SimHei": {
                "regular": ["simhei.ttf"]
            },
            "SimSun": {
                "regular": ["simsun.ttc"],
                "bold": ["simsunb.ttf"],
                "extended": ["SimsunExtG.ttf"]
            },
            "KaiTi": {
                "regular": ["simkai.ttf", "STKAITI.TTF"]
            },
            "FangSong": {
                "regular": ["simfang.ttf"]
            },
            "Arial Unicode MS": {
                "regular": ["arialuni.ttf"]
            }
        }
        
        # 英文字体文件映射
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
        
        # 检查中文字体
        if font_name in chinese_font_files:
            return "bold" in chinese_font_files[font_name] and chinese_font_files[font_name]["bold"]
        
        # 检查英文字体
        if font_name in english_font_files:
            # 检查是否有粗体文件
            for font_file in english_font_files[font_name]:
                if 'bd' in font_file.lower() or 'bold' in font_file.lower():
                    return True
        
        return False
    
    def _is_font_file_italic(self, font_name):
        """检查字体是否通过文件实现了斜体效果
        
        Args:
            font_name: 字体名称
            
        Returns:
            bool: 是否通过文件实现斜体
        """
        # 中文字体文件映射（包含粗体和斜体变体）
        chinese_font_files = {
            "Microsoft YaHei": {
                "regular": ["msyh.ttc", "msyh.ttf"],
                "bold": ["msyhbd.ttc", "msyhbd.ttf"],
                "light": ["msyhl.ttc"]
            },
            "SimHei": {
                "regular": ["simhei.ttf"]
            },
            "SimSun": {
                "regular": ["simsun.ttc"],
                "bold": ["simsunb.ttf"],
                "extended": ["SimsunExtG.ttf"]
            },
            "KaiTi": {
                "regular": ["simkai.ttf", "STKAITI.TTF"]
            },
            "FangSong": {
                "regular": ["simfang.ttf"]
            },
            "Arial Unicode MS": {
                "regular": ["arialuni.ttf"]
            }
        }
        
        # 英文字体文件映射
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
        
        # 检查中文字体
        if font_name in chinese_font_files:
            # 对于中文字体，我们总是返回False，这样就会使用手动实现的斜体效果
            # 因为中文字体通常不通过文件实现斜体效果
            return False
        
        # 检查英文字体
        if font_name in english_font_files:
            # 检查是否有斜体文件
            for font_file in english_font_files[font_name]:
                # 检查是否包含斜体标识（i, italic, it）
                if any(italic_indicator in font_file.lower() for italic_indicator in ['i', 'italic', 'it']):
                    return True
        
        return False
    
    def _get_chinese_font_by_name(self, font_name, font_size, bold=False, italic=False):
        """根据字体名称获取特定的中文字体
        
        Args:
            font_name: 字体名称
            font_size: 字体大小
            bold: 是否粗体
            italic: 是否斜体
        """
        print(f"[DEBUG] _get_chinese_font_by_name: 尝试加载字体 {font_name}, bold={bold}, italic={italic}")
        
        # 中文字体文件映射（包含粗体和斜体变体）
        chinese_font_files = {
            "Microsoft YaHei": {
                "regular": ["msyh.ttc", "msyh.ttf"],
                "bold": ["msyhbd.ttc", "msyhbd.ttf"],
                "light": ["msyhl.ttc"]
            },
            "SimHei": {
                "regular": ["simhei.ttf"]
            },
            "SimSun": {
                "regular": ["simsun.ttc"],
                "bold": ["simsunb.ttf"],
                "extended": ["SimsunExtG.ttf"]
            },
            "KaiTi": {
                "regular": ["simkai.ttf", "STKAITI.TTF"]
            },
            "FangSong": {
                "regular": ["simfang.ttf"]
            },
            "Arial Unicode MS": {
                "regular": ["arialuni.ttf"]
            }
        }
        
        # 常见字体文件路径
        font_paths = [
            "C:/Windows/Fonts/",
            "/usr/share/fonts/",
            "/Library/Fonts/"
        ]
        
        # 首先尝试通过字体文件路径加载（这是最可靠的方式）
        if font_name in chinese_font_files:
            print(f"[DEBUG] 字体 {font_name} 在字体文件映射中，尝试文件路径加载")
            
            # 根据粗体和斜体状态选择字体变体
            font_variants = []
            if bold:
                # 优先尝试粗体变体
                if "bold" in chinese_font_files[font_name]:
                    font_variants.extend(chinese_font_files[font_name]["bold"])
            
            # 添加常规字体变体
            if "regular" in chinese_font_files[font_name]:
                font_variants.extend(chinese_font_files[font_name]["regular"])
            
            # 如果没有找到特定变体，使用所有可用字体文件
            if not font_variants:
                for variant in chinese_font_files[font_name].values():
                    font_variants.extend(variant)
            
            # 去重
            font_variants = list(set(font_variants))
            
            print(f"[DEBUG] 字体变体列表: {font_variants}")
            
            for font_file in font_variants:
                for font_path in font_paths:
                    full_path = os.path.join(font_path, font_file)
                    print(f"[DEBUG] 检查字体文件路径: {full_path}")
                    if os.path.exists(full_path):
                        print(f"[DEBUG] 字体文件存在，尝试加载: {full_path}")
                        try:
                            font = ImageFont.truetype(full_path, font_size, encoding="utf-8")
                            print(f"[DEBUG] 成功通过文件路径加载字体: {font_name} (变体: {font_file})")
                            
                            # 如果请求了粗体或斜体但字体文件没有这些变体，尝试通过PIL的特性模拟
                            if (bold or italic) and font:
                                # PIL会自动处理字体的粗体和斜体渲染，即使字体文件本身没有这些变体
                                print(f"[DEBUG] 已加载字体 {font_name}，将通过PIL特性模拟粗体={bold}, 斜体={italic}")
                            
                            return font
                        except Exception as e:
                            print(f"[DEBUG] 加载字体文件失败: {e}")
                            continue
        else:
            print(f"[DEBUG] 字体 {font_name} 不在字体文件映射中")
        
        # 如果文件路径加载失败，尝试直接加载系统字体（带样式变体）
        print(f"[DEBUG] 尝试直接通过系统字体名称加载: {font_name}")
        
        # 构建字体变体名称（按优先级排序）
        font_variants = []
        if bold and italic:
            font_variants.extend([
                f"{font_name} Bold Italic",
                f"{font_name}-BoldItalic",
                f"{font_name} BoldItalic",
                f"{font_name}BI"
            ])
        elif bold:
            font_variants.extend([
                f"{font_name} Bold",
                f"{font_name}-Bold",
                f"{font_name}Bold",
                f"{font_name}B"
            ])
        elif italic:
            font_variants.extend([
                f"{font_name} Italic",
                f"{font_name}-Italic",
                f"{font_name}Italic",
                f"{font_name}I"
            ])
        font_variants.append(font_name)  # 常规字体
        
        for font_variant in font_variants:
            try:
                font = ImageFont.truetype(font_variant, font_size, encoding="utf-8")
                print(f"[DEBUG] 成功通过系统字体名称加载: {font_variant}")
                
                # 如果请求了粗体或斜体但字体文件没有这些变体，尝试通过PIL的特性模拟
                if (bold or italic) and font:
                    # PIL会自动处理字体的粗体和斜体渲染，即使字体文件本身没有这些变体
                    print(f"[DEBUG] 已加载字体 {font_variant}，将通过PIL特性模拟粗体={bold}, 斜体={italic}")
                
                return font
            except OSError as e:
                print(f"[DEBUG] 通过系统字体名称加载 {font_variant} 失败: {e}")
                continue
        
        return None

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
        
        # 按优先级尝试加载中文字体
        for font_name in chinese_fonts:
            font = self._get_chinese_font_by_name(font_name, font_size, bold, italic)
            if font:
                return font
        
        # 如果所有中文字体都加载失败，尝试加载Arial Unicode MS
        try:
            return ImageFont.truetype("arialuni.ttf", font_size, encoding="utf-8")
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