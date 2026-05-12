/**
 * Página placeholder para rutas que se construyen en iteraciones futuras.
 * Renderiza dentro del Shell, así la nav y el header funcionan normal.
 */

import { Construction } from "lucide-react";
import { Shell } from "@/components/shell/Shell";
import { cn } from "@/lib/utils";

interface PendingPageProps {
  activeKey: string;
  title: string;
  subtitle?: string;
  iteration: number;
}

export function PendingPage({ activeKey, title, subtitle, iteration }: PendingPageProps) {
  return (
    <Shell activeKey={activeKey} title={title} subtitle={subtitle}>
      <article
        className={cn(
          "animate-fade-in-up overflow-hidden rounded-2xl",
          "border border-border-subtle bg-bg-surface",
          "shadow-card",
        )}
      >
        <div
          aria-hidden
          className="h-1 bg-gradient-to-r from-brand-deep via-brand-mint to-brand-sky"
        />

        <div className="flex flex-col items-center gap-3 px-8 py-16 text-center">
          <div className="flex size-12 items-center justify-center rounded-xl bg-accent-soft text-accent ring-1 ring-black/5">
            <Construction className="size-6" />
          </div>
          <h2 className="mt-2 text-xl font-semibold tracking-tight">
            Pendiente — Iteración {iteration}
          </h2>
          <p className="max-w-md text-sm text-text-secondary">
            Esta sección se construye en la próxima iteración del plan.
          </p>
          <a
            href="/dashboard"
            className="mt-4 text-sm font-medium text-accent hover:underline"
          >
            ← Volver al dashboard
          </a>
        </div>
      </article>
    </Shell>
  );
}
