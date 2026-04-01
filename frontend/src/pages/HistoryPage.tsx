import { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { Image, FileText, Video, Trash2, Eye, X } from 'lucide-react';
import { useWorkflowHistory } from '../hooks/useWorkflowHistory';
import AppLayout from '../components/layout/AppLayout';
import PreviewModal from '../components/PreviewModal';
import { showToast } from '../services/toast';
import type { HistoryItem } from '../types';

const formatSize = (bytes: number): string => {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
};

const timeAgo = (timestamp: number): string => {
  const seconds = Math.floor((Date.now() - timestamp * 1000) / 1000);
  if (seconds < 60) return '刚刚';
  if (seconds < 3600) return Math.floor(seconds / 60) + '分钟前';
  if (seconds < 86400) return Math.floor(seconds / 3600) + '小时前';
  return Math.floor(seconds / 86400) + '天前';
};

const typeIcons = {
  image: Image,
  document: FileText,
  video: Video,
};

const typeColors = {
  image: 'text-blue-400',
  document: 'text-green-400',
  video: 'text-purple-400',
};

const typeLabels = {
  all: '全部',
  image: '图片',
  document: '文档',
  video: '视频',
};

interface HistoryCardProps {
  item: HistoryItem;
  onPreview: (item: HistoryItem) => void;
  onDelete: (item: HistoryItem) => void;
}

function HistoryCard({ item, onPreview, onDelete }: HistoryCardProps) {
  const Icon = typeIcons[item.type];

  return (
    <div className="group relative rounded-md border border-[var(--color-border)] bg-[var(--color-bg-card)] overflow-hidden hover:border-[var(--color-text-muted)] transition-colors">
      <div className="h-32 bg-[var(--color-bg-dark)] flex items-center justify-center">
        {item.type === 'image' ? (
          <img
            src={item.url}
            alt={item.name}
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
        ) : (
          <Icon className={`w-10 h-10 ${typeColors[item.type]} opacity-50`} />
        )}
      </div>

      <div className="p-2">
        <div className="flex items-center gap-1.5 mb-1">
          <span
            className={`text-[10px] px-1.5 py-0.5 rounded-full ${
              item.type === 'image'
                ? 'bg-blue-500/20 text-blue-400'
                : item.type === 'document'
                ? 'bg-green-500/20 text-green-400'
                : 'bg-purple-500/20 text-purple-400'
            }`}
          >
            {typeLabels[item.type]}
          </span>
        </div>
        <p className="text-xs text-[var(--color-text-primary)] truncate" title={item.name}>
          {item.name}
        </p>
        <div className="flex items-center justify-between mt-1">
          <span className="text-[10px] text-[var(--color-text-muted)]">{formatSize(item.size)}</span>
          <span className="text-[10px] text-[var(--color-text-muted)]">{timeAgo(item.created)}</span>
        </div>
      </div>

      <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
        <button
          onClick={() => onPreview(item)}
          className="px-3 py-1.5 bg-[var(--color-accent)] text-white text-xs rounded-md hover:bg-green-600 transition-colors flex items-center gap-1"
        >
          <Eye className="w-3 h-3" />
          预览
        </button>
        <button
          onClick={() => onDelete(item)}
          className="px-3 py-1.5 bg-red-500 text-white text-xs rounded-md hover:bg-red-600 transition-colors flex items-center gap-1"
        >
          <Trash2 className="w-3 h-3" />
          删除
        </button>
      </div>
    </div>
  );
}

function HistoryPage() {
  const { history, loading, error, deleteItem } = useWorkflowHistory();
  const [filter, setFilter] = useState<'all' | 'image' | 'document' | 'video'>('all');
  const [previewItem, setPreviewItem] = useState<HistoryItem | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<HistoryItem | null>(null);

  const filteredItems = history.filter((item) => {
    if (filter === 'all') return true;
    return item.type === filter;
  });

  const handlePreview = (item: HistoryItem) => {
    setPreviewItem(item);
  };

  const handleDelete = (item: HistoryItem) => {
    setDeleteTarget(item);
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;

    try {
      await deleteItem(deleteTarget.type, deleteTarget.name);
      showToast.success('删除成功');
    } catch (err) {
      showToast.error(err instanceof Error ? err.message : '删除失败');
    } finally {
      setDeleteTarget(null);
    }
  };

  if (error) {
    return (
      <AppLayout>
        <div className="p-4 h-full overflow-auto flex items-center justify-center">
          <div className="text-center">
            <p className="text-[var(--color-text-secondary)]">加载失败: {error}</p>
          </div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="p-4 h-full overflow-auto">
        <div className="flex items-center gap-2 mb-4">
          {(['all', 'image', 'document', 'video'] as const).map((type) => (
            <button
              key={type}
              onClick={() => setFilter(type)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors
                ${
                  filter === type
                    ? 'bg-[var(--color-accent)] text-white'
                    : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-secondary)] hover:text-[var(--color-text-primary)]'
                }`}
            >
              {typeLabels[type]}
            </button>
          ))}
          <span className="text-xs text-[var(--color-text-muted)] ml-auto">{filteredItems.length} 项</span>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-[var(--color-text-muted)]">加载中...</div>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <p className="text-[var(--color-text-muted)]">暂无历史记录</p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {filteredItems.map((item) => (
              <HistoryCard
                key={item.name}
                item={item}
                onPreview={handlePreview}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}

        <Dialog.Root
          open={!!deleteTarget}
          onOpenChange={(open) => !open && setDeleteTarget(null)}
        >
          <Dialog.Portal>
            <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
            <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-lg p-6 z-50 w-80">
              <Dialog.Title className="text-sm font-medium text-[var(--color-text-primary)]">
                确认删除
              </Dialog.Title>
              <Dialog.Description className="mt-2 text-sm text-[var(--color-text-secondary)]">
                确定要删除 "{deleteTarget?.name}" 吗？此操作不可撤销。
              </Dialog.Description>
              <div className="flex justify-end gap-2 mt-4">
                <button
                  onClick={() => setDeleteTarget(null)}
                  className="px-3 py-1.5 text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={confirmDelete}
                  className="px-3 py-1.5 bg-red-500 text-white text-sm rounded-md hover:bg-red-600 transition-colors"
                >
                  删除
                </button>
              </div>
              <Dialog.Close asChild>
                <button
                  className="absolute top-2 right-2 p-1 text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
                  aria-label="关闭"
                  onClick={() => setDeleteTarget(null)}
                >
                  <X className="w-4 h-4" />
                </button>
              </Dialog.Close>
            </Dialog.Content>
          </Dialog.Portal>
        </Dialog.Root>

        <PreviewModal
          item={previewItem}
          onClose={() => setPreviewItem(null)}
        />
      </div>
    </AppLayout>
  );
}

export default HistoryPage;
