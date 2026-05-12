/**
 * Queries y mutations de usuarios.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type UserListItem = components["schemas"]["UserListItem"];
type UserCreateRequest = components["schemas"]["UserCreateRequest"];
type UserUpdateRequest = components["schemas"]["UserUpdateRequest"];
type CreatedResponse = components["schemas"]["CreatedResponse"];

export function useUsers() {
  return useQuery({
    queryKey: ["users"],
    queryFn: () => api.get<UserListItem[]>("/users"),
    staleTime: 30_000,
  });
}

export function useCreateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: UserCreateRequest) =>
      api.post<CreatedResponse>("/users", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });
}

export function useUpdateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: UserUpdateRequest }) =>
      api.put(`/users/${id}`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });
}

export function useToggleUserStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.patch(`/users/${id}/status`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });
}

export function useResetUserPassword() {
  return useMutation({
    mutationFn: ({ id, password }: { id: number; password: string }) =>
      api.patch(`/users/${id}/password`, { password }),
  });
}
