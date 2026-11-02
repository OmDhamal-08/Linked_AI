"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TextField } from "@/components/ui/field";
import { Alert, Badge } from "@/components/ui/feedback";
import { useAuth } from "@/hooks/use-auth";
import { apiFetch, errorMessage } from "@/lib/api";
import { profileSchema } from "@/lib/schemas";
import type { User } from "@/types/api";

type ProfileValues = { name?: string; avatar_url?: string };

export default function ProfilePage() {
  const { user, refresh } = useAuth();
  const [status, setStatus] = useState<{ tone: "success" | "danger"; message: string } | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting, isDirty },
  } = useForm<ProfileValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: { name: user?.name ?? "", avatar_url: user?.avatar_url ?? "" },
  });

  async function onSubmit(values: ProfileValues) {
    setStatus(null);
    try {
      await apiFetch<User>("/auth/profile", {
        method: "POST",
        json: { name: values.name?.trim() ?? "", avatar_url: values.avatar_url?.trim() ?? "" },
      });
      await refresh();
      setStatus({ tone: "success", message: "Profile saved." });
    } catch (error) {
      setStatus({ tone: "danger", message: errorMessage(error) });
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold text-ink-900">Profile</h1>
        <p className="mt-1 text-sm text-ink-600">How your name appears across Linkdine AI.</p>
      </header>

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>Account</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-6">
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <span className="text-ink-600">Signed in as</span>
            <span className="font-medium text-ink-900">{user?.email}</span>
            <Badge tone={user?.plan === "premium" ? "brand" : "neutral"}>{user?.plan === "premium" ? "Premium" : "Free"}</Badge>
          </div>

          <form noValidate onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5" aria-label="Edit profile">
            {status ? <Alert tone={status.tone === "success" ? "success" : "danger"}>{status.message}</Alert> : null}
            <TextField label="Display name" autoComplete="name" error={errors.name?.message} {...register("name")} />
            <TextField
              label="Avatar URL (optional)"
              placeholder="https://"
              error={errors.avatar_url?.message}
              {...register("avatar_url")}
            />
            <div className="flex justify-end">
              <Button type="submit" loading={isSubmitting} disabled={!isDirty}>
                Save profile
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
