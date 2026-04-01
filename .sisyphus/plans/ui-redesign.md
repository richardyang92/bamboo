# Bamboo Frontend UI Redesign — IDE Style + Tailwind Migration

## TL;DR

> **Quick Summary**: 完全重写 Bamboo 前端 UI，从 Ant Design 迁移到 Tailwind CSS + Radix UI，采用紧凑 IDE 风格布局（图标侧导航 + 深色默认），大幅提升信息密度。
> 
> **Deliverables**:
> - 全新 IDE 风格布局：图标侧栏导航 + 紧凑头部 + 最大化内容区
> - 三个工作流面板用共享 `WorkflowPanel` 基座组件统一
> - 历史记录页用网格+筛选重新设计
> - 统一的深色/浅色主题系统（深色为默认）
> - 移除 Ant Design、React Flow、所有死代码
> - Toast 通知系统 (sonner) 替代 Ant Design message
> 
> **Estimated Effort**: Large
> **Parallel Execution**: YES - 5 waves
> **Critical Path**: T1→T4→T7→T8→T9→T10→T11→T12→T15→T17→FINAL

---

## Context

### Original Request
用户要求重新设计 UI 交互，当前 UI 信息密度太低。

### Interview Summary
**Key Discussions**:
- 当前 Ant Design 卡片嵌套3层、3:7分栏浪费空间、Header 空转、空状态占位巨大
- 用户选择: 紧凑 IDE 风格、迁移 Tailwind CSS、图标侧导航、历史页同步重设计、移除 React Flow、深色默认
- 测试策略: 测试后置

**Research Findings**:
- Data-Dense Dashboard: grid 布局、8px gap、12px padding、12-14px 字体
- 设计系统: #0F172A 背景、#F8FAFC 文字、#22C55E 强调、Fira Code/Sans 字体
- 当前 app 有 ~50 源文件，其中 10 个是死代码
- DocumentPanel 有 ~100 行 ReactMarkdown 配置重复（3处）
- 26 处 `message.*()` 调用嵌入在业务逻辑中

### Metis Review
**Identified Gaps** (addressed):
- **26处 message.*() 调用**: 创建 `services/toast.ts` 抽象层，用 sonner 替代
- **60+ 内联 style={{}} 对象**: 迁移时全部转为 Tailwind class
- **25+ .ant-* CSS 选择器**: 全部移除，用 Tailwind 替代
- **双主题系统冲突**: 保留 ThemeContext（已添加 .dark class），移除 Ant Design ConfigProvider
- **react-syntax-highlighter 未列入保留**: 确认保留（StreamContentItem 在用）
- **cherry-markdown 死依赖**: package.json 中有但未使用，移除

---

## Work Objectives

### Core Objective
将 Bamboo 前端从 Ant Design 卡片式布局迁移到紧凑 IDE 风格 Tailwind CSS 布局，最大化内容区信息密度，同时保留所有现有功能和业务逻辑。

### Concrete Deliverables
- `frontend/src/index.css` — Tailwind v4 基础 + `@theme` 设计系统变量
- `frontend/src/components/layout/Sidebar.tsx` — 图标侧导航
- `frontend/src/components/layout/Header.tsx` — 紧凑顶栏
- `frontend/src/components/layout/AppLayout.tsx` — IDE 风格外框
- `frontend/src/components/shared/WorkflowPanel.tsx` — 工作流面板基座
- `frontend/src/components/shared/MarkdownRenderer.tsx` — 共享 Markdown 渲染器
- `frontend/src/components/shared/ModelSelector.tsx` — Tailwind 版模型选择器
- `frontend/src/components/drawing/DrawingPanel.tsx` — 重写
- `frontend/src/components/document/DocumentPanel.tsx` — 重写
- `frontend/src/components/manim/ManimPanel.tsx` — 重写
- `frontend/src/pages/HomePage.tsx` — 重写（侧导航）
- `frontend/src/pages/HistoryPage.tsx` — 重写（网格+筛选）
- `frontend/src/components/PreviewModal.tsx` — 重写（Radix Dialog）
- `frontend/src/services/toast.ts` — Toast 抽象层
- `frontend/src/App.tsx` — 重写（移除 Ant Design Layout）
- `frontend/src/App.css` — 移除（合并到 Tailwind）
- 移除 10 个死代码文件 + React Flow 依赖

### Definition of Done
- [ ] `cd frontend && npm run build` 成功，零 TypeScript 错误
- [ ] 零 `from 'antd'` 和 `from '@ant-design/icons'` 导入残留
- [ ] 零 `.ant-*` CSS 选择器残留
- [ ] 所有 3 个工作流面板功能完整（输入→时间线→结果展示）
- [ ] WebSocket 实时状态更新正常工作
- [ ] 深色/浅色主题切换正常
- [ ] 历史记录页筛选和预览正常

### Must Have
- 图标侧导航切换三个工作流
- 紧凑的输入区 + 时间线 + 结果区
- 模型选择器可折叠/内联
- CLI 风格执行时间线（保留现有 WorkflowTimeline）
- 流式内容展示（保留思考过程展开）
- 深色模式为默认，浅色模式可切换
- Toast 通知替代 Ant Design message
- Markdown + KaTeX 渲染
- 图片/文档/视频预览

