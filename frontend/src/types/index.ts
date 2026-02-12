/**
 * Bamboo 前端类型定义
 */

// 工作流状态类型
export type WorkflowStatusType = 'idle' | 'running' | 'completed' | 'error';

// 工作流步骤状态
export type StepStatus = 'pending' | 'running' | 'completed' | 'error';

// 工作流类型
export type WorkflowType = 'drawing' | 'document_with_images' | 'manim';

// 工作流步骤
export interface WorkflowStep {
  step: string;
  name: string;
  status: StepStatus;
  timestamp?: string;
  completed_at?: string;
  error?: string;
}

// 工作流状态
export interface WorkflowStatus {
  status: WorkflowStatusType;
  current_step: string;
  steps: WorkflowStep[];
  result?: WorkflowResult;
  error?: string;
}

// 工作流结果
export interface WorkflowResult {
  type: 'image' | 'document_with_images' | 'video';
  image_path?: string;
  image_url?: string;
  image_size?: number;
  video_path?: string;
  video_url?: string;
  video_size?: number;
  path?: string;
  filename?: string;
  url?: string;
  size?: number;
  content?: string;
  outline?: string;
  generated_code?: string;
  images?: GeneratedImage[];
  image_count?: number;
}

// 生成的图片信息
export interface GeneratedImage {
  number?: number;
  description: string;
  enhanced_description?: string;
  placeholder?: string;
  path: string;
  relative_path?: string;
  size?: number;
  url?: string;  // 前端计算得出，不是后端直接返回
  filename?: string;
}

// 历史记录项
export interface HistoryItem {
  type: 'image' | 'document' | 'video';
  name: string;
  url: string;
  path?: string;
  size: number;
  created: number;
}

// WebSocket 消息类型
export interface WebSocketMessage {
  type: 'status_update' | 'stream_content';
  workflow_type: WorkflowType;
  status?: WorkflowStatusType;
  current_step?: string;
  steps?: WorkflowStep[];
  result?: WorkflowResult;
  error?: string;
  node?: string;
  content?: string;
}

// WebSocket 连接状态
export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'reconnecting';

// 流式内容条目
export interface StreamContentEntry {
  node: string;
  content: string;
  timestamp: number;
}

// 扩展的工作流步骤（可选，用于存储流式内容）
export interface WorkflowStepExtended extends WorkflowStep {
  streamContent?: string;
}

// 工作流视图模式
export type WorkflowViewMode = 'cards' | 'graph' | 'timeline';

// 扩展的工作流步骤（带时长信息）
export interface WorkflowStepWithDuration extends WorkflowStep {
  duration_ms?: number;
  started_at?: string;
}

// 视图配置
export interface WorkflowViewConfig {
  mode: WorkflowViewMode;
  showDetails: boolean;
  compactMode: boolean;
  selectedNodes: string[];
  highlightedNode?: string;
}

// 节点交互状态
export interface NodeInteractionState {
  expanded: Set<string>;
  selected: Set<string>;
  draggedNodeId?: string;
}

// 图布局节点
export interface GraphLayoutNode {
  id: string;
  position: { x: number; y: number };
  connections: { from?: string; to?: string };
}

// API 请求/响应类型
export interface WorkflowRequest {
  prompt: string;
  quality?: 'low' | 'medium' | 'high' | '4k';
}

export interface AIModifyRequest {
  selected_text: string;
  instructions: string;
}

export interface AIModifyResponse {
  modified_text: string;
}

export interface GenerateImageRequest {
  description: string;
}

export interface GenerateImageResponse {
  image_url: string;
  image_path: string;
}
