/**
 * NodeGraphView - 可视化节点图视图
 * 真实反映CodeAct工作流，包括分支、重试循环
 */
import React, { useMemo } from 'react';
import type { WorkflowStep, WorkflowType } from '../../../types';
import { getStatusColor } from './graphUtils';
import './NodeGraphView.css';

interface NodeGraphViewProps {
  steps: WorkflowStep[];
  currentStep?: string;
  workflowType: WorkflowType;
  onNodeClick?: (stepId: string) => void;
  onStreamContentClick?: (stepId: string) => void;
  className?: string;
}

// 定义节点类型
interface FlowNode {
  id: string;
  name: string;
  x: number;
  y: number;
  type: 'start' | 'process' | 'decision' | 'end' | 'retry';
  visible: boolean; // 是否显示（基于实际执行情况）
}

// 定义连接类型
interface FlowConnection {
  from: string;
  to: string;
  label?: string;
  type: 'success' | 'retry' | 'failure' | 'default';
  visible: boolean;
}

// CodeAct 绘图工作流节点定义（带位置）
const DRAWING_FLOW_NODES: FlowNode[] = [
  { id: 'refine_prompt', name: '润色提示词', x: 250, y: 50, type: 'start', visible: true },
  { id: 'generate_code', name: '生成绘图代码', x: 250, y: 150, type: 'process', visible: true },
  { id: 'execute_code', name: '执行绘图代码', x: 250, y: 250, type: 'process', visible: true },
  { id: 'analyze_execution_result', name: '分析执行结果', x: 250, y: 350, type: 'decision', visible: true },
  { id: 'fix_code_with_feedback', name: '修复代码', x: 450, y: 350, type: 'retry', visible: true },
  { id: 'save_image', name: '验证图片保存', x: 250, y: 470, type: 'end', visible: true },
];

// CodeAct 绘图工作流连接定义
const DRAWING_FLOW_CONNECTIONS: FlowConnection[] = [
  { from: 'refine_prompt', to: 'generate_code', type: 'default', visible: true },
  { from: 'generate_code', to: 'execute_code', type: 'default', visible: true },
  { from: 'execute_code', to: 'analyze_execution_result', type: 'default', visible: true },
  { from: 'analyze_execution_result', to: 'save_image', label: '成功', type: 'success', visible: true },
  { from: 'analyze_execution_result', to: 'fix_code_with_feedback', label: '失败', type: 'failure', visible: true },
  { from: 'fix_code_with_feedback', to: 'execute_code', label: '重试', type: 'retry', visible: true },
];

// 节点配置
const NODE_WIDTH = 160;
const NODE_HEIGHT = 50;
const NODE_RADIUS = 8;

