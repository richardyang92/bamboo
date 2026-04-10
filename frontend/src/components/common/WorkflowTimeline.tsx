/**
 * WorkflowTimeline - 工作流执行时间线组件（CLI日志风格）
 * 模拟现代CLI工具（Vercel/npm/Docker）的输出风格 - 玻璃拟态增强版
 */
import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Loader2, AlertCircle, ChevronRight, ChevronDown, Brain, FileOutput, MinusCircle } from 'lucide-react';
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
  compact?: boolean;  // NEW: when true, show simplified dashboard view
}

/**
 * 格式化耗时 - 使用 JetBrains Mono 字体显示
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
  if (status === 'skipped') {
    return <MinusCircle className="cli-icon cli-icon-skipped" strokeWidth={2} size={14} />;
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

/**
 * 紧凑模式下的状态图标（小号）
 */
const CompactStepIcon: React.FC<{ status: StepStatus; isStreaming: boolean }> = ({ status, isStreaming }) => {
  if (status === 'completed') {
    return <CheckCircle2 className="text-emerald-400" strokeWidth={2} size={12} />;
  }
  if (status === 'error') {
    return <AlertCircle className="text-rose-400" strokeWidth={2} size={12} />;
  }
  if (status === 'skipped') {
    return <MinusCircle className="text-slate-500" strokeWidth={2} size={12} />;
  }
  if (status === 'running' || isStreaming) {
    return (
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
      >
        <Loader2 className="text-cyan-400" strokeWidth={2} size={12} />
      </motion.div>
    );
  }
  return <div className="w-3 h-3 rounded-full border-2 border-slate-600" />;
};

const getElapsedTime = (startTime?: string): string => {
  if (!startTime) return '';
  const start = new Date(startTime).getTime();
  const now = Date.now();
  const duration = now - start;
  if (duration < 1000) return `${duration}ms`;
  return `${(duration / 1000).toFixed(1)}s`;
};

const getStepDuration = (step: WorkflowStep): string => {
  if (step.status === 'completed' && step.timestamp && step.completed_at) {
    return formatDuration(step.timestamp, step.completed_at);
  }
  if (step.status === 'running' && step.timestamp) {
    return getElapsedTime(step.timestamp);
  }
  return '';
};

const CompactTimeline: React.FC<{
  steps: WorkflowStep[];
  currentNode: string | null;
  isStreaming: boolean;
}> = ({ steps, currentNode, isStreaming }) => {
  let lastActiveIndex = -1;
  steps.forEach((step, index) => {
    if (step.status !== 'pending') {
      lastActiveIndex = index;
    }
  });

  const displaySteps = steps.filter((step, index) => {
    if (step.status !== 'pending') return true;
    return index === lastActiveIndex + 1;
  });

  return (
    <div className="relative space-y-1">
      <div 
        className="absolute left-[17px] top-2 bottom-2 w-0.5 bg-slate-700/30"
        style={{ zIndex: 0 }}
      />
      
      {displaySteps.map((step, index) => {
        const isCurrent = step.step === currentNode && isStreaming;
        const isPending = step.status === 'pending';
        const duration = getStepDuration(step);
        
        return (
          <motion.div
            key={step.step}
            initial={{ opacity: 0, x: -5 }}
            animate={{ opacity: isPending ? 0.4 : 1, x: 0 }}
            transition={{ duration: 0.2, delay: index * 0.05 }}
            className={`
              relative flex items-center gap-2 px-2 py-1.5 rounded-lg transition-colors
              ${isCurrent ? 'bg-[rgba(6,182,212,0.08)]' : 'hover:bg-slate-800/30'}
            `}
            style={{ zIndex: 1 }}
          >
            <div className="flex-shrink-0 w-4 h-4 flex items-center justify-center">
              <CompactStepIcon status={step.status} isStreaming={isCurrent} />
            </div>
            
            <span 
              className={`
                text-xs flex-1 truncate
                ${isCurrent ? 'text-cyan-400 font-medium' : 
                  step.status === 'error' ? 'text-rose-400' : 'text-slate-300'}
              `}
            >
              {step.name}
            </span>
            
            {duration && (
              <span className="text-[11px] text-slate-500 font-mono tabular-nums flex-shrink-0">
                {duration}
              </span>
            )}
            
            {step.status === 'running' && (
              <motion.span
                className="w-1.5 h-1.5 rounded-full bg-cyan-400 flex-shrink-0"
                animate={{ opacity: [1, 0.3, 1] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              />
            )}
          </motion.div>
        );
      })}
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
  compact,
}) => {
  if (compact) {
    return (
      <CompactTimeline
        steps={steps}
        currentNode={currentNode}
        isStreaming={isStreaming}
      />
    );
  }

  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set());
  const [thinkingExpandedKeys, setThinkingExpandedKeys] = useState<Set<string>>(new Set());
  const prevRunningStepRef = useRef<string | null>(null);

  useEffect(() => {
    const runningStep = steps.find(s => s.status === 'running');
    if (runningStep && runningStep.step !== prevRunningStepRef.current) {
      prevRunningStepRef.current = runningStep.step;
    }
  }, [steps]);

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

        const isJustActivated = step.step === prevRunningStepRef.current && step.status === 'running';

        return (
          <motion.div
            key={step.step}
            className="cli-step"
            initial={isJustActivated ? { opacity: 0, x: -10 } : { opacity: 1, x: 0 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
          >
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

              {/* 耗时（已完成时显示） - JetBrains Mono tabular-nums */}
              {duration && <span className="cli-duration font-mono tabular-nums">({duration})</span>}

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
                {/* 错误信息 - Glass card with red tint */}
                {step.error && (
                  <div className="cli-error-message">
                    <AlertCircle size={12} strokeWidth={2} className="cli-error-icon" />
                    <span className="cli-error-text">{step.error}</span>
                  </div>
                )}

                {/* 思考过程 - Glass card with indigo/purple tint */}
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
          </motion.div>
        );
      })}
    </div>
  );
};

export default React.memo(WorkflowTimeline);
