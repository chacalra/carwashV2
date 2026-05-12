/**
 * Definición declarativa de la nav lateral.
 * Cada item declara qué permiso lo hace visible.
 */

import type { LucideIcon } from "lucide-react";
import {
  BarChart3,
  CircleMinus,
  CirclePlus,
  LayoutDashboard,
  ListChecks,
  Settings,
} from "lucide-react";
import type { Permission } from "@/lib/auth/permissions";

export interface NavItem {
  key: string;
  label: string;
  href: string;
  icon: LucideIcon;
  permission: Permission;
  /** Iteración en la que se construye (para placeholders). */
  iteration: number;
}

export const NAV_ITEMS: NavItem[] = [
  {
    key: "dashboard",
    label: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
    permission: "dashboard",
    iteration: 2,
  },
  {
    key: "sales_form",
    label: "Nueva venta",
    href: "/sales/new",
    icon: CirclePlus,
    permission: "register_sale",
    iteration: 3,
  },
  {
    key: "movements",
    label: "Movimientos",
    href: "/sales",
    icon: ListChecks,
    permission: "movements",
    iteration: 4,
  },
  {
    key: "expense_form",
    label: "Nuevo egreso",
    href: "/expenses/new",
    icon: CircleMinus,
    permission: "register_expense",
    iteration: 6,
  },
  {
    key: "reports",
    label: "Reportes",
    href: "/reports",
    icon: BarChart3,
    permission: "export",
    iteration: 7,
  },
  {
    key: "settings",
    label: "Ajustes",
    href: "/settings",
    icon: Settings,
    permission: "settings",
    iteration: 8,
  },
];

/**
 * Devuelve la primera ruta del nav para la que el usuario tiene permiso.
 * Se usa como redirect post-login: si el operario no tiene `dashboard` no
 * lo mandamos ahí, sino al primer item que sí pueda ver (típicamente
 * `/sales/new`).
 */
export function getDefaultRouteForPermissions(permissions: string[]): string {
  for (const item of NAV_ITEMS) {
    if (permissions.includes(item.permission)) return item.href;
  }
  return "/login";
}
