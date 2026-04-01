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
    case 'running': return 'text-blue-400';
    case 'completed': return 'text-green-400';
    case 'error': return 'text-red-400';
    default: return 'text-gray-400';
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
    case 'running': return 'bg-blue-500/20 text-blue-400';
    case 'completed': return 'bg-green-500/20 text-green-400';
    case 'error': return 'bg-red-500/20 text-red-400';
    default: return 'bg-gray-500/20 text-gray-400';
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
      <div className="px-3.5 py-3 bg-gradient-to-br from-indigo-500/10 to-blue-500/10 border-l-[3px] border-l-indigo-500">
        <span className="text-base leading-none mr-1.5">🧠</span>
        <pre className="inline text-[var(--color-text-secondary)] text-[13px] leading-relaxed whitespace-pre-wrap break-words font-mono">
          {reasoningContent}
        </pre>
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
      className={`rounded-lg overflow-hidden transition-all duration-300 ${
        isActive ? 'border border-blue-500/30 shadow-[0_2px_8px_rgba(59,130,246,0.15)]' : ''
      } ${isStreaming ? 'animate-[pulse-border_2s_ease-in-out_infinite]' : ''}`}
    >
      <div className="flex justify-between items-center px-3.5 py-2.5 bg-[var(--color-bg-dark)] border-b border-[var(--color-border)] min-h-[44px]">
        <span className="flex items-center gap-1.5">
          {getStepIcon(step.status)}
          <span className="font-medium text-[13px] text-[var(--color-text-primary)]">
            {step.name}
          </span>
          <span
            className={`inline-flex items-center px-1.5 py-0.5 rounded text-[11px] leading-none font-medium ${getTagClasses(step.status)}`}
          >
            {getStatusText(step.status)}
          </span>
          {isStreaming && <Loader2 className="w-3 h-3 text-blue-400 animate-spin ml-1" />}
        </span>
        {content && (
          <span className="text-[11px] text-[var(--color-text-muted)]">
            {content.length} 字符
          </span>
        )}
      </div>

      <div
        className="p-3.5 bg-[var(--color-bg-card)] min-h-[60px] max-h-[500px] overflow-y-auto scroll-smooth"
        ref={contentBodyRef}
      >
        {renderReasoningContent()}
        {renderContent()}
        {shouldShowPlaceholder && (
          <div className="flex justify-center items-center py-6 min-h-[60px]">
            <span className="text-[13px] text-[var(--color-text-muted)]">
              {step.status === 'pending' ? '等待执行...' : contentType === 'reasoning' ? '暂无思考内容' : '此节点暂无流式内容'}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default React.memo(StreamContentItem);
