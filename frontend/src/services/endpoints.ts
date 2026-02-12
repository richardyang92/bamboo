/**
 * API 端点常量
 * 集中管理所有 API 端点路径
 */

// ==================== 绘图工作流端点 ====================
export const DRAWING_WORKFLOW = '/api/drawing/workflow';
export const DRAWING_STATUS = '/api/status';
export const DRAWING_IMAGES = '/api/images';
export const DRAWING_CLEAR = '/api/drawing/clear';

// ==================== 文档工作流端点 ====================
export const DOCUMENT_WORKFLOW = '/api/document/workflow-with-images';
export const DOCUMENT_AI_MODIFY = '/api/document/ai-modify';
export const DOCUMENT_GENERATE_IMAGE = '/api/document/generate-image';
export const DOCUMENTS = '/api/documents';

// ==================== Manim 动画工作流端点 ====================
export const MANIM_WORKFLOW = '/api/manim/workflow';
export const MANIM_VIDEOS = '/api/manim/videos';
export const MANIM_CLEAR = '/api/manim/clear';

// ==================== 统一端点 ====================
export const HISTORY = '/api/history';
export const HEALTH = '/api/health';

// ==================== WebSocket 端点 ====================
export const WEBSOCKET = '/ws';
