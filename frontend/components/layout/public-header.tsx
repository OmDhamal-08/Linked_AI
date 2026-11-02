import Link from "next/link";
import { APP_NAME } from "@/lib/config";

const LINKS = [
  { href: "/pricing", label: "Pricing" },
  { href: "/about", label: "About" },
  { href: "/login", label: "Log in" },
];

export function PublicHeader() {
  return (
    <header className="border-b border-ink-200 bg-white">
      <div className="mx-auto flex h-14 max-w-4xl items-center justify-between px-4 sm:px-6">
        <Link href="/" className="font-semibold text-ink-900">
          {APP_NAME}
        </Link>
        <nav aria-label="Public" className="flex items-center gap-5 text-sm">
          {LINKS.map(({ href, label }) => (
            <Link key={href} href={href} className={`text-ink-600 hover:text-ink-900 ${href === "/login" ? "" : "hidden sm:inline"}`}>
              {label}
            </Link>
          ))}
          <Link href="/signup" className="rounded-md bg-brand-600 px-3 py-1.5 font-medium text-white hover:bg-brand-700">
            Sign up
          </Link>
        </nav>
      </div>
    </header>
  );
}
