# Bamboo Frontend

Bamboo 项目的 React 前端应用，提供 AI 智能绘图、文档生成和数学动画制作的 Web 界面。

## 技术栈

- **框架**: React 19.2.0
- **语言**: TypeScript 5.9.3
- **构建工具**: Vite 7.3.1
- **UI 组件库**: Ant Design 6.3.0
- **路由**: react-router-dom 7.13.0
- **HTTP 客户端**: Axios 1.13.5
- **Markdown 渲染**: react-markdown 10.1.0
- **数学公式**: KaTeX 0.16.28
- **流程图组件**: ReactFlow (节点图可视化)
- **实时通信**: 原生 WebSocket API

## 项目结构

```
frontend/
├── src/
│   ├── components/           # React 组件
│   │   ├── common/          # 共享组件
│   │   │   ├── ModelSelector.tsx         # 全局模型选择器
│   │   │   ├── WorkflowStatusIndicator.tsx  # 工作流状态指示器
│   │   │   ├── WorkflowTimeline.tsx      # 工作流时间线
│   │   │   └── workflowViews/            # React Flow 工作流视图
│   │   ├── drawing/         # 绘图工作流 UI
│   │   │   └── DrawingPanel.tsx
│   │   ├── document/        # 文档工作流 UI
│   │   │   └── DocumentPanel.tsx
│   │   └── manim/           # Manim 动画工作流 UI
│   │       └── ManimPanel.tsx
│   ├── pages/               # 页面组件
│   │   ├── HomePage.tsx     # 主页（工作流界面）
│   │   └── HistoryPage.tsx  # 历史记录页面
│   ├── services/            # 服务层
│   │   ├── api.ts           # Axios HTTP 客户端
│   │   └── websocket.ts     # WebSocket 客户端
│   ├── contexts/            # React Context
│   │   └── WorkflowContext.tsx  # 工作流状态管理
│   ├── hooks/               # 自定义 Hooks
│   │   └── useWebSocket.ts  # WebSocket Hook
│   ├── types/               # TypeScript 类型定义
│   │   └── index.ts
│   ├── config/              # 配置文件
│   │   └── workflowGraphs.ts   # 工作流图配置
│   ├── constants/           # 常量定义
│   │   └── workflowSteps.ts    # 工作流步骤定义
│   ├── App.tsx              # 根组件
│   ├── main.tsx             # 入口文件
│   └── index.css            # 全局样式
├── vite.config.ts           # Vite 配置
├── tsconfig.json            # TypeScript 配置
├── tsconfig.app.json        # 应用 TypeScript 配置
├── tsconfig.node.json       # Node TypeScript 配置
└── package.json
```

## 开发命令

```bash
# 安装依赖
npm install

# 启动开发服务器（热更新）
npm run dev
# 运行在 http://localhost:5173

# TypeScript 类型检查
npm run build

# 代码检查
npm run lint

# 预览生产构建
npm run preview
```

## 环境变量

创建 `.env.local` 文件配置环境变量：

```env
VITE_API_URL=http://localhost:5001
VITE_WS_URL=ws://localhost:5001/ws
```

## 核心功能模块

### 1. 全局模型选择器 (ModelSelector)

- 支持切换 DeepSeek 和 Ollama 提供商
- 动态获取可用模型列表
- 自动检测模型能力（是否支持思考模式）
- 推理模式开关（仅对支持的模型有效）

### 2. 工作流面板

每个工作流（绘图/文档/动画）都包含：
- 输入区域：用户输入需求描述
- 控制按钮：开始生成、停止工作流、清除历史
- 状态显示：实时工作流进度
- 结果展示：生成的图片/文档/视频预览

### 3. 工作流可视化

- **节点图视图**：使用 ReactFlow 展示工作流节点和边
- **时间线视图**：按时间顺序展示工作流执行步骤
- **条件边**：支持根据条件跳过节点的可视化

### 4. 实时通信

- WebSocket 连接后端
- 实时接收工作流状态更新
- 支持 AI 流式响应显示
- 区分普通内容和思考内容

## API 集成

前端通过 `services/api.ts` 与后端通信：

```typescript
import * as api from './services/api';

// 获取可用模型
const models = await api.getAvailableModels();

// 启动绘图工作流
await api.startDrawingWorkflow('绘制一个折线图');

// 停止工作流
await api.stopDrawingWorkflow();

// 切换模型
await api.switchModel('ollama', 'llama3.1', false);
```

## WebSocket 使用

```typescript
import { useWebSocket } from './hooks/useWebSocket';

function MyComponent() {
  const { status, connect, disconnect } = useWebSocket('drawing');

  // status 包含实时工作流状态
  // connect() 建立连接
  // disconnect() 断开连接
}
```

## 类型定义

主要类型定义在 `types/index.ts`：

- `WorkflowType` - 工作流类型
- `WorkflowStatusType` - 工作流状态
- `StepStatus` - 步骤状态
- `WorkflowStatus` - 完整工作流状态
- `ModelInfo` - 模型信息（含能力）
- `AvailableModels` - 可用模型列表

## 代理配置

开发模式下，Vite 会代理 API 请求到后端：

```typescript
// vite.config.ts
proxy: {
  '/api': {
    target: 'http://localhost:5001',
    changeOrigin: true
  },
  '/ws': {
    target: 'ws://localhost:5001',
    ws: true
  }
}
```

## 生产构建

```bash
# 构建生产版本
npm run build

# 输出到 dist/ 目录
# 由后端 Flask 服务静态文件
```

## 注意事项

1. **后端依赖**：确保后端服务在 `http://localhost:5001` 运行
2. **WebSocket**：开发时需要同时启动后端以支持 WebSocket
3. **模型切换**：切换到 Ollama 模型前需确保 Ollama 服务已启动
4. **热更新**：修改代码后自动刷新，但 WebSocket 需要重新连接

## 相关文档

- [主项目 README](../README.md)
- [开发指南 CLAUDE.md](../CLAUDE.md)
- [Vite 文档](https://vite.dev/)
- [React 文档](https://react.dev/)
- [Ant Design 文档](https://ant.design/)
