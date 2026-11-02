import { Badge } from "@/components/ui/feedback";
import { titleCase } from "@/lib/utils";
import type { Blueprint, Suggestion } from "@/types/api";

/** What free users receive instead of the full post: a plan you can write from, with suggestions. */
export function BlueprintView({ blueprint, suggestions }: { blueprint: Blueprint; suggestions: Suggestion[] }) {
  return (
    <div className="flex flex-col gap-6">
      <section aria-labelledby="hooks-title">
        <h3 id="hooks-title" className="mb-2 text-sm font-semibold text-ink-900">
          Opening hook ideas
        </h3>
        <ul className="flex flex-col gap-2">
          {blueprint.hook_suggestions.map((hook) => (
            <li key={hook} className="rounded-md border border-ink-100 bg-white px-4 py-3 text-sm text-ink-800">
              {hook}
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="structure-title">
        <h3 id="structure-title" className="mb-2 text-sm font-semibold text-ink-900">
          Recommended structure
        </h3>
        <div className="flex flex-wrap items-center gap-1.5">
          {blueprint.structure.map((role, i) => (
            <span key={`${role}-${i}`} className="flex items-center gap-1.5">
              <Badge tone="brand">{titleCase(role)}</Badge>
              {i < blueprint.structure.length - 1 ? <span aria-hidden="true" className="text-ink-300">→</span> : null}
            </span>
          ))}
        </div>
      </section>

      {blueprint.keywords.length ? (
        <section aria-labelledby="keywords-title">
          <h3 id="keywords-title" className="mb-2 text-sm font-semibold text-ink-900">
            Keywords to work in naturally
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {blueprint.keywords.map((k) => (
              <Badge key={k}>{k}</Badge>
            ))}
          </div>
        </section>
      ) : null}

      {blueprint.hashtags.length ? (
        <section aria-labelledby="tags-title">
          <h3 id="tags-title" className="mb-2 text-sm font-semibold text-ink-900">
            Hashtag concepts
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {blueprint.hashtags.map((t) => (
              <Badge key={t}>#{t}</Badge>
            ))}
          </div>
        </section>
      ) : null}

      {suggestions.length ? (
        <section aria-labelledby="sugg-title">
          <h3 id="sugg-title" className="mb-2 text-sm font-semibold text-ink-900">
            Suggestions
          </h3>
          <ul className="flex flex-col gap-2">
            {suggestions.map((s) => (
              <li key={s.code} className="rounded-md bg-ink-50 px-3 py-2 text-sm text-ink-700">
                {s.message}
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
