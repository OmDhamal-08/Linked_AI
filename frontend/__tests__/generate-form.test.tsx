import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { GenerateForm } from "@/components/forms/generate-form";
import type { Taxonomy } from "@/types/api";

const taxonomy: Taxonomy = {
  knowledge_categories: ["AI"],
  post_types: ["achievement", "project"],
  tones: ["professional", "proud"],
  emotions: ["neutral", "happy"],
  audiences: ["students"],
  lengths: ["short", "medium", "long"],
  cta_types: ["question", "none"],
};

describe("GenerateForm", () => {
  it("shows validation messages and does not submit an incomplete form", async () => {
    const onSubmit = vi.fn();
    render(<GenerateForm taxonomy={taxonomy} isPremium={false} submitting={false} onSubmit={onSubmit} />);

    await userEvent.click(screen.getByRole("button", { name: /generate post/i }));

    expect(await screen.findByText(/Topic needs at least 2 characters/i)).toBeInTheDocument();
    expect(screen.getByText(/Achievement or event needs at least 5 characters/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits a complete, valid form", async () => {
    const onSubmit = vi.fn();
    render(<GenerateForm taxonomy={taxonomy} isPremium={true} submitting={false} onSubmit={onSubmit} />);

    await userEvent.type(screen.getByLabelText(/^Topic/), "Machine Learning");
    await userEvent.type(screen.getByLabelText(/Achievement or event/i), "Completed my first ML project");
    await userEvent.click(screen.getByRole("button", { name: /generate post/i }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    const payload = onSubmit.mock.calls[0][0];
    expect(payload.topic).toBe("Machine Learning");
    expect(payload.variations).toBe(1);
  });

  it("disables the generate button while submitting", () => {
    render(<GenerateForm taxonomy={taxonomy} isPremium={false} submitting={true} onSubmit={vi.fn()} />);
    expect(screen.getByRole("button", { name: /generate post/i })).toBeDisabled();
  });
});
