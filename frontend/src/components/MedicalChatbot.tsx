import { useRef, useState } from "react";
import { Loader2 } from "lucide-react";
import Sidebar from "./Sidebar";
import ChatArea from "./ChatArea";
import AuthModal from "./AuthModal";
import { useAuth } from "../hooks/useAuth";
import { useChat } from "../hooks/useChat";

export default function MedicalChatbot() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [inputValue, setInputValue] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const {
    user,
    isAuthenticated,
    isLoading: isAuthLoading,
    error: authError,
    login,
    register,
    logout,
    clearError,
  } = useAuth();

  const {
    history,
    messages,
    activeSessionId,
    models,
    selectedModelId,
    isLoading,
    isSending,
    error,
    config,
    searchMethod,
    loadSession,
    startNewChat,
    deleteSession,
    deleteAllSessions,
    sendMessage,
    uploadImage,
    selectModel,
    selectSearchMethod,
    bootstrap,
  } = useChat(isAuthenticated);

  const handleSend = async () => {
    const text = inputValue.trim();
    if (!text || isSending) return;
    setInputValue("");
    await sendMessage(text);
  };

  const handleFollowUp = async (question: string) => {
    if (isSending) return;
    await sendMessage(question);
  };

  const handleImageSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file || isSending) return;
    await uploadImage(file, inputValue.trim() || undefined);
    setInputValue("");
  };

  if (isAuthLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-surface-base">
        <Loader2 className="h-8 w-8 animate-spin text-accent/70" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <AuthModal
        error={authError}
        onLogin={login}
        onRegister={register}
        onClearError={clearError}
      />
    );
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen((open) => !open)}
        history={history}
        activeChatId={activeSessionId}
        user={user}
        onSelectChat={(id) => void loadSession(id)}
        onNewChat={startNewChat}
        onDeleteAll={() => void deleteAllSessions()}
        onDeleteChat={(id) => void deleteSession(id)}
        onLogout={logout}
      />

      <ChatArea
        messages={messages}
        inputValue={inputValue}
        onInputChange={setInputValue}
        onSend={() => void handleSend()}
        onFollowUp={(question) => void handleFollowUp(question)}
        onUploadClick={() => fileInputRef.current?.click()}
        models={models}
        selectedModelId={selectedModelId}
        onSelectModel={selectModel}
        searchMethods={config?.search_methods || []}
        selectedSearchMethod={searchMethod}
        onSelectSearchMethod={selectSearchMethod}
        isLoading={isLoading}
        isSending={isSending}
        error={error}
        onRetry={() => void bootstrap()}
      />

      <input
        ref={fileInputRef}
        type="file"
        accept="image/png,image/jpeg"
        className="hidden"
        onChange={(event) => void handleImageSelect(event)}
      />
    </div>
  );
}
