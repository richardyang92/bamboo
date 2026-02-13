/**
 * React Flow Node Graph View
 * Main React Flow implementation replacing original SVG-based NodeGraphView
 * Uses dagre auto-layout to automatically position nodes and avoid edge crossings
 */

import React, { useMemo, useCallback, useEffect } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import type { Connection, Node, FitViewOptions } from '@xyflow/react';
import type {
  WorkflowStep,
  WorkflowType,
  WorkflowNodeData,
} from '../../../types';
import { getWorkflowGraph } from '../../../config/workflowGraphs';
import WorkflowCustomNode from './ReactFlowCustomNode';
import WorkflowCustomEdge from './ReactFlowCustomEdge';
import './ReactFlowNodeGraphView.css';
import dagre from 'dagre';

interface ReactFlowNodeGraphViewProps {
  steps: WorkflowStep[];
  currentStep?: string;
  workflowType: WorkflowType;
  onNodeClick?: (stepId: string) => void;
  className?: string;
}

// Register custom node and edge types
const nodeTypes = {
  custom: WorkflowCustomNode,
};

const edgeTypes = {
  custom: WorkflowCustomEdge,
};

const ReactFlowNodeGraphView: React.FC<ReactFlowNodeGraphViewProps> = ({
  steps,
  workflowType,
  onNodeClick,
  className = '',
}) => {
  // Get base graph configuration
  const baseGraph = useMemo(
    () => getWorkflowGraph(workflowType),
    [workflowType]
  );

  // Create step map for status lookup
  const stepMap = useMemo(() => {
    const map = new Map<string, WorkflowStep>();
    steps.forEach((step) => map.set(step.step, step));
    return map;
  }, [steps]);

  // Apply dagre auto-layout to position nodes and avoid edge crossings
  const layoutedNodes = useMemo(() => {
    if (baseGraph.nodes.length === 0) {
      return [];
    }

    // Create dagre graph for layout calculation
    const dagreGraph = new dagre.graphlib.Graph();
    dagreGraph.setDefaultEdgeLabel(() => ({}));
    dagreGraph.setGraph({ rankdir: 'TB', ranksep: 100, nodesep: 80 });

    // Add nodes with dimensions
    baseGraph.nodes.forEach((node) => {
      dagreGraph.setNode(node.id, { width: 180, height: 60 });
    });

    // Add edges
    baseGraph.edges.forEach((edge) => {
      dagreGraph.setEdge(edge.source, edge.target);
    });

    // Run dagre layout
    dagre.layout(dagreGraph);

    // Apply layout positions to nodes (dagre returns x,y centered)
    return baseGraph.nodes.map((node) => {
      const dagreNode = dagreGraph.node(node.id);

      return {
        ...node,
        position: {
          x: (dagreNode?.x ?? 0) - 90,  // Center offset (node width is 180)
          y: dagreNode?.y ?? 0,
        },
      };
    });
  }, [baseGraph]);

  const [nodes, setNodes, onNodesChange] = useNodesState(
    layoutedNodes.map((node) => ({
      ...node,
      data: {
        ...node.data,
        status: stepMap.get(node.data.stepId)?.status || 'pending',
        retryInfo: stepMap.get(node.data.stepId)?.retry_info,
      },
    }))
  );
  const [edges, setEdges, onEdgesChange] = useEdgesState(baseGraph.edges.map((edge) => {
    const sourceStep = stepMap.get(edge.source);
    const targetStep = stepMap.get(edge.target);
    const isActive =
      sourceStep?.status === 'completed' &&
      targetStep?.status !== 'pending';

    return {
      ...edge,
      animated: isActive,
      style: {
        strokeWidth: isActive ? 2.5 : 1.5,
        opacity: isActive ? 1 : 0.4,
      },
    };
  }));

  // Update nodes when steps change
  useEffect(() => {
    const updatedNodes = layoutedNodes.map((node) => {
      const step = stepMap.get(node.data.stepId);
      return {
        ...node,
        data: {
          ...node.data,
          status: step?.status || 'pending',
          retryInfo: step?.retry_info,
        },
      };
    });
    setNodes(updatedNodes);
  }, [steps, layoutedNodes, stepMap, setNodes]);

  // Update edges when steps change
  useEffect(() => {
    const updatedEdges = baseGraph.edges.map((edge) => {
      const sourceStep = stepMap.get(edge.source);
      const targetStep = stepMap.get(edge.target);
      const isActive =
        sourceStep?.status === 'completed' &&
        targetStep?.status !== 'pending';

      return {
        ...edge,
        animated: isActive,
        style: {
          strokeWidth: isActive ? 2.5 : 1.5,
          opacity: isActive ? 1 : 0.4,
        },
      };
    });
    setEdges(updatedEdges);
  }, [steps, baseGraph.edges, stepMap, setEdges]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onNodeClickHandler = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      if (onNodeClick) {
        onNodeClick((node.data as WorkflowNodeData).stepId);
      }
    },
    [onNodeClick]
  );

  const fitViewOptions: FitViewOptions = {
    padding: 0.2,
    includeHiddenNodes: false,
    minZoom: 0.5,
    maxZoom: 1.5,
  };

  // Get node color for minimap
  const getMinimapNodeColor = (node: Node): string => {
    const data = node.data as WorkflowNodeData;
    const status = data.status || 'pending';
    switch (status) {
      case 'completed':
        return '#52c41a';
      case 'running':
        return '#1890ff';
      case 'error':
        return '#ff4d4f';
      default:
        return '#d9d9d9';
    }
  };

  if (nodes.length === 0) {
    return (
      <div className={`react-flow-graph-view empty ${className}`}>
        <p style={{ textAlign: 'center', color: '#999', marginTop: 60 }}>
          暂无步骤信息
        </p>
      </div>
    );
  }

  return (
    <div className={`react-flow-graph-view ${className}`}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClickHandler}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={fitViewOptions}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={true}
        zoomOnScroll={true}
        panOnScroll={true}
        selectNodesOnDrag={false}
        defaultViewport={{ x: 0, y: 0, zoom: 1 }}
        minZoom={0.3}
        maxZoom={2}
        attributionPosition="bottom-left"
        proOptions={{ hideAttribution: true }}
      >
        <Background
          color="#d9d9d9"
          gap={16}
          style={{ opacity: 0.3 }}
        />
        <Controls
          style={{
            display: 'flex',
            flexDirection: 'row',
            gap: '4px',
          }}
        />
        <MiniMap
          nodeColor={getMinimapNodeColor}
          style={{
            background: 'rgba(255, 255, 255, 0.9)',
            border: '1px solid #e8e9ea',
            borderRadius: '8px',
          }}
          maskColor="rgba(0, 0, 0, 0.05)"
        />
      </ReactFlow>
    </div>
  );
};

export default ReactFlowNodeGraphView;
