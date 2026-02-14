/**
 * Custom React Flow Edge Component
 * Supports different edge types with labels and proper styling
 */

import React, { memo } from 'react';
import {
  getBezierPath,
  EdgeLabelRenderer,
} from '@xyflow/react';
import type { EdgeProps } from '@xyflow/react';
import type { WorkflowEdgeData } from '../../../types';
import './ReactFlowCustomEdge.css';

const WorkflowCustomEdge = memo((props: EdgeProps) => {
  const {
    id,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    data,
    selected,
    style,
  } = props;

  const edgeData = data as WorkflowEdgeData;
  const edgeType = edgeData?.type || 'default';
  const label = edgeData?.label;
  const condition = edgeData?.condition;

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  // Color based on edge type and condition
  const getStrokeColor = () => {
    if (edgeType === 'conditional') {
      // 条件边根据 condition 字段区分颜色
      return condition === 'no_images' ? '#8c8c8c' : '#1890ff';  // 跳过路径用灰色，正常路径用蓝色
    }
    return {
      success: '#52c41a',
      failure: '#ff4d4f',
      retry: '#fa8c16',
      default: '#d9d9d9',
    }[edgeType];
  };
  const strokeColor = getStrokeColor();

  return (
    <>
      <path
        id={id}
        d={edgePath}
        fill="none"
        stroke={strokeColor}
        strokeWidth={selected ? 2.5 : 1.5}
        strokeDasharray={edgeType === 'conditional' ? '5,5' : 'none'}
        className={`custom-edge ${edgeType} ${selected ? 'selected' : ''}`}
        style={style}
      />

      {/* Arrow marker */}
      <defs>
        <marker
          id={`arrowhead-${id}`}
          markerWidth="10"
          markerHeight="7"
          refX="9"
          refY="3.5"
          orient="auto"
        >
          <polygon
            points="0 0, 10 3.5, 0 7"
            fill={strokeColor}
          />
        </marker>
      </defs>

      {/* Edge label */}
      {label && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
              background: 'white',
              padding: '2px 8px',
              borderRadius: '4px',
              fontSize: '11px',
              color: strokeColor,
              fontWeight: 500,
              pointerEvents: 'all',
              border: `1px solid ${strokeColor}40`,
              boxShadow: '0 2px 4px rgba(0, 0, 0, 0.08)',
            }}
            className="edge-label"
          >
            {label}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}) as React.FC<EdgeProps>;

WorkflowCustomEdge.displayName = 'WorkflowCustomEdge';

export default WorkflowCustomEdge;
