/**
 * Queries de catálogos (servicios, productos, tipos de vehículo, categorías de egresos).
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type CatalogItem = components["schemas"]["CatalogItem"];
type VehicleTypeItem = components["schemas"]["VehicleTypeItem"];
type ExpenseCategoryItem = components["schemas"]["ExpenseCategoryItem"];
type CatalogMutationRequest = components["schemas"]["CatalogMutationRequest"];
type CreatedResponse = components["schemas"]["CreatedResponse"];

export type CatalogResource =
  | "services"
  | "products"
  | "expense-categories"
  | "vehicle-types";

const RESOURCE_QUERY_KEY: Record<CatalogResource, string> = {
  services: "services",
  products: "products",
  "expense-categories": "expense-categories",
  "vehicle-types": "vehicle-types",
};

export function useCatalogMutations(resource: CatalogResource) {
  const qc = useQueryClient();
  const queryKey = ["catalogs", RESOURCE_QUERY_KEY[resource]];
  const invalidate = () => qc.invalidateQueries({ queryKey });

  const create = useMutation({
    mutationFn: (body: CatalogMutationRequest) =>
      api.post<CreatedResponse>(`/catalogs/${resource}`, body),
    onSuccess: invalidate,
  });

  const update = useMutation({
    mutationFn: ({ id, body }: { id: number; body: CatalogMutationRequest }) =>
      api.put(`/catalogs/${resource}/${id}`, body),
    onSuccess: invalidate,
  });

  const toggle = useMutation({
    mutationFn: (id: number) =>
      api.patch(`/catalogs/${resource}/${id}/status`),
    onSuccess: invalidate,
  });

  const remove = useMutation({
    mutationFn: (id: number) => api.delete(`/catalogs/${resource}/${id}`),
    onSuccess: invalidate,
  });

  return { create, update, toggle, remove };
}

export function useServices(onlyActive = true) {
  return useQuery({
    queryKey: ["catalogs", "services", onlyActive],
    queryFn: () =>
      api.get<CatalogItem[]>(`/catalogs/services?only_active=${onlyActive}`),
    staleTime: 60_000,
  });
}

export function useProducts(onlyActive = true) {
  return useQuery({
    queryKey: ["catalogs", "products", onlyActive],
    queryFn: () =>
      api.get<CatalogItem[]>(`/catalogs/products?only_active=${onlyActive}`),
    staleTime: 60_000,
  });
}

export function useVehicleTypes(onlyActive = true) {
  return useQuery({
    queryKey: ["catalogs", "vehicle-types", onlyActive],
    queryFn: () =>
      api.get<VehicleTypeItem[]>(`/catalogs/vehicle-types?only_active=${onlyActive}`),
    staleTime: 5 * 60_000,
  });
}

export function useExpenseCategories(onlyActive = true) {
  return useQuery({
    queryKey: ["catalogs", "expense-categories", onlyActive],
    queryFn: () =>
      api.get<ExpenseCategoryItem[]>(
        `/catalogs/expense-categories?only_active=${onlyActive}`,
      ),
    staleTime: 60_000,
  });
}
