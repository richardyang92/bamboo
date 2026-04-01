import { useState, useEffect, useMemo } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { X, Loader2 } from 'lucide-react';
import * as api from '../services/api';
import MarkdownRenderer from './shared/MarkdownRenderer';
import { showToast } from '../services/toast';
import type { HistoryItem } from '../types';

interface PreviewModalProps {
  item: HistoryItem | null;
  onClose: () => void;
}

function PreviewModal({ item, onClose }: PreviewModalProps) {
  const [loading, setLoading] = useState(false);
  const [documentContent, setDocumentContent] = useState('');

  useEffect(() => {
    if (item?.type === 'document') {
      fetchDocumentContent(item.name);
    } else {
      setDocumentContent('');
    }
  }, [item]);

  const fetchDocumentContent = async (filename: string) => {
    setLoading(true);
    try {
      const data = await api.getDocumentContent(filename);
      setDocumentContent(data.content);
    } catch (err) {
      showToast.error(err instanceof Error ? err.message : '获取文档内容失败');
    } finally {
      setLoading(false);
    }
  };

  const processedContent = useMemo(() => {
    if (!documentContent) return '';
    return documentContent.replace(/\.\.\/images\/([^)]+)/g, '/api/images/$1');
  }, [documentContent]);

  const getTitle = () => {
    if (!item) return '预览';
    const typeNames: Record<string, string> = {
      image: '图片',
      document: '文档',
      video: '视频',
    };
    return `${typeNames[item.type]}预览 - ${item.name}`;
  };

  const renderContent = () => {
    if (!item) return null;

    switch (item.type) {
      case 'image':
        return (
          <div className="flex items-center justify-center p-6">
            <img
              src={item.url}
              alt={item.name}
              className="max-w-full max-h-[70vh] object-contain"
            />
          </div>
        );

      case 'document':
        return (
          <div className="p-6 min-h-[400px]">
            {loading ? (
              <div className="flex items-center justify-center py-24">
                <Loader2 className="w-8 h-8 animate-spin text-[var(--color-accent)]" />
              </div>
            ) : (
              <MarkdownRenderer content={processedContent} />
            )}
          </div>
        );

      case 'video':
        return (
          <div className="flex items-center justify-center p-6">
            <video
              src={item.url}
              controls
              className="max-w-full max-h-[70vh]"
            >
              您的浏览器不支持视频播放
            </video>
          </div>
        );

      default:
        return (
          <div className="flex items-center justify-center p-6 text-[var(--color-text-muted)]">
            不支持的文件类型
          </div>
        );
    }
  };

  return (
    <Dialog.Root open={!!item} onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-lg z-50 w-[80%] max-w-4xl max-h-[90vh] flex flex-col">
          <Dialog.Title className="flex items-center justify-between px-4 py-3 border-b border-[var(--color-border)]">
            <span className="text-sm font-medium text-[var(--color-text-primary)] truncate pr-4">
              {getTitle()}
            </span>
            <Dialog.Close asChild>
              <button
                onClick={onClose}
                className="p-1 text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors shrink-0"
                aria-label="关闭"
              >
                <X className="w-4 h-4" />
              </button>
            </Dialog.Close>
          </Dialog.Title>
          <div className="flex-1 overflow-auto">{renderContent()}</div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

export default PreviewModal;
