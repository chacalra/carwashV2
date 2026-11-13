/**
 * Dashboard operativo.
 *
 * Jerarquía (de más a menos importante):
 *  1. Ventas del período: número protagonista + variación + tendencia diaria.
 *     Al lado, el "libro mayor": Contado / Crédito / Egresos / Balance neto.
 *  2. Franja de operación: Lavados, Ticket promedio, Venta servicios,
 *     Productos vendidos, Venta productos. Una sola pieza dividida en celdas.
 *  3. Rankings: ventas por ítem y egresos por categoría (barras inline).
 *  4. Clientes del período + Top productos.
 *
 * Doble query (período actual + anterior) para calcular variaciones.
 */

import { AlertCircle, ArrowDownRight, ArrowUpRight } from "lucide-react";
import { useMemo, useState } from "react";

import { TrendChart } from "@/components/dashboard/Charts";
import { EmptyState } from "@/components/shared/EmptyState";
import { LicensePlate } from "@/components/shared/LicensePlate";
import { MoneyText } from "@/components/shared/MoneyText";
import { Shell } from "@/components/shell/Shell";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useCustomerSummary,
  useDailySales,
  useProductSummary,
  useSalesSummary,
} from "@/lib/api/queries/reports";
import type { components } from "@/lib/api/schema";
import { useAuthStore } from "@/lib/auth/store";
import { formatMoney } from "@/lib/format";
import {
  getPeriodRange,
  PERIOD_LABELS,
  previousRange,
  type PeriodKey,
  type PeriodRange,
} from "@/lib/periods";
import { cn } from "@/lib/utils";

const PERIODS: PeriodKey[] = ["today", "week", "month", "custom"];

const COMPARE_LABEL: Record<PeriodKey, string> = {
  today: "vs. ayer",
  week: "vs. semana anterior",
  month: "vs. mes anterior",
  custom: "",
};

interface BreakdownItem {
  name: string;
  count: number | null;
  total: number | null;
}

type CustomerSummary = components["schemas"]["CustomerSummaryResponse"];
type ProductSummary = components["schemas"]["ProductSummaryResponse"];

// ----------------------------------------------------------------------------
// Primitivas de layout
// ----------------------------------------------------------------------------

function Panel({
  title,
  aside,
  children,
  className,
}: {
  title: string;
  aside?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section
      className={cn(
        "overflow-hidden rounded-lg border border-border-default bg-bg-surface animate-fade-in-up",
        className,
      )}
    >
      <header className="flex items-center justify-between gap-3 border-b border-border-subtle px-4 py-3">
        <h2 className="text-[13px] font-medium text-text-primary">{title}</h2>
        {aside ? (
          <span className="text-xs tabular-nums text-text-tertiary">{aside}</span>
        ) : null}
      </header>
      {children}
    </section>
  );
}

function PeriodSelector({
  active,
  onChange,
}: {
  active: PeriodKey;
  onChange: (p: PeriodKey) => void;
}) {
  return (
    <div
      role="tablist"
      aria-label="Período"
      className="inline-flex rounded-md border border-border-default bg-bg-sunken p-0.5"
    >
      {PERIODS.map((p) => {
        const isActive = active === p;
        return (
          <button
            key={p}
            type="button"
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(p)}
            className={cn(
              "rounded-[5px] px-3 py-1 text-[13px] transition-colors",
              isActive
                ? "bg-white font-medium text-text-primary shadow-[0_0_0_1px_var(--color-border-default),0_1px_2px_0_rgb(0_0_0/0.06)] dark:bg-white/12"
                : "text-text-secondary hover:text-text-primary",
            )}
          >
            {PERIOD_LABELS[p]}
          </button>
        );
      })}
    </div>
  );
}

function formatRange(range: PeriodRange) {
  const fmt = (iso: string, withYear: boolean) =>
    new Date(`${iso}T00:00:00`).toLocaleDateString("es-PY", {
      day: "numeric",
      month: "short",
      ...(withYear ? { year: "numeric" } : {}),
    });
  if (range.start === range.end) return fmt(range.end, true);
  return `${fmt(range.start, false)} – ${fmt(range.end, true)}`;
}

// ----------------------------------------------------------------------------
// Variación vs. período anterior
// ----------------------------------------------------------------------------

interface DeltaInfo {
  text: string;
  good: boolean;
}

