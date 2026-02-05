"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { AuthTokens, LoginCredentials, User } from "./types";

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = "auth_tokens";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const getStoredTokens = (): AuthTokens | null => {
    if (typeof window === "undefined") return null;
    const stored = localStorage.getItem(TOKEN_KEY);
    return stored ? JSON.parse(stored) : null;
  };

  const setStoredTokens = (tokens: AuthTokens | null) => {
    if (typeof window === "undefined") return;
    if (tokens) {
      localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens));
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
  };

  const fetchUser = useCallback(async (accessToken: string): Promise<User | null> => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/users/me`,
        {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        }
      );
      if (!response.ok) return null;
      return await response.json();
    } catch {
      return null;
    }
  }, []);

  const refreshAccessToken = useCallback(async (refreshToken: string): Promise<AuthTokens | null> => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/auth/refresh`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ refreshToken }),
        }
      );
      if (!response.ok) return null;
      return await response.json();
    } catch {
      return null;
    }
  }, []);

  useEffect(() => {
    const initAuth = async () => {
      const tokens = getStoredTokens();
      if (!tokens) {
        setIsLoading(false);
        return;
      }

      let currentUser = await fetchUser(tokens.accessToken);

      if (!currentUser && tokens.refreshToken) {
        const newTokens = await refreshAccessToken(tokens.refreshToken);
        if (newTokens) {
          setStoredTokens(newTokens);
          currentUser = await fetchUser(newTokens.accessToken);
        }
      }

      if (currentUser) {
        setUser(currentUser);
      } else {
        setStoredTokens(null);
      }

      setIsLoading(false);
    };

    initAuth();
  }, [fetchUser, refreshAccessToken]);

  const login = async (credentials: LoginCredentials) => {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/auth/login`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(credentials),
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "ログインに失敗しました");
    }

    const data = await response.json();
    setStoredTokens({ accessToken: data.accessToken, refreshToken: data.refreshToken });
    setUser(data.user);
  };

  const loginWithGoogle = async () => {
    // Google OAuthフローを開始
    window.location.href = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/auth/google`;
  };

  const logout = () => {
    setStoredTokens(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        loginWithGoogle,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
