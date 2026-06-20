import { ArrowUp, Plus } from "lucide-react";
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
    <div className="mx-auto w-full max-w-3xl px-4 pb-6 pt-2">
      <div className="rounded-2xl bg-[#2f2f2f] p-3 shadow-lg shadow-black/20">
        <input
          type="text"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything..."
          disabled={disabled}
          className="w-full bg-transparent px-2 py-2 text-sm text-neutral-100 placeholder:text-neutral-500 focus:outline-none disabled:opacity-50"
        />

        <div className="mt-2 flex items-center justify-between gap-3">
          <button
            type="button"
            onClick={onUploadClick}
            disabled={disabled}
            className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs text-neutral-400 transition-colors hover:bg-neutral-700/60 hover:text-neutral-200 disabled:opacity-50"
          >
            <Plus className="h-4 w-4 shrink-0" />
            <span className="text-left">Upload medical report or drug image</span>
          </button>

          <button
            type="button"
            onClick={onSend}
            disabled={disabled || !value.trim()}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-neutral-100 text-neutral-900 transition-colors hover:bg-white disabled:opacity-40"
            aria-label="Send message"
          >
            <ArrowUp className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-4 px-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-neutral-500">Pick Model:</span>
          {models.map((model) => {
            const isActive = model.id === selectedModelId;
            return (
              <button
                key={model.id}
                type="button"
                onClick={() => onSelectModel(model.id)}
                disabled={disabled}
                className={`rounded-full px-3 py-1 text-xs transition-colors disabled:opacity-50 ${
                  isActive
                    ? "border border-white text-neutral-100 ring-1 ring-white"
                    : "border border-neutral-700 text-neutral-400 hover:border-neutral-500 hover:text-neutral-200"
                }`}
              >
                {model.label}
              </button>
            );
          })}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-neutral-500">Search Method:</span>
          {searchMethods.map((method) => {
            const isActive = method === selectedSearchMethod;
            return (
              <button
                key={method}
                type="button"
                onClick={() => onSelectSearchMethod(method)}
                disabled={disabled}
                className={`rounded-full px-3 py-1 text-xs transition-colors disabled:opacity-50 ${
                  isActive
                    ? "border border-emerald-500/50 bg-emerald-500/10 text-emerald-400"
                    : "border border-neutral-700 text-neutral-400 hover:border-neutral-500 hover:text-neutral-200"
                }`}
              >
                {method}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
