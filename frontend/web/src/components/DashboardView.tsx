/**
 * Dashboard operativo (Pasada A — paridad de KPIs con el legacy de Streamlit).
 *
 * - Period selector: Hoy / Semana / Mes / Personalizado.
 * - Doble query: período actual + período anterior (para deltas).
 * - Dos secciones de KPIs:
 *    - Resumen financiero: Ventas / Contado / Crédito / Balance.
 *    - Operaciones: Lavados / Servicios / Productos / Venta productos / Ticket prom. / Egresos.
 * - Breakdowns abajo (sin charts; eso queda para Pasada B).
 */

import {
  Activity,
  AlertCircle,
  CalendarDays,
  Car,
  Coins,
  CreditCard,
  Hash,
  Package,
  ReceiptText,
  RefreshCw,
  TrendingDown,
  TrendingUp,
  Users,
  Wallet,
  Wrench,
} from "lucide-react";
import { useMemo, useState } from "react";

import { DonutChart, TrendChart } from "@/components/dashboard/Charts";
import { EmptyState } from "@/components/shared/EmptyState";
import { LicensePlate } from "@/components/shared/LicensePlate";
import { StatCard } from "@/components/shared/StatCard";
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
} from "@/lib/periods";
import { cn } from "@/lib/utils";

const PERIODS: PeriodKey[] = ["today", "week", "month", "custom"];

interface BreakdownItem {
  name: string;
  count: number | null;
  total: number | null;
}

interface DonutInput {
  name: string;
  total: number | null;
}

function ChartCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="overflow-hidden rounded-xl border border-border-subtle bg-bg-surface shadow-card animate-fade-in-up">
      <div className="border-b border-border-subtle px-5 py-4">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
          {title}
        </p>
      </div>
      <div className="p-3">{children}</div>
    </div>
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
    <div className="inline-flex flex-wrap gap-1 rounded-md border border-border-subtle bg-bg-sunken p-1">
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
              "rounded px-3 py-1.5 text-xs font-medium transition",
              isActive
                ? "bg-bg-surface text-text-primary shadow-sm ring-1 ring-black/5"
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

interface DeltaChipBig {
  delta: { value: string; tone: "pos" | "neg" } | undefined;
}

function makeDelta(
  current: number,
  previous: number,
  options?: { invert?: boolean; integer?: boolean },
): DeltaChipBig["delta"] {
  const diff = current - previous;
  if (Math.abs(diff) < 0.5) return undefined;
  const positive = options?.invert ? diff < 0 : diff > 0;
  const tone: "pos" | "neg" = positive ? "pos" : "neg";
  const sign = diff > 0 ? "+" : "−";
  const abs = Math.abs(diff);
  if (options?.integer) {
    return { tone, value: `${sign}${Math.round(abs).toLocaleString("es-PY")}` };
  }
  return { tone, value: `${sign}${formatMoney(abs, { withSymbol: false })}` };
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div className="border-l-2 border-brand-mint pl-3">
      <p className="text-[11px] font-bold uppercase tracking-[0.07em] text-brand-deep">
        {children}
      </p>
    </div>
  );
}

function KpiSkeletons({ cols }: { cols: number }) {
  return (
    <div
      className={cn("grid grid-cols-2 gap-3", {
        "lg:grid-cols-4": cols === 4,
        "lg:grid-cols-3 xl:grid-cols-6": cols === 6,
      })}
    >
      {Array.from({ length: cols }).map((_, i) => (
        <Skeleton
          key={i}
          className="h-[140px] rounded-xl border border-border-subtle bg-bg-surface"
        />
      ))}
    </div>
  );
}

