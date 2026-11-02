"use client";

import Link from "next/link";
import { Check } from "lucide-react";
import { PublicHeader } from "@/components/layout/public-header";
import { Button } from "@/components/ui/button";
import { Alert } from "@/components/ui/feedback";
import { usePlans } from "@/hooks/use-taxonomy";

function Feature({ included, children }: { included: boolean; children: React.ReactNode }) {
  return (
    <li className={`flex items-start gap-2 text-sm ${included ? "text-ink-800" : "text-ink-400"}`}>
      <Check className={`mt-0.5 h-4 w-4 shrink-0 ${included ? "text-brand-600" : "text-ink-300"}`} aria-hidden="true" />
      <span>
        {children}
        {!included ? <span className="sr-only"> (not included)</span> : null}
      </span>
    </li>
  );
}

export default function PricingPage() {
  const plans = usePlans();

  return (
    <div className="min-h-screen bg-ink-50">
      <PublicHeader />
      <main id="main" className="mx-auto max-w-4xl px-4 py-16 sm:px-6">
        <div className="text-center">
          <h1 className="text-3xl font-semibold text-ink-900">Simple plans</h1>
          <p className="mt-3 text-ink-600">Start free. Upgrade when you want full posts and the complete enhanced version.</p>
        </div>

        {!plans ? (
          <div className="mt-10">
            <Alert>Loading plan details…</Alert>
          </div>
        ) : null}

        <div className="mt-12 grid gap-6 md:grid-cols-2">
          <section aria-labelledby="free-plan" className="flex flex-col rounded-xl border border-ink-200 bg-white p-8 shadow-card">
            <h2 id="free-plan" className="text-lg font-semibold text-ink-900">
              Free
            </h2>
            <p className="mt-1 text-sm text-ink-500">For trying it out and improving your drafts.</p>
            <ul className="mt-6 flex flex-1 flex-col gap-3">
              <Feature included>
                {plans ? plans.free.generations_per_day : "A few"} post plans per day (blueprint: hooks, structure, keywords)
              </Feature>
              <Feature included>{plans ? plans.free.enhancements_per_day : "A few"} draft analyses per day</Feature>
              <Feature included>Quality analysis and suggestions</Feature>
              <Feature included={Boolean(plans?.free.full_post_generation)}>Complete generated posts</Feature>
              <Feature included={Boolean(plans?.free.enhanced_post)}>Complete enhanced posts</Feature>
              <Feature included={false}>Multiple variations and advanced review</Feature>
            </ul>
            <Link href="/signup" className="mt-8">
              <Button variant="secondary" className="w-full">
                Start free
              </Button>
            </Link>
          </section>

          <section aria-labelledby="premium-plan" className="flex flex-col rounded-xl border-2 border-brand-500 bg-white p-8 shadow-card">
            <h2 id="premium-plan" className="text-lg font-semibold text-ink-900">
              Premium
            </h2>
            <p className="mt-1 text-sm text-ink-500">For people who publish regularly.</p>
            <ul className="mt-6 flex flex-1 flex-col gap-3">
              <Feature included>Complete generated posts</Feature>
              <Feature included>Complete enhanced posts</Feature>
              <Feature included>
                Up to {plans ? plans.premium.variations : 3} variations per request
              </Feature>
              <Feature included>Advanced editorial review</Feature>
              <Feature included>Higher daily allowance{plans ? ` (up to ${plans.premium.daily_cap} per day)` : ""}</Feature>
            </ul>
            <Link href="/signup" className="mt-8">
              <Button className="w-full">Get Premium</Button>
            </Link>
          </section>
        </div>
        <p className="mt-8 text-center text-xs text-ink-500">
          Quality scores are guidance on clarity and structure. They do not predict LinkedIn reach.
        </p>
      </main>
    </div>
  );
}
