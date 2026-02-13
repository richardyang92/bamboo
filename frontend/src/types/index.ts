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
    // CodeAct 模式新增：重试信息
    retry_info?: {
        current: number;  // 当前重试次数
        max: number;     // 最大重试次数
    };
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
    content_type?: 'content' | 'reasoning';  // 新增：内容类型（普通内容或思考内容）
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

// ========== LLM 模型配置类型 ==========

// LLM 提供商类型
export type LLMProvider = 'deepseek' | 'ollama';

// 模型配置
export interface ModelConfig {
    provider: LLMProvider;
    model: string;
    api_key?: string;
    base_url?: string;
    supports_reasoning: boolean;
}

// 可用模型列表
export interface AvailableModels {
    providers: {
        [key in LLMProvider]: {
            provider: LLMProvider;
            models: string[];
            supports_reasoning: boolean;
            current: string;
        };
    };
    current_provider: LLMProvider;
    current_config: ModelConfig;
}

// 扩展的工作流请求，支持模型选择
export interface WorkflowRequestWithModel extends WorkflowRequest {
    model_provider?: LLMProvider;
    model_name?: string;
    enable_thinking?: boolean;  // 启用 thinking 模式（仅支持 Ollama 推理模型）
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

// ============================================================================
// React Flow Workflow Graph Types
// ============================================================================

// Node type categories for workflow graphs
export type NodeType = 'start' | 'process' | 'decision' | 'end' | 'retry';

// Edge type categories for workflow graphs
export type EdgeType = 'success' | 'failure' | 'retry' | 'default';

// Custom node data structure for React Flow
// Using index signature to satisfy React Flow's type constraints
export interface WorkflowNodeData {
    label: string;
    type: NodeType;
    workflowType: WorkflowType;
    stepId: string;
    status?: StepStatus;
    retryInfo?: {
        current: number;
        max: number;
    };
    [key: string]: any; // Index signature for additional properties
}

// Custom edge data structure for React Flow
// Using index signature to satisfy React Flow's type constraints
export interface WorkflowEdgeData {
    label?: string;
    type: EdgeType;
    workflowType: WorkflowType;
    [key: string]: any; // Index signature for additional properties
}
