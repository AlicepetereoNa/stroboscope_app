# 频闪效应模拟器 (Stroboscope App) ✨🔦

一个基于 Flask + Manim 的频闪效应可视化应用。支持设置旋转频率与闪烁频率，使用“相对频率逐帧法”生成视频：指针以 (r − N) 的相对速率逐帧运动，方向由相对频率正负决定，圆盘静止且标注 ABCD 四象限。

## 功能特性 🌟
- 🟦 圆盘静止、ABCD 四象限刻度与中心点
- 🔁 指针按相对频率 r −k - N 逐帧旋转（r=闪烁频率 Hz，N=旋转频率 Hz，k=调整系数）
- 🎛️ 渲染质量三档（快速/标准/高质量）
- 📈 渲染进度/状态查询
- 🧹 自动清理旧产物

## 环境要求 🧰
- 🐍 Python 3.10+
- 🧮 Manim (Community)
- 🎬 FFmpeg 可执行（用于输出 mp4）
- 🪟 Windows 10/11（已适配），其他平台按需调整

### 安装 ⚙️
```bash
# 进入项目目录
cd stroboscope_app

# 安装依赖
pip install -r requirements.txt

# 安装/确认 manim 与 ffmpeg（任选其一方式）
# conda:
conda install -c conda-forge manim ffmpeg
# 或 pip manim，另外确保 ffmpeg 在 PATH
```

> ✅ 验证：`manim -v` 与 `ffmpeg -version` 均可正常输出版本信息。

## 启动 🚀
```bash
python app.py
# 访问 http://127.0.0.1:5000
```

## 使用说明 🖱️
- 页面滑块设置：
  - ⏱️ 旋转频率（Hz）：指针实际旋转频率 N（内部会换算为 RPM 传给后端）
  - 💡 闪烁频率（Hz）：闪光发生频率 r
  - 🧩 渲染质量：1 快速(低分辨率/低 FPS)、2 标准、3 高质量
- 点击“生成动画”，等待进度完成后自动显示视频。

## 频闪实现（相对频率逐帧法）🧠
- 基本定义：相对频率 fr_raw = r − N（单位 Hz）
- 修正系数 k 的引入（使频率单位化到 [0,1) 并保留方向）：
  - k = ⌊|fr_raw|⌋
  - fr_unit = |fr_raw| − k ∈ [0,1)
  - fr = sign(fr_raw) × fr_unit
- 每帧角度步进：`Δθ = fr * 2π / fps`，其中 fps 为实际渲染帧率（由质量档位配置）
- 动画采用累计旋转：在同一指针对象上以 `run_time = 1/fps` 的节拍逐帧旋转，避免“过短等待”警告并与视频帧对齐。
- 方向说明：
  - ➕ fr > 0：指针顺时针（正方向）
  - ➖ fr < 0：指针逆时针（负方向）
  - 🟰 fr = 0：指针静止

## 后端接口 🔌
- `POST /generate_animation`
  - form 参数：
    - `rotation_speed` 数值（RPM，前端已将 Hz×60 换算）
    - `flash_frequency` 数值（Hz）
    - `render_quality` 枚举 {1,2,3}
  - 成功返回：`{ success: true, unique_id }`
- `GET /status`：返回渲染状态（进度、任务、耗时、错误等）
- `GET /get_video/<unique_id>`：返回视频 URL（`/static/animations/...mp4`）
- `POST /cleanup?force=1`：清理历史产物（含临时场景脚本、视频与 JSON）
- `GET /health`：健康检查与是否渲染中

## 配置 ⚙️🗂️
编辑 `config.ini`（不存在时会自动生成默认）：
- `[APP]` HOST/PORT/DEBUG/SECRET_KEY
- `[MANIM]` QUALITY_SETTINGS 三档参数（flag/fps/resolution/time_estimate）
- `[PATHS]` 目录：
  - `VIDEO_OUTPUT_DIR` 默认 `static/animations`
  - `MANIM_SCENES_DIR` 默认 `manim_scenes`
  - `LOGS_DIR` 默认 `logs`
- `[CLEANUP]` 自动清理时长等

## 关键路径 📁
- 📝 日志：`logs/stroboscope_YYYYMMDD.log`
- 🎞️ 输出视频：`static/animations/stroboscope_<uuid>.mp4`
- 🧾 临时场景：`manim_scenes/manim_scene_<uuid>.py`（渲染后自动清理）

## 常见问题（Troubleshooting）🧯
- ❌ 渲染失败（返回码 1）：
  - 确认 `manim` 与 `ffmpeg` 已安装，且可在当前环境调用
  - OpenGL 不可用时，后端会自动回退到 Cairo
  - 查看日志关键输出（包含 Manim 命令与剩余输出）
- 🕳️ 渲染成功但找不到视频：
  - 已在 `static/animations`、以及 `media/` 树下尝试查找并复制到统一目录
  - 仍无产物时，检查日志中的“目录快照”与 Manim 输出
- 🌫️ 视频只有闪烁、无旋转：
  - 相对频率 |fr_raw| 太低，或帧率过低导致步进不明显；检查 k 修正后的 fr 是否接近 0
  - 提高 `render_quality`（提高 FPS），或设置更大的 |r − N|
- ⏱️ `wait too short for FPS`：
  - 现已按 `config.frame_rate` 逐帧对齐并用 `run_time = 1/fps` 驱动，问题已修复

## 架构概览 🧭
- `app.py`：Flask 入口、路由与参数校验
- `stroboscope/utils.py`：配置、文件、日志、进度管理
- `stroboscope/manim_manager.py`：场景模板生成（ABCD 刻度、圆盘静止、相对频率逐帧法+k 修正）
- `stroboscope/render_engine.py`：子进程调用 Manim，解析进度，产出视频并归位

## 开发建议 🛠️
- 修改场景模板可在 `stroboscope/manim_manager.py::get_default_template` 中进行
- 大幅修改前先提升日志级别，便于定位渲染命令与输出
- 若需要 GPU/OpenGL，确保本机驱动与 OpenGL 环境可用；否则 Cairo 模式即可

## 许可证 📄
MIT License
