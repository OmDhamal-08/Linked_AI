"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Copy, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Alert, Badge, EmptyState, Spinner } from "@/components/ui/feedback";
import { SelectField } from "@/components/ui/field";
import { apiFetch, errorMessage } from "@/lib/api";
import { copyText, formatDate, titleCase } from "@/lib/utils";
import type { PostItem, PostList } from "@/types/api";

const PAGE_SIZE = 10;

export default function HistoryPage() {
  const [items, setItems] = useState<PostItem[] | null>(null);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [type, setType] = useState<"" | "generate" | "enhance">("");
  const [error, setError] = useState<string | null>(null);
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    const params = new URLSearchParams({ limit: String(PAGE_SIZE), offset: String(offset) });
    if (type) params.set("type", type);
    try {
      const data = await apiFetch<PostList>(`/posts?${params.toString()}`);
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(errorMessage(err));
    }
  }, [offset, type]);

  useEffect(() => {
    void load();
  }, [load]);

  async function remove(id: string) {
    try {
      await apiFetch(`/posts/${id}`, { method: "DELETE" });
      setConfirmId(null);
      setNotice("Post deleted.");
      await load();
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  async function copy(post: PostItem) {
    const ok = await copyText(post.output_text ?? post.input_text);
    setNotice(ok ? "Copied to clipboard." : "Copy is not available in this browser.");
  }

  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const page = Math.floor(offset / PAGE_SIZE) + 1;

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-ink-900">History</h1>
          <p className="mt-1 text-sm text-ink-600">Every post you generated or enhanced, newest first.</p>
        </div>
        <div className="w-full sm:w-56">
          <SelectField
            label="Show"
            value={type}
            onChange={(e) => {
              setOffset(0);
              setType(e.target.value as "" | "generate" | "enhance");
            }}
            options={[
              { value: "", label: "All posts" },
              { value: "generate", label: "Generated" },
              { value: "enhance", label: "Enhanced" },
            ]}
          />
        </div>
      </header>

      {error ? <Alert tone="danger">{error}</Alert> : null}
      {notice ? <Alert tone="success">{notice}</Alert> : null}

      {items === null && !error ? (
        <div className="flex justify-center py-12">
          <Spinner />
        </div>
      ) : null}

      {items && items.length === 0 ? (
        <EmptyState title="Nothing here yet" description="Posts you generate or enhance will be saved here." />
      ) : null}

      {items && items.length > 0 ? (
        <Card>
          <ul className="divide-y divide-ink-100">
            {items.map((post) => (
              <li key={post.id} className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0 flex-1">
                  <Link href={`/history/${post.id}`} className="block truncate text-sm font-medium text-ink-900 hover:text-brand-700">
                    {post.topic || post.input_text.slice(0, 80)}
                  </Link>
                  <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-ink-500">
                    <span>{formatDate(post.created_at)}</span>
                    <Badge>{post.type === "generate" ? "Generated" : "Enhanced"}</Badge>
                    {post.category ? <Badge>{titleCase(post.category)}</Badge> : null}
                    {post.score ? <span>Quality {post.score.overall}/100</span> : null}
                    {!post.output_text ? <span className="text-amber-700">Plan only</span> : null}
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <Link href={`/history/${post.id}`}>
                    <Button variant="secondary" size="sm">
                      View
                    </Button>
                  </Link>
                  <Button variant="ghost" size="sm" onClick={() => copy(post)} aria-label={`Copy post from ${formatDate(post.created_at)}`}>
                    <Copy className="h-4 w-4" aria-hidden="true" />
                  </Button>
                  {confirmId === post.id ? (
                    <>
                      <Button variant="danger" size="sm" onClick={() => remove(post.id)}>
                        Confirm delete
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => setConfirmId(null)}>
                        Keep
                      </Button>
                    </>
                  ) : (
                    <Button variant="ghost" size="sm" onClick={() => setConfirmId(post.id)} aria-label="Delete post">
                      <Trash2 className="h-4 w-4" aria-hidden="true" />
                    </Button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      {total > PAGE_SIZE ? (
        <nav aria-label="Pagination" className="flex items-center justify-between text-sm text-ink-600">
          <Button variant="secondary" size="sm" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>
            Previous
          </Button>
          <span>
            Page {page} of {pages}
          </span>
          <Button variant="secondary" size="sm" disabled={page >= pages} onClick={() => setOffset(offset + PAGE_SIZE)}>
            Next
          </Button>
        </nav>
      ) : null}
    </div>
  );
}