/**
 * Variación expresada en %. Si el período anterior fue 0 no hay base para un
 * porcentaje: mostramos la diferencia absoluta.
 * `invert` = subir es malo (egresos).
 */
function computeDelta(
  current: number,
  previous: number,
  options?: { invert?: boolean; integer?: boolean },
): DeltaInfo | undefined {
  const diff = current - previous;
  if (Math.abs(diff) < 0.5) return undefined;
  const up = diff > 0;
  const good = options?.invert ? !up : up;
  if (previous !== 0) {
    const pct = Math.abs(diff / previous) * 100;
    const shown = pct >= 10 ? Math.round(pct).toString() : pct.toFixed(1).replace(".", ",");
    return { text: `${shown}%`, good };
  }
  const abs = Math.abs(diff);
  const sign = up ? "+" : "−";
  const value = options?.integer
    ? Math.round(abs).toLocaleString("es-PY")
    : formatMoney(abs, { withSymbol: false });
  return { text: `${sign}${value}`, good };
}

function Delta({
  delta,
  up,
  className,
}: {
  delta: DeltaInfo | undefined;
  up: boolean;
  className?: string;
}) {
  if (!delta) return null;
  const Icon = up ? ArrowUpRight : ArrowDownRight;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-0.5 text-xs font-medium tabular-nums",
        delta.good ? "text-pos-fg" : "text-neg-fg",
        className,
      )}
    >
      <Icon size={12} strokeWidth={2.25} aria-hidden />
      {delta.text}
    </span>
  );
}

// ----------------------------------------------------------------------------
// Bloques
// ----------------------------------------------------------------------------

function LedgerRow({
  label,
  value,
  delta,
  up,
  emphasis,
}: {
  label: string;
  value: number;
  delta?: DeltaInfo;
  up?: boolean;
  emphasis?: boolean;
}) {
  return (
    <div
      className={cn(
        "flex flex-1 items-center justify-between gap-3 px-5",
        emphasis ? "border-t border-border-default py-4" : "py-3",
      )}
    >
      <span
        className={cn(
          "text-[13px]",
          emphasis ? "font-medium text-text-primary" : "text-text-secondary",
        )}
      >
        {label}
      </span>
      <span className="flex flex-col items-end gap-0.5">
        <MoneyText
          value={value}
          className={cn(
            "font-medium",
            emphasis ? "text-lg font-semibold" : "text-[15px]",
            emphasis && value < 0 && "text-neg-fg",
          )}
        />
        <Delta delta={delta} up={!!up} />
      </span>
    </div>
  );
}

function MetricCell({
  label,
  children,
  delta,
  up,
}: {
  label: string;
  children: React.ReactNode;
  delta?: DeltaInfo;
  up?: boolean;
}) {
  return (
    <div className="border-t border-l border-border-subtle px-4 py-3.5">
      <p className="text-xs text-text-secondary">{label}</p>
      <p className="mt-1 text-xl font-semibold tracking-tight tabular-nums">{children}</p>
      <div className="mt-0.5 h-4">
        <Delta delta={delta} up={!!up} />
      </div>
    </div>
  );
}

function RankedList({
  items,
  emptyLabel,
  barClass,
  countLabel,
}: {
  items: BreakdownItem[];
  emptyLabel: string;
  barClass: string;
  countLabel?: (n: number) => string;
}) {
  if (items.length === 0) {
    return <p className="px-4 py-6 text-[13px] text-text-tertiary">{emptyLabel}</p>;
  }
  const sorted = [...items].sort((a, b) => (b.total ?? 0) - (a.total ?? 0));
  const total = sorted.reduce((acc, i) => acc + (i.total ?? 0), 0);
  const max = Math.max(1, ...sorted.map((i) => i.total ?? 0));
  return (
    <ul className="divide-y divide-border-subtle">
      {sorted.map((it) => {
        const share = total > 0 ? ((it.total ?? 0) / total) * 100 : 0;
        return (
          <li key={it.name} className="px-4 py-2.5">
            <div className="flex items-baseline justify-between gap-3">
              <p className="min-w-0 truncate text-[13px]">
                {it.name}
                {it.count != null && countLabel ? (
                  <span className="ml-2 text-xs text-text-tertiary">{countLabel(it.count)}</span>
                ) : null}
              </p>
              <span className="flex shrink-0 items-baseline gap-2">
                <span className="w-9 text-right text-xs tabular-nums text-text-tertiary">
                  {Math.round(share)}%
                </span>
                <MoneyText value={it.total ?? 0} className="text-[13px] font-medium" />
              </span>
            </div>
            <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-bg-sunken">
              <div
                className={cn("h-full rounded-full", barClass)}
                style={{ width: `${(((it.total ?? 0) / max) * 100).toFixed(1)}%` }}
              />
            </div>
          </li>
        );
      })}
    </ul>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-[320px] rounded-lg" />
      <Skeleton className="h-[96px] rounded-lg" />
      <div className="grid gap-4 lg:grid-cols-2">
        <Skeleton className="h-[240px] rounded-lg" />
        <Skeleton className="h-[240px] rounded-lg" />
      </div>
    </div>
  );
}

