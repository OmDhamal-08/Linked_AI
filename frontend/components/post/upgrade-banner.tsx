import Link from "next/link";
import { Lock } from "lucide-react";
import { Button } from "@/components/ui/button";

export function UpgradeBanner({ message }: { message?: string | null }) {
  return (
    <div className="flex flex-col gap-3 rounded-md border border-ink-200 bg-ink-50 p-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-start gap-3">
        <Lock className="mt-0.5 h-4 w-4 shrink-0 text-ink-500" aria-hidden="true" />
        <div>
          <p className="text-sm font-semibold text-ink-900">Full post is a Premium feature</p>
          <p className="text-sm text-ink-600">
            {message ?? "You can still review the analysis, keywords, structure and hook suggestions on the free plan."}
          </p>
        </div>
      </div>
      <Link href="/pricing">
        <Button variant="secondary" size="sm" type="button">
          See plans
        </Button>
      </Link>
    </div>
  );
}
