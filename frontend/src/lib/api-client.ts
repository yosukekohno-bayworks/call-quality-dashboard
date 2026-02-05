import { ApiError, AuthTokens } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const TOKEN_KEY = "auth_tokens";

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private getTokens(): AuthTokens | null {
    if (typeof window === "undefined") return null;
    const stored = localStorage.getItem(TOKEN_KEY);
    return stored ? JSON.parse(stored) : null;
  }

  private setTokens(tokens: AuthTokens | null): void {
    if (typeof window === "undefined") return;
    if (tokens) {
      localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens));
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
  }

  private async refreshToken(): Promise<boolean> {
    const tokens = this.getTokens();
    if (!tokens?.refreshToken) return false;

    try {
      const response = await fetch(`${this.baseUrl}/api/auth/refresh`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ refreshToken: tokens.refreshToken }),
      });

      if (!response.ok) {
        this.setTokens(null);
        return false;
      }

      const newTokens = await response.json();
      this.setTokens(newTokens);
      return true;
    } catch {
      this.setTokens(null);
      return false;
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retry = true
  ): Promise<T> {
    const tokens = this.getTokens();
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    if (tokens?.accessToken) {
      (headers as Record<string, string>)["Authorization"] = `Bearer ${tokens.accessToken}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    // Handle 401 - try to refresh token
    if (response.status === 401 && retry) {
      const refreshed = await this.refreshToken();
      if (refreshed) {
        return this.request<T>(endpoint, options, false);
      }
      // Redirect to login if refresh failed
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
      throw new Error("認証の有効期限が切れました。再度ログインしてください。");
    }

    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({
        message: "エラーが発生しました",
      }));
      throw new Error(error.message);
    }

    // Handle empty response
    const text = await response.text();
    return text ? JSON.parse(text) : ({} as T);
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: "GET" });
  }

  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: "PUT",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async patch<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: "PATCH",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: "DELETE" });
  }

  async upload<T>(endpoint: string, formData: FormData): Promise<T> {
    const tokens = this.getTokens();
    const headers: HeadersInit = {};

    if (tokens?.accessToken) {
      headers["Authorization"] = `Bearer ${tokens.accessToken}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "POST",
      headers,
      body: formData,
    });

    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({
        message: "アップロードに失敗しました",
      }));
      throw new Error(error.message);
    }

    return response.json();
  }
}

export const apiClient = new ApiClient(API_BASE_URL);
