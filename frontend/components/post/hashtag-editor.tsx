"use client";

import { type KeyboardEvent, useState } from "react";
import { X } from "lucide-react";
import { Badge } from "@/components/ui/feedback";

interface Props {
  value: string[];
  onChange: (tags: string[]) => void;
  max?: number;
}

function normalise(tag: string): string {
  return tag.trim().replace(/^#+/, "").replace(/[^A-Za-z0-9_]/g, "").slice(0, 40);
}

/** Accept, remove or add hashtags. Keeps the list short and relevant (max 5 by default). */
export function HashtagEditor({ value, onChange, max = 5 }: Props) {
  const [draft, setDraft] = useState("");

  function add(raw: string) {
    const tag = normalise(raw);
    if (!tag || value.some((t) => t.toLowerCase() === tag.toLowerCase()) || value.length >= max) return;
    onChange([...value, tag]);
    setDraft("");
  }

  function onKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter" || event.key === ",") {
      event.preventDefault();
      add(draft);
    } else if (event.key === "Backspace" && !draft && value.length) {
      onChange(value.slice(0, -1));
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center gap-1.5">
        {value.map((tag) => (
          <Badge key={tag} tone="brand" className="gap-1 pr-1">
            #{tag}
            <button
              type="button"
              aria-label={`Remove hashtag ${tag}`}
              onClick={() => onChange(value.filter((t) => t !== tag))}
              className="rounded-full p-0.5 hover:bg-brand-100"
            >
              <X className="h-3 w-3" aria-hidden="true" />
            </button>
          </Badge>
        ))}
      </div>
      <input
        aria-label="Add a hashtag"
        value={draft}
        disabled={value.length >= max}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={onKeyDown}
        onBlur={() => draft && add(draft)}
        placeholder={value.length >= max ? `Maximum ${max} hashtags` : "Add a hashtag and press Enter"}
        className="h-9 w-full rounded-lg border border-ink-200 px-3 text-sm placeholder:text-ink-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30 disabled:bg-ink-50"
      />
    </div>
  );
}
