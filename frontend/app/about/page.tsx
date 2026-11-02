import type { Metadata } from "next";
import { PublicHeader } from "@/components/layout/public-header";
import { APP_NAME } from "@/lib/config";

export const metadata: Metadata = { title: "About" };

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-white">
      <PublicHeader />
      <main id="main" className="mx-auto max-w-2xl px-4 py-12 sm:px-6">
        <h1 className="text-2xl font-semibold text-ink-900">About</h1>
        <div className="mt-6 flex flex-col gap-4 leading-7 text-ink-700">
          <p>
            {APP_NAME} is a small tool for writing LinkedIn posts about things you&apos;ve actually done. You give it the facts, it
            suggests a structure, an opening line, relevant keywords and a closing question. You edit the result.
          </p>
          <p>
            Before writing, it looks up similar examples in a knowledge base and uses their patterns (how they open, how they&apos;re
            structured, which terms they use) as guidance. It stores those patterns, not the original posts.
          </p>
          <p>
            It won&apos;t add achievements, numbers or companies you didn&apos;t mention. The score you see is a rough measure of
            readability and structure, not a prediction of how many people will see the post.
          </p>
          <p>Your posts are yours: you can edit or delete any of them from your history.</p>
        </div>
      </main>
    </div>
  );
}