// ----------------------------------------------------------------------------
// Contenido
// ----------------------------------------------------------------------------

export function DashboardContent() {
  const [period, setPeriod] = useState<PeriodKey>("month");
  const [customRange, setCustomRange] = useState(getPeriodRange("month"));

  const range = period === "custom" ? customRange : getPeriodRange(period);
  const prev = previousRange(range);
  const showDelta = period !== "custom";

  const current = useSalesSummary(range.start, range.end);
  const previous = useSalesSummary(prev.start, prev.end);
  const trend = useDailySales(range.start, range.end);
  const customers = useCustomerSummary(range.start, range.end);
  const products = useProductSummary(range.start, range.end);

  const summary = current.data;
  const prevSummary = previous.data;

  const m = useMemo(() => {
    const pick = (s: typeof summary) => {
      const salesTotal = s?.sales_total ?? 0;
      const expenseTotal = s?.expense_total ?? 0;
      const serviceCount = s?.service_count ?? 0;
      const serviceSalesTotal = s?.service_sales_total ?? 0;
      return {
        salesTotal,
        expenseTotal,
        netBalance: s?.net_balance ?? salesTotal - expenseTotal,
        serviceCount,
        serviceSalesTotal,
        productCount: s?.product_count ?? 0,
        productSalesTotal: salesTotal - serviceSalesTotal,
        ticketAvg: serviceCount > 0 ? serviceSalesTotal / serviceCount : 0,
        contado: s?.payment_breakdown?.contado ?? 0,
        credito: s?.payment_breakdown?.credito ?? 0,
      };
    };
    return { cur: pick(summary), prev: pick(prevSummary) };
  }, [summary, prevSummary]);

  if (current.isError) {
    return (
      <EmptyState
        icon={AlertCircle}
        title="No pudimos cargar el dashboard"
        description={current.error instanceof Error ? current.error.message : "Error desconocido."}
      />
    );
  }

  const { cur, prev: p } = m;
  const d = (
    c: number,
    pv: number,
    o?: { invert?: boolean; integer?: boolean },
  ) => (showDelta ? computeDelta(c, pv, o) : undefined);
  const showTrend = period !== "today" && (trend.data?.length ?? 0) > 0;

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <PeriodSelector active={period} onChange={setPeriod} />
        {period === "custom" ? (
          <div className="flex items-center gap-2">
            <Input
              type="date"
              aria-label="Desde"
              value={customRange.start}
              onChange={(e) => setCustomRange({ ...customRange, start: e.target.value })}
              className="h-8 w-[150px] text-[13px]"
            />
            <span className="text-text-tertiary">–</span>
            <Input
              type="date"
              aria-label="Hasta"
              value={customRange.end}
              onChange={(e) => setCustomRange({ ...customRange, end: e.target.value })}
              className="h-8 w-[150px] text-[13px]"
            />
          </div>
        ) : (
          <span className="text-[13px] text-text-tertiary">{formatRange(range)}</span>
        )}
      </div>

      {current.isLoading ? (
        <DashboardSkeleton />
      ) : (
        <>
          {/* 1. Ventas + libro mayor */}
          <section className="grid overflow-hidden rounded-lg border border-border-default bg-bg-surface animate-fade-in-up lg:grid-cols-[minmax(0,1fr)_320px]">
            <div className="px-5 pt-5 pb-3">
              <p className="text-[13px] text-text-secondary">Ventas</p>
              <div className="mt-1 flex flex-wrap items-baseline gap-x-3 gap-y-1">
                <MoneyText
                  value={cur.salesTotal}
                  className="text-[34px] font-semibold leading-none tracking-tight sm:text-[40px]"
                />
                {showDelta ? (
                  <span className="flex items-baseline gap-1.5">
                    <Delta
                      delta={d(cur.salesTotal, p.salesTotal)}
                      up={cur.salesTotal > p.salesTotal}
                      className="text-[13px]"
                    />
                    {d(cur.salesTotal, p.salesTotal) ? (
                      <span className="text-xs text-text-tertiary">{COMPARE_LABEL[period]}</span>
                    ) : null}
                  </span>
                ) : null}
              </div>
              {showTrend ? (
                <div className="mt-5">
                  <TrendChart data={trend.data ?? []} start={range.start} end={range.end} />
                </div>
              ) : (
                <p className="mt-6 text-xs text-text-tertiary">
                  La tendencia diaria se muestra en períodos de más de un día.
                </p>
              )}
            </div>

            <div className="flex flex-col divide-y divide-border-subtle border-t border-border-subtle bg-white/25 dark:bg-white/[0.02] lg:border-t-0 lg:border-l">
              <LedgerRow label="Contado" value={cur.contado} />
              <LedgerRow label="Crédito" value={cur.credito} />
              <LedgerRow
                label="Egresos"
                value={cur.expenseTotal === 0 ? 0 : -cur.expenseTotal}
                delta={d(cur.expenseTotal, p.expenseTotal, { invert: true })}
                up={cur.expenseTotal > p.expenseTotal}
              />
              <LedgerRow
                label="Balance neto"
                value={cur.netBalance}
                delta={d(cur.netBalance, p.netBalance)}
                up={cur.netBalance > p.netBalance}
                emphasis
              />
            </div>
          </section>

          {/* 2. Franja de operación */}
          <section
            aria-label="Operación"
            className="overflow-hidden rounded-lg border border-border-default bg-bg-surface animate-fade-in-up"
          >
            <div className="-mt-px -ml-px grid grid-cols-2 lg:grid-cols-5 [&>*:last-child]:col-span-2 lg:[&>*:last-child]:col-span-1">
            <MetricCell
              label="Lavados"
              delta={d(cur.serviceCount, p.serviceCount, { integer: true })}
              up={cur.serviceCount > p.serviceCount}
            >
              {cur.serviceCount.toLocaleString("es-PY")}
            </MetricCell>
            <MetricCell
              label="Ticket promedio"
              delta={d(cur.ticketAvg, p.ticketAvg)}
              up={cur.ticketAvg > p.ticketAvg}
            >
              <MoneyText value={Math.round(cur.ticketAvg)} />
            </MetricCell>
            <MetricCell
              label="Venta servicios"
              delta={d(cur.serviceSalesTotal, p.serviceSalesTotal)}
              up={cur.serviceSalesTotal > p.serviceSalesTotal}
            >
              <MoneyText value={cur.serviceSalesTotal} />
            </MetricCell>
            <MetricCell
              label="Productos vendidos"
              delta={d(cur.productCount, p.productCount, { integer: true })}
              up={cur.productCount > p.productCount}
            >
              {cur.productCount.toLocaleString("es-PY")}
            </MetricCell>
            <MetricCell
              label="Venta productos"
              delta={d(cur.productSalesTotal, p.productSalesTotal)}
              up={cur.productSalesTotal > p.productSalesTotal}
            >
              <MoneyText value={cur.productSalesTotal} />
            </MetricCell>
            </div>
          </section>

          {/* 3. Rankings */}
          <div className="grid gap-4 lg:grid-cols-2">
            <Panel title="Ventas por ítem" aside={formatMoney(sumTotals(summary?.sales_breakdown))}>
              <RankedList
                items={(summary?.sales_breakdown ?? []) as BreakdownItem[]}
                emptyLabel="Sin ventas en el período."
                barClass="bg-accent"
                countLabel={(n) => `${n} ${n === 1 ? "operación" : "operaciones"}`}
              />
            </Panel>
            <Panel
              title="Egresos por categoría"
              aside={formatMoney(sumTotals(summary?.expense_breakdown))}
            >
              <RankedList
                items={(summary?.expense_breakdown ?? []) as BreakdownItem[]}
                emptyLabel="Sin egresos en el período."
                barClass="bg-text-tertiary/60"
              />
            </Panel>
          </div>

          {/* 4. Clientes + productos */}
          <div className="grid gap-4 lg:grid-cols-2">
            <CustomersPanel
              data={customers.data}
              isLoading={customers.isLoading}
              isError={customers.isError}
            />
            <ProductsPanel
              data={products.data}
              isLoading={products.isLoading}
              isError={products.isError}
            />
          </div>
        </>
      )}
    </div>
  );
}

