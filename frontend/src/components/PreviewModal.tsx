/**
 * 预览模态框组件
 * 用于预览历史记录中的图片、文档和视频
 */
import { Modal, Spin, message } from 'antd';
import { useState, useEffect, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeKatex from 'rehype-katex';
import rehypeRaw from 'rehype-raw';
import * as api from '../services/api';
import type { HistoryItem } from '../types';
import 'katex/dist/katex.min.css';

interface PreviewModalProps {
  visible: boolean;
  item: HistoryItem | null;
  onClose: () => void;
}

function PreviewModal({ visible, item, onClose }: PreviewModalProps) {
  const [loading, setLoading] = useState(false);
  const [documentContent, setDocumentContent] = useState<string>('');

  // 当 item 变化时获取文档内容
  useEffect(() => {
    if (visible && item?.type === 'document') {
      fetchDocumentContent(item.name);
    } else {
      setDocumentContent('');
    }
  }, [visible, item]);

  const fetchDocumentContent = async (filename: string) => {
    setLoading(true);
    try {
      const data = await api.getDocumentContent(filename);
      setDocumentContent(data.content);
    } catch (err) {
      message.error(err instanceof Error ? err.message : '获取文档内容失败');
    } finally {
      setLoading(false);
    }
  };

  // 处理图片路径：将 ../images/xxx.png 转换为 /api/images/xxx.png
  const processedContent = useMemo(() => {
    if (!documentContent) return '';
    return documentContent.replace(
      /..\/images\/([^)]+)/g,
      '/api/images/$1'
    );
  }, [documentContent]);

  const renderContent = () => {
    if (!item) return null;

    switch (item.type) {
      case 'image':
        return (
          <div style={{ textAlign: 'center', padding: '24px' }}>
            <img
              src={item.url}
              alt={item.name}
              style={{ maxWidth: '100%', maxHeight: '70vh', objectFit: 'contain' }}
            />
          </div>
        );

      case 'document':
        return (
          <div style={{ minHeight: '400px', padding: '24px' }}>
            {loading ? (
              <div style={{ textAlign: 'center', padding: '100px 0' }}>
                <Spin size="large" />
              </div>
            ) : (
              <div className="markdown-preview" style={{ lineHeight: '1.8' }}>
                <ReactMarkdown
                  rehypePlugins={[
                    rehypeRaw,
                    [rehypeKatex, {
                      throwOnError: false,
                      strict: false,
                    }]
                  ]}
                  components={{
                    // 自定义图片渲染，确保路径正确
                    img: ({ node, ...props }) => (
                      <img
                        {...props}
                        style={{ maxWidth: '100%', height: 'auto' }}
                        onError={(e) => {
                          console.error('Image load error:', props.src, e);
                        }}
                      />
                    ),
                    // 自定义代码块样式
                    code: ({ node, className, children, ...props }) => {
                      // 检查是否是行内代码（没有 language- 前缀）
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
            )}
          </div>
        );

      case 'video':
        return (
          <div style={{ textAlign: 'center', padding: '24px' }}>
            <video
              src={item.url}
              controls
              style={{ maxWidth: '100%', maxHeight: '70vh' }}
            >
              您的浏览器不支持视频播放
            </video>
          </div>
        );

      default:
        return <div style={{ padding: '24px', textAlign: 'center' }}>不支持的文件类型</div>;
    }
  };

  const getTitle = () => {
    if (!item) return '预览';
    const typeNames = {
      image: '图片',
      document: '文档',
      video: '视频',
    };
    return `${typeNames[item.type]}预览 - ${item.name}`;
  };

  return (
    <Modal
      title={getTitle()}
      open={visible}
      onCancel={onClose}
      width="80%"
      style={{ top: 20 }}
      footer={null}
    >
      {renderContent()}
    </Modal>
  );
}

export default PreviewModal;
