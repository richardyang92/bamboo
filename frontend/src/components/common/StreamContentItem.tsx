/**
 * StreamContentItem - 单节点流式内容卡片
 * 显示单个节点的流式内容，支持代码/Markdown渲染
 */
import React, { useEffect, useRef } from 'react';
import { Spin, Tag, Space, Typography } from 'antd';
import { CheckCircleFilled, CloseCircleFilled, LoadingOutlined, ClockCircleFilled } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import type { WorkflowStep, WorkflowType } from '../../types';
import CodeBlock from './CodeBlock';
import './StreamContentItem.css';

const { Text } = Typography;

interface StreamContentItemProps {
  step: WorkflowStep;
  content: string;
  isActive: boolean;
  isStreaming: boolean;
  workflowType: WorkflowType;
  contentType?: 'content' | 'reasoning';  // 新增：内容类型
  reasoningContent?: string;  // 新增：独立的思考内容
}

// 获取步骤状态颜色
const getStatusColor = (status: WorkflowStep['status']): string => {
  switch (status) {
    case 'running':
      return '#1890ff'; // 蓝色
    case 'completed':
      return '#52c41a'; // 绿色
    case 'error':
      return '#ff4d4f'; // 红色
    case 'pending':
    default:
      return '#d9d9d9'; // 灰色
  }
};

// 获取步骤状态文本
const getStatusText = (status: WorkflowStep['status']): string => {
  switch (status) {
    case 'running':
      return '执行中';
    case 'completed':
      return '已完成';
    case 'error':
      return '失败';
    case 'pending':
    default:
      return '等待中';
  }
};

// 获取步骤图标
const getStepIcon = (status: WorkflowStep['status'], size = 16) => {
  const color = getStatusColor(status);

  if (status === 'running') {
    return <LoadingOutlined style={{ fontSize: size, color }} spin />;
  }
  if (status === 'completed') {
    return <CheckCircleFilled style={{ fontSize: size, color }} />;
  }
  if (status === 'error') {
    return <CloseCircleFilled style={{ fontSize: size, color }} />;
  }
  return <ClockCircleFilled style={{ fontSize: size, color }} />;
};

// 检测代码语言
const detectLanguage = (workflowType: WorkflowType): string => {
  if (workflowType === 'drawing' || workflowType === 'manim') {
    return 'python';
  }
  return 'text';
};

const StreamContentItem: React.FC<StreamContentItemProps> = ({
  step,
  content,
  isActive,
  isStreaming,
  workflowType,
  contentType = 'content',  // 默认为普通内容
  reasoningContent = '',  // 新增：独立的思考内容
}) => {
  const language = detectLanguage(workflowType);
  const isReasoning = contentType === 'reasoning';  // 是否为思考内容
  const hasReasoning = !!reasoningContent;  // 是否有思考内容
  const contentBodyRef = useRef<HTMLDivElement>(null);

  // 内容变化时自动滚动到底部
  useEffect(() => {
    if (contentBodyRef.current && (content || reasoningContent)) {
      // 使用 requestAnimationFrame 确保 DOM 渲染完成后再滚动
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          if (contentBodyRef.current) {
            contentBodyRef.current.scrollTop = contentBodyRef.current.scrollHeight;
          }
        });
      });
    }
  }, [content, reasoningContent]);

  // 判断是否渲染为Markdown
  const shouldRenderAsMarkdown = workflowType === 'document_with_images';
  // 判断是否渲染为代码
  const shouldRenderAsCode = workflowType === 'drawing' || workflowType === 'manim';

  // 空内容占位（节点已完成且无内容时不显示）
  const shouldShowPlaceholder = !content && !hasReasoning && step.status !== 'completed';
  const placeholder = shouldShowPlaceholder ? (
    <div className="stream-content-placeholder">
      <Text type="secondary" style={{ fontSize: '13px' }}>
        {step.status === 'pending' ? '等待执行...' : isReasoning ? '暂无思考内容' : '此节点暂无流式内容'}
      </Text>
    </div>
  ) : null;

  // 渲染思考内容
  const renderReasoningContent = () => {
    if (!hasReasoning) return null;

    return (
      <div className="stream-content-reasoning">
        <Space size="small">
          <span className="reasoning-icon">🧠</span>
          <pre className="reasoning-text">{reasoningContent}</pre>
        </Space>
      </div>
    );
  };

  // 渲染普通内容
  const renderContent = () => {
    if (!content) return null;

    if (shouldRenderAsMarkdown) {
      return (
        <div className="stream-content-markdown">
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
      );
    }

    if (shouldRenderAsCode) {
      return <CodeBlock code={content} language={language} showLineNumbers={true} />;
    }

    // 纯文本渲染
    return (
      <pre className="stream-content-text">
        {content}
      </pre>
    );
  };

  return (
    <div className={`stream-content-item ${isActive ? 'active' : ''} ${isStreaming ? 'streaming' : ''}`}>
      {/* 节点头部 */}
      <div className="stream-content-header">
        <Space size="small">
          {getStepIcon(step.status, 14)}
          <Text strong style={{ fontSize: '13px' }}>
            {step.name}
          </Text>
          <Tag
            color={step.status === 'running' ? 'processing' : step.status === 'completed' ? 'success' : step.status === 'error' ? 'error' : 'default'}
            style={{ fontSize: '11px', margin: 0 }}
          >
            {getStatusText(step.status)}
          </Tag>
          {isStreaming && <Spin size="small" />}
        </Space>
        {content && (
          <Text type="secondary" style={{ fontSize: '11px' }}>
            {content.length} 字符
          </Text>
        )}
      </div>

      {/* 内容区域 */}
      <div className="stream-content-body" ref={contentBodyRef}>
        {/* 先渲染思考内容 */}
        {renderReasoningContent()}
        {/* 再渲染普通内容 */}
        {renderContent()}
        {/* 如果没有任何内容，显示占位符（已完成节点除外） */}
        {shouldShowPlaceholder && placeholder}
      </div>
    </div>
  );
};

export default React.memo(StreamContentItem);
