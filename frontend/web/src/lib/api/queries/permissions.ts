/**
 * Queries de permisos del sistema (catálogo, solo lectura).
 */

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type PermissionItem = components["schemas"]["PermissionItem"];

export function usePermissions() {
  return useQuery({
    queryKey: ["permissions"],
    queryFn: () => api.get<PermissionItem[]>("/permissions"),
    staleTime: 5 * 60_000,
  });
}
