/**
 * StreamControls - 流式内容控制条
 * 提供自动滚动切换和内容统计
 */
import React from 'react';
import { Space, Switch, Typography, Badge } from 'antd';

const { Text } = Typography;

interface StreamControlsProps {
  isScrolling: boolean;
  onToggleScroll: () => void;
  contentLength: number;
  isStreaming: boolean;
  className?: string;
}

// 格式化内容大小
const formatContentLength = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const StreamControls: React.FC<StreamControlsProps> = ({
  isScrolling,
  onToggleScroll,
  contentLength,
  isStreaming,
  className = '',
}) => {
  return (
    <div className={`stream-controls ${className}`} style={{ marginTop: '8px' }}>
      <Space size="middle">
        {/* 自动滚动开关 */}
        <Space size="small">
          <Text style={{ fontSize: '12px' }}>自动滚动</Text>
          <Switch
            size="small"
            checked={isScrolling}
            onChange={onToggleScroll}
            disabled={!isStreaming}
          />
        </Space>

        {/* 内容大小 */}
        <Text type="secondary" style={{ fontSize: '12px' }}>
          内容: {formatContentLength(contentLength)}
        </Text>

        {/* 流式状态指示 */}
        <Badge
          status={isStreaming ? 'processing' : 'default'}
          text={
            <Text style={{ fontSize: '12px' }}>
              {isStreaming ? '接收中...' : '已完成'}
            </Text>
          }
        />
      </Space>
    </div>
  );
};

export default StreamControls;
