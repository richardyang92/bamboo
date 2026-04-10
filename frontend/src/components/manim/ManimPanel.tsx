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
      <Select.Trigger className="inline-flex items-center gap-1 px-3 py-1.5 text-xs bg-white/5 backdrop-blur-sm border border-white/10 text-slate-300 rounded-lg hover:bg-white/10 transition-colors">
        <Select.Value />
        <Select.Icon><ChevronDown className="w-3 h-3" /></Select.Icon>
      </Select.Trigger>
      <Select.Portal>
        <Select.Content className="z-50 overflow-hidden rounded-xl border border-white/10 bg-slate-900/95 backdrop-blur-xl shadow-xl" position="popper" sideOffset={4}>
          <Select.Viewport className="p-1">
            {qualityOptions.map(opt => (
              <Select.Item key={opt.value} value={opt.value} className="relative flex items-center px-3 py-1.5 text-sm cursor-pointer text-slate-200 rounded-lg outline-none hover:bg-white/5 data-[highlighted]:bg-white/5">
                <Select.ItemText>{opt.label}</Select.ItemText>
                <Select.ItemIndicator className="absolute right-2 text-[#06b6d4]"><Check className="w-3.5 h-3.5" /></Select.ItemIndicator>
              </Select.Item>
            ))}
          </Select.Viewport>
        </Select.Content>
      </Select.Portal>
    </Select.Root>
  );

  const renderManimResult = (result: WorkflowResult) => (
    <Tabs.Root defaultValue="video" className="h-full flex flex-col">
      <Tabs.List className="bg-white/5 rounded-full p-1 inline-flex w-fit">
        <Tabs.Trigger value="video" className="px-4 py-1.5 text-sm font-medium transition-all duration-200 rounded-full
                       data-[state=inactive]:text-slate-400 data-[state=inactive]:hover:text-slate-300 data-[state=inactive]:hover:bg-white/5
                       data-[state=active]:bg-[#06b6d4] data-[state=active]:text-white data-[state=active]:shadow-md">视频</Tabs.Trigger>
        <Tabs.Trigger value="code" className="px-4 py-1.5 text-sm font-medium transition-all duration-200 rounded-full
                       data-[state=inactive]:text-slate-400 data-[state=inactive]:hover:text-slate-300 data-[state=inactive]:hover:bg-white/5
                       data-[state=active]:bg-[#06b6d4] data-[state=active]:text-white data-[state=active]:shadow-md">代码</Tabs.Trigger>
      </Tabs.List>
      <Tabs.Content value="video" className="pt-3 flex-1 overflow-auto">
        <div className="flex items-center justify-center h-full">
          <video
            src={result.video_url}
            controls
            className="max-w-full max-h-full rounded-2xl shadow-2xl"
            style={{ background: 'rgba(15, 23, 42, 0.9)' }}
          />
        </div>
      </Tabs.Content>
      <Tabs.Content value="code" className="pt-3 flex-1 overflow-auto">
        <pre className="p-4 rounded-xl overflow-auto font-mono text-sm text-slate-200" style={{ background: 'rgba(15, 23, 42, 0.9)' }}>
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