/**
 * 时间处理工具函数
 * 用于计算和格式化工作流步骤的执行时长
 */

import type { WorkflowStep } from '../types';

/**
 * 计算步骤的执行时长（毫秒）
 * @param step 工作流步骤
 * @returns 执行时长（毫秒），如果无法计算则返回 undefined
 */
export const calculateStepDuration = (step: WorkflowStep): number | undefined => {
  if (!step.timestamp || !step.completed_at) return undefined;

  const start = new Date(step.timestamp).getTime();
  const end = new Date(step.completed_at).getTime();
  const duration = end - start;

  // 过滤异常值（负数或过大值）
  if (duration < 0 || duration > 24 * 60 * 60 * 1000) return undefined;

  return duration;
};

/**
 * 时长显示格式类型
 */
export type DurationFormat = 'ms' | 'seconds' | 'human';

/**
 * 格式化时长显示
 * @param ms 毫秒数
 * @param format 显示格式
 * @returns 格式化后的时长字符串
 */
export const formatDuration = (ms: number, format: DurationFormat = 'human'): string => {
  if (ms < 0) return '0ms';

  switch (format) {
    case 'ms':
      return `${Math.round(ms)}ms`;
    case 'seconds':
      return `${(ms / 1000).toFixed(2)}s`;
    case 'human':
      if (ms < 1000) return `${Math.round(ms)}ms`;
      if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
      const mins = Math.floor(ms / 60000);
      const secs = Math.round((ms % 60000) / 1000);
      return `${mins}m ${secs}s`;
    default:
      return `${ms}ms`;
  }
};

/**
 * 获取相对时间描述
 * @param timestamp ISO 时间戳
 * @returns 相对时间字符串（如"刚刚"、"3秒前"）
 */
export const getRelativeTime = (timestamp: string): string => {
  const now = Date.now();
  const time = new Date(timestamp).getTime();
  const diff = now - time;

  if (diff < 0) return '未来';
  if (diff < 1000) return '刚刚';
  if (diff < 60000) return `${Math.floor(diff / 1000)}秒前`;
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
  return `${Math.floor(diff / 86400000)}天前`;
};

/**
 * 格式化时间戳为 HH:mm:ss 格式
 * @param timestamp ISO 时间戳
 * @returns 格式化后的时间字符串
 */
export const formatTimestamp = (timestamp?: string): string => {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  return `${hours}:${minutes}:${seconds}`;
};

/**
 * 根据时长获取颜色
 * @param ms 毫秒数
 * @returns CSS 颜色值
 */
export const getDurationColor = (ms: number): string => {
  if (ms < 1000) return '#52c41a'; // 绿色 - 快速
  if (ms < 5000) return '#1890ff'; // 蓝色 - 正常
  if (ms < 15000) return '#faad14'; // 橙色 - 较慢
  return '#ff4d4f'; // 红色 - 很慢
};

/**
 * 计算步骤总数中完成的数量
 * @param steps 步骤数组
 * @returns [已完成数, 总数]
 */
export const getStepCounts = (steps: WorkflowStep[]): [number, number] => {
  const completed = steps.filter(s => s.status === 'completed').length;
  return [completed, steps.length];
};

/**
 * 获取步骤的进度百分比
 * @param steps 步骤数组
 * @returns 0-100 的百分比
 */
export const getStepProgress = (steps: WorkflowStep[]): number => {
  const [completed, total] = getStepCounts(steps);
  return total > 0 ? Math.round((completed / total) * 100) : 0;
};
