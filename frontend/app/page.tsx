import Link from "next/link";
import { CheckCircle2, Gauge, LineChart, ListChecks, ShieldCheck, Sparkles } from "lucide-react";
import { PublicHeader } from "@/components/layout/public-header";
import { Button } from "@/components/ui/button";
import { APP_NAME } from "@/lib/config";

const FEATURES = [
  {
    icon: Sparkles,
    title: "Generate with structure",
    body: "Answer a few structured questions. We recommend a hook, flow and call to action that fit your topic and audience.",
  },
  {
    icon: ListChecks,
    title: "Enhance what you wrote",
    body: "Paste a draft to see what is weak: the opening line, missing terms, clarity and the call to action.",
  },
  {
    icon: Gauge,
    title: "Quality, not promises",
    body: "A transparent AI content quality score for clarity, structure and tone. It is guidance, never a reach prediction.",
  },
  {
    icon: LineChart,
    title: "Track your progress",
    body: "Your history and quality trends show what improves over time, so you can see what works for your writing.",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      <PublicHeader />
      <main id="main">
        <section className="mx-auto max-w-6xl px-4 pb-20 pt-20 text-center sm:px-6">
          <p className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-800 ring-1 ring-brand-200">
            <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
            Original posts. Your facts only.
          </p>
          <h1 className="mx-auto max-w-3xl text-4xl font-semibold tracking-tight text-ink-900 sm:text-5xl">
            Write LinkedIn posts that are clear, relevant and easy to read.
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-ink-600">
            {APP_NAME} is AI-powered LinkedIn content optimization. It helps students and professionals turn real achievements into
            well-structured posts. It does not promise viral reach.
          </p>
          <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link href="/signup">
              <Button size="lg">Start free</Button>
            </Link>
            <Link href="/enhance">
              <Button size="lg" variant="secondary">
                Improve an existing draft
              </Button>
            </Link>
          </div>
          <ul className="mx-auto mt-8 flex max-w-xl flex-wrap justify-center gap-x-6 gap-y-2 text-sm text-ink-500">
            <li className="flex items-center gap-1.5">
              <CheckCircle2 className="h-4 w-4 text-brand-600" aria-hidden="true" />
              No credit card needed
            </li>
            <li className="flex items-center gap-1.5">
              <CheckCircle2 className="h-4 w-4 text-brand-600" aria-hidden="true" />
              Free analysis every day
            </li>
          </ul>
        </section>

        <section aria-labelledby="features" className="border-t border-ink-100 bg-ink-50/60 py-20">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <h2 id="features" className="text-center text-2xl font-semibold text-ink-900">
              Built for careful, credible writing
            </h2>
            <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {FEATURES.map(({ icon: Icon, title, body }) => (
                <div key={title} className="rounded-xl border border-ink-100 bg-white p-6 shadow-card">
                  <Icon className="h-5 w-5 text-brand-700" aria-hidden="true" />
                  <h3 className="mt-4 text-base font-semibold text-ink-900">{title}</h3>
                  <p className="mt-2 text-sm leading-6 text-ink-600">{body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section aria-labelledby="principles" className="mx-auto max-w-3xl px-4 py-20 sm:px-6">
          <h2 id="principles" className="text-2xl font-semibold text-ink-900">
            Our principles
          </h2>
          <ul className="mt-6 flex flex-col gap-4 text-ink-700">
            <li>We never invent achievements, numbers, companies or credentials. Only your facts appear in your post.</li>
            <li>We do not copy other creators. Patterns are learned from licensed or permitted data, and posts are written from scratch.</li>
            <li>Quality scores describe clarity and structure. They are not predictions of LinkedIn reach.</li>
          </ul>
        </section>
      </main>
      <footer className="border-t border-ink-100 py-8 text-center text-xs text-ink-500">
        © {new Date().getFullYear()} {APP_NAME}. All rights reserved.
      </footer>
    </div>
  );
}
