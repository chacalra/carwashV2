/**
 * Queries y mutations de egresos.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type ExpenseCreateRequest = components["schemas"]["ExpenseCreateRequest"];
type CreatedResponse = components["schemas"]["CreatedResponse"];

export function useCreateExpense() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ExpenseCreateRequest) =>
      api.post<CreatedResponse>("/expenses", payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["reports"] });
      qc.invalidateQueries({ queryKey: ["expenses"] });
    },
  });
}
