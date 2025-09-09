# --- START OF FILE app.py ---

"""
频闪效应模拟器主应用程序
"""

import os
import uuid
from flask import Flask, render_template, request, jsonify, url_for
from stroboscope import config_manager, file_manager, progress_monitor, logger, render_engine, scene_manager # 导入 scene_manager

app = Flask(__name__)

# 从配置文件加载设置
app.config['SECRET_KEY'] = config_manager.get('APP', 'SECRET_KEY', 'dev-secret-key')
app.config['DEBUG'] = config_manager.get('APP', 'DEBUG', 'True').lower() == 'true'

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/health')
def health():
    """健康检查"""
    return jsonify({
        'ok': True,
        'is_rendering': render_engine.is_busy()
    })

@app.route('/status')
def get_status():
    """获取渲染状态"""
    return jsonify(render_engine.get_render_status())

@app.route('/cleanup', methods=['POST'])
# 修改 app.py 中的 cleanup_old_videos 方法
def cleanup_old_videos():
    """清理旧的视频文件"""
    try:
        max_age_hours = int(config_manager.get('CLEANUP', 'AUTO_CLEANUP_HOURS', '1'))
        
        # 更健壮地处理 force 参数
        force_flag = False
        try:
            if request.method == 'GET':
                force_flag = request.args.get('force', '0').lower() in ['1', 'true']
            else:
                force_flag = request.form.get('force', '0').lower() in ['1', 'true']
        except Exception:
            force_flag = False
            
        # 调用 FileManager 提供的更全面的清理方法
        deleted_count = file_manager.cleanup_old_files(max_age_hours, delete_scenes_all=force_flag)
        
        logger.info(f"清理了 {deleted_count} 个旧文件")
        return jsonify({'success': True, 'deleted_count': deleted_count})
    except Exception as e:
        logger.error(f"清理文件失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/generate_animation', methods=['POST'])
def generate_animation():
    """生成频闪效应动画"""
    try:
        rotation_speed_rpm = float(request.form.get('rotation_speed', 30))
        flash_frequency_hz = float(request.form.get('flash_frequency', 25))
        render_quality = int(request.form.get('render_quality', 1))
        
        # 验证参数范围
        if rotation_speed_rpm < 0 or rotation_speed_rpm > 200:
            return jsonify({'success': False, 'message': '旋转速度必须在0-200 RPM之间'}), 400
        
        if flash_frequency_hz < 0 or flash_frequency_hz > 100:
            return jsonify({'success': False, 'message': '闪烁频率必须在0-100 Hz之间'}), 400
            
        if render_quality < 1 or render_quality > 3:
            return jsonify({'success': False, 'message': '渲染质量必须在1-3之间'}), 400
        
        # 检查是否正在渲染
        if render_engine.is_busy():
            return jsonify({'success': False, 'message': '正在渲染中，请稍候...'}), 409
        
        # 生成唯一ID
        unique_id = str(uuid.uuid4())
        
        # 启动渲染
        # 正确传递参数给渲染引擎（而不是传递字典）
        success = render_engine.render_animation(
            rotation_speed_rpm,
            flash_frequency_hz,
            render_quality,
            unique_id
        )
        
        if success:
            logger.info(f"开始渲染动画: {unique_id}")
            return jsonify({
                'success': True, 
                'message': '开始渲染动画...',
                'unique_id': unique_id
            })
        else:
            return jsonify({'success': False, 'message': '渲染引擎繁忙'}), 409
        
    except ValueError as e:
        logger.error(f"参数格式错误: {e}")
        return jsonify({'success': False, 'message': '参数格式错误'}), 400
    except Exception as e:
        logger.error(f"服务器错误: {e}")
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500

@app.route('/get_video/<unique_id>')
def get_video(unique_id):
    """获取渲染完成的视频"""
    video_path = file_manager.get_video_path(unique_id)
    
    if video_path and os.path.exists(video_path):
        # 确保 url_for 生成的路径正确，指向 static/animations 目录
        # 这里需要注意的是，url_for('static', filename=...) 期望 filename 是相对于 static 目录的路径
        # file_manager.get_video_path 返回的是绝对路径或相对项目根目录的路径
        # 所以我们需要提取 filename 相对 static/animations 的部分
        relative_video_path = os.path.relpath(video_path, app.static_folder).replace(os.sep, '/')
        video_url = url_for('static', filename=relative_video_path)
        return jsonify({'success': True, 'video_url': video_url})
    else:
        return jsonify({'success': False, 'message': '视频文件不存在'}), 404

if __name__ == '__main__':
    # 启动时清理旧文件
    try:
        max_age_hours = int(config_manager.get('CLEANUP', 'AUTO_CLEANUP_HOURS', '1'))
        deleted_count = file_manager.cleanup_old_files(max_age_hours) # 调用增强后的清理方法
        logger.info(f"启动时清理了 {deleted_count} 个旧文件")
    except Exception as e:
        logger.error(f"启动清理失败: {e}")
    
    # 获取配置
    host = config_manager.get('APP', 'HOST', '127.0.0.1')
    port = int(config_manager.get('APP', 'PORT', '5000'))
    debug = config_manager.get('APP', 'DEBUG', 'True').lower() == 'true'
    
    logger.info(f"启动频闪效应模拟器: http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
