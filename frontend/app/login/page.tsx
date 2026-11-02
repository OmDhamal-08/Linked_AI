import { Suspense } from "react";
import { LoginForm } from "@/components/auth/login-form";
import { PublicHeader } from "@/components/layout/public-header";

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-ink-50">
      <PublicHeader />
      <main id="main" className="mx-auto flex max-w-md flex-col px-4 py-16 sm:px-6">
        <h1 className="text-2xl font-semibold text-ink-900">Welcome back</h1>
        <p className="mb-8 mt-2 text-sm text-ink-600">Log in to continue to your dashboard.</p>
        <Suspense fallback={null}>
          <LoginForm />
        </Suspense>
      </main>
    </div>
  );
}
