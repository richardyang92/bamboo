/**
 * ProcessingView - 工作流处理视图组件（右侧面板）
 * 显示工作流执行过程中的各个步骤及其内容
 */
import React, { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, Loader2, ChevronRight, ChevronDown, Brain, AlertCircle, Clock } from 'lucide-react';
import type { WorkflowStep, WorkflowType, StepStatus } from '../../types';
import CodeBlock from './CodeBlock';

// ============================================================================
// Types
// ============================================================================

interface ProcessingViewProps {
  steps: WorkflowStep[];
  streamContent: Map<string, string>;
  reasoningContent: Map<string, string>;
  currentNode: string | null;
  isStreaming: boolean;
  workflowType: WorkflowType;
}

interface StepCardProps {
  step: WorkflowStep;
  content: string;
  reasoning: string;
  isActive: boolean;
  isStreaming: boolean;
  workflowType: WorkflowType;
  isExpanded: boolean;
  onToggleExpand: () => void;
  isReasoningExpanded: boolean;
  onToggleReasoning: () => void;
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * 格式化耗时
 */
const formatDuration = (startTime?: string, endTime?: string): string => {
  if (!startTime || !endTime) return '';
  const duration = new Date(endTime).getTime() - new Date(startTime).getTime();
  if (duration < 1000) return `${duration}ms`;
  return `${(duration / 1000).toFixed(1)}s`;
};

/**
 * 获取状态颜色类名
 */
const getStatusColor = (status: StepStatus): string => {
  switch (status) {
    case 'running':
      return 'text-cyan-400';
    case 'completed':
      return 'text-emerald-400';
    case 'error':
      return 'text-rose-400';
    case 'skipped':
      return 'text-amber-400';
    default:
      return 'text-slate-400';
  }
};

/**
 * 获取状态图标
 */
const StatusIcon: React.FC<{ status: StepStatus }> = ({ status }) => {
  const colorClass = getStatusColor(status);

  switch (status) {
    case 'running':
      return <Loader2 className={`w-4 h-4 ${colorClass} animate-spin`} />;
    case 'completed':
      return <CheckCircle2 className={`w-4 h-4 ${colorClass}`} />;
    case 'error':
      return <AlertCircle className={`w-4 h-4 ${colorClass}`} />;
    case 'skipped':
      return <Clock className={`w-4 h-4 ${colorClass}`} />;
    default:
      return <div className={`w-2 h-2 rounded-full ${colorClass.replace('text-', 'bg-')}`} />;
  }
};

/**
 * 检测语言
 */
const detectLanguage = (workflowType: WorkflowType): string => {
  if (workflowType === 'drawing' || workflowType === 'manim') {
    return 'python';
  }
  return 'text';
};

// ============================================================================
// StepCard Component
// ============================================================================

const StepCard: React.FC<StepCardProps> = ({
  step,
  content,
  reasoning,
  isActive,
  isStreaming,
  workflowType,
  isExpanded,
  onToggleExpand,
  isReasoningExpanded,
  onToggleReasoning,
}) => {
  const contentRef = useRef<HTMLDivElement>(null);
  const hasContent = !!content || !!reasoning || !!step.error;
  const duration = formatDuration(step.timestamp, step.completed_at);
  const language = detectLanguage(workflowType);

  // 自动滚动到内容底部
  useEffect(() => {
    if (contentRef.current && isActive && isStreaming) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, [content, reasoning, isActive, isStreaming]);

  // 渲染内容区域
  const renderContent = () => {
    if (!content) return null;

    // drawing / manim: 显示代码
    if (workflowType === 'drawing' || workflowType === 'manim') {
      return (
        <div className="mt-3">
          <CodeBlock code={content} language={language} showLineNumbers={true} />
        </div>
      );
    }

    // document_with_images: 显示文本
    return (
      <pre className="m-0 mt-3 p-4 rounded-lg bg-[rgba(15,23,42,0.6)] border border-[rgba(148,163,184,0.1)] text-slate-300 text-[13px] leading-relaxed whitespace-pre-wrap break-words font-mono">
        {content}
        {isActive && isStreaming && (
          <span className="animate-pulse text-cyan-400">▊</span>
        )}
      </pre>
    );
  };

  // 渲染思考内容
  const renderReasoning = () => {
    if (!reasoning) return null;

    return (
      <div className="mt-3 rounded-xl overflow-hidden bg-gradient-to-br from-indigo-500/10 via-purple-500/10 to-blue-500/10 backdrop-blur-sm border border-indigo-500/20">
        {/* 思考头部 */}
        <button
          onClick={onToggleReasoning}
          className="w-full flex items-center gap-2 px-3.5 py-2.5 border-b border-indigo-500/10 hover:bg-indigo-500/5 transition-colors"
        >
          {isReasoningExpanded ? (
            <ChevronDown className="w-3.5 h-3.5 text-indigo-300" />
          ) : (
            <ChevronRight className="w-3.5 h-3.5 text-indigo-300" />
          )}
          <Brain className="w-3.5 h-3.5 text-indigo-300" />
          <span className="text-xs font-medium text-indigo-300">Thinking</span>
        </button>

        {/* 思考内容 */}
        <AnimatePresence>
          {isReasoningExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden"
            >
              <div className="px-3.5 py-3">
                <pre className="m-0 text-slate-300 text-[13px] leading-relaxed whitespace-pre-wrap break-words font-mono">
                  {reasoning}
                  {isActive && isStreaming && (
                    <span className="animate-pulse text-cyan-400">▊</span>
                  )}
                </pre>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  };

  // 渲染错误信息
  const renderError = () => {
    if (!step.error) return null;

    return (
      <div className="mt-3 flex items-start gap-2 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20">
        <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
        <span className="text-sm text-rose-300">{step.error}</span>
      </div>
    );
  };

  // 渲染优化后的提示词（refine_prompt 步骤）
  const renderRefinedPrompt = () => {
    if (step.step !== 'refine_prompt' || !content) return null;

    return (
      <div className="mt-3 p-4 rounded-lg bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/20">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs font-medium text-cyan-400">优化后的提示词</span>
        </div>
        <p className="text-sm text-slate-300 leading-relaxed">{content}</p>
      </div>
    );
  };

  // 渲染执行状态
  const renderExecutionStatus = () => {
    if (step.step !== 'execute_code' && step.step !== 'analyze_execution_result' && step.step !== 'save_image') {
      return null;
    }

    if (step.status === 'running') {
      return (
        <div className="mt-3 flex items-center gap-2 text-sm text-slate-400">
          <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
          <span>
            {step.step === 'execute_code' && '正在执行代码...'}
            {step.step === 'analyze_execution_result' && '正在分析执行结果...'}
            {step.step === 'save_image' && '正在保存文件...'}
          </span>
        </div>
      );
    }

    if (step.status === 'completed') {
      return (
        <div className="mt-3 flex items-center gap-2 text-sm text-emerald-400">
          <CheckCircle2 className="w-4 h-4" />
          <span>
            {step.step === 'execute_code' && '代码执行完成'}
            {step.step === 'analyze_execution_result' && '分析完成'}
            {step.step === 'save_image' && '文件保存成功'}
          </span>
        </div>
      );
    }

    return null;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`rounded-xl overflow-hidden backdrop-blur-sm border ${
        isActive
          ? 'border-cyan-500/30 shadow-[0_0_20px_rgba(6,182,212,0.15)]'
          : 'border-[rgba(148,163,184,0.1)]'
      } bg-[rgba(15,23,42,0.5)]`}
    >
      {/* 头部 */}
      <div
        className={`flex items-center gap-3 p-4 ${
          hasContent ? 'cursor-pointer hover:bg-[rgba(30,41,59,0.3)]' : ''
        } transition-colors`}
        onClick={() => hasContent && onToggleExpand()}
      >
        {/* 状态图标 */}
        <StatusIcon status={step.status} />

        {/* 步骤名称 */}
        <span className="flex-1 text-sm font-medium text-slate-200">{step.name}</span>

        {/* 耗时 */}
        {duration && (
          <span className="text-xs text-slate-500 font-mono tabular-nums">{duration}</span>
        )}

        {/* 展开/折叠图标 */}
        {hasContent && (
          <motion.div
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronDown className="w-4 h-4 text-slate-500" />
          </motion.div>
        )}
      </div>

      {/* 内容区域 */}
      <AnimatePresence>
        {isExpanded && hasContent && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <div
              ref={contentRef}
              className="px-4 pb-4 max-h-[500px] overflow-y-auto scroll-smooth"
            >
              {/* 错误信息 */}
              {renderError()}

              {/* 优化后的提示词 */}
              {renderRefinedPrompt()}

              {/* 执行状态 */}
              {renderExecutionStatus()}

              {/* 思考内容 */}
              {renderReasoning()}

              {/* 主内容 */}
              {(step.step === 'generate_code' || step.step === 'fix_code_with_feedback') &&
                renderContent()}

              {/* 文档内容 */}
              {workflowType === 'document_with_images' && step.step !== 'refine_prompt' &&
                renderContent()}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

// ============================================================================
// ProcessingView Component
// ============================================================================

const ProcessingView: React.FC<ProcessingViewProps> = ({
  steps,
  streamContent,
  reasoningContent,
  currentNode,
  isStreaming,
  workflowType,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const activeCardRef = useRef<HTMLDivElement>(null);
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());
  const [expandedReasoning, setExpandedReasoning] = useState<Set<string>>(new Set());

  // 过滤非pending状态的步骤
  const activeSteps = useMemo(() => {
    return steps.filter((step) => step.status !== 'pending');
  }, [steps]);

  // 自动展开当前流式步骤
  useEffect(() => {
    if (currentNode && isStreaming) {
      setExpandedSteps((prev) => new Set(prev).add(currentNode));
    }
  }, [currentNode, isStreaming]);

  // 自动滚动到活动卡片
  useEffect(() => {
    if (activeCardRef.current && isStreaming) {
      activeCardRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [currentNode, isStreaming, activeSteps]);

  // 切换步骤展开状态
  const handleToggleExpand = (stepId: string) => {
    setExpandedSteps((prev) => {
      const next = new Set(prev);
      if (next.has(stepId)) {
        next.delete(stepId);
      } else {
        next.add(stepId);
      }
      return next;
    });
  };

  // 切换思考展开状态
  const handleToggleReasoning = (stepId: string) => {
    setExpandedReasoning((prev) => {
      const next = new Set(prev);
      if (next.has(stepId)) {
        next.delete(stepId);
      } else {
        next.add(stepId);
      }
      return next;
    });
  };

  return (
    <div
      ref={containerRef}
      className="h-full overflow-auto p-4 space-y-3"
    >
      {activeSteps.map((step) => {
        const content = streamContent.get(step.step) || '';
        const reasoning = reasoningContent.get(step.step) || '';
        const isActive = step.step === currentNode && isStreaming;
        const isExpanded = expandedSteps.has(step.step);
        const isReasoningExpanded = expandedReasoning.has(step.step);

        return (
          <div
            key={step.step}
            ref={isActive ? activeCardRef : null}
          >
            <StepCard
              step={step}
              content={content}
              reasoning={reasoning}
              isActive={isActive}
              isStreaming={isStreaming}
              workflowType={workflowType}
              isExpanded={isExpanded}
              onToggleExpand={() => handleToggleExpand(step.step)}
              isReasoningExpanded={isReasoningExpanded}
              onToggleReasoning={() => handleToggleReasoning(step.step)}
            />
          </div>
        );
      })}

      {/* 空状态 */}
      {activeSteps.length === 0 && (
        <div className="flex flex-col items-center justify-center h-full text-slate-500">
          <div className="w-16 h-16 rounded-full bg-slate-800/50 flex items-center justify-center mb-4">
            <Clock className="w-8 h-8 text-slate-600" />
          </div>
          <p className="text-sm">等待工作流开始...</p>
        </div>
      )}
    </div>
  );
};

export default React.memo(ProcessingView);
