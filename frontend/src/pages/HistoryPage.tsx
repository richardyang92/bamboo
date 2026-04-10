import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import * as Dialog from '@radix-ui/react-dialog';
import { Image, FileText, Video, Trash2, Eye, X, History } from 'lucide-react';
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
  image: {
    bg: 'bg-blue-500/20',
    text: 'text-blue-400',
    border: 'border-blue-500/30',
    gradient: 'from-blue-500/20 via-blue-600/10 to-transparent',
    iconBg: 'bg-blue-500/10',
  },
  document: {
    bg: 'bg-emerald-500/20',
    text: 'text-emerald-400',
    border: 'border-emerald-500/30',
    gradient: 'from-emerald-500/20 via-emerald-600/10 to-transparent',
    iconBg: 'bg-emerald-500/10',
  },
  video: {
    bg: 'bg-violet-500/20',
    text: 'text-violet-400',
    border: 'border-violet-500/30',
    gradient: 'from-violet-500/20 via-violet-600/10 to-transparent',
    iconBg: 'bg-violet-500/10',
  },
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
  const colors = typeColors[item.type];

  return (
    <motion.div
      whileHover={{ y: -4 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className="group relative bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden transition-all duration-300 ease-out hover:shadow-xl hover:shadow-black/20 hover:border-cyan-500/30 cursor-pointer"
    >
      <div className="h-40 bg-gradient-to-br from-slate-800/50 to-slate-900/50 flex items-center justify-center overflow-hidden relative">
        {item.type === 'image' ? (
          <img
            src={item.url}
            alt={item.name}
            className="w-full h-full object-cover rounded-t-2xl"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
        ) : (
          <div className={`absolute inset-0 bg-gradient-to-br ${colors.gradient} opacity-60`} />
        )}
        
        {item.type !== 'image' && (
          <div className={`relative z-10 w-16 h-16 ${colors.iconBg} backdrop-blur-sm rounded-2xl flex items-center justify-center border ${colors.border}`}>
            <Icon className={`w-8 h-8 ${colors.text}`} />
          </div>
        )}

        <div className="absolute top-3 left-3 z-10">
          <span className={`text-[11px] px-2.5 py-1 rounded-full font-medium ${colors.bg} ${colors.text} backdrop-blur-sm border ${colors.border}`}>
            {typeLabels[item.type]}
          </span>
        </div>
      </div>

      <div className="p-4">
        <p className="text-sm text-[#f8fafc] truncate font-medium" title={item.name}>
          {item.name}
        </p>
        <div className="flex items-center justify-between mt-2">
          <span className="text-xs text-[#64748b]">{formatSize(item.size)}</span>
          <span className="text-xs text-[#64748b]">{timeAgo(item.created)}</span>
        </div>
      </div>

        <div className="absolute inset-0 z-20 bg-slate-950/60 backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-all duration-200 flex items-center justify-center gap-3 rounded-2xl">
        <button
          onClick={() => onPreview(item)}
          className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-cyan-400 text-white text-sm font-medium rounded-full hover:from-cyan-400 hover:to-cyan-300 transition-all duration-200 flex items-center gap-1.5 shadow-lg shadow-cyan-500/25 cursor-pointer"
        >
          <Eye className="w-4 h-4" />
          预览
        </button>
        <button
          onClick={() => onDelete(item)}
          className="px-4 py-2 bg-rose-500/90 text-white text-sm font-medium rounded-full hover:bg-rose-500 transition-all duration-200 flex items-center gap-1.5 cursor-pointer"
        >
          <Trash2 className="w-4 h-4" />
          删除
        </button>
      </div>
    </motion.div>
  );
}

function SkeletonCard() {
  return (
    <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden">
      <div className="h-40 bg-slate-800/50 animate-pulse" />
      <div className="p-4 space-y-2">
        <div className="h-4 bg-slate-700/50 rounded animate-pulse w-3/4" />
        <div className="flex items-center justify-between">
          <div className="h-3 bg-slate-700/50 rounded animate-pulse w-16" />
          <div className="h-3 bg-slate-700/50 rounded animate-pulse w-12" />
        </div>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="flex flex-col items-center justify-center h-96"
    >
      <div className="relative">
        <div className="absolute inset-0 bg-cyan-500/20 blur-3xl rounded-full" />
        <div className="relative w-20 h-20 bg-gradient-to-br from-cyan-500/30 to-blue-600/20 backdrop-blur-xl rounded-2xl flex items-center justify-center border border-white/10">
          <History className="w-10 h-10 text-cyan-400/80" />
        </div>
      </div>
      <p className="mt-6 text-lg text-[#94a3b8]">暂无历史记录</p>
      <p className="mt-2 text-sm text-[#64748b]">开始创作，你的作品将出现在这里</p>
    </motion.div>
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
        <div className="p-6 h-full overflow-auto flex items-center justify-center">
          <div className="text-center">
            <div className="w-16 h-16 bg-rose-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-rose-500/30">
              <X className="w-8 h-8 text-rose-400" />
            </div>
            <p className="text-[#94a3b8]">加载失败: {error}</p>
          </div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="p-6 h-full overflow-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            {(['all', 'image', 'document', 'video'] as const).map((type) => (
              <button
                key={type}
                onClick={() => setFilter(type)}
                className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-200 cursor-pointer ${
                  filter === type
                    ? 'bg-[#06b6d4] text-white shadow-lg shadow-cyan-500/25'
                    : 'bg-transparent text-[#94a3b8] hover:bg-white/5 hover:text-[#f8fafc]'
                }`}
              >
                {typeLabels[type]}
              </button>
            ))}
          </div>
          <span className="text-sm text-[#64748b]">{filteredItems.length} 项</span>
        </div>

        <AnimatePresence mode="wait">
          {loading ? (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
            >
              {[...Array(8)].map((_, i) => (
                <SkeletonCard key={i} />
              ))}
            </motion.div>
          ) : filteredItems.length === 0 ? (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <EmptyState />
            </motion.div>
          ) : (
            <motion.div
              key="content"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
            >
              {filteredItems.map((item) => (
                <HistoryCard
                  key={item.name}
                  item={item}
                  onPreview={handlePreview}
                  onDelete={handleDelete}
                />
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        <Dialog.Root
          open={!!deleteTarget}
          onOpenChange={(open) => !open && setDeleteTarget(null)}
        >
          <Dialog.Portal>
            <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50" />
            <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-slate-900/90 backdrop-blur-2xl border border-white/10 rounded-2xl p-6 z-50 w-96 shadow-2xl shadow-black/40">
              <Dialog.Title className="text-base font-semibold text-[#f8fafc]">
                确认删除
              </Dialog.Title>
              <Dialog.Description className="mt-3 text-sm text-[#94a3b8]">
                确定要删除 <span className="text-[#f8fafc] font-medium">"{deleteTarget?.name}"</span> 吗？此操作不可撤销。
              </Dialog.Description>
              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => setDeleteTarget(null)}
                  className="px-4 py-2 text-sm text-[#94a3b8] hover:text-[#f8fafc] hover:bg-white/5 rounded-lg transition-all duration-200 cursor-pointer"
                >
                  取消
                </button>
                <button
                  onClick={confirmDelete}
                  className="px-4 py-2 bg-rose-500 hover:bg-rose-600 text-white text-sm font-medium rounded-lg transition-all duration-200 cursor-pointer shadow-lg shadow-rose-500/20"
                >
                  删除
                </button>
              </div>
              <Dialog.Close asChild>
                <button
                  className="absolute top-4 right-4 p-1.5 text-[#64748b] hover:text-[#f8fafc] hover:bg-white/10 rounded-lg transition-all duration-200 cursor-pointer"
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
