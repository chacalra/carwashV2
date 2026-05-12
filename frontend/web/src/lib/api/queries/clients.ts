/**
 * Queries de clientes. Lookup por RUC/CI (lazy via fn directa).
 */

import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type ClientResponse = components["schemas"]["ClientResponse"];

export async function findClientByRucCi(rucCi: string): Promise<ClientResponse | null> {
  return api.get<ClientResponse | null>(
    `/clients/by-ruc-ci/${encodeURIComponent(rucCi)}`,
  );
}
