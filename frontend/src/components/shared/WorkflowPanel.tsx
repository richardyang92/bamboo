import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Square, Trash2, Loader2, Check, Sparkles } from 'lucide-react';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useWorkflow } from '../../contexts/WorkflowContext';
import { showToast } from '../../services/toast';
import WorkflowTimeline from '../common/WorkflowTimeline';
import EmptyView from '../common/EmptyView';
import WorkflowStatusIndicator from '../common/WorkflowStatusIndicator';
import ResultPlaceholder from '../common/ResultPlaceholder';
import ProcessingView from '../common/ProcessingView';
import type { WorkflowType, WorkflowResult, LLMProvider } from '../../types';

function ResultRenderer({ renderFn, result }: { renderFn: (r: WorkflowResult) => React.ReactNode; result: WorkflowResult }) {
  return renderFn(result);
}

const TYPEWRITER_EXAMPLES: Record<WorkflowType, string[]> = {
  drawing: ["绘制正弦函数图像", "展示傅科摆运动轨迹", "生成地月系统示意图", "绘制理想气体状态方程PV图", "展示牛顿摆能量守恒"],
  document_with_images: ["量子力学基础教程", "Python数据分析入门", "深度学习原理详解", "线性代数核心概念", "微积分基本定理"],
  manim: ["展示圆的面积推导过程", "傅里叶变换可视化", "洛伦兹吸引子动画", "泰勒展开几何直观", "矩阵乘法动画演示"],
};

const TEMPLATE_CHIPS: Record<WorkflowType, { label: string; prompt: string }[]> = {
  drawing: [
    { label: "科学图表", prompt: "绘制一个【在此输入数据描述】的科学图表" },
    { label: "数学函数", prompt: "绘制【在此输入函数表达式】的函数图像" },
    { label: "物理模拟", prompt: "展示【在此输入物理现象】的运动示意图" },
    { label: "数据分析", prompt: "绘制【在此输入数据类型】的数据可视化图表" },
    { label: "流程图", prompt: "绘制一个【在此输入流程描述】的流程图" },
  ],
  document_with_images: [
    { label: "技术教程", prompt: "编写一篇关于【在此输入主题】的技术教程" },
    { label: "学术总结", prompt: "对【在此输入主题】进行系统性总结" },
    { label: "入门指南", prompt: "编写【在此输入主题】的入门指南" },
    { label: "原理详解", prompt: "详细解释【在此输入原理】的工作原理" },
  ],
  manim: [
    { label: "数学动画", prompt: "制作一个【在此输入数学概念】的动画演示" },
    { label: "几何变换", prompt: "展示【在此输入几何变换】的动画过程" },
    { label: "物理演示", prompt: "动画演示【在此输入物理现象】" },
  ],
};