function sumTotals(items: { total?: number | null }[] | null | undefined) {
  return (items ?? []).reduce((acc, i) => acc + (i.total ?? 0), 0);
}

function ListSkeleton({ rows }: { rows: number }) {
  return (
    <div className="space-y-2 p-4">
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-8 w-full rounded-md" />
      ))}
    </div>
  );
}

function CustomersPanel({
  data,
  isLoading,
  isError,
}: {
  data: CustomerSummary | undefined;
  isLoading: boolean;
  isError: boolean;
}) {
  if (isError) return null;
  const plates = data?.top_plates ?? [];
  return (
    <Panel title="Clientes del período">
      <div className="grid grid-cols-3 divide-x divide-border-subtle border-b border-border-subtle">
        {[
          { label: "Vehículos únicos", value: data?.unique_vehicles ?? 0 },
          { label: "Recurrentes", value: data?.recurring_customers ?? 0 },
          { label: "Nuevos", value: data?.new_customers ?? 0 },
        ].map((s) => (
          <div key={s.label} className="px-4 py-3">
            <p className="text-xs text-text-secondary">{s.label}</p>
            <p className="mt-0.5 text-lg font-semibold tabular-nums">{s.value}</p>
          </div>
        ))}
      </div>
      <p className="px-4 pt-3 pb-1 text-xs text-text-tertiary">Placas más frecuentes</p>
      {isLoading ? (
        <ListSkeleton rows={3} />
      ) : plates.length === 0 ? (
        <p className="px-4 pb-5 pt-2 text-[13px] text-text-tertiary">
          Sin vehículos registrados en el período.
        </p>
      ) : (
        <ul className="divide-y divide-border-subtle">
          {plates.map((pl, i) => (
            <li
              key={`${pl.license_plate ?? "—"}-${i}`}
              className="flex items-center justify-between gap-3 px-4 py-2"
            >
              <div className="flex min-w-0 items-center gap-3">
                <LicensePlate plate={pl.license_plate} size="xs" />
                <span className="truncate text-[13px] text-text-secondary">
                  {[pl.vehicle_type, pl.owner_name].filter(Boolean).join(" · ") || "Sin datos"}
                </span>
              </div>
              <span className="shrink-0 text-xs tabular-nums text-text-tertiary">
                {pl.visit_count} {pl.visit_count === 1 ? "visita" : "visitas"}
              </span>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

function ProductsPanel({
  data,
  isLoading,
  isError,
}: {
  data: ProductSummary | undefined;
  isLoading: boolean;
  isError: boolean;
}) {
  if (isError) return null;
  const list = data?.top_products ?? [];
  const total = list.reduce((acc, pr) => acc + (pr.total ?? 0), 0);
  const maxCount = Math.max(1, ...list.map((pr) => pr.sale_count));

  return (
    <Panel title="Top productos" aside={list.length > 0 ? formatMoney(total) : undefined}>
      {isLoading ? (
        <ListSkeleton rows={4} />
      ) : list.length === 0 ? (
        <p className="px-4 py-6 text-[13px] text-text-tertiary">
          Sin productos vendidos en el período.
        </p>
      ) : (
        <ul className="divide-y divide-border-subtle">
          {list.map((pr) => (
            <li key={pr.name} className="px-4 py-2.5">
              <div className="flex items-baseline justify-between gap-3">
                <p className="min-w-0 truncate text-[13px]">
                  {pr.name}
                  <span className="ml-2 text-xs text-text-tertiary">
                    {pr.sale_count} {pr.sale_count === 1 ? "unidad vendida" : "unidades vendidas"}
                  </span>
                </p>
                <MoneyText value={pr.total} className="text-[13px] font-medium" />
              </div>
              <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-bg-sunken">
                <div
                  className="h-full rounded-full bg-brand-sky"
                  style={{ width: `${((pr.sale_count / maxCount) * 100).toFixed(1)}%` }}
                />
              </div>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

export function DashboardView() {
  const user = useAuthStore((s) => s.user);
  return (
    <Shell activeKey="dashboard" title="Dashboard" subtitle={user?.lavanderiaName ?? undefined}>
      <DashboardContent />
    </Shell>
  );
}
