"use client";

import { useCallback, useEffect, useState } from "react";
import { IngestionUpload } from "@/components/admin/ingestion-upload";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, Badge, EmptyState } from "@/components/ui/feedback";
import { useAuth } from "@/hooks/use-auth";
import { apiFetch, errorMessage } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { IngestionReport, KnowledgeItem } from "@/types/api";

interface KnowledgeList {
  items: KnowledgeItem[];
  total: number;
}
interface UsageRow {
  date: string;
  feature: string;
  provider: string | null;
  status: string;
  requests: number;
  tokens: number;
  estimated_cost: number;
}
interface ErrorRow {
  id: string;
  feature: string;
  provider: string | null;
  error_code: string | null;
  created_at: string;
}

export default function AdminPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<{ total: number; by_category: Record<string, number> } | null>(null);
  const [knowledge, setKnowledge] = useState<KnowledgeList | null>(null);
  const [jobs, setJobs] = useState<IngestionReport[] | null>(null);
  const [usage, setUsage] = useState<UsageRow[] | null>(null);
  const [errors, setErrors] = useState<ErrorRow[] | null>(null);
  const [message, setMessage] = useState<{ tone: "success" | "danger"; text: string } | null>(null);

  const loadAll = useCallback(async () => {
    try {
      const [s, k, j, u, e] = await Promise.all([
        apiFetch<{ total: number; by_category: Record<string, number> }>("/admin/knowledge/stats"),
        apiFetch<KnowledgeList>("/admin/knowledge?limit=20"),
        apiFetch<{ items: IngestionReport[] }>("/admin/ingestion-jobs"),
        apiFetch<{ rows: UsageRow[] }>("/admin/usage?days=30"),
        apiFetch<{ items: ErrorRow[] }>("/admin/errors"),
      ]);
      setStats(s);
      setKnowledge(k);
      setJobs(j.items);
      setUsage(u.rows);
      setErrors(e.items);
    } catch (err) {
      setMessage({ tone: "danger", text: errorMessage(err) });
    }
  }, []);

  useEffect(() => {
    if (user?.is_admin) void loadAll();
  }, [user, loadAll]);

  async function deleteItem(id: string) {
    try {
      await apiFetch(`/admin/knowledge/${id}`, { method: "DELETE" });
      setMessage({ tone: "success", text: "Record removed from the knowledge base." });
      await loadAll();
    } catch (err) {
      setMessage({ tone: "danger", text: errorMessage(err) });
    }
  }

  if (!user?.is_admin) {
    return <Alert tone="danger" title="Admin access required">Ask an administrator to grant you access.</Alert>;
  }

  return (
    <div className="flex flex-col gap-8">
      <header>
        <h1 className="text-2xl font-semibold text-ink-900">Admin</h1>
        <p className="mt-1 text-sm text-ink-600">Knowledge base, ingestion, usage and errors.</p>
      </header>

      {message ? <Alert tone={message.tone === "success" ? "success" : "danger"}>{message.text}</Alert> : null}

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Upload a dataset</CardTitle>
          </CardHeader>
          <CardContent>
            <IngestionUpload onDone={loadAll} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Knowledge base</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <p className="text-sm text-ink-700">
              <span className="text-2xl font-semibold text-ink-900">{stats?.total ?? "–"}</span> records
            </p>
            <div className="flex flex-wrap gap-1.5">
              {stats
                ? Object.entries(stats.by_category).map(([cat, n]) => (
                    <Badge key={cat}>
                      {cat}: {n}
                    </Badge>
                  ))
                : null}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent ingestion jobs</CardTitle>
        </CardHeader>
        <CardContent>
          {jobs && jobs.length === 0 ? <EmptyState title="No ingestion jobs yet" /> : null}
          {jobs && jobs.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs text-ink-500">
                  <tr>
                    <th scope="col" className="pb-2 font-medium">File</th>
                    <th scope="col" className="pb-2 font-medium">Status</th>
                    <th scope="col" className="pb-2 font-medium">Uploaded</th>
                    <th scope="col" className="pb-2 font-medium">Processed</th>
                    <th scope="col" className="pb-2 font-medium">Rejected</th>
                    <th scope="col" className="pb-2 font-medium">Duplicates</th>
                    <th scope="col" className="pb-2 font-medium">Embeddings</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-ink-100">
                  {jobs.map((j) => (
                    <tr key={j.job_id}>
                      <td className="py-2 pr-3">{j.filename}</td>
                      <td className="py-2 pr-3 capitalize">{j.status}</td>
                      <td className="py-2 pr-3">{j.records_uploaded}</td>
                      <td className="py-2 pr-3">{j.records_processed}</td>
                      <td className="py-2 pr-3">{j.records_rejected}</td>
                      <td className="py-2 pr-3">{j.duplicates}</td>
                      <td className="py-2 pr-3">{j.embeddings_generated}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Knowledge records</CardTitle>
        </CardHeader>
        <CardContent>
          {knowledge && knowledge.items.length === 0 ? <EmptyState title="No records" /> : null}
          <ul className="divide-y divide-ink-100">
            {knowledge?.items.map((item) => (
              <li key={item.id} className="flex flex-col gap-2 py-3 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-ink-900">{item.topic}</p>
                  <p className="text-xs text-ink-500">
                    {item.category} · {item.tone} · {item.hook_type} · {item.cta_type}
                  </p>
                </div>
                <Button variant="ghost" size="sm" onClick={() => deleteItem(item.id)} aria-label={`Delete ${item.topic}`}>
                  Delete
                </Button>
              </li>
            ))}
          </ul>
          {knowledge ? <p className="mt-3 text-xs text-ink-500">Showing {knowledge.items.length} of {knowledge.total}.</p> : null}
        </CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Usage (last 30 days)</CardTitle>
          </CardHeader>
          <CardContent>
            {usage && usage.length === 0 ? <EmptyState title="No usage yet" /> : null}
            {usage && usage.length > 0 ? (
              <table className="w-full text-left text-sm">
                <thead className="text-xs text-ink-500">
                  <tr>
                    <th scope="col" className="pb-2 font-medium">Date</th>
                    <th scope="col" className="pb-2 font-medium">Feature</th>
                    <th scope="col" className="pb-2 font-medium">Status</th>
                    <th scope="col" className="pb-2 font-medium">Requests</th>
                    <th scope="col" className="pb-2 font-medium">Tokens</th>
                    <th scope="col" className="pb-2 font-medium">Est. cost</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-ink-100">
                  {usage.map((row, i) => (
                    <tr key={`${row.date}-${row.feature}-${row.status}-${i}`}>
                      <td className="py-2 pr-3">{row.date}</td>
                      <td className="py-2 pr-3">{row.feature}</td>
                      <td className="py-2 pr-3">{row.status}</td>
                      <td className="py-2 pr-3">{row.requests}</td>
                      <td className="py-2 pr-3">{row.tokens}</td>
                      <td className="py-2 pr-3">${row.estimated_cost.toFixed(4)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent errors</CardTitle>
          </CardHeader>
          <CardContent>
            {errors && errors.length === 0 ? <EmptyState title="No recent errors" description="Failures are recorded here with a code, never a stack trace." /> : null}
            <ul className="divide-y divide-ink-100">
              {errors?.map((e) => (
                <li key={e.id} className="flex flex-wrap items-center gap-2 py-2 text-sm">
                  <Badge tone="danger">{e.error_code ?? "error"}</Badge>
                  <span className="text-ink-700">{e.feature}</span>
                  <span className="text-ink-500">{e.provider ?? ""}</span>
                  <span className="ml-auto text-xs text-ink-500">{formatDate(e.created_at)}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
