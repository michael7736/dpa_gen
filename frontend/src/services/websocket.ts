/**
 * WebSocket客户端服务
 * 用于实时进度推送和双向通信
 */

interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

interface PipelineProgressMessage extends WebSocketMessage {
  type: 'pipeline_progress';
  pipeline_id: string;
  document_id: string;
  overall_progress: number;
  current_stage: string;
  stages: Array<{
    id: string;
    name: string;
    status: string;
    progress: number;
    message: string;
    can_interrupt: boolean;
    started_at?: string;
    completed_at?: string;
    duration?: number;
    error?: string;
  }>;
  can_resume: boolean;
  interrupted: boolean;
  completed: boolean;
  timestamp: string;
}

interface StageUpdateMessage extends WebSocketMessage {
  type: 'stage_update';
  pipeline_id: string;
  stage_id: string;
  stage_type: string;
  stage_name: string;
  status: string;
  progress: number;
  message: string;
  timestamp: string;
}

type ProgressCallback = (progress: PipelineProgressMessage) => void;
type StageUpdateCallback = (update: StageUpdateMessage) => void;
type ConnectionCallback = (connected: boolean) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private progressCallbacks = new Map<string, ProgressCallback>();
  private stageUpdateCallbacks = new Map<string, StageUpdateCallback>();
  private connectionCallbacks = new Set<ConnectionCallback>();
  private isConnecting = false;
  private userId: string | null = null;
  private connectionId: string | null = null;
  private isDisabled = false; // 标记WebSocket是否被禁用

  constructor() {
    this.generateConnectionId();
  }

  private generateConnectionId() {
    this.connectionId = Math.random().toString(36).substr(2, 9);
  }

  /**
   * 连接WebSocket
   */
  async connect(userId: string): Promise<void> {
    if (this.isDisabled) {
      console.log('WebSocket已被禁用，跳过连接');
      return;
    }

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return;
    }

    if (this.isConnecting) {
      return;
    }

    this.userId = userId;
    this.isConnecting = true;

    try {
      // 首先检查后端是否可用
      const healthCheckUrl = 'http://localhost:8200/api/v1/health';
      try {
        const response = await fetch(healthCheckUrl);
        if (!response.ok) {
          throw new Error(`后端服务不可用: ${response.status}`);
        }
      } catch (error) {
        console.error('后端健康检查失败:', error);
        this.isConnecting = false;
        throw new Error('无法连接到后端服务，请确保API服务正在运行');
      }

      const wsUrl = `ws://localhost:8200/api/v1/ws/${userId}?connection_id=${this.connectionId}`;
      console.log('尝试连接WebSocket:', wsUrl);
      this.ws = new WebSocket(wsUrl);

      // 设置连接超时
      const connectTimeout = setTimeout(() => {
        if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
          console.error('WebSocket连接超时');
          this.ws.close();
          this.isConnecting = false;
          this.notifyConnectionCallbacks(false);
        }
      }, 10000); // 10秒超时

      this.ws.onopen = () => {
        console.log('WebSocket连接建立');
        clearTimeout(connectTimeout);
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.notifyConnectionCallbacks(true);
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('解析WebSocket消息失败:', error);
        }
      };

      this.ws.onclose = (event) => {
        console.log('WebSocket连接关闭:', event.code, event.reason);
        this.isConnecting = false;
        this.notifyConnectionCallbacks(false);
        
        // 自动重连
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        } else {
          console.warn('WebSocket重连次数超限，禁用WebSocket功能');
          this.isDisabled = true;
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
        console.error('WebSocket连接URL:', wsUrl);
        console.error('WebSocket状态:', this.ws?.readyState);
        this.isConnecting = false;
        this.notifyConnectionCallbacks(false);
      };

    } catch (error) {
      console.error('WebSocket连接失败:', error);
      this.isConnecting = false;
      throw error;
    }
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    this.reconnectAttempts = this.maxReconnectAttempts; // 阻止自动重连
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.progressCallbacks.clear();
    this.stageUpdateCallbacks.clear();
  }

  /**
   * 订阅管道进度
   */
  subscribePipelineProgress(pipelineId: string, callback: ProgressCallback): void {
    this.progressCallbacks.set(pipelineId, callback);
    
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.sendMessage({
        type: 'subscribe_pipeline',
        pipeline_id: pipelineId
      });
    }
  }

  /**
   * 取消订阅管道进度
   */
  unsubscribePipelineProgress(pipelineId: string): void {
    this.progressCallbacks.delete(pipelineId);
    
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.sendMessage({
        type: 'unsubscribe_pipeline',
        pipeline_id: pipelineId
      });
    }
  }

  /**
   * 订阅阶段更新
   */
  subscribeStageUpdates(pipelineId: string, callback: StageUpdateCallback): void {
    this.stageUpdateCallbacks.set(pipelineId, callback);
  }

  /**
   * 取消订阅阶段更新
   */
  unsubscribeStageUpdates(pipelineId: string): void {
    this.stageUpdateCallbacks.delete(pipelineId);
  }

  /**
   * 监听连接状态变化
   */
  onConnectionChange(callback: ConnectionCallback): void {
    this.connectionCallbacks.add(callback);
  }

  /**
   * 取消监听连接状态变化
   */
  offConnectionChange(callback: ConnectionCallback): void {
    this.connectionCallbacks.delete(callback);
  }

  /**
   * 获取连接状态
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * 检查WebSocket是否可用
   */
  isAvailable(): boolean {
    return !this.isDisabled && this.isConnected();
  }

  /**
   * 发送心跳
   */
  ping(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.sendMessage({
        type: 'ping',
        timestamp: Date.now()
      });
    }
  }

  /**
   * 获取连接统计
   */
  getStats(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.sendMessage({
        type: 'get_status'
      });
    }
  }

  private sendMessage(message: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  private handleMessage(message: WebSocketMessage): void {
    switch (message.type) {
      case 'connection':
        console.log('WebSocket连接确认:', message);
        break;

      case 'pipeline_progress':
        const progressMsg = message as PipelineProgressMessage;
        const progressCallback = this.progressCallbacks.get(progressMsg.pipeline_id);
        if (progressCallback) {
          progressCallback(progressMsg);
        }
        break;

      case 'stage_update':
        const stageMsg = message as StageUpdateMessage;
        const stageCallback = this.stageUpdateCallbacks.get(stageMsg.pipeline_id);
        if (stageCallback) {
          stageCallback(stageMsg);
        }
        break;

      case 'subscription_confirmed':
        console.log('订阅确认:', message);
        break;

      case 'unsubscription_confirmed':
        console.log('取消订阅确认:', message);
        break;

      case 'pong':
        console.log('心跳响应:', message);
        break;

      case 'status':
        console.log('连接状态:', message);
        break;

      case 'error':
        console.error('WebSocket错误消息:', message.message);
        break;

      default:
        console.log('未知消息类型:', message);
    }
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`计划重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts}), ${delay}ms后重试`);
    
    setTimeout(() => {
      if (this.userId) {
        this.connect(this.userId);
      }
    }, delay);
  }

  private notifyConnectionCallbacks(connected: boolean): void {
    this.connectionCallbacks.forEach(callback => {
      try {
        callback(connected);
      } catch (error) {
        console.error('连接状态回调错误:', error);
      }
    });
  }
}

// 全局WebSocket服务实例
export const webSocketService = new WebSocketService();

export type {
  WebSocketMessage,
  PipelineProgressMessage,
  StageUpdateMessage,
  ProgressCallback,
  StageUpdateCallback,
  ConnectionCallback
};