### Must NOT Have (Guardrails)
- **不得修改** `services/api.ts`、`services/websocket.ts`、`hooks/useWebSocket.ts`、`hooks/useWorkflowHistory.ts`、`contexts/WorkflowContext.tsx`、`types/index.ts`、`config/workflowGraphs.ts`、`constants/workflowSteps.ts`、`utils/timeUtils.ts`
- **不得修改** 后端代码 (`backend/`)
- **不得添加** 新的状态管理库 (Redux/Zustand/Jotai)
- **不得添加** 动画库 (framer-motion/react-spring)
- **不得添加** 额外的 npm 依赖（仅允许: tailwindcss, @tailwindcss/vite, @radix-ui/*, sonner, vitest, @testing-library/react, @testing-library/jest-dom, jsdom）
- **不得实现** 移动端响应式（这是桌面 IDE 风格应用）
- **不得** 在同一 commit 混合死代码删除和功能重写
- **避免 AI 模式**: 过度注释、不必要的抽象、泛型命名 (data/result/item)

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: NO (need to create)
- **Automated tests**: Tests-after (component smoke tests after implementation)
- **Framework**: vitest + @testing-library/react
- **If TDD**: N/A

### QA Policy
Every task MUST include agent-executed QA scenarios.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Frontend/UI**: Use Playwright (playwright skill) — Navigate, interact, assert DOM, screenshot
- **Build Verification**: Use Bash — `npm run build`, grep for errors
- **Import Verification**: Use Bash — `grep -r "from 'antd'" frontend/src/`

### Smoke Test Command (after EVERY commit)
```bash
cd frontend && npm run build 2>&1 | tail -5
# Expected: "✓ built in Xms"
# FAIL if: any TypeScript errors or import resolution failures
```

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — foundation + cleanup):
├── Task 1:  Dead code deletion (10 files + cherry-markdown) [quick]
├── Task 2:  Install Tailwind v4 + configure design system [quick]
├── Task 3:  Install headless UI primitives (Radix + sonner + vitest) [quick]
└── Task 4:  Toast abstraction layer (services/toast.ts) [quick]

Wave 2 (After Wave 1 — shared components):
├── Task 5:  MarkdownRenderer shared component [unspecified-high]
├── Task 6:  ModelSelector (Tailwind + Radix) [unspecified-high]
├── Task 7:  IDE Layout shell (Sidebar + Header + AppLayout) [visual-engineering]
└── Task 8:  WorkflowPanel base component [deep]

Wave 3 (After Wave 2 — page rewrites, MAX PARALLEL):
├── Task 9:  Rewrite HomePage + DrawingPanel [visual-engineering]
├── Task 10: Rewrite DocumentPanel [visual-engineering]
├── Task 11: Rewrite ManimPanel [visual-engineering]
└── Task 12: Rewrite App.tsx (remove Ant Design Layout) [deep]

Wave 4 (After Wave 3 — secondary pages + cleanup):
├── Task 13: Rewrite HistoryPage + PreviewModal [visual-engineering]
├── Task 14: Rewrite ThemeContext + common components [unspecified-high]
└── Task 15: Remove Ant Design + React Flow from package.json [quick]

Wave 5 (After Wave 4 — final integration + verification):
├── Task 16: End-to-end integration verification [deep]
└── Task 17: Final cleanup + bundle optimization [unspecified-high]

Wave FINAL (After ALL tasks — 4 parallel reviews):
├── Task F1: Plan compliance audit [oracle]
├── Task F2: Code quality review [unspecified-high]
├── Task F3: Real manual QA [unspecified-high]
└── Task F4: Scope fidelity check [deep]
-> Present results -> Get explicit user okay

Critical Path: T1→T2→T7→T8→T9→T12→T15→T16→F1-F4
Parallel Speedup: ~60% faster than sequential
Max Concurrent: 4 (Waves 2-3)
```

### Dependency Matrix

| Task | Depends On | Blocks | Wave |
|------|-----------|--------|------|
| 1 | — | 2, 3, 4 | 1 |
| 2 | 1 | 5, 6, 7, 8 | 1 |
| 3 | 1 | 4, 6 | 1 |
| 4 | 3 | 9, 10, 11 | 1 |
| 5 | 2 | 10, 13 | 2 |
| 6 | 2, 3 | 7, 9 | 2 |
| 7 | 2, 6 | 9, 12 | 2 |
| 8 | 2, 5, 6 | 9, 10, 11 | 2 |
| 9 | 7, 8 | 12, 16 | 3 |
| 10 | 5, 8 | 12, 16 | 3 |
| 11 | 8 | 12, 16 | 3 |
| 12 | 7, 9 | 13, 15 | 3 |
| 13 | 5, 12 | 16 | 4 |
| 14 | 12 | 15 | 4 |
| 15 | 12, 14 | 16 | 4 |
| 16 | 9, 10, 11, 13, 15 | 17 | 5 |
| 17 | 16 | FINAL | 5 |

### Agent Dispatch Summary

- **Wave 1**: **4** — T1→`quick`, T2→`quick`, T3→`quick`, T4→`quick`
- **Wave 2**: **4** — T5→`unspecified-high`, T6→`unspecified-high`, T7→`visual-engineering`, T8→`deep`
- **Wave 3**: **4** — T9→`visual-engineering`, T10→`visual-engineering`, T11→`visual-engineering`, T12→`deep`
- **Wave 4**: **3** — T13→`visual-engineering`, T14→`unspecified-high`, T15→`quick`
- **Wave 5**: **2** — T16→`deep`, T17→`unspecified-high`
- **FINAL**: **4** — F1→`oracle`, F2→`unspecified-high`, F3→`unspecified-high`, F4→`deep`

---

## TODOs

> Implementation + Test = ONE Task. Never separate.
> EVERY task MUST have: Recommended Agent Profile + Parallelization info + QA Scenarios.

- [x] 1. **Delete Dead Code and Unused Dependencies**

  **What to do**:
  - Delete 9 orphaned component files:
    - `components/common/workflowViews/NodeGraphView.tsx`
    - `components/common/workflowViews/CardListView.tsx`
    - `components/common/workflowViews/TimelineView.tsx`
    - `components/common/workflowViews/WorkflowViewToolbar.tsx`
    - `components/common/StreamContentViewer.tsx`
    - `components/common/StreamContentList.tsx`
    - `components/common/StepProgressDisplay.tsx`
    - `components/common/StepItem.tsx`
    - `components/common/workflowViews/graphUtils.ts`
  - Delete orphaned CSS files for those components:
    - `components/common/workflowViews/CardListView.css`
    - `components/common/workflowViews/TimelineView.css`
    - `components/common/workflowViews/NodeGraphView.css`
    - `components/common/workflowViews/WorkflowViewToolbar.css`
    - `components/common/StreamContentList.css`
  - Delete `services/endpoints.ts` (unused, API endpoints are inline in api.ts)
  - Remove `cherry-markdown` from `package.json` (declared but never imported)
  - Run `npm install` to update lock file

  **Must NOT do**:
  - Do NOT delete any active components (verify each file has zero imports via `grep -r "import.*from.*'./{filename}'" frontend/src/`)
  - Do NOT modify any active component files
  - Do NOT remove `react-flow` yet (leave for Task 15)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Pure file deletion, no logic changes
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `git-master`: Not needed — no complex git operations

  **Parallelization**:
  - **Can Run In Parallel**: YES (with T2, T3, T4 — but T2 depends on clean state, so run first)
  - **Parallel Group**: Wave 1
  - **Blocks**: T2, T3, T4
  - **Blocked By**: None (can start immediately)

  **References**:

  **Pattern References**:
  - `frontend/src/components/common/workflowViews/` — Directory containing orphaned view components
  - `frontend/src/components/common/StreamContentList.tsx` — Unused collapse-based multi-node viewer

  **Verification References**:
  - Before deleting each file, run: `grep -r "import.*{filename}" frontend/src/ --include="*.tsx" --include="*.ts" | grep -v "node_modules"`
  - Only delete if ZERO imports found (excluding the file itself)

  **WHY Each Reference Matters**:
  - Each file in the workflowViews directory is potentially imported by WorkflowExecutionTracker. Verify BEFORE deleting.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Dead files have zero imports
    Tool: Bash (grep)
    Preconditions: frontend/ directory exists
    Steps:
      1. For each file to delete, run: `grep -r "import.*from.*'./{path}'" frontend/src/ --include="*.tsx" --include="*.ts" | grep -v node_modules`
      2. Assert: each grep returns empty output
    Expected Result: Zero import references to any deleted file
    Failure Indicators: Any grep returns a match
    Evidence: .sisyphus/evidence/task-1-dead-code-import-check.txt

  Scenario: Build succeeds after deletion
    Tool: Bash
    Preconditions: All dead files deleted, npm install completed
    Steps:
      1. Run `cd frontend && npm run build 2>&1 | tail -10`
      2. Assert: output contains "✓ built in"
    Expected Result: Clean build with zero errors
    Failure Indicators: TypeScript errors about missing imports
    Evidence: .sisyphus/evidence/task-1-build-after-deletion.txt
  ```

  **Commit**: YES
  - Message: `chore: remove dead code and unused dependencies`
  - Files: All deleted files, package.json, package-lock.json
  - Pre-commit: `cd frontend && npm run build`

- [x] 2. **Install and Configure Tailwind CSS v4**

  **What to do**:
  - Install Tailwind CSS v4: `npm install -D tailwindcss @tailwindcss/vite`
  - Update `vite.config.ts`: add `@tailwindcss/vite` plugin to plugins array
  - Rewrite `frontend/src/index.css`:
    - Replace ALL content with Tailwind v4 setup:
      ```css
      @import "tailwindcss";
      @custom-variant dark (&:where(.dark, .dark *));
      @theme {
        /* Design system tokens */
        --color-primary: #1E293B;
        --color-secondary: #334155;
        --color-accent: #22C55E;
        --color-bg-dark: #0F172A;
        --color-bg-card: #1E293B;
        --color-bg-input: #0F172A;
        --color-text-primary: #F8FAFC;
        --color-text-secondary: #94A3B8;
        --color-text-muted: #64748B;
        --color-border: #334155;
        --font-sans: 'Fira Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        --font-mono: 'Fira Code', 'Consolas', 'Monaco', monospace;
        /* Spacing scale */
        --spacing-sidebar: 56px;
        --spacing-header: 40px;
      }
      /* Base styles */
      body { ... }
      /* Scrollbar styles */
      /* CLI timeline styles preserved from WorkflowTimeline.css */
      ```
    - Preserve WorkflowTimeline CSS (`.cli-*` classes) — copy from `components/common/WorkflowTimeline.css`
    - Preserve code block styles (`.code-block`)
    - Remove ALL `.ant-*` selectors and `.workflow-panel-*` selectors
  - Add Google Fonts import for Fira Code + Fira Sans to `index.html` `<head>`
  - Delete `frontend/src/App.css` entirely (all styles moved to Tailwind)

  **Must NOT do**:
  - Do NOT modify any TypeScript files yet
  - Do NOT remove Ant Design from package.json yet (leave for T15)
  - Do NOT delete WorkflowTimeline.css yet (copy its content first, then it'll be cleaned in T14)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Configuration and CSS-only changes, no component logic
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with T3, T4 — after T1)
  - **Parallel Group**: Wave 1 (with T3, T4)
  - **Blocks**: T5, T6, T7, T8
  - **Blocked By**: T1 (clean state first)

  **References**:

  **Pattern References**:
  - `frontend/src/index.css` — Current global styles, contains `.workflow-panel-*` layout and `.ant-*` overrides to remove
  - `frontend/src/components/common/WorkflowTimeline.css` — CLI timeline styles to preserve (copy into index.css)
  - `frontend/src/components/common/EmptyView.css` — CLI empty view styles to preserve
  - `frontend/src/components/common/StreamContentItem.css` — Stream content styles to preserve

  **External References**:
  - Tailwind v4 docs: CSS-first config with `@theme { }` directive
  - `@custom-variant dark` for class-based dark mode matching existing ThemeContext

  **WHY Each Reference Matters**:
  - `index.css` is the current layout foundation — all `.workflow-panel-*` classes define the grid layout that will be replaced
  - `WorkflowTimeline.css` must be preserved because the CLI timeline is the primary execution view (Metis confirmed: zero Ant Design imports, fully portable)

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Tailwind compiles successfully
    Tool: Bash
    Preconditions: tailwindcss and @tailwindcss/vite installed
    Steps:
      1. Run `cd frontend && npm run build 2>&1 | tail -10`
      2. Assert: output contains "✓ built in"
    Expected Result: Clean build with Tailwind CSS generated
    Failure Indicators: "Cannot find module '@tailwindcss/vite'" or CSS parse errors
    Evidence: .sisyphus/evidence/task-2-tailwind-build.txt

  Scenario: Dark mode variant is configured
    Tool: Bash (grep)
    Preconditions: index.css rewritten
    Steps:
      1. Run `grep "@custom-variant dark" frontend/src/index.css`
      2. Assert: output matches "@custom-variant dark (&:where(.dark, .dark *));"
    Expected Result: Custom dark variant present
    Failure Indicators: No match or wrong syntax
    Evidence: .sisyphus/evidence/task-2-dark-variant.txt

  Scenario: CLI timeline styles preserved
    Tool: Bash (grep)
    Preconditions: index.css rewritten
    Steps:
      1. Run `grep ".cli-timeline" frontend/src/index.css`
      2. Assert: output contains ".cli-timeline" class definition
    Expected Result: CLI timeline CSS preserved
    Failure Indicators: No match — WorkflowTimeline will break
    Evidence: .sisyphus/evidence/task-2-cli-styles.txt
  ```

  **Commit**: YES
  - Message: `chore: install and configure Tailwind CSS v4`
  - Files: index.css, App.css (delete), vite.config.ts, index.html, package.json, package-lock.json
  - Pre-commit: `cd frontend && npm run build`

