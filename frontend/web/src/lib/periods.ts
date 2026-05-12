/**
 * Helpers de período para el dashboard.
 * Espeja el comportamiento del legacy: Hoy / Semana (lun-hoy) / Mes / Personalizado.
 */

import { format } from "date-fns";

export type PeriodKey = "today" | "week" | "month" | "custom";

export interface PeriodRange {
  start: string; // yyyy-MM-dd
  end: string;
}

function iso(d: Date): string {
  return format(d, "yyyy-MM-dd");
}

function startOfWeekMonday(d: Date): Date {
  const out = new Date(d);
  const day = out.getDay(); // 0=Sun, 1=Mon, ...
  const diff = (day + 6) % 7; // distancia al lunes
  out.setDate(out.getDate() - diff);
  out.setHours(0, 0, 0, 0);
  return out;
}

function startOfMonth(d: Date): Date {
  const out = new Date(d.getFullYear(), d.getMonth(), 1);
  return out;
}

/**
 * Devuelve el rango asociado al período seleccionado.
 * Para "custom" devuelve los valores actuales pasados (o el mes actual por default).
 */
export function getPeriodRange(
  period: PeriodKey,
  custom?: { start: string; end: string },
): PeriodRange {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  if (period === "today") {
    return { start: iso(today), end: iso(today) };
  }
  if (period === "week") {
    return { start: iso(startOfWeekMonday(today)), end: iso(today) };
  }
  if (period === "month") {
    return { start: iso(startOfMonth(today)), end: iso(today) };
  }
  // custom
  return {
    start: custom?.start ?? iso(startOfMonth(today)),
    end: custom?.end ?? iso(today),
  };
}

/**
 * Devuelve el rango anterior equivalente al actual (para deltas).
 * Misma cantidad de días, terminando un día antes del start actual.
 */
export function previousRange(range: PeriodRange): PeriodRange {
  const start = new Date(`${range.start}T00:00:00`);
  const end = new Date(`${range.end}T00:00:00`);
  const days = Math.round((end.getTime() - start.getTime()) / 86_400_000) + 1;

  const prevEnd = new Date(start);
  prevEnd.setDate(prevEnd.getDate() - 1);
  const prevStart = new Date(prevEnd);
  prevStart.setDate(prevStart.getDate() - (days - 1));

  return { start: iso(prevStart), end: iso(prevEnd) };
}

export const PERIOD_LABELS: Record<PeriodKey, string> = {
  today: "Hoy",
  week: "Esta semana",
  month: "Este mes",
  custom: "Personalizado",
};
