/**
 * Mutaciones para ventas. Crea, edita, anula.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type SaleCreateRequest = components["schemas"]["SaleCreateRequest"];
type CreatedResponse = components["schemas"]["CreatedResponse"];
type SaleResponse = components["schemas"]["SaleResponse"];
type MessageResponse = components["schemas"]["MessageResponse"];

export function useSale(id: number | null) {
  return useQuery({
    queryKey: ["sales", "detail", id],
    queryFn: () => api.get<SaleResponse>(`/sales/${id}`),
    enabled: id !== null && Number.isFinite(id),
    staleTime: 0,
  });
}

export function useUpdateSale(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: SaleCreateRequest) =>
      api.put<SaleResponse>(`/sales/${id}`, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sales"] });
      qc.invalidateQueries({ queryKey: ["reports"] });
    },
  });
}

export function useSalesGrouped(start: string, end: string) {
  return useQuery({
    queryKey: ["sales", "grouped", start, end],
    queryFn: () =>
      api.get<SaleResponse[]>(
        `/sales/grouped?start_date=${start}&end_date=${end}`,
      ),
    enabled: Boolean(start && end),
  });
}

export function useVoidSale() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete<MessageResponse>(`/sales/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sales"] });
      qc.invalidateQueries({ queryKey: ["reports"] });
    },
  });
}

export function useCreateSale() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: SaleCreateRequest) =>
      api.post<CreatedResponse>("/sales", payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["reports"] });
      qc.invalidateQueries({ queryKey: ["sales"] });
    },
  });
}
