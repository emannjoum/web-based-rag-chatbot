import { Loader2, Lock, Triangle } from "lucide-react";
import AssistantMessage from "./AssistantMessage";
import ChatInput from "./ChatInput";
import type { ApiModelOption, ChatMessage } from "../types/api";
import { sourcesToLinks } from "../types/api";

interface ChatAreaProps {
  messages: ChatMessage[];
  inputValue: string;
  onInputChange: (value: string) => void;
  onSend: () => void;
  onFollowUp: (question: string) => void;
  onUploadClick: () => void;
  models: ApiModelOption[];
  selectedModelId: string;
  onSelectModel: (modelId: string) => void;
  searchMethods: string[];
  selectedSearchMethod: string;
  onSelectSearchMethod: (method: string) => void;
  isLoading: boolean;
  isSending: boolean;
  error: string | null;
  onRetry: () => void;
}

export default function ChatArea({
  messages,
  inputValue,
  onInputChange,
  onSend,
  onFollowUp,
  onUploadClick,
  models,
  selectedModelId,
  onSelectModel,
  searchMethods,
  selectedSearchMethod,
  onSelectSearchMethod,
  isLoading,
  isSending,
  error,
  onRetry,
}: ChatAreaProps) {
  const lastAssistantIndex = [...messages]
    .map((message, index) => ({ message, index }))
    .reverse()
    .find(({ message }) => message.role === "assistant")?.index;

  return (
    <main className="relative flex min-w-0 flex-1 flex-col bg-[#212121]">

      {error && (
        <div className="mx-4 mt-3 flex items-center justify-between rounded-lg border border-red-900/60 bg-red-950/30 px-4 py-2 text-sm text-red-300 sm:mx-6">
          <span>{error}</span>
          <button
            type="button"
            onClick={onRetry}
            className="text-xs font-medium text-red-200 underline-offset-2 hover:underline"
          >
            Retry
          </button>
        </div>
      )}

      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex h-full items-center justify-center text-neutral-500">
            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
            Loading clinical workspace...
          </div>
        ) : messages.length === 0 ? (
          <div className="flex h-full items-center justify-center px-6 text-center text-sm text-neutral-500">
            Ask a medical question or upload a clinical report or drug image to begin.
          </div>
        ) : (
          <div className="mx-auto flex max-w-3xl flex-col gap-8 px-4 py-8 sm:px-6">
            {messages.map((message, index) => {
              if (message.role === "user") {
                return (
                  <div key={`${index}-user`} className="flex justify-end">
                    <div className="max-w-[85%] rounded-2xl bg-[#2f2f2f] px-4 py-3 text-sm leading-relaxed text-neutral-100 sm:max-w-lg">
                      {message.content}
                    </div>
                  </div>
                );
              }

              const sources = sourcesToLinks(message.sources);
              const isLatestAssistant = index === lastAssistantIndex;

              return (
                <div key={`${index}-assistant`}>
                  <AssistantMessage markdown={message.content} 
                  sources={sources} ragas_eval={message.ragas_eval} 
                  thoughtDurationSeconds={message.thoughtDurationSeconds} />

                  {isLatestAssistant && message.suggestions && message.suggestions.length > 0 && (
                    <div className="mt-4 flex flex-wrap gap-2">
                      {message.suggestions.map((question) => (
                        <button
                          key={question}
                          type="button"
                          onClick={() => onFollowUp(question)}
                          disabled={isSending}
                          className="rounded-full border border-neutral-700 bg-[#2f2f2f] px-3 py-1.5 text-xs text-neutral-300 transition-colors hover:border-neutral-500 hover:bg-neutral-800 hover:text-neutral-100 disabled:opacity-50"
                        >
                          {question}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}

            {isSending && (
              <div className="flex items-center gap-2 text-sm text-neutral-500">
                <Loader2 className="h-4 w-4 animate-spin" />
                Consulting clinical knowledge base...
              </div>
            )}
          </div>
        )}
      </div>

      <div className="shrink-0 border-t border-neutral-800/60 bg-[#212121]">
        <ChatInput
          value={inputValue}
          onChange={onInputChange}
          onSend={onSend}
          onUploadClick={onUploadClick}
          models={models}
          selectedModelId={selectedModelId}
          onSelectModel={onSelectModel}
          searchMethods={searchMethods}
          selectedSearchMethod={selectedSearchMethod}
          onSelectSearchMethod={onSelectSearchMethod}
          disabled={isSending || isLoading}
        />
      </div>
    </main>
  );
}
