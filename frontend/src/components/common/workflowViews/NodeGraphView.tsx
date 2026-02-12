/**
 * NodeGraphView - 可视化节点图视图
 * 使用 SVG 渲染工作流节点的流程图
 */
import React, { useMemo } from 'react';
import type { WorkflowStep, GraphLayoutNode } from '../../../types';
import { getStatusColor } from './graphUtils';
import './NodeGraphView.css';

interface NodeGraphViewProps {
  steps: WorkflowStep[];
  currentStep?: string;
  onNodeClick?: (stepId: string) => void;
  className?: string;
}

// 简单的分层布局算法
const calculateLayout = (steps: WorkflowStep[]): GraphLayoutNode[] => {
  const nodesPerRow = 2; // 每行最多2个节点
  const nodeWidth = 180;
  const nodeHeight = 60;
  const horizontalGap = 60;
  const verticalGap = 80;

  return steps.map((step, index) => {
    const row = Math.floor(index / nodesPerRow);
    const col = index % nodesPerRow;

    return {
      id: step.step,
      position: {
        x: col * (nodeWidth + horizontalGap) + 20,
        y: row * (nodeHeight + verticalGap) + 20,
      },
      connections: {
        from: index > 0 ? steps[index - 1].step : undefined,
        to: index < steps.length - 1 ? steps[index + 1].step : undefined,
      },
    };
  });
};

// 计算 SVG 画布大小
const calculateCanvasSize = (nodes: GraphLayoutNode[]): { width: number; height: number } => {
  if (nodes.length === 0) return { width: 400, height: 300 };

  const maxX = Math.max(...nodes.map(n => n.position.x));
  const maxY = Math.max(...nodes.map(n => n.position.y));

  return {
    width: Math.max(400, maxX + 220),
    height: Math.max(300, maxY + 140),
  };
};

const NodeGraphView: React.FC<NodeGraphViewProps> = ({
  steps,
  currentStep = '',
  onNodeClick,
  className = '',
}) => {
  const layoutNodes = useMemo(() => calculateLayout(steps), [steps]);
  const canvasSize = useMemo(() => calculateCanvasSize(layoutNodes), [layoutNodes]);

  // 创建节点映射以便查找
  const stepMap = useMemo(() => {
    const map = new Map<string, WorkflowStep>();
    steps.forEach(step => map.set(step.step, step));
    return map;
  }, [steps]);

  // 渲染连接线
  const renderConnections = () => {
    return layoutNodes.map((node, index) => {
      if (!node.connections.to) return null;

      const fromNode = node;
      const toNode = layoutNodes.find(n => n.id === node.connections.to);
      if (!toNode) return null;

      const isOnActivePath =
        (fromNode.id === currentStep) ||
        (toNode.id === currentStep) ||
        (steps.find(s => s.step === currentStep)?.status === 'completed' &&
         steps.findIndex(s => s.step === fromNode.id) < steps.findIndex(s => s.step === currentStep));

      const fromX = fromNode.position.x + 90; // 节点宽度的一半
      const fromY = fromNode.position.y + 30; // 节点高度的一半
      const toX = toNode.position.x;
      const toY = toNode.position.y + 30;

      // 计算节点间的水平距离
      const deltaX = toX - fromX;

      // 优化的贝塞尔曲线控制点
      // 使用水平距离的 35-50% 作为控制点偏移，使曲线更平滑
      const controlOffset = Math.max(Math.abs(deltaX) * 0.4, 30);
      const controlX1 = fromX + controlOffset;
      const controlY1 = fromY;
      const controlX2 = toX - controlOffset;
      const controlY2 = toY;

      return (
        <g key={`connection-${index}`}>
          <path
            d={`M ${fromX} ${fromY} C ${controlX1} ${controlY1}, ${controlX2} ${controlY2}, ${toX} ${toY}`}
            fill="none"
            stroke={isOnActivePath ? '#1890ff' : '#d9d9d9'}
            strokeWidth={isOnActivePath ? 2 : 1.5}
            strokeDasharray={isOnActivePath ? '5,3' : undefined}
            className={isOnActivePath ? 'active-connection' : ''}
            style={{ transition: 'all 0.3s ease' }}
          />
          {/* 箭头 */}
          <polygon
            points={`${toX},${toY} ${toX - 8},${toY - 4} ${toX - 8},${toY + 4}`}
            fill={isOnActivePath ? '#1890ff' : '#d9d9d9'}
          />
        </g>
      );
    });
  };

  // 渲染节点
  const renderNodes = () => {
    return layoutNodes.map((node) => {
      const step = stepMap.get(node.id);
      if (!step) return null;

      const isCurrent = step.step === currentStep;
      const statusColor = getStatusColor(step.status);
      const stepNumber = steps.findIndex(s => s.step === step.step) + 1;

      return (
        <g
          key={node.id}
          transform={`translate(${node.position.x}, ${node.position.y})`}
          className={`graph-node ${step.status} ${isCurrent ? 'current' : ''}`}
          onClick={() => onNodeClick?.(node.id)}
          style={{ cursor: onNodeClick ? 'pointer' : 'default' }}
        >
          {/* 节点背景 */}
          <rect
            width="180"
            height="60"
            rx="8"
            fill="white"
            stroke={statusColor}
            strokeWidth={isCurrent ? 2 : 1.5}
            className="node-rect"
          />

          {/* 节点序号 */}
          <circle
            cx="20"
            cy="30"
            r="12"
            fill={statusColor}
          />
          <text
            x="20"
            y="30"
            textAnchor="middle"
            dominantBaseline="middle"
            fill="white"
            fontSize="12"
            fontWeight="bold"
          >
            {stepNumber}
          </text>

          {/* 节点名称 */}
          <text
            x="45"
            y="25"
            fill="#262626"
            fontSize="13"
            fontWeight={isCurrent ? 500 : 400}
          >
            {step.name.length > 12 ? step.name.substring(0, 12) + '...' : step.name}
          </text>

          {/* 状态文本 */}
          <text
            x="45"
            y="45"
            fill="#8c8c8c"
            fontSize="11"
          >
            {step.status === 'running' && '执行中...'}
            {step.status === 'completed' && '已完成'}
            {step.status === 'error' && '失败'}
            {step.status === 'pending' && '等待中'}
          </text>

          {/* 运行中动画效果 */}
          {step.status === 'running' && (
            <circle
              cx="90"
              cy="30"
              r="40"
              fill="none"
              stroke="#1890ff"
              strokeWidth="1"
              opacity="0.3"
              className="pulse-circle"
            />
          )}
        </g>
      );
    });
  };

  if (steps.length === 0) {
    return (
      <div className={`node-graph-view empty ${className}`}>
        <p style={{ textAlign: 'center', color: '#999', marginTop: 60 }}>
          暂无步骤信息
        </p>
      </div>
    );
  }

  return (
    <div className={`node-graph-view ${className}`}>
      <svg
        width="100%"
        viewBox={`0 0 ${canvasSize.width} ${canvasSize.height}`}
        style={{ overflow: 'visible' }}
      >
        {/* 连接线层 */}
        <g>{renderConnections()}</g>
        {/* 节点层 */}
        <g>{renderNodes()}</g>
      </svg>
    </div>
  );
};

export default NodeGraphView;
