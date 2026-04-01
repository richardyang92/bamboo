import { useState } from 'react';
import { Send, Square, Trash2, Loader2 } from 'lucide-react';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useWorkflow } from '../../contexts/WorkflowContext';
import { showToast } from '../../services/toast';
import WorkflowTimeline from '../common/WorkflowTimeline';
import EmptyView from '../common/EmptyView';
import WorkflowStatusIndicator from '../common/WorkflowStatusIndicator';
import ResultPlaceholder from '../common/ResultPlaceholder';
import type { WorkflowType, WorkflowResult, LLMProvider } from '../../types';

export interface WorkflowPanelProps {
  workflowType: WorkflowType;
  apiStart: (prompt: string, options?: { provider?: LLMProvider; model?: string; enable_thinking?: boolean }) => Promise<any>;
  apiStop: () => Promise<any>;
  apiClear: () => Promise<any>;
  placeholder: string;
  startLabel: string;
  runningLabel: string;
  extraControls?: React.ReactNode;
  renderResult: (result: WorkflowResult) => React.ReactNode;
}

export default function WorkflowPanel({
  workflowType,
  apiStart,
  apiStop,
  apiClear,
  placeholder,
  startLabel,
  runningLabel,
  extraControls,
  renderResult,
}: WorkflowPanelProps) {
  const {
    status,
    steps,
    result,
    error,
    connectionState,
    currentNode,
    isStreaming,
    streamContent,
    reasoningContent,
  } = useWebSocket(workflowType);

  const { state: { modelConfig } } = useWorkflow();
  const [prompt, setPrompt] = useState('');

  const isRunning = status === 'running';
  const hasActiveSteps = steps.filter(s => s.status !== 'pending').length > 0;

  const handleStart = async () => {
    if (!prompt.trim()) {
      showToast.warning('请输入需求');
      return;
    }

    try {
      await apiStart(prompt, {
        provider: modelConfig.provider,
        model: modelConfig.model,
        enable_thinking: modelConfig.enable_thinking,
      });
      showToast.success('工作流已启动');
    } catch (err) {
      showToast.error(err instanceof Error ? err.message : '启动失败');
    }
  };

  const handleStop = async () => {
    try {
      await apiStop();
      showToast.success('工作流已停止');
    } catch (err) {
      showToast.error(err instanceof Error ? err.message : '停止失败');
    }
  };

  const handleClear = async () => {
    try {
      await apiClear();
      showToast.success('历史记录已清除');
    } catch (err) {
      showToast.error(err instanceof Error ? err.message : '清除失败');
    }
  };

  const resultType = workflowType === 'document_with_images' ? 'document' : workflowType;

  return (
    <div className="flex h-full">
      <div className="flex flex-col w-[400px] shrink-0 border-r border-[var(--color-border)]">
        <div className="p-3 border-b border-[var(--color-border)]">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-medium text-[var(--color-text-primary)]">
              {placeholder.includes('绘图') ? '绘图需求' : placeholder.includes('文档') ? '文档主题' : '动画需求'}
            </span>
            <WorkflowStatusIndicator
              workflowStatus={status}
              connectionState={connectionState}
              workflowType={workflowType}
            />
          </div>

          <textarea
            className="w-full bg-[var(--color-bg-input)] border border-[var(--color-border)] rounded-md p-2 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] resize-none focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)]"
            rows={4}
            placeholder={placeholder}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={isRunning}
          />

          <div className="flex items-center gap-2 mt-2">
            <button
              className="bg-[var(--color-accent)] hover:bg-[var(--color-accent)]/90 text-white px-3 py-1.5 rounded-md text-sm font-medium inline-flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
              onClick={handleStart}
              disabled={isRunning}
            >
              {isRunning ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  {runningLabel}
                </>
              ) : (
                <>
                  <Send size={14} />
                  {startLabel}
                </>
              )}
            </button>

            {isRunning && (
              <button
                className="bg-red-500/20 text-red-400 hover:bg-red-500/30 px-3 py-1.5 rounded-md text-sm inline-flex items-center gap-1.5"
                onClick={handleStop}
              >
                <Square size={14} />
                停止
              </button>
            )}

            <button
              className="text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-secondary)] px-3 py-1.5 rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              onClick={handleClear}
              disabled={isRunning}
            >
              <Trash2 size={14} className="inline mr-1" />
              清除历史
            </button>

            {extraControls}
          </div>
        </div>

        <div className="flex-1 overflow-auto p-3">
          {hasActiveSteps ? (
            <WorkflowTimeline
              steps={steps}
              streamContent={streamContent}
              reasoningContent={reasoningContent}
              currentNode={currentNode}
              isStreaming={isStreaming}
              workflowType={workflowType}
            />
          ) : (
            <EmptyView workflowType={workflowType} />
          )}
        </div>
      </div>

      <div className="flex-1 overflow-auto p-3">
        {result ? renderResult(result) : <ResultPlaceholder type={resultType} error={error} />}
      </div>
    </div>
  );
}
