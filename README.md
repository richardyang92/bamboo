# Bamboo - AI 智能绘图、文档生成与数学动画工作流

一个使用LangGraph框架构建的AI Agent，支持智能绘图、高质量Markdown文档生成和数学动画制作。

## 功能特性

### 📊 智能绘图
- ✅ **AI驱动**：使用DeepSeek模型生成高质量绘图代码
- 📊 **Matplotlib支持**：生成各种类型的图表（折线图、柱状图、散点图等）
- 🔄 **自动化流程**：用户输入 → 代码生成 → 执行 → 保存图片
- 📁 **本地保存**：自动将生成的图表保存到本地
- 🎯 **中文支持**：完美支持中文显示
- 🛡️ **空白图像防护**：智能检测并防止生成空白图像，包含详细的错误检查清单
- 🎨 **流程图支持**：支持生成专业的流程图和架构图
- 🧠 **智能识别**：根据描述类型自动选择最佳绘图策略（力学图、流程图等）

### 🎬 Manim 数学动画
- 🎥 **AI驱动**：使用DeepSeek模型生成高质量Manim动画代码
- 📐 **数学可视化**：完美支持函数绘图、几何变换、数学公式动画
- 🎨 **丰富动画**：支持3D场景、相机动画、粒子效果等高级特性
- 🎯 **多质量渲染**：支持低/中/高/4K四种渲染质量
- 🛡️ **代码防护**：智能检测并修复括号配对、语法错误
- 🌐 **中文支持**：完美支持中文标注和公式渲染
- 🎓 **教育场景**：特别适合制作数学、物理教学动画

### 📝 文档生成（命令行）
- ✨ **AI写作**：使用DeepSeek模型生成高质量Markdown文档
- 🧮 **数学公式**：完美支持LaTeX数学公式渲染（基于KaTeX）
- 📚 **结构化内容**：自动生成大纲、章节、示例代码
- 🎨 **格式规范**：遵循标准的Markdown语法规范
- 📖 **多领域支持**：技术文档、教程、学术文章等
- 💻 **命令行模式**：通过CLI命令生成文档

### 🖼️ 带图片的文档生成
- 🎯 **智能识别**：自动识别文档中需要图片的部分
- 📊 **图表生成**：自动生成相关的图表并整合到文档中
- 🔗 **无缝集成**：图片与文档内容完美融合
- 💡 **灵活配置**：支持自定义图片生成选项

### 🌐 Web界面
- 📡 **实时更新**：通过WebSocket实时推送执行进度
- 📜 **历史记录**：查看和管理所有生成的图表和文档
- 🖼️ **预览功能**：实时预览生成的图表和文档
- 📥 **一键下载**：方便地下载生成的文件
- 📄 **文档预览**：支持Markdown文档预览和内容查看
- 🗑️ **文件管理**：支持删除单个文档或图片
- 🚀 **快速启动**：提供便捷的启动脚本
- ✏️ **AI编辑器**：智能文档编辑，支持AI修改选中文本内容
- 🎨 **图片生成**：在文档编辑器中直接生成图表并插入
- 🎬 **动画生成**：生成数学教学动画，支持多种质量选项

## 快速开始

### 1. 安装依赖

```bash
# 使用虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装所有依赖
pip install -r requirements.txt
```

### 2. 配置API密钥

复制并编辑环境变量文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，添加你的DeepSeek API密钥：

```
DEEPSEEK_API_KEY=你的DeepSeek密钥
```

> 💡 **提示**：获取DeepSeek API密钥请访问 https://platform.deepseek.com

## 使用方式

### 方式一：快速启动脚本（推荐）

使用提供的启动脚本：

```bash
chmod +x start.sh  # 首次运行需要添加执行权限
./start.sh
```

脚本会自动检查虚拟环境和配置文件，然后启动Web服务器。

### 方式二：Web界面

手动启动Web服务器：

