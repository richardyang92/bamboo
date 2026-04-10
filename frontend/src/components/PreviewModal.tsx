import { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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

const overlayVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
};

const contentVariants = {
  hidden: { 
    opacity: 0, 
    scale: 0.95,
    y: 10,
  },
  visible: { 
    opacity: 1, 
    scale: 1,
    y: 0,
    transition: {
      duration: 0.3,
      ease: [0.16, 1, 0.3, 1] as const,
    },
  },
  exit: { 
    opacity: 0, 
    scale: 0.95,
    y: 10,
    transition: {
      duration: 0.2,
      ease: 'easeIn' as const,
    },
  },
};

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
          <div className="flex items-center justify-center p-8 bg-slate-950/30">
            <motion.img
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3 }}
              src={item.url}
              alt={item.name}
              className="max-w-full max-h-[70vh] object-contain rounded-xl shadow-2xl shadow-black/50"
            />
          </div>
        );

      case 'document':
        return (
          <div className="p-8 min-h-[400px] bg-slate-950/30">
            {loading ? (
              <div className="flex items-center justify-center py-24">
                <Loader2 className="w-10 h-10 animate-spin text-cyan-500" />
              </div>
            ) : (
              <div className="max-w-4xl mx-auto">
                <MarkdownRenderer content={processedContent} />
              </div>
            )}
          </div>
        );

      case 'video':
        return (
          <div className="flex items-center justify-center p-8 bg-slate-950/30 min-h-[400px]">
            <video
              src={item.url}
              controls
              className="max-w-full max-h-[70vh] rounded-xl shadow-2xl shadow-black/50"
            >
              您的浏览器不支持视频播放
            </video>
          </div>
        );

      default:
        return (
          <div className="flex items-center justify-center p-8 min-h-[400px] text-[#64748b]">
            不支持的文件类型
          </div>
        );
    }
  };

  return (
    <Dialog.Root open={!!item} onOpenChange={(open) => !open && onClose()}>
      <AnimatePresence>
        {item && (
          <Dialog.Portal forceMount>
            <Dialog.Overlay asChild>
              <motion.div
                initial="hidden"
                animate="visible"
                exit="hidden"
                variants={overlayVariants}
                transition={{ duration: 0.2 }}
                className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
              />
            </Dialog.Overlay>
            <Dialog.Content asChild>
              <motion.div
                initial="hidden"
                animate="visible"
                exit="exit"
                variants={contentVariants}
                className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-slate-900/90 backdrop-blur-2xl border border-white/10 rounded-2xl z-50 w-[85%] max-w-5xl max-h-[90vh] flex flex-col shadow-2xl shadow-black/50"
              >
                <Dialog.Title className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-white/5 backdrop-blur-xl rounded-t-2xl">
                  <span className="text-sm font-medium text-[#f8fafc] truncate pr-4">
                    {getTitle()}
                  </span>
                  <Dialog.Close asChild>
                    <button
                      onClick={onClose}
                      className="p-2 text-[#64748b] hover:text-[#f8fafc] hover:bg-white/10 rounded-xl transition-all duration-200 shrink-0 cursor-pointer"
                      aria-label="关闭"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </Dialog.Close>
                </Dialog.Title>
                <div className="flex-1 overflow-auto rounded-b-2xl">
                  {renderContent()}
                </div>
              </motion.div>
            </Dialog.Content>
          </Dialog.Portal>
        )}
      </AnimatePresence>
    </Dialog.Root>
  );
}

export default PreviewModal;
