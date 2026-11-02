"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { APP_NAME } from "@/lib/config";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/use-auth";

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/generate", label: "Generate" },
  { href: "/enhance", label: "Enhance" },
  { href: "/history", label: "History" },
  { href: "/analytics", label: "Analytics" },
  { href: "/settings", label: "Settings" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();

  const items = user?.is_admin ? [...NAV, { href: "/admin", label: "Admin" }] : NAV;

  async function handleLogout() {
    await logout();
    router.replace("/login");
  }

  return (
    <div className="min-h-screen bg-white">
      <header className="border-b border-ink-200">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-6 px-4 sm:h-14 sm:flex-nowrap sm:px-6">
          <Link href="/dashboard" className="flex-1 shrink-0 py-3 font-semibold text-ink-900 sm:flex-none sm:py-0">
            {APP_NAME}
          </Link>
          <nav aria-label="Main" className="no-scrollbar order-last flex w-full min-w-0 gap-4 overflow-x-auto text-sm sm:order-none sm:w-auto sm:flex-1">
            {items.map(({ href, label }) => {
              const active = pathname === href || pathname.startsWith(`${href}/`);
              return (
                <Link
                  key={href}
                  href={href}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "whitespace-nowrap py-3 sm:py-4",
                    active ? "border-b-2 border-ink-900 font-medium text-ink-900" : "text-ink-500 hover:text-ink-900",
                  )}
                >
                  {label}
                </Link>
              );
            })}
          </nav>
          <div className="flex shrink-0 items-center gap-4 text-sm">
            <Link href="/profile" className="hidden max-w-[160px] truncate text-ink-600 hover:text-ink-900 sm:inline" title={user?.email}>
              {user?.name || user?.email}
              {user?.plan === "premium" ? <span className="ml-1 text-ink-400">(Premium)</span> : null}
            </Link>
            <button type="button" onClick={handleLogout} className="text-ink-500 hover:text-ink-900">
              Sign out
            </button>
          </div>
        </div>
      </header>
      <main id="main" className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
        {children}
      </main>
    </div>
  );
}