function BreakdownCard({
  title,
  items,
  emptyLabel,
}: {
  title: string;
  items: BreakdownItem[];
  emptyLabel: string;
}) {
  const total = items.reduce((acc, i) => acc + (i.total ?? 0), 0);
  return (
    <div className="overflow-hidden rounded-xl border border-border-subtle bg-bg-surface shadow-card animate-fade-in-up">
      <div className="flex items-center justify-between border-b border-border-subtle px-5 py-4">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
          {title}
        </p>
        <span className="font-mono text-xs tabular-nums text-text-secondary">
          {formatMoney(total)}
        </span>
      </div>
      {items.length === 0 ? (
        <div className="px-5 py-6 text-sm text-text-tertiary">{emptyLabel}</div>
      ) : (
        <ul className="divide-y divide-border-subtle">
          {items.map((it) => {
            const pct = total > 0 ? ((it.total ?? 0) / total) * 100 : 0;
            return (
              <li key={it.name} className="px-5 py-3">
                <div className="flex items-center justify-between gap-2">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{it.name}</p>
                    {it.count !== null && it.count !== undefined ? (
                      <p className="text-xs text-text-tertiary">
                        {it.count} {it.count === 1 ? "operación" : "operaciones"}
                      </p>
                    ) : null}
                  </div>
                  <span className="font-mono text-sm font-medium tabular-nums">
                    {formatMoney(it.total ?? 0)}
                  </span>
                </div>
                <div className="mt-2 h-1 overflow-hidden rounded-full bg-bg-sunken">
                  <div
                    className="h-full rounded-full bg-brand-mint/60"
                    style={{ width: `${pct.toFixed(1)}%` }}
                  />
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

export function DashboardContent() {
  const [period, setPeriod] = useState<PeriodKey>("month");
  const [customRange, setCustomRange] = useState(getPeriodRange("month"));

  const range =
    period === "custom" ? customRange : getPeriodRange(period);
  const prev = previousRange(range);
  const showDelta = period !== "custom";

  const current = useSalesSummary(range.start, range.end);
  const previous = useSalesSummary(prev.start, prev.end);
  const trend = useDailySales(range.start, range.end);
  const customers = useCustomerSummary(range.start, range.end);
  const products = useProductSummary(range.start, range.end);

  const summary = current.data;
  const prevSummary = previous.data;

  const computed = useMemo(() => {
    const salesTotal = summary?.sales_total ?? 0;
    const expenseTotal = summary?.expense_total ?? 0;
    const netBalance = summary?.net_balance ?? salesTotal - expenseTotal;
    const serviceCount = summary?.service_count ?? 0;
    const serviceSalesTotal = summary?.service_sales_total ?? 0;
    const productCount = summary?.product_count ?? 0;
    const productSalesTotal = salesTotal - serviceSalesTotal;
    const ticketAvg = serviceCount > 0 ? serviceSalesTotal / serviceCount : 0;

    const contado = summary?.payment_breakdown?.contado ?? 0;
    const credito = summary?.payment_breakdown?.credito ?? 0;

    const prevSalesTotal = prevSummary?.sales_total ?? 0;
    const prevExpenseTotal = prevSummary?.expense_total ?? 0;
    const prevNetBalance = prevSummary?.net_balance ?? prevSalesTotal - prevExpenseTotal;
    const prevServiceCount = prevSummary?.service_count ?? 0;
    const prevServiceSalesTotal = prevSummary?.service_sales_total ?? 0;
    const prevProductCount = prevSummary?.product_count ?? 0;
    const prevProductSalesTotal = prevSalesTotal - prevServiceSalesTotal;
    const prevTicketAvg =
      prevServiceCount > 0 ? prevServiceSalesTotal / prevServiceCount : 0;

    return {
      salesTotal,
      expenseTotal,
      netBalance,
      serviceCount,
      serviceSalesTotal,
      productCount,
      productSalesTotal,
      ticketAvg,
      contado,
      credito,
      prevSalesTotal,
      prevExpenseTotal,
      prevNetBalance,
      prevServiceCount,
      prevServiceSalesTotal,
      prevProductCount,
      prevProductSalesTotal,
      prevTicketAvg,
    };
  }, [summary, prevSummary]);

  if (current.isError) {
    return (
      <EmptyState
        icon={AlertCircle}
        title="No pudimos cargar el dashboard"
        description={
          current.error instanceof Error ? current.error.message : "Error desconocido."
        }
      />
    );
  }

  const isLoading = current.isLoading;

  return (
    <div className="space-y-6">
      {/* Toolbar de período */}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <PeriodSelector active={period} onChange={setPeriod} />
        {period === "custom" ? (
          <div className="flex items-end gap-2">
            <div>
              <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-text-tertiary">
                Desde
              </label>
              <Input
                type="date"
                value={customRange.start}
                onChange={(e) =>
                  setCustomRange({ ...customRange, start: e.target.value })
                }
                className="h-9 w-[150px]"
              />
            </div>
            <div>
              <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-text-tertiary">
                Hasta
              </label>
              <Input
                type="date"
                value={customRange.end}
                onChange={(e) =>
                  setCustomRange({ ...customRange, end: e.target.value })
                }
                className="h-9 w-[150px]"
              />
            </div>
          </div>
        ) : null}
      </div>

      {isLoading ? (
        <>
          <KpiSkeletons cols={4} />
          <KpiSkeletons cols={6} />
        </>
      ) : (
        <>
          {/* Resumen financiero */}
          <section className="space-y-3">
            <SectionTitle>Resumen financiero</SectionTitle>
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              <StatCard
                label="Ventas"
                value={computed.salesTotal}
                tone="pos"
                icon={<TrendingUp size={16} strokeWidth={2.5} />}
                delta={
                  showDelta
                    ? makeDelta(computed.salesTotal, computed.prevSalesTotal)
                    : undefined
                }
                delay={50}
              />
              <StatCard
                label="Contado"
                value={computed.contado}
                tone="neutral"
                icon={<Coins size={16} strokeWidth={2.5} />}
                delay={100}
              />
              <StatCard
                label="Crédito"
                value={computed.credito}
                tone="neutral"
                icon={<CreditCard size={16} strokeWidth={2.5} />}
                delay={150}
              />
              <StatCard
                label="Balance neto"
                value={computed.netBalance}
                tone={computed.netBalance >= 0 ? "neutral" : "neg"}
                icon={<Activity size={16} strokeWidth={2.5} />}
                delta={
                  showDelta
                    ? makeDelta(computed.netBalance, computed.prevNetBalance)
                    : undefined
                }
                delay={200}
              />
            </div>
          </section>

          {/* Operaciones */}
          <section className="space-y-3">
            <SectionTitle>Operaciones</SectionTitle>
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-3 xl:grid-cols-6">
              <StatCard
                label="Lavados"
                value={computed.serviceCount}
                money={false}
                tone="neutral"
                icon={<Hash size={16} strokeWidth={2.5} />}
                delta={
                  showDelta
                    ? makeDelta(computed.serviceCount, computed.prevServiceCount, { integer: true })
                    : undefined
                }
                delay={50}
              />
              <StatCard
                label="Servicios"
                value={computed.serviceSalesTotal}
                tone="pos"
                icon={<Wrench size={16} strokeWidth={2.5} />}
                delta={
                  showDelta
                    ? makeDelta(computed.serviceSalesTotal, computed.prevServiceSalesTotal)
                    : undefined
                }
                delay={100}
              />
              <StatCard
                label="Productos"
                value={computed.productCount}
                money={false}
                tone="neutral"
                icon={<Package size={16} strokeWidth={2.5} />}
                delta={
                  showDelta
                    ? makeDelta(computed.productCount, computed.prevProductCount, { integer: true })
                    : undefined
                }
                delay={150}
              />
              <StatCard
                label="Venta productos"
                value={computed.productSalesTotal}
                tone="pos"
                icon={<ReceiptText size={16} strokeWidth={2.5} />}
                delta={
                  showDelta
                    ? makeDelta(computed.productSalesTotal, computed.prevProductSalesTotal)
                    : undefined
                }
                delay={200}
              />
              <StatCard
                label="Ticket promedio"
                value={Math.round(computed.ticketAvg)}
                tone="neutral"
                icon={<TrendingUp size={16} strokeWidth={2.5} />}
                delta={
                  showDelta
                    ? makeDelta(computed.ticketAvg, computed.prevTicketAvg)
                    : undefined
                }
                delay={250}
              />
              <StatCard
                label="Egresos"
                value={computed.expenseTotal === 0 ? 0 : -computed.expenseTotal}
                tone="neg"
                icon={<Wallet size={16} strokeWidth={2.5} />}
                delta={
                  showDelta
                    ? makeDelta(computed.expenseTotal, computed.prevExpenseTotal, {
                        invert: true,
                      })
                    : undefined
                }
                delay={300}
              />
            </div>
          </section>

          {/* Tendencia */}
          {period !== "today" && (trend.data?.length ?? 0) > 1 ? (
            <section className="space-y-3">
              <SectionTitle>Tendencia diaria</SectionTitle>
              <div className="rounded-xl border border-border-subtle bg-bg-surface p-4 shadow-card animate-fade-in-up">
                <TrendChart data={trend.data ?? []} />
              </div>
            </section>
          ) : null}

          {/* Distribución (donuts) + listado detallado */}
          <section className="space-y-3">
            <SectionTitle>Distribución del período</SectionTitle>
            <div className="grid gap-4 lg:grid-cols-2">
              <ChartCard title="Ventas por item">
                <DonutChart
                  data={(summary?.sales_breakdown ?? []) as DonutInput[]}
                />
              </ChartCard>
              <ChartCard title="Egresos por categoría">
                <DonutChart
                  data={(summary?.expense_breakdown ?? []) as DonutInput[]}
                />
              </ChartCard>
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
              <BreakdownCard
                title="Ventas por item — detalle"
                items={(summary?.sales_breakdown ?? []) as BreakdownItem[]}
                emptyLabel="Sin ventas en el período."
              />
              <BreakdownCard
                title="Egresos por categoría — detalle"
                items={(summary?.expense_breakdown ?? []) as BreakdownItem[]}
                emptyLabel="Sin egresos en el período."
              />
            </div>
          </section>

          {/* Clientes del período */}
          <CustomersSection
            data={customers.data}
            isLoading={customers.isLoading}
            isError={customers.isError}
          />

          {/* Top productos */}
          <ProductsSection
            data={products.data}
            isLoading={products.isLoading}
            isError={products.isError}
          />
        </>
      )}
    </div>
  );
}

type CustomerSummary = components["schemas"]["CustomerSummaryResponse"];
type ProductSummary = components["schemas"]["ProductSummaryResponse"];

function CustomersSection({
  data,
  isLoading,
  isError,
}: {
  data: CustomerSummary | undefined;
  isLoading: boolean;
  isError: boolean;
}) {
  if (isError) return null;
  return (
    <section className="space-y-3">
      <SectionTitle>Clientes del período</SectionTitle>
      <div className="grid grid-cols-3 gap-3">
        <StatCard
          label="Vehículos únicos"
          value={data?.unique_vehicles ?? 0}
          money={false}
          tone="neutral"
          icon={<Car size={16} strokeWidth={2.5} />}
        />
        <StatCard
          label="Recurrentes"
          value={data?.recurring_customers ?? 0}
          money={false}
          tone="pos"
          icon={<RefreshCw size={16} strokeWidth={2.5} />}
        />
        <StatCard
          label="Nuevos"
          value={data?.new_customers ?? 0}
          money={false}
          tone="neutral"
          icon={<Users size={16} strokeWidth={2.5} />}
        />
      </div>

      <div className="overflow-hidden rounded-xl border border-border-subtle bg-bg-surface shadow-card animate-fade-in-up">
        <div className="border-b border-border-subtle px-5 py-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
            Top placas
          </p>
        </div>
        {isLoading ? (
          <div className="space-y-2 p-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-9 w-full rounded-md" />
            ))}
          </div>
        ) : (data?.top_plates ?? []).length === 0 ? (
          <div className="px-5 py-6 text-sm text-text-tertiary">
            Sin vehículos registrados en el período.
          </div>
        ) : (
          <ul className="divide-y divide-border-subtle">
            {(data?.top_plates ?? []).map((p, i) => (
              <li
                key={`${p.license_plate ?? "—"}-${i}`}
                className="flex items-center justify-between gap-3 px-5 py-3"
              >
                <div className="min-w-0">
                  <LicensePlate plate={p.license_plate} size="sm" />
                  <p className="mt-1 truncate text-xs text-text-tertiary">
                    {[p.vehicle_type, p.owner_name].filter(Boolean).join(" · ") || "Sin datos"}
                  </p>
                </div>
                <span className="inline-flex items-center gap-1 rounded-full bg-pos-soft px-2 py-0.5 text-[11px] font-medium text-pos">
                  {p.visit_count} {p.visit_count === 1 ? "visita" : "visitas"}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

function ProductsSection({
  data,
  isLoading,
  isError,
}: {
  data: ProductSummary | undefined;
  isLoading: boolean;
  isError: boolean;
}) {
  if (isError) return null;
  const total = (data?.top_products ?? []).reduce((acc, p) => acc + (p.total ?? 0), 0);
  const maxCount = Math.max(1, ...(data?.top_products ?? []).map((p) => p.sale_count));

  return (
    <section className="space-y-3">
      <SectionTitle>Top productos</SectionTitle>
      <div className="overflow-hidden rounded-xl border border-border-subtle bg-bg-surface shadow-card animate-fade-in-up">
        <div className="flex items-center justify-between border-b border-border-subtle px-5 py-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
            Productos más vendidos
          </p>
          <span className="font-mono text-xs tabular-nums text-text-secondary">
            {formatMoney(total)}
          </span>
        </div>
        {isLoading ? (
          <div className="space-y-2 p-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full rounded-md" />
            ))}
          </div>
        ) : (data?.top_products ?? []).length === 0 ? (
          <div className="px-5 py-6 text-sm text-text-tertiary">
            Sin productos vendidos en el período.
          </div>
        ) : (
          <ul className="divide-y divide-border-subtle">
            {(data?.top_products ?? []).map((p) => {
              const pct = (p.sale_count / maxCount) * 100;
              return (
                <li key={p.name} className="px-5 py-3">
                  <div className="flex items-center justify-between gap-2">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">{p.name}</p>
                      <p className="text-xs text-text-tertiary">
                        {p.sale_count} {p.sale_count === 1 ? "unidad vendida" : "unidades vendidas"}
                      </p>
                    </div>
                    <span className="font-mono text-sm font-medium tabular-nums">
                      {formatMoney(p.total)}
                    </span>
                  </div>
                  <div className="mt-2 h-1 overflow-hidden rounded-full bg-bg-sunken">
                    <div
                      className="h-full rounded-full bg-brand-sky/60"
                      style={{ width: `${pct.toFixed(1)}%` }}
                    />
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </section>
  );
}

export function DashboardView() {
  const user = useAuthStore((s) => s.user);
  const subtitle = user?.lavanderiaName ?? "Operación";

  return (
    <Shell
      activeKey="dashboard"
      title={`Buen día, ${user?.username ?? "operador"}`}
      subtitle={subtitle}
      actions={
        <span className="inline-flex items-center gap-1.5 rounded-md border border-border-default bg-bg-surface px-3 py-1.5 text-xs font-medium text-text-secondary">
          <CalendarDays size={14} />
          {new Intl.DateTimeFormat("es-PY", { dateStyle: "long" }).format(new Date())}
        </span>
      }
    >
      <DashboardContent />
    </Shell>
  );
}