```bash
# 确保已激活虚拟环境
source venv/bin/activate

# 启动服务器
python app.py
```

然后在浏览器中访问：`http://localhost:5001`

Web界面功能：
- 📊 **智能绘图**：实时输入绘图需求，生成图表
- 🖼️ **带图片文档生成**：输入主题，自动生成包含图表的Markdown文档
- 📊 **可视化展示**：实时显示工作流执行步骤
- ⚡ **实时更新**：WebSocket推送状态更新
- 🖼️ **预览功能**：预览生成的图表和文档
- 📜 **历史记录**：访问 `/history` 页面查看所有生成内容
- 📥 **一键下载**：下载生成的图片和文档
- 🗑️ **管理功能**：删除不需要的历史记录
- ✏️ **AI编辑器**：选中文本后使用AI进行智能修改
- 🎨 **图片生成**：在编辑器中直接生成图表并插入
- 🔧 **WebSocket测试**：访问 `/test` 页面测试WebSocket连接

### 方式三：命令行模式

#### 绘图功能

```bash
python draw_pic.py "你的绘图需求"
```

示例：

```bash
python draw_pic.py "绘制一个简单的折线图，显示2023年每个月的销售额"
```

#### 文档生成功能

```bash
python write_md.py "文档主题"
```

示例：

```bash
python write_md.py "量子力学基础教程"
```

#### 带图片的文档生成功能

```bash
python write_md_with_images.py "文档主题"
```

示例：

```bash
python write_md_with_images.py "量子力学基础教程"
```

此功能会自动识别文档中需要图表的部分，并生成相关图表整合到文档中。

#### Manim 动画生成功能

```bash
python manim_gen.py "动画描述" [质量]
```

示例：

```bash
# 生成中等质量动画（默认）
python manim_gen.py "展示一个圆从左侧移动到右侧的动画"

# 生成低质量动画（快速预览）
python manim_gen.py "绘制正弦函数图像" low

# 生成高质量动画
python manim_gen.py "展示三维立方体旋转" high

# 生成4K超高清动画
python manim_gen.py "复杂的数学公式变换动画" 4k
```

**质量选项说明**：
- `low`: 480p, 15fps - 快速预览，文件小
- `medium`: 720p, 30fps - 平衡质量（默认）
- `high`: 1080p, 60fps - 最佳质量
- `4k`: 2160p, 60fps - 超高清质量

## 工作流程

### 📊 绘图工作流

系统采用LangGraph构建的4步工作流：

1. **润色提示词** (refine_prompt)
   - 增强用户的绘图需求
   - 添加必要的绘图要求和规范
   - 包含物理约束和绘图最佳实践

2. **生成绘图代码** (generate_code)
   - 调用DeepSeek模型
   - 生成完整的matplotlib绘图代码
   - 智能识别绘图类型（数据图表、力学示意图、流程图等）
   - 根据类型应用专门的绘图策略和提示词
   - 确保代码可直接执行

3. **执行绘图代码** (execute_code)
   - 在安全环境中执行生成的代码
   - 内置空白图像防护机制
   - 验证数据有效性（检查NaN、Inf、全零等）
   - 显式设置坐标轴范围和颜色
   - 自动生成唯一文件名
   - 保存图表到本地

4. **验证图片保存** (save_image)
   - 验证图片是否成功生成
   - 获取图片大小等信息
   - 返回执行结果

### 📝 文档生成工作流（命令行）

文档生成采用类似的5步工作流（仅支持命令行模式）：

1. **润写作需求** (refine_prompt)
   - 增强用户的写作需求
   - 添加文档写作要求和格式规范
   - 包含数学公式KaTeX兼容性要求

2. **生成文档大纲** (generate_outline)
   - 调用DeepSeek模型生成结构化大纲
   - 确保逻辑清晰、层次分明
   - 覆盖主题的所有重要方面

3. **生成文档内容** (generate_content)
   - 根据大纲展开完整内容
   - 使用标准Markdown语法
   - 自动修复LaTeX公式转义问题

