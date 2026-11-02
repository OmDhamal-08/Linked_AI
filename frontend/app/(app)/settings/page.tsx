"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, Badge } from "@/components/ui/feedback";
import { useAuth } from "@/hooks/use-auth";
import { apiFetch, errorMessage } from "@/lib/api";
import { MOCK_PAYMENTS_ENABLED } from "@/lib/config";
import { formatDate } from "@/lib/utils";
import type { SubscriptionInfo } from "@/types/api";

export default function SettingsPage() {
  const { user, logout, refresh } = useAuth();
  const router = useRouter();
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<{ tone: "success" | "danger"; message: string } | null>(null);

  useEffect(() => {
    apiFetch<SubscriptionInfo>("/subscription")
      .then(setSubscription)
      .catch((err) => setStatus({ tone: "danger", message: errorMessage(err) }));
  }, []);

  async function changePlan(path: "/subscription/mock-upgrade" | "/subscription/cancel") {
    setBusy(true);
    setStatus(null);
    try {
      const data = await apiFetch<SubscriptionInfo>(path, { method: "POST" });
      setSubscription(data);
      await refresh();
      setStatus({ tone: "success", message: path.endsWith("cancel") ? "Your plan is now Free." : "Premium is active." });
    } catch (err) {
      setStatus({ tone: "danger", message: errorMessage(err) });
    } finally {
      setBusy(false);
    }
  }

  async function signOut() {
    await logout();
    router.replace("/login");
  }

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold text-ink-900">Settings</h1>
        <p className="mt-1 text-sm text-ink-600">Manage your plan and session.</p>
      </header>

      {status ? <Alert tone={status.tone === "success" ? "success" : "danger"}>{status.message}</Alert> : null}

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>Plan</CardTitle>
          <CardDescription>
            {subscription?.plan === "premium" ? "You have full access to posts and variations." : "You are on the Free plan."}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-5">
          <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
            <dt className="text-ink-500">Current plan</dt>
            <dd>
              <Badge tone={subscription?.plan === "premium" ? "brand" : "neutral"}>{subscription?.plan ?? user?.plan ?? "free"}</Badge>
            </dd>
            <dt className="text-ink-500">Status</dt>
            <dd className="capitalize text-ink-900">{subscription?.status ?? "-"}</dd>
            <dt className="text-ink-500">Renews / expires</dt>
            <dd className="text-ink-900">{subscription?.expires_at ? formatDate(subscription.expires_at) : "-"}</dd>
          </dl>
          <div className="flex flex-wrap gap-2">
            {subscription?.plan !== "premium" ? (
              <Link href="/pricing">
                <Button variant="secondary">Compare plans</Button>
              </Link>
            ) : null}
            {MOCK_PAYMENTS_ENABLED && subscription?.plan !== "premium" ? (
              <Button onClick={() => changePlan("/subscription/mock-upgrade")} loading={busy}>
                Activate Premium (test mode)
              </Button>
            ) : null}
            {subscription?.plan === "premium" ? (
              <Button variant="secondary" onClick={() => changePlan("/subscription/cancel")} loading={busy}>
                Cancel subscription
              </Button>
            ) : null}
          </div>
          {MOCK_PAYMENTS_ENABLED ? (
            <p className="text-xs text-ink-500">Test mode: no real payment is taken. Disable mock payments in production.</p>
          ) : null}
        </CardContent>
      </Card>

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>Session</CardTitle>
          <CardDescription>Sign out on this device.</CardDescription>
        </CardHeader>
        <CardContent>
          <Button variant="danger" onClick={signOut}>
            Sign out
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
