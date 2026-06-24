import { useState } from "react";
import {
  ChevronUp,
  MessageSquarePlus,
  PanelLeftClose,
  PanelLeftOpen,
  Trash2,
  User,
} from "lucide-react";
import type { ChatHistoryItem } from "../types/api";
import { useGroupedHistory } from "../hooks/useGroupedHistory";

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  history: ChatHistoryItem[];
  activeChatId: string | null;
  onSelectChat: (id: string) => void;
  onNewChat: () => void;
  onDeleteAll: () => void;
  onDeleteChat: (id: string) => void;
}

export default function Sidebar({
  isOpen,
  onToggle,
  history,
  activeChatId,
  onSelectChat,
  onNewChat,
  onDeleteAll,
  onDeleteChat,
}: SidebarProps) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const groupedHistory = useGroupedHistory(history);

  if (!isOpen) {
    return (
      <aside className="flex w-14 shrink-0 flex-col items-center border-r border-border-subtle bg-surface-muted py-4">
        <button
          type="button"
          onClick={onToggle}
          className="rounded-lg p-2.5 text-text-muted transition-colors hover:bg-surface-overlay hover:text-text-primary"
          aria-label="Open sidebar"
        >
          <PanelLeftOpen className="h-5 w-5" />
        </button>
        <button
          type="button"
          onClick={onNewChat}
          className="mt-2 rounded-lg p-2.5 text-text-muted transition-colors hover:bg-surface-overlay hover:text-accent"
          aria-label="New chat"
        >
          <MessageSquarePlus className="h-5 w-5" />
        </button>
      </aside>
    );
  }

  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-border-subtle bg-surface-muted lg:w-72">
      <div className="border-b border-border-subtle/60 px-4 py-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent/15 ring-1 ring-accent/25">
            <span className="text-sm font-bold text-accent" style={{ fontFamily: "var(--font-serif)" }}>
              A
            </span>
          </div>
          <div className="min-w-0">
            <h1 className="truncate text-sm font-semibold text-text-primary">Altibbi</h1>
            <p className="text-[11px] text-text-muted">Medical assistant</p>
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-1 p-3">
        <button
          type="button"
          onClick={onNewChat}
          className="flex w-full items-center gap-2.5 rounded-lg bg-accent/10 px-3 py-2.5 text-sm font-medium text-accent transition-colors hover:bg-accent/18"
        >
          <MessageSquarePlus className="h-4 w-4" />
          <span>New consultation</span>
        </button>

        <button
          type="button"
          onClick={onToggle}
          className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-text-muted transition-colors hover:bg-surface-overlay hover:text-text-secondary"
        >
          <PanelLeftClose className="h-4 w-4" />
          <span>Collapse sidebar</span>
        </button>

        {history.length > 0 && (
          <button
            type="button"
            onClick={onDeleteAll}
            className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-text-muted transition-colors hover:bg-surface-overlay hover:text-red-400/80"
          >
            <Trash2 className="h-4 w-4" />
            <span>Clear all history</span>
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-3 pb-3">
        {groupedHistory.length === 0 ? (
          <div className="px-3 py-6 text-center">
            <p className="text-xs text-text-muted">No conversations yet.</p>
            <p className="mt-1 text-[11px] text-text-muted/70">Start a new consultation above.</p>
          </div>
        ) : (
          groupedHistory.map((group) => (
            <div key={group.label} className="mb-3">
              <p className="px-3 pb-1.5 text-[10px] font-semibold uppercase tracking-widest text-text-muted/80">
                {group.label}
              </p>
              <ul className="space-y-0.5">
                {group.items.map((item) => {
                  const isActive = activeChatId === item.id;
                  const isHovered = hoveredId === item.id;

                  return (
                    <li key={item.id}>
                      <button
                        type="button"
                        onClick={() => onSelectChat(item.id)}
                        onMouseEnter={() => setHoveredId(item.id)}
                        onMouseLeave={() => setHoveredId(null)}
                        className={`group flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                          isActive
                            ? "bg-surface-overlay text-text-primary ring-1 ring-border-subtle/80"
                            : "text-text-secondary hover:bg-surface-overlay/60"
                        }`}
                      >
                        <span className="truncate pr-2">{item.title}</span>
                        {isHovered && (
                          <span
                            role="button"
                            tabIndex={0}
                            onClick={(event) => {
                              event.stopPropagation();
                              onDeleteChat(item.id);
                            }}
                            onKeyDown={(event) => {
                              if (event.key === "Enter" || event.key === " ") {
                                event.preventDefault();
                                event.stopPropagation();
                                onDeleteChat(item.id);
                              }
                            }}
                            className="shrink-0 rounded p-1 text-text-muted transition-colors hover:bg-surface-base hover:text-red-400/80"
                            aria-label={`Delete ${item.title}`}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </span>
                        )}
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))
        )}
      </div>

      <div className="sticky bottom-0 border-t border-border-subtle bg-surface-muted p-3">
        <button
          type="button"
          className="flex w-full items-center justify-between rounded-lg px-2 py-2 text-sm text-text-secondary transition-colors hover:bg-surface-overlay"
        >
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-surface-overlay ring-1 ring-border-subtle">
              <User className="h-4 w-4 text-text-muted" />
            </div>
            <span>Guest</span>
          </div>
          <ChevronUp className="h-4 w-4 text-text-muted" />
        </button>
      </div>
    </aside>
  );
}
