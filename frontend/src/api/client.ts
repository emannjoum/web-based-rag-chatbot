import type {
  ApiAuthResponse,
  ApiChatCompletionResponse,
  ApiConfig,
  ApiErrorBody,
  ApiSessionDetail,
  ApiSessionSummary,
  ApiUser,
} from "../types/api";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
const TOKEN_STORAGE_KEY = "medatlas_access_token";

class ApiClientError extends Error {
  status: number;
  code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
  }
}

class ChatApiClient {
  private readonly baseUrl: string;
  private accessToken: string | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  setAccessToken(token: string | null): void {
    this.accessToken = token;
  }

  getStoredToken(): string | null {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  }

  persistToken(token: string | null): void {
    if (token) {
      localStorage.setItem(TOKEN_STORAGE_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
    }
    this.setAccessToken(token);
  }

  restoreTokenFromStorage(): string | null {
    const token = this.getStoredToken();
    this.setAccessToken(token);
    return token;
  }

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const headers: Record<string, string> = {
      Accept: "application/json",
      ...(init?.headers as Record<string, string> | undefined),
    };

    if (this.accessToken) {
      headers.Authorization = `Bearer ${this.accessToken}`;
    }

    const response = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      headers,
    });

    if (!response.ok) {
      let detail = `Request failed with status ${response.status}`;
      let code: string | undefined;
      try {
        const body = (await response.json()) as ApiErrorBody;
        detail = body.detail ?? detail;
        code = body.code;
      } catch {
        // ignore JSON parse errors
      }
      throw new ApiClientError(detail, response.status, code);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return (await response.json()) as T;
  }

  register(payload: {
    email: string;
    password: string;
    display_name: string;
  }): Promise<ApiAuthResponse> {
    return this.request("/api/v1/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  login(payload: { email: string; password: string }): Promise<ApiAuthResponse> {
    return this.request("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  getMe(): Promise<ApiUser> {
    return this.request("/api/v1/auth/me");
  }

  getHealth(): Promise<{ status: string }> {
    return this.request("/health");
  }

  getConfig(): Promise<ApiConfig> {
    return this.request("/api/v1/config");
  }

  listSessions(): Promise<{ sessions: ApiSessionSummary[] }> {
    return this.request("/api/v1/sessions");
  }

  getSession(sessionId: string): Promise<ApiSessionDetail> {
    return this.request(`/api/v1/sessions/${sessionId}`);
  }

  deleteSession(sessionId: string): Promise<{ deleted: boolean }> {
    return this.request(`/api/v1/sessions/${sessionId}`, { method: "DELETE" });
  }

  deleteAllSessions(): Promise<{ deleted_count: number }> {
    return this.request("/api/v1/sessions", { method: "DELETE" });
  }

  sendMessage(payload: {
    message: string;
    session_id?: string | null;
    model_id: string;
    search_method?: string;
  }): Promise<ApiChatCompletionResponse> {
    return this.request("/api/v1/chat/completions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  uploadImage(payload: {
    file: File;
    session_id?: string | null;
    model_id: string;
    caption?: string;
    search_method?: string;
  }): Promise<ApiChatCompletionResponse> {
    const formData = new FormData();
    formData.append("file", payload.file);
    if (payload.session_id) formData.append("session_id", payload.session_id);
    formData.append("model_id", payload.model_id);
    if (payload.caption) formData.append("caption", payload.caption);
    if (payload.search_method) formData.append("search_method", payload.search_method);

    return this.request("/api/v1/chat/image", {
      method: "POST",
      body: formData,
    });
  }
}

export const apiClient = new ChatApiClient();
export { ApiClientError, TOKEN_STORAGE_KEY };
