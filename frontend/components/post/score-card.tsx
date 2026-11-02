import type { QualityScore } from "@/types/api";
import { cn } from "@/lib/utils";

const DIMENSIONS: { key: keyof Omit<QualityScore, "label" | "overall">; label: string }[] = [
  { key: "relevance", label: "Relevance" },
  { key: "readability", label: "Readability" },
  { key: "hook_strength", label: "Hook strength" },
  { key: "structure", label: "Structure" },
  { key: "keyword_alignment", label: "Keyword alignment" },
  { key: "tone_alignment", label: "Tone alignment" },
  { key: "cta_quality", label: "CTA quality" },
  { key: "originality_signals", label: "Originality signals" },
];

function barColor(value: number): string {
  if (value >= 75) return "bg-brand-500";
  if (value >= 50) return "bg-amber-500";
  return "bg-red-400";
}

/** Writing quality score (hook, keywords, readability, structure). Not a reach prediction. */
export function ScoreCard({ score, title = "Quality score" }: { score: QualityScore; title?: string }) {
  return (
    <section aria-labelledby="score-title" className="flex flex-col gap-4">
      <div>
        <h3 id="score-title" className="text-sm font-semibold text-ink-900">
          {title}
        </h3>
        <p className="text-xs text-ink-500">Heuristic guidance on clarity and structure. It does not predict reach.</p>
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-3xl font-semibold text-ink-900" aria-label={`Overall ${score.overall} out of 100`}>
          {score.overall}
        </span>
        <span className="text-sm text-ink-500">/ 100 overall</span>
      </div>
      <ul className="flex flex-col gap-2.5">
        {DIMENSIONS.map(({ key, label }) => {
          const value = score[key];
          return (
            <li key={key} className="flex flex-col gap-1">
              <div className="flex justify-between text-xs text-ink-600">
                <span>{label}</span>
                <span className="tabular-nums">{value}</span>
              </div>
              <div
                className="h-1.5 w-full overflow-hidden rounded-full bg-ink-100"
                role="meter"
                aria-label={label}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={value}
              >
                <div className={cn("h-full rounded-full transition-all", barColor(value))} style={{ width: `${value}%` }} />
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
