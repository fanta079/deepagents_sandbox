/**
 * WebSocket 客户端 — 支持指数退避重连
 *
 * 基于 socket.io-client，包装以下增强：
 * - 指数退避重连（1s → 2s → 4s → ... → maxDelay）
 * - 最多重试 maxRetries 次
 * - 重试时触发事件，方便 UI 更新状态
 * - 超出最大重试次数后彻底放弃
 */

import { io, Socket } from "socket.io-client";

export interface ReconnectingSocketOptions {
  url: string;
  path?: string;
  query?: Record<string, string>;
  /** 最大重试次数（默认 10） */
  maxRetries?: number;
  /** 初始重连延迟 ms（默认 1000） */
  baseDelay?: number;
  /** 最大重连延迟 ms（默认 30000） */
  maxDelay?: number;
  /** 连接超时 ms（默认 20000） */
  connectTimeout?: number;
}

export interface ReconnectingSocketEvents {
  onConnect?: (socket: Socket) => void;
  onDisconnect?: (reason: string) => void;
  onConnectError?: (error: Error) => void;
  onReconnecting?: (attempt: number, delay: number) => void;
  onReconnectFailed?: () => void;
  onMessage?: (data: unknown) => void;
  onSystem?: (data: unknown) => void;
  onPersonal?: (data: unknown) => void;
  [event: string]: ((...args: unknown[]) => void) | undefined;
}

export class ReconnectingWebSocket {
  private socket: Socket | null = null;
  private url: string;
  private path: string;
  private query: Record<string, string>;
  private retryCount = 0;
  private maxRetries: number;
  private baseDelay: number;
  private maxDelay: number;
  private connectTimeout: number;
  private retryTimer: ReturnType<typeof setTimeout> | null = null;
  private manuallyDisconnected = false;

  // 事件回调
  public onConnect?: (socket: Socket) => void;
  public onDisconnect?: (reason: string) => void;
  public onConnectError?: (error: Error) => void;
  public onReconnecting?: (attempt: number, delay: number) => void;
  public onReconnectFailed?: () => void;
  public onMessage?: (data: unknown) => void;
  public onSystem?: (data: unknown) => void;
  public onPersonal?: (data: unknown) => void;

  constructor(options: ReconnectingSocketOptions) {
    this.url = options.url;
    this.path = options.path ?? "/ws";
    this.query = options.query ?? {};
    this.maxRetries = options.maxRetries ?? 10;
    this.baseDelay = options.baseDelay ?? 1000;
    this.maxDelay = options.maxDelay ?? 30000;
    this.connectTimeout = options.connectTimeout ?? 20000;

    this.connect();
  }

  /** 计算指数退避延迟 */
  private getBackoffDelay(): number {
    const delay = this.baseDelay * Math.pow(2, this.retryCount);
    return Math.min(delay, this.maxDelay);
  }

  private connect(): void {
    // 清理旧连接
    if (this.socket) {
      this.socket.removeAllListeners();
      if (this.socket.connected) {
        this.socket.disconnect();
      }
    }

    this.socket = io(this.url, {
      path: this.path,
      query: this.query,
      transports: ["websocket"],
      reconnection: false, // 我们自己控制重连
      timeout: this.connectTimeout,
    });

    this.socket.on("connect", () => {
      console.log("[ReconnectingWebSocket] 已连接");
      this.retryCount = 0; // 重置重试计数
      if (this.onConnect) this.onConnect(this.socket!);
    });

    this.socket.on("disconnect", (reason: string) => {
      console.log(`[ReconnectingWebSocket] 断开: ${reason}`);
      if (this.onDisconnect) this.onDisconnect(reason);
      if (!this.manuallyDisconnected) {
        this.scheduleReconnect();
      }
    });

    this.socket.on("connect_error", (error: Error) => {
      console.error(`[ReconnectingWebSocket] 连接错误: ${error.message}`);
      if (this.onConnectError) this.onConnectError(error);
      if (!this.manuallyDisconnected) {
        this.scheduleReconnect();
      }
    });

    this.socket.on("message", (data: unknown) => {
      if (this.onMessage) this.onMessage(data);
    });

    this.socket.on("system", (data: unknown) => {
      if (this.onSystem) this.onSystem(data);
    });

    this.socket.on("personal", (data: unknown) => {
      if (this.onPersonal) this.onPersonal(data);
    });
  }

  private scheduleReconnect(): void {
    if (this.manuallyDisconnected) return;

    this.retryCount++;
    if (this.retryCount > this.maxRetries) {
      console.error(`[ReconnectingWebSocket] 超过最大重试次数 (${this.maxRetries})，放弃重连`);
      if (this.onReconnectFailed) this.onReconnectFailed();
      return;
    }

    const delay = this.getBackoffDelay();
    console.log(`[ReconnectingWebSocket] 第 ${this.retryCount}/${this.maxRetries} 次重连，${delay}ms 后...`);

    if (this.onReconnecting) this.onReconnecting(this.retryCount, delay);

    this.retryTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  /** 主动断开（不再自动重连） */
  public disconnect(): void {
    this.manuallyDisconnected = true;
    if (this.retryTimer) {
      clearTimeout(this.retryTimer);
      this.retryTimer = null;
    }
    if (this.socket) {
      this.socket.removeAllListeners();
      this.socket.disconnect();
      this.socket = null;
    }
  }

  /** 发送消息 */
  public send(event: string, data?: unknown): boolean {
    if (this.socket?.connected) {
      this.socket.emit(event, typeof data === "string" ? data : JSON.stringify(data));
      return true;
    }
    return false;
  }

  /** 获取底层 socket */
  public getSocket(): Socket | null {
    return this.socket;
  }

  /** 是否已连接 */
  public isConnected(): boolean {
    return this.socket?.connected ?? false;
  }
}
