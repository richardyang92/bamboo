# 基于DeepSeek的AI绘图Agent

一个使用LangGraph框架构建的AI绘图Agent，能够根据用户需求自动生成、执行和保存matplotlib图表。

## 功能特性

- ✅ **AI驱动**：使用DeepSeek模型生成高质量绘图代码
- 📊 **Matplotlib支持**：生成各种类型的图表
- 🔄 **自动化流程**：用户输入 → 代码生成 → 执行 → 保存图片
- 📁 **本地保存**：自动将生成的图表保存到本地
- 🎯 **中文支持**：完美支持中文显示
- 🌐 **Web界面**：实时展示工作流执行状态
- 📡 **实时更新**：通过WebSocket实时推送执行进度
- 📜 **历史记录**：查看和管理所有生成的图表历史
- 🚀 **快速启动**：提供便捷的启动脚本

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

> 💡 **提示**：详细的DeepSeek API配置指南请参考 [doc/DEEPSEEK_SETUP.md](doc/DEEPSEEK_SETUP.md)

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
- 📝 实时输入绘图需求
- 📊 可视化展示工作流执行步骤
- ⚡ WebSocket实时更新状态
- 🖼️ 预览生成的图表
- 💻 查看生成的代码
- 📜 查看历史记录（访问 `/history` 页面）
- 🗑️ 清除历史记录
- 📥 下载生成的图片

### 方式三：命令行模式

直接运行脚本：

```bash
python main.py "你的绘图需求"
```

示例：

```bash
python main.py "绘制一个简单的折线图，显示2023年每个月的销售额，数据是[100, 120, 150, 180, 200, 220, 250, 280, 300, 320, 350, 400]"
```

交互模式（不带参数运行）：

```bash
python main.py
请输入你的绘图需求：绘制一个柱状图，显示不同产品的销量
```

## 工作流程

系统采用LangGraph构建的4步工作流：

1. **润色提示词** (refine_prompt)
   - 增强用户的绘图需求
   - 添加必要的绘图要求和规范
   - 包含物理约束和绘图最佳实践

2. **生成绘图代码** (generate_code)
   - 调用DeepSeek模型
   - 生成完整的matplotlib绘图代码
   - 确保代码可直接执行

3. **执行绘图代码** (execute_code)
   - 在安全环境中执行生成的代码
   - 自动生成唯一文件名
   - 保存图表到本地

4. **验证图片保存** (save_image)
   - 验证图片是否成功生成
   - 获取图片大小等信息
   - 返回执行结果

## 代码结构

```
bamboo/
├── main.py              # 核心工作流逻辑
├── app.py               # Web服务器和API接口
├── start.sh             # 快速启动脚本
├── templates/
│   ├── index.html       # Web前端主界面
│   └── history.html     # 历史记录页面
├── doc/
│   └── DEEPSEEK_SETUP.md # DeepSeek API配置指南
├── images/              # 生成的图表保存目录
├── requirements.txt     # Python依赖包
├── .env                 # 环境变量配置
├── .env.example         # 环境变量示例
├── .gitignore           # Git忽略文件配置
├── LICENSE              # Apache 2.0许可证
└── README.md            # 项目文档
```

### 主要文件说明

- **main.py**: 定义工作流图和各个节点的处理函数
- **app.py**: Flask Web服务器，提供RESTful API和WebSocket支持
- **start.sh**: 快速启动脚本，自动检查环境并启动服务
- **templates/index.html**: 响应式Web界面，实时展示工作流状态
- **templates/history.html**: 历史记录页面，展示所有生成的图表
- **doc/DEEPSEEK_SETUP.md**: 详细的DeepSeek API配置和获取指南

## API 接口

Web服务器提供以下API接口：

### POST /api/workflow
启动新的绘图工作流

**请求体**：
```json
{
  "prompt": "绘制一个折线图"
}
```

### GET /api/status
获取当前工作流状态

### GET /api/images
列出所有生成的图片

### GET /api/images/<filename>
获取指定的图片文件

### POST /api/clear
清除历史记录

### WebSocket事件
- `status_update`: 接收工作流状态更新
- `connect`: 客户端连接
- `disconnect`: 客户端断开

## 输出示例

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

## 注意事项

1. **API密钥安全**：不要将你的API密钥提交到版本控制系统
2. **模型选择**：目前使用的是DeepSeek模型，提供高性价比的代码生成能力
3. **代码安全**：生成的代码会在安全环境中执行，但仍建议谨慎处理未知输入
4. **中文显示**：程序已配置中文支持，但可能需要根据你的系统调整字体设置
5. **端口配置**：默认使用5001端口，如需修改请编辑 [app.py](app.py#L373)

## 技术栈

- **后端框架**: Flask 3.0.0 + Flask-SocketIO 5.3.6
- **工作流引擎**: LangGraph 0.0.28
- **AI模型**: DeepSeek (兼容OpenAI API)
- **绘图库**: Matplotlib >= 3.9.0
- **数值计算**: NumPy >= 2.0.0
- **实时通信**: WebSocket (Socket.IO + Eventlet)
- **前端**: 原生 HTML/CSS/JavaScript

## DeepSeek API 优势

- 💰 **高性价比**：极具竞争力的价格，¥1/百万tokens
- 🎁 **免费额度**：新用户通常有免费试用额度
- 💻 **代码能力强**：特别擅长代码生成和理解
- 🔌 **兼容性好**：使用标准的OpenAI接口，集成简单

详细配置请参考 [DeepSeek配置指南](doc/DEEPSEEK_SETUP.md)

## 常见问题

### 1. 端口被占用
如果5001端口被占用，可以修改 [app.py](app.py#L373) 最后一行：
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
- 是否按照 [DeepSeek配置指南](doc/DEEPSEEK_SETUP.md) 正确配置

### 4. 启动脚本无执行权限
```bash
chmod +x start.sh
```

### 5. 虚拟环境激活失败
确保使用正确的激活命令：
- Linux/Mac: `source venv/bin/activate`
- Windows: `venv\Scripts\activate`

## 扩展建议

- [ ] 添加用户认证系统
- [ ] 实现历史记录持久化存储到数据库
- [ ] 支持更多绘图库（seaborn、plotly等）
- [ ] 添加图表编辑和重新生成功能
- [ ] 实现代码模板管理
- [ ] 支持批量绘图
- [ ] 添加数据导入功能（CSV、Excel等）
- [ ] 实现图表分享功能
- [ ] 添加图表导出为SVG/PDF功能
- [ ] 支持自定义图表主题和样式

## 许可证

本项目采用 Apache License 2.0 许可证。详见 [LICENSE](LICENSE) 文件。

## 致谢

- [LangGraph](https://github.com/langchain-ai/langgraph) - 强大的工作流编排框架
- [DeepSeek](https://www.deepseek.com/) - 提供高性价比的AI模型服务
- [Flask](https://flask.palletsprojects.com/) - 轻量级Web框架
- [Matplotlib](https://matplotlib.org/) - 强大的Python绘图库

---

Made with ❤️ by [richardyang92](https://github.com/richardyang92)
