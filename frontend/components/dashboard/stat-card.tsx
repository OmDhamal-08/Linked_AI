import type { ReactNode } from "react";
import { Card, CardContent } from "@/components/ui/card";

export function StatCard({ label, value, hint, icon }: { label: string; value: ReactNode; hint?: string; icon?: ReactNode }) {
  return (
    <Card>
      <CardContent className="flex items-start justify-between gap-4 pt-5">
        <div className="flex flex-col gap-1">
          <p className="text-xs font-medium uppercase tracking-wide text-ink-500">{label}</p>
          <p className="text-2xl font-semibold text-ink-900">{value}</p>
          {hint ? <p className="text-xs text-ink-500">{hint}</p> : null}
        </div>
        {icon ? <div className="rounded-lg bg-brand-50 p-2 text-brand-700">{icon}</div> : null}
      </CardContent>
    </Card>
  );
}
