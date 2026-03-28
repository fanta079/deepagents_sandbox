// User types
export interface UserBase {
  username: string;
  email: string;
  full_name?: string;
}

export interface UserCreate extends UserBase {
  password: string;
}

export interface UserUpdate {
  email?: string;
  full_name?: string;
  password?: string;
  is_active?: boolean;
}

export interface UserResponse extends UserBase {
  id: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
}

// Auth types
export interface Token {
  access_token: string;
  token_type: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

// Task types
export type TaskStatus = "pending" | "running" | "success" | "failed" | "cancelled";
export type TaskPriority = "low" | "normal" | "high" | "urgent";

export interface TaskBase {
  title: string;
  description?: string;
  priority: TaskPriority;
  tags?: string[];
}

export interface TaskCreate extends TaskBase {
  owner_id: string;
  max_retries?: number;
}

export interface TaskUpdate {
  title?: string;
  description?: string;
  priority?: TaskPriority;
  max_retries?: number;
  progress?: number;
  tags?: string[];
}

export interface TaskStatusUpdate {
  status: TaskStatus;
  result?: string;
  error?: string;
  progress?: number;
}

export interface TaskResponse extends TaskBase {
  id: string;
  status: TaskStatus;
  result?: string;
  error?: string;
  progress: number;
  retry_count: number;
  max_retries: number;
  owner_id: string;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
}

// Agent types
export interface AgentMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequest {
  messages: AgentMessage[];
  backend?: string;
  stream?: boolean;
}

export interface ChatResponse {
  message: string;
  finish_reason?: string;
  backend: string;
}

// File types
export interface FileUploadResponse {
  filename: string;
  original_filename: string;
  size: number;
  url: string;
}

// WebSocket types
export interface WSMessage {
  type: "message" | "system" | "personal";
  user_id?: string;
  from?: string;
  to?: string;
  content: string;
  timestamp: string;
}

// Dashboard stats
export interface DashboardStats {
  user_count: number;
  task_count: number;
  agent_status: "ok" | "error";
}
