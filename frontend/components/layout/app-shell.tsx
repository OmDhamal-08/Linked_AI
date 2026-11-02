"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { BarChart3, Clock, LayoutDashboard, PenSquare, Settings, Shield, Sparkles, User as UserIcon, LogOut } from "lucide-react";
import type { ReactNode } from "react";
import { APP_NAME } from "@/lib/config";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/use-auth";
import { Badge } from "@/components/ui/feedback";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/generate", label: "Generate", icon: PenSquare },
  { href: "/enhance", label: "Enhance", icon: Sparkles },
  { href: "/history", label: "History", icon: Clock },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/profile", label: "Profile", icon: UserIcon },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();

  const items = user?.is_admin ? [...NAV, { href: "/admin", label: "Admin", icon: Shield }] : NAV;

  async function handleLogout() {
    await logout();
    router.replace("/login");
  }

  return (
    <div className="min-h-screen bg-ink-50">
      <div className="mx-auto flex max-w-[1400px]">
        <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-ink-100 bg-white px-4 py-6 md:flex">
          <Link href="/dashboard" className="mb-8 flex items-center gap-2 px-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">
              <Sparkles className="h-4 w-4" aria-hidden="true" />
            </span>
            <span className="text-base font-semibold text-ink-900">{APP_NAME}</span>
          </Link>
          <nav aria-label="Main" className="flex flex-1 flex-col gap-1">
            {items.map(({ href, label, icon: Icon }) => {
              const active = pathname === href || pathname.startsWith(`${href}/`);
              return (
                <Link
                  key={href}
                  href={href}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                    active ? "bg-brand-50 text-brand-800" : "text-ink-600 hover:bg-ink-100 hover:text-ink-900",
                  )}
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  {label}
                </Link>
              );
            })}
          </nav>
          <div className="mt-6 border-t border-ink-100 pt-4">
            <div className="mb-3 flex items-center justify-between px-2">
              <p className="truncate text-sm text-ink-600" title={user?.email}>
                {user?.name || user?.email}
              </p>
              <Badge tone={user?.plan === "premium" ? "brand" : "neutral"}>{user?.plan === "premium" ? "Premium" : "Free"}</Badge>
            </div>
            <button
              type="button"
              onClick={handleLogout}
              className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-ink-600 hover:bg-ink-100 hover:text-ink-900"
            >
              <LogOut className="h-4 w-4" aria-hidden="true" />
              Sign out
            </button>
          </div>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <nav aria-label="Main mobile" className="flex gap-1 overflow-x-auto border-b border-ink-100 bg-white px-3 py-2 md:hidden">
            {items.map(({ href, label }) => (
              <Link
                key={href}
                href={href}
                className={cn(
                  "whitespace-nowrap rounded-md px-3 py-1.5 text-sm",
                  pathname.startsWith(href) ? "bg-brand-50 text-brand-800" : "text-ink-600",
                )}
              >
                {label}
              </Link>
            ))}
          </nav>
          <main id="main" className="min-w-0 flex-1 px-4 py-8 sm:px-8">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}
