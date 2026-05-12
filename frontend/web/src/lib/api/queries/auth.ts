/**
 * Hooks de TanStack Query para auth (login).
 */

import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { useAuthStore } from "@/lib/auth/store";
import { useBrandStore } from "@/lib/branding/store";
import type { components } from "@/lib/api/schema";

type LoginRequest = components["schemas"]["LoginRequest"];
type LoginResponse = components["schemas"]["LoginResponse"];

export function useLogin() {
  return useMutation({
    mutationFn: (creds: LoginRequest) =>
      api.post<LoginResponse>("/auth/login", creds, { skipAuth: true }),
    onSuccess: (data) => {
      useAuthStore.getState().login({
        token: data.access_token,
        user: {
          id: data.user.id,
          username: data.user.username,
          role: data.user.role ?? null,
          lavanderiaId: data.user.lavanderia_id,
          lavanderiaName: data.user.lavanderia_name ?? null,
        },
        permissions: data.permissions,
        expiresAt: data.expires_at ?? null,
      });

      // Aplicar branding del tenant (logo + colores). Si los campos vienen
      // null, el store los ignora y se mantienen los defaults Mukusoft.
      const t = data.tenant;
      useBrandStore.getState().setBrand({
        logoUrl: t.logo_url ?? null,
        logoUrlDark: t.logo_url_dark ?? null,
        colorPrimary: t.color_primario ?? null,
        colorSecondary: t.color_secundario ?? null,
        showMukusoft: t.mostrar_marca_mukusoft,
      });
    },
  });
}
