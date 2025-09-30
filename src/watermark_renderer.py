#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水印渲染引擎
"""

from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import os
from PyQt5.QtGui import QColor
import io


class WatermarkRenderer:
    """水印渲染器"""
    
    def __init__(self, parent=None):
        self.font_cache = {}
        self.last_watermark_position = None  # 记录最后一次渲染的水印位置
        self.last_rendered_image = None  # 缓存最后一次渲染的图片
        self.last_rendered_settings = None  # 缓存最后一次渲染的设置
        self.font_path_cache = {}  # 缓存字体文件路径，避免重复文件系统检查
        self.compression_scale = 1.0  # 原图到压缩图的压缩比例，默认为1.0
        self.parent = parent  # 设置parent属性
        
    def set_compression_scale(self, scale):
        """
        设置压缩比例
        
        Args:
            scale: 压缩比例值
        """
        self.compression_scale = scale
        
    def render_text_watermark(self, image, watermark_settings):
        """
        渲染文本水印到图片上（使用图片水印渲染接口，但保留原有的位置计算逻辑）
        
        Args:
            image: PIL Image对象
            watermark_settings: 水印设置字典
            
        Returns:
            PIL Image对象（带水印的图片）
        """
        if not watermark_settings.get("text"):
            return image
            
        # 检查是否可以使用缓存
        if (self.last_rendered_image is not None and 
            self.last_rendered_settings is not None and
            self._settings_equal(watermark_settings, self.last_rendered_settings)):
            print("[DEBUG] 使用缓存的水印图片")
            return self.last_rendered_image
        
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
        enable_shadow = watermark_settings.get("enable_shadow", False)
        enable_outline = watermark_settings.get("enable_outline", False)
        outline_color = watermark_settings.get("outline_color", (0, 0, 0))
        outline_width = watermark_settings.get("outline_width", None)
        outline_offset = watermark_settings.get("outline_offset", (0, 0))
        shadow_color = watermark_settings.get("shadow_color", (0, 0, 0))
        shadow_offset = watermark_settings.get("shadow_offset", None)
        shadow_blur = watermark_settings.get("shadow_blur", None)
        
        # 创建图片副本
        watermarked_image = image.copy()
        
        # 将文本转换为图片
        text_image = self._text_to_image(
            text, font_family, font_size, font_bold, font_italic, color, opacity,
            enable_shadow, enable_outline, outline_color, outline_width, outline_offset,
            shadow_color, shadow_offset, shadow_blur
        )
        
        # 获取文本图片尺寸
        text_width, text_height = text_image.size
        
        # 计算水印位置（使用原有的位置计算逻辑）
        img_width, img_height = watermarked_image.size
        print(f"[DEBUG] WatermarkRenderer.render_text_watermark: 使用position={position}计算水印位置")
        x, y = self._calculate_position(position, img_width, img_height, text_width, text_height)
        
        # 更新current_watermark_settings中的坐标
        if hasattr(self, 'parent') and self.parent and hasattr(self.parent, 'image_manager'):
            current_path = self.parent.image_manager.get_current_image_path()
            if current_path:
                current_watermark_settings = self.parent.image_manager.ensure_watermark_settings_initialized()
                if current_watermark_settings is not None:
                    # 更新watermark_x和watermark_y
                    current_watermark_settings["watermark_x"] = int(round(x*self.compression_scale))
                    current_watermark_settings["watermark_y"] = int(round(y*self.compression_scale))
                    # 保存更新后的水印设置回image_manager
                    self.parent.image_manager.set_watermark_settings(current_path, current_watermark_settings)
                    print(f"[DEBUG] WatermarkRenderer.render_text_watermark: 更新并保存水印坐标: watermark_x={x}, watermark_y={y}")
                else:
                    print(f"[DEBUG] WatermarkRenderer.render_text_watermark: current_watermark_settings为None，无法更新坐标")
            else:
                print(f"[DEBUG] WatermarkRenderer.render_text_watermark: 当前图片路径为空，无法更新坐标")
        
        # 记录水印位置
        self.last_watermark_position = (x, y)
        print(f"[DEBUG] WatermarkRenderer.render_text_watermark: 水印初始化坐标: x={x}, y={y}")
        
        # 如果需要旋转，应用旋转
        if rotation != 0:
            text_image = text_image.rotate(rotation, expand=True, fillcolor=(0, 0, 0, 0))
            # 旋转后重新计算位置
            rotated_width, rotated_height = text_image.size
            x = x - (rotated_width - text_width) // 2
            y = y - (rotated_height - text_height) // 2
        
        # 更新current_watermark_settings中的最终坐标
        if hasattr(self, 'parent') and self.parent and hasattr(self.parent, 'image_manager'):
            current_path = self.parent.image_manager.get_current_image_path()
            if current_path:
                current_watermark_settings = self.parent.image_manager.ensure_watermark_settings_initialized()
                if current_watermark_settings is not None:
                    # 更新最终的watermark_x和watermark_y
                    current_watermark_settings["watermark_x"] = int(round(x*self.compression_scale))
                    current_watermark_settings["watermark_y"] = int(round(y*self.compression_scale))
                    # 保存更新后的水印设置回image_manager
                    self.parent.image_manager.set_watermark_settings(current_path, current_watermark_settings)
                    print(f"[DEBUG] WatermarkRenderer.render_text_watermark: 更新并保存最终水印坐标: watermark_x={x}, watermark_y={y}")
                else:
                    print(f"[DEBUG] WatermarkRenderer.render_text_watermark: current_watermark_settings为None，无法更新最终坐标")
            else:
                print(f"[DEBUG] WatermarkRenderer.render_text_watermark: 当前图片路径为空，无法更新最终坐标")
        
        # 将文本图片粘贴到主图像上
        watermarked_image.paste(text_image, (int(round(x*self.compression_scale)), int(round(y*self.compression_scale))), text_image)
            
        # 更新缓存
        self.last_rendered_image = watermarked_image
        self.last_rendered_settings = watermark_settings.copy()
            
        return watermarked_image
    
    def _text_to_image(self, text, font_family, font_size, font_bold, font_italic, color, opacity, 
                       enable_shadow, enable_outline, outline_color, outline_width, outline_offset,
                       shadow_color, shadow_offset, shadow_blur):
        """
        将文本转换为图片
        
        Args:
            text: 文本内容
            font_family: 字体名称
            font_size: 字体大小
            font_bold: 是否粗体
            font_italic: 是否斜体
            color: 文本颜色
            opacity: 透明度
            enable_shadow: 是否启用阴影
            enable_outline: 是否启用描边
            outline_color: 描边颜色
            outline_width: 描边宽度
            outline_offset: 描边偏移量
            shadow_color: 阴影颜色
            shadow_offset: 阴影偏移量
            shadow_blur: 阴影模糊半径
            
        Returns:
            PIL Image对象（文本图片）
        """
        # 获取字体
        font = self._get_font(font_family, font_size, text, font_bold, font_italic)
        
        # 创建绘图对象计算文本尺寸
        temp_img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        
        # 计算文本尺寸
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 创建足够大的透明图像来容纳文本
        text_img = Image.new('RGBA', (text_width + 40, text_height + 40), (0, 0, 0, 0))
        text_draw = ImageDraw.Draw(text_img)
        
        # 处理粗体和斜体效果
        is_chinese_text = self._contains_chinese(text)
        
        if (font_bold and (not self._is_font_file_bold(font_family) or is_chinese_text)) or (font_italic and (not self._is_font_file_italic(font_family) or is_chinese_text)) or is_chinese_text:
            print(f"[DEBUG] 手动实现粗体或斜体效果: {font_family}")
            # 如果是中文字体且需要斜体效果
            if font_italic and (not self._is_font_file_italic(font_family) or is_chinese_text):
                # 创建一个单独的图像来绘制文本，然后应用斜体变换
                # 增加画布边距以避免斜体时汉字下半部分被截断
                temp_text_img = Image.new('RGBA', (text_width + 40, text_height + 40), (0, 0, 0, 0))
                temp_text_draw = ImageDraw.Draw(temp_text_img)
                
                # 正常绘制文本（添加向上的位移以避免斜体时汉字下半部分被截断）
                temp_text_draw.text((20, 20), text, font=font, fill=(color.red(), color.green(), color.blue(), int(255 * opacity)))
                
                # 使用仿射变换实现斜体效果
                import numpy as np
                # 定义斜体变换矩阵（降低倾斜系数）
                shear_factor = 0.15  # 降低的倾斜系数
                matrix = [1, shear_factor, 0, 0, 1, 0, 0, 0, 1]
                # 应用变换，增加宽度以容纳斜体效果
                skewed_img = temp_text_img.transform(
                    (int(temp_text_img.width + temp_text_img.height * shear_factor), temp_text_img.height),
                    Image.AFFINE,
                    matrix,
                    resample=Image.BICUBIC
                )
                
                # 添加向上的位移来解决汉字下半部分被截断的问题
                vertical_offset = -5  # 向上移动5个像素，增加位移量
                
                # 如果还需要粗体效果，则多次绘制斜体图像
                if font_bold and (not self._is_font_file_bold(font_family) or is_chinese_text):
                    for dx in range(2):
                        for dy in range(2):
                            x_offset = dx
                            y_offset = dy + vertical_offset  # 添加垂直位移
                            text_img.paste(skewed_img, (x_offset, y_offset), skewed_img)
                else:
                    # 仅斜体效果
                    text_img.paste(skewed_img, (0, vertical_offset), skewed_img)  # 添加垂直位移
            # 对于英文字体或不需要斜体的字体
            else:
                # 通过多次绘制文本实现粗体效果
                for dx in range(2):
                    for dy in range(2):
                        x_offset = 20 + dx
                        y_offset = 20 + dy
                        # 如果需要斜体效果（英文字体）
                        if font_italic and not self._is_font_file_italic(font_family):
                            # 对于英文字体，使用逐行偏移方法
                            lines = text.split('\n')
                            line_height = font_size  # 估算行高
                            for i, line in enumerate(lines):
                                # 计算当前行的y坐标
                                line_y = y_offset + i * line_height
                                # 根据行号计算水平偏移量（模拟斜体倾斜效果）
                                offset_x = int(i * line_height * 0.2)  # 0.2是斜体倾斜系数
                                text_draw.text((x_offset + offset_x, line_y), line, font=font, fill=(color.red(), color.green(), color.blue(), int(255 * opacity)))
                        else:
                            text_draw.text((x_offset, y_offset), text, font=font, fill=(color.red(), color.green(), color.blue(), int(255 * opacity)))
        else:
            # 正常绘制文本
            # 添加向上的位移以避免汉字下半部分被截断
            text_draw.text((20, 15), text, font=font, fill=(color.red(), color.green(), color.blue(), int(255 * opacity)))
        
        # 应用阴影和描边效果
        final_img = self._apply_text_effects(text_img, text_width, text_height, 0, 
                                            enable_shadow, enable_outline, color, opacity, font, text, 
                                            outline_color=outline_color, outline_width=outline_width, 
                                            outline_offset=outline_offset,
                                            shadow_color=shadow_color, shadow_offset=shadow_offset, 
                                            shadow_blur=shadow_blur, italic=font_italic)
        
        # 裁剪图像，去除透明边缘
        bbox = final_img.getbbox()
        if bbox:
            final_img = final_img.crop(bbox)
        
        return final_img
    
    def _apply_text_effects(self, temp_img, text_width, text_height, diagonal, enable_shadow, enable_outline, 
                          color, opacity, font, text, outline_color=(0, 0, 0), outline_width=None, 
                          outline_offset=(0, 0), shadow_color=(0, 0, 0), shadow_offset=None, shadow_blur=None, italic=False):
        """
        应用文本效果（阴影和描边）
        
        Args:
            temp_img: 包含基本文本的临时图像
            text_width: 文本宽度
            text_height: 文本高度
            diagonal: 对角线长度（用于旋转情况）
            enable_shadow: 是否启用阴影
            enable_outline: 是否启用描边
            color: 文本颜色
            opacity: 透明度
            font: 字体对象
            text: 实际文本内容
            outline_color: 描边颜色，默认为黑色
            outline_width: 描边宽度，默认为字体大小的1/12
            outline_offset: 描边偏移量，默认为(0, 0)
            shadow_color: 阴影颜色，默认为黑色
            shadow_offset: 阴影偏移量，默认为(3, 3)
            shadow_blur: 阴影模糊半径，默认为3
            italic: 是否斜体
        
        Returns:
            PIL Image对象: 应用效果后的图像
        """
        # 创建最终图像
        if diagonal > 0:
            # 旋转情况
            result_img = Image.new('RGBA', (diagonal, diagonal), (0, 0, 0, 0))
        else:
            # 非旋转情况
            result_img = Image.new('RGBA', temp_img.size, (0, 0, 0, 0))
        
        result_draw = ImageDraw.Draw(result_img)
        
        # 先应用描边效果
        if enable_outline:
            # 设置默认描边参数
            if outline_width is None:
                # 增加描边宽度为字体大小的1/12，使描边更明显
                stroke_width = max(2, int(font.size / 12))
            else:
                stroke_width = outline_width
                
            # 描边透明度略高于文本
            outline_opacity = min(1.0, opacity * 1.2)
            
            # 对于旋转和非旋转情况，我们都直接在结果图像上绘制描边
            if diagonal > 0:
                # 旋转情况
                text_x = (diagonal - text_width) // 2
                text_y = (diagonal - text_height) // 2 - 5  # 向上移动5个像素
            else:
                # 非旋转情况
                text_x = 20
                text_y = 15  # 与之前的绘制位置一致
                
            # 绘制描边（使用8个方向）
            directions = [(-stroke_width, -stroke_width), (-stroke_width, 0), (-stroke_width, stroke_width),
                         (0, -stroke_width), (0, stroke_width),
                         (stroke_width, -stroke_width), (stroke_width, 0), (stroke_width, stroke_width)]
            
            # 如果是斜体文本，我们需要特殊处理描边，确保描边也倾斜
            if italic and (not diagonal > 0 or (diagonal > 0 and not self._is_font_file_italic(font.getname()[0]))):
                # 对于斜体文本，我们不使用传统的8方向描边，而是使用另一种方式创建倾斜的描边
                # 创建一个临时图像来绘制斜体描边
                if diagonal > 0:
                    outline_temp_img = Image.new('RGBA', (diagonal, diagonal), (0, 0, 0, 0))
                else:
                    outline_temp_img = Image.new('RGBA', (text_width + 40, text_height + 40), (0, 0, 0, 0))
                outline_temp_draw = ImageDraw.Draw(outline_temp_img)
                
                # 绘制斜体描边
                if diagonal > 0:
                    # 绘制斜体描边
                    for dx, dy in directions:
                        outline_temp_draw.text((text_x + dx + outline_offset[0], text_y + dy + outline_offset[1]), text, font=font, 
                                              fill=(outline_color[0], outline_color[1], outline_color[2], int(255 * outline_opacity)))
                    
                    # 对描边应用斜体变换
                    import numpy as np
                    shear_factor = 0.15  # 与主文本相同的倾斜系数
                    matrix = [1, shear_factor, 0, 0, 1, 0, 0, 0, 1]
                    # 应用变换
                    skewed_outline_img = outline_temp_img.transform(
                        (int(outline_temp_img.width + outline_temp_img.height * shear_factor), outline_temp_img.height),
                        Image.AFFINE,
                        matrix,
                        resample=Image.BICUBIC
                    )
                    
                    # 将倾斜后的描边粘贴到结果图像
                    result_img.paste(skewed_outline_img, ((diagonal - skewed_outline_img.width) // 2, 
                                                         (diagonal - text_height) // 2 - 5), skewed_outline_img)
                else:
                    # 非旋转情况的斜体描边
                    if self._contains_chinese(text):
                        # 中文斜体描边
                        for dx, dy in directions:
                            outline_temp_draw.text((text_x + dx + outline_offset[0], text_y + dy + outline_offset[1]), text, font=font, 
                                              fill=(outline_color[0], outline_color[1], outline_color[2], int(255 * outline_opacity)))
                        
                        # 对描边应用斜体变换
                        shear_factor = 0.15  # 与主文本相同的倾斜系数
                        matrix = [1, shear_factor, 0, 0, 1, 0, 0, 0, 1]
                        # 应用变换
                        skewed_outline_img = outline_temp_img.transform(
                            (int(outline_temp_img.width + outline_temp_img.height * shear_factor), outline_temp_img.height),
                            Image.AFFINE,
                            matrix,
                            resample=Image.BICUBIC
                        )
                        
                        # 将倾斜后的描边粘贴到结果图像
                        result_img.paste(skewed_outline_img, (0, 0), skewed_outline_img)
                    else:
                        # 英文斜体描边，使用逐行偏移方法
                        lines = text.split('\n')
                        line_height = font.size  # 估算行高
                        for i, line in enumerate(lines):
                            # 计算当前行的y坐标
                            line_y = text_y + i * line_height
                            # 根据行号计算水平偏移量（模拟斜体倾斜效果）
                            offset_x = int(i * line_height * 0.2)  # 0.2是斜体倾斜系数
                            
                            # 绘制倾斜的描边
                            for dx, dy in directions:
                                result_draw.text((text_x + dx + offset_x + outline_offset[0], line_y + dy + outline_offset[1]), line, font=font, 
                                                fill=(outline_color[0], outline_color[1], outline_color[2], int(255 * outline_opacity)))
            else:
                # 非斜体文本的传统8方向描边
                for dx, dy in directions:
                    if diagonal > 0:
                        # 使用指定的描边颜色
                        result_draw.text((text_x + dx + outline_offset[0], text_y + dy + outline_offset[1]), text, font=font, 
                                        fill=(outline_color[0], outline_color[1], outline_color[2], int(255 * outline_opacity)))
                    else:
                        # 对于非旋转情况，我们只处理单行文本
                        result_draw.text((text_x + dx + outline_offset[0], text_y + dy + outline_offset[1]), text, font=font, 
                                        fill=(outline_color[0], outline_color[1], outline_color[2], int(255 * outline_opacity)))
        
        # 然后将原图像粘贴到结果图像上（如果有描边，这会覆盖描边内部）
        if diagonal > 0:
            # 旋转情况：居中粘贴
            paste_x = (diagonal - temp_img.width) // 2
            paste_y = (diagonal - temp_img.height) // 2
            result_img.paste(temp_img, (paste_x, paste_y), temp_img)
        else:
            # 非旋转情况：直接复制
            result_img.paste(temp_img, (0, 0), temp_img)
        
        # 应用阴影效果
        if enable_shadow:
            # 设置默认阴影参数
            if shadow_offset is None:
                # 增加阴影偏移量使阴影更明显
                shadow_offset = (3, 3)
            if shadow_blur is None:
                # 默认模糊半径
                shadow_blur = 3
                
            # 阴影透明度增加，使阴影更明显
            shadow_opacity = min(0.7, opacity * 0.8)  # 提高阴影不透明度
            
            if diagonal > 0:
                # 旋转情况
                # 保持原图像尺寸不变，只偏移阴影位置
                shadow_img = Image.new('RGBA', (diagonal, diagonal), (0, 0, 0, 0))
                shadow_draw = ImageDraw.Draw(shadow_img)
                
                if italic and (not self._is_font_file_italic(font.getname()[0])):
                    # 对于斜体文本，需要特殊处理阴影，确保阴影也倾斜
                    # 创建一个临时图像来绘制斜体阴影
                    shadow_temp_img = Image.new('RGBA', (diagonal, diagonal), (0, 0, 0, 0))
                    shadow_temp_draw = ImageDraw.Draw(shadow_temp_img)
                    
                    # 绘制斜体阴影
                    text_x = (diagonal - text_width) // 2 + shadow_offset[0]
                    text_y = (diagonal - text_height) // 2 - 5 + shadow_offset[1]
                    shadow_temp_draw.text((text_x, text_y), text, font=font, 
                                        fill=(shadow_color[0], shadow_color[1], shadow_color[2], int(255 * shadow_opacity)))
                    
                    # 对阴影应用斜体变换
                    import numpy as np
                    shear_factor = 0.15  # 与主文本相同的倾斜系数
                    matrix = [1, shear_factor, 0, 0, 1, 0, 0, 0, 1]
                    # 应用变换
                    skewed_shadow_img = shadow_temp_img.transform(
                        (int(shadow_temp_img.width + shadow_temp_img.height * shear_factor), shadow_temp_img.height),
                        Image.AFFINE,
                        matrix,
                        resample=Image.BICUBIC
                    )
                    
                    # 将倾斜后的阴影粘贴到阴影图像
                    shadow_img.paste(skewed_shadow_img, ((diagonal - skewed_shadow_img.width) // 2, 
                                                          (diagonal - text_height) // 2 - 5), skewed_shadow_img)
                else:
                    # 非斜体文本的阴影
                    # 绘制偏移的阴影
                    text_x = (diagonal - text_width) // 2 + shadow_offset[0]
                    text_y = (diagonal - text_height) // 2 - 5 + shadow_offset[1]
                    shadow_draw.text((text_x, text_y), text, font=font, 
                                    fill=(shadow_color[0], shadow_color[1], shadow_color[2], int(255 * shadow_opacity)))
                
                # 如果需要阴影模糊效果且PIL支持ImageFilter
                if shadow_blur > 0:
                    try:
                        from PIL import ImageFilter
                        # 仅对阴影应用高斯模糊
                        shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
                    except ImportError:
                        # 如果PIL不支持ImageFilter，则忽略模糊效果
                        pass
                
                # 将原图像放在阴影上方，保持原位置不变
                shadow_img.paste(result_img, (0, 0), result_img)
                result_img = shadow_img
            else:
                # 非旋转情况
                # 保持原图像尺寸不变，只偏移阴影位置
                shadow_img = Image.new('RGBA', (result_img.width, result_img.height), (0, 0, 0, 0))
                shadow_draw = ImageDraw.Draw(shadow_img)
                
                if italic and (not self._is_font_file_italic(font.getname()[0])):
                    # 对于斜体文本，需要特殊处理阴影，确保阴影也倾斜
                    # 创建一个临时图像来绘制斜体阴影
                    shadow_temp_img = Image.new('RGBA', (result_img.width, result_img.height), (0, 0, 0, 0))
                    shadow_temp_draw = ImageDraw.Draw(shadow_temp_img)
                    
                    # 绘制斜体阴影
                    shadow_temp_draw.text((20 + shadow_offset[0], 15 + shadow_offset[1]), text, font=font, 
                                        fill=(shadow_color[0], shadow_color[1], shadow_color[2], int(255 * shadow_opacity)))
                    
                    # 对阴影应用斜体变换
                    shear_factor = 0.15  # 与主文本相同的倾斜系数
                    matrix = [1, shear_factor, 0, 0, 1, 0, 0, 0, 1]
                    # 应用变换
                    skewed_shadow_img = shadow_temp_img.transform(
                        (int(shadow_temp_img.width + shadow_temp_img.height * shear_factor), shadow_temp_img.height),
                        Image.AFFINE,
                        matrix,
                        resample=Image.BICUBIC
                    )
                    
                    # 将倾斜后的阴影粘贴到阴影图像
                    shadow_img.paste(skewed_shadow_img, (0, 0), skewed_shadow_img)
                else:
                    # 非斜体文本的阴影
                    # 绘制偏移的阴影
                    shadow_draw.text((20 + shadow_offset[0], 15 + shadow_offset[1]), text, font=font, 
                                    fill=(shadow_color[0], shadow_color[1], shadow_color[2], int(255 * shadow_opacity)))
                
                # 如果需要阴影模糊效果且PIL支持ImageFilter
                if shadow_blur > 0:
                    try:
                        from PIL import ImageFilter
                        # 仅对阴影应用高斯模糊
                        shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
                    except ImportError:
                        # 如果PIL不支持ImageFilter，则忽略模糊效果
                        pass
                
                # 将原图像放在阴影上方，保持原位置不变
                shadow_img.paste(result_img, (0, 0), result_img)
                result_img = shadow_img
        
        return result_img
    
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
            # 检查是否有粗体变体
            if "bold" in chinese_font_files[font_name]:
                bold_files = chinese_font_files[font_name]["bold"]
                # 检查粗体文件是否实际存在
                font_paths = [
                    "C:/Windows/Fonts/",
                    "/usr/share/fonts/",
                    "/Library/Fonts/"
                ]
                for font_file in bold_files:
                    for font_path in font_paths:
                        full_path = os.path.join(font_path, font_file)
                        if os.path.exists(full_path):
                            return True
            return False
        
        # 检查英文字体
        if font_name in english_font_files:
            # 检查是否有粗体文件
            font_paths = [
                "C:/Windows/Fonts/",
                "/usr/share/fonts/",
                "/Library/Fonts/"
            ]
            for font_file in english_font_files[font_name]:
                if 'bd' in font_file.lower() or 'bold' in font_file.lower():
                    # 检查文件是否实际存在
                    for font_path in font_paths:
                        full_path = os.path.join(font_path, font_file)
                        if os.path.exists(full_path):
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
            font_paths = [
                "C:/Windows/Fonts/",
                "/usr/share/fonts/",
                "/Library/Fonts/"
            ]
            for font_file in english_font_files[font_name]:
                # 检查是否包含斜体标识（i, italic, it）
                if any(italic_indicator in font_file.lower() for italic_indicator in ['i', 'italic', 'it']):
                    # 检查文件是否实际存在
                    for font_path in font_paths:
                        full_path = os.path.join(font_path, font_file)
                        if os.path.exists(full_path):
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
                    
                    # 使用缓存检查文件是否存在
                    cache_key = full_path
                    if cache_key in self.font_path_cache:
                        if not self.font_path_cache[cache_key]:
                            print(f"[DEBUG] 字体文件不存在（缓存）: {full_path}")
                            continue
                        print(f"[DEBUG] 字体文件存在（缓存）: {full_path}")
                    else:
                        # 检查文件是否存在并缓存结果
                        exists = os.path.exists(full_path)
                        self.font_path_cache[cache_key] = exists
                        if not exists:
                            print(f"[DEBUG] 字体文件不存在: {full_path}")
                            continue
                        print(f"[DEBUG] 字体文件存在: {full_path}")
                    
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
                    
                    # 使用缓存检查文件是否存在
                    cache_key = full_path
                    if cache_key in self.font_path_cache:
                        if not self.font_path_cache[cache_key]:
                            continue
                    else:
                        # 检查文件是否存在并缓存结果
                        exists = os.path.exists(full_path)
                        self.font_path_cache[cache_key] = exists
                        if not exists:
                            continue
                    
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
    
    def _settings_equal(self, settings1, settings2):
        """比较两个水印设置是否相同"""
        # 只比较影响渲染的关键设置
        key_keys = ["text", "font_family", "font_size", "font_bold", "font_italic", 
                   "color", "opacity", "position", "rotation", "enable_shadow", 
                   "enable_outline", "outline_color", "outline_width", "outline_offset",
                   "shadow_color", "shadow_offset", "shadow_blur"]
        
        for key in key_keys:
            if key not in settings1 and key not in settings2:
                continue
            if key not in settings1 or key not in settings2:
                return False
            if settings1[key] != settings2[key]:
                return False
        return True
    
    def _calculate_position(self, position, img_width, img_height, text_width, text_height):
        """计算水印位置"""
        margin = 20  # 边距
        
        # 处理元组形式的相对位置（九宫格位置）
        if isinstance(position, tuple) and len(position) >= 2:
            print(f"[BRANCH] _calculate_position: 处理元组形式的相对位置，position={position}")
            # 检查是否是相对位置（0-1之间的值）
            x_ratio, y_ratio = position[0], position[1]
            if 0 <= x_ratio <= 1 and 0 <= y_ratio <= 1:
                print(f"[BRANCH] _calculate_position: 处理相对位置（0-1之间的值），x_ratio={x_ratio}, y_ratio={y_ratio}")
                # 计算绝对位置，直接转换为整数
                x = int(round(img_width * x_ratio - text_width / 2))
                y = int(round(img_height * y_ratio - text_height / 2))
                print(f"[DEBUG] WatermarkRenderer._calculate_position: 修改position为 ({x}, {y})")
                
                # 如果有压缩比例，应用压缩比例并确保结果为整数
                if hasattr(self, 'compression_scale') and self.compression_scale is not None:
                    x = int(round(x * self.compression_scale))
                    y = int(round(y * self.compression_scale))
                    print(f"[DEBUG] WatermarkRenderer._calculate_position: 修改position为 ({x}, {y})")
                    print(f"[DEBUG] 应用压缩比例 {self.compression_scale:.4f} 到水印坐标: ({x}, {y})")
                
                # 如果有current_watermark_settings，更新watermark_x和watermark_y
                # 详细检查条件，以便调试
                has_parent_attr = hasattr(self, 'parent')
                parent_exists = has_parent_attr and self.parent
                has_image_manager_attr = parent_exists and hasattr(self.parent, 'image_manager')
                
                # print(f"[DEBUG] WatermarkRenderer._calculate_position: 检查parent和image_manager属性:")
                # print(f"  - hasattr(self, 'parent'): {has_parent_attr}")
                # if has_parent_attr:
                #     print(f"  - self.parent: {self.parent}")
                #     print(f"  - self.parent is not None/Falsy: {bool(self.parent)}")
                # if parent_exists:
                #     print(f"  - hasattr(self.parent, 'image_manager'): {has_image_manager_attr}")
                
                # if not has_parent_attr:
                #     print(f"[DEBUG] WatermarkRenderer._calculate_position: 情况1: 当前对象没有parent属性")
                # elif not parent_exists:
                #     print(f"[DEBUG] WatermarkRenderer._calculate_position: 情况2: parent属性存在但值为None或False")
                # elif not has_image_manager_attr:
                #     print(f"[DEBUG] WatermarkRenderer._calculate_position: 情况3: parent对象存在但没有image_manager属性")
                
                if has_parent_attr and parent_exists and has_image_manager_attr:
                    current_watermark_settings = self.parent.image_manager.ensure_watermark_settings_initialized()
                    if current_watermark_settings is not None:
                        # 更新watermark_x和watermark_y
                        current_watermark_settings["watermark_x"] = int(round(x*self.compression_scale))
                        current_watermark_settings["watermark_y"] = int(round(y*self.compression_scale))
                        print(f"[DEBUG] WatermarkRenderer._calculate_position: 更新current_watermark_settings中的watermark_x为 {x}, watermark_y为 {y}")
                        
                        # 同时更新position
                        if hasattr(self, 'compression_scale') and self.compression_scale is not None and self.compression_scale > 0:
                            # 计算原图坐标
                            original_x = int(round(x))
                            original_y = int(round(y))
                            current_watermark_settings["position"] = (original_x, original_y)
                            print(f"[DEBUG] WatermarkRenderer._calculate_position: 更新current_watermark_settings中的position为 ({original_x}, {original_y})")
                    else:
                        print(f"[DEBUG] WatermarkRenderer._calculate_position: current_watermark_settings为None，无法更新坐标")
                
                # 在return前再次更新current_watermark_settings
                if has_parent_attr and parent_exists and has_image_manager_attr:
                    current_watermark_settings = self.parent.image_manager.ensure_watermark_settings_initialized()
                    if current_watermark_settings is not None:
                        current_watermark_settings["watermark_x"] = int(round(x*self.compression_scale))
                        current_watermark_settings["watermark_y"] = int(round(y*self.compression_scale))
                
                return x, y
            else:
                # 处理绝对坐标（九宫格计算出的原图坐标）
                print(f"[BRANCH] _calculate_position: 处理绝对坐标（九宫格计算出的原图坐标），x_ratio={x_ratio}, y_ratio={y_ratio}")
                # 这些坐标已经是基于原图的绝对坐标，直接使用position中的坐标
                x = int(round(position[0] ))
                y = int(round(position[1] ))
                print(f"[DEBUG] WatermarkRenderer._calculate_position: 修改position为 ({x}, {y})")
                
                # 如果有压缩比例，应用压缩比例并确保结果为整数
                if hasattr(self, 'compression_scale') and self.compression_scale is not None:
                    # x = int(round(x * self.compression_scale))
                    # y = int(round(y * self.compression_scale))
                    print(f"[DEBUG] WatermarkRenderer._calculate_position: 修改position为 ({x}, {y})")
                    print(f"[DEBUG] 应用压缩比例 {self.compression_scale:.4f} 到水印坐标: ({x}, {y})")
                
                # 如果有current_watermark_settings，更新watermark_x和watermark_y
                # 详细检查条件，以便调试
                has_parent_attr = hasattr(self, 'parent')
                parent_exists = has_parent_attr and self.parent
                has_image_manager_attr = parent_exists and hasattr(self.parent, 'image_manager')
                
                # print(f"[DEBUG] WatermarkRenderer._calculate_position: 检查parent和image_manager属性:")
                # print(f"  - hasattr(self, 'parent'): {has_parent_attr}")
                # if has_parent_attr:
                #     print(f"  - self.parent: {self.parent}")
                #     print(f"  - self.parent is not None/Falsy: {bool(self.parent)}")
                # if parent_exists:
                #     print(f"  - hasattr(self.parent, 'image_manager'): {has_image_manager_attr}")
                
                # if not has_parent_attr:
                #     print(f"[DEBUG] WatermarkRenderer._calculate_position: 情况1: 当前对象没有parent属性")
                # elif not parent_exists:
                #     print(f"[DEBUG] WatermarkRenderer._calculate_position: 情况2: parent属性存在但值为None或False")
                # elif not has_image_manager_attr:
                #     print(f"[DEBUG] WatermarkRenderer._calculate_position: 情况3: parent对象存在但没有image_manager属性")
                
                if has_parent_attr and parent_exists and has_image_manager_attr:
                    current_watermark_settings = self.parent.image_manager.ensure_watermark_settings_initialized()
                    if current_watermark_settings is not None:
                        # 更新watermark_x和watermark_y
                        current_watermark_settings["watermark_x"] = int(round(x*self.compression_scale))
                        current_watermark_settings["watermark_y"] = int(round(y*self.compression_scale))
                        print(f"[DEBUG] WatermarkRenderer._calculate_position: 更新current_watermark_settings中的watermark_x为 {x}, watermark_y为 {y}")
                        
                        # 同时更新position
                        if hasattr(self, 'compression_scale') and self.compression_scale is not None and self.compression_scale > 0:
                            # 计算原图坐标
                            original_x = int(round(x))
                            original_y = int(round(y))
                            current_watermark_settings["position"] = (original_x, original_y)
                            print(f"[DEBUG] WatermarkRenderer._calculate_position: 更新current_watermark_settings中的position为 ({original_x}, {original_y})")
                    else:
                        print(f"[DEBUG] WatermarkRenderer._calculate_position: current_watermark_settings为None，无法更新坐标")
                
                # 在return前再次更新current_watermark_settings
                if has_parent_attr and parent_exists and has_image_manager_attr:
                    current_watermark_settings = self.parent.image_manager.ensure_watermark_settings_initialized()
                    if current_watermark_settings is not None:
                        current_watermark_settings["watermark_x"] = int(round(x*self.compression_scale))
                        current_watermark_settings["watermark_y"] = int(round(y*self.compression_scale))
                
                return x, y
        
        # 处理预定义的位置字符串
        print(f"[BRANCH] _calculate_position: 处理预定义的位置字符串，position='{position}'")
        if position == "top-left":
            print(f"[BRANCH] _calculate_position: 执行top-left分支")
            x = margin
            y = margin
        elif position == "top-center":
            print(f"[BRANCH] _calculate_position: 执行top-center分支")
            x = (img_width - text_width) // 2
            y = margin
        elif position == "top-right":
            print(f"[BRANCH] _calculate_position: 执行top-right分支")
            x = img_width - text_width - margin
            y = margin
        elif position == "middle-left":
            print(f"[BRANCH] _calculate_position: 执行middle-left分支")
            x = margin
            y = (img_height - text_height) // 2
        elif position == "center":
            print(f"[BRANCH] _calculate_position: 执行center分支")
            x = (img_width - text_width) // 2
            y = (img_height - text_height) // 2
        elif position == "middle-right":
            print(f"[BRANCH] _calculate_position: 执行middle-right分支")
            x = img_width - text_width - margin
            y = (img_height - text_height) // 2
        elif position == "bottom-left":
            print(f"[BRANCH] _calculate_position: 执行bottom-left分支")
            x = margin
            y = img_height - text_height - margin
        elif position == "bottom-center":
            print(f"[BRANCH] _calculate_position: 执行bottom-center分支")
            x = (img_width - text_width) // 2
            y = img_height - text_height - margin
        elif position == "bottom-right":
            print(f"[BRANCH] _calculate_position: 执行bottom-right分支")
            x = img_width - text_width - margin
            y = img_height - text_height - margin
        else:
            print(f"[BRANCH] _calculate_position: 执行默认分支（未知位置字符串）")
            x = margin
            y = margin
            
        print(f"[DEBUG] WatermarkRenderer._calculate_position: 修改position为 ({x}, {y})")
        
        # 如果有current_watermark_settings，更新watermark_x和watermark_y
        # 详细检查条件，以便调试
        has_parent_attr = hasattr(self, 'parent')
        parent_exists = has_parent_attr and self.parent
        has_image_manager_attr = parent_exists and hasattr(self.parent, 'image_manager')
        
        # print(f"[DEBUG] WatermarkRenderer._calculate_position: 检查parent和image_manager属性:")
        # print(f"  - hasattr(self, 'parent'): {has_parent_attr}")
        # if has_parent_attr:
        #     print(f"  - self.parent: {self.parent}")
        #     print(f"  - self.parent is not None/Falsy: {bool(self.parent)}")
        # if parent_exists:
        #     print(f"  - hasattr(self.parent, 'image_manager'): {has_image_manager_attr}")
        
        # if not has_parent_attr:
        #     print(f"[DEBUG] WatermarkRenderer._calculate_position: 情况1: 当前对象没有parent属性")
        # elif not parent_exists:
        #     print(f"[DEBUG] WatermarkRenderer._calculate_position: 情况2: parent属性存在但值为None或False")
        # elif not has_image_manager_attr:
        #     print(f"[DEBUG] WatermarkRenderer._calculate_position: 情况3: parent对象存在但没有image_manager属性")
        
        if has_parent_attr and parent_exists and has_image_manager_attr:
            current_watermark_settings = self.parent.image_manager.ensure_watermark_settings_initialized()
            if current_watermark_settings is not None:
                # 更新watermark_x和watermark_y
                current_watermark_settings["watermark_x"] = int(round(x*self.compression_scale))
                current_watermark_settings["watermark_y"] = int(round(y*self.compression_scale))
                print(f"[DEBUG] WatermarkRenderer._calculate_position: 更新current_watermark_settings中的watermark_x为 {x}, watermark_y为 {y}")
                
                # 同时更新position
                if hasattr(self, 'compression_scale') and self.compression_scale is not None and self.compression_scale > 0:
                    # 计算原图坐标
                    original_x = int(round(x))
                    original_y = int(round(y))
                    current_watermark_settings["position"] = (original_x, original_y)
                    print(f"[DEBUG] WatermarkRenderer._calculate_position: 更新current_watermark_settings中的position为 ({original_x}, {original_y})")
            else:
                print(f"[DEBUG] WatermarkRenderer._calculate_position: current_watermark_settings为None，无法更新坐标")
        
        # 在return前再次更新current_watermark_settings
        if has_parent_attr and parent_exists and has_image_manager_attr:
            current_watermark_settings = self.parent.image_manager.ensure_watermark_settings_initialized()
            if current_watermark_settings is not None:
                current_watermark_settings["watermark_x"] = int(round(x*self.compression_scale))
                current_watermark_settings["watermark_y"] = int(round(y*self.compression_scale))
        
        return x, y
    
    def render_image_watermark(self, image, watermark_settings, is_preview=False):
        """
        渲染图片水印到图片上
        
        Args:
            image: PIL Image对象
            watermark_settings: 水印设置字典
            is_preview: 是否为预览模式，预览模式会应用压缩比例
            
        Returns:
            PIL Image对象（带水印的图片）
        """
        if not watermark_settings.get("image_path"):
            return image
        
        # 创建图片副本
        watermarked_image = image.copy()
        
        try:
            # 获取水印设置
            image_path = watermark_settings["image_path"]
            scale = watermark_settings.get("scale", 50) / 100.0  # 转换为比例
            opacity = watermark_settings.get("opacity", 80) / 100.0  # 转换为比例
            position = watermark_settings.get("position", (0.5, 0.5))  # 使用二元组表示中心位置
            keep_aspect_ratio = watermark_settings.get("keep_aspect_ratio", True)
            rotation = watermark_settings.get("rotation", 0)  # 旋转角度
            
            # 加载水印图片
            watermark_img = Image.open(image_path).convert("RGBA")
            
            # 调整水印图片大小
            original_width, original_height = watermark_img.size
            
            # 根据是否为预览模式决定是否应用压缩比例
            if is_preview:
                # 预览模式：应用压缩比例，使水印在预览图中大小合适
                new_width = int(original_width * scale * self.compression_scale)
                new_height = int(original_height * scale * self.compression_scale)
            else:
                # 导出模式：不应用压缩比例，使用原始比例
                new_width = int(original_width * scale)
                new_height = int(original_height * scale)
            
            # 如果需要保持纵横比，使用缩放比例
            if keep_aspect_ratio:
                watermark_img = watermark_img.resize((new_width, new_height), Image.LANCZOS)
            else:
                # 如果有单独指定的宽高，使用指定的宽高
                if "watermark_width" in watermark_settings and "watermark_height" in watermark_settings:
                    new_width = watermark_settings["watermark_width"]
                    new_height = watermark_settings["watermark_height"]
                    watermark_img = watermark_img.resize((new_width, new_height), Image.LANCZOS)
            
            # 调整透明度
            if opacity < 1.0:
                # 创建一个带有透明度的新图像
                r, g, b, a = watermark_img.split()
                a = a.point(lambda p: int(p * opacity))
                watermark_img = Image.merge('RGBA', (r, g, b, a))
            
            # 计算水印位置
            img_width, img_height = watermarked_image.size
            watermark_width, watermark_height = watermark_img.size
            print(f"[DEBUG] WatermarkRenderer.render_image_watermark: 使用position={position}计算水印位置")
            
            # 使用TextWatermarkWidget的坐标处理逻辑
            # 首先检查position是字符串还是元组
            if isinstance(position, str):
                # 如果是字符串位置（如"center"、"top-left"等），直接使用_calculate_position方法
                x, y = self._calculate_position(position, img_width, img_height, watermark_width, watermark_height)
            else:
                # 如果是元组位置，可能是相对位置（0-1之间的值）或绝对位置
                if isinstance(position, tuple) and len(position) >= 2:
                    x_ratio, y_ratio = position[0], position[1]
                    if 0 <= x_ratio <= 1 and 0 <= y_ratio <= 1:
                        # 相对位置（0-1之间的值）
                        print(f"[BRANCH] render_image_watermark: 处理相对位置（0-1之间的值），x_ratio={x_ratio}, y_ratio={y_ratio}")
                        # 计算绝对位置，直接转换为整数
                        x = int(round(img_width * x_ratio - watermark_width / 2))
                        y = int(round(img_height * y_ratio - watermark_height / 2))
                        print(f"[DEBUG] WatermarkRenderer.render_image_watermark: 计算出position为 ({x}, {y})")
                    else:
                        # 绝对位置（九宫格计算出的原图坐标）
                        print(f"[BRANCH] render_image_watermark: 处理绝对坐标（九宫格计算出的原图坐标），x_ratio={x_ratio}, y_ratio={y_ratio}")
                        x = int(round(position[0]))
                        y = int(round(position[1]))
                        print(f"[DEBUG] WatermarkRenderer.render_image_watermark: 使用绝对position为 ({x}, {y})")
                else:
                    # 默认使用(0.5, 0.5)位置
                    print(f"[BRANCH] render_image_watermark: 使用默认(0.5, 0.5)位置")
                    x_ratio, y_ratio = 0.5, 0.5
                    # 计算绝对位置，直接转换为整数
                    x = int(round(img_width * x_ratio - watermark_width / 2))
                    y = int(round(img_height * y_ratio - watermark_height / 2))
                    print(f"[DEBUG] WatermarkRenderer.render_image_watermark: 计算出position为 ({x}, {y})")
            
            # 如果是预览模式且有压缩比例，应用压缩比例并确保结果为整数
            # 注意：position是水印在原图上的坐标，watermark_x是水印在压缩图上的坐标
            # 关系：watermark_x = x * self.compression_scale（取整）
            if is_preview and hasattr(self, 'compression_scale') and self.compression_scale is not None:
                x = int(round(x * self.compression_scale))
                y = int(round(y * self.compression_scale))
                print(f"[DEBUG] WatermarkRenderer.render_image_watermark: 预览模式，应用压缩比例 {self.compression_scale:.4f} 到水印坐标: ({x}, {y})")
            else:
                print(f"[DEBUG] WatermarkRenderer.render_image_watermark: 导出模式，不应用压缩比例，水印坐标: ({x}, {y})")
            
            # 记录水印位置
            self.last_watermark_position = (x, y)
            print(f"[DEBUG] WatermarkRenderer.render_image_watermark: 图片水印初始化坐标: x={x}, y={y}")
            
            # 如果需要旋转，应用旋转
            if rotation != 0:
                # 保存原始尺寸
                original_width, original_height = watermark_img.size
                
                # 应用旋转
                watermark_img = watermark_img.rotate(rotation, expand=True, fillcolor=(0, 0, 0, 0))
                
                # 旋转后重新计算位置，确保水印中心点不变
                rotated_width, rotated_height = watermark_img.size
                x = x - (rotated_width - original_width) // 2
                y = y - (rotated_height - original_height) // 2
                
                print(f"[DEBUG] WatermarkRenderer.render_image_watermark: 应用旋转{rotation}度，旋转后尺寸: {rotated_width}x{rotated_height}，调整后坐标: x={x}, y={y}")
            
            # 根据模式选择坐标来源
            # 注意：position是水印在原图上的坐标，watermark_x是水印在压缩图上的坐标
            # 预览模式使用watermark_settings["watermark_x"]（压缩图上的坐标）
            # 导出模式使用position（原图上的坐标）
            if "watermark_x" in watermark_settings and "watermark_y" in watermark_settings:
                if is_preview:
                    # 预览模式使用手动指定的坐标
                    x = watermark_settings["watermark_x"]
                    y = watermark_settings["watermark_y"]
                    print(f"[DEBUG] WatermarkRenderer.render_image_watermark: 预览模式，使用手动指定坐标: ({x}, {y})")
                else:
                    # 导出模式使用position计算出的坐标（不使用手动指定的坐标）
                    print(f"[DEBUG] WatermarkRenderer.render_image_watermark: 导出模式，使用position计算出的坐标，忽略手动指定坐标")
                self.last_watermark_position = (x, y)
            
            # 如果有current_watermark_settings，更新watermark_x和watermark_y
            # 注意：position是水印在原图上的坐标，watermark_x是水印在压缩图上的坐标
            # 关系：watermark_x = x * self.compression_scale（取整）
            if hasattr(self, 'parent') and self.parent and hasattr(self.parent, 'image_manager'):
                current_watermark_settings = self.parent.image_manager.ensure_watermark_settings_initialized()
                if current_watermark_settings is not None:
                    # 如果是预览模式，需要将坐标转换回原始坐标（去除压缩比例）
                    if is_preview and hasattr(self, 'compression_scale') and self.compression_scale is not None and self.compression_scale != 0:
                        # 如果是使用手动指定坐标，直接保存
                        # 注意：watermark_settings["watermark_x"]已经是压缩图上的坐标，无需转换
                        if "watermark_x" in watermark_settings and "watermark_y" in watermark_settings:
                            current_watermark_settings["watermark_x"] = int(round(x))
                            current_watermark_settings["watermark_y"] = int(round(y))
                            print(f"[DEBUG] WatermarkRenderer.render_image_watermark: 预览模式，直接保存手动指定坐标({x}, {y})")
                        else:
                            # 如果是使用position计算坐标，需要转换回原始坐标
                            # 注意：position是原图上的坐标，预览时应用了压缩比例，现在需要去除压缩比例
                            # 关系：original_x = x / self.compression_scale
                            original_x = int(round(x / self.compression_scale))
                            original_y = int(round(y / self.compression_scale))
                            print(f"[DEBUG] WatermarkRenderer.render_image_watermark: 预览模式，将position计算坐标({x}, {y})转换回原始坐标({original_x}, {original_y})")
                            # 更新最终的watermark_x和watermark_y为原始坐标
                            current_watermark_settings["watermark_x"] = original_x
                            current_watermark_settings["watermark_y"] = original_y
                    else:
                        # 导出模式直接使用当前坐标
                        # 注意：导出模式使用position（原图上的坐标），不应用压缩比例
                        current_watermark_settings["watermark_x"] = int(round(x))
                        current_watermark_settings["watermark_y"] = int(round(y))
                        print(f"[DEBUG] WatermarkRenderer.render_image_watermark: 导出模式，直接使用当前坐标更新watermark_x为 {x}, watermark_y为 {y}")
                else:
                    print(f"[DEBUG] WatermarkRenderer.render_image_watermark: current_watermark_settings为None，无法更新最终坐标")
            
            # 将水印粘贴到主图片上
            watermarked_image.paste(watermark_img, (x, y), watermark_img)
            
        except Exception as e:
            print(f"Render image watermark failed: {e}")
            # 出错时返回原图的副本
            pass
        
        return watermarked_image
    
    def preview_watermark(self, image_path, watermark_settings, preview_size=None):
        """
        预览水印效果
        
        Args:
            image_path: 图片路径
            watermark_settings: 水印设置
            preview_size: 预览尺寸（设置为None，自动计算适合的预览尺寸）
            
        Returns:
            PIL Image对象（预览图片）和原始图片尺寸比例
        """
        try:
            # 加载原始图片
            original_image = Image.open(image_path)
            
            # 保存原始图片尺寸和比例
            original_width, original_height = original_image.size
            original_aspect_ratio = original_width / original_height
            
            # 计算适合的预览尺寸（480p到720p之间）
            if preview_size is None:
                # 定义目标分辨率范围
                min_dimension = 480  # 480p
                max_dimension = 720  # 720p
                
                # 计算缩放比例，使预览尺寸在480p到720p之间
                if original_width > max_dimension or original_height > max_dimension:
                    # 如果原图尺寸大于720p，按比例缩小到720p以内
                    if original_width > original_height:
                        # 横向图片，以宽度为基准
                        scale = max_dimension / original_width
                    else:
                        # 纵向图片，以高度为基准
                        scale = max_dimension / original_height
                elif original_width < min_dimension and original_height < min_dimension:
                    # 如果原图尺寸小于480p，按比例放大到480p
                    if original_width > original_height:
                        # 横向图片，以宽度为基准
                        scale = min_dimension / original_width
                    else:
                        # 纵向图片，以高度为基准
                        scale = min_dimension / original_height
                else:
                    # 原图尺寸已在480p到720p之间，不缩放
                    scale = 1.0
                
                # 计算预览尺寸
                preview_width = int(original_width * scale)
                preview_height = int(original_height * scale)
                
                print(f"[DEBUG] 原图尺寸: {original_width}x{original_height}, 缩放比例: {scale:.4f}, 预览尺寸: {preview_width}x{preview_height}")
            else:
                # 使用指定的预览尺寸
                preview_width, preview_height = preview_size
            
            # 创建预览图片（缩放到适合的尺寸）
            preview_image = original_image.copy()
            if preview_width != original_width or preview_height != original_height:
                preview_image = preview_image.resize((preview_width, preview_height), Image.LANCZOS)
            
            # 计算压缩比例
            # 注意：压缩比例用于将原图坐标转换为预览图坐标
            # 关系：预览图坐标 = 原图坐标 * compression_scale
            compression_scale = preview_width / original_width
            print(f"[DEBUG] 计算压缩比例: {compression_scale:.4f}")
            
            # 设置压缩比例，用于水印坐标计算
            self.compression_scale = compression_scale
            
            # 复制水印设置并根据水印类型进行调整
            adjusted_watermark_settings = watermark_settings.copy()
            watermark_type = watermark_settings.get("type", "text")
            
            # 根据水印类型选择不同的渲染方法
            if watermark_type == "text":
                # 调整水印字体大小，使其乘以压缩比例
                if "font_size" in adjusted_watermark_settings:
                    adjusted_font_size = int(adjusted_watermark_settings["font_size"] * compression_scale)
                    adjusted_watermark_settings["font_size"] = adjusted_font_size
                    print(f"[DEBUG] 调整字体大小: {watermark_settings['font_size']} -> {adjusted_font_size} (乘以压缩比例 {compression_scale:.4f})")
                
                # 应用文本水印
                watermarked_image = self.render_text_watermark(preview_image, adjusted_watermark_settings)
            elif watermark_type == "image":
                # 应用图片水印，使用TextWatermarkWidget的坐标处理逻辑
                watermarked_image = self.render_image_watermark(preview_image, adjusted_watermark_settings, is_preview=True)
            else:
                # 默认为文本水印
                watermarked_image = self.render_text_watermark(preview_image, adjusted_watermark_settings)
            
            # 确保水印位置是整数
            watermark_position = None
            if self.last_watermark_position is not None:
                # 直接存储为整数，不使用浮点数
                watermark_position = (int(self.last_watermark_position[0]), int(self.last_watermark_position[1]))
            
            # 返回水印预览图、原始图片比例信息和水印位置
            return watermarked_image, {
                'original_width': original_width,
                'original_height': original_height,
                'original_aspect_ratio': original_aspect_ratio,
                'preview_width': preview_width,
                'preview_height': preview_height,
                'scale_factor': preview_width / original_width,  # 添加缩放因子
                'watermark_position': watermark_position  # 添加水印位置信息
            }
            
        except Exception as e:
            print(f"Preview watermark failed: {e}")
            # Create error preview image
            error_image = Image.new('RGB', (800, 600), (255, 255, 255))
            draw = ImageDraw.Draw(error_image)
            draw.text((10, 10), f"Preview failed: {str(e)}", fill=(255, 0, 0))
            # Return error image and default ratio info
            return error_image, {
                'original_width': 800,
                'original_height': 600,
                'original_aspect_ratio': 800 / 600,
                'preview_width': 800,
                'preview_height': 600,
                'scale_factor': 1.0
            }