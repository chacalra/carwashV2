import { QueryClient } from "@tanstack/react-query";

/** Singleton compartido entre islas React (todas las islas comparten cache). */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 0,
    },
  },
});
