# --- START OF FILE render_engine.py ---

"""
渲染引擎
负责执行Manim渲染任务并监控进度
"""

import os
import sys
import subprocess
import threading
import time
import shutil
import re # 导入正则表达式模块
from typing import Dict, Any, Optional
from .utils import config_manager, file_manager, progress_monitor, logger

# 确保导入 scene_manager
from .manim_manager import scene_manager

class RenderEngine:
    """渲染引擎"""
    
    def __init__(self):
        self.is_rendering = False
        self.current_thread = None
        self._lock = threading.Lock() # 添加一个锁来保护 is_rendering
    
    def is_busy(self) -> bool:
        """检查是否正在渲染 (线程安全)"""
        with self._lock:
            return self.is_rendering

    def _set_rendering_status(self, status: bool):
        """设置渲染状态 (线程安全)"""
        with self._lock:
            self.is_rendering = status

    def render_animation(self, rotation_speed: float, flash_frequency: float, 
                        quality_level: int, unique_id: str) -> bool:
        """渲染动画"""
        if self.is_busy():
            logger.warning("渲染任务正在进行中，请稍候...")
            return False
        
        # 获取质量设置
        quality_setting = scene_manager.get_quality_setting(quality_level)
        estimated_time = quality_setting.get('time_estimate', '未知')
        
        # 启动渲染线程
        # 设置渲染状态为 True
        self._set_rendering_status(True) 
        self.current_thread = threading.Thread(
            target=self._render_thread,
            args=(rotation_speed, flash_frequency, quality_level, unique_id, estimated_time),
            name=f"ManimRenderThread-{unique_id}" # 命名线程便于调试
        )
        self.current_thread.daemon = True # 设置为守护线程，主程序退出时会强制停止
        self.current_thread.start()
        
        return True
    
    def _render_thread(self, rotation_speed: float, flash_frequency: float, 
                      quality_level: int, unique_id: str, estimated_time: str):
        """渲染线程"""
        scene_file_path = None # 初始化为 None
        final_video_output_path = None # 初始化为 None
        try:
            progress_monitor.start_render(estimated_time)

            # 检查 ffmpeg 是否可用（Manim 生成 mp4 必需）
            try:
                import shutil as _shutil
                ffmpeg_path = _shutil.which("ffmpeg")
            except Exception:
                ffmpeg_path = None
            if not ffmpeg_path:
                raise Exception(
                    "未检测到 ffmpeg，无法生成 mp4。请安装后重试（conda install -c conda-forge ffmpeg / scoop install ffmpeg / choco install ffmpeg）。"
                )
            
            # 生成场景文件
            progress_monitor.update_progress(10, "生成动画代码...")
            # 关键修改：传递 quality_level 参数给 scene_manager.generate_scene_file
            scene_unique_id, scene_file_path = scene_manager.generate_scene_file(
                rotation_speed, flash_frequency, quality_level
            )
            
            # 获取质量设置
            quality_setting = scene_manager.get_quality_setting(quality_level)
            quality_flag = quality_setting['flag'] # 例如 "-ql", "-qm", "-qh"
            
            # 构建Manim命令
            progress_monitor.update_progress(20, "准备渲染参数...")
            
            output_filename = f"stroboscope_{unique_id}.mp4" 
            
            # --- 关键修改：确保所有传递给 Manim 的路径都使用正斜杠 ---
            # 获取绝对路径，然后替换所有反斜杠为正斜杠
            # absolute_video_output_dir_for_manim = os.path.abspath(file_manager.video_dir).replace('\\', '/')
            # scene_file_path_for_manim = os.path.abspath(scene_file_path).replace('\\', '/')
            absolute_video_output_dir_for_manim = os.path.abspath(file_manager.video_dir)
            scene_file_path_for_manim = os.path.abspath(scene_file_path)
            
            # Python内部检查时使用的路径，仍然使用 os.path.join
            final_video_output_path = os.path.join(file_manager.video_dir, output_filename) 
            
            logger.info(f"预期最终视频输出路径 (Python内部): {final_video_output_path}")
            logger.info(f"传递给Manim的媒体目录: {absolute_video_output_dir_for_manim}")
            logger.info(f"传递给Manim的场景文件路径: {scene_file_path_for_manim}")

            # 优先通过当前 Python 解释器调用 manim，避免 PATH 问题
            def build_manim_command(renderer: str) -> list[str]:
                return [
                    sys.executable, "-m", "manim",
                    "render",
                    "--renderer", renderer,
                    "--format", "mp4",
                    quality_flag,          # 质量标志，例如 -qh, -qm, -ql
                    "--disable_caching",   # 禁用缓存
                    "--media_dir", absolute_video_output_dir_for_manim, # 指定媒体输出目录
                    "--output_file", output_filename, # 指定输出文件名
                    "--progress_bar", "display", # 明确显示进度条
                    "--fps", str(quality_setting.get('fps', 60)), # 设置 FPS
                    scene_file_path_for_manim, # 场景文件路径
                    "StroboscopicEffectDynamic" # 场景类名
                ]

            manim_command = build_manim_command("opengl")
            
            logger.info(f"Manim命令: {' '.join(manim_command)}")

            # 执行渲染
            progress_monitor.update_progress(30, "启动Manim渲染...")
            logger.info(f"开始渲染动画: {output_filename}")
            
            # 启动子进程并实时读取输出
            process = subprocess.Popen(
                manim_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # 将 stderr 合并到 stdout，方便统一读取进度
                text=True,
                bufsize=1, # 行缓冲
                universal_newlines=True
            )
            
            # 监控渲染进度（改进版）
            self._monitor_render_progress_from_stdout(process, unique_id)
            
            # 等待进程完成
            process.wait() # 实时读取stdout后，只需等待进程结束
            
            # 在检查文件前稍作等待，给文件系统一点时间
            time.sleep(1) 

            if process.returncode == 0:
                # 查找生成的视频文件
                progress_monitor.update_progress(90, "处理输出文件...")
                
                # 增强文件查找逻辑：即使指定了 --output_file，也再次确认
                found_video_path = self._find_generated_video(unique_id)
                
                if found_video_path and os.path.exists(found_video_path):
                    # 将结果统一复制/移动到 static/animations 目录，确保前端可访问
                    try:
                        if os.path.normpath(found_video_path) != os.path.normpath(final_video_output_path):
                            os.makedirs(os.path.dirname(final_video_output_path), exist_ok=True)
                            shutil.copy2(found_video_path, final_video_output_path)
                            logger.info(f"已将视频复制到统一目录: {final_video_output_path}")
                        final_video_output_path = final_video_output_path
                    except Exception as cp_err:
                        logger.warning(f"复制渲染结果到统一目录失败，将直接使用原始路径: {found_video_path}，错误: {cp_err}")
                        final_video_output_path = found_video_path
                    
                    progress_monitor.finish_render(success=True)
                    logger.info(f"动画渲染完成: {output_filename}, 路径: {final_video_output_path}")
                else:
                    logger.error(f"Manim渲染成功，但未找到生成的视频文件: {final_video_output_path} 或其他位置。")
                    # 读取剩余输出，以防有延迟的错误信息
                    remaining_output = process.stdout.read()
                    raise Exception(f"Manim渲染成功，但未找到生成的视频文件。请检查Manim输出目录。Manim剩余输出: {remaining_output}")
            else:
                # 如果 opengl 失败，尝试回退到 cairo 渲染器
                logger.warning(f"使用 OpenGL 渲染失败 (返回码: {process.returncode})，尝试使用 Cairo 渲染器重试...")
                try:
                    manim_command_fallback = build_manim_command("cairo")
                    logger.info(f"Manim回退命令: {' '.join(manim_command_fallback)}")
                    process_fb = subprocess.Popen(
                        manim_command_fallback,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        universal_newlines=True
                    )
                    self._monitor_render_progress_from_stdout(process_fb, unique_id)
                    process_fb.wait()
                    time.sleep(1)

                    if process_fb.returncode == 0:
                        progress_monitor.update_progress(90, "处理输出文件...")
                        found_video_path = self._find_generated_video(unique_id)
                        if found_video_path and os.path.exists(found_video_path):
                            final_video_output_path = found_video_path
                            progress_monitor.finish_render(success=True)
                            logger.info(f"动画渲染完成(回退cairo): {output_filename}, 路径: {final_video_output_path}")
                        else:
                            remaining_output_fb = process_fb.stdout.read() if process_fb.stdout else ""
                            raise Exception(f"Manim回退渲染成功，但未找到视频文件。输出: {remaining_output_fb}")
                    else:
                        remaining_output_fb = process_fb.stdout.read() if process_fb.stdout else ""
                        raise Exception(f"Manim回退渲染失败 (返回码: {process_fb.returncode}). 输出: {remaining_output_fb}")
                except Exception as fb_err:
                    remaining_output = process.stdout.read() if process.stdout else ""
                    full_error_message = f"Manim渲染失败 (返回码: {process.returncode}). 输出: {remaining_output}；回退失败: {fb_err}"
                    logger.error(full_error_message)
                    raise Exception(full_error_message)
                
        except Exception as e:
            progress_monitor.finish_render(success=False, error=str(e))
            logger.error(f"渲染过程中发生异常: {e}")
        finally:
            self._set_rendering_status(False) # 渲染结束，设置状态为 False
            # 清理场景文件
            if scene_file_path and os.path.exists(scene_file_path):
                scene_manager.cleanup_scene_file(scene_file_path)
            
            # 确保删除 Manim 可能生成的额外文件，例如 .json 文件
            # Manim 0.17.x 通常会生成一个与视频同名的 .json 文件
            if final_video_output_path: # 只有当视频路径已确定时才尝试删除json
                json_file_path = final_video_output_path.replace('.mp4', '.json')
                if os.path.exists(json_file_path):
                    try:
                        os.remove(json_file_path)
                        logger.info(f"清理了Manim生成的json文件: {json_file_path}")
                    except Exception as e:
                        logger.error(f"清理Manim生成的json文件失败: {e}")

    def _monitor_render_progress_from_stdout(self, process: subprocess.Popen, unique_id: str):
        """通过解析Manim的stdout实时监控渲染进度"""
        progress_monitor.update_progress(40, "正在渲染动画...")
        
        progress_regex_detailed = re.compile(
            r".*?\[(\d{2}):(\d{2}):(\d{2})/(\d{2}):(\d{2}):(\d{2})\]\s+(\d+)%\s+Playing Animation:.*"
        )
        progress_regex_simple = re.compile(r".*?Progress:\s*(\d+)%")
        
        last_reported_progress = 30 # 从30%开始监控，因为前面有准备步骤
        
        # 实时读取 Manim 进程的输出
        for line in process.stdout:
            # 统一用 info，避免旧进程中 Logger 没有 debug 方法导致异常
            logger.info(f"Manim Output: {line.strip()}")
            
            match_detailed = progress_regex_detailed.match(line)
            if match_detailed:
                try:
                    current_h, current_m, current_s, total_h, total_m, total_s, percentage_str = match_detailed.groups()
                    current_seconds = int(current_h) * 3600 + int(current_m) * 60 + int(current_s)
                    total_seconds = int(total_h) * 3600 + int(total_m) * 60 + int(total_s)
                    percentage = int(percentage_str)
                    
                    # 将 Manim 的 0-100% 映射到我们的 40-85% 范围
                    mapped_progress = int(40 + (percentage / 100) * (85 - 40))
                    if mapped_progress > last_reported_progress:
                        progress_monitor.update_progress(mapped_progress, f"正在渲染动画... ({percentage}%)")
                        last_reported_progress = mapped_progress
                        logger.info(f"渲染进度更新: {mapped_progress}% ({line.strip()})")
                except Exception as e:
                    logger.warning(f"解析Manim详细进度失败: {line.strip()}, 错误: {e}")
                continue # 处理完这行就进入下一行

            match_simple = progress_regex_simple.match(line)
            if match_simple:
                try:
                    percentage = int(match_simple.group(1))
                    mapped_progress = int(40 + (percentage / 100) * (85 - 40))
                    if mapped_progress > last_reported_progress:
                        progress_monitor.update_progress(mapped_progress, f"正在渲染动画... ({percentage}%)")
                        last_reported_progress = mapped_progress
                        logger.info(f"渲染进度更新: {mapped_progress}% ({line.strip()})")
                except Exception as e:
                    logger.warning(f"解析Manim简单进度失败: {line.strip()}, 错误: {e}")
                continue
            
            # 如果 Manim 输出中包含错误信息，也记录下来
            if "ERROR" in line.upper() or "FATAL" in line.upper():
                logger.error(f"Manim子进程错误输出: {line.strip()}")
                progress_monitor.update_progress(last_reported_progress, f"Manim警告/错误: {line.strip()}")
        
        # 渲染循环结束后，确保进度条至少达到85%
        if last_reported_progress < 85:
            progress_monitor.update_progress(85, "渲染完成，处理文件...")

    def _find_generated_video(self, unique_id: str) -> Optional[str]:
        """
        在常见的 Manim 输出目录中查找与 unique_id 匹配的视频文件。
        1) 优先检查配置的视频目录
        2) 兼容查找项目根下的 media/ 与 media/videos/ 目录
        """
        video_pattern = f"stroboscope_{unique_id}.mp4"
        search_roots = [
            file_manager.video_dir,
            os.path.join(file_manager.video_dir, 'videos'),
            os.path.join(os.getcwd(), 'media'),
            os.path.join(os.getcwd(), 'media', 'videos')
        ]

        for root_dir in search_roots:
            if not os.path.exists(root_dir):
                continue
            logger.info(f"尝试在 {root_dir} 及其子目录中查找视频文件: {video_pattern}")

            expected_path = os.path.join(root_dir, video_pattern)
            if os.path.exists(expected_path):
                logger.info(f"视频文件在预期路径找到: {expected_path}")
                return expected_path

            # 遍历子目录
            for root, _, files in os.walk(root_dir):
                for file in files:
                    # 精确匹配或包含 unique_id 的 mp4 文件都接受（不同 Manim 版本可能附加后缀）
                    if file == video_pattern or (file.endswith('.mp4') and unique_id in file):
                        found_path = os.path.join(root, file)
                        logger.info(f"视频文件通过遍历找到: {found_path}")
                        return found_path

        # 输出关键目录快照，帮助定位
        try:
            for probe in [file_manager.video_dir, os.path.join(file_manager.video_dir, 'videos')]:
                if os.path.exists(probe):
                    entries = ", ".join(sorted(os.listdir(probe)))
                    logger.warning(f"目录快照 {probe}: {entries}")
                else:
                    logger.warning(f"目录不存在 {probe}")
        except Exception as snap_err:
            logger.warning(f"列举目录失败: {snap_err}")

        logger.warning(f"未能在常见目录中找到视频文件: {video_pattern}")
        return None

    def get_render_status(self) -> Dict[str, Any]:
        """获取渲染状态"""
        return progress_monitor.get_status()
    
# 全局实例
render_engine = RenderEngine()