const NodeGraphView: React.FC<NodeGraphViewProps> = ({
  steps,
  currentStep = '',
  workflowType: _workflowType, // 预留：用于支持不同工作流类型的流程图
  onNodeClick,
  onStreamContentClick: _onStreamContentClick, // 预留：用于点击查看流式内容
  className = '',
}) => {
  // 创建步骤映射
  const stepMap = useMemo(() => {
    const map = new Map<string, WorkflowStep>();
    steps.forEach(step => map.set(step.step, step));
    return map;
  }, [steps]);

  // 确定节点和连接的可见性
  const { visibleNodes, visibleConnections } = useMemo(() => {
    // 所有节点始终可见
    const nodes = DRAWING_FLOW_NODES;

    // 所有连接始终可见
    const connections = DRAWING_FLOW_CONNECTIONS;

    return { visibleNodes: nodes, visibleConnections: connections };
  }, []);

  // 计算画布大小
  const canvasSize = useMemo(() => {
    if (visibleNodes.length === 0) return { width: 600, height: 400 };
    const maxX = Math.max(...visibleNodes.map(n => n.x + NODE_WIDTH));
    const maxY = Math.max(...visibleNodes.map(n => n.y + NODE_HEIGHT));
    return { width: Math.max(600, maxX + 50), height: Math.max(400, maxY + 50) };
  }, [visibleNodes]);

  // 渲染连接线
  const renderConnections = () => {
    return visibleConnections
      .filter(conn => conn.visible)
      .map((conn, index) => {
        const fromNode = visibleNodes.find(n => n.id === conn.from);
        const toNode = visibleNodes.find(n => n.id === conn.to);
        if (!fromNode || !toNode) return null;

        const fromStep = stepMap.get(conn.from);
        const toStep = stepMap.get(conn.to);

        // 判断连接是否在活跃路径上
        const isOnActivePath = fromStep?.status === 'completed' && toStep?.status !== 'pending';
        // 判断是否是循环连接（需要高亮显示）
        const isRetryConnection = conn.type === 'retry';

        // 根据连接类型选择合适的起点和终点
        let fromX, fromY, toX, toY;

        if (conn.type === 'retry' && conn.from === 'fix_code_with_feedback' && conn.to === 'execute_code') {
          // 特殊处理重试连接：从 fix_code_with_feedback 左侧到 execute_code 右侧
          fromX = fromNode.x;  // 左侧
          fromY = fromNode.y + NODE_HEIGHT / 2;  // 垂直居中
          toX = toNode.x + NODE_WIDTH;  // 右侧
          toY = toNode.y + NODE_HEIGHT / 2;  // 垂直居中
        } else {
          // 默认：从底部中心到顶部中心
          fromX = fromNode.x + NODE_WIDTH / 2;
          fromY = fromNode.y + NODE_HEIGHT;
          toX = toNode.x + NODE_WIDTH / 2;
          toY = toNode.y;
        }

        // 连接样式
        let strokeColor = isOnActivePath ? '#52c41a' : '#d9d9d9';
        let strokeWidth = isOnActivePath ? 2 : 1.5;

        // 循环连接使用特殊颜色高亮
        if (isRetryConnection) {
          strokeColor = isOnActivePath ? '#fa8c16' : '#ffd591';
          strokeWidth = isOnActivePath ? 2.5 : 2;
        }

        // 不同连接类型的路径
        let pathD = '';
        let labelX = 0, labelY = 0;

        // 检测连接方向
        const isLeftwardConnection = fromX > toX;  // 从右向左的连接
        const isRightwardConnection = fromX < toX;  // 从左向右的连接
        const isUpwardConnection = fromY > toY;    // 从下向上的连接

        if (conn.type === 'retry' && conn.from === 'fix_code_with_feedback' && conn.to === 'execute_code') {
          // 特殊处理：重试回环连接（从右侧节点的左侧回到左侧节点的右侧）
          const midX = (fromX + toX) / 2;  // 中间 x 坐标
          // 路径：从左 → 向左到中点 → 向上/下到目标高度 → 向左到目标
          pathD = `M ${fromX} ${fromY} L ${midX} ${fromY} L ${midX} ${toY} L ${toX} ${toY}`;
          labelX = midX - 15;  // 稍微向左偏移，避免遮挡连接线
          labelY = (fromY + toY) / 2 - 5;
        } else if (conn.type === 'failure' && conn.from === 'analyze_execution_result' && conn.to === 'fix_code_with_feedback') {
          // 特殊处理：失败分支连接（从 analyze_execution_result 右侧到 fix_code_with_feedback 左侧）
          // 使用右侧中心到左侧中心
          fromX = fromNode.x + NODE_WIDTH;  // 右侧
          fromY = fromNode.y + NODE_HEIGHT / 2;  // 垂直居中
          toX = toNode.x;  // 左侧
          toY = toNode.y + NODE_HEIGHT / 2;  // 垂直居中
          pathD = `M ${fromX} ${fromY} L ${toX} ${toY}`;
          labelX = (fromX + toX) / 2;
          labelY = fromY - 10;
        } else if (conn.type === 'failure') {
          if (isLeftwardConnection && isUpwardConnection) {
            // 从右下向左上的回环连接（fix_code_with_feedback → execute_code）
            // 从 fix_code_with_feedback 的左侧出发，向上，然后连接到 execute_code 的右侧
            const fromLeftX = toNode.x + NODE_WIDTH / 2 - 10;  // execute_code 右侧附近
            const fromTopY = fromNode.y;  // fix_code_with_feedback 顶部

            pathD = `M ${fromLeftX} ${fromTopY} L ${fromLeftX} ${toY + NODE_HEIGHT / 2} L ${toX} ${toY + NODE_HEIGHT / 2}`;
            labelX = fromLeftX - 20;
            labelY = (fromTopY + toY) / 2;
          } else if (isRightwardConnection) {
            // 向右的分支连接（analyze_execution_result → fix_code_with_feedback）
            pathD = `M ${fromX} ${fromY} L ${fromX} ${fromY + 20} L ${toX} ${fromY + 20} L ${toX} ${toY}`;
            labelX = (fromX + toX) / 2;
            labelY = fromY + 15;
          } else {
            // 垂直方向，使用默认分支样式
            pathD = `M ${fromX} ${fromY} L ${fromX} ${fromY + 20} L ${toX} ${fromY + 20} L ${toX} ${toY}`;
            labelX = (fromX + toX) / 2;
            labelY = fromY + 15;
          }
        } else if (conn.type === 'success') {
          // 向下的成功连接
          pathD = `M ${fromX} ${fromY} L ${toX} ${toY}`;
          labelX = toX + 25;
          labelY = (fromY + toY) / 2;
        } else {
          // 默认垂直连接
          pathD = `M ${fromX} ${fromY} L ${toX} ${toY}`;
        }

        return (
          <g key={`connection-${index}`}>
            <path
              d={pathD}
              fill="none"
              stroke={strokeColor}
              strokeWidth={strokeWidth}
              className={`${isOnActivePath ? 'active-connection' : ''} ${conn.type === 'retry' ? 'retry-connection' : ''}`}
              style={{ transition: 'all 0.3s ease' }}
            />
            {/* 箭头 - 根据连接方向动态计算 */}
            {(() => {
              // 计算连接方向
              const dx = toX - fromX;
              const dy = toY - fromY;
              const angle = Math.atan2(dy, dx) * (180 / Math.PI);

              // 箭头大小
              const arrowLength = 10;

              // 计算箭头的两个翼点
              const leftX = toX - arrowLength/2 * Math.cos(angle - Math.PI/6);
              const leftY = toY - arrowLength/2 * Math.sin(angle - Math.PI/6);
              const rightX = toX + arrowLength/2 * Math.cos(angle + Math.PI/6);
              const rightY = toY + arrowLength/2 * Math.sin(angle + Math.PI/6);

              return (
                <polygon
                  points={`${toX},${toY} ${leftX},${leftY} ${rightX},${rightY}`}
                  fill={isOnActivePath ? '#52c41a' : (isRetryConnection ? '#fa8c16' : '#8c8c8c')}
                  stroke={isOnActivePath ? '#52c41a' : (isRetryConnection ? '#fa8c16' : '#8c8c8c')}
                  strokeWidth="1"
                />
              );
            })()}
            {/* 标签 */}
            {conn.label && (
              <text
                x={labelX}
                y={labelY}
                textAnchor="middle"
                fill={isOnActivePath ? '#52c41a' : '#8c8c8c'}
                fontSize="11"
                style={{ background: 'white' }}
              >
                {conn.label}
              </text>
            )}
          </g>
        );
      });
  };

  // 渲染节点
  const renderNodes = () => {
    return visibleNodes.map((node) => {
      const step = stepMap.get(node.id);
      const isCurrent = step?.step === currentStep;
      const status = step?.status || 'pending';
      const statusColor = getStatusColor(status);
      const hasRetry = step?.retry_info && step.retry_info.current > 0;

      return (
        <g
          key={node.id}
          transform={`translate(${node.x}, ${node.y})`}
          className={`graph-node ${status} ${isCurrent ? 'current' : ''} ${node.type}`}
          onClick={() => onNodeClick?.(node.id)}
          style={{ cursor: onNodeClick ? 'pointer' : 'default' }}
        >
          {/* 节点阴影 */}
          <rect
            x="2"
            y="2"
            width={NODE_WIDTH}
            height={NODE_HEIGHT}
            rx={NODE_RADIUS}
            fill="rgba(0,0,0,0.05)"
          />

          {/* 节点背景 */}
          <rect
            x="0"
            y="0"
            width={NODE_WIDTH}
            height={NODE_HEIGHT}
            rx={NODE_RADIUS}
            fill="white"
            stroke={statusColor}
            strokeWidth={isCurrent ? 2 : 1.5}
            className="node-rect"
          />

          {/* 节点类型图标 */}
          {node.type === 'decision' && (
            <polygon
              points="15,25 25,15 35,25 25,35"
              fill={status === 'completed' ? statusColor : '#d9d9d9'}
            />
          )}
          {node.type === 'start' && (
            <circle
              cx="25"
              cy="25"
              r="8"
              fill={status === 'completed' ? statusColor : '#d9d9d9'}
            />
          )}
          {node.type === 'end' && (
            <circle
              cx="25"
              cy="25"
              r="8"
              fill="none"
              stroke={status === 'completed' ? statusColor : '#d9d9d9'}
              strokeWidth="2"
            />
          )}
          {node.type === 'retry' && (
            <path
              d="M 20 25 L 30 25 M 25 20 L 30 25 L 25 30"
              stroke={status === 'completed' ? statusColor : '#d9d9d9'}
              strokeWidth="2"
              fill="none"
            />
          )}

          {/* 节点名称 */}
          <text
            x="45"
            y="20"
            fill="#262626"
            fontSize="12"
            fontWeight={isCurrent ? 500 : 400}
          >
            {node.name}
          </text>

          {/* 状态文本 */}
          <text
            x="45"
            y="38"
            fill="#8c8c8c"
            fontSize="10"
          >
            {status === 'running' && '执行中...'}
            {status === 'completed' && '已完成'}
            {status === 'error' && '失败'}
            {status === 'pending' && '等待中'}
          </text>

          {/* 重试标签 */}
          {hasRetry && step?.retry_info && (
            <g>
              <rect
                x={NODE_WIDTH - 45}
                y="5"
                width="40"
                height="16"
                rx="4"
                fill="#fa8c16"
              />
              <text
                x={NODE_WIDTH - 25}
                y="16"
                textAnchor="middle"
                fill="white"
                fontSize="9"
                fontWeight="bold"
              >
                {step.retry_info.current}/{step.retry_info.max}
              </text>
            </g>
          )}

          {/* 运行中动画 */}
          {status === 'running' && (
            <circle
              cx={NODE_WIDTH / 2}
              cy={NODE_HEIGHT / 2}
              r="35"
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

  if (visibleNodes.length === 0) {
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
