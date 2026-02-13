/**
 * useWebSocket Hook - 增强版
 * 用于管理 WebSocket 连接、监听工作流状态更新、追踪连接状态和累积流式内容
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { getWebSocket } from '../services/websocket';
import { getInitialSteps, mergeStepStatus } from '../constants/workflowSteps';
import type {
  WorkflowType,
  WorkflowStatus,
  WorkflowStep,
  WebSocketMessage,
  ConnectionState,
} from '../types';

interface UseWebSocketReturn {
  // 原有状态
  status: WorkflowStatus['status'];
  steps: WorkflowStep[];
  result: any;
  error: string | null;

  // 新增状态
  currentStep: string;
  connectionState: ConnectionState;
  reconnectAttempts: number;
  streamContent: Map<string, string>;  // 普通内容
  reasoningContent: Map<string, string>;  // 新增：思考内容
  currentNode: string | null;
  isStreaming: boolean;

  // 原有方法
  connect: (workflowType: WorkflowType) => void;
  disconnect: () => void;
  switchWorkflow: (workflowType: WorkflowType) => void;

  // 新增方法
  clearStreamContent: () => void;
  getStreamContent: (node: string) => string;
  getReasoningContent: (node: string) => string;  // 新增：获取思考内容方法
  getConnectionState: () => ConnectionState;
}

export function useWebSocket(workflowType: WorkflowType): UseWebSocketReturn {
  // 获取预定义的初始步骤
  const initialSteps = getInitialSteps(workflowType);

  // 原有状态
  const [status, setStatus] = useState<WorkflowStatus['status']>('idle');
  const [steps, setSteps] = useState<WorkflowStep[]>(initialSteps);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<string>('');

  // 新增状态
  const [connectionState, setConnectionState] = useState<ConnectionState>('connecting');
  const [reconnectAttempts, setReconnectAttempts] = useState<number>(0);
  const [streamContent, setStreamContent] = useState<Map<string, string>>(new Map());
  const [reasoningContent, setReasoningContent] = useState<Map<string, string>>(new Map());  // 新增：思考内容状态
  const [currentNode, setCurrentNode] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);

  const wsRef = useRef<ReturnType<typeof getWebSocket> | null>(null);
  const streamTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const listenersRegistered = useRef(false);
  const lastConnectedType = useRef<WorkflowType | null>(null);

  // 处理流式内容超时（用于判断流式内容是否结束）
  useEffect(() => {
    if (isStreaming) {
      // 每次收到新内容时重置超时
      if (streamTimeoutRef.current) {
        clearTimeout(streamTimeoutRef.current);
      }
      streamTimeoutRef.current = setTimeout(() => {
        setIsStreaming(false);
      }, 3000); // 3秒无新内容认为流式结束
    }

    return () => {
      if (streamTimeoutRef.current) {
        clearTimeout(streamTimeoutRef.current);
      }
    };
  }, [isStreaming]);

  // 使用 ref 来避免循环依赖
  const clearStreamContentRef = useRef(() => {
    setStreamContent(new Map());
    setReasoningContent(new Map());  // 新增：清理思考内容
    setCurrentNode(null);
    setIsStreaming(false);
  });

  // 处理状态更新消息
  const handleStatusUpdate = useCallback((data: WebSocketMessage) => {
    if (data.workflow_type === workflowType) {
      if (data.status !== undefined) {
        setStatus(data.status);

        // 工作流开始时清理旧的流式内容
        if (data.status === 'running') {
          clearStreamContentRef.current();
        }
      }
      if (data.current_step !== undefined) {
        setCurrentStep(data.current_step);
      }
      if (data.steps !== undefined) {
        // 合并后端步骤状态到预定义步骤
        const mergedSteps = mergeStepStatus(initialSteps, data.steps);
        setSteps(mergedSteps);
      }
      if (data.result !== undefined) {
        setResult(data.result);
        setIsStreaming(false);
      }
      if (data.error !== undefined) {
        setError(data.error);
        setIsStreaming(false);
      }
    }
  }, [workflowType, initialSteps]);

  // 处理流式内容消息
  const handleStreamContent = useCallback((data: WebSocketMessage) => {
    if (data.workflow_type === workflowType && data.node && data.content) {
      // 根据 content_type 区分思考内容和普通内容
      const isReasoning = data.content_type === 'reasoning';

      if (isReasoning) {
        // 思考内容
        setReasoningContent(prev => {
          const newMap = new Map(prev);
          const existing = newMap.get(data.node!) || '';
          newMap.set(data.node!, existing + data.content!);
          return newMap;
        });
      } else {
        // 普通内容
        setStreamContent(prev => {
          const newMap = new Map(prev);
          const existing = newMap.get(data.node!) || '';
          newMap.set(data.node!, existing + data.content!);
          return newMap;
        });
      }

      setCurrentNode(data.node);
      setIsStreaming(true);

      // 重置超时
      if (streamTimeoutRef.current) {
        clearTimeout(streamTimeoutRef.current);
      }
      streamTimeoutRef.current = setTimeout(() => {
        setIsStreaming(false);
      }, 3000);
    }
  }, [workflowType]);

  // 清除流式内容
  const clearStreamContent = useCallback(() => {
    clearStreamContentRef.current();
  }, [clearStreamContentRef]);

  // 获取指定节点的流式内容
  const getStreamContent = useCallback((node: string): string => {
    return streamContent.get(node) || '';
  }, [streamContent]);

  // 获取指定节点的思考内容
  const getReasoningContent = useCallback((node: string): string => {
    return reasoningContent.get(node) || '';
  }, [reasoningContent]);

  // 获取连接状态
  const getConnectionState = useCallback((): ConnectionState => {
    return connectionState;
  }, [connectionState]);

  // 连接方法
  const connect = useCallback((type: WorkflowType) => {
    setConnectionState('connecting');
    if (!wsRef.current) {
      wsRef.current = getWebSocket();
    }

    const wsInstance = wsRef.current;

    // 只注册一次事件监听器
    if (!listenersRegistered.current) {
      // 设置事件监听
      wsInstance.on('status_update', handleStatusUpdate);
      wsInstance.on('stream_content', handleStreamContent);

      // 监听连接状态变化
      wsInstance.on('open', () => {
        setConnectionState('connected');
        setReconnectAttempts(0);
      });

      wsInstance.on('close', () => {
        setConnectionState('disconnected');
        lastConnectedType.current = null;
      });

      wsInstance.on('error', () => {
        setConnectionState('disconnected');
        lastConnectedType.current = null;
      });

      listenersRegistered.current = true;
    }

    // 只有在工作流类型改变或未连接时才建立新连接
    if (!wsInstance.isConnected() || lastConnectedType.current !== type) {
      lastConnectedType.current = type;
      wsInstance.connect(type);
    }
  }, [handleStatusUpdate, handleStreamContent]);

  // 断开连接方法
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.off('status_update', handleStatusUpdate);
      wsRef.current.off('stream_content', handleStreamContent);
      wsRef.current.disconnect();
      wsRef.current = null;
      listenersRegistered.current = false;
    }
  }, [handleStatusUpdate, handleStreamContent]);

  // 切换工作流类型
  const switchWorkflow = useCallback((type: WorkflowType) => {
    if (wsRef.current) {
      wsRef.current.switchWorkflow(type);
      // 切换工作流时清理流式内容
      clearStreamContent();
    }
  }, [clearStreamContent]);

  // 组件挂载时连接
  useEffect(() => {
    connect(workflowType);

    return () => {
      disconnect();
    };
  }, [workflowType]); // 移除 connect 和 disconnect 从依赖数组，避免循环

  return {
    // 原有返回值
    status,
    steps,
    result,
    error,
    currentStep,

    // 新增返回值
    connectionState,
    reconnectAttempts,
    streamContent,
    reasoningContent,  // 思考内容
    currentNode,
    isStreaming,

    // 原有方法
    connect,
    disconnect,
    switchWorkflow,

    // 新增方法
    clearStreamContent,
    getStreamContent,
    getReasoningContent,  // 获取思考内容
    getConnectionState,
  };
}

export default useWebSocket;