4. **保存文档** (save_document)
   - 保存到 `docs/` 目录
   - 自动生成唯一文件名（带时间戳）
   - 返回文件路径和大小

5. **验证文档** (verify_document)
   - 验证文件是否成功保存
   - 统计文档字数、行数等信息

### 🖼️ 带图片的文档生成工作流

带图片的文档生成采用增强的8步工作流：

1. **润写作需求** (refine_prompt)
   - 增强用户的写作需求
   - 添加文档写作要求和格式规范
   - 包含图片生成指令

2. **生成文档大纲** (generate_outline)
   - 调用DeepSeek模型生成结构化大纲
   - 确保逻辑清晰、层次分明
   - 标注需要图表的位置

3. **生成文档内容** (generate_content)
   - 根据大纲展开完整内容
   - 使用标准Markdown语法
   - 在适当位置插入图片占位符

4. **识别图片需求** (identify_image_requests)
   - 分析文档内容，识别需要生成的图表
   - 确定每个图片的类型和描述

5. **生成图表** (generate_images)
   - 为每个图片需求生成对应的绘图代码
   - 智能识别图表类型（流程图、数据图表、力学图等）
   - 针对不同类型使用优化的绘图策略
   - 执行代码并保存图片
   - 收集所有生成的图片路径

6. **整合图片到文档** (embed_images)
   - 将生成的图片路径替换文档中的占位符
   - 生成包含图片的完整文档内容

7. **保存文档** (save_document)
   - 保存到 `docs/` 目录
   - 自动生成唯一文件名（带时间戳）
   - 返回文件路径和大小

8. **验证文档** (verify_document)
   - 验证文件和图片是否成功保存
   - 统计文档字数、行数、图片数量等信息

### 🎬 Manim 动画生成工作流

Manim 动画生成采用 4 步工作流：

1. **润色动画需求** (refine_prompt)
   - 增强用户的动画需求描述
   - 添加动画制作要求和规范
   - 包含布局和防重叠要求

2. **生成动画代码** (generate_code)
   - 调用 DeepSeek 模型生成 Manim 代码
   - 智能识别场景类型（2D/3D/相机动画）
   - 根据类型应用专门的代码生成策略
   - 自动检测和修复括号配对问题
   - 确保代码符合 Manim 语法规范

3. **渲染动画视频** (execute_code)
   - 在安全环境中执行生成的代码
   - 使用 Manim 渲染指定质量的视频
   - 自动清理缓存避免潜在问题
   - 支持多种渲染质量选项
   - 自动查找并移动生成的视频文件

4. **验证视频保存** (save_video)
   - 验证视频是否成功生成
   - 获取视频大小等信息
   - 返回执行结果和视频路径

## 代码结构

```
bamboo/
├── draw_pic.py               # 绘图工作流核心逻辑
├── write_md.py               # 文档生成工作流核心逻辑
├── write_md_with_images.py   # 带图片的文档生成工作流
├── manim_gen.py              # Manim动画工作流核心逻辑
├── app.py                    # Web服务器和API接口
├── start.sh                  # 快速启动脚本
├── AGENTS.md                 # 开发指南和代码规范
├── templates/
│   ├── index.html            # Web前端主界面
│   ├── history.html          # 历史记录页面
│   └── test.html             # WebSocket测试页面
├── images/                   # 生成的图表保存目录
├── docs/                     # 生成的文档保存目录
├── videos/                   # 生成的动画视频保存目录
├── requirements.txt           # Python依赖包
├── .env                      # 环境变量配置
├── .env.example              # 环境变量示例
├── .gitignore                # Git忽略文件配置
├── LICENSE                   # Apache 2.0许可证
└── README.md                 # 项目文档
```

### 主要文件说明

