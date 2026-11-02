"use client";

import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { SelectField, TextAreaField } from "@/components/ui/field";
import { TagInput } from "@/components/forms/tag-input";
import { type EnhanceFormValues, type EnhancePayload, enhanceSchema } from "@/lib/schemas";
import { titleCase } from "@/lib/utils";
import type { Taxonomy } from "@/types/api";

interface Props {
  taxonomy: Taxonomy;
  submitting: boolean;
  onSubmit: (payload: EnhancePayload) => void;
  onChange?: (text: string) => void;
}

/** Enhance-post form. The left column of the Enhance page. */
export function EnhanceForm({ taxonomy, submitting, onSubmit, onChange }: Props) {
  const form = useForm<EnhanceFormValues, unknown, EnhancePayload>({
    resolver: zodResolver(enhanceSchema),
    defaultValues: { text: "", tone: "", cta: "question", keywords: [] },
    mode: "onTouched",
  });
  const { register, handleSubmit, control, formState } = form;
  const { errors } = formState;
  const textRegister = register("text");

  return (
    <form noValidate onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5" aria-label="Enhance an existing post">
      <TextAreaField
        label="Your draft"
        placeholder="Paste your LinkedIn draft here."
        className="min-h-[220px]"
        error={errors.text?.message}
        hint="We check clarity, the opening line, structure and keywords."
        {...textRegister}
        onChange={(e) => {
          textRegister.onChange(e);
          onChange?.(e.target.value);
        }}
      />
      <div className="grid gap-5 sm:grid-cols-2">
        <SelectField
          label="Tone (optional)"
          error={errors.tone?.message}
          options={[{ value: "", label: "Keep my tone" }, ...taxonomy.tones.map((v) => ({ value: v, label: titleCase(v) }))]}
          {...register("tone")}
        />
        <SelectField
          label="Call to action"
          error={errors.cta?.message}
          options={taxonomy.cta_types.map((v) => ({ value: v, label: titleCase(v) }))}
          {...register("cta")}
        />
      </div>
      <Controller
        control={control}
        name="keywords"
        render={({ field, fieldState }) => (
          <TagInput label="Keywords to include (optional)" value={field.value ?? []} onChange={field.onChange} error={fieldState.error?.message} />
        )}
      />
      <div className="flex justify-end">
        <Button type="submit" size="lg" loading={submitting}>
          Analyze and improve
        </Button>
      </div>
    </form>
  );
}
