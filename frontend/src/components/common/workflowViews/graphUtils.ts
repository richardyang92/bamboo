/**
 * 节点图视图工具函数
 */

import type { WorkflowStep } from '../../../types';

/**
 * 获取步骤状态颜色
 */
export const getStatusColor = (status: WorkflowStep['status']): string => {
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

/**
 * 获取步骤状态文本
 */
export const getStatusText = (status: WorkflowStep['status']): string => {
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
