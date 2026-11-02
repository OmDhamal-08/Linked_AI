"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import type { PlansInfo, Taxonomy } from "@/types/api";

/** Loads option lists from the backend so the UI never hard-codes categories or tones. */
export function useTaxonomy() {
  const [taxonomy, setTaxonomy] = useState<Taxonomy | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    apiFetch<Taxonomy>("/meta/taxonomy", { auth: false })
      .then((data) => active && setTaxonomy(data))
      .catch(() => active && setError("Could not load form options. Refresh to try again."));
    return () => {
      active = false;
    };
  }, []);

  return { taxonomy, error };
}

export function usePlans() {
  const [plans, setPlans] = useState<PlansInfo | null>(null);
  useEffect(() => {
    let active = true;
    apiFetch<PlansInfo>("/meta/plans", { auth: false })
      .then((data) => active && setPlans(data))
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, []);
  return plans;
}
