import { describe, expect, it } from "vitest";
import { enhanceSchema, generateSchema, loginSchema, signupSchema } from "@/lib/schemas";

const validGenerate = {
  category: "achievement",
  topic: "Machine Learning",
  event: "Completed my first end-to-end machine learning project",
  field: "AI/ML",
  tone: "proud",
  emotion: "happy",
  audience: "students and developers",
  length: "medium" as const,
  cta: "question" as const,
  keywords: ["machine learning"],
  context: "",
  variations: 1,
};

describe("generateSchema", () => {
  it("accepts a complete, valid request", () => {
    expect(generateSchema.safeParse(validGenerate).success).toBe(true);
  });

  it("requires a topic and an event with friendly messages", () => {
    const result = generateSchema.safeParse({ ...validGenerate, topic: " ", event: "ok" });
    expect(result.success).toBe(false);
    if (!result.success) {
      const messages = result.error.issues.map((i) => i.message);
      expect(messages.some((m) => m.includes("Topic"))).toBe(true);
      expect(messages.some((m) => m.includes("Achievement or event"))).toBe(true);
    }
  });

  it("trims whitespace from text fields", () => {
    const parsed = generateSchema.parse({ ...validGenerate, topic: "  AI  " });
    expect(parsed.topic).toBe("AI");
  });

  it("limits keywords to 10", () => {
    const keywords = Array.from({ length: 11 }, (_, i) => `kw${i}`);
    expect(generateSchema.safeParse({ ...validGenerate, keywords }).success).toBe(false);
  });

  it("rejects unknown length values", () => {
    expect(generateSchema.safeParse({ ...validGenerate, length: "epic" }).success).toBe(false);
  });
});

describe("enhanceSchema", () => {
  it("requires at least 30 characters", () => {
    expect(enhanceSchema.safeParse({ text: "too short", cta: "question", keywords: [] }).success).toBe(false);
  });

  it("accepts a realistic draft", () => {
    const text = "I shipped my first API this week and learned a lot about testing.";
    expect(enhanceSchema.safeParse({ text, cta: "question", keywords: [] }).success).toBe(true);
  });
});

describe("auth schemas", () => {
  it("rejects invalid email and short passwords on signup", () => {
    expect(signupSchema.safeParse({ email: "not-an-email", password: "longenough" }).success).toBe(false);
    expect(signupSchema.safeParse({ email: "a@b.co", password: "short" }).success).toBe(false);
  });

  it("requires a password on login", () => {
    expect(loginSchema.safeParse({ email: "a@b.co", password: "" }).success).toBe(false);
  });
});
