/**
 * Wrapper que tiene que envolver todas las islas React con estado/queries.
 * Pasa por aquí: QueryClientProvider + sonner Toaster.
 */

import { QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { GlobalErrorBoundary } from "@/components/ErrorBoundary";
import { Toaster } from "@/components/ui/sonner";
import { queryClient } from "@/lib/api/query-client";

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <GlobalErrorBoundary>{children}</GlobalErrorBoundary>
      <Toaster
        richColors
        position="top-right"
        toastOptions={{
          // Borde lateral por tipo (alineado al DS).
          classNames: {
            toast: "border-l-[3px] border-l-border-default",
            success: "!border-l-pos",
            error: "!border-l-neg",
            warning: "!border-l-warn",
            info: "!border-l-accent",
          },
        }}
      />
    </QueryClientProvider>
  );
}