- [x] 3. **Install Headless UI Primitives and Test Infrastructure**

  **What to do**:
  - Install Radix UI primitives: `npm install @radix-ui/react-tabs @radix-ui/react-select @radix-ui/react-dialog @radix-ui/react-tooltip @radix-ui/react-popover @radix-ui/react-switch @radix-ui/react-separator`
  - Install toast: `npm install sonner`
  - Install test infrastructure: `npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom`
  - Create `frontend/vitest.config.ts`:
    ```typescript
    import { defineConfig } from 'vitest/config';
    import react from '@vitejs/plugin-react';
    export default defineConfig({
      plugins: [react()],
      test: { environment: 'jsdom', globals: true, setupFiles: ['./test-setup.ts'] }
    });
    ```
  - Create `frontend/test-setup.ts`: `import '@testing-library/jest-dom';`
  - Add test script to `package.json`: `"test": "vitest run", "test:watch": "vitest"`

  **Must NOT do**:
  - Do NOT install any other UI component libraries
  - Do NOT install animation libraries (framer-motion, react-spring)
  - Do NOT install state management libraries

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Package installation and config file creation only
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with T2, T4 — after T1)
  - **Parallel Group**: Wave 1
  - **Blocks**: T4, T6
  - **Blocked By**: T1

  **References**:

  **External References**:
  - Radix UI: Headless primitives for Tabs, Select, Dialog, Tooltip, Popover, Switch
  - Sonner: Lightweight toast library with `toast.success()`, `toast.error()`, `toast.warning()` API
  - Vitest: Vite-native test runner

  **WHY Each Reference Matters**:
  - Radix UI provides accessible, unstyled primitives that work with Tailwind — the exact replacement for Ant Design's Tabs, Select, Modal, etc.
  - Sonner's API (`toast.success/error/warning`) maps 1:1 to Ant Design's `message.success/error/warning`

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: All packages install successfully
    Tool: Bash
    Preconditions: npm install completed
    Steps:
      1. Run `cd frontend && node -e "require('@radix-ui/react-tabs'); require('sonner'); require('vitest'); console.log('OK')"`
      2. Assert: output is "OK"
    Expected Result: All packages resolvable
    Failure Indicators: "Cannot find module" errors
    Evidence: .sisyphus/evidence/task-3-packages-check.txt

  Scenario: Vitest runs with no tests
    Tool: Bash
    Preconditions: vitest.config.ts created
    Steps:
      1. Run `cd frontend && npx vitest run 2>&1 | tail -5`
      2. Assert: output contains "No test files found" or "0 tests"
    Expected Result: Vitest infrastructure working
    Failure Indicators: Config parse errors
    Evidence: .sisyphus/evidence/task-3-vitest-setup.txt
  ```

  **Commit**: YES
  - Message: `chore: install Radix UI, sonner, vitest`
  - Files: package.json, package-lock.json, vitest.config.ts, test-setup.ts
  - Pre-commit: `cd frontend && npm run build`

- [x] 4. **Create Toast Abstraction Layer**

  **What to do**:
  - Create `frontend/src/services/toast.ts`:
    ```typescript
    import { toast } from 'sonner';
    export const showToast = {
      success: (msg: string) => toast.success(msg),
      error: (msg: string) => toast.error(msg),
      warning: (msg: string) => toast.warning(msg),
      info: (msg: string) => toast.info(msg),
    };
    ```
  - This provides a framework-agnostic interface. When Ant Design is removed, only this file needs to change (sonner already is the implementation).
  - Write a smoke test: `frontend/src/services/__tests__/toast.test.ts`

  **Must NOT do**:
  - Do NOT modify any existing component files to use this yet (that happens in T9-T14)
  - Do NOT remove Ant Design message imports yet

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Single utility file with trivial test
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with T2 — after T1 and T3)
  - **Parallel Group**: Wave 1
  - **Blocks**: T9, T10, T11 (panels will use this instead of `message.*`)
  - **Blocked By**: T3 (sonner must be installed)

  **References**:

  **Pattern References**:
  - `frontend/src/components/drawing/DrawingPanel.tsx:48` — Example of current `message.success('绘图工作流已启动')` usage to be replaced
  - `frontend/src/components/drawing/DrawingPanel.tsx:50` — Example of current `message.error(...)` usage

  **API/Type References**:
  - `sonner` API: `toast.success(msg)`, `toast.error(msg)`, `toast.warning(msg)`, `toast.info(msg)` — 1:1 mapping to Ant Design's `message.*`

  **WHY Each Reference Matters**:
  - DrawingPanel shows the exact pattern to replace: 26 `message.*()` calls across 7 files. This abstraction decouples them.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Toast module exports correct API
    Tool: Bash
    Preconditions: services/toast.ts created
    Steps:
      1. Run `cd frontend && npx vitest run src/services/__tests__/toast.test.ts 2>&1 | tail -10`
      2. Assert: output contains "Tests  X passed"
    Expected Result: Toast smoke test passes
    Failure Indicators: Import errors or test failures
    Evidence: .sisyphus/evidence/task-4-toast-test.txt

  Scenario: Build succeeds with toast module
    Tool: Bash
    Steps:
      1. Run `cd frontend && npm run build 2>&1 | tail -5`
      2. Assert: output contains "✓ built in"
    Expected Result: Clean build
    Failure Indicators: TypeScript errors
    Evidence: .sisyphus/evidence/task-4-build.txt
  ```

  **Commit**: YES
  - Message: `feat: add toast abstraction layer`
  - Files: services/toast.ts, services/__tests__/toast.test.ts
  - Pre-commit: `cd frontend && npm run build && npx vitest run`

- [x] 5. **Create Shared MarkdownRenderer Component**

  **What to do**:
  - Create `frontend/src/components/shared/MarkdownRenderer.tsx`
  - Extract the shared ReactMarkdown configuration currently duplicated in:
    - `DocumentPanel.tsx` lines 199-248 (preview tab)
    - `DocumentPanel.tsx` lines 262-311 (outline tab)
    - `PreviewModal.tsx` (document preview)
  - The component should accept `content: string` as prop
  - Include: `remarkMath`, `rehypeRaw`, `rehypeKatex` (with `throwOnError: false, strict: false`)
  - Include shared `img` component override (max-width 100%, onerror logging)
  - Include shared `code` component override (inline vs block detection)
  - Replace 3 duplicates with single import

  **Must NOT do**:
  - Do NOT change the rendering behavior — preserve exact same markdown/code/image rendering
  - Do NOT add syntax highlighting yet (keep react-syntax-highlighter integration in StreamContentItem separate)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Needs careful extraction of existing behavior, moderate complexity
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with T6, T7, T8)
  - **Blocks**: T10 (DocumentPanel), T13 (PreviewModal)
  - **Blocked By**: T2 (Tailwind must be configured)

  **References**:

  **Pattern References**:
  - `frontend/src/components/document/DocumentPanel.tsx:199-248` — ReactMarkdown config for preview tab (PRIMARY PATTERN TO FOLLOW)
  - `frontend/src/components/document/DocumentPanel.tsx:262-311` — Identical config for outline tab (DUPLICATE)
  - `frontend/src/components/PreviewModal.tsx` — Third instance of same config

  **API/Type References**:
  - `react-markdown` — `ReactMarkdown` component API
  - `remark-math` — Math notation parsing plugin
  - `rehype-katex` — KaTeX rendering plugin
  - `rehype-raw` — Raw HTML in markdown

  **WHY Each Reference Matters**:
  - The DocumentPanel duplicates ~100 lines of ReactMarkdown config. This is the exact code to extract into the shared component.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: MarkdownRenderer renders basic markdown
    Tool: Bash (vitest)
    Preconditions: Component created
    Steps:
      1. Write test: render(<MarkdownRenderer content="# Hello **world**" />)
      2. Assert: h1 element with "Hello" exists, bold text exists
      3. Run `cd frontend && npx vitest run src/components/shared/__tests__/MarkdownRenderer.test.tsx`
    Expected Result: Test passes, markdown rendered correctly
    Failure Indicators: Component import errors or missing plugins
    Evidence: .sisyphus/evidence/task-5-markdown-test.txt

  Scenario: MarkdownRenderer renders math (KaTeX)
    Tool: Bash (vitest)
    Steps:
      1. Write test: render(<MarkdownRenderer content="$E = mc^2$" />)
      2. Assert: katex HTML elements present in output
    Expected Result: KaTeX math rendered
    Failure Indicators: Missing remark-math or rehype-katex
    Evidence: .sisyphus/evidence/task-5-katex-test.txt

  Scenario: Build succeeds
    Tool: Bash
    Steps:
      1. Run `cd frontend && npm run build 2>&1 | tail -5`
    Expected Result: "✓ built in Xms"
    Evidence: .sisyphus/evidence/task-5-build.txt
  ```

  **Commit**: YES
  - Message: `feat: add MarkdownRenderer shared component`
  - Files: components/shared/MarkdownRenderer.tsx, components/shared/__tests__/MarkdownRenderer.test.tsx
  - Pre-commit: `cd frontend && npm run build && npx vitest run`

- [x] 6. **Create Tailwind ModelSelector Component**

  **What to do**:
  - Create `frontend/src/components/shared/ModelSelector.tsx` (overwrite existing Ant Design version)
  - Replace Ant Design `Select` with Radix UI Select for provider and model dropdowns
  - Replace Ant Design `Switch` with Radix UI Switch for thinking toggle
  - Replace Ant Design `Tag` with custom Tailwind badge components for status indicators
  - Replace `@ant-design/icons` (RobotOutlined, ThunderboltOutlined, BulbOutlined) with Lucide equivalents
  - Compact design: provider selector + model selector + thinking toggle in a single row
  - Props interface stays the same: `onModelChange: (config: ModelConfig) => void`
  - Must work with existing `WorkflowContext` — read `modelConfig` from context, call `setModelConfig`

  **Must NOT do**:
  - Do NOT change the API calls in `api.ts` for model switching
  - Do NOT change the `ModelConfig` type definition
  - Do NOT add new state — use existing `WorkflowContext`

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Complex interactive component with 3 sub-controls, Radix UI integration
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: T7 (layout needs ModelSelector), T9 (panels use it)
  - **Blocked By**: T2 (Tailwind), T3 (Radix UI)

  **References**:

  **Pattern References**:
  - `frontend/src/components/common/ModelSelector.tsx` — CURRENT implementation with Ant Design Select, Switch, Tag (FOLLOW the logic, replace the UI)
  - `frontend/src/contexts/WorkflowContext.tsx` — State management: `modelConfig`, `setModelConfig` interface

  **API/Type References**:
  - `frontend/src/types/index.ts:ModelConfig` — Type definition for model configuration
  - `frontend/src/services/api.ts:getAvailableModels()` — API call to fetch model list
  - `frontend/src/services/api.ts:switchModel()` — API call to switch model

  **External References**:
  - Radix UI Select: https://www.radix-ui.com/primitives/docs/components/select
  - Radix UI Switch: https://www.radix-ui.com/primitives/docs/components/switch

  **WHY Each Reference Matters**:
  - ModelSelector.tsx is the exact file being rewritten. Read the CURRENT logic to preserve behavior while replacing UI primitives.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: ModelSelector renders provider options
    Tool: Bash (vitest)
    Steps:
      1. Mock `api.getAvailableModels` to return DeepSeek + Ollama providers
      2. Render ModelSelector
      3. Assert: "DeepSeek" and "Ollama" text visible
    Expected Result: Both providers rendered
    Evidence: .sisyphus/evidence/task-6-model-selector-test.txt

  Scenario: ModelSelector switches provider
    Tool: Bash (vitest)
    Steps:
      1. Render ModelSelector
      2. Click provider dropdown, select "Ollama"
      3. Assert: `onModelChange` called with `{ provider: 'ollama', ... }`
    Expected Result: Provider change triggers callback
    Evidence: .sisyphus/evidence/task-6-provider-switch.txt

  Scenario: Build succeeds
    Tool: Bash
    Steps:
      1. `cd frontend && npm run build`
    Expected Result: Clean build
    Evidence: .sisyphus/evidence/task-6-build.txt
  ```

  **Commit**: YES
  - Message: `feat: add ModelSelector with Radix UI`
  - Files: components/shared/ModelSelector.tsx, components/shared/__tests__/ModelSelector.test.tsx
  - Pre-commit: `cd frontend && npm run build`

