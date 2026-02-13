/**
 * Custom React Flow Node Component
 * Preserves all visual features from the original SVG-based implementation
 */

import React, { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import type { NodeProps } from '@xyflow/react';
import type { WorkflowNodeData } from '../../../types';
import './ReactFlowCustomNode.css';

const WorkflowCustomNode = memo((props: NodeProps) => {
  const data = props.data as WorkflowNodeData;
  const { selected } = props;

  const {
    label,
    type: nodeType,
    status = 'pending',
    retryInfo,
  } = data;

  // Status color mapping
  const statusColor = {
    pending: '#d9d9d9',
    running: '#1890ff',
    completed: '#52c41a',
    error: '#ff4d4f',
  }[status];

  // Render node type icon
  const renderNodeIcon = () => {
    const iconColor = status === 'completed' ? statusColor : '#d9d9d9';

    switch (nodeType) {
      case 'start':
        return (
          <circle cx="20" cy="20" r="8" fill={iconColor} className="node-icon" />
        );
      case 'decision':
        return (
          <polygon
            points="15,20 25,10 35,20 25,30"
            fill={iconColor}
            className="node-icon"
          />
        );
      case 'end':
        return (
          <circle
            cx="20"
            cy="20"
            r="8"
            fill="none"
            stroke={iconColor}
            strokeWidth="2"
            className="node-icon"
          />
        );
      case 'retry':
        return (
          <path
            d="M 15 20 L 25 20 M 20 15 L 25 20 L 20 25"
            stroke={iconColor}
            strokeWidth="2"
            fill="none"
            className="node-icon"
          />
        );
      default:
        return null;
    }
  };

  // Status text mapping
  const getStatusText = () => {
    switch (status) {
      case 'running':
        return '执行中...';
      case 'completed':
        return '已完成';
      case 'error':
        return '失败';
      case 'pending':
      default:
        return '等待中';
    }
  };

  // Retry badge
  const hasRetry = retryInfo && retryInfo.current > 0;

  return (
    <div
      className={`workflow-node ${status} ${selected ? 'selected' : ''} ${nodeType}`}
    >
      {/* Node SVG */}
      <svg width="180" height="60" className="node-svg">
        {/* Shadow */}
        <rect
          x="2"
          y="2"
          width="176"
          height="56"
          rx="8"
          fill="rgba(0,0,0,0.05)"
        />

        {/* Background */}
        <rect
          x="0"
          y="0"
          width="176"
          height="56"
          rx="8"
          fill="white"
          stroke={statusColor}
          strokeWidth={status === 'running' ? 2.5 : 1.5}
          className="node-rect"
        />

        {/* Icon */}
        {renderNodeIcon()}

        {/* Label */}
        <text
          x="45"
          y="25"
          fill="#262626"
          fontSize="12"
          fontWeight={status === 'running' ? 500 : 400}
          className="node-label"
        >
          {label}
        </text>

        {/* Status text */}
        <text
          x="45"
          y="42"
          fill="#8c8c8c"
          fontSize="10"
          className="node-status-text"
        >
          {getStatusText()}
        </text>

        {/* Retry badge */}
        {hasRetry && (
          <g className="retry-badge">
            <rect x="130" y="5" width="40" height="16" rx="4" fill="#fa8c16" />
            <text
              x="150"
              y="16"
              textAnchor="middle"
              fill="white"
              fontSize="9"
              fontWeight="bold"
            >
              {retryInfo.current}/{retryInfo.max}
            </text>
          </g>
        )}
      </svg>

      {/* Running animation overlay */}
      {status === 'running' && (
        <div className="pulse-animation">
          <div className="pulse-circle"></div>
        </div>
      )}

      {/* Connection handles */}
      <Handle
        type="target"
        position={Position.Top}
        className="custom-handle"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="custom-handle"
      />
    </div>
  );
}) as React.FC<NodeProps>;

WorkflowCustomNode.displayName = 'WorkflowCustomNode';

export default WorkflowCustomNode;
