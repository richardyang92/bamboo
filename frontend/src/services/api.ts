/**
 * API 服务
 * 封装所有与后端 API 的通信
 */
import axios, { AxiosError } from 'axios';
import type {
  AIModifyResponse,
  GenerateImageResponse,
  HistoryItem,
  AvailableModels,
  ModelConfig,
  LLMProvider
} from '../types';

// 创建 axios 实例
const api = axios.create({
  // 开发环境使用 Vite 代理，生产环境使用环境变量
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    console.log(`[API] Response:`, response.status, response.data);
    return response.data;
  },
  (error: AxiosError<any>) => {
    const message = error.response?.data?.error || error.message || '请求失败';
    console.error('[API] Response error:', message);
    return Promise.reject(new Error(message));
  }
);

// ==================== 绘图工作流 API ====================

/**
 * 启动绘图工作流（支持模型选择）
 */
export const startDrawingWorkflow = async (
  prompt: string,
  modelConfig?: { provider?: LLMProvider; model?: string; enable_thinking?: boolean }
) => {
  return api.post('/api/drawing/workflow', {
    prompt,
    model_provider: modelConfig?.provider,
    model_name: modelConfig?.model,
    enable_thinking: modelConfig?.enable_thinking,
  });
};

/**
 * 获取绘图状态
 */
export const getDrawingStatus = async () => {
  return api.get('/api/status');
};

/**
 * 列出所有图片
 */
export const listImages = async (): Promise<HistoryItem[]> => {
  return api.get('/api/images');
};

/**
 * 获取图片文件
 */
export const getImageUrl = (filename: string): string => {
  return `/api/images/${filename}`;
};

/**
 * 删除图片
 */
export const deleteImage = async (filename: string) => {
  return api.delete(`/api/images/${filename}`);
};

/**
 * 清除绘图历史记录
 */
export const clearDrawingHistory = async () => {
  return api.post('/api/drawing/clear');
};

/**
 * 停止绘图工作流
 */
export const stopDrawingWorkflow = async () => {
  return api.post('/api/drawing/stop');
};

// ==================== 文档工作流 API ====================

/**
 * 启动文档生成工作流（支持模型选择）
 */
export const startDocumentWorkflow = async (
  prompt: string,
  modelConfig?: { provider?: LLMProvider; model?: string; enable_thinking?: boolean }
) => {
  return api.post('/api/document/workflow-with-images', {
    prompt,
    model_provider: modelConfig?.provider,
    model_name: modelConfig?.model,
    enable_thinking: modelConfig?.enable_thinking,
  });
};

/**
 * AI 修改选中的文本
 */
export const aiModifyText = async (
  selectedText: string,
  instructions: string
): Promise<AIModifyResponse> => {
  return api.post('/api/document/ai-modify', {
    selected_text: selectedText,
    instructions: instructions,
  });
};

/**
 * AI 生成图片
 */
export const aiGenerateImage = async (
  description: string
): Promise<GenerateImageResponse> => {
  return api.post('/api/document/generate-image', {
    description,
  });
};

/**
 * 列出所有文档
 */
export const listDocuments = async (): Promise<HistoryItem[]> => {
  return api.get('/api/documents');
};

/**
 * 获取文档文件
 */
export const getDocumentUrl = (filename: string): string => {
  return `/api/documents/${filename}`;
};

/**
 * 获取文档内容
 */
export const getDocumentContent = async (filename: string): Promise<{ content: string }> => {
  return api.get(`/api/documents/${filename}/content`);
};

/**
 * 删除文档
 */
export const deleteDocument = async (filename: string) => {
  return api.delete(`/api/documents/${filename}`);
};

/**
 * 清除文档历史记录
 */
export const clearDocumentHistory = async () => {
  return api.post('/api/document/clear');
};

/**
 * 停止文档工作流
 */
export const stopDocumentWorkflow = async () => {
  return api.post('/api/document/stop');
};

// ==================== Manim 动画工作流 API ====================

/**
 * 启动 Manim 动画工作流（支持模型选择）
 */
export const startManimWorkflow = async (
  prompt: string,
  quality: string = 'medium',
  modelConfig?: { provider?: LLMProvider; model?: string; enable_thinking?: boolean }
) => {
  return api.post('/api/manim/workflow', {
    prompt,
    quality,
    model_provider: modelConfig?.provider,
    model_name: modelConfig?.model,
    enable_thinking: modelConfig?.enable_thinking,
  });
};

/**
 * 列出所有视频
 */
export const listVideos = async (): Promise<HistoryItem[]> => {
  return api.get('/api/manim/videos');
};

/**
 * 获取视频文件
 */
export const getVideoUrl = (filename: string): string => {
  return `/api/manim/videos/${filename}`;
};

/**
 * 删除视频
 */
export const deleteVideo = async (filename: string) => {
  return api.delete(`/api/manim/videos/${filename}`);
};

/**
 * 清除 Manim 历史记录
 */
export const clearManimHistory = async () => {
  return api.post('/api/manim/clear');
};

/**
 * 停止 Manim 工作流
 */
export const stopManimWorkflow = async () => {
  return api.post('/api/manim/stop');
};

// ==================== 统一 API ====================

/**
 * 获取所有历史记录
 */
export const listHistory = async (): Promise<HistoryItem[]> => {
  return api.get('/api/history');
};

/**
 * 健康检查
 */
export const healthCheck = async () => {
  return api.get('/api/health');
};

export default api;

// ==================== 模型管理 API ====================

/**
 * 获取可用的模型列表
 */
export const getAvailableModels = async (): Promise<AvailableModels> => {
  return api.get('/api/models');
};

/**
 * 切换当前使用的模型
 */
export const switchModel = async (
  provider: LLMProvider,
  model: string
): Promise<{ success: boolean; current_config: ModelConfig }> => {
  return api.post('/api/models/switch', { provider, model });
};

/**
 * 获取当前使用的模型
 */
export const getCurrentModel = async (): Promise<ModelConfig> => {
  return api.get('/api/models/current');
};
