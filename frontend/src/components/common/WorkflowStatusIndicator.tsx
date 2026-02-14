/**
 * WorkflowStatusIndicator - 工作流和连接状态指示器
 * 显示工作流执行状态和WebSocket连接状态
 */
import React from 'react';
import { Badge, Space, Typography, Tooltip } from 'antd';
import {
  LoadingOutlined,
  WifiOutlined,
  DisconnectOutlined,
} from '@ant-design/icons';
import type { WorkflowType, WorkflowStatusType } from '../../types';

const { Text } = Typography;

// 连接状态类型（临时定义，稍后会移到types/index.ts）
type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'reconnecting';

interface WorkflowStatusIndicatorProps {
  workflowStatus: WorkflowStatusType;
  connectionState: ConnectionState;
  workflowType: WorkflowType;
  reconnectAttempts?: number;
  className?: string;
}

// 工作流状态映射
const workflowStatusConfig: Record<WorkflowStatusType, { status: 'success' | 'processing' | 'error' | 'default' | 'warning'; text: string }> = {
  idle: { status: 'default', text: '空闲' },
  running: { status: 'processing', text: '运行中' },
  completed: { status: 'success', text: '已完成' },
  error: { status: 'error', text: '出错' },
  stopped: { status: 'warning', text: '已停止' },
};

// 连接状态映射
const connectionStatusConfig: Record<ConnectionState, { status: 'success' | 'error' | 'default' | 'warning'; text: string; icon: React.ReactNode }> = {
  connected: { status: 'success', text: '已连接', icon: <WifiOutlined /> },
  connecting: { status: 'default', text: '连接中...', icon: <LoadingOutlined spin /> },
  disconnected: { status: 'error', text: '未连接', icon: <DisconnectOutlined /> },
  reconnecting: { status: 'warning', text: '重连中...', icon: <LoadingOutlined spin /> },
};

const WorkflowStatusIndicator: React.FC<WorkflowStatusIndicatorProps> = ({
  workflowStatus,
  connectionState,
  workflowType,
  reconnectAttempts = 0,
  className = '',
}) => {
  const workflowConfig = workflowStatusConfig[workflowStatus];
  const connectionConfig = connectionStatusConfig[connectionState];

  // 工作流类型显示名称
  const workflowTypeNames: Record<WorkflowType, string> = {
    drawing: '绘图',
    document_with_images: '文档',
    manim: '动画',
  };

  // 重连信息
  const reconnectInfo = reconnectAttempts > 0 ? ` (${reconnectAttempts}/${5})` : '';

  return (
    <Space className={`workflow-status-indicator ${className}`} size="middle">
      {/* 工作流状态 */}
      <Tooltip title={`工作流状态: ${workflowConfig.text}`}>
        <Badge
          status={workflowConfig.status}
          text={
            <Text style={{ fontSize: '12px' }}>
              {workflowTypeNames[workflowType]}: {workflowConfig.text}
            </Text>
          }
        />
      </Tooltip>

      {/* 连接状态 */}
      <Tooltip title={`WebSocket: ${connectionConfig.text}${reconnectInfo}`}>
        <Space size="small">
          {connectionConfig.icon}
          <Text style={{ fontSize: '12px' }}>
            {connectionConfig.text}
            {reconnectInfo}
          </Text>
        </Space>
      </Tooltip>
    </Space>
  );
};

export default WorkflowStatusIndicator;