- **draw_pic.py**: 绘图工作流，定义图表生成的各个节点
- **write_md.py**: 文档生成工作流（命令行模式），定义文档创作的各个节点
- **write_md_with_images.py**: 带图片的文档生成工作流，支持自动生成图表并整合到文档中
- **manim_gen.py**: Manim 动画工作流，定义数学动画生成的各个节点
- **app.py**: Flask Web服务器，提供RESTful API和WebSocket支持
- **AGENTS.md**: 开发指南，包含代码风格规范、工作流模式和API集成说明
- **start.sh**: 快速启动脚本，自动检查环境并启动服务
- **templates/index.html**: 响应式Web界面，支持绘图、文档编辑和动画生成功能
- **templates/history.html**: 历史记录页面，展示所有生成的图表、文档和视频
- **templates/test.html**: WebSocket连接测试页面，用于调试实时通信

## API 接口

Web服务器提供以下API接口：

### 绘图相关

#### POST /api/workflow
启动新的绘图工作流

**请求体**：
```json
{
  "prompt": "绘制一个折线图"
}
```

### 文档相关

#### GET /api/documents
列出所有生成的文档文件

#### POST /api/document/workflow-with-images
启动带图片的文档生成工作流

**请求体**：
```json
{
  "prompt": "量子力学基础教程"
}
```

该接口会自动识别文档中需要图表的部分，并生成相关图表整合到文档中。

#### POST /api/document/ai-modify
AI修改选中的文本内容

**请求体**：
```json
{
  "selected_text": "需要修改的文本内容",
  "instructions": "修改指令"
}
```

**响应**：
```json
{
  "modified_text": "修改后的文本内容"
}
```

此接口用于文档编辑器中的AI辅助编辑功能。

#### POST /api/document/generate-image
AI生成图片（用于文档编辑器中插入图表）

**请求体**：
```json
{
  "description": "图片描述"
}
```

**响应**：
```json
{
  "image_url": "/api/images/plot_xxx.png",
  "image_path": "/path/to/images/plot_xxx.png"
}
```

此接口调用绘图工作流生成指定描述的图表。

### Manim 动画相关

#### POST /api/manim/workflow
启动 Manim 动画工作流

**请求体**：
```json
{
  "prompt": "展示一个圆从左侧移动到右侧的动画",
  "quality": "medium"
}
```

**质量参数选项**：
- `low`: 480p, 15fps
- `medium`: 720p, 30fps（默认）
- `high`: 1080p, 60fps
- `4k`: 2160p, 60fps

#### GET /api/manim/videos
列出所有生成的动画视频

#### GET /api/manim/videos/<filename>
获取指定的动画视频文件

#### DELETE /api/manim/videos/<filename>
删除指定的动画视频文件

#### POST /api/manim/clear
清除所有动画历史记录

### 绘图相关（补充）

#### GET /api/documents/<filename>/content
获取文档的文本内容（JSON格式）

#### DELETE /api/documents/<filename>
删除指定的文档文件

### 绘图相关（补充）

#### POST /api/drawing/workflow
启动绘图工作流（新的API端点）

**请求体**：
```json
{
  "prompt": "绘制一个折线图"
}
```

#### GET /api/status
获取当前绘图工作流状态

#### POST /api/drawing/clear
清除绘图历史记录

### 通用接口

#### GET /api/history
获取所有历史记录（图表和文档）

#### GET /api/images
列出所有生成的图片

#### GET /api/images/<filename>
获取指定的图片文件

#### DELETE /api/images/<filename>
删除指定的图片文件

#### POST /api/clear
清除所有历史记录

### WebSocket事件
- `status_update`: 接收工作流状态更新（支持绘图、文档生成和Manim动画工作流）
- `connect`: 客户端连接
- `disconnect`: 客户端断开

**支持的工作流类型**：
- `drawing` - 绘图工作流
- `document_with_images` - 文档生成工作流
- `manim` - Manim 动画工作流

客户端连接示例：
```javascript
const socket = new WebSocket('ws://localhost:5001/ws');
socket.send(JSON.stringify({workflow_type: 'manim'}));
```

