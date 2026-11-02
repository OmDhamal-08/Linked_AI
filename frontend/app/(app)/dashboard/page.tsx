"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { BarChart3, FileText, Gauge, Sparkles } from "lucide-react";
import { UsageMeter } from "@/components/dashboard/usage-meter";
import { StatCard } from "@/components/dashboard/stat-card";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, Badge, EmptyState } from "@/components/ui/feedback";
import { useAuth } from "@/hooks/use-auth";
import { apiFetch, errorMessage } from "@/lib/api";
import { formatDate, titleCase } from "@/lib/utils";
import type { PostItem, PostList, SubscriptionInfo, UsageSummary } from "@/types/api";

export default function DashboardPage() {
  const { user } = useAuth();
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);
  const [recent, setRecent] = useState<PostItem[] | null>(null);
  const [stats, setStats] = useState<{ generated: number; enhanced: number; averageScore: number | null } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const [u, sub, recentPosts, gen, enh] = await Promise.all([
          apiFetch<UsageSummary>("/usage"),
          apiFetch<SubscriptionInfo>("/subscription"),
          apiFetch<PostList>("/posts?limit=5"),
          apiFetch<PostList>("/posts?type=generate&limit=50"),
          apiFetch<PostList>("/posts?type=enhance&limit=1"),
        ]);
        if (!active) return;
        const scores = gen.items.map((p) => p.score?.overall).filter((v): v is number => typeof v === "number");
        setUsage(u);
        setSubscription(sub);
        setRecent(recentPosts.items);
        setStats({
          generated: gen.total,
          enhanced: enh.total,
          averageScore: scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : null,
        });
      } catch (err) {
        if (active) setError(errorMessage(err));
      }
    }
    void load();
    return () => {
      active = false;
    };
  }, []);

  const firstName = user?.name?.split(" ")[0] ?? user?.email?.split("@")[0] ?? "there";

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-ink-900">Welcome back, {firstName}</h1>
          <p className="mt-1 text-sm text-ink-600">Pick up where you left off, or start something new.</p>
        </div>
        <div className="flex gap-2">
          <Link href="/generate">
            <Button>
              <Sparkles className="h-4 w-4" aria-hidden="true" />
              Generate post
            </Button>
          </Link>
          <Link href="/enhance">
            <Button variant="secondary">Enhance post</Button>
          </Link>
        </div>
      </header>

      {error ? <Alert tone="danger">{error}</Alert> : null}

      <section aria-label="Quick statistics" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Posts generated" value={stats?.generated ?? "–"} icon={<FileText className="h-4 w-4" aria-hidden="true" />} />
        <StatCard label="Posts enhanced" value={stats?.enhanced ?? "–"} icon={<Sparkles className="h-4 w-4" aria-hidden="true" />} />
        <StatCard
          label="Average quality score"
          value={stats?.averageScore ?? "–"}
          hint="AI content quality (not reach)"
          icon={<Gauge className="h-4 w-4" aria-hidden="true" />}
        />
        <StatCard
          label="Current plan"
          value={<span className="capitalize">{subscription?.plan ?? user?.plan ?? "free"}</span>}
          hint={subscription?.plan === "premium" ? "Full posts unlocked" : "Upgrade for full posts"}
          icon={<BarChart3 className="h-4 w-4" aria-hidden="true" />}
        />
      </section>

      <div className="grid gap-6 xl:grid-cols-[1fr_1.5fr]">
        <Card>
          <CardHeader>
            <CardTitle>Today&apos;s usage</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-5">
            {usage ? (
              <>
                <UsageMeter label="Post generation" usage={usage.features.generate} />
                <UsageMeter label="Enhancements" usage={usage.features.enhance} />
                <p className="text-xs text-ink-500">Limits reset at midnight UTC.</p>
              </>
            ) : (
              <p className="text-sm text-ink-500">Loading usage…</p>
            )}
            {subscription?.plan !== "premium" ? (
              <Link href="/pricing" className="text-sm font-medium text-brand-700 hover:underline">
                Compare plans
              </Link>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle>Recent posts</CardTitle>
            <Link href="/history" className="text-sm font-medium text-brand-700 hover:underline">
              View all
            </Link>
          </CardHeader>
          <CardContent>
            {recent === null ? (
              <p className="text-sm text-ink-500">Loading…</p>
            ) : recent.length === 0 ? (
              <EmptyState
                title="No posts yet"
                description="Generate your first post from an achievement, or paste a draft to enhance."
                action={
                  <Link href="/generate">
                    <Button size="sm">Create a post</Button>
                  </Link>
                }
              />
            ) : (
              <ul className="divide-y divide-ink-100">
                {recent.map((post) => (
                  <li key={post.id} className="flex items-center justify-between gap-4 py-3">
                    <Link href={`/history/${post.id}`} className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-ink-900">
                        {post.topic || (post.input_text.slice(0, 60) + "…")}
                      </p>
                      <p className="text-xs text-ink-500">{formatDate(post.created_at)}</p>
                    </Link>
                    <div className="flex shrink-0 items-center gap-2">
                      <Badge>{post.type === "generate" ? "Generated" : "Enhanced"}</Badge>
                      {post.category ? <Badge className="hidden sm:inline-flex">{titleCase(post.category)}</Badge> : null}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
