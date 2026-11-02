import Link from "next/link";
import { Lock } from "lucide-react";
import { Button } from "@/components/ui/button";

export function UpgradeBanner({ message }: { message?: string | null }) {
  return (
    <div className="flex flex-col gap-3 rounded-xl border border-amber-200 bg-amber-50 p-5 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-start gap-3">
        <Lock className="mt-0.5 h-4 w-4 shrink-0 text-amber-700" aria-hidden="true" />
        <div>
          <p className="text-sm font-semibold text-amber-900">Full post is a Premium feature</p>
          <p className="text-sm text-amber-800">
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
