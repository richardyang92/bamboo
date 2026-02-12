/**
 * StepItem - 单个步骤渲染组件
 * 显示步骤的状态图标、名称和可选的时间戳
 */
import React from 'react';
import { Space, Typography, Tooltip } from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import type { WorkflowStep } from '../../types';
import dayjs from 'dayjs';

const { Text } = Typography;

interface StepItemProps {
  step: WorkflowStep;
  isActive: boolean;
  showTimestamp?: boolean;
}

const StepItem: React.FC<StepItemProps> = ({ step, isActive, showTimestamp = false }) => {
  // 获取步骤状态图标
  const getStatusIcon = () => {
    switch (step.status) {
      case 'running':
        return <LoadingOutlined spin />;
      case 'completed':
        return <CheckCircleOutlined />;
      case 'error':
        return <CloseCircleOutlined />;
      case 'pending':
      default:
        return <ClockCircleOutlined />;
    }
  };

  // 获取步骤状态颜色
  const getStatusColor = () => {
    switch (step.status) {
      case 'running':
        return '#1890ff';
      case 'completed':
        return '#52c41a';
      case 'error':
        return '#ff4d4f';
      case 'pending':
      default:
        return '#d9d9d9';
    }
  };

  // 格式化时间戳
  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return null;
    return dayjs(timestamp).format('HH:mm:ss');
  };

  const icon = getStatusIcon();
  const color = getStatusColor();

  return (
    <Space size="small">
      <span style={{ color, fontSize: '16px' }}>{icon}</span>
      <Text style={{ color: isActive ? color : undefined, fontWeight: isActive ? 500 : 'normal' }}>
        {step.name}
      </Text>
      {showTimestamp && step.timestamp && (
        <Text type="secondary" style={{ fontSize: '12px' }}>
          {formatTimestamp(step.timestamp)}
        </Text>
      )}
      {step.error && (
        <Tooltip title={step.error}>
          <Text type="danger" style={{ fontSize: '12px', marginLeft: '4px' }}>
            (失败)
          </Text>
        </Tooltip>
      )}
    </Space>
  );
};

export default StepItem;
