/**
 * 文档工作流面板 - 增强版
 * 集成实时状态展示、步骤进度和流式内容
 */
import { useState, useMemo } from 'react';
import { Card, Input, Button, Space, Tabs, message, Image } from 'antd';
import { SendOutlined, LoadingOutlined, PictureOutlined, StopOutlined } from '@ant-design/icons';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useWorkflow } from '../../contexts/WorkflowContext';
import * as api from '../../services/api';
import WorkflowStatusIndicator from '../common/WorkflowStatusIndicator';
import WorkflowExecutionTracker from '../common/WorkflowExecutionTracker';
import WorkflowTimeline from '../common/WorkflowTimeline';
import EmptyView from '../common/EmptyView';
import ResultPlaceholder from '../common/ResultPlaceholder';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import rehypeRaw from 'rehype-raw';
import 'katex/dist/katex.min.css';

const { TextArea } = Input;

function DocumentPanel() {
  const {
    status,
    steps,
    currentStep,
    result,
    error,
    connectionState,
    currentNode,
    isStreaming,
    streamContent,
    reasoningContent,  // 新增：获取思考内容
  } = useWebSocket('document_with_images');

  const { state: { modelConfig } } = useWorkflow();
  const [prompt, setPrompt] = useState('');

  const handleStart = async () => {
    if (!prompt.trim()) {
      message.warning('请输入文档主题');
      return;
    }

    try {
      await api.startDocumentWorkflow(prompt, {
        provider: modelConfig.provider,
        model: modelConfig.model,
        enable_thinking: modelConfig.enable_thinking,
      });
      message.success('文档工作流已启动');
    } catch (err) {
      message.error(err instanceof Error ? err.message : '启动失败');
    }
  };

  const handleClear = async () => {
    try {
      await api.clearDocumentHistory();
      message.success('历史记录已清除');
    } catch (err) {
      message.error(err instanceof Error ? err.message : '清除失败');
    }
  };

  const handleStop = async () => {
    try {
      await api.stopDocumentWorkflow();
      message.success('工作流已停止');
    } catch (err) {
      message.error(err instanceof Error ? err.message : '停止失败');
    }
  };

  const isRunning = status === 'running';

  // 辅助函数：将相对路径或绝对路径转换为API URL
  const convertImagePathToUrl = (path: string | undefined): string => {
    if (!path) return '';
    // 如果是相对路径 ../images/xxx.png，转换为 /api/images/xxx.png
    if (path.includes('../images/')) {
      return path.replace(/\.\.\/images\//g, '/api/images/');
    }
    // 如果是绝对路径，提取文件名并构建 API URL
    const filename = path.split(/[\\/]/).pop();
    if (filename) {
      return `/api/images/${filename}`;
    }
    return '';
  };

  // 处理图片路径：将 ../images/xxx.png 转换为 /api/images/xxx.png
  const processedContent = useMemo(() => {
    if (!result?.content) return '';
    return result.content.replace(
      /\.\.\/images\/([^)]+)/g,
      '/api/images/$1'
    );
  }, [result?.content]);

  // 处理大纲中的图片路径
  const processedOutline = useMemo(() => {
    if (!result?.outline) return '';
    return result.outline.replace(
      /\.\.\/images\/([^)]+)/g,
      '/api/images/$1'
    );
  }, [result?.outline]);

  return (
    <div className="workflow-panel">
      <div className="workflow-panel-left">
        <Space style={{ width: '100%' }} direction="vertical" size="large">
          {/* 输入区域 - 带状态指示器 */}
          <Card
            title={
              <Space>
                <span>文档主题</span>
                <WorkflowStatusIndicator
                  workflowStatus={status}
                  connectionState={connectionState}
                  workflowType="document_with_images"
                />
              </Space>
            }
          >
            <Space style={{ width: '100%' }} direction="vertical">
              <TextArea
                rows={4}
                placeholder="请描述你想要生成的文档主题，例如：机器学习入门"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                disabled={isRunning}
              />
              <Space style={{ width: '100%' }}>
                <Button
                  type="primary"
                  icon={isRunning ? <LoadingOutlined /> : <SendOutlined />}
                  onClick={handleStart}
                  disabled={isRunning}
                >
                  {isRunning ? '生成中...' : '开始生成'}
                </Button>
                {isRunning && (
                  <Button
                    danger
                    icon={<StopOutlined />}
                    onClick={handleStop}
                  >
                    停止
                  </Button>
                )}
                <Button onClick={handleClear} disabled={isRunning}>
                  清除历史
                </Button>
              </Space>
            </Space>
          </Card>

          {/* 工作流执行时间线 */}
          <Card
            title="执行时间线">
            {steps.filter(s => s.status !== 'pending').length > 0 ? (
              <WorkflowTimeline
                steps={steps}
                streamContent={streamContent}
                reasoningContent={reasoningContent}
                currentNode={currentNode}
                isStreaming={isStreaming}
                workflowType="document_with_images"
              />
            ) : (
              <EmptyView workflowType="document_with_images" />
            )}
          </Card>
        </Space>
      </div>

      {/* 右侧结果区域 */}
      <div className="workflow-panel-right">
        {result && result.url ? (
          /* 优先：显示生成结果 */
          <Card title="生成结果">
              <Tabs
                items={[
                  {
                    key: 'preview',
                    label: '预览',
                    children: (
                      <div
                        className="markdown-preview"
                        style={{
                          padding: '16px',
                          lineHeight: '1.8'
                        }}
                      >
                        <ReactMarkdown
                          remarkPlugins={[remarkMath]}
                          rehypePlugins={[
                            rehypeRaw,
                            [rehypeKatex, {
                              throwOnError: false,
                              strict: false,
                            }]
                          ]}
                          components={{
                            img: ({ node, ...props }) => (
                              <img
                                {...props}
                                style={{ maxWidth: '100%', height: 'auto' }}
                                onError={(e) => {
                                  console.error('Image load error:', props.src, e);
                                }}
                              />
                            ),
                            code: ({ node, className, children, ...props }) => {
                              const isInline = !className || !className.includes('language-');
                              if (isInline) {
                                return (
                                  <code className={className} {...props}>
                                    {children}
                                  </code>
                                );
                              }
                              return (
                                <div style={{ margin: '16px 0' }}>
                                  <pre
                                    style={{
                                      background: '#f5f5f5',
                                      padding: '16px',
                                      borderRadius: '4px',
                                      overflow: 'auto',
                                    }}
                                  >
                                    <code className={className} {...props}>
                                      {children}
                                    </code>
                                  </pre>
                                </div>
                              );
                            },
                          }}
                        >
                          {processedContent}
                        </ReactMarkdown>
                      </div>
                    ),
                  },
                  {
                    key: 'outline',
                    label: '大纲',
                    children: (
                      <div
                        className="markdown-preview"
                        style={{
                          padding: '16px',
                          lineHeight: '1.8'
                        }}
                      >
                        <ReactMarkdown
                          remarkPlugins={[remarkMath]}
                          rehypePlugins={[
                            rehypeRaw,
                            [rehypeKatex, {
                              throwOnError: false,
                              strict: false,
                            }]
                          ]}
                          components={{
                            img: ({ node, ...props }) => (
                              <img
                                {...props}
                                style={{ maxWidth: '100%', height: 'auto' }}
                                onError={(e) => {
                                  console.error('Image load error:', props.src, e);
                                }}
                              />
                            ),
                            code: ({ node, className, children, ...props }) => {
                              const isInline = !className || !className.includes('language-');
                              if (isInline) {
                                return (
                                  <code className={className} {...props}>
                                    {children}
                                  </code>
                                );
                              }
                              return (
                                <div style={{ margin: '16px 0' }}>
                                  <pre
                                    style={{
                                      background: '#f5f5f5',
                                      padding: '16px',
                                      borderRadius: '4px',
                                      overflow: 'auto',
                                    }}
                                  >
                                    <code className={className} {...props}>
                                      {children}
                                    </code>
                                  </pre>
                                </div>
                              );
                            },
                          }}
                        >
                          {processedOutline}
                        </ReactMarkdown>
                      </div>
                    ),
                  },
                  {
                    key: 'images',
                    label: `图片 (${result.image_count || 0})`,
                    children: result.images && result.images.length > 0 ? (
                      <div style={{ padding: '8px' }}>
                        <Space wrap>
                          {result.images.map((img: any, i: number) => {
                            const imageUrl = convertImagePathToUrl(img.relative_path || img.path || img.url);
                            const hasImageUrl = !!imageUrl;

                            return (
                              <div key={i} style={{ textAlign: 'center' }}>
                                {hasImageUrl ? (
                                  <>
                                    <Image
                                      src={imageUrl}
                                      alt={img.description || ''}
                                      style={{
                                        maxWidth: '200px',
                                        maxHeight: '200px',
                                        objectFit: 'contain'
                                      }}
                                      fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMIAAADDCAYAAADQvc6UAAABRWlDQ1BJQ0MgUHJvZmlsZQAAKJF9kT1Iw0AcxV9TpVVqCWaAFBVbOhXmuyKiKFjbwKZFgOUfTEp3Zyc3VkwELyJpCoZW1eJpUD8L5U2tXVAQ4T8qC6lOiWwCAWZ0ALy4g1tAAFRLj4h5+THXd3x9fX1dX13d3h3d3d3d3d3d3d3d3d3d3d3d3d3f/gADgABJkBdAgCk9TM/ufn35+fX59fT09PT4+Pj5+fn6+vr39/f4+Pj8/Pz8/Pz8/P39/f39/f4+Pj4+Pj5+fn5+fn6+vr6+vr7+/v7+/v8/Pz8/Pz8/Pz9/f39/f39/f7+/v7+/v7+/v7+/v7+/v7+/v7+/v8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABSU1kB9QLDAQ5I6f9P9f///wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
                                      onError={(e) => {
                                        console.error('Image load error:', imageUrl, e);
                                        const target = e.target as HTMLImageElement;
                                        target.style.display = 'none';
                                        const placeholder = target.parentElement?.querySelector('.image-placeholder') as HTMLDivElement;
                                        if (placeholder) placeholder.style.display = 'flex';
                                      }}
                                    />
                                    <div
                                      className="image-placeholder"
                                      style={{
                                        display: 'none',
                                        width: '200px',
                                        height: '200px',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        flexDirection: 'column',
                                        background: '#f0f0f0',
                                        borderRadius: '8px',
                                        color: '#999'
                                      }}
                                    >
                                      <PictureOutlined style={{ fontSize: '48px', marginBottom: '8px' }} />
                                      <span style={{ fontSize: '12px' }}>图片加载失败</span>
                                    </div>
                                  </>
                                ) : (
                                  <div
                                    style={{
                                      width: '200px',
                                      height: '200px',
                                      alignItems: 'center',
                                      justifyContent: 'center',
                                      flexDirection: 'column',
                                      background: '#f0f0f0',
                                      borderRadius: '8px',
                                      color: '#999',
                                      display: 'flex'
                                    }}
                                  >
                                    <PictureOutlined style={{ fontSize: '48px', marginBottom: '8px' }} />
                                    <span style={{ fontSize: '12px' }}>图片路径缺失</span>
                                  </div>
                                )}
                                {img.description && (
                                  <div style={{
                                    fontSize: '12px',
                                    marginTop: '4px',
                                    maxWidth: '200px',
                                    wordBreak: 'break-word',
                                    textAlign: 'left',
                                    display: '-webkit-box',
                                    WebkitLineClamp: 3,
                                    WebkitBoxOrient: 'vertical',
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis'
                                  }}>
                                    {img.description}
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </Space>
                      </div>
                    ) : (
                      <div style={{ textAlign: 'center', padding: '24px', color: '#999' }}>
                        暂无图片
                      </div>
                    ),
                  },
                ]}
              />
            </Card>
          ) : steps.length > 0 ? (
            /* 有步骤历史：显示执行进度 */
            <Card title="执行进度">
              <WorkflowExecutionTracker
                steps={steps}
                currentStep={currentStep}
                workflowType="document_with_images"
              />
            </Card>
          ) : (
            /* 默认：显示占位符 */
            <Card title="生成结果">
              <ResultPlaceholder type="document" error={error} />
            </Card>
          )}
      </div>
    </div>
  );
}

export default DocumentPanel;
