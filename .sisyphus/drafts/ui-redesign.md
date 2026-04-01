# Draft: UI 交互重新设计

## 问题诊断 (信息密度太低)

### 当前 UI 架构分析
- **框架**: React 19 + TypeScript + Ant Design 6
- **布局**: Header → Content(16px padding) → HomePage(Tabs)
- **主页结构**: GlobalModelBar + Tabs(3个tab) → 左右分栏(3:7)
- **左面板**: Card(输入区) + Card(执行时间线)
- **右面板**: Card(生成结果/执行进度/占位符)

### 具体的信息密度问题

1. **Header 占用空间过多**
   - 整个 sticky header 只放了 Logo + 2个导航链接 + 主题切换
   - 白白浪费了一条完整的水平空间

2. **GlobalModelBar 独立占一整行**
   - 只是模型选择器，却用 Card 包裹独占一行
   - 可以折叠到 header 或侧边栏

3. **Tab 切换占据一整行**
   - 3 个 Tab (数据可视化/文档+图表/数学动画) 各自占满一行
   - Tab 下方 16px 间距

4. **左右分栏比例 3:7 太疏**
   - 左侧 30% 放了输入区 + 时间线，空间利用不足
   - 大量空白 padding: Content 24px, Card padding 16px

5. **Card 嵌套过深**
   - 输入区用 Card 包裹，时间线用 Card 包裹，结果区也用 Card 包裹
   - Card title + Card body padding 吃掉大量空间
   - Card title 区域 min-height: auto, padding: 16px 24px

6. **空状态太多空白**
   - EmptyView / ResultPlaceholder 都有 48px 上下 padding
   - 大量"等待xxx启动..."文字占据空间但没信息量

7. **时间线区域和结果区域不连通**
   - 时间线在左下角，用户需要左右切换视线
   - 执行过程中的流式内容在左下，但结果展示在右侧

8. **历史记录页信息密度也低**
   - List.Item 布局，每个 item 占一行，信息分散
   - 没有缩略图预览，只有文字名称

### 用户需求
- 提高信息密度
- 更好的交互设计

## 用户决策 (已确认)

1. **风格**: 紧凑 IDE 风格 (类 Cursor/VSCode)
2. **UI 框架**: 迁移到 Tailwind CSS (放弃 Ant Design)
3. **导航**: 三个工作流收起为图标侧导航

## 探索发现补充

### 死代码组件 (需清理)
- `StreamContentList.tsx` - 未使用的 Collapse 面板
- `CardListView.tsx`, `TimelineView.tsx`, `NodeGraphView.tsx` - 旧视图实现
- `WorkflowViewToolbar.tsx` - 视图切换工具栏
- `StepProgressDisplay.tsx` - Ant Design Steps 进度
- `StepItem.tsx` - 单步渲染器

### 暗色模式问题
- 三种策略混用：`.dark` CSS类、`data-theme`属性、`@media (prefers-color-scheme)`
- 迁移到 Tailwind 后需要统一

### DocumentPanel 代码重复
- Preview 和 Outline tab 的 ReactMarkdown 配置完全重复 (约80行)
- 迁移时可提取为共享组件

## 用户决策 (全部确认)

1. **风格**: 紧凑 IDE 风格 (类 Cursor/VSCode)
2. **UI 框架**: 迁移到 Tailwind CSS (放弃 Ant Design)
3. **导航**: 三个工作流收起为图标侧导航
4. **历史记录页**: 一起重新设计
5. **React Flow**: 移除 (卸载 @xyflow/react 依赖)
6. **默认主题**: 深色模式为默认

## 设计系统 (来自 ui-ux-pro-max)

- **颜色**: Primary #1E293B, CTA #22C55E, BG #0F172A, Text #F8FAFC
- **字体**: Fira Code (代码) / Fira Sans (UI)
- **Data-Dense Dashboard 参考**: grid 布局、8px gap、12px card padding、12-14px 字体

## Scope Boundaries
- INCLUDE: 全部前端 UI (首页 + 历史页 + 侧导航 + 主题系统 + Tailwind 迁移 + 清理死代码 + 移除 React Flow)
- EXCLUDE: 后端逻辑、工作流引擎、API接口、WebSocket 协议