- [x] 7. **Build IDE Layout Shell (Sidebar + Header + AppLayout)**

  **What to do**:
  - Create `frontend/src/components/layout/Sidebar.tsx`:
    - 56px wide icon sidebar (左对齐)
    - Icons for: 绘图 (BarChart), 文档 (FileText), 动画 (Video), 历史记录 (History)
    - Active state: highlighted icon + small indicator bar
    - Workflow switch calls `setCurrentWorkflow` from context
    - Workflow navigation triggers route change or panel switch
    - Bottom section: theme toggle icon (Sun/Moon)
  - Create `frontend/src/components/layout/Header.tsx`:
    - 40px height compact bar
    - Left: Page title (dynamic based on active workflow)
    - Right: ModelSelector inline (compact, no Card wrapper)
    - No logo needed (sidebar has branding)
  - Create `frontend/src/components/layout/AppLayout.tsx`:
    - Sidebar (56px fixed) + main content area (flex: 1)
    - Main content = Header (40px) + Content (flex: 1, overflow: hidden)
    - Full height layout (100vh)
    - Dark theme: bg-[#0F172A] sidebar, bg-[#1E293B] main content
    - Light theme: bg-white sidebar, bg-gray-50 main content
  - Style: Tailwind classes only, zero inline styles

  **Must NOT do**:
  - Do NOT implement mobile responsive (desktop-only IDE)
  - Do NOT add animation libraries
  - Do NOT modify `App.tsx` yet (that's T12)
  - Do NOT modify any existing page components

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: Core visual layout with dark/light theme, interactive sidebar
  - **Skills**: [`ui-ux-pro-max`]
    - `ui-ux-pro-max`: Design system tokens and color palette guidance

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: T9 (HomePage needs layout), T12 (App.tsx uses layout)
  - **Blocked By**: T2 (Tailwind), T6 (ModelSelector)

  **References**:

  **Pattern References**:
  - `frontend/src/App.tsx:26-80` — Current Layout structure to replace (Header + Content)
  - `frontend/src/pages/HomePage.tsx` — Current tab-based navigation (logic to move into sidebar)

  **API/Type References**:
  - `frontend/src/contexts/WorkflowContext.tsx:setCurrentWorkflow` — Sidebar calls this
  - `frontend/src/contexts/ThemeContext.tsx:useTheme` — Theme toggle

  **Design System References**:
  - Colors: Primary #1E293B, CTA #22C55E, BG #0F172A, Text #F8FAFC
  - Data-Dense Dashboard: 56px sidebar, 40px header, 8px gap, 12px padding

  **WHY Each Reference Matters**:
  - App.tsx shows the current layout structure being replaced. HomePage shows the navigation logic to move into sidebar.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Sidebar renders all 4 navigation icons
    Tool: Bash (vitest)
    Steps:
      1. Render <Sidebar />
      2. Assert: 4 icon buttons rendered (BarChart, FileText, Video, History)
      3. Assert: Each has cursor-pointer and hover state classes
    Expected Result: All 4 navigation items visible
    Evidence: .sisyphus/evidence/task-7-sidebar-test.txt

  Scenario: Sidebar click switches active workflow
    Tool: Bash (vitest)
    Steps:
      1. Render <Sidebar /> with WorkflowContext
      2. Click "document" icon
      3. Assert: `setCurrentWorkflow` called with 'document'
    Expected Result: Workflow switch triggered
    Evidence: .sisyphus/evidence/task-7-sidebar-click.txt

  Scenario: Layout renders with correct structure
    Tool: Bash (vitest)
    Steps:
      1. Render <AppLayout />
      2. Assert: Sidebar has w-14 class (56px)
      3. Assert: Header has h-10 class (40px)
      4. Assert: Content area has flex-1 class
    Expected Result: IDE layout structure correct
    Evidence: .sisyphus/evidence/task-7-layout-test.txt

  Scenario: Build succeeds
    Tool: Bash
    Steps:
      1. `cd frontend && npm run build`
    Expected Result: Clean build
    Evidence: .sisyphus/evidence/task-7-build.txt
  ```

  **Commit**: YES
  - Message: `feat: add IDE layout (Sidebar + Header + AppLayout)`
  - Files: components/layout/Sidebar.tsx, components/layout/Header.tsx, components/layout/AppLayout.tsx, components/layout/__tests__/*.test.tsx
  - Pre-commit: `cd frontend && npm run build`

- [x] 8. **Create Shared WorkflowPanel Base Component**

  **What to do**:
  - Create `frontend/src/components/shared/WorkflowPanel.tsx`
  - Extract the shared structure from all 3 panels:
    ```
    Props:
    - workflowType: 'drawing' | 'document_with_images' | 'manim'
    - apiStart: (prompt, options) => Promise
    - apiStop: () => Promise
    - apiClear: () => Promise
    - placeholder: string
    - startLabel: string
    - runningLabel: string
    - extraControls?: ReactNode (e.g., Manim quality selector)
    - renderResult: (result) => ReactNode
    ```
  - Component provides:
    - Input area: textarea + action buttons (start/stop/clear) + status indicator
    - Timeline area: WorkflowTimeline (reuse existing component as-is)
    - Result area: delegated to `renderResult` prop
  - Layout: Top-bottom split (NOT left-right):
    - Top strip: Input + controls (compact, ~80px when collapsed)
    - Bottom: Two-column split — Left: Timeline, Right: Result
    - Or: Timeline as collapsible bottom drawer, Result fills main area
  - Use `useWebSocket(workflowType)` internally
  - Use `useWorkflow()` for model config
  - Replace `message.*()` with `showToast.*()` from toast.ts

  **Must NOT do**:
  - Do NOT modify `WorkflowTimeline.tsx` — reuse as-is (it already uses zero Ant Design)
  - Do NOT modify `useWebSocket` hook
  - Do NOT add new state management

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Architectural component that unifies 3 panels, needs careful prop design
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: T9, T10, T11 (all panels use this)
  - **Blocked By**: T2 (Tailwind), T5 (MarkdownRenderer), T6 (ModelSelector)

  **References**:

  **Pattern References**:
  - `frontend/src/components/drawing/DrawingPanel.tsx` — Drawing panel structure (FOLLOW this pattern)
  - `frontend/src/components/document/DocumentPanel.tsx` — Document panel structure
  - `frontend/src/components/manim/ManimPanel.tsx` — Manim panel structure (has extra quality selector)

  **API/Type References**:
  - `frontend/src/hooks/useWebSocket.ts:useWebSocket` — Hook signature and return type
  - `frontend/src/contexts/WorkflowContext.tsx` — Model config access
  - `frontend/src/types/index.ts:WorkflowStep`, `WorkflowResult` — Type definitions
  - `frontend/src/services/toast.ts` — Toast abstraction (from T4)

  **WHY Each Reference Matters**:
  - All 3 panels have identical structure with minor variations (Manim has quality selector, Document has different result tabs). The WorkflowPanel base captures the shared 80%.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: WorkflowPanel renders input area
    Tool: Bash (vitest)
    Steps:
      1. Render <WorkflowPanel workflowType="drawing" apiStart={mock} apiStop={mock} apiClear={mock} placeholder="test" startLabel="Start" runningLabel="Running" renderResult={() => null} />
      2. Assert: textarea with placeholder exists
      3. Assert: Start button exists
    Expected Result: Input area rendered with correct elements
    Evidence: .sisyphus/evidence/task-8-workflow-panel-test.txt

  Scenario: WorkflowPanel disables input when running
    Tool: Bash (vitest)
    Steps:
      1. Mock useWebSocket to return { status: 'running' }
      2. Render WorkflowPanel
      3. Assert: textarea is disabled
      4. Assert: Stop button is visible
    Expected Result: Running state handled correctly
    Evidence: .sisyphus/evidence/task-8-running-state.txt

  Scenario: Build succeeds
    Tool: Bash
    Steps:
      1. `cd frontend && npm run build`
    Expected Result: Clean build
    Evidence: .sisyphus/evidence/task-8-build.txt
  ```

  **Commit**: YES
  - Message: `feat: add WorkflowPanel base component`
  - Files: components/shared/WorkflowPanel.tsx, components/shared/__tests__/WorkflowPanel.test.tsx
  - Pre-commit: `cd frontend && npm run build`

- [x] 9. **Rewrite HomePage and DrawingPanel**

  **What to do**:
  - Rewrite `frontend/src/pages/HomePage.tsx`:
    - Remove Ant Design `Tabs` import
    - Use `AppLayout` (sidebar navigation handles workflow switching)
    - Render active panel based on sidebar state (not tabs)
    - Remove `GlobalModelBar` (ModelSelector moved to Header)
  - Rewrite `frontend/src/components/drawing/DrawingPanel.tsx`:
    - Remove all Ant Design imports (Card, Input, Button, Space, Image, Tabs, message)
    - Remove `@ant-design/icons` imports
    - Use `WorkflowPanel` base component with `workflowType="drawing"`
    - Implement `renderResult` prop:
      - Image tab: `<img>` with Tailwind styling (max-w-full, object-contain)
      - Code tab: `<pre>` with Fira Code font, dark background
    - Use `showToast.*()` instead of `message.*()`
    - Replace Ant Design `Image` with native `<img>` + lightbox trigger
    - Replace Ant Design `Tabs` with Radix UI Tabs
    - All styling via Tailwind classes, zero inline styles
  - Delete `frontend/src/components/common/GlobalModelBar.tsx` (no longer needed, ModelSelector in Header)

  **Must NOT do**:
  - Do NOT modify `useWebSocket` hook
  - Do NOT change API call signatures
  - Do NOT modify `WorkflowTimeline` component

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: Full panel rewrite with Tailwind styling, result display
  - **Skills**: [`ui-ux-pro-max`]
    - `ui-ux-pro-max`: Layout and spacing guidelines for compact UI

  **Parallelization**:
  - **Can Run In Parallel**: YES (with T10, T11)
  - **Parallel Group**: Wave 3
  - **Blocks**: T12 (App.tsx needs all panels working)
  - **Blocked By**: T7 (layout), T8 (WorkflowPanel base)

  **References**:

  **Pattern References**:
  - `frontend/src/components/drawing/DrawingPanel.tsx` — CURRENT implementation (follow logic, replace UI)
  - `frontend/src/components/shared/WorkflowPanel.tsx` — NEW base component (from T8)

  **API/Type References**:
  - `frontend/src/services/api.ts:startDrawingWorkflow()` — API call
  - `frontend/src/services/api.ts:stopDrawingWorkflow()` — API call
  - `frontend/src/services/api.ts:clearDrawingHistory()` — API call
  - `frontend/src/types/index.ts` — WorkflowResult type for drawing (has image_url, generated_code)

  **WHY Each Reference Matters**:
  - DrawingPanel is being rewritten. Read current logic to preserve behavior while replacing all Ant Design components with Tailwind + Radix.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: DrawingPanel renders with no Ant Design imports
    Tool: Bash (grep)
    Steps:
      1. Run `grep -r "from 'antd'" frontend/src/pages/HomePage.tsx frontend/src/components/drawing/`
      2. Run `grep -r "from '@ant-design/icons'" frontend/src/pages/HomePage.tsx frontend/src/components/drawing/`
      3. Assert: both return empty
    Expected Result: Zero Ant Design imports
    Failure Indicators: Any matches found
    Evidence: .sisyphus/evidence/task-9-no-antd.txt

  Scenario: DrawingPanel renders input and buttons
    Tool: Bash (vitest)
    Steps:
      1. Render DrawingPanel with mocked WebSocket
      2. Assert: textarea with placeholder exists
      3. Assert: "开始生成" button exists
    Expected Result: All UI elements present
    Evidence: .sisyphus/evidence/task-9-drawing-panel-test.txt

  Scenario: HomePage shows DrawingPanel by default
    Tool: Bash (vitest)
    Steps:
      1. Render HomePage
      2. Assert: textarea visible (DrawingPanel rendered)
    Expected Result: DrawingPanel is default view
    Evidence: .sisyphus/evidence/task-9-homepage-test.txt

  Scenario: Build succeeds
    Tool: Bash
    Steps:
      1. `cd frontend && npm run build 2>&1 | tail -5`
    Expected Result: "✓ built in Xms"
    Evidence: .sisyphus/evidence/task-9-build.txt
  ```

  **Commit**: YES
  - Message: `refactor: rewrite HomePage and DrawingPanel with Tailwind`
  - Files: pages/HomePage.tsx, components/drawing/DrawingPanel.tsx
  - Pre-commit: `cd frontend && npm run build`

- [x] 10. **Rewrite DocumentPanel**

  **What to do**:
  - Rewrite `frontend/src/components/document/DocumentPanel.tsx`:
    - Remove all Ant Design imports (Card, Input, Button, Space, Tabs, Image, message)
    - Remove `@ant-design/icons` imports
    - Use `WorkflowPanel` base component with `workflowType="document_with_images"`
    - Implement `renderResult` prop with 3 tabs (Radix UI Tabs):
      - Preview: Use shared `MarkdownRenderer`
      - Outline: Use shared `MarkdownRenderer`
      - Images: Grid of image thumbnails with descriptions
    - Replace `result.content.replace(../images/...)` path logic — keep the logic but in cleaner form
    - Use `showToast.*()` instead of `message.*()`
    - All styling via Tailwind, zero inline styles

  **Must NOT do**:
  - Do NOT modify `useWebSocket` hook
  - Do NOT change API calls
  - Do NOT change the image path conversion logic

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: Most complex panel with Markdown rendering, image gallery, multiple tabs
  - **Skills**: [`ui-ux-pro-max`]

  **Parallelization**:
  - **Can Run In Parallel**: YES (with T9, T11)
  - **Parallel Group**: Wave 3
  - **Blocks**: T12
  - **Blocked By**: T5 (MarkdownRenderer), T8 (WorkflowPanel base)

  **References**:

  **Pattern References**:
  - `frontend/src/components/document/DocumentPanel.tsx` — CURRENT implementation (follow logic, replace UI)
  - `frontend/src/components/shared/MarkdownRenderer.tsx` — NEW shared component (from T5)
  - `frontend/src/components/shared/WorkflowPanel.tsx` — NEW base component (from T8)

  **API/Type References**:
  - `frontend/src/services/api.ts:startDocumentWorkflow()` — API call
  - `frontend/src/services/api.ts:stopDocumentWorkflow()` — API call
  - `frontend/src/services/api.ts:clearDocumentHistory()` — API call
  - `frontend/src/types/index.ts` — WorkflowResult for document (has url, content, outline, images, image_count)

  **WHY Each Reference Matters**:
  - DocumentPanel is the most complex panel. The MarkdownRenderer extraction (T5) eliminates ~100 lines of duplication here.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: DocumentPanel renders with no Ant Design imports
    Tool: Bash (grep)
    Steps:
      1. `grep -r "from 'antd'" frontend/src/components/document/`
      2. `grep -r "from '@ant-design/icons'" frontend/src/components/document/`
      3. Assert: both empty
    Expected Result: Zero Ant Design imports
    Evidence: .sisyphus/evidence/task-10-no-antd.txt

  Scenario: DocumentPanel uses MarkdownRenderer
    Tool: Bash (grep)
    Steps:
      1. `grep "MarkdownRenderer" frontend/src/components/document/DocumentPanel.tsx`
      2. Assert: import exists
    Expected Result: Shared component used instead of inline config
    Evidence: .sisyphus/evidence/task-10-markdown-import.txt

  Scenario: Build succeeds
    Tool: Bash
    Steps:
      1. `cd frontend && npm run build`
    Expected Result: Clean build
    Evidence: .sisyphus/evidence/task-10-build.txt
  ```

  **Commit**: YES
  - Message: `refactor: rewrite DocumentPanel with Tailwind`
  - Files: components/document/DocumentPanel.tsx
  - Pre-commit: `cd frontend && npm run build`

- [x] 11. **Rewrite ManimPanel**

  **What to do**:
  - Rewrite `frontend/src/components/manim/ManimPanel.tsx`:
    - Remove all Ant Design imports (Card, Input, Button, Space, Tabs, Select, message)
    - Remove `@ant-design/icons` imports
    - Use `WorkflowPanel` base component with `workflowType="manim"`
    - Pass quality selector as `extraControls` prop to WorkflowPanel
    - Implement `renderResult` prop:
      - Video tab: `<video>` with controls, Tailwind styling
      - Code tab: `<pre>` with Fira Code font
    - Replace Ant Design `Select` for quality with Radix UI Select
    - Use `showToast.*()` instead of `message.*()`
    - All styling via Tailwind

  **Must NOT do**:
  - Do NOT change quality options or values
  - Do NOT modify API calls

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`ui-ux-pro-max`]

  **Parallelization**:
  - **Can Run In Parallel**: YES (with T9, T10)
  - **Parallel Group**: Wave 3
  - **Blocks**: T12
  - **Blocked By**: T8 (WorkflowPanel base)

  **References**:

  **Pattern References**:
  - `frontend/src/components/manim/ManimPanel.tsx` — CURRENT implementation

  **API/Type References**:
  - `frontend/src/services/api.ts:startManimWorkflow()` — API call (note: takes quality param)
  - `frontend/src/types/index.ts` — WorkflowResult for manim (has video_url, generated_code)

  **WHY Each Reference Matters**:
  - ManimPanel is structurally identical to DrawingPanel but adds the quality selector. The WorkflowPanel base handles the shared structure.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: ManimPanel renders quality selector
    Tool: Bash (vitest)
    Steps:
      1. Render ManimPanel
      2. Assert: quality dropdown visible with 4 options
    Expected Result: Quality selector rendered
    Evidence: .sisyphus/evidence/task-11-quality-test.txt

  Scenario: ManimPanel has no Ant Design imports
    Tool: Bash (grep)
    Steps:
      1. `grep -r "from 'antd'" frontend/src/components/manim/`
      2. Assert: empty output
    Expected Result: Zero imports
    Evidence: .sisyphus/evidence/task-11-no-antd.txt

  Scenario: Build succeeds
    Tool: Bash
    Steps:
      1. `cd frontend && npm run build`
    Expected Result: Clean build
    Evidence: .sisyphus/evidence/task-11-build.txt
  ```

  **Commit**: YES
  - Message: `refactor: rewrite ManimPanel with Tailwind`
  - Files: components/manim/ManimPanel.tsx
  - Pre-commit: `cd frontend && npm run build`

- [x] 12. **Rewrite App.tsx — Remove Ant Design Layout**

  **What to do**:
  - Rewrite `frontend/src/App.tsx`:
    - Remove: `Layout`, `theme`, `Button`, `ConfigProvider` from Ant Design
    - Remove: `HomeOutlined`, `HistoryOutlined`, `SunOutlined`, `MoonOutlined` from @ant-design/icons
    - Remove: `antd/locale/zh_CN` import
    - Use new `AppLayout` component (from T7) instead of Ant Design `Layout`
    - Routes remain: `/` → HomePage, `/history` → HistoryPage
    - Theme: Keep `ThemeContext` for dark/light toggle, remove Ant Design `ConfigProvider`
    - Add `sonner` `<Toaster />` component at root level
    - Use Lucide icons for theme toggle
  - Delete `frontend/src/App.css`:
    - All styles migrated to Tailwind classes or `index.css` design system
    - Remove `.dark .ant-*` overrides (no longer needed)
    - Remove `.workflow-status-indicator`, `.code-block`, `.stream-controls` (handled by Tailwind)
    - Preserve `@keyframes fadeIn` animation → move to `index.css` if needed
  - Update `frontend/src/index.css`:
    - Remove all `.ant-*` selector overrides
    - Remove `.workflow-panel`, `.workflow-panel-left`, `.workflow-panel-right` (replaced by WorkflowPanel component)
    - Remove all `@media` responsive breakpoints (desktop-only now)
    - Keep only: Tailwind `@import`, `@theme`, `@custom-variant dark`, base resets, font imports

  **Must NOT do**:
  - Do NOT modify routes or routing logic
  - Do NOT remove `ThemeContext` — keep it, just stop using Ant Design's ConfigProvider

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Root component rewrite that connects all pieces, must be done after all panels work
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO (must wait for T7, T9, T10, T11)
  - **Parallel Group**: Wave 3 (sequential within wave — last)
  - **Blocks**: T13, T14, T15
  - **Blocked By**: T7 (layout), T9, T10, T11 (all panels must work)

  **References**:

  **Pattern References**:
  - `frontend/src/App.tsx` — CURRENT root component
  - `frontend/src/components/layout/AppLayout.tsx` — NEW layout (from T7)

  **API/Type References**:
  - `frontend/src/contexts/ThemeContext.tsx` — Theme provider (KEEP)
  - `frontend/src/contexts/WorkflowContext.tsx` — Workflow provider (KEEP)

  **WHY Each Reference Matters**:
  - App.tsx is the root that wraps everything. Must cleanly replace Ant Design ConfigProvider with Tailwind-based theming.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: App.tsx has no Ant Design imports
    Tool: Bash (grep)
    Steps:
      1. `grep "from 'antd'" frontend/src/App.tsx`
      2. `grep "from '@ant-design/icons'" frontend/src/App.tsx`
      3. `grep "antd/locale" frontend/src/App.tsx`
      4. Assert: all return empty
    Expected Result: Zero Ant Design in root component
    Evidence: .sisyphus/evidence/task-12-no-antd.txt

  Scenario: App.tsx has Toaster component
    Tool: Bash (grep)
    Steps:
      1. `grep "Toaster" frontend/src/App.tsx`
      2. Assert: import from 'sonner' exists
    Expected Result: Sonner Toaster present
    Evidence: .sisyphus/evidence/task-12-toaster.txt

  Scenario: App.css deleted, index.css clean
    Tool: Bash
    Steps:
      1. `test -f frontend/src/App.css && echo "EXISTS" || echo "DELETED"`
      2. Assert: "DELETED"
      3. `grep ".ant-" frontend/src/index.css`
      4. Assert: empty output
    Expected Result: App.css gone, no Ant CSS selectors
    Evidence: .sisyphus/evidence/task-12-css-cleanup.txt

  Scenario: Build succeeds
    Tool: Bash
    Steps:
      1. `cd frontend && npm run build 2>&1 | tail -5`
    Expected Result: "✓ built in Xms"
    Evidence: .sisyphus/evidence/task-12-build.txt
  ```

  **Commit**: YES
  - Message: `refactor: rewrite App.tsx with new layout`
  - Files: App.tsx, App.css (delete), index.css (clean up)
  - Pre-commit: `cd frontend && npm run build`

- [ ] 13. **Rewrite HistoryPage and PreviewModal**

  **What to do**:
  - Rewrite `frontend/src/pages/HistoryPage.tsx`:
    - Remove all Ant Design imports (Card, List, Tag, Button, Empty, message, Modal)
    - Remove `@ant-design/icons` imports
    - New layout: Grid view instead of flat List
      - Filter bar at top: type filters (All / Images / Documents / Videos) using Radix Tabs or button group
      - Grid of cards: thumbnail/icon + filename + type badge + size + relative time
      - Each card: hover → show preview button + delete button
      - Click → open PreviewModal
    - Delete confirmation: Use Radix UI Dialog instead of `Modal.confirm`
    - Use `showToast.*()` for success/error feedback
    - All styling via Tailwind
  - Rewrite `frontend/src/components/PreviewModal.tsx`:
    - Replace Ant Design `Modal` with Radix UI `Dialog`
    - Replace Ant Design `Image` with native `<img>` for images
    - Use shared `MarkdownRenderer` for document preview
    - Video: native `<video>` element (same as current)
    - Dialog: 80% width, centered, with close button
    - Dark theme aware

  **Must NOT do**:
  - Do NOT change the `useWorkflowHistory` hook
  - Do NOT change API calls for delete
  - Do NOT add search functionality (out of scope)

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: Grid layout with filter bar, modal, card design
  - **Skills**: [`ui-ux-pro-max`]

  **Parallelization**:
  - **Can Run In Parallel**: YES (with T14, T15)
  - **Parallel Group**: Wave 4
  - **Blocks**: T16
  - **Blocked By**: T5 (MarkdownRenderer), T12 (App.tsx must be done)

  **References**:

  **Pattern References**:
  - `frontend/src/pages/HistoryPage.tsx` — CURRENT history page with flat List
  - `frontend/src/components/PreviewModal.tsx` — CURRENT preview modal

  **API/Type References**:
  - `frontend/src/hooks/useWorkflowHistory.ts` — Data hook (preserved)
  - `frontend/src/types/index.ts:HistoryItem` — Type: `{ name, type, size, created, url? }`
  - `frontend/src/components/shared/MarkdownRenderer.tsx` — Shared renderer (from T5)

  **WHY Each Reference Matters**:
  - HistoryPage's current List.Item layout is too sparse. Grid layout with filter bar is the main UX improvement here.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: HistoryPage renders grid layout
    Tool: Bash (vitest)
    Steps:
      1. Mock useWorkflowHistory to return 3 items
      2. Render HistoryPage
      3. Assert: grid container with Tailwind grid classes
      4. Assert: 3 cards rendered
    Expected Result: Grid layout with items
    Evidence: .sisyphus/evidence/task-13-grid-test.txt

  Scenario: Filter bar works
    Tool: Bash (vitest)
    Steps:
      1. Render HistoryPage with mixed items (image, document, video)
      2. Click "Documents" filter
      3. Assert: only document card visible
    Expected Result: Filter correctly hides/shows items
    Evidence: .sisyphus/evidence/task-13-filter-test.txt

  Scenario: No Ant Design imports
    Tool: Bash (grep)
    Steps:
      1. `grep -r "from 'antd'" frontend/src/pages/HistoryPage.tsx frontend/src/components/PreviewModal.tsx`
      2. Assert: empty
    Expected Result: Clean
    Evidence: .sisyphus/evidence/task-13-no-antd.txt

  Scenario: Build succeeds
    Tool: Bash
    Steps:
      1. `cd frontend && npm run build`
    Expected Result: Clean build
    Evidence: .sisyphus/evidence/task-13-build.txt
  ```

  **Commit**: YES
  - Message: `refactor: rewrite HistoryPage and PreviewModal`
  - Files: pages/HistoryPage.tsx, components/PreviewModal.tsx
  - Pre-commit: `cd frontend && npm run build`

- [ ] 14. **Unify Theme System and Rewrite Remaining Common Components**

  **What to do**:
  - Rewrite `frontend/src/contexts/ThemeContext.tsx`:
    - Keep: `.dark` class toggle on `<html>`, localStorage persistence
    - Remove: `data-theme` attribute (not needed with Tailwind)
    - Add: System preference detection (`window.matchMedia('(prefers-color-scheme: dark)')`)
    - Add: FOUC prevention — set class in `<script>` in `index.html` before React loads
    - Default to dark mode (as user requested)
  - Rewrite `frontend/src/components/common/WorkflowStatusIndicator.tsx`:
    - Remove Ant Design `Badge`, `Tooltip`, `Typography`
    - Use Tailwind-styled status dot + custom tooltip (Radix UI Tooltip)
    - Keep same status logic: idle/running/completed/error/stopped
  - Delete dead CSS files that are no longer imported:
    - `components/common/EmptyView.css`
    - `components/common/StreamContentItem.css`
    - `components/common/WorkflowExecutionTracker.css`
  - Rewrite `frontend/src/components/common/EmptyView.tsx`:
    - Replace external CSS file with Tailwind classes
    - Keep Lucide Clock icon
  - Rewrite `frontend/src/components/common/StreamContentItem.tsx`:
    - Remove Ant Design `Tag` usage
    - Replace inline styles with Tailwind classes
    - Keep react-syntax-highlighter integration
    - Move CSS from `.css` file to Tailwind classes
  - Rewrite `frontend/src/components/common/WorkflowExecutionTracker.tsx`:
    - Since React Flow is removed, this component becomes a simple "step list" view
    - OR delete entirely if timeline is sufficient
    - Remove React Flow imports and references
  - Update `frontend/index.html`:
    - Add FOUC prevention script: `<script>if(!localStorage.theme||localStorage.theme==='dark')document.documentElement.classList.add('dark')</script>`
    - Add Google Fonts link for Fira Code + Fira Sans

  **Must NOT do**:
  - Do NOT change `WorkflowTimeline.tsx` or `WorkflowTimeline.css` — these already use zero Ant Design
  - Do NOT add animation libraries

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Multiple small components to rewrite, theme system unification
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with T13, T15)
  - **Parallel Group**: Wave 4
  - **Blocks**: T15
  - **Blocked By**: T12 (App.tsx must be done first)

  **References**:

  **Pattern References**:
  - `frontend/src/contexts/ThemeContext.tsx` — CURRENT theme context (keep .dark class toggle)
  - `frontend/src/components/common/WorkflowStatusIndicator.tsx` — Status indicator to rewrite
  - `frontend/src/components/common/StreamContentItem.tsx` — Stream content with react-syntax-highlighter
  - `frontend/src/components/common/WorkflowExecutionTracker.tsx` — Currently wraps React Flow (being removed)

  **API/Type References**:
  - `frontend/src/types/index.ts:WorkflowStatusType`, `StepStatus` — Status types

  **WHY Each Reference Matters**:
  - ThemeContext unification is critical — currently has dual system. WorkflowStatusIndicator is used by all panels.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: ThemeContext defaults to dark
    Tool: Bash (vitest)
    Steps:
      1. Import useTheme from ThemeContext
      2. Render without localStorage
      3. Assert: mode === 'dark'
    Expected Result: Dark mode is default
    Evidence: .sisyphus/evidence/task-14-dark-default.txt

  Scenario: ThemeContext toggles correctly
    Tool: Bash (vitest)
    Steps:
      1. Render ThemeProvider
      2. Call toggleTheme()
      3. Assert: mode switched to 'light', .dark class removed
    Expected Result: Toggle works
    Evidence: .sisyphus/evidence/task-14-theme-toggle.txt

  Scenario: No Ant Design in common components
    Tool: Bash (grep)
    Steps:
      1. `grep -r "from 'antd'" frontend/src/components/common/ --include="*.tsx"`
      2. Assert: empty (except WorkflowTimeline.tsx which never had antd)
    Expected Result: Clean
    Evidence: .sisyphus/evidence/task-14-no-antd.txt

  Scenario: Build succeeds
    Tool: Bash
    Steps:
      1. `cd frontend && npm run build`
    Expected Result: Clean build
    Evidence: .sisyphus/evidence/task-14-build.txt
  ```

  **Commit**: YES
  - Message: `refactor: unify theme system and common components`
  - Files: contexts/ThemeContext.tsx, components/common/*.tsx, index.html
  - Pre-commit: `cd frontend && npm run build`

- [ ] 15. **Remove Ant Design and React Flow Dependencies**

  **What to do**:
  - Remove from `package.json`:
    - `antd` and all `@ant-design/*` packages
    - `@xyflow/react`
    - Any Ant Design locale packages
  - Run `npm install` to update lock file and remove packages
  - Delete ALL React Flow related files:
    - `components/common/workflowViews/ReactFlowNodeGraphView.tsx`
    - `components/common/workflowViews/ReactFlowCustomNode.tsx`
    - `components/common/workflowViews/ReactFlowCustomEdge.tsx` (if exists)
    - `components/common/workflowViews/ReactFlowCustomNode.css`
    - `components/common/workflowViews/ReactFlowCustomEdge.css`
    - `components/common/workflowViews/ReactFlowNodeGraphView.css`
    - `components/common/workflowNodes/WorkflowNodeCard.tsx`
    - `components/common/workflowNodes/WorkflowNodeCard.css`
    - `components/common/WorkflowExecutionTracker.css` (if not already deleted)
  - Delete `config/workflowGraphs.ts` — graph definitions no longer needed
  - Run full verification: build + grep for any remaining antd imports

  **Must NOT do**:
  - Do NOT remove any package that is still imported (verify first)
  - Do NOT remove `react-markdown`, `remark-math`, `rehype-katex`, `rehype-raw`, `katex`
  - Do NOT remove `axios`, `dayjs`, `react-syntax-highlighter`, `lucide-react`
  - Do NOT remove `react-router-dom`

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Package removal and file deletion
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO (depends on T12 and T14 being complete)
  - **Parallel Group**: Wave 4 (last in wave)
  - **Blocks**: T16
  - **Blocked By**: T12, T14

  **References**:

  **Verification References**:
  - Run before deleting: `grep -r "from 'antd'" frontend/src/ --include="*.tsx" --include="*.ts" | grep -v node_modules`
  - Run before deleting: `grep -r "from '@ant-design/icons'" frontend/src/ --include="*.tsx" --include="*.ts" | grep -v node_modules`
  - Run before deleting: `grep -r "from '@xyflow/react'" frontend/src/ --include="*.tsx" --include="*.ts" | grep -v node_modules`
  - ALL must return empty before proceeding with package removal

  **WHY Each Reference Matters**:
  - These grep commands are the safety check — if any file still imports Ant Design, removing it will break the build.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Zero Ant Design imports in source
    Tool: Bash (grep)
    Preconditions: All components rewritten
    Steps:
      1. `grep -r "from 'antd'" frontend/src/ --include="*.tsx" --include="*.ts" | grep -v node_modules | grep -v __tests__`
      2. `grep -r "from '@ant-design/icons'" frontend/src/ --include="*.tsx" --include="*.ts" | grep -v node_modules | grep -v __tests__`
      3. Assert: both return empty
    Expected Result: Zero Ant Design references
    Failure Indicators: Any matches — DO NOT PROCEED, fix the file first
    Evidence: .sisyphus/evidence/task-15-zero-antd.txt

  Scenario: Zero React Flow imports in source
    Tool: Bash (grep)
    Steps:
      1. `grep -r "from '@xyflow/react'" frontend/src/ --include="*.tsx" --include="*.ts" | grep -v node_modules`
      2. Assert: empty
    Expected Result: Zero React Flow references
    Evidence: .sisyphus/evidence/task-15-zero-reactflow.txt

  Scenario: Build succeeds without Ant Design
    Tool: Bash
    Steps:
      1. `cd frontend && npm run build 2>&1 | tail -10`
    Expected Result: "✓ built in Xms" — zero errors
    Failure Indicators: "Cannot find module 'antd'" or similar
    Evidence: .sisyphus/evidence/task-15-build.txt

  Scenario: Bundle size decreased
    Tool: Bash
    Steps:
      1. `cd frontend && npm run build && du -sh dist/assets/`
      2. Compare with original build size
    Expected Result: Total JS < 500KB (Ant Design was ~300KB)
    Evidence: .sisyphus/evidence/task-15-bundle-size.txt
  ```

  **Commit**: YES
  - Message: `chore: remove Ant Design and React Flow dependencies`
  - Files: package.json, deleted files, config/workflowGraphs.ts
  - Pre-commit: `cd frontend && npm run build`

- [ ] 16. **End-to-End Integration Verification**

  **What to do**:
  - Write integration smoke tests for critical user flows:
    1. App loads → sidebar visible → default to drawing panel
    2. Click sidebar "document" → DocumentPanel renders
    3. Click sidebar "history" → HistoryPage renders with grid
    4. Theme toggle → dark/light switch works
    5. Model selector → dropdown opens, options visible
  - Run full build verification
  - Run all tests: `npx vitest run`
  - Verify no console errors on load (if possible via test)
  - Check for any remaining `.css` files that are orphaned (no imports)
  - Verify `index.html` has FOUC prevention script and font imports

  **Must NOT do**:
  - Do NOT fix bugs found — create a follow-up list for T17
  - Do NOT add new features

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Comprehensive integration testing across all components
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 5
  - **Blocks**: T17
  - **Blocked By**: T9, T10, T11, T13, T15 (all implementation done)

  **References**:

  **Verification References**:
  - `frontend/src/App.tsx` — Root component to test
  - `frontend/src/pages/HomePage.tsx` — Main page
  - `frontend/src/pages/HistoryPage.tsx` — History page
  - `frontend/src/components/layout/AppLayout.tsx` — Layout shell

  **WHY Each Reference Matters**:
  - Integration tests verify the full component tree works together after the migration.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Full integration suite passes
    Tool: Bash (vitest)
    Steps:
      1. `cd frontend && npx vitest run 2>&1 | tail -20`
      2. Assert: "Tests X passed" with zero failures
    Expected Result: All integration tests pass
    Evidence: .sisyphus/evidence/task-16-integration-tests.txt

  Scenario: Production build succeeds
    Tool: Bash
    Steps:
      1. `cd frontend && npm run build`
      2. Assert: clean build, no warnings
    Expected Result: Build OK
    Evidence: .sisyphus/evidence/task-16-prod-build.txt

  Scenario: No orphaned CSS files
    Tool: Bash
    Steps:
      1. For each .css file in frontend/src/: grep for its import across .tsx/.ts files
      2. Assert: every .css file is imported exactly once
    Expected Result: No orphaned stylesheets
    Evidence: .sisyphus/evidence/task-16-css-check.txt
  ```

  **Commit**: YES
  - Message: `test: integration verification`
  - Files: tests/integration/*.test.tsx
  - Pre-commit: `cd frontend && npm run build && npx vitest run`

- [ ] 17. **Final Cleanup and Bundle Optimization**

  **What to do**:
  - Remove any remaining dead CSS:
    - Check for unused Tailwind classes (manual review)
    - Remove any `.css` files still referencing `.ant-*`
  - Clean up `frontend/index.html`:
    - Remove any Ant Design CDN links if present
    - Ensure Google Fonts (Fira Code + Fira Sans) loaded
    - Ensure FOUC prevention script present
  - Verify `tailwind.config.ts` or CSS `@theme` has correct design tokens
  - Run final bundle size check
  - Run `npm run lint` and fix any issues
  - Remove any commented-out code or TODO comments left during rewrite
  - Final `npm run build` verification

  **Must NOT do**:
  - Do NOT add new features
  - Do NOT change any business logic

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Multi-file cleanup and verification
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 5 (after T16)
  - **Blocks**: FINAL wave
  - **Blocked By**: T16

  **References**:

  **Verification References**:
  - Run: `cd frontend && npm run build && npm run lint`
  - Run: `grep -r "TODO\|FIXME\|HACK" frontend/src/ --include="*.tsx" --include="*.ts" | grep -v node_modules`
  - Run: `grep -r "console\.log" frontend/src/ --include="*.tsx" --include="*.ts" | grep -v node_modules | grep -v __tests__`

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Clean lint output
    Tool: Bash
    Steps:
      1. `cd frontend && npm run lint 2>&1`
      2. Assert: zero errors (warnings OK)
    Expected Result: Clean lint
    Evidence: .sisyphus/evidence/task-17-lint.txt

  Scenario: No TODO/FIXME/HACK comments
    Tool: Bash (grep)
    Steps:
      1. `grep -r "TODO\|FIXME\|HACK" frontend/src/ --include="*.tsx" --include="*.ts" | grep -v node_modules`
      2. Assert: empty (or only pre-existing ones documented)
    Expected Result: No developer debt markers
    Evidence: .sisyphus/evidence/task-17-no-todo.txt

  Scenario: Final production build
    Tool: Bash
    Steps:
      1. `cd frontend && npm run build 2>&1`
      2. `du -sh dist/assets/`
      3. Assert: build succeeds, total < 500KB
    Expected Result: Clean build, reasonable bundle size
    Evidence: .sisyphus/evidence/task-17-final-build.txt
  ```

  **Commit**: YES
  - Message: `chore: final cleanup and bundle optimization`
  - Files: index.html, index.css, any remaining files
  - Pre-commit: `cd frontend && npm run build && npm run lint`

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, grep import). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in .sisyphus/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `npm run build` + `npm run lint`. Review all changed files for: `as any`/`@ts-ignore`, empty catches, console.log in prod, commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, generic names. Verify Tailwind classes are used (no inline styles except dynamic values). Check `@theme` variables are used consistently.
  Output: `Build [PASS/FAIL] | Lint [PASS/FAIL] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real Manual QA** — `unspecified-high` (+ `playwright` skill)
  Start from clean state (`npm run dev`). Execute EVERY QA scenario from EVERY task — follow exact steps, capture evidence. Test cross-task integration (workflow start → timeline → result display → theme toggle). Test edge cases: WebSocket disconnected, API error, empty history. Save to `.sisyphus/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff. Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance. Verify preserved files (services, hooks, contexts, types) are UNTOUCHED. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Preserved [N/N untouched] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

| Commit | Message | Files | Pre-commit |
|--------|---------|-------|------------|
| 1 | `chore: remove dead code and unused dependencies` | 10 deleted files, package.json | `npm run build` |
| 2 | `chore: install and configure Tailwind CSS v4` | index.css, vite.config.ts, package.json | `npm run build` |
| 3 | `chore: install Radix UI, sonner, vitest` | package.json, vitest.config.ts | `npm run build` |
| 4 | `feat: add toast abstraction layer` | services/toast.ts | `npm run build` |
| 5 | `feat: add MarkdownRenderer shared component` | components/shared/MarkdownRenderer.tsx | `npm run build` |
| 6 | `feat: add ModelSelector with Radix UI` | components/shared/ModelSelector.tsx | `npm run build` |
| 7 | `feat: add IDE layout (Sidebar + Header + AppLayout)` | components/layout/*.tsx | `npm run build` |
| 8 | `feat: add WorkflowPanel base component` | components/shared/WorkflowPanel.tsx | `npm run build` |
| 9 | `refactor: rewrite HomePage and DrawingPanel with Tailwind` | pages/HomePage.tsx, components/drawing/ | `npm run build` |
| 10 | `refactor: rewrite DocumentPanel with Tailwind` | components/document/ | `npm run build` |
| 11 | `refactor: rewrite ManimPanel with Tailwind` | components/manim/ | `npm run build` |
| 12 | `refactor: rewrite App.tsx with new layout` | App.tsx, App.css (delete) | `npm run build` |
| 13 | `refactor: rewrite HistoryPage and PreviewModal` | pages/HistoryPage.tsx, PreviewModal.tsx | `npm run build` |
| 14 | `refactor: unify theme system and common components` | contexts/ThemeContext.tsx, components/common/ | `npm run build` |
| 15 | `chore: remove Ant Design and React Flow dependencies` | package.json | `npm run build` |
| 16 | `test: integration verification` | tests/ | `npm run build && npx vitest run` |
| 17 | `chore: final cleanup and bundle optimization` | index.html, CSS files | `npm run build` |

---

## Success Criteria

### Verification Commands
```bash
# Build succeeds
cd frontend && npm run build
# Expected: "✓ built in Xms", zero errors

# Zero Ant Design imports
grep -r "from 'antd'" frontend/src/
# Expected: empty output

grep -r "from '@ant-design/icons'" frontend/src/
# Expected: empty output

# Zero React Flow imports
grep -r "from '@xyflow/react'" frontend/src/
# Expected: empty output

# Zero old CSS overrides
grep -r ".ant-" frontend/src/
# Expected: empty output

# Bundle size check
cd frontend && npm run build && du -sh dist/assets/
# Expected: < 500KB total JS

# Theme system works
grep -r "@custom-variant dark" frontend/src/index.css
# Expected: present
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] All preserved files untouched (services, hooks, contexts, types)
- [ ] `npm run build` passes
- [ ] No Ant Design imports
- [ ] No React Flow imports
- [ ] Dark mode default, light mode switchable
- [ ] All 3 workflow panels functional
- [ ] History page with grid + filter
- [ ] WebSocket real-time updates work
- [ ] Markdown + KaTeX rendering works
