"use client";

import { useState } from "react";
import { Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Alert } from "@/components/ui/feedback";
import { apiFetch, errorMessage } from "@/lib/api";
import type { IngestionReport } from "@/types/api";

/** Admin dataset upload. Shows the counts the backend reports for every ingestion. */
export function IngestionUpload({ onDone }: { onDone?: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [report, setReport] = useState<IngestionReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) {
      setError("Choose a .csv or .json file first.");
      return;
    }
    setBusy(true);
    setError(null);
    setReport(null);
    try {
      const body = new FormData();
      body.append("file", file);
      const result = await apiFetch<IngestionReport>("/admin/knowledge/ingest", { method: "POST", body, timeoutMs: 180_000 });
      setReport(result);
      onDone?.();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-4" aria-label="Upload a knowledge dataset">
      <label className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-ink-300 bg-white px-6 py-8 text-center hover:border-brand-400">
        <Upload className="h-5 w-5 text-ink-500" aria-hidden="true" />
        <span className="text-sm font-medium text-ink-800">{file ? file.name : "Choose a CSV or JSON file"}</span>
        <span className="text-xs text-ink-500">Requires a text column. Other metadata is generated when missing.</span>
        <input
          type="file"
          accept=".csv,.json,application/json,text/csv"
          className="sr-only"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
      </label>
      <div className="flex justify-end">
        <Button type="submit" loading={busy}>
          Ingest dataset
        </Button>
      </div>
      {error ? <Alert tone="danger">{error}</Alert> : null}
      {report ? (
        <Alert tone={report.status === "completed" ? "success" : "danger"} title={`Ingestion ${report.status}`}>
          <dl className="mt-2 grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
            <dt>Records uploaded</dt>
            <dd>{report.records_uploaded}</dd>
            <dt>Records processed</dt>
            <dd>{report.records_processed}</dd>
            <dt>Records rejected</dt>
            <dd>{report.records_rejected}</dd>
            <dt>Duplicates skipped</dt>
            <dd>{report.duplicates}</dd>
            <dt>Embeddings generated</dt>
            <dd>{report.embeddings_generated}</dd>
            <dt>PII redacted</dt>
            <dd>{report.pii_redacted}</dd>
          </dl>
        </Alert>
      ) : null}
    </form>
  );
}
