import axios from "axios";
import type {
  Token,
  LoginRequest,
  UserCreate,
  UserUpdate,
  UserResponse,
  TaskCreate,
  TaskUpdate,
  TaskStatusUpdate,
  TaskResponse,
  ChatRequest,
  ChatResponse,
  FileUploadResponse,
  AgentMessage,
} from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

// Add JWT token to requests
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle 401 responses
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("access_token");
        window.location.href = "/auth";
      }
    }
    return Promise.reject(err);
  }
);

// ——— Auth ——————————————————————————————————————————————————————————
export const authLogin = async (data: LoginRequest): Promise<Token> => {
  const res = await api.post<Token>("/api/v1/auth/login", data);
  return res.data;
};

export const authRegister = async (data: UserCreate): Promise<UserResponse> => {
  const res = await api.post<UserResponse>("/api/v1/users/", data);
  return res.data;
};

// ——— Users ——————————————————————————————————————————————————————————
export const getUsers = async (params?: {
  page?: number;
  page_size?: number;
  search?: string;
}): Promise<UserResponse[]> => {
  const res = await api.get<UserResponse[]>("/api/v1/users/", { params });
  return res.data;
};

export const getUser = async (userId: string): Promise<UserResponse> => {
  const res = await api.get<UserResponse>(`/api/v1/users/${userId}`);
  return res.data;
};

export const createUser = async (data: UserCreate): Promise<UserResponse> => {
  const res = await api.post<UserResponse>("/api/v1/users/", data);
  return res.data;
};

export const updateUser = async (
  userId: string,
  data: UserUpdate
): Promise<UserResponse> => {
  const res = await api.patch<UserResponse>(`/api/v1/users/${userId}`, data);
  return res.data;
};

export const deleteUser = async (userId: string): Promise<void> => {
  await api.delete(`/api/v1/users/${userId}`);
};

// ——— Tasks ——————————————————————————————————————————————————————————
export const getTasks = async (params?: {
  status?: string;
  owner_id?: string;
  search?: string;
  page?: number;
  page_size?: number;
}): Promise<TaskResponse[]> => {
  const res = await api.get<TaskResponse[]>("/api/v1/tasks/", { params });
  return res.data;
};

export const getTask = async (taskId: string): Promise<TaskResponse> => {
  const res = await api.get<TaskResponse>(`/api/v1/tasks/${taskId}`);
  return res.data;
};

export const createTask = async (data: TaskCreate): Promise<TaskResponse> => {
  const res = await api.post<TaskResponse>("/api/v1/tasks/", data);
  return res.data;
};

export const updateTask = async (
  taskId: string,
  data: TaskUpdate
): Promise<TaskResponse> => {
  const res = await api.patch<TaskResponse>(`/api/v1/tasks/${taskId}`, data);
  return res.data;
};

export const updateTaskStatus = async (
  taskId: string,
  data: TaskStatusUpdate
): Promise<TaskResponse> => {
  const res = await api.patch<TaskResponse>(`/api/v1/tasks/${taskId}/status`, data);
  return res.data;
};

export const retryTask = async (taskId: string): Promise<TaskResponse> => {
  const res = await api.patch<TaskResponse>(`/api/v1/tasks/${taskId}/retry`);
  return res.data;
};

export const cancelTask = async (taskId: string): Promise<TaskResponse> => {
  const res = await api.post<TaskResponse>(`/api/v1/tasks/${taskId}/cancel`);
  return res.data;
};

export const deleteTask = async (taskId: string): Promise<void> => {
  await api.delete(`/api/v1/tasks/${taskId}`);
};

// ——— Agent ——————————————————————————————————————————————————————————
export const chatWithAgent = async (
  data: ChatRequest
): Promise<ChatResponse> => {
  const res = await api.post<ChatResponse>("/api/v1/agent/chat", data);
  return res.data;
};

export const chatStreamWithAgent = async function* (
  messages: AgentMessage[],
  backend: string = "opensandbox"
): AsyncGenerator<string, void, unknown> {
  let retries = 3;
  while (retries > 0) {
    try {
      const res = await fetch(`${API_URL}/api/v1/agent/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(typeof window !== "undefined" && localStorage.getItem("access_token")
            ? { Authorization: `Bearer ${localStorage.getItem("access_token")}` }
            : {}),
        },
        body: JSON.stringify({ messages, backend, stream: true }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      if (!res.body) throw new Error("No response body");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = line.slice(6);
              if (data === "[DONE]") return;
              if (data.startsWith("ERROR:")) throw new Error(data.slice(6));
              yield data;
            }
          }
        }
        break; // 正常结束
      } finally {
        reader.releaseLock();
      }
    } catch (error) {
      retries--;
      if (retries === 0) throw error;
      // 指数退避: 1s, 2s
      await new Promise((r) => setTimeout(r, 1000 * (3 - retries)));
    }
  }
};

// ——— Files ——————————————————————————————————————————————————————————
export const uploadFile = async (file: File): Promise<FileUploadResponse> => {
  const formData = new FormData();
  formData.append("file", file);
  const res = await api.post<FileUploadResponse>("/api/v1/files/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
};

export const downloadFile = (filename: string): string => {
  return `${API_URL}/api/v1/files/${filename}`;
};

export const deleteFile = async (filename: string): Promise<void> => {
  await api.delete(`/api/v1/files/${filename}`);
};

// ——— Dashboard ——————————————————————————————————————————————————————————
export const getDashboardStats = async () => {
  const [users, tasks, agentHealth] = await Promise.all([
    getUsers({ page_size: 1 }).catch(() => []),
    getTasks({ page_size: 1 }).catch(() => []),
    api.get("/api/v1/agent/health").then(r => ({ ok: true })).catch(() => ({ ok: false })),
  ]);

  // Get total counts from list endpoints
  const [allUsers, allTasks] = await Promise.all([
    getUsers({ page_size: 1000 }).catch(() => []),
    getTasks({ page_size: 1000 }).catch(() => []),
  ]);

  return {
    user_count: allUsers.length,
    task_count: allTasks.length,
    agent_status: agentHealth.ok ? "ok" : "error",
  };
};
