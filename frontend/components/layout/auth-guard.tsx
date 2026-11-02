"use client";

import { usePathname, useRouter } from "next/navigation";
import { type ReactNode, useEffect } from "react";
import { useAuth } from "@/hooks/use-auth";
import { Spinner } from "@/components/ui/feedback";

/** Protects authenticated routes. Unauthenticated visitors are sent to /login with a return path. */
export function AuthGuard({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !user) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }
  }, [loading, user, router, pathname]);

  if (loading || !user) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center" aria-live="polite">
        <Spinner />
        <span className="sr-only">Checking your session…</span>
      </div>
    );
  }
  return <>{children}</>;
}
