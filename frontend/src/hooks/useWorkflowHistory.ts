/**
 * useWorkflowHistory Hook
 * 用于获取和管理工作流历史记录
 */
import { useState, useEffect, useCallback } from 'react';
import * as api from '../services/api';
import type { HistoryItem } from '../types';

interface UseWorkflowHistoryReturn {
  history: HistoryItem[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  deleteItem: (type: string, filename: string) => Promise<void>;
}

export function useWorkflowHistory(): UseWorkflowHistoryReturn {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 获取历史记录
  const fetchHistory = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listHistory();
      setHistory(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取历史记录失败');
    } finally {
      setLoading(false);
    }
  }, []);

  // 删除项目
  const deleteItem = useCallback(async (type: string, filename: string) => {
    try {
      if (type === 'image') {
        await api.deleteImage(filename);
      } else if (type === 'document') {
        await api.deleteDocument(filename);
      } else if (type === 'video') {
        await api.deleteVideo(filename);
      }
      // 刷新历史记录
      await fetchHistory();
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : '删除失败');
    }
  }, [fetchHistory]);

  // 组件挂载时获取历史记录
  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  return {
    history,
    loading,
    error,
    refresh: fetchHistory,
    deleteItem,
  };
}

export default useWorkflowHistory;
