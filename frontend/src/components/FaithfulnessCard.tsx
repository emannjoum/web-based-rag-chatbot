import { useState } from "react";
import { BookOpen, ChevronDown, ChevronUp, Loader2 } from "lucide-react";

interface RagasEval {
  faithfulness: number;
  answer_relevancy: number;
}

interface FaithfulnessCardProps {
  ragas_eval?: RagasEval;
  hasSources: boolean;
}

interface AlignmentTier {
  label: string;
  description: string;
  color: string;
  trackColor: string;
}

function getAlignmentTier(score: number): AlignmentTier {
  const pct = score * 100;
  if (pct >= 80) {
    return {
      label: "Strong alignment",
      description: "This answer closely reflects the cited Altibbi sources.",
      color: "#6b9e82",
      trackColor: "#6b9e8225",
    };
  }
  if (pct >= 60) {
    return {
      label: "Good alignment",
      description: "Most claims are supported by the referenced sources.",
      color: "#7a9e8e",
      trackColor: "#7a9e8e25",
    };
  }
  if (pct >= 40) {
    return {
      label: "Moderate alignment",
      description: "Some statements may extend beyond what sources directly state.",
      color: "#a8a07a",
      trackColor: "#a8a07a25",
    };
  }
  return {
    label: "Limited alignment",
    description: "We recommend reviewing the sources below for full context.",
    color: "#a88a7a",
    trackColor: "#a88a7a25",
  };
}

function ScoreRing({ score, color }: { score: number; color: string }) {
  const size = 52;
  const stroke = 4;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - score * circumference;
  const pct = Math.round(score * 100);

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--color-border-subtle)"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="faithfulness-ring transition-all duration-700"
          style={{ "--ring-circumference": `${circumference}px` } as React.CSSProperties}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-xs font-semibold text-text-primary">{pct}</span>
      </div>
    </div>
  );
}

function MetricBar({ label, value, color }: { label: string; value: number; color: string }) {
  const pct = Math.max(0, Math.min(100, value * 100));
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-[11px]">
        <span className="text-text-muted">{label}</span>
        <span className="font-medium text-text-secondary">{pct.toFixed(0)}%</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-border-subtle/60">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

export default function FaithfulnessCard({ ragas_eval, hasSources }: FaithfulnessCardProps) {
  const [expanded, setExpanded] = useState(false);

  if (!hasSources) return null;

  if (!ragas_eval) {
    return (
      <div className="mt-4 flex items-center gap-3 rounded-xl border border-border-subtle/60 bg-surface-muted/50 px-4 py-3">
        <Loader2 className="h-4 w-4 shrink-0 animate-spin text-accent/70" />
        <div>
          <p className="text-xs font-medium text-text-secondary">Verifying source alignment</p>
          <p className="text-[11px] text-text-muted animate-gentle-pulse">
            Comparing this answer against cited Altibbi content…
          </p>
        </div>
      </div>
    );
  }

  const tier = getAlignmentTier(ragas_eval.faithfulness);

  return (
    <div className="mt-4 overflow-hidden rounded-xl border border-border-subtle/60 bg-surface-muted/40">
      <button
        type="button"
        onClick={() => setExpanded((open) => !open)}
        className="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-surface-overlay/30"
        aria-expanded={expanded}
      >
        <ScoreRing score={ragas_eval.faithfulness} color={tier.color} />

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <BookOpen className="h-3.5 w-3.5 shrink-0 text-accent/80" />
            <span className="text-xs font-semibold text-text-primary">Source alignment</span>
          </div>
          <p className="mt-0.5 text-[11px] leading-snug text-text-muted">{tier.label}</p>
        </div>

        {expanded ? (
          <ChevronUp className="h-4 w-4 shrink-0 text-text-muted" />
        ) : (
          <ChevronDown className="h-4 w-4 shrink-0 text-text-muted" />
        )}
      </button>

      {expanded && (
        <div
          className="border-t border-border-subtle/50 px-4 py-3"
          style={{ backgroundColor: tier.trackColor }}
        >
          <p className="mb-3 text-xs leading-relaxed text-text-secondary">{tier.description}</p>

          <div className="space-y-2.5">
            <MetricBar
              label="Grounded in sources"
              value={ragas_eval.faithfulness}
              color={tier.color}
            />
            <MetricBar
              label="Relevance to your question"
              value={ragas_eval.answer_relevancy}
              color="#7a9aaa"
            />
          </div>

          <p className="mt-3 text-[10px] leading-relaxed text-text-muted/80">
            Scores reflect how well this response is supported by and relevant to the retrieved
            Altibbi sources — not a judgment on medical accuracy.
          </p>
        </div>
      )}
    </div>
  );
}
