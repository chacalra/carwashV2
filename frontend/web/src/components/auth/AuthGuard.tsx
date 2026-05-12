/**
 * AuthGuard — protege páginas privadas.
 * Si no hay sesión válida, redirige a /login.
 * Mientras el store hidrata, renderiza un placeholder.
 */

import type { ReactNode } from "react";
import { useEffect } from "react";
import { useAuthStore } from "@/lib/auth/store";

export function AuthGuard({ children }: { children: ReactNode }) {
  const hydrated = useAuthStore((s) => s.hydrated);
  const token = useAuthStore((s) => s.token);
  const expiresAt = useAuthStore((s) => s.expiresAt);

  const isAuthed = (() => {
    if (!token) return false;
    if (expiresAt) {
      const exp = new Date(expiresAt).getTime();
      if (!Number.isNaN(exp) && exp <= Date.now()) return false;
    }
    return true;
  })();

  useEffect(() => {
    if (hydrated && !isAuthed && typeof window !== "undefined") {
      window.location.href = "/login";
    }
  }, [hydrated, isAuthed]);

  if (!hydrated) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-text-tertiary">
        Cargando…
      </div>
    );
  }

  if (!isAuthed) return null;

  return <>{children}</>;
}
