import { useCallback, useEffect, useState } from "react";
import { apiClient, ApiClientError } from "../api/client";
import type {
  ApiConfig,
  ApiModelOption,
  ChatHistoryItem,
  ChatMessage,
} from "../types/api";

interface UseChatState {
  config: ApiConfig | null;
  history: ChatHistoryItem[];
  messages: ChatMessage[];
  activeSessionId: string | null;
  selectedModelId: string;
  searchMethod: string;
  isLoading: boolean;
  isSending: boolean;
  error: string | null;
}

export function useChat(isAuthenticated: boolean) {
  const [state, setState] = useState<UseChatState>({
    config: null,
    history: [],
    messages: [],
    activeSessionId: null,
    selectedModelId: "",
    searchMethod: "Serper",
    isLoading: true,
    isSending: false,
    error: null,
  });

  const setError = useCallback((error: string | null) => {
    setState((current) => ({ ...current, error }));
  }, []);

  const refreshHistory = useCallback(async () => {
    const { sessions } = await apiClient.listSessions();
    setState((current) => ({
      ...current,
      history: sessions.map((session) => ({
        id: session.id,
        title: session.title,
        lastActive: session.last_active,
      })),
    }));
  }, []);

  const bootstrap = useCallback(async () => {
    setState((current) => ({ ...current, isLoading: true, error: null }));
    try {
      await apiClient.getHealth();
      const config = await apiClient.getConfig();
      await refreshHistory();
      setState((current) => ({
        ...current,
        config,
        selectedModelId: config.default_model_id,
        searchMethod: config.default_search_method,
        isLoading: false,
      }));
    } catch (error) {
      const message =
        error instanceof ApiClientError
          ? error.message
          : "Unable to reach the MedAtlas API. Ensure the backend is running.";
      setState((current) => ({
        ...current,
        isLoading: false,
        error: message,
      }));
    }
  }, [refreshHistory]);

  useEffect(() => {
    if (!isAuthenticated) {
      setState({
        config: null,
        history: [],
        messages: [],
        activeSessionId: null,
        selectedModelId: "",
        searchMethod: "Serper",
        isLoading: false,
        isSending: false,
        error: null,
      });
      return;
    }
    void bootstrap();
  }, [bootstrap, isAuthenticated]);

  useEffect(() => {
    const sessionId = state.activeSessionId;
    if (!sessionId || state.isSending || state.isLoading) return;

    const lastAssistant = [...state.messages].reverse().find((m) => m.role === "assistant");
    if (
      !lastAssistant ||
      lastAssistant.ragas_eval ||
      lastAssistant.eval_status === "success" ||
      lastAssistant.eval_status === "failed"
    ) {
      return;
    }
    if (!lastAssistant.sources || Object.keys(lastAssistant.sources).length === 0) return;

    let cancelled = false;
    let attempts = 0;
    const maxAttempts = 15;

    const poll = async () => {
      if (cancelled || attempts >= maxAttempts) return;
      attempts += 1;

      try {
        const detail = await apiClient.getSession(sessionId);
        if (cancelled) return;

        const updatedAssistant = [...detail.messages]
          .reverse()
          .find((m) => m.role === "assistant");

        if (
          updatedAssistant?.ragas_eval ||
          updatedAssistant?.eval_status === "success" ||
          updatedAssistant?.eval_status === "failed"
        ) {
          setState((current) => ({
            ...current,
            messages: detail.messages,
          }));
          return;
        }

        setTimeout(poll, 2000);
      } catch {
        // Silently stop polling on error
      }
    };

    const timer = setTimeout(poll, 2000);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [state.activeSessionId, state.isSending, state.isLoading, state.messages]);

  const loadSession = useCallback(async (sessionId: string) => {
    setState((current) => ({ ...current, isLoading: true, error: null }));
    try {
      const detail = await apiClient.getSession(sessionId);
      setState((current) => ({
        ...current,
        activeSessionId: detail.session_id,
        messages: detail.messages,
        isLoading: false,
      }));
    } catch (error) {
      const message =
        error instanceof ApiClientError ? error.message : "Failed to load session.";
      setState((current) => ({ ...current, isLoading: false, error: message }));
    }
  }, []);

  const startNewChat = useCallback(() => {
    setState((current) => ({
      ...current,
      activeSessionId: null,
      messages: [],
      error: null,
    }));
  }, []);

  const deleteSession = useCallback(
    async (sessionId: string) => {
      try {
        await apiClient.deleteSession(sessionId);
        await refreshHistory();
        setState((current) => ({
          ...current,
          activeSessionId: current.activeSessionId === sessionId ? null : current.activeSessionId,
          messages: current.activeSessionId === sessionId ? [] : current.messages,
        }));
      } catch (error) {
        const message =
          error instanceof ApiClientError ? error.message : "Failed to delete session.";
        setError(message);
      }
    },
    [refreshHistory, setError],
  );

  const deleteAllSessions = useCallback(async () => {
    try {
      await apiClient.deleteAllSessions();
      setState((current) => ({
        ...current,
        activeSessionId: null,
        messages: [],
        history: [],
      }));
    } catch (error) {
      const message =
        error instanceof ApiClientError ? error.message : "Failed to delete all sessions.";
      setError(message);
    }
  }, [setError]);

  const sendMessage = useCallback(
    async (message: string) => {
      if (!message.trim() || !state.selectedModelId) return;

      const optimisticUser: ChatMessage = { role: "user", content: message.trim() };
      setState((current) => ({
        ...current,
        messages: [...current.messages, optimisticUser],
        isSending: true,
        error: null,
      }));

      try {
        const response = await apiClient.sendMessage({
          message: message.trim(),
          session_id: state.activeSessionId,
          model_id: state.selectedModelId,
          search_method: state.searchMethod,
        });

        setState((current) => ({
          ...current,
          activeSessionId: response.session_id,
          messages: [
            ...current.messages.slice(0, -1),
            response.user_message,
            response.assistant_message,
          ],
          isSending: false,
        }));
        await refreshHistory();
      } catch (error) {
        const messageText =
          error instanceof ApiClientError ? error.message : "Failed to send message.";
        setState((current) => ({
          ...current,
          messages: current.messages.slice(0, -1),
          isSending: false,
          error: messageText,
        }));
      }
    },
    [refreshHistory, state.activeSessionId, state.searchMethod, state.selectedModelId],
  );

  const uploadImage = useCallback(
    async (file: File, caption?: string) => {
      if (!state.selectedModelId) return;

      setState((current) => ({ ...current, isSending: true, error: null }));
      try {
        const response = await apiClient.uploadImage({
          file,
          session_id: state.activeSessionId,
          model_id: state.selectedModelId,
          caption,
          search_method: state.searchMethod,
        });

        setState((current) => ({
          ...current,
          activeSessionId: response.session_id,
          messages: [
            ...current.messages,
            response.user_message,
            response.assistant_message,
          ],
          isSending: false,
        }));
        await refreshHistory();
      } catch (error) {
        const messageText =
          error instanceof ApiClientError ? error.message : "Failed to upload image.";
        setState((current) => ({ ...current, isSending: false, error: messageText }));
      }
    },
    [refreshHistory, state.activeSessionId, state.searchMethod, state.selectedModelId],
  );

  const selectSearchMethod = useCallback((method: string) => {
    setState((current) => ({ ...current, searchMethod: method }));
  }, []);

  const selectModel = useCallback((modelId: string) => {
    setState((current) => ({ ...current, selectedModelId: modelId }));
  }, []);

  const models: ApiModelOption[] = state.config?.models ?? [];

  return {
    ...state,
    models,
    bootstrap,
    loadSession,
    startNewChat,
    deleteSession,
    deleteAllSessions,
    sendMessage,
    uploadImage,
    selectModel,
    selectSearchMethod,
    setError,
  };
}
