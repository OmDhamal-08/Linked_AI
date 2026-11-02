import Link from "next/link";
import { Sparkles } from "lucide-react";
import { APP_NAME } from "@/lib/config";

export function PublicHeader() {
  return (
    <header className="sticky top-0 z-10 border-b border-ink-100 bg-white/85 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">
            <Sparkles className="h-4 w-4" aria-hidden="true" />
          </span>
          <span className="font-semibold text-ink-900">{APP_NAME}</span>
        </Link>
        <nav aria-label="Public" className="flex items-center gap-1 text-sm">
          <Link href="/pricing" className="rounded-md px-3 py-2 text-ink-600 hover:bg-ink-100 hover:text-ink-900">
            Pricing
          </Link>
          <Link href="/about" className="rounded-md px-3 py-2 text-ink-600 hover:bg-ink-100 hover:text-ink-900">
            About
          </Link>
          <Link href="/login" className="rounded-md px-3 py-2 text-ink-600 hover:bg-ink-100 hover:text-ink-900">
            Log in
          </Link>
          <Link href="/signup" className="ml-1 rounded-lg bg-brand-600 px-4 py-2 font-medium text-white hover:bg-brand-700">
            Get started
          </Link>
        </nav>
      </div>
    </header>
  );
}