## 输出示例

### 📊 绘图输出

```
1. 正在生成绘图代码...
2. 正在执行绘图代码...
3. 正在验证图片保存...
✅ 绘图成功！图片已保存到: plot.png
📏 图片大小: 234.16 KB
📝 生成的代码:
import matplotlib.pyplot as plt
...
📍 图片绝对路径: /Users/yangyang/Projects/bamboo/images/plot.png
```

### 📝 文档生成输出

```
1. 正在润色写作需求...
✅ 原始需求: '量子力学基础教程'
✅ 增强后的提示词已生成

2. 正在生成文档大纲...
✅ 文档大纲生成完成

3. 正在生成文档内容...
✅ Markdown 文档内容生成完成

4. 正在保存文档...
✓ 文档已保存: docs/doc_量子力学基础教程_20260123_180000.md (大小: 12345 字节)

5. 正在验证文档...
✓ 文档验证成功
[STATS] 行数: 245, 字符数: 12345, 标题数: 28
```

生成的文档包含：
- 清晰的章节结构
- 标准的Markdown格式
- LaTeX数学公式（支持KaTeX渲染）
- 代码示例和说明
- 表格和列表

### 🖼️ 带图片的文档生成输出

```
1. 正在润色写作需求...
✅ 原始需求: '量子力学基础教程'
✅ 增强后的提示词已生成

2. 正在生成文档大纲...
✅ 文档大纲生成完成

3. 正在生成文档内容...
✅ Markdown 文档内容生成完成

4. 正在识别图片需求...
✅ 识别到 3 个需要生成的图表

5. 正在生成图表...
✅ 图片1生成成功: images/plot_001.png
✅ 图片2生成成功: images/plot_002.png
✅ 图片3生成成功: images/plot_003.png

6. 正在整合图片到文档...
✅ 图片已整合到文档中

7. 正在保存文档...
✓ 文档已保存: docs/doc_量子力学基础教程_20260123_180000.md (大小: 15678 字节)

8. 正在验证文档...
✓ 文档验证成功
[STATS] 行数: 320, 字符数: 15678, 标题数: 35, 图片数: 3
```

### 🎬 Manim 动画生成输出

```
1. 正在润色动画需求...
✅ 原始需求: '展示一个圆从左侧移动到右侧的动画'
✅ 增强后的提示词已生成

2. 正在生成 Manim 动画代码...
✅ Manim 代码生成完成

3. 正在渲染动画视频（这可能需要较长时间）...
🎬 开始渲染动画（可能需要 30 秒到 5 分钟）...
✅ 视频渲染成功！

4. 正在验证视频保存...
视频大小: 2.45 MB
✅ 动画生成成功！
📁 保存路径: /path/to/videos/manim_20260211_203421_a1b2c3d4.mp4
📏 文件大小: 2570240 字节
🎥 渲染质量: medium
📍 视频绝对路径: /Users/yangyang/Projects/bamboo/videos/manim_20260211_203421_a1b2c3d4.mp4
```

生成的动画特点：
- 专业的数学可视化效果
- 流畅的动画过渡
- 清晰的中文标注
- 支持多种渲染质量
- 可嵌入到教学材料中

## 注意事项

1. **API密钥安全**：不要将你的API密钥提交到版本控制系统
2. **模型选择**：目前使用的是DeepSeek模型，提供高性价比的代码生成能力
3. **代码安全**：生成的代码会在安全环境中执行，但仍建议谨慎处理未知输入
4. **中文显示**：程序已配置中文支持，但可能需要根据你的系统调整字体设置
5. **端口配置**：默认使用5001端口，如需修改请编辑 [app.py](app.py) 最后一行
6. **Manim 依赖**：Manim 需要安装 FFmpeg 和 LaTeX，首次使用可能需要较长时间安装依赖
7. **动画渲染**：Manim 动画渲染可能需要 30 秒到 5 分钟，取决于场景复杂度和质量设置

