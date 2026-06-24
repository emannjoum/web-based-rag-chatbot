import { ArrowUp, ImagePlus } from "lucide-react";
import type { ApiModelOption } from "../types/api";

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  onUploadClick: () => void;
  models: ApiModelOption[];
  selectedModelId: string;
  onSelectModel: (modelId: string) => void;
  searchMethods: string[];
  selectedSearchMethod: string;
  onSelectSearchMethod: (method: string) => void;
  disabled?: boolean;
}

export default function ChatInput({
  value,
  onChange,
  onSend,
  onUploadClick,
  models,
  selectedModelId,
  onSelectModel,
  searchMethods,
  selectedSearchMethod,
  onSelectSearchMethod,
  disabled = false,
}: ChatInputProps) {
  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      onSend();
    }
  };

  return (
    <div className="mx-auto w-full max-w-3xl px-4 pb-5 pt-3">
      <div className="surface-card p-3 shadow-lg shadow-black/10 ring-1 ring-border-subtle/50">
        <input
          type="text"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe your symptoms or ask a health question…"
          disabled={disabled}
          className="w-full bg-transparent px-2 py-2.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none disabled:opacity-50"
        />

        <div className="mt-1 flex items-center justify-between gap-3 border-t border-border-subtle/40 pt-2">
          <button
            type="button"
            onClick={onUploadClick}
            disabled={disabled}
            className="flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs text-text-muted transition-colors hover:bg-surface-overlay hover:text-text-secondary disabled:opacity-50"
          >
            <ImagePlus className="h-4 w-4 shrink-0" />
            <span>Upload report or drug image</span>
          </button>

          <button
            type="button"
            onClick={onSend}
            disabled={disabled || !value.trim()}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-accent text-white transition-all hover:bg-accent-soft disabled:opacity-35 disabled:hover:bg-accent"
            aria-label="Send message"
          >
            <ArrowUp className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 px-1">
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-[11px] font-medium text-text-muted">Model</span>
          {models.map((model) => {
            const isActive = model.id === selectedModelId;
            return (
              <button
                key={model.id}
                type="button"
                onClick={() => onSelectModel(model.id)}
                disabled={disabled}
                className={`rounded-full border px-3 py-1 text-xs transition-colors disabled:opacity-50 ${
                  isActive ? "chip-active" : "chip-inactive"
                }`}
              >
                {model.label}
              </button>
            );
          })}
        </div>

        {searchMethods.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[11px] font-medium text-text-muted">Search</span>
            {searchMethods.map((method) => {
              const isActive = method === selectedSearchMethod;
              return (
                <button
                  key={method}
                  type="button"
                  onClick={() => onSelectSearchMethod(method)}
                  disabled={disabled}
                  className={`rounded-full border px-3 py-1 text-xs transition-colors disabled:opacity-50 ${
                    isActive ? "chip-active" : "chip-inactive"
                  }`}
                >
                  {method}
                </button>
              );
            })}
          </div>
        )}
      </div>

      <p className="mt-2 px-1 text-center text-[10px] text-text-muted/60">
        For informational purposes only — not a substitute for professional medical advice.
      </p>
    </div>
  );
}
