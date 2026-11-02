"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft, Trash2 } from "lucide-react";
import { BlueprintView } from "@/components/post/blueprint-view";
import { PostResult } from "@/components/post/post-result";
import { UpgradeBanner } from "@/components/post/upgrade-banner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, Spinner } from "@/components/ui/feedback";
import { apiFetch, errorMessage } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { PostItem } from "@/types/api";

export default function HistoryDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [post, setPost] = useState<PostItem | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    let active = true;
    apiFetch<PostItem>(`/posts/${params.id}`)
      .then((data) => active && setPost(data))
      .catch((err) => active && setError(errorMessage(err)));
    return () => {
      active = false;
    };
  }, [params.id]);

  async function remove() {
    setDeleting(true);
    try {
      await apiFetch(`/posts/${params.id}`, { method: "DELETE" });
      router.replace("/history");
    } catch (err) {
      setError(errorMessage(err));
      setDeleting(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between gap-4">
        <Link href="/history" className="inline-flex items-center gap-2 text-sm font-medium text-ink-600 hover:text-ink-900">
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Back to history
        </Link>
        {post ? (
          <Button variant="ghost" size="sm" onClick={remove} loading={deleting}>
            <Trash2 className="h-4 w-4" aria-hidden="true" />
            Delete
          </Button>
        ) : null}
      </div>

      {error ? <Alert tone="danger">{error}</Alert> : null}
      {!post && !error ? (
        <div className="flex justify-center py-16">
          <Spinner />
        </div>
      ) : null}

      {post ? (
        <>
          <p className="text-sm text-ink-500">
            {post.type === "generate" ? "Generated" : "Enhanced"} on {formatDate(post.created_at)}
          </p>
          {post.output_text ? (
            <PostResult
              postId={post.id}
              text={post.output_text}
              hashtags={post.hashtags}
              score={post.score}
              analysis={
                post.analysis
                  ? {
                      tone: post.tone ?? undefined,
                      topic: post.topic ?? undefined,
                      structure: post.analysis.structure,
                      hook_strength: post.analysis.hook_score / 100,
                      readability: post.analysis.readability_score,
                      emotion: post.analysis.emotion ?? undefined,
                      hook_type: post.analysis.hook_type ?? undefined,
                    }
                  : null
              }
              suggestions={post.suggestions}
              keywordsUsed={post.keywords_used}
            />
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>Saved plan</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-6">
                <UpgradeBanner />
                <p className="text-sm text-ink-700">Original input:</p>
                <p className="prose-post rounded-md bg-ink-50/60 p-4 text-sm">{post.input_text}</p>
                <BlueprintView
                  blueprint={{ structure: post.analysis?.structure ?? [], hook_suggestions: [], cta: "question", keywords: post.keywords_used, hashtags: post.hashtags }}
                  suggestions={post.suggestions}
                />
              </CardContent>
            </Card>
          )}
        </>
      ) : null}
    </div>
  );
}
