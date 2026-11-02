"use client";

import { useEffect, useState } from "react";
import { UsageMeter } from "@/components/dashboard/usage-meter";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, EmptyState, Spinner } from "@/components/ui/feedback";
import { apiFetch, errorMessage } from "@/lib/api";
import { formatDate, titleCase } from "@/lib/utils";
import type { PostItem, PostList, QualityScore, UsageSummary } from "@/types/api";

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

function average(values: number[]): number | null {
  return values.length ? Math.round(values.reduce((a, b) => a + b, 0) / values.length) : null;
}

export default function AnalyticsPage() {
  const [posts, setPosts] = useState<PostItem[] | null>(null);
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all([apiFetch<PostList>("/posts?limit=100"), apiFetch<UsageSummary>("/usage")])
      .then(([list, u]) => {
        if (!active) return;
        setPosts(list.items);
        setUsage(u);
      })
      .catch((err) => active && setError(errorMessage(err)));
    return () => {
      active = false;
    };
  }, []);

  const scored = (posts ?? []).filter((p): p is PostItem & { score: QualityScore } => Boolean(p.score));
  const overallAverage = average(scored.map((p) => p.score.overall));

  return (
    <div className="flex flex-col gap-8">
      <header>
        <h1 className="text-2xl font-semibold text-ink-900">Analytics</h1>
        <p className="mt-1 text-sm text-ink-600">
          Quality trends across your recent generated posts. Scores describe clarity and structure, not reach.
        </p>
      </header>

      {error ? <Alert tone="danger">{error}</Alert> : null}
      {!posts && !error ? (
        <div className="flex justify-center py-16">
          <Spinner />
        </div>
      ) : null}

      {posts && scored.length === 0 ? (
        <EmptyState title="No scored posts yet" description="Generate a full post to see quality analytics here." />
      ) : null}

      {scored.length > 0 ? (
        <div className="grid gap-6 xl:grid-cols-[1.2fr_1fr]">
          <Card>
            <CardHeader>
              <CardTitle>Average quality by dimension</CardTitle>
              <p className="text-sm text-ink-500">
                Overall average: <span className="font-semibold text-ink-900">{overallAverage}</span> / 100 across {scored.length} posts
              </p>
            </CardHeader>
            <CardContent>
              <ul className="flex flex-col gap-3">
                {DIMENSIONS.map(({ key, label }) => {
                  const value = average(scored.map((p) => p.score[key])) ?? 0;
                  return (
                    <li key={key} className="flex flex-col gap-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-ink-700">{label}</span>
                        <span className="tabular-nums text-ink-900">{value}</span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-ink-100" role="meter" aria-label={label} aria-valuemin={0} aria-valuemax={100} aria-valuenow={value}>
                        <div className="h-full rounded-full bg-brand-500" style={{ width: `${value}%` }} />
                      </div>
                    </li>
                  );
                })}
              </ul>
            </CardContent>
          </Card>

          <div className="flex flex-col gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Recent scores</CardTitle>
              </CardHeader>
              <CardContent>
                <table className="w-full text-sm">
                  <caption className="sr-only">Recent post quality scores</caption>
                  <thead className="text-left text-xs text-ink-500">
                    <tr>
                      <th scope="col" className="pb-2 font-medium">Date</th>
                      <th scope="col" className="pb-2 font-medium">Topic</th>
                      <th scope="col" className="pb-2 text-right font-medium">Score</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-ink-100">
                    {scored.slice(0, 8).map((p) => (
                      <tr key={p.id}>
                        <td className="py-2 pr-3 text-ink-600">{formatDate(p.created_at)}</td>
                        <td className="py-2 pr-3 text-ink-900">{p.topic ? titleCase(p.topic) : "-"}</td>
                        <td className="py-2 text-right font-medium tabular-nums text-ink-900">{p.score.overall}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>

            {usage ? (
              <Card>
                <CardHeader>
                  <CardTitle>Usage today</CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col gap-4">
                  <UsageMeter label="Post generation" usage={usage.features.generate} />
                  <UsageMeter label="Enhancements" usage={usage.features.enhance} />
                </CardContent>
              </Card>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}
