export type UserRole = "admin" | "sv" | "qa" | "operator" | "executive";

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  tenantId: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, string[]>;
}
