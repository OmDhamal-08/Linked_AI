import { Badge } from "@/components/ui/feedback";
import type { Analysis, Suggestion } from "@/types/api";
import { titleCase } from "@/lib/utils";

interface Props {
  analysis?: Analysis | null;
  suggestions: Suggestion[];
  hookStrength?: number;
  missingKeywords?: string[];
}

/** Plain-language breakdown of the post: what was detected and what to improve. */
export function AnalysisPanel({ analysis, suggestions, hookStrength, missingKeywords = [] }: Props) {
  const hook = hookStrength ?? analysis?.hook_strength;
  return (
    <div className="flex flex-col gap-5">
      {analysis ? (
        <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
          <div>
            <dt className="text-xs text-ink-500">Topic</dt>
            <dd className="font-medium text-ink-900">{analysis.topic || "General"}</dd>
          </div>
          <div>
            <dt className="text-xs text-ink-500">Tone</dt>
            <dd className="font-medium text-ink-900">{analysis.tone ? titleCase(analysis.tone) : "-"}</dd>
          </div>
          <div>
            <dt className="text-xs text-ink-500">Opening hook</dt>
            <dd className="font-medium text-ink-900">{hook !== undefined ? `${Math.round(hook * 100)} / 100` : "-"}</dd>
          </div>
          <div>
            <dt className="text-xs text-ink-500">Readability</dt>
            <dd className="font-medium text-ink-900">{analysis.readability !== undefined ? `${Math.round(analysis.readability)} / 100` : "-"}</dd>
          </div>
        </dl>
      ) : null}

      {analysis?.structure?.length ? (
        <div>
          <p className="mb-2 text-xs text-ink-500">Detected structure</p>
          <div className="flex flex-wrap gap-1.5">
            {analysis.structure.map((role, i) => (
              <Badge key={`${role}-${i}`} tone="brand">
                {titleCase(role)}
              </Badge>
            ))}
          </div>
        </div>
      ) : null}

      {missingKeywords.length ? (
        <div>
          <p className="mb-2 text-xs text-ink-500">Keywords to consider</p>
          <div className="flex flex-wrap gap-1.5">
            {missingKeywords.map((k) => (
              <Badge key={k}>{k}</Badge>
            ))}
          </div>
        </div>
      ) : null}

      {suggestions.length ? (
        <div>
          <p className="mb-2 text-sm font-semibold text-ink-900">Suggestions</p>
          <ul className="flex flex-col gap-2">
            {suggestions.map((s) => (
              <li key={s.code} className="rounded-md bg-ink-50 px-3 py-2 text-sm text-ink-700">
                {s.message}
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="text-sm text-ink-500">No major issues found. Nice work.</p>
      )}
    </div>
  );
}
