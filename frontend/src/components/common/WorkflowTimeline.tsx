/**
 * WorkflowTimeline - 工作流执行时间线组件（CLI日志风格）
 * 模拟现代CLI工具（Vercel/npm/Docker）的输出风格
 */
import React, { useState, useEffect } from 'react';
import { CheckCircle2, Loader2, AlertCircle, ChevronRight, ChevronDown, Brain, FileOutput } from 'lucide-react';
import type { WorkflowStep, WorkflowType, StepStatus } from '../../types';
import StreamContentItem from './StreamContentItem';
import './WorkflowTimeline.css';

interface WorkflowTimelineProps {
  steps: WorkflowStep[];
  streamContent: Map<string, string>;
  reasoningContent: Map<string, string>;
  currentNode: string | null;
  isStreaming: boolean;
  workflowType: WorkflowType;
}

/**
 * 格式化耗时
 */
const formatDuration = (startTime?: string, endTime?: string): string => {
  if (!startTime || !endTime) return '';
  const start = new Date(startTime).getTime();
  const end = new Date(endTime).getTime();
  const duration = end - start;
  if (duration < 1000) return `${duration}ms`;
  return `${(duration / 1000).toFixed(2)}s`;
};

/**
 * 格式化时间戳
 */
const formatTime = (timestamp?: string): string => {
  if (!timestamp) return '';
  return new Date(timestamp).toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

/**
 * 获取步骤图标
 */
const StepIcon: React.FC<{ status: StepStatus; isStreaming: boolean }> = ({ status, isStreaming }) => {
  if (status === 'completed') {
    return <CheckCircle2 className="cli-icon cli-icon-success" strokeWidth={2} size={14} />;
  }
  if (status === 'error') {
    return <AlertCircle className="cli-icon cli-icon-error" strokeWidth={2} size={14} />;
  }
  if (status === 'running' || isStreaming) {
    return <Loader2 className="cli-icon cli-icon-spinning cli-icon-running" strokeWidth={2} size={14} />;
  }
  return <div className="cli-icon cli-icon-pending" />;
};

/**
 * 思考过程展开区域
 */
const ThinkingSection: React.FC<{
  reasoning: string;
  isExpanded: boolean;
  onToggle: () => void;
}> = ({ reasoning, isExpanded, onToggle }) => {
  if (!reasoning) return null;

  return (
    <div className="cli-section">
      <button className="cli-section-header" onClick={onToggle}>
        {isExpanded ? (
          <ChevronDown size={12} className="cli-chevron" />
        ) : (
          <ChevronRight size={12} className="cli-chevron" />
        )}
        <Brain size={12} className="cli-section-icon" />
        <span className="cli-section-label">Thinking</span>
      </button>
      {isExpanded && (
        <div className="cli-section-content cli-thinking-content">
          <pre className="cli-text">{reasoning}</pre>
        </div>
      )}
    </div>
  );
};

/**
 * 输出内容区域
 */
const OutputSection: React.FC<{
  step: WorkflowStep;
  content: string;
  isStreaming: boolean;
  workflowType: WorkflowType;
}> = ({ step, content, isStreaming, workflowType }) => {
  if (!content) return null;

  return (
    <div className="cli-section">
      <div className="cli-section-header cli-section-header-static">
        <ChevronRight size={12} className="cli-chevron cli-chevron-fixed" />
        <FileOutput size={12} className="cli-section-icon" />
        <span className="cli-section-label">Output</span>
        {isStreaming && <span className="cli-cursor" />}
      </div>
      <div className="cli-section-content">
        <StreamContentItem
          step={step}
          content={content}
          reasoningContent=""
          isActive={isStreaming}
          isStreaming={isStreaming}
          workflowType={workflowType}
        />
      </div>
    </div>
  );
};

const WorkflowTimeline: React.FC<WorkflowTimelineProps> = ({
  steps,
  streamContent,
  reasoningContent,
  currentNode,
  isStreaming,
  workflowType,
}) => {
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set());
  const [thinkingExpandedKeys, setThinkingExpandedKeys] = useState<Set<string>>(new Set());

  // 自动展开当前正在流式输出的节点
  useEffect(() => {
    if (currentNode && isStreaming) {
      setExpandedKeys(prev => new Set(prev).add(currentNode));
    }
  }, [currentNode, isStreaming]);

  /**
   * 切换步骤展开状态
   */
  const handleToggleExpand = (stepId: string) => {
    setExpandedKeys(prev => {
      const next = new Set(prev);
      if (next.has(stepId)) {
        next.delete(stepId);
      } else {
        next.add(stepId);
      }
      return next;
    });
  };

  /**
   * 切换思考过程展开状态
   */
  const handleToggleThinking = (stepId: string) => {
    setThinkingExpandedKeys(prev => {
      const next = new Set(prev);
      if (next.has(stepId)) {
        next.delete(stepId);
      } else {
        next.add(stepId);
      }
      return next;
    });
  };

  // 过滤出已开始执行的步骤
  const activeSteps = steps.filter(step => step.status !== 'pending');

  return (
    <div className="cli-timeline">
      {activeSteps.map((step) => {
        const content = streamContent.get(step.step) || '';
        const reasoning = reasoningContent.get(step.step) || '';
        const hasContent = !!content || !!reasoning;
        const isExpanded = expandedKeys.has(step.step);
        const isThinkingExpanded = thinkingExpandedKeys.has(step.step);
        const isCurrent = step.step === currentNode && isStreaming;
        const duration = formatDuration(step.timestamp, step.completed_at);
        const timeStr = formatTime(step.timestamp);

        return (
          <div key={step.step} className="cli-step">
            {/* 步骤头部行 */}
            <div className="cli-step-header" onClick={() => hasContent && handleToggleExpand(step.step)}>
              {/* 时间戳 */}
              <span className="cli-time">[{timeStr}]</span>

              {/* 状态图标 */}
              <div className="cli-status-wrapper">
                <StepIcon status={step.status} isStreaming={isCurrent} />
              </div>

              {/* 步骤名称 */}
              <span className="cli-step-name">{step.name}</span>

              {/* 耗时（已完成时显示） */}
              {duration && <span className="cli-duration">({duration})</span>}

              {/* 展开指示器 */}
              {hasContent && (
                <span className="cli-expand-hint">
                  {isExpanded ? '▼' : '▶'}
                </span>
              )}
            </div>

            {/* 可展开的详细内容 */}
            {isExpanded && hasContent && (
              <div className="cli-step-details">
                {/* 错误信息 */}
                {step.error && (
                  <div className="cli-error-message">
                    <AlertCircle size={12} strokeWidth={2} className="cli-error-icon" />
                    <span className="cli-error-text">{step.error}</span>
                  </div>
                )}

                {/* 思考过程 */}
                <ThinkingSection
                  reasoning={reasoning}
                  isExpanded={isThinkingExpanded}
                  onToggle={() => handleToggleThinking(step.step)}
                />

                {/* 输出内容 */}
                <OutputSection
                  step={step}
                  content={content}
                  isStreaming={isCurrent}
                  workflowType={workflowType}
                />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default React.memo(WorkflowTimeline);
