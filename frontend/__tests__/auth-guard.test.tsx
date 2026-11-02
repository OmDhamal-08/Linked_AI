import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { AuthGuard } from "@/components/layout/auth-guard";

const replace = vi.fn();
let authState: { user: unknown; loading: boolean } = { user: null, loading: false };

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
  usePathname: () => "/generate",
}));

vi.mock("@/hooks/use-auth", () => ({
  useAuth: () => authState,
}));

describe("AuthGuard (protected routes)", () => {
  it("redirects anonymous visitors to login with a return path", async () => {
    authState = { user: null, loading: false };
    render(
      <AuthGuard>
        <p>Secret</p>
      </AuthGuard>,
    );
    await waitFor(() => expect(replace).toHaveBeenCalledWith("/login?next=%2Fgenerate"));
    expect(screen.queryByText("Secret")).not.toBeInTheDocument();
  });

  it("shows a loading state while the session is being checked", () => {
    replace.mockClear();
    authState = { user: null, loading: true };
    render(
      <AuthGuard>
        <p>Secret</p>
      </AuthGuard>,
    );
    expect(screen.getByText(/Checking your session/i)).toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });

  it("renders protected content for a logged-in user", () => {
    authState = { user: { id: "1", email: "a@b.co" }, loading: false };
    render(
      <AuthGuard>
        <p>Secret</p>
      </AuthGuard>,
    );
    expect(screen.getByText("Secret")).toBeInTheDocument();
  });
});
