import { useState, useEffect } from 'react';
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

const workflowStatusConfig: Record<WorkflowStatusType, { 
  bg: string; 
  border: string;
  text: string;
  dot: string;
  pulse?: boolean;
}> = {
  idle: { 
    bg: 'bg-[rgba(100,116,139,0.15)]', 
    border: 'border-[rgba(100,116,139,0.2)]',
    text: 'text-[#94a3b8]', 
    dot: 'bg-[#64748b]' 
  },
  running: { 
    bg: 'bg-[rgba(245,158,11,0.15)]', 
    border: 'border-[rgba(245,158,11,0.3)]',
    text: 'text-[#f59e0b]', 
    dot: 'bg-[#f59e0b]',
    pulse: true 
  },
  completed: { 
    bg: 'bg-[rgba(16,185,129,0.15)]', 
    border: 'border-[rgba(16,185,129,0.2)]',
    text: 'text-[#10b981]', 
    dot: 'bg-[#10b981]' 
  },
  error: { 
    bg: 'bg-[rgba(244,63,94,0.15)]', 
    border: 'border-[rgba(244,63,94,0.2)]',
    text: 'text-[#f43f5e]', 
    dot: 'bg-[#f43f5e]' 
  },
  stopped: { 
    bg: 'bg-[rgba(249,115,22,0.15)]', 
    border: 'border-[rgba(249,115,22,0.2)]',
    text: 'text-[#f97316]', 
    dot: 'bg-[#f97316]' 
  },
};

const connectionStatusConfig: Record<ConnectionState, { 
  bg: string;
  border: string;
  text: string;
  icon: React.ReactNode;
  pulse?: boolean;
}> = {
  connected: { 
    bg: 'bg-[rgba(16,185,129,0.15)]',
    border: 'border-[rgba(16,185,129,0.2)]',
    text: 'text-[#10b981]', 
    icon: <Wifi className="w-3 h-3 text-[#10b981]" /> 
  },
  connecting: { 
    bg: 'bg-[rgba(100,116,139,0.15)]',
    border: 'border-[rgba(100,116,139,0.2)]',
    text: 'text-[#94a3b8]', 
    icon: <Loader2 className="w-3 h-3 text-[#94a3b8] animate-spin" />,
    pulse: true 
  },
  disconnected: { 
    bg: 'bg-[rgba(244,63,94,0.15)]',
    border: 'border-[rgba(244,63,94,0.2)]',
    text: 'text-[#f43f5e]', 
    icon: <WifiOff className="w-3 h-3 text-[#f43f5e]" /> 
  },
  reconnecting: { 
    bg: 'bg-[rgba(249,115,22,0.15)]',
    border: 'border-[rgba(249,115,22,0.2)]',
    text: 'text-[#f97316]', 
    icon: <Loader2 className="w-3 h-3 text-[#f97316] animate-spin" />,
    pulse: true 
  },
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
  const [showCompletedFlash, setShowCompletedFlash] = useState(false);
  const wfConfig = workflowStatusConfig[workflowStatus];
  const connConfig = connectionStatusConfig[connectionState];
  const reconnectInfo = reconnectAttempts > 0 ? ` ${reconnectAttempts}/5` : '';

  useEffect(() => {
    if (workflowStatus === 'completed') {
      setShowCompletedFlash(true);
      const timer = setTimeout(() => setShowCompletedFlash(false), 300);
      return () => clearTimeout(timer);
    }
  }, [workflowStatus]);

  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <span 
        className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full
          ${wfConfig.bg} ${wfConfig.border} border
          backdrop-blur-sm cursor-default`}
        title={`工作流状态: ${workflowStatus === 'idle' ? '空闲' : workflowStatus === 'running' ? '运行中' : workflowStatus === 'completed' ? '已完成' : workflowStatus === 'error' ? '出错' : '已停止'}`}
      >
        <span className={`w-1.5 h-1.5 rounded-full ${wfConfig.dot} ${wfConfig.pulse ? 'animate-[subtle-pulse_2s_ease-in-out_infinite]' : ''} ${showCompletedFlash ? 'animate-[scale-flash_0.3s_ease-out]' : ''}`} />
        <span className={`text-[11px] font-medium ${wfConfig.text}`}>
          {workflowTypeNames[workflowType]}
        </span>
      </span>

      <span 
        className={`inline-flex items-center gap-1 px-2 py-1 rounded-full
          ${connConfig.bg} ${connConfig.border} border
          backdrop-blur-sm cursor-default`}
        title={`WebSocket: ${connectionState === 'connected' ? '已连接' : connectionState === 'connecting' ? '连接中' : connectionState === 'disconnected' ? '未连接' : '重连中'}${reconnectInfo}`}
      >
        {connConfig.icon}
        <span className={`text-[11px] font-medium ${connConfig.text}`}>
          {connectionState === 'connected' ? '已连接' : connectionState === 'connecting' ? '连接中' : connectionState === 'disconnected' ? '未连接' : '重连中'}{reconnectInfo}
        </span>
      </span>
    </span>
  );
};

export default WorkflowStatusIndicator;
