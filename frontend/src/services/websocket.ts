/**
 * WebSocket 服务
 * 处理与后端的实时通信
 */
import type { WorkflowType, WebSocketMessage } from '../types';

// 事件回调类型
type EventCallback = (data: any) => void;

/**
 * 工作流 WebSocket 类
 */
export class WorkflowWebSocket {
  private ws: WebSocket | null = null;
  private listeners = new Map<string, EventCallback[]>();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 2000;
  private workflowType: WorkflowType = 'drawing';
  readonly url: string;

  constructor(url: string) {
    this.url = url;
  }

  /**
   * 连接到 WebSocket 服务器
   */
  connect(workflowType: WorkflowType): void {
    this.workflowType = workflowType;
    // Reset reconnect counter — a new connect() call means we want a fresh attempt,
    // regardless of any previous disconnect() that set it to max.
    this.reconnectAttempts = 0;
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log(`[WebSocket] Connected to ${this.url}`);
      this.reconnectAttempts = 0;
      // 触发 open 事件
      this.emit('open', { workflow_type: workflowType, type: 'open' });
      // 发送工作流类型
      this.send({ workflow_type: workflowType });
    };

    this.ws.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);
        console.log('[WebSocket] Message received:', data);
        this.emit(data.type || 'message', data);
      } catch (error) {
        console.error('[WebSocket] Failed to parse message:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('[WebSocket] Error:', error);
      // 触发 error 事件
      this.emit('error', { workflow_type: workflowType, type: 'error' });
    };

    this.ws.onclose = () => {
      console.log('[WebSocket] Closed');
      // 触发 close 事件
      this.emit('close', { workflow_type: workflowType, type: 'close' });
      this.attemptReconnect(workflowType);
    };
  }

  /**
   * 发送消息
   */
  send(data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = JSON.stringify(data);
      console.log('[WebSocket] Sending:', data);
      this.ws.send(message);
    } else {
      console.warn('[WebSocket] Cannot send: connection not open');
    }
  }

  /**
   * 监听事件
   */
  on(event: string, callback: EventCallback): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(callback);
  }

  /**
   * 移除事件监听
   */
  off(event: string, callback: EventCallback): void {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event)!;
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  /**
   * 触发事件
   */
  private emit(event: string, data: any): void {
    if (this.listeners.has(event)) {
      this.listeners.get(event)!.forEach((cb) => cb(data));
    }
  }

  /**
   * 尝试重连
   */
  private attemptReconnect(workflowType: WorkflowType): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(
        `[WebSocket] Reconnecting... attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`
      );
      setTimeout(() => {
        this.connect(workflowType);
      }, this.reconnectDelay);
    } else {
      console.error('[WebSocket] Max reconnection attempts reached');
    }
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    if (this.ws) {
      this.reconnectAttempts = this.maxReconnectAttempts;
      this.ws.onopen = null;
      this.ws.onmessage = null;
      this.ws.onerror = null;
      this.ws.onclose = null;
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * 切换工作流类型
   */
  switchWorkflow(workflowType: WorkflowType): void {
    if (this.workflowType !== workflowType) {
      console.log(`[WebSocket] Switching workflow: ${this.workflowType} -> ${workflowType}`);
      this.workflowType = workflowType;
      this.send({ workflow_type: workflowType });
    }
  }

  /**
   * 检查是否已连接
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// 单例 WebSocket 实例
let wsInstance: WorkflowWebSocket | null = null;

/**
 * 获取 WebSocket 单例实例
 */
export const getWebSocket = (): WorkflowWebSocket => {
  if (!wsInstance) {
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:5001/ws';
    wsInstance = new WorkflowWebSocket(wsUrl);
  }
  return wsInstance;
};

/**
 * 重置 WebSocket 实例
 */
export const resetWebSocket = (): void => {
  if (wsInstance) {
    wsInstance.disconnect();
    wsInstance = null;
  }
};
