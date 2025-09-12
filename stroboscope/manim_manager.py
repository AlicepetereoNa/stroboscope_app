"""
Manim场景管理器
负责生成和管理Manim动画场景
"""

import os
import uuid
from typing import Dict, Any
from .utils import config_manager, file_manager, logger

class ManimSceneManager:
    """Manim场景管理器"""
    
    def __init__(self):
        self.scene_template = self.load_scene_template()
        self.quality_settings = config_manager.get_quality_settings()
    
    def load_scene_template(self) -> str:
        """加载场景模板"""
        # 尝试从 'manim_scenes' 目录加载外部模板文件
        template_path = os.path.join(file_manager.scenes_dir, "manim_template.py")
        if os.path.exists(template_path):
            logger.info(f"从 {template_path} 加载Manim场景模板。")
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            logger.warning(f"未找到外部Manim场景模板文件: {template_path}，使用默认内置模板。")
            return self.get_default_template()
    
    def get_default_template(self) -> str:
        """获取默认模板"""
        # 完整的频闪效应模拟：圆盘不闪烁，只有指针运动和闪烁
        return """
from manim import *
import numpy as np

class StroboscopicEffectDynamic(Scene):
    def construct(self):
        # 设置背景
        self.camera.background_color = "#1a1a1a"
        
        # 创建圆盘（不闪烁，保持可见，不运动）
        circle_radius = 1.8
        disk = Circle(radius=circle_radius, color=BLUE, fill_opacity=0.3, stroke_width=3)
        
        # 创建ABCD四个刻度标记（不闪烁，保持可见）
        marks = VGroup()
        labels = VGroup()
        
        # 四个主要刻度位置：A(0°), B(90°), C(180°), D(270°)
        positions = [
            (0, "A"),      # 右侧 (0°)
            (PI/2, "B"),   # 上方 (90°)
            (PI, "C"),     # 左侧 (180°)
            (3*PI/2, "D")  # 下方 (270°)
        ]
        
        for angle, label_text in positions:
            # 创建刻度线
            start_point = 1.5 * np.array([np.cos(angle), np.sin(angle), 0])
            end_point = 1.8 * np.array([np.cos(angle), np.sin(angle), 0])
            mark = Line(start_point, end_point, color=WHITE, stroke_width=4)
            marks.add(mark)
            
            # 创建标签文字
            label_pos = 1.9 * np.array([np.cos(angle), np.sin(angle), 0])
            label = Text(label_text, font_size=24, color=YELLOW).move_to(label_pos)
            labels.add(label)
        
        # 添加中心点（不闪烁，保持可见）
        center_dot = Dot(radius=0.08, color=RED)
        
        # 创建指针（会闪烁和旋转）
        pointer = Line(ORIGIN, 1.4 * RIGHT, color=YELLOW, stroke_width=6)
        pointer.add_tip()
        
        # 组合圆盘、刻度和标签（静态部分）
        static_disk = VGroup(disk, marks, labels, center_dot)
        
        # 指针单独处理（动态部分）
        rotating_pointer = VGroup(pointer)
        
        # 添加标题
        title = Text("频闪效应模拟", font_size=36, color=WHITE, font="{font_family_placeholder}").to_edge(UP)
        
        # --- 从外部传入的参数，通过format替换 ---
        rotation_speed_rpm = {rotation_speed_rpm_placeholder}
        flash_frequency_hz = {flash_frequency_hz_placeholder}
        # ------------------------------------
        
        # 注意：此模板最终会被外层 Python 的 format() 处理，
        # 因此避免在源码中再使用花括号格式，改用百分号格式，防止 KeyError
        subtitle = Text("旋转速度: %.1f RPM | 闪烁频率: %.1f Hz" % (rotation_speed_rpm, flash_frequency_hz), 
               font_size=20, color=GRAY, font="{font_family_placeholder}").next_to(title, DOWN)
        
        # 添加调试信息
        total_animation_time = 12  # 动画时长
        total_rotations = rotation_speed_rpm * total_animation_time / 60
        total_flashes = flash_frequency_hz * total_animation_time
        rotation_period = 60.0 / rotation_speed_rpm  # 旋转一圈的时间
        rotation_frequency_hz = rotation_speed_rpm / 60  # 旋转频率(Hz)
        relative_frequency = flash_frequency_hz - rotation_frequency_hz  # 相对频率
        
        # 确定运动方向
        if relative_frequency > 0:
            direction_text = "顺时针"
        elif relative_frequency < 0:
            direction_text = "逆时针"
        else:
            direction_text = "静止"
            
        debug_info = Text("旋转: %.1f Hz，闪烁: %.1f Hz，观察: %.2f Hz (%s)" % 
                         (rotation_frequency_hz, flash_frequency_hz, abs(relative_frequency), direction_text), 
                         font_size=14, color=GREEN, font="{font_family_placeholder}").next_to(subtitle, DOWN)
        self.add(title, subtitle)
        self.add(static_disk)  # 添加静态圆盘
        self.add(rotating_pointer)  # 添加指针

        # 计算真实角速度 (RPM to rad/sec)
        angular_speed = rotation_speed_rpm * 2 * PI / 60
        
        # 添加测试信息
        rotation_frequency_hz = rotation_speed_rpm / 60
        relative_frequency = flash_frequency_hz - rotation_frequency_hz
        test_info = Text("帧运动：旋转%.1fHz，闪烁%.1fHz，相对%.2fHz" % 
                        (rotation_frequency_hz, flash_frequency_hz, relative_frequency), 
                        font_size=12, color=RED, font="{font_family_placeholder}")
        
        # 说明文字固定放在底部，避免与调试信息重叠
        explanation = Text("观察指针在频闪下的视觉效果 - 圆盘静止，指针旋转", font_size=20, color=YELLOW, font="{font_family_placeholder}").to_edge(DOWN)
        self.add(explanation)
        
        # --- 新的频闪逻辑：指针以相对速率一帧一帧运动 ---
        if flash_frequency_hz == 0:
            # 如果闪烁频率为0，连续旋转（常亮）
            self.play(
                Rotate(rotating_pointer, angle=angular_speed * total_animation_time, 
                       about_point=ORIGIN, run_time=total_animation_time),
                rate_func=linear
            )
        else:
            # 计算相对频率（引入修正系数 k，使 |fr| ∈ [0,1) ）
            rotation_frequency_hz = rotation_speed_rpm / 60  # 将RPM转换为Hz
            fr_raw = flash_frequency_hz - rotation_frequency_hz  # r - N（可正可负）
            sign_dir = 1 if fr_raw >= 0 else -1
            k = int(np.floor(abs(fr_raw)))
            fr_unit = abs(fr_raw) - k  # ∈ [0,1)
            fr = sign_dir * fr_unit     # 带方向的相对频率
            
            # 使用实际渲染 FPS
            fps = config.frame_rate
            frame_duration = 1.0 / fps
            relative_angular_speed = fr * 2 * PI  # rad/sec（可正可负）
            angle_per_frame = relative_angular_speed * frame_duration
            
            # 调试信息（覆盖并展示 k 与单位化频率）
            dir_text = "顺时针" if fr >= 0 else "逆时针"
            debug2 = Text("k=%d，单位化频率|fr|=%.3f，方向=%s" % (k, fr_unit, dir_text),
                          font_size=12, color=YELLOW, font="{font_family_placeholder}")
            
            # 计算总帧数
            total_frames = int(total_animation_time * fps)
            
            # 一帧一帧地运动：在同一指针上累计旋转
            for _ in range(total_frames):
                self.play(
                    Rotate(rotating_pointer, angle=angle_per_frame, about_point=ORIGIN, run_time=frame_duration),
                    rate_func=linear
                )

        # 将调试信息分组，统一放置在副标题下方，竖向排列，避免底部重叠
        info_group = VGroup(debug_info, test_info)
        if flash_frequency_hz != 0:
            info_group = VGroup(debug_info, test_info, debug2)
        info_group.arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        info_group.next_to(subtitle, DOWN, aligned_edge=LEFT)
        self.add(info_group)

        # 最终等待
        self.wait(2)
        
        # 显示结束文字
        end_text = Text("动画结束", font_size=32, color=GREEN, font="{font_family_placeholder}").move_to(ORIGIN)
        self.play(Write(end_text))
        self.wait(1)
"""
    
    def generate_scene_file(self, rotation_speed: float, flash_frequency: float, quality_level: int) -> tuple[str, str]:
        """生成场景文件"""
        unique_id = str(uuid.uuid4())
        
        # 关键：每次生成前刷新模板，避免进程热更新后缓存的旧模板仍含有花括号格式
        self.scene_template = self.load_scene_template()
        
        # 替换模板中的参数
        # 从配置读取中文字体，默认 Noto Sans CJK SC（需在服务器安装）
        font_family = config_manager.get('APP', 'FONT_FAMILY', 'Noto Sans CJK SC')
        scene_code = self.scene_template.format(
            rotation_speed_rpm_placeholder=rotation_speed,
            flash_frequency_hz_placeholder=flash_frequency,
            font_family_placeholder=font_family
        )
        
        # 生成文件路径
        filename = f"manim_scene_{unique_id}.py"
        file_path = os.path.join(file_manager.scenes_dir, filename)
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(scene_code)
        
        logger.info(f"生成场景文件: {filename}")
        return unique_id, file_path
    
    def get_quality_setting(self, quality_level: int) -> Dict[str, Any]:
        """获取质量设置"""
        return self.quality_settings.get(str(quality_level), self.quality_settings["1"])
    
    def cleanup_scene_file(self, file_path: str):
        """清理场景文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"清理场景文件: {os.path.basename(file_path)}")
        except Exception as e:
            logger.error(f"清理场景文件失败: {e}")

# 全局实例
scene_manager = ManimSceneManager()