/**
 * StreamContentViewer - 流式内容展示器
 * 按工作流类型展示代码或Markdown内容，支持自动滚动和完成后折叠
 */
import React, { useState, useEffect, useRef } from 'react';
import { Card, Spin } from 'antd';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import type { WorkflowType } from '../../types';
import CodeBlock from './CodeBlock';
import StreamControls from './StreamControls';

interface StreamContentViewerProps {
  content: string;
  nodeType: string;
  workflowType: WorkflowType;
  isStreaming: boolean;
  className?: string;
}

const StreamContentViewer: React.FC<StreamContentViewerProps> = ({
  content,
  nodeType,
  workflowType,
  isStreaming,
  className = '',
}) => {
  const [autoScroll, setAutoScroll] = useState(true);
  const contentRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    if (autoScroll && contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, [content, autoScroll]);

  // 判断是否渲染为Markdown
  const shouldRenderAsMarkdown = workflowType === 'document_with_images';
  // 判断是否渲染为代码
  const shouldRenderAsCode = workflowType === 'drawing' || workflowType === 'manim';

  // 检测代码语言
  const detectLanguage = (): string => {
    if (workflowType === 'drawing' || workflowType === 'manim') {
      return 'python';
    }
    return 'text';
  };

  // 如果没有内容，显示占位提示
  const placeholder = !content ? (
    <div
      style={{
        color: '#999',
        fontSize: '14px',
        textAlign: 'center',
        padding: '40px 20px',
        fontFamily: 'monospace',
      }}
    >
      {isStreaming ? '等待生成内容...' : '暂无流式内容，请开始工作流'}
    </div>
  ) : null;

  return (
    <Card
      className={`stream-content-viewer ${className}`}
      title={
        <span>
          {isStreaming && <Spin size="small" style={{ marginRight: 8 }} />}
          流式内容 - {nodeType}
        </span>
      }
      style={{ marginTop: '16px', height: '100%', display: 'flex', flexDirection: 'column' }}
      styles={{ body: { flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: '16px' } }}
    >
      <div
        ref={contentRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          background: '#1e1e1e',
          borderRadius: '8px',
          padding: '16px',
          minHeight: 0,
        }}
      >
        {placeholder || (
          <>
            {shouldRenderAsMarkdown ? (
              // Markdown渲染
              <div style={{ color: '#d4d4d4', fontSize: '14px', lineHeight: '1.6' }}>
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
                            fontFamily: 'monospace',
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
            ) : shouldRenderAsCode ? (
              // 代码渲染
              <CodeBlock
                code={content}
                language={detectLanguage()}
                maxHeight="500px"
                showLineNumbers={true}
              />
            ) : (
              // 纯文本渲染
              <pre
                style={{
                  color: '#d4d4d4',
                  fontSize: '13px',
                  lineHeight: '1.6',
                  fontFamily: 'monospace',
                  whiteSpace: 'pre-wrap',
                  wordWrap: 'break-word',
                }}
              >
                {content}
              </pre>
            )}
          </>
        )}
      </div>
      {!placeholder && (
        <StreamControls
          isScrolling={autoScroll}
          onToggleScroll={() => setAutoScroll(!autoScroll)}
          contentLength={content.length}
          isStreaming={isStreaming}
        />
      )}
    </Card>
  );
};

export default StreamContentViewer;