function useTypewriter(workflowType: WorkflowType, isActive: boolean) {
  const examples = TYPEWRITER_EXAMPLES[workflowType];
  const [displayText, setDisplayText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isTyping, setIsTyping] = useState(true);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearTypewriterInterval = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!isActive) {
      setDisplayText('');
      clearTypewriterInterval();
      return;
    }

    const currentExample = examples[currentIndex];

    if (isTyping) {
      let charIndex = displayText.length;
      intervalRef.current = setInterval(() => {
        if (charIndex < currentExample.length) {
          setDisplayText(currentExample.slice(0, charIndex + 1));
          charIndex++;
        } else {
          clearTypewriterInterval();
          setTimeout(() => setIsTyping(false), 2000);
        }
      }, 60);
    } else {
      intervalRef.current = setInterval(() => {
        if (displayText.length > 0) {
          setDisplayText(displayText.slice(0, -1));
        } else {
          clearTypewriterInterval();
          setCurrentIndex((prev) => (prev + 1) % examples.length);
          setIsTyping(true);
        }
      }, 30);
    }

    return () => clearTypewriterInterval();
  }, [isActive, isTyping, currentIndex, displayText, examples, clearTypewriterInterval]);

  return displayText;
}

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
  const [isFocused, setIsFocused] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const isRunning = status === 'running';
  const hasActiveSteps = steps.filter(s => s.status !== 'pending').length > 0;
  const showTypewriter = !isFocused && !prompt && !isRunning;
  const typewriterText = useTypewriter(workflowType, showTypewriter);

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
      
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 1500);
      
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

  const handleChipClick = (chipPrompt: string) => {
    setPrompt(chipPrompt);
    textareaRef.current?.focus();
  };

  const resultType = workflowType === 'document_with_images' ? 'document' : workflowType;

  return (
    <div className="flex h-full">
      <div className="flex flex-col w-[400px] shrink-0 
        bg-[rgba(30,41,59,0.5)] backdrop-blur-md
        border-r border-[rgba(148,163,184,0.08)]">
        
        <div className="p-4 border-b border-[rgba(148,163,184,0.08)]">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-sm font-medium text-[#f8fafc]">
              {placeholder.includes('绘图') ? '绘图需求' : placeholder.includes('文档') ? '文档主题' : '动画需求'}
            </span>
            <WorkflowStatusIndicator
              workflowStatus={status}
              connectionState={connectionState}
              workflowType={workflowType}
            />
          </div>

          <div className="relative">
            <textarea
              ref={textareaRef}
              className="w-full 
                bg-[rgba(15,23,42,0.8)] 
                border border-[rgba(148,163,184,0.1)] 
                rounded-2xl 
                p-3 text-sm text-[#f8fafc] 
                placeholder:text-[#64748b] 
                resize-none 
                focus:outline-none 
                focus:shadow-[0_0_0_2px_rgba(6,182,212,0.3),0_0_20px_rgba(6,182,212,0.1)]
                focus:border-[rgba(6,182,212,0.5)]
                focus:scale-[1.01]
                transition-all duration-300 ease-out
                disabled:opacity-50 disabled:cursor-not-allowed"
              rows={3}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              disabled={isRunning}
            />
            {showTypewriter && typewriterText && (
              <div className="absolute top-3 left-3 right-3 pointer-events-none text-[#64748b] text-sm">
                {typewriterText}
                <span className="animate-pulse">|</span>
              </div>
            )}
          </div>

          {!isRunning && (
            <div className="flex flex-wrap gap-1.5 mt-2">
              {TEMPLATE_CHIPS[workflowType].map((chip) => (
                <button
                  key={chip.label}
                  onClick={() => handleChipClick(chip.prompt)}
                  className="px-2.5 py-1 text-xs rounded-full bg-white/5 text-[#94a3b8] border border-white/5 hover:bg-white/10 hover:text-[#f8fafc] hover:border-white/10 transition-all duration-200 cursor-pointer active:scale-95"
                >
                  {chip.label}
                </button>
              ))}
            </div>
          )}

          <div className="flex items-center gap-2 mt-3">
            <motion.button
              layout
              className="relative overflow-hidden
                bg-gradient-to-br from-[#06b6d4] to-[#3b82f6]
                text-white px-4 py-2 rounded-xl text-sm font-medium 
                inline-flex items-center gap-2 
                hover:shadow-lg hover:shadow-[rgba(6,182,212,0.3)]
                active:scale-[0.98]
                disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none"
              onClick={handleStart}
              disabled={isRunning}
              animate={showSuccess ? { scale: [1, 1.05, 1] } : { scale: 1 }}
              transition={{ duration: 0.2, type: "spring", stiffness: 400, damping: 20 }}
            >
              <AnimatePresence mode="wait" initial={false}>
                {isRunning ? (
                  <motion.div
                    key="running"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.15 }}
                    className="inline-flex items-center gap-2"
                  >
                    <Loader2 size={16} className="animate-spin" />
                    <span className="opacity-90">{runningLabel}</span>
                  </motion.div>
                ) : showSuccess ? (
                  <motion.div
                    key="success"
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.15 }}
                    className="inline-flex items-center gap-2"
                  >
                    <Check size={16} />
                    <span>已启动</span>
                  </motion.div>
                ) : (
                  <motion.div
                    key="idle"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.15 }}
                    className="inline-flex items-center gap-2"
                  >
                    <Sparkles size={16} className="opacity-90" />
                    <span>{startLabel}</span>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.button>

            {isRunning && (
              <button
                className="
                  bg-[rgba(244,63,94,0.15)] 
                  text-[#f43f5e] 
                  hover:bg-[rgba(244,63,94,0.25)]
                  px-3 py-2 rounded-xl text-sm 
                  inline-flex items-center gap-1.5
                  transition-all duration-200
                  active:scale-[0.98]"
                onClick={handleStop}
              >
                <Square size={14} fill="currentColor" />
                停止
              </button>
            )}

            <button
              className="
                text-[#94a3b8] 
                hover:text-[#f8fafc] 
                hover:bg-[rgba(148,163,184,0.1)]
                px-3 py-2 rounded-xl text-sm 
                inline-flex items-center gap-1.5
                transition-all duration-200
                disabled:opacity-50 disabled:cursor-not-allowed"
              onClick={handleClear}
              disabled={isRunning}
            >
              <Trash2 size={14} />
              清除历史
            </button>

            {extraControls}
          </div>
        </div>

        <div className={`flex-1 overflow-auto ${isRunning ? 'p-2' : 'p-4'}`}>
          {hasActiveSteps ? (
            <WorkflowTimeline
              steps={steps}
              streamContent={streamContent}
              reasoningContent={reasoningContent}
              currentNode={currentNode}
              isStreaming={isStreaming}
              workflowType={workflowType}
              compact={isRunning}
            />
          ) : (
            <EmptyView workflowType={workflowType} />
          )}
        </div>
      </div>

      <div className="flex-1 overflow-hidden
        bg-[radial-gradient(ellipse_at_top,rgba(30,41,59,0.3),transparent_50%)]
        bg-[radial-gradient(ellipse_at_bottom_right,rgba(6,182,212,0.05),transparent_50%)]">
        <AnimatePresence mode="wait">
          {result ? (
            <motion.div
              key="result"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="h-full overflow-auto p-4"
            >
              <ResultRenderer renderFn={renderResult} result={result} />
            </motion.div>
          ) : isRunning ? (
            <motion.div
              key="processing"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="h-full"
            >
              <ProcessingView
                steps={steps}
                streamContent={streamContent}
                reasoningContent={reasoningContent}
                currentNode={currentNode}
                isStreaming={isStreaming}
                workflowType={workflowType}
              />
            </motion.div>
          ) : (
            <motion.div
              key="placeholder"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="h-full overflow-auto p-4"
            >
              <ResultPlaceholder type={resultType} error={error} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
