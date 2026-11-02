"use client";

import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { SelectField, TextAreaField, TextField } from "@/components/ui/field";
import { TagInput } from "@/components/forms/tag-input";
import { type GenerateFormValues, type GeneratePayload, generateSchema } from "@/lib/schemas";
import { titleCase } from "@/lib/utils";
import type { Taxonomy } from "@/types/api";

interface Props {
  taxonomy: Taxonomy;
  isPremium: boolean;
  submitting: boolean;
  onSubmit: (payload: GeneratePayload) => void;
}

const LENGTH_LABELS: Record<string, string> = { short: "Short", medium: "Medium", long: "Long" };
const CTA_LABELS: Record<string, string> = {
  question: "Question",
  invite_comments: "Invite comments",
  share: "Invite shares",
  follow: "Invite follows",
  none: "None",
};

/** Generate-post form. Validation mirrors the backend; the page owns the API call. */
export function GenerateForm({ taxonomy, isPremium, submitting, onSubmit }: Props) {
  const form = useForm<GenerateFormValues, unknown, GeneratePayload>({
    resolver: zodResolver(generateSchema),
    defaultValues: {
      category: "achievement",
      topic: "",
      event: "",
      field: "",
      tone: "professional",
      emotion: "neutral",
      audience: "students and professionals",
      length: "medium",
      cta: "question",
      keywords: [],
      context: "",
      variations: 1,
    },
    mode: "onTouched",
  });
  const { register, handleSubmit, control, formState } = form;
  const { errors } = formState;

  return (
    <form noValidate onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5" aria-label="Generate a LinkedIn post">
      <div className="grid gap-5 sm:grid-cols-2">
        <SelectField
          label="Post type"
          error={errors.category?.message}
          options={taxonomy.post_types.map((v) => ({ value: v, label: titleCase(v) }))}
          {...register("category")}
        />
        <SelectField
          label="Length"
          error={errors.length?.message}
          options={taxonomy.lengths.map((v) => ({ value: v, label: LENGTH_LABELS[v] ?? titleCase(v) }))}
          {...register("length")}
        />
      </div>

      <TextField label="Topic" placeholder="e.g. Machine Learning" error={errors.topic?.message} {...register("topic")} />

      <TextAreaField
        label="Achievement or event"
        placeholder="Describe what happened in one or two sentences."
        hint="Only include facts you are comfortable publishing. The post will not invent details."
        error={errors.event?.message}
        {...register("event")}
      />

      <div className="grid gap-5 sm:grid-cols-2">
        <TextField label="Field (optional)" placeholder="e.g. AI/ML" error={errors.field?.message} {...register("field")} />
        <TextField label="Audience" error={errors.audience?.message} {...register("audience")} />
      </div>

      <div className="grid gap-5 sm:grid-cols-3">
        <SelectField
          label="Tone"
          error={errors.tone?.message}
          options={taxonomy.tones.map((v) => ({ value: v, label: titleCase(v) }))}
          {...register("tone")}
        />
        <SelectField
          label="Emotion"
          error={errors.emotion?.message}
          options={taxonomy.emotions.map((v) => ({ value: v, label: titleCase(v) }))}
          {...register("emotion")}
        />
        <SelectField
          label="Call to action"
          error={errors.cta?.message}
          options={taxonomy.cta_types.map((v) => ({ value: v, label: CTA_LABELS[v] ?? titleCase(v) }))}
          {...register("cta")}
        />
      </div>

      <Controller
        control={control}
        name="keywords"
        render={({ field, fieldState }) => (
          <TagInput
            label="Keywords (optional)"
            value={field.value ?? []}
            onChange={field.onChange}
            error={fieldState.error?.message}
            hint="Terms your audience searches for. Up to 10."
          />
        )}
      />

      <TextAreaField
        label="Additional context (optional)"
        placeholder="Anything else the post should reflect. Stay factual."
        error={errors.context?.message}
        {...register("context")}
      />

      <SelectField
        label="Variations"
        hint={isPremium ? "Premium: compare up to three versions." : "Available on Premium."}
        error={errors.variations?.message}
        options={[
          { value: "1", label: "1 version" },
          { value: "2", label: "2 versions", disabled: !isPremium },
          { value: "3", label: "3 versions", disabled: !isPremium },
        ]}
        {...register("variations", { valueAsNumber: true })}
      />

      <div className="flex justify-end">
        <Button type="submit" size="lg" loading={submitting}>
          Generate post
        </Button>
      </div>
    </form>
  );
}