## 技术栈

### 后端
- **Web框架**: Flask 3.0.0
- **实时通信**: Flask-SocketIO 5.3.6 + Eventlet
- **工作流引擎**: LangGraph 0.0.28
- **AI模型**: DeepSeek (兼容OpenAI API)
- **绘图**: Matplotlib >= 3.9.0
- **数值计算**: NumPy >= 2.0.0
- **动画渲染**: Manim >= 0.18.0
- **视频处理**: FFmpeg

### 前端
- **基础**: 原生 HTML/CSS/JavaScript
- **Markdown渲染**: Marked.js
- **数学公式**: KaTeX
- **实时通信**: Socket.IO Client

## DeepSeek API 优势

- 💰 **高性价比**：极具竞争力的价格，¥1/百万tokens
- 🎁 **免费额度**：新用户通常有免费试用额度
- 💻 **代码能力强**：特别擅长代码生成和理解
- 🔌 **兼容性好**：使用标准的OpenAI接口，集成简单

获取DeepSeek API密钥请访问 https://platform.deepseek.com

## 常见问题

### 1. 端口被占用
如果5001端口被占用，可以修改 [app.py](app.py) 最后一行：
```python
socketio.run(app, debug=True, host='0.0.0.0', port=5002)  # 改为5002
```

### 2. 生成的图片中文显示异常
系统已配置多种中文字体备选方案。如果仍有问题，请检查系统字体安装情况。

### 3. API调用失败
请检查：
- API密钥是否正确配置在 `.env` 文件中
- 网络连接是否正常
- API额度是否充足
- 获取API密钥请访问 https://platform.deepseek.com

### 4. 启动脚本无执行权限
```bash
chmod +x start.sh
```

### 5. 虚拟环境激活失败
确保使用正确的激活命令：
- Linux/Mac: `source venv/bin/activate`
- Windows: `venv\Scripts\activate`

## 扩展建议

### 动画功能
- [ ] 支持更多动画效果（粒子系统、物理模拟等）
- [ ] 添加动画编辑和重新生成功能
- [ ] 实现代码模板管理
- [ ] 支持批量动画生成
- [ ] 添加音频配音功能
- [ ] 实现动画拼接和合并
- [ ] 支持导出为 GIF 格式
- [ ] 添加动画预设和参数调节

### 绘图功能
- [ ] 支持更多绘图库（seaborn、plotly等）
- [ ] 添加图表编辑和重新生成功能
- [ ] 实现代码模板管理
- [ ] 支持批量绘图
- [ ] 添加数据导入功能（CSV、Excel等）
- [ ] 实现图表分享功能
- [ ] 添加图表导出为SVG/PDF功能
- [ ] 支持自定义图表主题和样式

### 文档功能
- [ ] 支持更多输出格式（PDF、HTML、Word等）
- [ ] 添加文档模板系统
- [ ] 实现文档续写和编辑功能
- [ ] 支持多语言文档生成
- [ ] 添加参考文献管理
- [ ] 实现文档版本控制
- [ ] 支持协作文档编辑
- [ ] 添加文档导出和分享功能

### 通用功能
- [ ] 添加用户认证系统
- [ ] 实现历史记录持久化存储到数据库
- [ ] 添加使用统计和分析
- [ ] 实现API限流和配额管理

## 许可证

本项目采用 Apache License 2.0 许可证。详见 [LICENSE](LICENSE) 文件。

## 致谢

- [LangGraph](https://github.com/langchain-ai/langgraph) - 强大的工作流编排框架
- [DeepSeek](https://www.deepseek.com/) - 提供高性价比的AI模型服务
- [Flask](https://flask.palletsprojects.com/) - 轻量级Web框架
- [Matplotlib](https://matplotlib.org/) - 强大的Python绘图库
- [Manim](https://www.manim.community/) - 专业的数学动画引擎

---

Made with ❤️ by [richardyang92](https://github.com/richardyang92)
