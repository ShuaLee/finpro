/* eslint-disable react-refresh/only-export-components */
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { getAuthStatus, login as loginRequest, logout as logoutRequest, refreshSession } from "../api/auth";
import { ApiError } from "../api/http";

type AuthUser = {
  email: string;
  isEmailVerified: boolean;
  isLocked: boolean;
};

type AuthContextValue = {
  user: AuthUser | null;
  loading: boolean;
  refreshAuth: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function mapStatusToUser(status: Awaited<ReturnType<typeof getAuthStatus>>): AuthUser | null {
  if (!status.authenticated || !status.email) {
    return null;
  }

  return {
    email: status.email,
    isEmailVerified: Boolean(status.is_email_verified),
    isLocked: Boolean(status.is_locked),
  };
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshAuth = useCallback(async () => {
    try {
      const status = await getAuthStatus();
      setUser(mapStatusToUser(status));
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) {
        try {
          await refreshSession();
          const refreshedStatus = await getAuthStatus();
          setUser(mapStatusToUser(refreshedStatus));
          return;
        } catch (refreshCaught) {
          if (refreshCaught instanceof ApiError && refreshCaught.status === 401) {
            setUser(null);
            return;
          }
          throw refreshCaught;
        }
      }
      throw caught;
    }
  }, []);

  useEffect(() => {
    const boot = async () => {
      try {
        await refreshAuth();
      } finally {
        setLoading(false);
      }
    };

    void boot();
  }, [refreshAuth]);

  const login = useCallback(async (email: string, password: string) => {
    await loginRequest(email, password);
    await refreshAuth();
  }, [refreshAuth]);

  const logout = useCallback(async () => {
    await logoutRequest();
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    loading,
    refreshAuth,
    login,
    logout,
  }), [user, loading, refreshAuth, login, logout]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
