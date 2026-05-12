/**
 * Helpers de formato para Carwash.
 * Montos en guaraníes (sin decimales), fechas en es-PY.
 */

import { format, parseISO } from "date-fns";
import { es } from "date-fns/locale";

/**
 * Formatea un número como guaraníes.
 *   formatMoney(50000)       -> "Gs. 50.000"
 *   formatMoney(-650000)     -> "-Gs. 650.000"
 *   formatMoney(null)        -> "—"
 */
export function formatMoney(value: number | null | undefined, opts?: { withSymbol?: boolean }) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const n = Math.round(value);
  const sign = n < 0 ? "-" : "";
  const formatted = Math.abs(n).toLocaleString("es-PY");
  if (opts?.withSymbol === false) return `${sign}${formatted}`;
  return `${sign}Gs. ${formatted}`;
}

/**
 * Formatea una fecha ISO al formato dd/MM/yyyy.
 */
export function formatDate(iso: string | null | undefined) {
  if (!iso) return "—";
  try {
    return format(parseISO(iso), "dd/MM/yyyy", { locale: es });
  } catch {
    return iso;
  }
}

/**
 * Formato largo: "06 de mayo de 2026"
 */
export function formatDateLong(iso: string | null | undefined) {
  if (!iso) return "—";
  try {
    return format(parseISO(iso), "dd 'de' MMMM 'de' yyyy", { locale: es });
  } catch {
    return iso;
  }
}

/**
 * Devuelve la fecha de hoy en ISO (yyyy-MM-dd) — útil para query params.
 */
export function todayISO() {
  const d = new Date();
  return format(d, "yyyy-MM-dd");
}

/**
 * Primer día del mes actual en ISO.
 */
export function firstDayOfMonthISO() {
  const d = new Date();
  d.setDate(1);
  return format(d, "yyyy-MM-dd");
}
