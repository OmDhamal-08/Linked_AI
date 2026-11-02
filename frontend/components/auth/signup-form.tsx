"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { TextField } from "@/components/ui/field";
import { Alert } from "@/components/ui/feedback";
import { useAuth } from "@/hooks/use-auth";
import { errorMessage } from "@/lib/api";
import { signupSchema } from "@/lib/schemas";

type SignupValues = { name?: string; email: string; password: string };

export function SignupForm() {
  const router = useRouter();
  const { signup } = useAuth();
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<SignupValues>({ resolver: zodResolver(signupSchema), mode: "onTouched" });

  async function onSubmit(values: SignupValues) {
    setServerError(null);
    try {
      await signup(values.email, values.password, values.name);
      router.replace("/dashboard");
    } catch (error) {
      setServerError(errorMessage(error));
    }
  }

  return (
    <form noValidate onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5" aria-label="Create an account">
      {serverError ? <Alert tone="danger">{serverError}</Alert> : null}
      <TextField label="Name (optional)" autoComplete="name" error={errors.name?.message} {...register("name")} />
      <TextField label="Email" type="email" autoComplete="email" error={errors.email?.message} {...register("email")} />
      <TextField
        label="Password"
        type="password"
        autoComplete="new-password"
        hint="At least 8 characters."
        error={errors.password?.message}
        {...register("password")}
      />
      <Button type="submit" size="lg" loading={isSubmitting}>
        Create account
      </Button>
      <p className="text-center text-sm text-ink-600">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-brand-700 hover:underline">
          Log in
        </Link>
      </p>
    </form>
  );
}
