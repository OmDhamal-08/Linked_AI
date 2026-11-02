"use client";

import { useState } from "react";
import { Check, Copy, Pencil, RefreshCw, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Alert, Badge } from "@/components/ui/feedback";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { HashtagEditor } from "@/components/post/hashtag-editor";
import { ScoreCard } from "@/components/post/score-card";
import { AnalysisPanel } from "@/components/post/analysis-panel";
import { apiFetch, errorMessage } from "@/lib/api";
import { copyText } from "@/lib/utils";
import type { Analysis, QualityScore, Suggestion } from "@/types/api";

interface Props {
  postId: string | null;
  text: string;
  variations?: string[];
  hashtags: string[];
  score: QualityScore | null;
  analysis?: Analysis | null;
  suggestions?: Suggestion[];
  keywordsUsed?: string[];
  title?: string;
  onRegenerate?: () => void;
  regenerating?: boolean;
}

/** Shows a generated or enhanced post with copy, regenerate, variations, edit, save and analysis. */
export function PostResult({
  postId,
  text,
  variations = [],
  hashtags,
  score,
  analysis,
  suggestions = [],
  keywordsUsed = [],
  title = "Your post",
  onRegenerate,
  regenerating = false,
}: Props) {
  const allVersions = [text, ...variations.filter((v) => v !== text)];
  const [activeIndex, setActiveIndex] = useState(0);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");
  const [current, setCurrent] = useState<string | null>(null);
  const [tags, setTags] = useState<string[]>(hashtags);
  const [copied, setCopied] = useState(false);
  const [status, setStatus] = useState<{ tone: "success" | "danger"; message: string } | null>(null);
  const [saving, setSaving] = useState(false);

  const body = current ?? allVersions[activeIndex] ?? text;

  async function handleCopy() {
    const finalText = [body, tags.length ? tags.map((t) => `#${t}`).join(" ") : ""].filter(Boolean).join("\n\n");
    const ok = await copyText(finalText);
    setCopied(ok);
    setStatus(ok ? null : { tone: "danger", message: "Copy is not available in this browser. Select the text and copy it manually." });
    if (ok) setTimeout(() => setCopied(false), 1800);
  }

  function startEdit() {
    setDraft(body);
    setEditing(true);
    setStatus(null);
  }

  async function saveEdits() {
    if (!postId) {
      setCurrent(draft);
      setEditing(false);
      return;
    }
    setSaving(true);
    setStatus(null);
    try {
      await apiFetch(`/posts/${postId}`, { method: "PATCH", json: { output_text: draft, hashtags: tags } });
      setCurrent(draft);
      setEditing(false);
      setStatus({ tone: "success", message: "Saved to your history." });
    } catch (error) {
      setStatus({ tone: "danger", message: errorMessage(error) });
    } finally {
      setSaving(false);
    }
  }

  async function saveHashtags(next: string[]) {
    setTags(next);
    if (!postId) return;
    try {
      await apiFetch(`/posts/${postId}`, { method: "PATCH", json: { hashtags: next } });
    } catch (error) {
      setStatus({ tone: "danger", message: errorMessage(error) });
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
      <Card className="min-w-0">
        <CardHeader className="flex-row items-center justify-between gap-3">
          <div className="flex flex-col gap-1">
            <CardTitle>{title}</CardTitle>
            {postId ? <span className="text-xs text-ink-500">Saved automatically to your history</span> : null}
          </div>
          <div className="flex flex-wrap items-center justify-end gap-2">
            <Button variant="secondary" size="sm" onClick={handleCopy} aria-label="Copy post">
              {copied ? <Check className="h-4 w-4" aria-hidden="true" /> : <Copy className="h-4 w-4" aria-hidden="true" />}
              {copied ? "Copied" : "Copy"}
            </Button>
            {onRegenerate ? (
              <Button variant="secondary" size="sm" onClick={onRegenerate} loading={regenerating}>
                <RefreshCw className="h-4 w-4" aria-hidden="true" />
                Regenerate
              </Button>
            ) : null}
            {!editing ? (
              <Button variant="secondary" size="sm" onClick={startEdit}>
                <Pencil className="h-4 w-4" aria-hidden="true" />
                Edit
              </Button>
            ) : null}
          </div>
        </CardHeader>
        <CardContent className="flex flex-col gap-5">
          {allVersions.length > 1 ? (
            <div role="tablist" aria-label="Variations" className="flex gap-2">
              {allVersions.map((_, i) => (
                <button
                  key={i}
                  role="tab"
                  aria-selected={activeIndex === i}
                  onClick={() => {
                    setActiveIndex(i);
                    setCurrent(null);
                  }}
                  className={`rounded-full px-3 py-1 text-xs font-medium ${activeIndex === i ? "bg-brand-600 text-white" : "bg-ink-100 text-ink-700 hover:bg-ink-200"}`}
                >
                  Variation {i + 1}
                </button>
              ))}
            </div>
          ) : null}

          {editing ? (
            <div className="flex flex-col gap-3">
              <label htmlFor="post-editor" className="sr-only">
                Edit your post
              </label>
              <textarea
                id="post-editor"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                className="min-h-[260px] w-full rounded-lg border border-ink-200 p-4 text-[15px] leading-7 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
              />
              <div className="flex gap-2">
                <Button onClick={saveEdits} loading={saving}>
                  <Save className="h-4 w-4" aria-hidden="true" />
                  Save changes
                </Button>
                <Button variant="ghost" onClick={() => setEditing(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <article aria-label="Post text" className="prose-post rounded-lg bg-ink-50/60 p-5">
              {body}
            </article>
          )}

          {status ? <Alert tone={status.tone === "success" ? "success" : "danger"}>{status.message}</Alert> : null}

          <div className="flex flex-col gap-2">
            <p className="text-xs font-medium text-ink-600">Hashtags</p>
            <HashtagEditor value={tags} onChange={saveHashtags} />
          </div>

          {keywordsUsed.length ? (
            <div>
              <p className="mb-2 text-xs font-medium text-ink-600">Keywords used</p>
              <div className="flex flex-wrap gap-1.5">
                {keywordsUsed.map((k) => (
                  <Badge key={k} tone="brand">
                    {k}
                  </Badge>
                ))}
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <div className="flex min-w-0 flex-col gap-6">
        {score ? (
          <Card>
            <CardContent className="pt-5">
              <ScoreCard score={score} />
            </CardContent>
          </Card>
        ) : null}
        <Card>
          <CardHeader>
            <CardTitle>Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <AnalysisPanel analysis={analysis} suggestions={suggestions} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
