/**
 * Error boundary global.
 * Captura errores de render en cualquier Island. Para errores de queries,
 * TanStack los expone via `isError` en cada hook (acá no llegan).
 *
 * Fallback con icono, mensaje, "Reintentar" (resetea boundary y queryClient)
 * y "Volver al dashboard". Logging mínimo a consola.
 */

import { AlertTriangle, RefreshCw, Home } from "lucide-react";
import { Component, type ErrorInfo, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";

interface Props {
  children: ReactNode;
  /** Callback opcional al resetear (ej. invalidar queries). */
  onReset?: () => void;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    if (typeof console !== "undefined") {
      console.error("[ErrorBoundary]", error, info.componentStack);
    }
  }

  reset = () => {
    this.setState({ error: null });
    this.props.onReset?.();
  };

  render() {
    if (!this.state.error) return this.props.children;
    return <ErrorFallback error={this.state.error} onReset={this.reset} />;
  }
}

function ErrorFallback({ error, onReset }: { error: Error; onReset: () => void }) {
  return (
    <div className="flex min-h-[60vh] items-center justify-center p-6">
      <div className="w-full max-w-md rounded-xl border border-border-subtle bg-bg-surface p-6 shadow-card text-center animate-fade-in-up">
        <div className="mx-auto inline-flex h-12 w-12 items-center justify-center rounded-full bg-neg-soft text-neg">
          <AlertTriangle size={22} strokeWidth={2.25} />
        </div>
        <h2 className="mt-4 text-base font-semibold tracking-tight">
          Algo no salió como esperábamos
        </h2>
        <p className="mt-2 text-sm text-text-secondary">
          {error.message || "Error inesperado al renderizar la pantalla."}
        </p>
        <div className="mt-5 flex items-center justify-center gap-2">
          <Button type="button" variant="outline" onClick={onReset}>
            <RefreshCw size={14} />
            Reintentar
          </Button>
          <a
            href="/dashboard"
            className="inline-flex h-9 items-center justify-center gap-1.5 rounded-md bg-accent px-4 text-sm font-medium text-white transition hover:bg-accent-hover"
          >
            <Home size={14} />
            Ir al dashboard
          </a>
        </div>
      </div>
    </div>
  );
}

/**
 * Wrapper que conecta el reset del boundary con el queryClient para
 * invalidar todas las queries y forzar refetch al reintentar.
 */
export function GlobalErrorBoundary({ children }: { children: ReactNode }) {
  const qc = useQueryClient();
  return (
    <ErrorBoundary
      onReset={() => {
        qc.resetQueries();
      }}
    >
      {children}
    </ErrorBoundary>
  );
}
