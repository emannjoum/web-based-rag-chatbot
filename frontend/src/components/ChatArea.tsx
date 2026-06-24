import { Loader2, MessageCircleHeart, RefreshCw } from "lucide-react";
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

const SUGGESTED_PROMPTS = [
  "What are common symptoms of seasonal allergies?",
  "How does paracetamol work for fever?",
  "When should I see a doctor for a persistent cough?",
];

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
    <main className="relative flex min-w-0 flex-1 flex-col">
      {error && (
        <div className="mx-4 mt-3 flex items-center justify-between rounded-xl border border-red-900/40 bg-red-950/20 px-4 py-2.5 text-sm text-red-300/90 sm:mx-6">
          <span>{error}</span>
          <button
            type="button"
            onClick={onRetry}
            className="flex items-center gap-1 text-xs font-medium text-red-200/90 underline-offset-2 hover:underline"
          >
            <RefreshCw className="h-3 w-3" />
            Retry
          </button>
        </div>
      )}

      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-text-muted">
            <Loader2 className="h-6 w-6 animate-spin text-accent/70" />
            <p className="text-sm">Preparing your clinical workspace…</p>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center px-6">
            <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-accent/10 ring-1 ring-accent/20">
              <MessageCircleHeart className="h-8 w-8 text-accent/80" />
            </div>
            <h2
              className="mb-2 text-xl font-semibold text-text-primary"
              style={{ fontFamily: "var(--font-serif)" }}
            >
              How can I help you today?
            </h2>
            <p className="mb-8 max-w-md text-center text-sm leading-relaxed text-text-muted">
              Ask a medical question or upload a clinical report or drug image. Answers are
              grounded in Altibbi&apos;s verified health content.
            </p>
            <div className="flex max-w-lg flex-wrap justify-center gap-2">
              {SUGGESTED_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => onFollowUp(prompt)}
                  disabled={isSending}
                  className="rounded-full border border-border-subtle bg-surface-raised/60 px-4 py-2 text-left text-xs text-text-secondary transition-colors hover:border-accent/30 hover:bg-accent/8 hover:text-text-primary disabled:opacity-50"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="mx-auto flex max-w-3xl flex-col gap-10 px-4 py-8 sm:px-6">
            {messages.map((message, index) => {
              if (message.role === "user") {
                return (
                  <div key={`${index}-user`} className="flex justify-end">
                    <div className="max-w-[85%] rounded-2xl rounded-br-md bg-user-bubble px-4 py-3 text-sm leading-relaxed text-text-primary shadow-sm ring-1 ring-border-subtle/40 sm:max-w-lg">
                      {message.content}
                    </div>
                  </div>
                );
              }

              const sources = sourcesToLinks(message.sources);
              const isLatestAssistant = index === lastAssistantIndex;

              return (
                <div key={`${index}-assistant`}>
                  <AssistantMessage
                    markdown={message.content}
                    sources={sources}
                    ragas_eval={message.ragas_eval}
                    thoughtDurationSeconds={message.thoughtDurationSeconds}
                  />

                  {isLatestAssistant && message.suggestions && message.suggestions.length > 0 && (
                    <div className="ml-11 mt-5">
                      <p className="mb-2.5 text-[11px] font-medium uppercase tracking-wider text-text-muted">
                        Continue exploring
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {message.suggestions.map((question) => (
                          <button
                            key={question}
                            type="button"
                            onClick={() => onFollowUp(question)}
                            disabled={isSending}
                            className="rounded-full border border-border-subtle bg-surface-raised/50 px-3.5 py-1.5 text-xs text-text-secondary transition-colors hover:border-accent/30 hover:bg-accent/8 hover:text-text-primary disabled:opacity-50"
                          >
                            {question}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}

            {isSending && (
              <div className="ml-11 flex items-center gap-2.5 text-sm text-text-muted">
                <Loader2 className="h-4 w-4 animate-spin text-accent/70" />
                <span className="animate-gentle-pulse">Consulting Altibbi knowledge base…</span>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="shrink-0 border-t border-border-subtle/60 bg-surface-base/80 backdrop-blur-sm">
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
