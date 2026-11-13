/**
 * Charts del dashboard (Recharts).
 *  - TrendChart: barras de ventas diarias en el período.
 *
 * Un solo color (accent: deep teal en light, mint en dark). Los días sin
 * ventas se completan con 0 para que el eje X sea un calendario honesto y
 * no salte de "02-nov" a "06-nov" como si fueran contiguos.
 */

import { addDays, format, isAfter, parseISO } from "date-fns";
import { es } from "date-fns/locale";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatMoney } from "@/lib/format";

interface TrendPoint {
  date: string;
  total: number;
}

function fillDays(data: TrendPoint[], start?: string, end?: string) {
  if (!start || !end) return data;
  const byDate = new Map(data.map((d) => [d.date, d.total]));
  const today = new Date();
  const out: TrendPoint[] = [];
  let cur = parseISO(start);
  const last = parseISO(end);
  // No dibujamos días futuros: el mes en curso termina hoy.
  while (!isAfter(cur, last) && !isAfter(cur, today) && out.length < 400) {
    const key = format(cur, "yyyy-MM-dd");
    out.push({ date: key, total: byDate.get(key) ?? 0 });
    cur = addDays(cur, 1);
  }
  return out.length > 0 ? out : data;
}

function compact(v: number) {
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1).replace(".0", "")}M`;
  if (v >= 1_000) return `${Math.round(v / 1000)}k`;
  return `${v}`;
}

export function TrendChart({
  data,
  start,
  end,
  height = 200,
}: {
  data: TrendPoint[];
  start?: string;
  end?: string;
  height?: number;
}) {
  const formatted = fillDays(data, start, end).map((d) => {
    const date = parseISO(d.date);
    return {
      ...d,
      label: format(date, "d", { locale: es }),
      full: format(date, "EEE d 'de' MMM", { locale: es }),
    };
  });

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={formatted} margin={{ top: 4, right: 0, bottom: 0, left: 0 }} barCategoryGap="20%">
        <CartesianGrid stroke="var(--color-border-subtle)" vertical={false} />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 11, fill: "var(--color-text-tertiary)" }}
          tickLine={false}
          axisLine={{ stroke: "var(--color-border-default)" }}
          interval="preserveStartEnd"
          minTickGap={8}
        />
        <YAxis
          orientation="right"
          width={36}
          tick={{ fontSize: 11, fill: "var(--color-text-tertiary)" }}
          tickLine={false}
          axisLine={false}
          tickCount={4}
          tickFormatter={compact}
        />
        <Tooltip
          cursor={{ fill: "var(--color-bg-sunken)" }}
          contentStyle={{
            borderRadius: 6,
            border: "1px solid var(--color-border-default)",
            background: "var(--color-bg-surface)",
            color: "var(--color-text-primary)",
            fontSize: 12,
            boxShadow: "var(--shadow-sm)",
            padding: "6px 10px",
          }}
          labelFormatter={(_, payload) => payload?.[0]?.payload?.full ?? ""}
          formatter={(v) => [formatMoney(Number(v)), "Ventas"]}
        />
        <Bar dataKey="total" fill="var(--color-accent)" radius={[2, 2, 0, 0]} maxBarSize={28} />
      </BarChart>
    </ResponsiveContainer>
  );
}
