import React, { useEffect, useRef } from 'react';
import { CheckCircle2, XCircle, Loader2, Clock } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import type { WorkflowStep, WorkflowType } from '../../types';
import CodeBlock from './CodeBlock';

interface StreamContentItemProps {
  step: WorkflowStep;
  content: string;
  isActive: boolean;
  isStreaming: boolean;
  workflowType: WorkflowType;
  contentType?: 'content' | 'reasoning';
  reasoningContent?: string;
}

const getStatusColor = (status: WorkflowStep['status']): string => {
  switch (status) {
    case 'running': return 'text-cyan-400';
    case 'completed': return 'text-emerald-400';
    case 'error': return 'text-rose-400';
    default: return 'text-slate-400';
  }
};

const getStatusText = (status: WorkflowStep['status']): string => {
  switch (status) {
    case 'running': return '执行中';
    case 'completed': return '已完成';
    case 'error': return '失败';
    default: return '等待中';
  }
};

const getStepIcon = (status: WorkflowStep['status']) => {
  const colorClass = getStatusColor(status);
  switch (status) {
    case 'running':
      return <Loader2 className={`w-3.5 h-3.5 ${colorClass} animate-spin`} />;
    case 'completed':
      return <CheckCircle2 className={`w-3.5 h-3.5 ${colorClass}`} />;
    case 'error':
      return <XCircle className={`w-3.5 h-3.5 ${colorClass}`} />;
    default:
      return <Clock className={`w-3.5 h-3.5 ${colorClass}`} />;
  }
};

const getTagClasses = (status: WorkflowStep['status']): string => {
  switch (status) {
    case 'running': return 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/20';
    case 'completed': return 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/20';
    case 'error': return 'bg-rose-500/15 text-rose-400 border border-rose-500/20';
    default: return 'bg-slate-500/15 text-slate-400 border border-slate-500/20';
  }
};

const detectLanguage = (workflowType: WorkflowType): string => {
  if (workflowType === 'drawing' || workflowType === 'manim') return 'python';
  return 'text';
};

const StreamContentItem: React.FC<StreamContentItemProps> = ({
  step,
  content,
  isActive,
  isStreaming,
  workflowType,
  contentType = 'content',
  reasoningContent = '',
}) => {
  const language = detectLanguage(workflowType);
  const hasReasoning = !!reasoningContent;
  const contentBodyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (contentBodyRef.current && (content || reasoningContent)) {
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          if (contentBodyRef.current) {
            contentBodyRef.current.scrollTop = contentBodyRef.current.scrollHeight;
          }
        });
      });
    }
  }, [content, reasoningContent]);

  const shouldRenderAsMarkdown = workflowType === 'document_with_images';
  const shouldRenderAsCode = workflowType === 'drawing' || workflowType === 'manim';

  const shouldShowPlaceholder = !content && !hasReasoning && step.status !== 'completed';

  const renderReasoningContent = () => {
    if (!hasReasoning) return null;
    return (
      <div className="mb-3 rounded-lg overflow-hidden bg-gradient-to-br from-indigo-500/10 via-purple-500/10 to-blue-500/10 backdrop-blur-sm border border-indigo-500/20">
        <div className="px-3.5 py-2.5 border-b border-indigo-500/10">
          <span className="text-xs font-medium text-indigo-300 flex items-center gap-1.5">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            Thinking
          </span>
        </div>
        <div className="px-3.5 py-3">
          <pre className="m-0 text-slate-300 text-[13px] leading-relaxed whitespace-pre-wrap break-words font-mono">
            {reasoningContent}
          </pre>
        </div>
      </div>
    );
  };

  const renderContent = () => {
    if (!content) return null;

    if (shouldRenderAsMarkdown) {
      return (
        <div className="text-[var(--color-text-primary)] text-sm leading-relaxed break-words">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code({ className, children, ...props }: any) {
                const match = /language-(\w+)/.exec(className || '');
                const isInline = !className || !match;
                return !isInline ? (
                  <SyntaxHighlighter
                    style={oneDark}
                    language={match[1]}
                    PreTag="div"
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code
                    className={className}
                    style={{
                      background: '#2d2d2d',
                      padding: '2px 6px',
                      borderRadius: '3px',
                      fontFamily: 'var(--font-mono)',
                    }}
                    {...props}
                  >
                    {children}
                  </code>
                );
              },
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
      );
    }

    if (shouldRenderAsCode) {
      return <CodeBlock code={content} language={language} showLineNumbers={true} />;
    }

    return (
      <pre className="m-0 p-0 text-[var(--color-text-primary)] text-[13px] leading-relaxed font-mono whitespace-pre-wrap break-words">
        {content}
      </pre>
    );
  };

  return (
    <div
      className={`rounded-xl overflow-hidden transition-all duration-300 ${
        isActive ? 'border border-cyan-500/30 shadow-[0_0_20px_rgba(6,182,212,0.15)]' : 'border border-slate-700/30'
      } ${isStreaming ? 'animate-[pulse-border_2s_ease-in-out_infinite]' : ''}`}
    >
      {/* Header bar with glass effect */}
      <div className="flex justify-between items-center px-4 py-3 bg-[rgba(15,23,42,0.8)] backdrop-blur-md border-b border-slate-700/30 min-h-[48px]">
        <span className="flex items-center gap-2">
          {getStepIcon(step.status)}
          <span className="font-medium text-[13px] text-slate-200">
            {step.name}
          </span>
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] leading-none font-medium ${getTagClasses(step.status)}`}
          >
            {getStatusText(step.status)}
          </span>
          {isStreaming && <Loader2 className="w-3.5 h-3.5 text-cyan-400 animate-spin ml-1" />}
        </span>
        {content && (
          <span className="text-[11px] text-slate-500 font-mono">
            {content.length} chars
          </span>
        )}
      </div>

      {/* Content body with glass effect */}
      <div
        className="p-4 bg-[rgba(15,23,42,0.5)] backdrop-blur-sm min-h-[60px] max-h-[500px] overflow-y-auto scroll-smooth"
        ref={contentBodyRef}
      >
        {renderReasoningContent()}
        {renderContent()}
        {shouldShowPlaceholder && (
          <div className="flex justify-center items-center py-6 min-h-[60px]">
            <span className="text-[13px] text-slate-500">
              {step.status === 'pending' ? 'Waiting...' : contentType === 'reasoning' ? 'No thinking content' : 'No stream content'}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default React.memo(StreamContentItem);
