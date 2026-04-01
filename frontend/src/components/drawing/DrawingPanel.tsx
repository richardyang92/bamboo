import * as Tabs from '@radix-ui/react-tabs';
import WorkflowPanel from '../shared/WorkflowPanel';
import * as api from '../../services/api';
import type { WorkflowResult } from '../../types';

function renderDrawingResult(result: WorkflowResult) {
  if (!result.image_url) {
    return (
      <div className="flex items-center justify-center h-full text-[var(--color-text-muted)]">
        无生成结果
      </div>
    );
  }

  return (
    <Tabs.Root defaultValue="image" className="h-full flex flex-col">
      <Tabs.List className="flex border-b border-[var(--color-border)]">
        <Tabs.Trigger
          value="image"
          className="px-3 py-1.5 text-sm text-[var(--color-text-secondary)] data-[state=active]:text-[var(--color-text-primary)] data-[state=active]:border-b-2 data-[state=active]:border-[var(--color-accent)]"
        >
          图片
        </Tabs.Trigger>
        <Tabs.Trigger
          value="code"
          className="px-3 py-1.5 text-sm text-[var(--color-text-secondary)] data-[state=active]:text-[var(--color-text-primary)] data-[state=active]:border-b-2 data-[state=active]:border-[var(--color-accent)]"
        >
          代码
        </Tabs.Trigger>
      </Tabs.List>

      <Tabs.Content value="image" className="pt-3 flex-1 overflow-auto">
        <div className="flex items-center justify-center h-full">
          <img
            src={result.image_url}
            alt="生成的图表"
            className="max-w-full max-h-full object-contain"
          />
        </div>
      </Tabs.Content>

      <Tabs.Content value="code" className="pt-3 flex-1 overflow-auto">
        <pre className="bg-[var(--color-bg-dark)] p-4 rounded-md overflow-auto font-mono text-sm text-[var(--color-text-primary)]">
          {result.generated_code || '暂无代码'}
        </pre>
      </Tabs.Content>
    </Tabs.Root>
  );
}

function DrawingPanel() {
  return (
    <WorkflowPanel
      workflowType="drawing"
      apiStart={api.startDrawingWorkflow}
      apiStop={api.stopDrawingWorkflow}
      apiClear={api.clearDrawingHistory}
      placeholder="请描述你想要绘制的图表，例如：绘制一个正弦函数图像"
      startLabel="开始生成"
      runningLabel="生成中..."
      renderResult={renderDrawingResult}
    />
  );
}

export default DrawingPanel;
