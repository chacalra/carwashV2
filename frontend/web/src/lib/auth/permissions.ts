/**
 * Permisos disponibles en el backend (ver docs/FRONTEND_GUIDE.md §3).
 */
export type Permission =
  | "dashboard"
  | "register_sale"
  | "edit_sale"
  | "manage_sales"
  | "register_expense"
  | "movements"
  | "export"
  | "settings";

import { useAuthStore } from "@/lib/auth/store";

/** Hook reactivo: re-renderiza si cambian los permisos del usuario. */
export function usePermission(perm: Permission): boolean {
  return useAuthStore((s) => s.permissions.includes(perm));
}
