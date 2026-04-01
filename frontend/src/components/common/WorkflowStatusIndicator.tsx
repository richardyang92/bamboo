import React from 'react';
import { Wifi, WifiOff, Loader2 } from 'lucide-react';
import type { WorkflowType, WorkflowStatusType } from '../../types';

type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'reconnecting';

interface WorkflowStatusIndicatorProps {
  workflowStatus: WorkflowStatusType;
  connectionState: ConnectionState;
  workflowType: WorkflowType;
  reconnectAttempts?: number;
  className?: string;
}

const workflowStatusConfig: Record<WorkflowStatusType, { dotClass: string; text: string }> = {
  idle: { dotClass: 'bg-gray-400', text: '空闲' },
  running: { dotClass: 'bg-green-400 animate-pulse', text: '运行中' },
  completed: { dotClass: 'bg-blue-400', text: '已完成' },
  error: { dotClass: 'bg-red-400', text: '出错' },
  stopped: { dotClass: 'bg-orange-400', text: '已停止' },
};

const connectionStatusConfig: Record<ConnectionState, { dotClass: string; text: string; icon: React.ReactNode }> = {
  connected: { dotClass: 'bg-green-400', text: '已连接', icon: <Wifi className="w-3 h-3 text-green-400" /> },
  connecting: { dotClass: 'bg-gray-400 animate-pulse', text: '连接中...', icon: <Loader2 className="w-3 h-3 text-gray-400 animate-spin" /> },
  disconnected: { dotClass: 'bg-red-400', text: '未连接', icon: <WifiOff className="w-3 h-3 text-red-400" /> },
  reconnecting: { dotClass: 'bg-orange-400 animate-pulse', text: '重连中...', icon: <Loader2 className="w-3 h-3 text-orange-400 animate-spin" /> },
};

const workflowTypeNames: Record<WorkflowType, string> = {
  drawing: '绘图',
  document_with_images: '文档',
  manim: '动画',
};

const WorkflowStatusIndicator: React.FC<WorkflowStatusIndicatorProps> = ({
  workflowStatus,
  connectionState,
  workflowType,
  reconnectAttempts = 0,
  className = '',
}) => {
  const wfConfig = workflowStatusConfig[workflowStatus];
  const connConfig = connectionStatusConfig[connectionState];
  const reconnectInfo = reconnectAttempts > 0 ? ` (${reconnectAttempts}/5)` : '';

  return (
    <span className={`inline-flex items-center gap-3 ${className}`}>
      <span className="inline-flex items-center gap-1.5 cursor-default" title={`工作流状态: ${wfConfig.text}`}>
        <span className={`w-2 h-2 rounded-full ${wfConfig.dotClass}`} />
        <span className="text-xs text-[var(--color-text-muted)]">
          {workflowTypeNames[workflowType]}: {wfConfig.text}
        </span>
      </span>

      <span className="inline-flex items-center gap-1.5 cursor-default" title={`WebSocket: ${connConfig.text}${reconnectInfo}`}>
        {connConfig.icon}
        <span className="text-xs text-[var(--color-text-muted)]">
          {connConfig.text}{reconnectInfo}
        </span>
      </span>
    </span>
  );
};

export default WorkflowStatusIndicator;
