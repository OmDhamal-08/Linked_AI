"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";

export const LOADING_MESSAGES = [
  "Analyzing your content...",
  "Finding relevant content patterns...",
  "Creating your post...",
  "Checking quality...",
];

/** Cycles progress messages while a request runs, with a Cancel action. */
export function LoadingSteps({ active, onCancel }: { active: boolean; onCancel?: () => void }) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (!active) {
      setIndex(0);
      return;
    }
    const timer = setInterval(() => setIndex((i) => Math.min(i + 1, LOADING_MESSAGES.length - 1)), 1400);
    return () => clearInterval(timer);
  }, [active]);

  if (!active) return null;
  return (
    <div className="flex items-center gap-3 rounded-md border border-ink-200 p-4" aria-live="polite">
      <span aria-hidden="true" className="h-4 w-4 animate-spin rounded-full border-2 border-ink-200 border-t-ink-600" />
      <p className="flex-1 text-sm text-ink-700">{LOADING_MESSAGES[index]}</p>
      {onCancel ? (
        <Button variant="ghost" size="sm" onClick={onCancel}>
          Cancel
        </Button>
      ) : null}
    </div>
  );
}
