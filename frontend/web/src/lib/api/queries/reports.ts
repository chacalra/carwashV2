/**
 * Queries para reportes.
 */

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type SalesSummaryResponse = components["schemas"]["SalesSummaryResponse"];
type DailySalesItem = components["schemas"]["DailySalesItem"];
type CustomerSummaryResponse = components["schemas"]["CustomerSummaryResponse"];
type ProductSummaryResponse = components["schemas"]["ProductSummaryResponse"];

export function useSalesSummary(start: string, end: string) {
  return useQuery({
    queryKey: ["reports", "sales-summary", start, end],
    queryFn: () =>
      api.get<SalesSummaryResponse>(
        `/reports/sales-summary?start_date=${start}&end_date=${end}`,
      ),
    enabled: Boolean(start && end),
  });
}

export function useDailySales(start: string, end: string) {
  return useQuery({
    queryKey: ["reports", "daily-sales", start, end],
    queryFn: () =>
      api.get<DailySalesItem[]>(
        `/reports/daily-sales?start_date=${start}&end_date=${end}`,
      ),
    enabled: Boolean(start && end),
  });
}

export function useCustomerSummary(start: string, end: string) {
  return useQuery({
    queryKey: ["reports", "customer-summary", start, end],
    queryFn: () =>
      api.get<CustomerSummaryResponse>(
        `/reports/customer-summary?start_date=${start}&end_date=${end}`,
      ),
    enabled: Boolean(start && end),
  });
}

export function useProductSummary(start: string, end: string) {
  return useQuery({
    queryKey: ["reports", "product-summary", start, end],
    queryFn: () =>
      api.get<ProductSummaryResponse>(
        `/reports/product-summary?start_date=${start}&end_date=${end}`,
      ),
    enabled: Boolean(start && end),
  });
}
