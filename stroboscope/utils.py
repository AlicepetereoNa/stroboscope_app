# --- START OF FILE utils.py ---

"""
频闪效应模拟器工具模块
包含文件管理、进度监控、配置管理等工具函数
"""

import os
from pathlib import Path
import shutil
import time
import configparser
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import json # 确保导入 json
import threading

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.ini"):
        # Resolve project root as the repository root: one level up from this package directory
        self.project_root = Path(__file__).resolve().parents[1]
        # Ensure config path is relative to project root
        cfg_path = Path(config_file)
        self.config_file = str(cfg_path if cfg_path.is_absolute() else self.project_root / cfg_path)
        self.config = configparser.ConfigParser()
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file, encoding='utf-8')
        else:
            self.create_default_config()
    
    def create_default_config(self):
        """创建默认配置"""
        self.config['APP'] = {
            'DEBUG': 'True',
            'HOST': '127.0.0.1',
            'PORT': '5000',
            'SECRET_KEY': 'your-secret-key-here' # !!! 生产环境请务必修改此项 !!!
        }
        
        self.config['MANIM'] = {
            'QUALITY_SETTINGS': '{"1": {"flag": "-ql", "name": "快速", "resolution": "480p", "fps": 15, "time_estimate": "15-30秒"}, "2": {"flag": "-qm", "name": "标准", "resolution": "720p", "fps": 30, "time_estimate": "30-60秒"}, "3": {"flag": "-qh", "name": "高质量", "resolution": "1080p", "fps": 60, "time_estimate": "60-120秒"}}'
        }
        
        self.config['PATHS'] = {
            'TEMP_DIR': 'temp_files',
            'LOGS_DIR': 'logs',
            'MANIM_SCENES_DIR': 'manim_scenes',
            'VIDEO_OUTPUT_DIR': 'static/animations'
        }
        
        self.config['CLEANUP'] = {
            'AUTO_CLEANUP_HOURS': '1',
            'MAX_TEMP_FILES': '50'
        }
        
        self.save_config()
    
    def save_config(self):
        """保存配置文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)
    
    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(section, key, fallback=fallback)
    
    def get_quality_settings(self) -> Dict[str, Dict[str, Any]]:
        """获取质量设置"""
        settings_str = self.get('MANIM', 'QUALITY_SETTINGS', '{}')
        return json.loads(settings_str)

    def get_manim_fps(self, quality_level: int) -> int:
        """根据质量等级获取Manim渲染的FPS"""
        settings = self.get_quality_settings()
        # 默认返回 60 FPS，如果找不到对应设置，或者设置中没有 'fps' 键
        return settings.get(str(quality_level), {}).get('fps', 60)

class FileManager:
    """文件管理器"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        project_root = config_manager.project_root
        self.temp_dir = os.path.join(str(project_root), self.config.get('PATHS', 'TEMP_DIR', 'temp_files'))
        self.logs_dir = os.path.join(str(project_root), self.config.get('PATHS', 'LOGS_DIR', 'logs'))
        self.scenes_dir = os.path.join(str(project_root), self.config.get('PATHS', 'MANIM_SCENES_DIR', 'manim_scenes'))
        self.video_dir = os.path.join(str(project_root), self.config.get('PATHS', 'VIDEO_OUTPUT_DIR', 'static/animations'))
        
        # 如果配置里仍是旧路径 src/manim_scenes，则迁移到新路径 manim_scenes
        if os.path.normpath(self.scenes_dir).endswith(os.path.normpath(os.path.join('src', 'manim_scenes'))):
            self.scenes_dir = os.path.join(project_root, 'manim_scenes')
        
        # 确保目录存在
        self.ensure_directories()
    
    def ensure_directories(self):
        """确保所有必要的目录存在"""
        directories = [self.temp_dir, self.logs_dir, self.scenes_dir, self.video_dir]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def cleanup_old_files(self, max_age_hours: int = 1, delete_scenes_all: bool = False) -> int:
        """清理旧文件。增加 delete_scenes_all 参数，用于强制清理所有场景文件。"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        deleted_count = 0
        
        # 清理临时文件
        if os.path.exists(self.temp_dir):
            for filename in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, filename)
                # 仅删除文件，不删除子目录
                if os.path.isfile(file_path): 
                    file_age = current_time - os.path.getmtime(file_path) # 使用 getmtime 更准确
                    if file_age > max_age_seconds:
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                            logger.info(f"清理了旧临时文件: {file_path}")
                        except Exception as e:
                            logger.error(f"清理临时文件失败 {file_path}: {e}")
        
        # 清理视频文件 (Manim的输出，通常在 video_dir 下)
        if os.path.exists(self.video_dir):
            for root, dirs, files in os.walk(self.video_dir):
                for filename in files:
                    # Manim可能还会生成json文件，这些也应该被清理
                    if filename.endswith('.mp4') or filename.endswith('.json'): 
                        file_path = os.path.join(root, filename)
                        file_age = current_time - os.path.getmtime(file_path) # 使用 getmtime
                        if file_age > max_age_seconds:
                            try:
                                os.remove(file_path)
                                deleted_count += 1
                                logger.info(f"清理了旧视频/JSON文件: {file_path}")
                            except Exception as e:
                                logger.error(f"清理视频/JSON文件失败 {file_path}: {e}")

        # 清理Manim场景文件 (由 ManimSceneManager 生成)
        if os.path.exists(self.scenes_dir):
            for filename in os.listdir(self.scenes_dir):
                # 确保只删除生成的场景文件，而不是模板文件
                # 增加 `delete_scenes_all` 标志，如果为 True，则删除所有以 `manim_scene_` 开头的 .py 文件
                if filename.startswith('manim_scene_') and filename.endswith('.py'):
                    file_path = os.path.join(self.scenes_dir, filename)
                    file_age = current_time - os.path.getmtime(file_path) # 使用 getmtime
                    if delete_scenes_all or file_age > max_age_seconds:
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                            logger.info(f"清理了旧Manim场景文件: {file_path} (强制清理: {delete_scenes_all})")
                        except Exception as e:
                            logger.error(f"清理Manim场景文件失败 {file_path}: {e}")
        
        return deleted_count
    
    def get_video_path(self, unique_id: str) -> str:
        """
        根据 unique_id 获取预期视频文件路径，不检查是否存在。
        渲染引擎会负责在渲染完成后确认文件存在。
        """
        video_pattern = f"stroboscope_{unique_id}.mp4"
        return os.path.join(self.video_dir, video_pattern)

class ProgressMonitor:
    """进度监控器"""
    
    def __init__(self):
        self.status = {
            'is_rendering': False,
            'progress': 0,
            'current_task': '',
            'error': None,
            'start_time': None,
            'estimated_time': '未知', # 确保始终有默认值
            'current_animation': 0,
            'total_animations': 0,
            'elapsed_time': '0.0秒' # 确保始终有默认值
        }
        self.lock = threading.Lock() # 添加线程锁
    
    def _update_status_safely(self, **kwargs):
        """线程安全地更新状态"""
        with self.lock:
            self.status.update(kwargs)

    def start_render(self, estimated_time: str = None):
        """开始渲染"""
        self._update_status_safely(
            is_rendering=True,
            progress=0,
            current_task='准备渲染...',
            error=None,
            start_time=time.time(),
            estimated_time=estimated_time if estimated_time else '未知',
            current_animation=0,
            total_animations=0,
            elapsed_time='0.0秒'
        )
    
    def update_progress(self, progress: int, task: str, current_animation: int = None, total_animations: int = None):
        """更新进度"""
        updates = {
            'progress': min(progress, 100),
            'current_task': task
        }
        if current_animation is not None:
            updates['current_animation'] = current_animation
        if total_animations is not None:
            updates['total_animations'] = total_animations
        
        self._update_status_safely(**updates)
    
    def finish_render(self, success: bool = True, error: str = None):
        """完成渲染"""
        with self.lock: # 锁定以确保状态更新的原子性
            self.status.update({
                'is_rendering': False,
                'progress': 100 if success else self.status['progress'],
                'current_task': '渲染完成！' if success else f'渲染失败: {error}',
                'error': error if not success else None
            })
            if self.status['start_time']:
                elapsed_time_val = time.time() - self.status['start_time']
                self.status['elapsed_time'] = f"{elapsed_time_val:.1f}秒"
            else:
                self.status['elapsed_time'] = '0.0秒'
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        with self.lock: # 读取状态时也需要锁定
            status = self.status.copy()
        
        # 计算已用时间（在获取时计算，避免频繁更新状态）
        if status['is_rendering'] and status['start_time']: # 只在渲染中才动态计算
            elapsed_time_val = time.time() - status['start_time']
            status['elapsed_time'] = f"{elapsed_time_val:.1f}秒"
        
        return status

class Logger:
    """日志管理器"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.logs_dir = self.config.get('PATHS', 'LOGS_DIR', 'logs')
        self.setup_logging()
    
    def setup_logging(self):
        """设置日志"""
        os.makedirs(self.logs_dir, exist_ok=True) # 确保日志目录存在
        log_file = os.path.join(self.logs_dir, f"stroboscope_{datetime.now().strftime('%Y%m%d')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('stroboscope')
    
    def info(self, message: str):
        """记录信息日志"""
        self.logger.info(message)
    
    def error(self, message: str):
        """记录错误日志"""
        self.logger.error(message)
    
    def warning(self, message: str):
        """记录警告日志"""
        self.logger.warning(message)

    def debug(self, message: str):
        """记录调试日志"""
        self.logger.debug(message)

# 全局实例
config_manager = ConfigManager()
file_manager = FileManager(config_manager)
progress_monitor = ProgressMonitor()
logger = Logger(config_manager)