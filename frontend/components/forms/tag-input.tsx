"use client";

import { type KeyboardEvent, useId, useState } from "react";
import { X } from "lucide-react";
import { Badge } from "@/components/ui/feedback";

interface Props {
  label: string;
  value: string[];
  onChange: (next: string[]) => void;
  max?: number;
  hint?: string;
  error?: string;
  placeholder?: string;
}

/** Keyword chips. Enter or comma adds a term; duplicates are ignored case-insensitively. */
export function TagInput({ label, value, onChange, max = 10, hint, error, placeholder }: Props) {
  const [draft, setDraft] = useState("");
  const id = useId();

  function add(raw: string) {
    const term = raw.trim().slice(0, 40);
    if (!term) return;
    if (value.length >= max) return;
    if (value.some((v) => v.toLowerCase() === term.toLowerCase())) {
      setDraft("");
      return;
    }
    onChange([...value, term]);
    setDraft("");
  }

  function onKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter" || event.key === ",") {
      event.preventDefault();
      add(draft);
    } else if (event.key === "Backspace" && draft === "" && value.length) {
      onChange(value.slice(0, -1));
    }
  }

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium text-ink-800">
        {label}
      </label>
      <div className="flex min-h-10 flex-wrap items-center gap-1.5 rounded-lg border border-ink-200 bg-white px-2 py-1.5 focus-within:border-brand-500 focus-within:ring-2 focus-within:ring-brand-500/30">
        {value.map((term) => (
          <Badge key={term} tone="brand" className="gap-1 pr-1">
            {term}
            <button
              type="button"
              aria-label={`Remove ${term}`}
              onClick={() => onChange(value.filter((v) => v !== term))}
              className="rounded-full p-0.5 hover:bg-brand-100"
            >
              <X className="h-3 w-3" aria-hidden="true" />
            </button>
          </Badge>
        ))}
        <input
          id={id}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={onKeyDown}
          onBlur={() => add(draft)}
          disabled={value.length >= max}
          aria-invalid={Boolean(error) || undefined}
          aria-describedby={hint || error ? `${id}-desc` : undefined}
          placeholder={value.length >= max ? `Maximum ${max} keywords` : placeholder ?? "Type a keyword and press Enter"}
          className="min-w-[10rem] flex-1 border-0 bg-transparent px-1 py-1 text-sm text-ink-900 placeholder:text-ink-400 focus:outline-none"
        />
      </div>
      {error ? (
        <p id={`${id}-desc`} role="alert" className="text-xs text-red-600">
          {error}
        </p>
      ) : hint ? (
        <p id={`${id}-desc`} className="text-xs text-ink-500">
          {hint}
        </p>
      ) : null}
    </div>
  );
}
