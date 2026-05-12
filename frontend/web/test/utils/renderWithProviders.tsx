/**
 * Helper para tests de componentes que dependen de TanStack Query.
 * Crea un QueryClient nuevo por cada render (sin retries, gcTime infinito en test)
 * para evitar fugas entre tests.
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, type RenderOptions } from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";

export function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: Infinity, staleTime: 0 },
      mutations: { retry: false },
    },
  });
}

export function renderWithProviders(
  ui: ReactElement,
  options?: RenderOptions & { client?: QueryClient },
) {
  const client = options?.client ?? makeQueryClient();
  const Wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return { client, ...render(ui, { wrapper: Wrapper, ...options }) };
}
