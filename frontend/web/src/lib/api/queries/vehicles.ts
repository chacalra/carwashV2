/**
 * Queries de vehículos. Lookup por placa + upsert (find_or_create).
 */

import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type VehicleResponse = components["schemas"]["VehicleResponse"];
type VehicleCreateRequest = components["schemas"]["VehicleCreateRequest"];
type CreatedResponse = components["schemas"]["CreatedResponse"];

export async function findVehicleByPlate(plate: string): Promise<VehicleResponse | null> {
  return api.get<VehicleResponse | null>(
    `/vehicles/by-plate/${encodeURIComponent(plate)}`,
  );
}

export function useUpsertVehicle() {
  return useMutation({
    mutationFn: (payload: VehicleCreateRequest) =>
      api.post<CreatedResponse>("/vehicles", payload),
  });
}
