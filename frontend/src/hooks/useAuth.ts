import { useCallback, useEffect, useState } from "react";
import { apiClient, ApiClientError } from "../api/client";
import type { ApiUser } from "../types/api";

interface UseAuthState {
  user: ApiUser | null;
  isLoading: boolean;
  error: string | null;
}

export function useAuth() {
  const [state, setState] = useState<UseAuthState>({
    user: null,
    isLoading: true,
    error: null,
  });

  const applyAuthResponse = useCallback((user: ApiUser, token: string) => {
    apiClient.persistToken(token);
    setState({ user, isLoading: false, error: null });
  }, []);

  const restoreSession = useCallback(async () => {
    setState((current) => ({ ...current, isLoading: true, error: null }));
    const token = apiClient.restoreTokenFromStorage();
    if (!token) {
      setState({ user: null, isLoading: false, error: null });
      return;
    }

    try {
      const user = await apiClient.getMe();
      setState({ user, isLoading: false, error: null });
    } catch {
      apiClient.persistToken(null);
      setState({ user: null, isLoading: false, error: null });
    }
  }, []);

  useEffect(() => {
    void restoreSession();
  }, [restoreSession]);

  const login = useCallback(
    async (email: string, password: string) => {
      setState((current) => ({ ...current, error: null }));
      try {
        const response = await apiClient.login({ email, password });
        applyAuthResponse(response.user, response.access_token);
      } catch (error) {
        const message =
          error instanceof ApiClientError ? error.message : "Unable to sign in.";
        setState((current) => ({ ...current, error: message }));
        throw error;
      }
    },
    [applyAuthResponse],
  );

  const register = useCallback(
    async (email: string, password: string, displayName: string) => {
      setState((current) => ({ ...current, error: null }));
      try {
        const response = await apiClient.register({
          email,
          password,
          display_name: displayName,
        });
        applyAuthResponse(response.user, response.access_token);
      } catch (error) {
        const message =
          error instanceof ApiClientError ? error.message : "Unable to create account.";
        setState((current) => ({ ...current, error: message }));
        throw error;
      }
    },
    [applyAuthResponse],
  );

  const logout = useCallback(() => {
    apiClient.persistToken(null);
    setState({ user: null, isLoading: false, error: null });
  }, []);

  return {
    user: state.user,
    isAuthenticated: state.user !== null,
    isLoading: state.isLoading,
    error: state.error,
    login,
    register,
    logout,
    clearError: () => setState((current) => ({ ...current, error: null })),
  };
}
