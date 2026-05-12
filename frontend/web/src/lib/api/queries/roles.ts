/**
 * Queries y mutations de roles.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type RoleResponse = components["schemas"]["RoleResponse"];
type CreatedResponse = components["schemas"]["CreatedResponse"];

export function useRoles() {
  return useQuery({
    queryKey: ["roles"],
    queryFn: () => api.get<RoleResponse[]>("/roles"),
    staleTime: 30_000,
  });
}

export function useRolePermissions(roleId: number | null) {
  return useQuery({
    queryKey: ["roles", roleId, "permissions"],
    queryFn: () => api.get<string[]>(`/roles/${roleId}/permissions`),
    enabled: roleId !== null,
  });
}

export function useCreateRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { name: string }) =>
      api.post<CreatedResponse>("/roles", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["roles"] }),
  });
}

export function useRenameRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, name }: { id: number; name: string }) =>
      api.put(`/roles/${id}`, { name }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["roles"] }),
  });
}

export function useToggleRoleStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.patch(`/roles/${id}/status`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["roles"] }),
  });
}

export function useUpdateRolePermissions() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, permissions }: { id: number; permissions: string[] }) =>
      api.put(`/roles/${id}/permissions`, { permissions }),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: ["roles"] });
      qc.invalidateQueries({
        queryKey: ["roles", vars.id, "permissions"],
      });
    },
  });
}
