import { useState } from 'react';
import * as Select from '@radix-ui/react-select';
import * as Tabs from '@radix-ui/react-tabs';
import { ChevronDown, Check } from 'lucide-react';
import WorkflowPanel from '../shared/WorkflowPanel';
import * as api from '../../services/api';
import type { WorkflowResult } from '../../types';

const qualityOptions = [
  { value: 'low', label: '480p' },
  { value: 'medium', label: '720p' },
  { value: 'high', label: '1080p' },
  { value: '4k', label: '4K' },
];

function ManimPanel() {
  const [quality, setQuality] = useState<'low' | 'medium' | 'high' | '4k'>('medium');

  const qualitySelector = (
    <Select.Root value={quality} onValueChange={(v) => setQuality(v as any)}>
      <Select.Trigger className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs bg-[var(--color-bg-input)] border border-[var(--color-border)] text-[var(--color-text-secondary)]">
        <Select.Value />
        <Select.Icon><ChevronDown className="w-3 h-3" /></Select.Icon>
      </Select.Trigger>
      <Select.Portal>
        <Select.Content className="z-50 overflow-hidden rounded-md border border-[var(--color-border)] bg-[var(--color-bg-dark)] shadow-xl" position="popper" sideOffset={4}>
          <Select.Viewport className="p-1">
            {qualityOptions.map(opt => (
              <Select.Item key={opt.value} value={opt.value} className="relative flex items-center px-3 py-1.5 text-sm cursor-pointer text-[var(--color-text-primary)] rounded-md outline-none hover:bg-[var(--color-secondary)] data-[highlighted]:bg-[var(--color-secondary)]">
                <Select.ItemText>{opt.label}</Select.ItemText>
                <Select.ItemIndicator className="absolute right-2 text-[var(--color-accent)]"><Check className="w-3.5 h-3.5" /></Select.ItemIndicator>
              </Select.Item>
            ))}
          </Select.Viewport>
        </Select.Content>
      </Select.Portal>
    </Select.Root>
  );

  const renderManimResult = (result: WorkflowResult) => (
    <Tabs.Root defaultValue="video">
      <Tabs.List className="flex border-b border-[var(--color-border)]">
        <Tabs.Trigger value="video" className="px-3 py-1.5 text-sm text-[var(--color-text-secondary)] data-[state=active]:text-[var(--color-text-primary)] data-[state=active]:border-b-2 data-[state=active]:border-[var(--color-accent)]">视频</Tabs.Trigger>
        <Tabs.Trigger value="code" className="px-3 py-1.5 text-sm text-[var(--color-text-secondary)] data-[state=active]:text-[var(--color-text-primary)] data-[state=active]:border-b-2 data-[state=active]:border-[var(--color-accent)]">代码</Tabs.Trigger>
      </Tabs.List>
      <Tabs.Content value="video" className="pt-3">
        <div className="flex items-center justify-center min-h-0 h-full">
          <video
            src={result.video_url}
            controls
            className="max-w-full max-h-full rounded-md"
          />
        </div>
      </Tabs.Content>
      <Tabs.Content value="code" className="pt-3">
        <pre className="bg-[var(--color-bg-dark)] p-4 rounded-md overflow-auto font-mono text-sm text-[var(--color-text-primary)]">
          {result.generated_code}
        </pre>
      </Tabs.Content>
    </Tabs.Root>
  );

  return (
    <WorkflowPanel
      workflowType="manim"
      apiStart={(prompt, options) => api.startManimWorkflow(prompt, quality, options)}
      apiStop={api.stopManimWorkflow}
      apiClear={api.clearManimHistory}
      placeholder="请描述你想要的数学动画，例如：展示一个圆从左侧移动到右侧的动画"
      startLabel="开始生成"
      runningLabel="渲染中..."
      extraControls={qualitySelector}
      renderResult={renderManimResult}
    />
  );
}

export default ManimPanel;
