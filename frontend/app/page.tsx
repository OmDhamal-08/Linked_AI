import Link from "next/link";
import { PublicHeader } from "@/components/layout/public-header";
import { Button } from "@/components/ui/button";
import { APP_NAME } from "@/lib/config";

const STEPS = [
  {
    title: "Generate",
    body: "Fill in what you did, the tools you used and who you're writing for. You get a draft post built around your facts.",
  },
  {
    title: "Enhance",
    body: "Paste a draft you already wrote. It points out a weak opening, missing keywords, long paragraphs or a missing call to action.",
  },
  {
    title: "Review",
    body: "Each post gets a simple score for the hook, readability, keywords and structure. Edit it, copy it, or keep it in your history.",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      <PublicHeader />
      <main id="main" className="mx-auto max-w-4xl px-4 sm:px-6">
        <section className="py-16">
          <h1 className="max-w-2xl text-3xl font-semibold text-ink-900 sm:text-4xl">Write LinkedIn posts about your work.</h1>
          <p className="mt-4 max-w-xl text-ink-600">
            Describe a project, internship or certification and get a well-structured post, or paste a draft and see what to fix.
          </p>
          <div className="mt-8 flex gap-3">
            <Link href="/signup">
              <Button>Get started</Button>
            </Link>
            <Link href="/login">
              <Button variant="secondary">Log in</Button>
            </Link>
          </div>
        </section>

        <section aria-labelledby="how" className="border-t border-ink-200 py-12">
          <h2 id="how" className="text-sm font-medium text-ink-500">
            How it works
          </h2>
          <ol className="mt-6 grid gap-8 sm:grid-cols-3">
            {STEPS.map(({ title, body }, i) => (
              <li key={title}>
                <p className="font-medium text-ink-900">
                  {i + 1}. {title}
                </p>
                <p className="mt-2 text-sm leading-6 text-ink-600">{body}</p>
              </li>
            ))}
          </ol>
        </section>
      </main>
      <footer className="mx-auto max-w-4xl border-t border-ink-200 px-4 py-6 text-xs text-ink-500 sm:px-6">
        {APP_NAME} · <Link href="/about" className="hover:text-ink-900">About</Link> ·{" "}
        <Link href="/pricing" className="hover:text-ink-900">Pricing</Link>
      </footer>
    </div>
  );
}
