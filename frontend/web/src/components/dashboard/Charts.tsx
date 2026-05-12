/**
 * Charts del dashboard (Recharts).
 *  - TrendChart: barras de ventas diarias en el período.
 *  - DonutChart: distribución (sales o expenses breakdown).
 *
 * Esquema de color Mukusoft (deep / sky / mint / pos / warn).
 */

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatMoney } from "@/lib/format";

// Paleta resuelta vía CSS vars: cambia automáticamente con el tema.
const PALETTE = [
  "var(--color-brand-deep)",
  "var(--color-brand-mint)",
  "var(--color-brand-sky)",
  "var(--color-pos)",
  "var(--color-warn)",
  "var(--color-text-secondary)",
  "var(--color-accent)",
  "var(--color-text-tertiary)",
];

interface TrendPoint {
  date: string;
  total: number;
}

export function TrendChart({ data }: { data: TrendPoint[] }) {
  // Formato corto en eje X: "06 may"
  const formatted = data.map((d) => ({
    ...d,
    label: new Date(`${d.date}T00:00:00`).toLocaleDateString("es-PY", {
      day: "2-digit",
      month: "short",
    }),
  }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart
        data={formatted}
        margin={{ top: 8, right: 8, bottom: 8, left: -10 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" vertical={false} />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 11, fill: "var(--color-text-tertiary)" }}
          tickLine={false}
          axisLine={{ stroke: "var(--color-border-default)" }}
        />
        <YAxis
          tick={{ fontSize: 11, fill: "var(--color-text-tertiary)" }}
          tickLine={false}
          axisLine={{ stroke: "var(--color-border-default)" }}
          tickFormatter={(v: number) =>
            v >= 1_000_000
              ? `${(v / 1_000_000).toFixed(1)}M`
              : v >= 1_000
                ? `${Math.round(v / 1000)}k`
                : `${v}`
          }
        />
        <Tooltip
          cursor={{ fill: "var(--color-accent-soft)" }}
          contentStyle={{
            borderRadius: 8,
            border: "1px solid var(--color-border-default)",
            background: "var(--color-bg-surface)",
            color: "var(--color-text-primary)",
            fontSize: 12,
            boxShadow: "var(--shadow-md)",
          }}
          formatter={(v) => [formatMoney(Number(v)), "Ventas"]}
        />
        <Bar
          dataKey="total"
          fill="var(--color-brand-mint)"
          radius={[4, 4, 0, 0]}
          maxBarSize={40}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}

interface DonutItem {
  name: string;
  total: number | null;
}

export function DonutChart({ data }: { data: DonutItem[] }) {
  const cleaned = data
    .map((d) => ({ name: d.name, value: d.total ?? 0 }))
    .filter((d) => d.value > 0);

  if (cleaned.length === 0) {
    return (
      <div className="flex h-[260px] items-center justify-center text-sm text-text-tertiary">
        Sin datos para graficar.
      </div>
    );
  }

  const total = cleaned.reduce((acc, d) => acc + d.value, 0);

  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie
          data={cleaned}
          dataKey="value"
          nameKey="name"
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={95}
          paddingAngle={2}
          stroke="var(--color-bg-surface)"
          strokeWidth={2}
        >
          {cleaned.map((_, i) => (
            <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            borderRadius: 8,
            border: "1px solid var(--color-border-default)",
            background: "var(--color-bg-surface)",
            color: "var(--color-text-primary)",
            fontSize: 12,
            boxShadow: "var(--shadow-md)",
          }}
          formatter={(v, name) => {
            const num = Number(v);
            const pct = total > 0 ? ((num / total) * 100).toFixed(1) : "0";
            return [`${formatMoney(num)} (${pct}%)`, String(name)];
          }}
        />
        <Legend
          verticalAlign="bottom"
          iconType="circle"
          iconSize={8}
          wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
