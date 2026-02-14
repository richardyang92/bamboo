/**
 * Workflow Graph Configuration for React Flow
 * Defines nodes and edges for all workflow types
 */

import type { Node, Edge } from '@xyflow/react';
import type {
  WorkflowType,
  NodeType,
  EdgeType,
  WorkflowNodeData,
  WorkflowEdgeData,
} from '../types';

// Re-export types for convenience
export type { NodeType, EdgeType, WorkflowNodeData, WorkflowEdgeData };

// ============================================================================
// DRAWING WORKFLOW
// ============================================================================

export const DRAWING_NODES: Node<WorkflowNodeData>[] = [
  {
    id: 'refine_prompt',
    type: 'custom',
    position: { x: 0, y: 0 }, // Auto-layout will set position
    data: {
      label: '润色提示词',
      type: 'start',
      stepId: 'refine_prompt',
      workflowType: 'drawing',
    },
  },
  {
    id: 'generate_code',
    type: 'custom',
    position: { x: 0, y: 0 },
    data: {
      label: '生成绘图代码',
      type: 'process',
      stepId: 'generate_code',
      workflowType: 'drawing',
    },
  },
  {
    id: 'execute_code',
    type: 'custom',
    position: { x: 0, y: 0 },
    data: {
      label: '执行绘图代码',
      type: 'process',
      stepId: 'execute_code',
      workflowType: 'drawing',
    },
  },
  {
    id: 'analyze_execution_result',
    type: 'custom',
    position: { x: 0, y: 0 },
    data: {
      label: '分析执行结果',
      type: 'decision',
      stepId: 'analyze_execution_result',
      workflowType: 'drawing',
    },
  },
  {
    id: 'fix_code_with_feedback',
    type: 'custom',
    position: { x: 0, y: 0 },
    data: {
      label: '修复代码',
      type: 'retry',
      stepId: 'fix_code_with_feedback',
      workflowType: 'drawing',
    },
  },
  {
    id: 'save_image',
    type: 'custom',
    position: { x: 0, y: 0 },
    data: {
      label: '验证图片保存',
      type: 'end',
      stepId: 'save_image',
      workflowType: 'drawing',
    },
  },
];

export const DRAWING_EDGES: Edge<WorkflowEdgeData>[] = [
  {
    id: 'e-refine-generate',
    source: 'refine_prompt',
    target: 'generate_code',
    type: 'custom',
    data: { type: 'default', workflowType: 'drawing' },
  },
  {
    id: 'e-generate-execute',
    source: 'generate_code',
    target: 'execute_code',
    type: 'custom',
    data: { type: 'default', workflowType: 'drawing' },
  },
  {
    id: 'e-execute-analyze',
    source: 'execute_code',
    target: 'analyze_execution_result',
    type: 'custom',
    data: { type: 'default', workflowType: 'drawing' },
  },
  {
    id: 'e-analyze-save',
    source: 'analyze_execution_result',
    target: 'save_image',
    type: 'custom',
    label: '成功',
    data: { type: 'success', workflowType: 'drawing' },
  },
  {
    id: 'e-analyze-fix',
    source: 'analyze_execution_result',
    target: 'fix_code_with_feedback',
    type: 'custom',
    label: '失败',
    data: { type: 'failure', workflowType: 'drawing' },
  },
  {
    id: 'e-fix-execute',
    source: 'fix_code_with_feedback',
    target: 'execute_code',
    type: 'custom',
    label: '重试',
    data: { type: 'retry', workflowType: 'drawing' },
  },
];

// ============================================================================
// DOCUMENT WORKFLOW
// ============================================================================

export const DOCUMENT_NODES: Node<WorkflowNodeData>[] = [
  {
    id: 'refine_prompt',
    type: 'custom',
    position: { x: 0, y: 0 },
    data: {
      label: '润色写作需求',
      type: 'start',
      stepId: 'refine_prompt',
      workflowType: 'document_with_images',
    },
  },
  {
    id: 'generate_outline',
    type: 'custom',
    position: { x: 0, y: 0 },
    data: {
      label: '生成文档大纲',
      type: 'process',
      stepId: 'generate_outline',
      workflowType: 'document_with_images',
    },
  },
  {
    id: 'generate_content',
    type: 'custom',
    position: { x: 0, y: 0 },
    data: {
      label: '生成文档内容',
      type: 'process',
      stepId: 'generate_content',
      workflowType: 'document_with_images',
    },
  },
  {
    id: 'identify_image_requests',
    type: 'custom',
    position: { x: 0, y: 0 },
    data: {
      label: '识别图片需求',
      type: 'decision',
      stepId: 'identify_image_requests',
      workflowType: 'document_with_images',
    },
  },
  {
    id: 'generate_images',
    type: 'custom',
    position: { x: 0, y: 0 },
    data: {
      label: '生成图表',
      type: 'process',
      stepId: 'generate_images',
      workflowType: 'document_with_images',
    },
  },
  {
    id: 'embed_images',
    type: 'custom',
    position: { x: 0, y: 0 },
    data: {
      label: '整合图片到文档',
      type: 'process',
      stepId: 'embed_images',
      workflowType: 'document_with_images',
    },
  },
  {
    id: 'save_document',
    type: 'custom',
    position: { x: 0, y: 0 },
    data: {
      label: '保存文档',
      type: 'process',
      stepId: 'save_document',
      workflowType: 'document_with_images',
    },
  },
  {
    id: 'verify_document',
    type: 'custom',
    position: { x: 0, y: 0 },
    data: {
      label: '验证文档',
      type: 'end',
      stepId: 'verify_document',
      workflowType: 'document_with_images',
    },
  },
];

