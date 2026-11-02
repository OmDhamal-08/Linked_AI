"use client";

import { useRef, useState } from "react";
import { BlueprintView } from "@/components/post/blueprint-view";
import { LoadingSteps } from "@/components/post/loading-steps";
import { PostResult } from "@/components/post/post-result";
import { UpgradeBanner } from "@/components/post/upgrade-banner";
import { GenerateForm } from "@/components/forms/generate-form";
import { Alert, Spinner } from "@/components/ui/feedback";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/use-auth";
import { useTaxonomy } from "@/hooks/use-taxonomy";
import { ApiError, apiFetch, errorMessage } from "@/lib/api";
import type { GeneratePayload } from "@/lib/schemas";
import type { GenerateResponse } from "@/types/api";

const GENERATE_TIMEOUT_MS = 90_000;

export default function GeneratePage() {
  const { user } = useAuth();
  const { taxonomy, error: taxonomyError } = useTaxonomy();
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [lastPayload, setLastPayload] = useState<GeneratePayload | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const controllerRef = useRef<AbortController | null>(null);
  const isPremium = user?.plan === "premium";

  async function run(payload: GeneratePayload) {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    setSubmitting(true);
    setError(null);
    try {
      const data = await apiFetch<GenerateResponse>("/posts/generate", {
        method: "POST",
        json: payload,
        signal: controller.signal,
        timeoutMs: GENERATE_TIMEOUT_MS,
      });
      setResult(data);
      setLastPayload(payload);
    } catch (err) {
      if (err instanceof ApiError && err.code === "cancelled") return;
      setError(errorMessage(err));
    } finally {
      if (controllerRef.current === controller) {
        controllerRef.current = null;
        setSubmitting(false);
      }
    }
  }

  function cancel() {
    controllerRef.current?.abort();
    controllerRef.current = null;
    setSubmitting(false);
  }

  return (
    <div className="flex flex-col gap-8">
      <header>
        <h1 className="text-2xl font-semibold text-ink-900">Generate a post</h1>
        <p className="mt-1 text-sm text-ink-600">Describe the achievement in your own words. We keep your facts and suggest the structure.</p>
      </header>

      {taxonomyError ? <Alert tone="danger">{taxonomyError}</Alert> : null}
      {error ? <Alert tone="danger">{error}</Alert> : null}

      <div className="grid gap-8 xl:grid-cols-[1fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Post details</CardTitle>
          </CardHeader>
          <CardContent>
            {taxonomy ? (
              <GenerateForm taxonomy={taxonomy} isPremium={isPremium} submitting={submitting} onSubmit={run} />
            ) : (
              <div className="flex items-center gap-2 text-sm text-ink-500">
                <Spinner className="h-4 w-4" /> Loading options…
              </div>
            )}
          </CardContent>
        </Card>

        <div className="flex min-w-0 flex-col gap-6">
          <LoadingSteps active={submitting} onCancel={cancel} />

          {!submitting && result ? (
            result.locked ? (
              <Card>
                <CardHeader>
                  <CardTitle>Your post plan</CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col gap-6">
                  <UpgradeBanner message={result.upgrade_hint} />
                  <BlueprintView blueprint={result.blueprint} suggestions={result.suggestions} />
                </CardContent>
              </Card>
            ) : result.post ? (
              <PostResult
                postId={result.post_id}
                text={result.post}
                variations={result.variations}
                hashtags={result.hashtags}
                score={result.score}
                analysis={result.analysis}
                suggestions={result.suggestions}
                keywordsUsed={result.keywords_used}
                onRegenerate={lastPayload ? () => run(lastPayload) : undefined}
                regenerating={submitting}
              />
            ) : null
          ) : null}

          {!submitting && !result ? (
            <Card className="border-dashed">
              <CardContent className="py-10 text-center text-sm text-ink-500">
                {user ? "Your generated post will appear here." : null}
                <p className="mt-2 text-xs">Free plans show the structure and hooks. Premium unlocks the complete post.</p>
              </CardContent>
            </Card>
          ) : null}
        </div>
      </div>
    </div>
  );
}
