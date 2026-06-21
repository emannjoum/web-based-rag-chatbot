import { useState } from "react";
import {
  ChevronUp,
  PanelLeft,
  SquarePen,
  Trash,
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
      <aside className="flex w-14 shrink-0 flex-col items-center border-r border-neutral-800 bg-[#171717] py-3">
        <button
          type="button"
          onClick={onToggle}
          className="rounded-lg p-2 text-neutral-400 transition-colors hover:bg-neutral-800 hover:text-neutral-100"
          aria-label="Open sidebar"
        >
          <PanelLeft className="h-5 w-5" />
        </button>
      </aside>
    );
  }

  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-neutral-800 bg-[#171717] lg:w-72">
      <div className="flex flex-col gap-1 p-3">
        <button
          type="button"
          onClick={onToggle}
          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-neutral-300 transition-colors hover:bg-neutral-800"
        >
          <PanelLeft className="h-4 w-4" />
          <span>Open sidebar</span>
        </button>

        <button
          type="button"
          onClick={onNewChat}
          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-neutral-200 transition-colors hover:bg-neutral-800"
        >
          <SquarePen className="h-4 w-4" />
          <span>New chat</span>
        </button>

        <button
          type="button"
          onClick={onDeleteAll}
          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-neutral-400 transition-colors hover:bg-neutral-800 hover:text-red-400"
        >
          <Trash className="h-4 w-4" />
          <span>Delete all</span>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-3 pb-3">
        <p className="px-3 py-2 text-[11px] font-semibold tracking-widest text-neutral-500">
          HISTORY
        </p>

        {groupedHistory.length === 0 ? (
          <p className="px-3 text-xs text-neutral-600">No conversations yet.</p>
        ) : (
          groupedHistory.map((group) => (
            <div key={group.label} className="mb-2">
              <p className="px-3 pb-1 text-[11px] font-semibold tracking-widest text-neutral-500">
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
                            ? "bg-neutral-800 text-neutral-100"
                            : "text-neutral-300 hover:bg-neutral-800/70"
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
                            className="shrink-0 rounded p-1 text-neutral-500 transition-colors hover:bg-neutral-700 hover:text-red-400"
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

      <div className="sticky bottom-0 border-t border-neutral-800 bg-[#171717] p-3">
        <button
          type="button"
          className="flex w-full items-center justify-between rounded-lg px-2 py-2 text-sm text-neutral-300 transition-colors hover:bg-neutral-800"
        >
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-neutral-700">
              <User className="h-4 w-4 text-neutral-300" />
            </div>
            <span>Guest</span>
          </div>
          <ChevronUp className="h-4 w-4 text-neutral-500" />
        </button>
      </div>
    </aside>
  );
}
