/**
 * WorkflowNodeCard - 工作流节点卡片组件
 * 可复用的节点卡片，用于卡片列表视图和时间线视图
 */
import React from 'react';
import { Card, Tag, Collapse, Space, Typography } from 'antd';
import {
  CheckCircleFilled,
  CloseCircleFilled,
  LoadingOutlined,
  ClockCircleFilled,
} from '@ant-design/icons';
import type { WorkflowStep } from '../../../types';
import {
  formatDuration,
  formatTimestamp,
  getDurationColor,
} from '../../../utils/timeUtils';
import './WorkflowNodeCard.css';

const { Text } = Typography;

interface WorkflowNodeCardProps {
  step: WorkflowStep;
  isExpanded?: boolean;
  onToggle?: () => void;
  compact?: boolean;
  showStreamContentLink?: boolean;
  onStreamContentClick?: () => void;
  className?: string;
}

// 获取步骤状态颜色
const getStatusColor = (status: WorkflowStep['status']): string => {
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

// 获取步骤状态文本
const getStatusText = (status: WorkflowStep['status']): string => {
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

// 获取步骤图标
const getStepIcon = (status: WorkflowStep['status'], size = 16) => {
  const color = getStatusColor(status);

  if (status === 'running') {
    return <LoadingOutlined style={{ fontSize: size, color }} spin />;
  }
  if (status === 'completed') {
    return <CheckCircleFilled style={{ fontSize: size, color }} />;
  }
  if (status === 'error') {
    return <CloseCircleFilled style={{ fontSize: size, color }} />;
  }
  return <ClockCircleFilled style={{ fontSize: size, color }} />;
};

const WorkflowNodeCard: React.FC<WorkflowNodeCardProps> = ({
  step,
  isExpanded = false,
  onToggle,
  compact = false,
  showStreamContentLink = false,
  onStreamContentClick,
  className = '',
}) => {
  const statusColor = getStatusColor(step.status);
  const duration = step.completed_at && step.timestamp
    ? new Date(step.completed_at).getTime() - new Date(step.timestamp).getTime()
    : undefined;

  const isRunning = step.status === 'running';

  // 展开内容
  const expandedContent = (
    <div className="node-card-details">
      {/* 时间信息 */}
      <Space direction="vertical" size="small" style={{ width: '100%' }}>
        {(step.timestamp || step.completed_at) && (
          <Space size="middle" wrap={false}>
            {step.timestamp && (
              <Text type="secondary" style={{ fontSize: '12px' }}>
                开始: {formatTimestamp(step.timestamp)}
              </Text>
            )}
            {step.completed_at && (
              <Text type="secondary" style={{ fontSize: '12px' }}>
                完成: {formatTimestamp(step.completed_at)}
              </Text>
            )}
          </Space>
        )}
        {duration !== undefined && (
          <Tag
            color={getDurationColor(duration)}
            style={{ margin: 0, fontSize: '11px' }}
          >
            耗时: {formatDuration(duration)}
          </Tag>
        )}
      </Space>

      {/* 错误信息 */}
      {step.error && (
        <Collapse
          ghost
          items={[
            {
              key: 'error',
              label: <Text type="danger" style={{ fontSize: '12px' }}>查看错误详情</Text>,
              children: (
                <pre className="error-stack">
                  <code>{step.error}</code>
                </pre>
              ),
            },
          ]}
          style={{ marginTop: '12px' }}
        />
      )}

      {/* 流式内容链接 */}
      {showStreamContentLink && onStreamContentClick && (step.status === 'running' || step.status === 'completed') && (
        <Text
          type="secondary"
          style={{ fontSize: '12px', cursor: 'pointer', textDecoration: 'underline' }}
          onClick={onStreamContentClick}
        >
          查看流式内容 →
        </Text>
      )}
    </div>
  );

  return (
    <Card
      className={`workflow-node-card ${compact ? 'compact' : ''} ${isRunning ? 'running' : ''} ${className}`}
      size={compact ? 'small' : 'default'}
      hoverable
      onClick={onToggle}
      style={{
        borderColor: isRunning ? statusColor : undefined,
        transition: 'all 0.3s ease',
      }}
    >
      {/* 卡片头部 */}
      <Space size="small" style={{ width: '100%', justifyContent: 'space-between' }}>
        <Space size="small">
          {getStepIcon(step.status, compact ? 14 : 16)}
          <Text
            strong
            style={{
              fontSize: compact ? '13px' : '14px',
              color: step.status === 'error' ? '#ff4d4f' : undefined,
            }}
          >
            {step.name}
            {/* CodeAct 模式：显示重试信息 */}
            {step.retry_info && step.retry_info.current > 0 && (
              <Tag
                color="orange"
                style={{
                  fontSize: '11px',
                  marginLeft: '8px',
                  lineHeight: '20px'
                }}
              >
                重试 {step.retry_info.current}/{step.retry_info.max}
              </Tag>
            )}
          </Text>
          {isRunning && (
            <Tag color="processing" style={{ fontSize: '11px', margin: 0 }}>
              {getStatusText(step.status)}
            </Tag>
          )}
        </Space>

        {/* 时长徽章（在头部显示） */}
        {duration !== undefined && !isExpanded && (
          <Tag
            color={getDurationColor(duration)}
            style={{ fontSize: '11px', margin: 0 }}
          >
            {formatDuration(duration, 'seconds')}
          </Tag>
        )}
      </Space>

      {/* 展开的详细内容 */}
      {isExpanded && expandedContent}
    </Card>
  );
};

export default React.memo(WorkflowNodeCard);
