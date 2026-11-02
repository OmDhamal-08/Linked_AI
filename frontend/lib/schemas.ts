import { z } from "zod";

/**
 * Form validation schemas. These mirror the backend rules (see app/schemas/posts.py).
 * The backend is the source of truth; these give fast, friendly feedback on the client.
 */

const trimmed = (min: number, max: number, label: string) =>
  z
    .string()
    .trim()
    .min(min, `${label} needs at least ${min} characters.`)
    .max(max, `${label} can be at most ${max} characters.`);

export const generateSchema = z.object({
  category: z.string().min(1, "Choose a post type."),
  topic: trimmed(2, 120, "Topic"),
  event: trimmed(5, 500, "Achievement or event"),
  field: z.string().trim().max(120, "Field can be at most 120 characters.").default(""),
  tone: z.string().min(1, "Choose a tone."),
  emotion: z.string().min(1, "Choose an emotion."),
  audience: trimmed(2, 120, "Audience").default("students and professionals"),
  length: z.enum(["short", "medium", "long"]),
  cta: z.enum(["question", "invite_comments", "share", "follow", "none"]),
  keywords: z.array(z.string().trim().min(1).max(40)).max(10, "Use at most 10 keywords."),
  context: z.string().trim().max(4000, "Additional context can be at most 4000 characters.").default(""),
  variations: z.number().int().min(1).max(3).default(1),
});

export type GenerateFormValues = z.input<typeof generateSchema>;
export type GeneratePayload = z.output<typeof generateSchema>;

export const enhanceSchema = z.object({
  text: z
    .string()
    .trim()
    .min(30, "Paste at least 30 characters of your post.")
    .max(4000, "Posts can be at most 4000 characters."),
  tone: z.string().optional(),
  cta: z.enum(["question", "invite_comments", "share", "follow", "none"]),
  keywords: z.array(z.string().trim().min(1).max(40)).max(10, "Use at most 10 keywords."),
});

export type EnhanceFormValues = z.input<typeof enhanceSchema>;
export type EnhancePayload = z.output<typeof enhanceSchema>;

export const loginSchema = z.object({
  email: z.string().trim().email("Enter a valid email address."),
  password: z.string().min(1, "Enter your password."),
});

export const signupSchema = z.object({
  name: z.string().trim().max(120, "Name can be at most 120 characters.").optional(),
  email: z.string().trim().email("Enter a valid email address."),
  password: z.string().min(8, "Use at least 8 characters for your password.").max(128),
});

export const profileSchema = z.object({
  name: z.string().trim().max(120, "Name can be at most 120 characters.").optional(),
  avatar_url: z
    .string()
    .trim()
    .max(500)
    .refine((v) => v === "" || /^https?:\/\//.test(v), "Use a full http or https link.")
    .optional(),
});
