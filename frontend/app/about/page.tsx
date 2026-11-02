import type { Metadata } from "next";
import { PublicHeader } from "@/components/layout/public-header";

export const metadata: Metadata = { title: "About" };

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-white">
      <PublicHeader />
      <main id="main" className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
        <h1 className="text-3xl font-semibold text-ink-900">About Linkdine AI</h1>
        <div className="prose-like mt-6 flex flex-col gap-5 text-ink-700 leading-7">
          <p>
            Linkdine AI helps professionals and students share their work clearly. You describe an achievement or paste a draft, and
            we suggest a structure, an opening line, relevant terms and a call to action. You stay in control of every fact.
          </p>
          <h2 className="pt-4 text-xl font-semibold text-ink-900">What we optimise for</h2>
          <p>Relevance to your topic, clarity, readability, a strong opening line, natural keywords, a meaningful call to action and a tone that fits your audience.</p>
          <h2 className="pt-4 text-xl font-semibold text-ink-900">What we do not do</h2>
          <p>
            We do not guarantee viral reach or engagement, and no keyword is promised to boost visibility. We do not scrape LinkedIn and we do not
            copy posts. The knowledge base stores derived patterns and embeddings, not third-party text.
          </p>
          <h2 className="pt-4 text-xl font-semibold text-ink-900">Your data</h2>
          <p>
            Your posts belong to you. You can edit, copy or delete them at any time from your history. Personal details such as email addresses
            are removed from any dataset before it is used.
          </p>
        </div>
      </main>
    </div>
  );
}