export const DOCUMENT_EDGES: Edge<WorkflowEdgeData>[] = [
  {
    id: 'e-refine-outline',
    source: 'refine_prompt',
    target: 'generate_outline',
    type: 'custom',
    data: { type: 'default', workflowType: 'document_with_images' },
  },
  {
    id: 'e-outline-content',
    source: 'generate_outline',
    target: 'generate_content',
    type: 'custom',
    data: { type: 'default', workflowType: 'document_with_images' },
  },
  {
    id: 'e-content-identify',
    source: 'generate_content',
    target: 'identify_image_requests',
    type: 'custom',
    data: { type: 'default', workflowType: 'document_with_images' },
  },
  // 条件边：有图片需求
  {
    id: 'e-identify-generate',
    source: 'identify_image_requests',
    target: 'generate_images',
    type: 'custom',
    label: '有图片',
    data: {
      type: 'conditional',
      workflowType: 'document_with_images',
      condition: 'has_images'
    },
  },
  // 条件边：无图片需求（跳过生图流程）
  {
    id: 'e-identify-save-skip',
    source: 'identify_image_requests',
    target: 'save_document',
    type: 'custom',
    label: '无图片',
    data: {
      type: 'conditional',
      workflowType: 'document_with_images',
      condition: 'no_images'
    },
  },
  {
    id: 'e-generate-embed',
    source: 'generate_images',
    target: 'embed_images',
    type: 'custom',
    data: { type: 'default', workflowType: 'document_with_images' },
  },
  {
    id: 'e-embed-save',
    source: 'embed_images',
    target: 'save_document',
    type: 'custom',
    data: { type: 'default', workflowType: 'document_with_images' },
  },
  {
    id: 'e-save-verify',
    source: 'save_document',
    target: 'verify_document',
    type: 'custom',
    data: { type: 'default', workflowType: 'document_with_images' },
  },
];

// ============================================================================
// MANIM WORKFLOW
// ============================================================================

export const MANIM_NODES: Node<WorkflowNodeData>[] = [
  {
    id: 'refine_prompt',
    type: 'custom',
    position: { x: 0, y: 0 },
    data: {
      label: '润色动画需求',
      type: 'start',
      stepId: 'refine_prompt',
      workflowType: 'manim',
    },
  },
  {
    id: 'generate_code',
    type: 'custom',
    position: { x: 0, y: 0 },
    data: {
      label: '生成动画代码',
      type: 'process',
      stepId: 'generate_code',
      workflowType: 'manim',
    },
  },
  {
    id: 'execute_code',
    type: 'custom',
    position: { x: 0, y: 0 },
    data: {
      label: '渲染动画视频',
      type: 'process',
      stepId: 'execute_code',
      workflowType: 'manim',
    },
  },
  {
    id: 'save_video',
    type: 'custom',
    position: { x: 0, y: 0 },
    data: {
      label: '验证视频保存',
      type: 'end',
      stepId: 'save_video',
      workflowType: 'manim',
    },
  },
];

export const MANIM_EDGES: Edge<WorkflowEdgeData>[] = [
  {
    id: 'e-refine-generate',
    source: 'refine_prompt',
    target: 'generate_code',
    type: 'custom',
    data: { type: 'default', workflowType: 'manim' },
  },
  {
    id: 'e-generate-execute',
    source: 'generate_code',
    target: 'execute_code',
    type: 'custom',
    data: { type: 'default', workflowType: 'manim' },
  },
  {
    id: 'e-execute-save',
    source: 'execute_code',
    target: 'save_video',
    type: 'custom',
    data: { type: 'default', workflowType: 'manim' },
  },
];

// ============================================================================
// EXPORT FUNCTIONS
// ============================================================================

/**
 * Get workflow graph configuration (nodes and edges) for a given workflow type
 */
export const getWorkflowGraph = (
  workflowType: WorkflowType
): { nodes: Node<WorkflowNodeData>[]; edges: Edge<WorkflowEdgeData>[] } => {
  switch (workflowType) {
    case 'drawing':
      return { nodes: DRAWING_NODES, edges: DRAWING_EDGES };
    case 'document_with_images':
      return { nodes: DOCUMENT_NODES, edges: DOCUMENT_EDGES };
    case 'manim':
      return { nodes: MANIM_NODES, edges: MANIM_EDGES };
    default:
      return { nodes: [], edges: [] };
  }
};
