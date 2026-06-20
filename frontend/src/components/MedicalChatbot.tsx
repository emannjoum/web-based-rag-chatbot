import { useRef, useState } from "react";
import Sidebar from "./Sidebar";
import ChatArea from "./ChatArea";
import { useChat } from "../hooks/useChat";

export default function MedicalChatbot() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [inputValue, setInputValue] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const {
    history,
    messages,
    activeSessionId,
    models,
    selectedModelId,
    isLoading,
    isSending,
    error,
    loadSession,
    startNewChat,
    deleteSession,
    deleteAllSessions,
    sendMessage,
    uploadImage,
    selectModel,
    bootstrap,
  } = useChat();

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

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen((open) => !open)}
        history={history}
        activeChatId={activeSessionId}
        onSelectChat={(id) => void loadSession(id)}
        onNewChat={startNewChat}
        onDeleteAll={() => void deleteAllSessions()}
        onDeleteChat={(id) => void deleteSession(id)}
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
