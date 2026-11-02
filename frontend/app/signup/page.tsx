import { Suspense } from "react";
import { SignupForm } from "@/components/auth/signup-form";
import { PublicHeader } from "@/components/layout/public-header";

export default function SignupPage() {
  return (
    <div className="min-h-screen bg-white">
      <PublicHeader />
      <main id="main" className="mx-auto flex max-w-md flex-col px-4 py-16 sm:px-6">
        <h1 className="text-2xl font-semibold text-ink-900">Create your account</h1>
        <p className="mb-8 mt-2 text-sm text-ink-600">Free to start. No credit card needed.</p>
        <Suspense fallback={null}>
          <SignupForm />
        </Suspense>
      </main>
    </div>
  );
}
