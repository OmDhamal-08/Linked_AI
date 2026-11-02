"use client";

import { useState } from "react";
import { EnhanceForm } from "@/components/forms/enhance-form";
import { AnalysisPanel } from "@/components/post/analysis-panel";
import { PostResult } from "@/components/post/post-result";
import { ScoreCard } from "@/components/post/score-card";
import { UpgradeBanner } from "@/components/post/upgrade-banner";
import { LoadingSteps } from "@/components/post/loading-steps";
import { Alert } from "@/components/ui/feedback";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/feedback";
import { useTaxonomy } from "@/hooks/use-taxonomy";
import { apiFetch, errorMessage } from "@/lib/api";
import type { EnhancePayload } from "@/lib/schemas";
import { titleCase } from "@/lib/utils";
import type { EnhanceResponse } from "@/types/api";

export default function EnhancePage() {
  const { taxonomy, error: taxonomyError } = useTaxonomy();
  const [result, setResult] = useState<EnhanceResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run(payload: EnhancePayload) {
    setSubmitting(true);
    setError(null);
    try {
      const data = await apiFetch<EnhanceResponse>("/posts/enhance", {
        method: "POST",
        // An empty tone means "keep my tone": omit it rather than sending an invalid value.
        json: { ...payload, tone: payload.tone || undefined },
        timeoutMs: 90_000,
      });
      setResult(data);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <header>
        <h1 className="text-2xl font-semibold text-ink-900">Enhance an existing post</h1>
        <p className="mt-1 text-sm text-ink-600">Paste your draft. We analyse it and suggest concrete improvements.</p>
      </header>

      {taxonomyError ? <Alert tone="danger">{taxonomyError}</Alert> : null}
      {error ? <Alert tone="danger">{error}</Alert> : null}

      <div className="grid gap-8 xl:grid-cols-[1fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Your draft</CardTitle>
          </CardHeader>
          <CardContent>
            {taxonomy ? (
              <EnhanceForm taxonomy={taxonomy} submitting={submitting} onSubmit={run} />
            ) : (
              <p className="text-sm text-ink-500">Loading options…</p>
            )}
          </CardContent>
        </Card>

        <div className="flex min-w-0 flex-col gap-6">
          <LoadingSteps active={submitting} />
          {!submitting && result ? (
            <>
              <Card>
                <CardHeader className="flex-row items-center justify-between">
                  <CardTitle>Analysis</CardTitle>
                  {result.analysis.post_type ? <Badge tone="brand">{titleCase(result.analysis.post_type)}</Badge> : null}
                </CardHeader>
                <CardContent className="flex flex-col gap-6">
                  <ScoreCard score={result.score_before} title="Current draft score" />
                  <AnalysisPanel
                    analysis={result.analysis}
                    suggestions={result.suggestions}
                    missingKeywords={result.missing_keywords}
                  />
                  {result.hook_suggestions.length ? (
                    <div>
                      <p className="mb-2 text-sm font-semibold text-ink-900">Hook ideas</p>
                      <ul className="flex flex-col gap-2">
                        {result.hook_suggestions.map((h) => (
                          <li key={h} className="rounded-md border border-ink-100 px-3 py-2 text-sm text-ink-800">
                            {h}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                  {result.recommended_structure.length ? (
                    <p className="text-sm text-ink-700">
                      Suggested flow:{" "}
                      <span className="font-medium">{result.recommended_structure.map(titleCase).join(" → ")}</span>
                    </p>
                  ) : null}
                </CardContent>
              </Card>

              {result.locked ? (
                <UpgradeBanner message={result.upgrade_hint} />
              ) : result.enhanced_post ? (
                <PostResult
                  postId={result.post_id}
                  text={result.enhanced_post}
                  hashtags={result.analysis.hashtags ?? []}
                  score={result.score_after}
                  analysis={result.analysis}
                  suggestions={result.suggestions}
                  title="Enhanced post"
                />
              ) : null}
            </>
          ) : null}

          {!submitting && !result ? (
            <Card className="border-dashed">
              <CardContent className="py-10 text-center text-sm text-ink-500">
                Your analysis will appear here.
                <div className="mt-6 text-left">
                  <ScoreCard
                    score={{
                      label: "Quality score",
                      relevance: 0,
                      readability: 0,
                      hook_strength: 0,
                      structure: 0,
                      keyword_alignment: 0,
                      tone_alignment: 0,
                      cta_quality: 0,
                      originality_signals: 0,
                      overall: 0,
                    }}
                    title="Score preview"
                  />
                </div>
              </CardContent>
            </Card>
          ) : null}
        </div>
      </div>
    </div>
  );
}
