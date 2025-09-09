# stroboscope_app
# (https://github.com/user-attachments/files/22235055/README.md)
# 频闪效应模拟器

一个基于Python Flask和Manim的交互式频闪效应模拟器，用于演示和教学频闪效应的视觉现象。

## 功能特点

- 🎯 **交互式控制**: 实时调整旋转速度和闪烁频率
- 🎨 **现代化UI**: 美观的渐变界面和响应式设计
- ⚡ **实时渲染**: 后台异步渲染，带进度显示
- 📱 **响应式设计**: 支持桌面和移动设备
- 🎛️ **预设模式**: 快速选择常用参数组合
- 📊 **可视化效果**: 清晰的圆盘和标记点设计

## 安装要求

### 系统要求
- Python 3.8+
- FFmpeg (用于视频处理)
- LaTeX (用于Manim文本渲染)

### Python依赖
```bash
pip install -r requirements.txt
```

## 安装步骤

1. **克隆或下载项目**
   ```bash
   git clone <repository-url>
   cd stroboscope_app
   ```

2. **安装Python依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **安装系统依赖**

   **Windows:**
   - 下载并安装 [FFmpeg](https://ffmpeg.org/download.html)
   - 下载并安装 [MiKTeX](https://miktex.org/) 或 [TeX Live](https://www.tug.org/texlive/)

   **macOS:**
   ```bash
   brew install ffmpeg
   brew install --cask mactex
   ```

   **Linux (Ubuntu/Debian):**
   ```bash
   sudo apt update
   sudo apt install ffmpeg texlive-full
   ```

4. **运行应用程序**
   ```bash
   python app.py
   ```

5. **打开浏览器访问**
   ```
   http://localhost:5000
   ```

## 使用方法

### 基本操作
1. **调整参数**: 使用滑块调整旋转速度(RPM)和闪烁频率(Hz)
2. **预设模式**: 点击预设按钮快速选择常用参数
3. **生成动画**: 点击"生成动画"按钮开始渲染
4. **观看效果**: 在右侧面板观看生成的动画

### 参数说明
- **旋转速度 (RPM)**: 圆盘的旋转速度，范围0-200转/分钟
- **闪烁频率 (Hz)**: 闪光灯的闪烁频率，范围0-100次/秒

### 频闪效应原理
- 当闪烁频率与旋转频率同步时，物体看起来静止
- 当闪烁频率略高于旋转频率时，物体看起来缓慢旋转
- 当闪烁频率略低于旋转频率时，物体看起来反向旋转

## 技术架构

### 后端
- **Flask**: Web框架
- **Manim**: 数学动画引擎
- **Threading**: 后台异步渲染
- **UUID**: 唯一文件标识

### 前端
- **HTML5**: 页面结构
- **CSS3**: 现代化样式和动画
- **JavaScript**: 交互逻辑和AJAX通信

# 频闪效应模拟器

一个基于Python Flask和Manim的交互式频闪效应模拟器，用于演示和教学频闪效应的视觉现象。

## 🎯 项目特点

- 🎨 **现代化UI**: 美观的渐变界面和响应式设计
- ⚡ **实时渲染**: 后台异步渲染，带详细进度显示
- 📊 **智能进度条**: 显示渲染进度、已用时间、预估时间等详细信息
- 🎛️ **多种质量选项**: 快速、标准、高质量三种渲染模式
- 📱 **响应式设计**: 支持桌面和移动设备
- 🔧 **模块化架构**: 清晰的代码结构和配置管理
- 📝 **完整日志**: 详细的运行日志和错误记录

## 📁 项目结构

```
stroboscope_app/
├── app.py                 # Flask主应用程序
├── config.ini            # 配置文件
├── requirements.txt       # Python依赖
├── README.md             # 项目说明
├── start.bat             # Windows启动脚本
├── start.sh              # Linux/Mac启动脚本
├── src/                  # 源代码目录
│   ├── __init__.py       # 模块初始化
│   ├── utils.py          # 工具模块（配置、文件、进度管理）
│   ├── manim_manager.py  # Manim场景管理器
│   └── render_engine.py  # 渲染引擎
├── templates/            # HTML模板
│   └── index.html        # 主页面
├── static/               # 静态文件
│   ├── animations/        # 生成的视频文件
│   ├── css/              # 样式文件
│   └── js/               # JavaScript文件
├── temp_files/           # 临时文件目录
├── logs/                 # 日志文件目录
└── src/manim_scenes/     # Manim场景文件目录
```

## 故障排除

### 常见问题

1. **Manim渲染失败**
   - 确保FFmpeg已正确安装
   - 检查LaTeX是否正确安装
   - 查看控制台错误信息

2. **视频无法播放**
   - 检查浏览器是否支持MP4格式
   - 确保视频文件已正确生成

3. **渲染速度慢**
   - 降低视频质量设置
   - 减少动画时长
   - 使用更快的硬件

### 调试模式
```bash
# 启用调试模式
export FLASK_DEBUG=1
python app.py
```

## 开发说明

### 自定义动画
修改 `MANIM_SCENE_TEMPLATE` 变量来自定义动画效果：
- 调整圆盘大小和颜色
- 修改标记点数量和样式
- 改变动画时长和效果

### 添加新功能
1. 在 `app.py` 中添加新的路由
2. 在 `templates/index.html` 中添加UI元素
3. 在JavaScript中添加交互逻辑

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 联系方式

如有问题或建议，请通过GitHub Issues联系。
