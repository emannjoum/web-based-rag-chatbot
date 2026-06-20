import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { ChevronDown, ChevronRight, Sparkles } from "lucide-react";
import type { SourceLink } from "../types/api";

interface AssistantMessageProps {
  markdown: string;
  sources: SourceLink[];
  thoughtDurationSeconds?: number;
}

function formatCitations(text: string): string {
  return text.replace(/\[(\d+)\]/g, "[$1](#cite-$1)");
}

export default function AssistantMessage({
  markdown,
  sources,
  thoughtDurationSeconds = 4,
}: AssistantMessageProps) {
  const [thoughtOpen, setThoughtOpen] = useState(false);

  return (
    <div className="max-w-3xl">
      <button
        type="button"
        onClick={() => setThoughtOpen((open) => !open)}
        className="mb-3 flex items-center gap-1.5 text-xs text-neutral-500 transition-colors hover:text-neutral-300"
      >
        <Sparkles className="h-3.5 w-3.5" />
        <span>Thought for {thoughtDurationSeconds} seconds</span>
        {thoughtOpen ? (
          <ChevronDown className="h-3.5 w-3.5" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5" />
        )}
      </button>

      {thoughtOpen && (
        <div className="mb-4 rounded-lg border border-neutral-800 bg-neutral-900/50 px-3 py-2 text-xs leading-relaxed text-neutral-500">
          Analyzed clinical knowledge base, cross-referenced documentation sources,
          and structured a response with verified citations.
        </div>
      )}

      <div className="prose-chat">
        <ReactMarkdown
          components={{
            a: ({ href, children }) => {
              const match = href?.match(/^#cite-(\d+)$/);
              if (match) {
                return (
                  <sup className="citation-sup">
                    <a href={`#source-${match[1]}`} className="hover:text-sky-300">
                      [{match[1]}]
                    </a>
                  </sup>
                );
              }
              return (
                <a
                  href={href}
                  className="text-sky-400 underline-offset-2 hover:underline"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {children}
                </a>
              );
            },
          }}
        >
          {formatCitations(markdown)}
        </ReactMarkdown>
      </div>

      {sources.length > 0 && (
        <div className="mt-5 rounded-lg border border-neutral-800 bg-neutral-900/40 px-4 py-3">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-neutral-400">
            Sources Used:
          </p>
          <ol className="list-decimal space-y-1.5 pl-5 text-sm">
            {sources.map((source) => (
              <li key={source.id} id={`source-${source.id}`}>
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sky-400 underline-offset-2 transition-colors hover:text-sky-300 hover:underline"
                >
                  {source.label}
                </a>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
