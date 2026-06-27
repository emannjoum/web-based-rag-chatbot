import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { ChevronDown, ChevronRight, Stethoscope } from "lucide-react";
import type { SourceLink } from "../types/api";
import FaithfulnessCard from "./FaithfulnessCard";

interface AssistantMessageProps {
  markdown: string;
  sources: SourceLink[];
  thoughtDurationSeconds?: number;
  ragas_eval?: { faithfulness: number; answer_relevancy: number } | null;
  eval_status?: "pending" | "success" | "failed" | null;
}

function formatCitations(text: string): string {
  return text.replace(/\[(\d+)\]/g, "[$1](#cite-$1)");
}

function getPageName(url: string): string {
  try {
    const { hostname, pathname } = new URL(url);
    const domain = hostname.replace("www.", "").split(".")[0];
    const pathParts = pathname.split("/").filter(Boolean);
    let lastPart = pathParts[pathParts.length - 1];

    if (!lastPart) return domain.charAt(0).toUpperCase() + domain.slice(1);

    try {
      lastPart = decodeURIComponent(lastPart);
    } catch {
      // Ignore if decoding fails
    }

    return lastPart
      .replace(/[-_]/g, " ")
      .split(" ")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  } catch {
    try {
      return decodeURIComponent(url);
    } catch {
      return url;
    }
  }
}

export default function AssistantMessage({
  markdown,
  sources,
  thoughtDurationSeconds = 4,
  ragas_eval,
  eval_status,
}: AssistantMessageProps) {
  const [thoughtOpen, setThoughtOpen] = useState(false);

  return (
    <div className="max-w-3xl">
      <div className="mb-4 flex items-start gap-3">
        <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent/15 ring-1 ring-accent/20">
          <Stethoscope className="h-4 w-4 text-accent" />
        </div>

        <div className="min-w-0 flex-1">
          <button
            type="button"
            onClick={() => setThoughtOpen((open) => !open)}
            className="mb-3 flex items-center gap-1.5 rounded-md px-1 py-0.5 text-xs text-text-muted transition-colors hover:text-text-secondary"
          >
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-accent/60" />
            <span>Reasoned for {thoughtDurationSeconds}s</span>
            {thoughtOpen ? (
              <ChevronDown className="h-3.5 w-3.5" />
            ) : (
              <ChevronRight className="h-3.5 w-3.5" />
            )}
          </button>

          {thoughtOpen && (
            <div className="mb-4 rounded-lg border border-border-subtle/60 bg-surface-muted/60 px-3.5 py-2.5 text-xs leading-relaxed text-text-muted">
              Searched the knowledge base, reviewed matched documentation, and composed a
              response with inline source citations from Altibbi.
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
                        <a href={`#source-${match[1]}`} className="hover:text-accent-soft">
                          [{match[1]}]
                        </a>
                      </sup>
                    );
                  }
                  return (
                    <a
                      href={href}
                      className="text-accent underline-offset-2 hover:text-accent-soft hover:underline"
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
        </div>
      </div>

      {sources.length > 0 && (
        <div className="surface-card ml-11 px-4 py-3.5">
          <p className="mb-2.5 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-text-muted">
            <span className="inline-block h-px w-3 bg-accent/40" />
            Referenced sources
          </p>
          <ol className="list-decimal space-y-2 pl-5 text-sm">
            {sources.map((source) => (
              <li key={source.id} id={`source-${source.id}`} className="text-text-secondary">
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-accent/90 underline-offset-2 transition-colors hover:text-accent hover:underline"
                >
                  {getPageName(source.url)}
                </a>
              </li>
            ))}
          </ol>
        </div>
      )}

      <div className="ml-11">
        <FaithfulnessCard
          ragas_eval={ragas_eval}
          eval_status={eval_status}
          hasSources={sources.length > 0}
        />
      </div>
    </div>
  );
}
