import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import * as authApi from '@/lib/api/authApi';
import { setUnauthorizedHandler } from '@/lib/api/client';
import type { CurrentUser } from '@/types/domain';

/** Discriminated union: no "user may be undefined while authenticated" ambiguity. */
export type AuthState =
  | { status: 'loading'; user: null }
  | { status: 'authenticated'; user: CurrentUser }
  | { status: 'unauthenticated'; user: null };

interface AuthContextValue {
  state: AuthState;
  user: CurrentUser | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({ status: 'loading', user: null });

  // Session lives in an httpOnly cookie managed by the backend; the client only
  // keeps the (non-sensitive) user profile in memory.
  useEffect(() => {
    let active = true;
    authApi.getCurrentUser().then((user) => {
      if (!active) return;
      setState(user ? { status: 'authenticated', user } : { status: 'unauthenticated', user: null });
    });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(() => setState({ status: 'unauthenticated', user: null }));
    return () => setUnauthorizedHandler(null);
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const user = await authApi.login({ username, password });
    setState({ status: 'authenticated', user });
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      setState({ status: 'unauthenticated', user: null });
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ state, user: state.user, isAuthenticated: state.status === 'authenticated', login, logout }),
    [state, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
