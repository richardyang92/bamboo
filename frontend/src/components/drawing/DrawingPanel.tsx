import * as Tabs from '@radix-ui/react-tabs';
import { Download } from 'lucide-react';
import WorkflowPanel from '../shared/WorkflowPanel';
import * as api from '../../services/api';
import type { WorkflowResult } from '../../types';

function renderDrawingResult(result: WorkflowResult) {
  return (
    <Tabs.Root defaultValue="image" className="h-full flex flex-col">
      <Tabs.List className="bg-white/5 rounded-full p-1 inline-flex w-fit">
        <Tabs.Trigger
          value="image"
          className="px-4 py-1.5 text-sm font-medium transition-all duration-200 rounded-full
                     data-[state=inactive]:text-slate-400 data-[state=inactive]:hover:text-slate-300 data-[state=inactive]:hover:bg-white/5
                     data-[state=active]:bg-[#06b6d4] data-[state=active]:text-white data-[state=active]:shadow-md"
        >
          图片
        </Tabs.Trigger>
        <Tabs.Trigger
          value="code"
          className="px-4 py-1.5 text-sm font-medium transition-all duration-200 rounded-full
                     data-[state=inactive]:text-slate-400 data-[state=inactive]:hover:text-slate-300 data-[state=inactive]:hover:bg-white/5
                     data-[state=active]:bg-[#06b6d4] data-[state=active]:text-white data-[state=active]:shadow-md"
        >
          代码
        </Tabs.Trigger>
      </Tabs.List>

      <Tabs.Content value="image" className="pt-3 flex-1 overflow-auto">
        <div className="flex items-center justify-center h-full p-4">
          {!result.image_url ? (
            <div className="text-slate-400">无生成结果</div>
          ) : (
            <div className="relative group">
              <img
                src={result.image_url}
                alt="生成的图表"
                className="max-w-full max-h-full object-contain rounded-2xl shadow-2xl"
              />
              <div className="absolute inset-0 flex items-center justify-center bg-black/30 backdrop-blur-sm rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                <a
                  href={result.image_url}
                  download
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 backdrop-blur-md border border-white/20 text-white text-sm font-medium hover:bg-white/20 transition-colors cursor-pointer"
                >
                  <Download className="w-4 h-4" />
                  下载图片
                </a>
              </div>
            </div>
          )}
        </div>
      </Tabs.Content>

      <Tabs.Content value="code" className="pt-3 flex-1 overflow-auto">
        <pre className="p-4 rounded-xl overflow-auto font-mono text-sm text-slate-200" style={{ background: 'rgba(15, 23, 42, 0.9)' }}>
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