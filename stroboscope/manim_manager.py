# --- START OF FILE manim_manager.py ---

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
        # 尝试从 'src/manim_scenes' 目录加载外部模板文件
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
        # 注意：这里是修改后的 Manim 场景代码
        return """
from manim import *
import numpy as np

class StroboscopicEffectDynamic(Scene):
    def construct(self):
        # 设置背景
        self.camera.background_color = "#1a1a1a"
        
        # 创建圆盘（提高对比度与描边）
        circle_radius = 1.9
        disk = Circle(radius=circle_radius, color=BLUE_E, fill_opacity=0.85, stroke_width=5)
        
        # 创建标记点 - 更少更大更醒目
        mark_positions = []
        num_marks = 8  # 更少的标记能更清晰地观察 aliasing
        for i in range(num_marks):
            angle = i * 2 * PI / num_marks
            x = circle_radius * 0.9 * np.cos(angle)
            y = circle_radius * 0.9 * np.sin(angle)
            mark_positions.append([x, y, 0])
        
        marks = VGroup()
        for pos in mark_positions:
            mark = Dot(point=pos, radius=0.12, color=RED_E)
            marks.add(mark)
        
        # 添加中心点
        center_dot = Dot(radius=0.12, color=WHITE)

        # 添加几条辐条，进一步增强方向感
        spokes = VGroup()
        for theta in [0, PI/2, PI, 3*PI/2]:
            start = np.array([0, 0, 0])
            end = np.array([circle_radius * 0.95 * np.cos(theta), circle_radius * 0.95 * np.sin(theta), 0])
            spoke = Line(start, end, color=WHITE, stroke_width=6)
            spokes.add(spoke)
        
        # 组合所有元素
        rotating_disk = VGroup(disk, marks, center_dot, spokes)

        # 在顶部添加一个静态参考刻度，帮助感知方向
        reference_tick = Triangle(fill_opacity=1.0, color=YELLOW_E).scale(0.08)
        reference_tick.rotate(PI)
        reference_tick.move_to(np.array([0, circle_radius * 1.08, 0]))
        
        # 添加标题
        title = Text("频闪效应模拟", font_size=36, color=WHITE).to_edge(UP)
        
        # --- 从外部传入的参数，通过format替换 ---
        rotation_speed_rpm = {rotation_speed_rpm_placeholder}
        flash_frequency_hz = {flash_frequency_hz_placeholder}
        # ------------------------------------
        
        # 注意：此模板最终会被外层 Python 的 format() 处理，
        # 因此避免在源码中再使用花括号格式，改用百分号格式，防止 KeyError
        subtitle = Text("旋转速度: %.1f RPM | 闪烁频率: %.1f Hz" % (rotation_speed_rpm, flash_frequency_hz), 
               font_size=20, color=GRAY).next_to(title, DOWN)
        
        self.add(title, subtitle)
        self.add(rotating_disk)
        self.add(reference_tick)

        angular_speed = rotation_speed_rpm * 2 * PI / 60  # RPM to rad/sec
        
        total_animation_time = 10  # 动画总时长，可以配置
        
        # 添加说明文字
        explanation = Text("观察圆盘在频闪下的视觉效果", font_size=24, color=YELLOW).to_edge(DOWN)
        self.add(explanation)
        
        # --- 核心修改部分：处理 flash_frequency_hz == 0 的情况，并优化闪烁逻辑 ---
        if flash_frequency_hz == 0:
            # 如果闪烁频率为0，模拟连续旋转（常亮）
            # 圆盘持续可见，不进行闪烁逻辑
            self.play(
                Rotate(rotating_disk, angle=angular_speed * total_animation_time, 
                       about_point=ORIGIN, run_time=total_animation_time),
                rate_func=linear
            )
        else:
            # 正常频闪逻辑
            flash_interval = 1 / flash_frequency_hz
            # 确保 flash_duration 足够长，至少大于一帧时长，且小于或等于 flash_interval 的一定比例
            # 0.08 是一个相对合理的值，但如果 flash_interval 变得很小，可能需要调整
            # Manim 默认 60 FPS，所以一帧约 0.016667 秒
            # 由于该代码在 Manim 场景内运行，不能依赖后端对象，直接按60FPS计算最小帧时长
            min_frame_duration = 1 / 60
            
            # 为了获得更强的“定格”效果，缩短占空比
            flash_duration = min(flash_interval * 0.3, 0.08)
            flash_duration = max(flash_duration, min_frame_duration) # 确保至少一帧时长

            current_time = 0
            while current_time < total_animation_time:
                # 计算旋转角度
                angle_to_rotate = angular_speed * flash_interval
                
                # 隐藏阶段（模拟闪光灯关闭）
                # 只有当非闪烁时间足够长时才执行 FadeOut
                hide_time = flash_interval - flash_duration
                if hide_time > min_frame_duration: # 只有隐藏时间大于一帧才执行 FadeOut
                    self.play(
                        FadeOut(rotating_disk),
                        run_time=hide_time,
                        rate_func=linear
                    )
                elif hide_time > 0: # 如果小于一帧但大于0，就等待这段时间
                    self.wait(hide_time)
                
                # 显示阶段（模拟闪光灯开启）
                # 这里 Rotate 和 FadeIn 同时执行
                self.play(
                    Rotate(rotating_disk, angle=angle_to_rotate, about_point=ORIGIN, run_time=flash_duration),
                    FadeIn(rotating_disk),
                    rate_func=linear
                )
                
                current_time += flash_interval
        # --- 核心修改部分结束 ---

        # 最终等待
        self.wait(2)
        
        # 显示结束文字
        end_text = Text("动画结束", font_size=32, color=GREEN).move_to(ORIGIN)
        self.play(Write(end_text))
        self.wait(1)
"""
    
    def generate_scene_file(self, rotation_speed: float, flash_frequency: float, quality_level: int) -> tuple[str, str]:
        """生成场景文件"""
        unique_id = str(uuid.uuid4())
        
        # 关键：每次生成前刷新模板，避免进程热更新后缓存的旧模板仍含有花括号格式
        self.scene_template = self.load_scene_template()
        
        # 替换模板中的参数，注意：默认模板中只有两个占位符，所以只传递两个参数
        scene_code = self.scene_template.format(
            rotation_speed_rpm_placeholder=rotation_speed,
            flash_frequency_hz_placeholder=flash_frequency
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