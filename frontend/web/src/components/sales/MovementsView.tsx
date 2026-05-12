/**
 * Iter 4 — Movimientos.
 *
 * Listado de ventas en un rango (default mes actual). Filtros: tipo de cobro,
 * búsqueda local por placa/RUC/cliente. Tabla con filas expandibles que
 * muestran los items. Acciones: ver (expand), editar (placeholder Iter 5),
 * anular (DELETE /sales/{id} con confirm).
 */

import {
  AlertCircle,
  CalendarDays,
  Building2,
  ChevronDown,
  ChevronRight,
  CircleSlash,
  Filter,
  Loader2,
  Package,
  Pencil,
  ReceiptText,
  RefreshCw,
  Search,
  Trash2,
  Wrench,
  X,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";

import { EmptyState } from "@/components/shared/EmptyState";
import { LicensePlate } from "@/components/shared/LicensePlate";
import { Shell } from "@/components/shell/Shell";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api/client";
import { useSalesGrouped, useVoidSale } from "@/lib/api/queries/sales";
import { useAuthStore } from "@/lib/auth/store";
import type { components } from "@/lib/api/schema";
import { firstDayOfMonthISO, formatDate, formatMoney, todayISO } from "@/lib/format";
import { cn } from "@/lib/utils";

type SaleResponse = components["schemas"]["SaleResponse"];

type TipoCobroFilter = "all" | "Contado" | "Credito";

type ItemKind = "service" | "product";

interface ItemsBreakdown {
  principal: { kind: ItemKind; name: string; quantity: number } | null;
  extras: number; // items adicionales mas alla del principal
}

function breakdownItems(sale: SaleResponse): ItemsBreakdown {
  if (!sale.items.length) return { principal: null, extras: 0 };
  // Damos prioridad al servicio como principal: en este negocio el lavado es
  // el motivo de la venta, los productos son add-on.
  const service = sale.items.find((it) => it.item_type === "Servicio");
  const principalItem = service ?? sale.items[0];
  const principal = {
    kind: principalItem.item_type === "Servicio" ? "service" : "product",
    name: principalItem.item_name,
    quantity: principalItem.quantity,
  } satisfies ItemsBreakdown["principal"];
  const extras = sale.items.length - 1;
  return { principal, extras };
}

function ItemsSummary({ sale }: { sale: SaleResponse }) {
  const { principal, extras } = breakdownItems(sale);
  if (!principal) {
    return <span className="text-text-tertiary">Sin ítems</span>;
  }
  const Icon = principal.kind === "service" ? Wrench : Package;
  return (
    <span className="inline-flex max-w-full items-center gap-1.5">
      <Icon
        size={13}
        strokeWidth={2}
        className={cn(
          "shrink-0",
          principal.kind === "service" ? "text-brand-deep" : "text-brand-sky",
        )}
        aria-hidden
      />
      <span className="truncate text-text-secondary">
        {principal.quantity > 1 ? `${principal.quantity}× ` : ""}
        {principal.name}
      </span>
      {extras > 0 ? (
        <span className="shrink-0 rounded-full bg-bg-sunken px-1.5 py-0.5 text-[10px] font-medium tabular-nums text-text-tertiary">
          +{extras}
        </span>
      ) : null}
    </span>
  );
}

// Clave canonica de los items de una venta para detectar identidad entre filas.
// Considera mismos ids + mismas cantidades, sin importar orden.
function itemsKey(sale: SaleResponse): string {
  return sale.items
    .map((it) => `${it.item_type}:${it.service_id ?? it.product_id}:${it.quantity}`)
    .sort()
    .join("|");
}

export function MovementsInner() {
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const canEdit = hasPermission("edit_sale");
  const canVoid = hasPermission("manage_sales");

  const [start, setStart] = useState(firstDayOfMonthISO());
  const [end, setEnd] = useState(todayISO());
  const [tipoCobro, setTipoCobro] = useState<TipoCobroFilter>("all");
  const [search, setSearch] = useState("");
  const [selectedRazones, setSelectedRazones] = useState<string[]>([]);
  const [excludeRazones, setExcludeRazones] = useState(false);
  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const [voidTarget, setVoidTarget] = useState<SaleResponse | null>(null);

  const { data, isLoading, isError, error, refetch, isFetching } = useSalesGrouped(start, end);

  // Razones sociales unicas presentes en ventas con factura del rango.
  // Refleja el comportamiento del legacy (`_get_billable_client_options`).
  const razonesOptions = useMemo(() => {
    const set = new Set<string>();
    for (const s of data ?? []) {
      if (s.requires_invoice && s.customer_name) set.add(s.customer_name);
    }
    return Array.from(set).sort((a, b) => a.localeCompare(b, "es"));
  }, [data]);

  // Si cambia el rango y desaparecen razones seleccionadas, las limpiamos.
  useEffect(() => {
    if (selectedRazones.length === 0) return;
    const stillValid = selectedRazones.filter((r) => razonesOptions.includes(r));
    if (stillValid.length !== selectedRazones.length) {
      setSelectedRazones(stillValid);
      if (stillValid.length === 0) setExcludeRazones(false);
    }
  }, [razonesOptions, selectedRazones]);
  const voidSale = useVoidSale();

  const filtered = useMemo(() => {
    const list = data ?? [];
    const term = search.trim().toLowerCase();
    const razonesActive = selectedRazones.length > 0;
    return list.filter((s) => {
      if (tipoCobro !== "all" && s.payment_type !== tipoCobro) return false;
      if (razonesActive) {
        const matches = s.requires_invoice && selectedRazones.includes(s.customer_name);
        if (excludeRazones ? matches : !matches) return false;
      }
      if (!term) return true;
      const haystack = [
        s.customer_name,
        s.ruc_ci,
        s.license_plate,
        s.payment_method,
        ...s.items.map((it) => it.item_name),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return haystack.includes(term);
    });
  }, [data, tipoCobro, search, selectedRazones, excludeRazones]);

  const stats = useMemo(() => {
    const list = filtered;
    const total = list.reduce((acc, s) => acc + (s.is_voided ? 0 : s.total), 0);
    const count = list.filter((s) => !s.is_voided).length;
    const avg = count > 0 ? total / count : 0;
    return { total, count, avg, all: list.length };
  }, [filtered]);

  // Si todas las filas visibles tienen exactamente los mismos items (mismo
  // servicio/producto en mismas cantidades), lo subimos al banner del header
  // y eliminamos la columna ITEMS de la tabla. Aplica al caso muy comun de
  // filtrar 1 empresa que siempre compra el mismo lavado.
  const commonItems = useMemo(() => {
    const list = filtered.filter((s) => !s.is_voided);
    if (list.length === 0) return null;
    const firstKey = itemsKey(list[0]);
    if (!firstKey) return null;
    const allSame = list.every((s) => itemsKey(s) === firstKey);
    return allSame ? list[0] : null;
  }, [filtered]);

  // Si todas las filas visibles comparten cliente, lo mostramos en el header
  // y achicamos su peso visual en cada fila. Reduce ruido cuando filtrás por
  // una sola empresa (que es lo mas comun en uso contable).
  const singleCustomer = useMemo(() => {
    const list = filtered.filter((s) => !s.is_voided);
    if (list.length === 0) return null;
    const first = list[0];
    const allSame = list.every(
      (s) => s.customer_name === first.customer_name && s.ruc_ci === first.ruc_ci,
    );
    return allSame
      ? { name: first.customer_name, ruc: first.ruc_ci ?? null }
      : null;
  }, [filtered]);

  // Cuando hay >1 razon social seleccionada, breakdown por cliente para que el
  // usuario vea cuanto factura cada empresa sin tener que sumar a mano.
  const razonesBreakdown = useMemo(() => {
    if (selectedRazones.length < 2 || excludeRazones) return null;
    const totals = new Map<string, { total: number; count: number }>();
    for (const s of filtered) {
      if (s.is_voided) continue;
      if (!s.requires_invoice) continue;
      const entry = totals.get(s.customer_name) ?? { total: 0, count: 0 };
      entry.total += s.total;
      entry.count += 1;
      totals.set(s.customer_name, entry);
    }
    return Array.from(totals.entries())
      .map(([name, v]) => ({ name, total: v.total, count: v.count }))
      .sort((a, b) => b.total - a.total);
  }, [filtered, selectedRazones, excludeRazones]);

  const toggleExpand = (id: number) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const onVoid = (sale: SaleResponse) => {
    if (sale.is_voided) return;
    setVoidTarget(sale);
  };

  const confirmVoid = () => {
    if (!voidTarget) return;
    const target = voidTarget;
    voidSale.mutate(target.id, {
      onSuccess: () => {
        toast.success("Venta anulada", { description: `Movimiento #${target.id}.` });
        setVoidTarget(null);
      },
      onError: (err) => {
        const msg = err instanceof ApiError ? err.message : "No se pudo anular.";
        toast.error("Error al anular", { description: msg });
        setVoidTarget(null);
      },
    });
  };

  const clearFilters = () => {
    setTipoCobro("all");
    setSearch("");
    setSelectedRazones([]);
    setExcludeRazones(false);
  };

  const activeFilterCount =
    (tipoCobro !== "all" ? 1 : 0) +
    (search.trim() !== "" ? 1 : 0) +
    (selectedRazones.length > 0 ? 1 : 0);
  const filtersActive = activeFilterCount > 0;

  return (
    <div className="space-y-4">
      {/* Filtros */}
      <section className="rounded-xl border border-border-subtle bg-bg-surface shadow-card animate-fade-in-up">
        <div className="flex flex-wrap items-end gap-3 p-4">
          <div className="flex min-w-[140px] flex-1 flex-col gap-1 sm:flex-none">
            <label className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
              Desde
            </label>
            <Input
              type="date"
              value={start}
              onChange={(e) => setStart(e.target.value)}
              className="h-9 sm:w-[160px]"
            />
          </div>

          <div className="flex min-w-[140px] flex-1 flex-col gap-1 sm:flex-none">
            <label className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
              Hasta
            </label>
            <Input
              type="date"
              value={end}
              onChange={(e) => setEnd(e.target.value)}
              className="h-9 sm:w-[160px]"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
              Tipo de cobro
            </label>
            <div className="inline-flex rounded-md border border-border-subtle bg-bg-sunken p-1">
              {(
                [
                  { v: "all" as TipoCobroFilter, l: "Todos" },
                  { v: "Contado" as TipoCobroFilter, l: "Contado" },
                  { v: "Credito" as TipoCobroFilter, l: "Crédito" },
                ]
              ).map((opt) => {
                const active = tipoCobro === opt.v;
                return (
                  <button
                    key={opt.v}
                    type="button"
                    onClick={() => setTipoCobro(opt.v)}
                    className={cn(
                      "rounded px-3 py-1 text-xs font-medium transition",
                      active
                        ? "bg-bg-surface text-text-primary shadow-sm ring-1 ring-black/5"
                        : "text-text-secondary hover:text-text-primary",
                    )}
                  >
                    {opt.l}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="flex flex-1 flex-col gap-1 min-w-[220px]">
            <label className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
              Buscar
            </label>
            <div className="relative">
              <Search
                size={14}
                className="absolute left-2.5 top-1/2 -translate-y-1/2 text-text-tertiary"
              />
              <Input
                placeholder="Cliente, RUC, placa…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="h-9 pl-8"
              />
              {search ? (
                <button
                  type="button"
                  onClick={() => setSearch("")}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-text-tertiary hover:text-text-primary"
                  aria-label="Limpiar búsqueda"
                >
                  <X size={14} />
                </button>
              ) : null}
            </div>
          </div>

          <RazonSocialFilter
            options={razonesOptions}
            selected={selectedRazones}
            onChange={(next) => {
              setSelectedRazones(next);
              if (next.length === 0) setExcludeRazones(false);
            }}
            exclude={excludeRazones}
            onExcludeChange={setExcludeRazones}
          />

          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              disabled={isFetching}
            >
              {isFetching ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <RefreshCw size={14} />
              )}
              Refrescar
            </Button>
          </div>
        </div>

        {/* Chips removibles de filtros activos. Mas claro que un contador. */}
        {filtersActive ? (
          <div className="flex flex-wrap items-center gap-1.5 border-t border-border-subtle px-4 py-2">
            <Filter size={12} className="text-text-tertiary" aria-hidden />
            {tipoCobro !== "all" ? (
              <ActiveFilterChip
                label={tipoCobro}
                onRemove={() => setTipoCobro("all")}
              />
            ) : null}
            {search.trim() !== "" ? (
              <ActiveFilterChip
                label={`"${search.trim()}"`}
                onRemove={() => setSearch("")}
              />
            ) : null}
            {selectedRazones.map((name) => (
              <ActiveFilterChip
                key={name}
                label={excludeRazones ? `≠ ${name}` : name}
                onRemove={() =>
                  setSelectedRazones((prev) => prev.filter((r) => r !== name))
                }
              />
            ))}
            <button
              type="button"
              onClick={clearFilters}
              className="ml-auto text-[11px] text-text-tertiary hover:text-text-primary"
            >
              Limpiar todos
            </button>
          </div>
        ) : null}

        {/* Strip de stats */}
        <div className="grid grid-cols-3 divide-x divide-border-subtle border-t border-border-subtle">
          <Stat label="Ventas" value={`${stats.count}`} hint={stats.all !== stats.count ? `${stats.all - stats.count} anuladas` : undefined} />
          <Stat label="Total" value={formatMoney(stats.total)} mono />
          <Stat label="Ticket promedio" value={formatMoney(stats.avg)} mono />
        </div>

        {/* Breakdown por razón social cuando hay >1 empresa seleccionada. */}
        {razonesBreakdown && razonesBreakdown.length > 1 ? (
          <div className="border-t border-border-subtle px-4 py-3">
            <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
              Por razón social
            </p>
            <ul className="grid gap-1.5 sm:grid-cols-2 lg:grid-cols-3">
              {razonesBreakdown.map((r) => (
                <li
                  key={r.name}
                  className="flex items-baseline justify-between gap-2 rounded-md bg-bg-sunken px-3 py-1.5"
                >
                  <span className="truncate text-xs text-text-secondary">
                    <span className="text-text-tertiary">{r.count}×</span> {r.name}
                  </span>
                  <span className="font-mono text-xs font-semibold tabular-nums">
                    {formatMoney(r.total)}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </section>

      {/* Banner del cliente único y/o items idénticos en todas las filas. */}
      {singleCustomer || commonItems ? (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-accent/30 bg-accent-soft px-4 py-2.5">
          <div className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1">
            {singleCustomer ? (
              <span className="flex min-w-0 items-center gap-2">
                <Building2 size={14} className="shrink-0 text-accent" />
                <span className="text-sm font-semibold text-accent">
                  {singleCustomer.name}
                </span>
                {singleCustomer.ruc ? (
                  <span className="text-sm text-text-secondary">
                    · {singleCustomer.ruc}
                  </span>
                ) : null}
              </span>
            ) : null}
            {commonItems ? (
              <span className="flex min-w-0 items-center gap-1.5 rounded-full bg-bg-surface/60 px-2 py-0.5 text-xs">
                <ItemsSummary sale={commonItems} />
              </span>
            ) : null}
          </div>
          <span className="shrink-0 text-[11px] text-text-tertiary">
            {stats.count} ventas · {formatMoney(stats.total)}
          </span>
        </div>
      ) : null}

      {/* Tabla / estados */}
      {isLoading ? (
        <TableSkeleton />
      ) : isError ? (
        <EmptyState
          icon={AlertCircle}
          title="No pudimos cargar las ventas"
          description={error instanceof Error ? error.message : "Error desconocido."}
        />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={ReceiptText}
          title={(data?.length ?? 0) === 0 ? "Sin ventas en el período" : "Sin coincidencias"}
          description={
            (data?.length ?? 0) === 0
              ? "Cuando registres ventas en este rango van a aparecer acá."
              : "Probá ajustar los filtros o limpiarlos."
          }
        />
      ) : (
        <SalesTable
          rows={filtered}
          expanded={expanded}
          toggleExpand={toggleExpand}
          canEdit={canEdit}
          canVoid={canVoid}
          onVoid={onVoid}
          isVoidPending={voidSale.isPending}
          hideCustomer={Boolean(singleCustomer)}
          hideItems={Boolean(commonItems)}
        />
      )}

      <AlertDialog
        open={voidTarget !== null}
        onOpenChange={(open) => {
          if (!open) setVoidTarget(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Anular esta venta?</AlertDialogTitle>
            <AlertDialogDescription>
              {voidTarget
                ? `Movimiento #${voidTarget.id} por ${formatMoney(voidTarget.total)}. Es una anulación lógica y se puede revisar después.`
                : ""}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={voidSale.isPending}>
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={(e) => {
                e.preventDefault();
                confirmVoid();
              }}
              disabled={voidSale.isPending}
              className="bg-neg text-white hover:bg-neg/90"
            >
              {voidSale.isPending ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  Anulando…
                </>
              ) : (
                <>Anular</>
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

function Stat({
  label,
  value,
  hint,
  mono,
}: {
  label: string;
  value: string;
  hint?: string;
  mono?: boolean;
}) {
  return (
    <div className="px-5 py-3">
      <p className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
        {label}
      </p>
      <p className={cn("text-lg font-semibold", mono && "font-mono tabular-nums")}>
        {value}
      </p>
      {hint ? <p className="text-[11px] text-text-tertiary">{hint}</p> : null}
    </div>
  );
}

function TableSkeleton() {
  return (
    <div className="overflow-hidden rounded-xl border border-border-subtle bg-bg-surface shadow-card">
      <div className="space-y-2 p-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-11 w-full rounded-md" />
        ))}
      </div>
    </div>
  );
}

function PaymentBadge({ sale }: { sale: SaleResponse }) {
  const isCredit = sale.payment_type === "Credito";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium",
        isCredit
          ? "bg-warn-soft text-warn"
          : "bg-pos-soft text-pos",
      )}
    >
      {isCredit ? "Crédito" : "Contado"}
      {sale.payment_method ? (
        <span className="text-text-tertiary">· {sale.payment_method}</span>
      ) : null}
    </span>
  );
}

function SalesTable({
  rows,
  expanded,
  toggleExpand,
  canEdit,
  canVoid,
  onVoid,
  isVoidPending,
  hideCustomer = false,
  hideItems = false,
}: {
  rows: SaleResponse[];
  expanded: Set<number>;
  toggleExpand: (id: number) => void;
  canEdit: boolean;
  canVoid: boolean;
  onVoid: (sale: SaleResponse) => void;
  isVoidPending: boolean;
  hideCustomer?: boolean;
  hideItems?: boolean;
}) {
  return (
    <div className="animate-fade-in-up">
      {/* Mobile: cards */}
      <ul className="space-y-3 md:hidden">
        {rows.map((s) => (
          <SaleCard
            key={s.id}
            sale={s}
            isOpen={expanded.has(s.id)}
            onToggle={() => toggleExpand(s.id)}
            canEdit={canEdit}
            canVoid={canVoid}
            onVoid={onVoid}
            isVoidPending={isVoidPending}
            hideCustomer={hideCustomer}
            hideItems={hideItems}
          />
        ))}
      </ul>

      {/* Desktop/tablet: tabla */}
      <div className="hidden overflow-hidden rounded-xl border border-border-subtle bg-bg-surface shadow-card md:block">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border-subtle bg-bg-sunken/60 text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
              <th className="w-8 px-3 py-2.5"></th>
              <th className="px-3 py-2.5 text-left">Fecha</th>
              {hideCustomer ? null : <th className="px-3 py-2.5 text-left">Cliente</th>}
              <th className="px-3 py-2.5 text-left">Vehículo</th>
              {hideItems ? null : <th className="px-3 py-2.5 text-left">Items</th>}
              <th className="px-3 py-2.5 text-left">Cobro</th>
              <th className="px-3 py-2.5 text-right">Total</th>
              <th className="px-3 py-2.5 text-right"></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((s) => {
              const isOpen = expanded.has(s.id);
              return (
                <Row
                  key={s.id}
                  sale={s}
                  isOpen={isOpen}
                  onToggle={() => toggleExpand(s.id)}
                  canEdit={canEdit}
                  canVoid={canVoid}
                  onVoid={onVoid}
                  isVoidPending={isVoidPending}
                  hideCustomer={hideCustomer}
                  hideItems={hideItems}
                />
              );
            })}
          </tbody>
        </table>
        </div>
      </div>
    </div>
  );
}

function SaleCard({
  sale,
  isOpen,
  onToggle,
  canEdit,
  canVoid,
  onVoid,
  isVoidPending,
  hideCustomer = false,
  hideItems = false,
}: {
  sale: SaleResponse;
  isOpen: boolean;
  onToggle: () => void;
  canEdit: boolean;
  canVoid: boolean;
  onVoid: (sale: SaleResponse) => void;
  isVoidPending: boolean;
  hideCustomer?: boolean;
  hideItems?: boolean;
}) {
  return (
    <li
      className={cn(
        "rounded-xl border border-border-subtle bg-bg-surface shadow-card",
        sale.is_voided && "opacity-60",
      )}
    >
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-start justify-between gap-3 p-4 text-left"
        aria-expanded={isOpen}
      >
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 text-[11px] text-text-tertiary">
            <CalendarDays size={12} />
            <span className="font-mono tabular-nums">{formatDate(sale.date)}</span>
            <span>·</span>
            <span>#{sale.id}</span>
          </div>
          {hideCustomer ? null : (
            <p className="mt-1 truncate font-medium">{sale.customer_name}</p>
          )}
          {hideItems ? null : (
            <div className="truncate text-xs">
              <ItemsSummary sale={sale} />
            </div>
          )}
          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            <PaymentBadge sale={sale} />
            {sale.license_plate ? <LicensePlate plate={sale.license_plate} size="xs" /> : null}
            {sale.is_voided ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-neg-soft px-2 py-0.5 text-[11px] font-medium text-neg">
                <CircleSlash size={11} /> Anulada
              </span>
            ) : null}
          </div>
        </div>
        <div className="flex flex-col items-end gap-1">
          <span className="font-mono text-base font-semibold tabular-nums">
            {formatMoney(sale.total)}
          </span>
          {isOpen ? (
            <ChevronDown size={16} className="text-text-tertiary" />
          ) : (
            <ChevronRight size={16} className="text-text-tertiary" />
          )}
        </div>
      </button>

      {isOpen ? (
        <div className="space-y-3 border-t border-border-subtle px-4 py-3">
          <ul className="divide-y divide-border-subtle rounded-lg border border-border-subtle">
            {sale.items.map((it) => (
              <li
                key={it.id}
                className="flex items-baseline justify-between gap-2 px-3 py-2 text-sm"
              >
                <span className="truncate">
                  <span className="text-[10px] uppercase tracking-wider text-text-tertiary">
                    {it.item_type === "Servicio" ? "Servicio" : "Producto"}
                  </span>
                  <span className="ml-2">{it.item_name}</span>
                </span>
                <span className="font-mono tabular-nums text-text-secondary">
                  {it.quantity}× {formatMoney(it.unit_price)}
                </span>
              </li>
            ))}
          </ul>
          {sale.notes ? (
            <p className="text-xs text-text-secondary">
              <span className="font-semibold">Nota:</span> {sale.notes}
            </p>
          ) : null}
          <p className="text-[11px] text-text-tertiary">
            Registrada por {sale.created_by}
            {sale.created_at ? ` · ${formatDate(sale.created_at)}` : ""}
          </p>
          <div className="flex items-center gap-2">
            {canEdit && !sale.is_voided ? (
              <a
                href={`/sales/edit?id=${sale.id}`}
                className="inline-flex h-9 flex-1 items-center justify-center gap-1.5 rounded-md border border-border-subtle text-sm font-medium text-text-secondary hover:bg-bg-sunken"
              >
                <Pencil size={14} /> Editar
              </a>
            ) : null}
            {canVoid && !sale.is_voided ? (
              <button
                type="button"
                disabled={isVoidPending}
                onClick={() => onVoid(sale)}
                className="inline-flex h-9 flex-1 items-center justify-center gap-1.5 rounded-md border border-border-subtle text-sm font-medium text-neg hover:bg-neg-soft disabled:opacity-50"
              >
                <Trash2 size={14} /> Anular
              </button>
            ) : null}
          </div>
        </div>
      ) : null}
    </li>
  );
}

function Row({
  sale,
  isOpen,
  onToggle,
  canEdit,
  canVoid,
  onVoid,
  isVoidPending,
  hideCustomer = false,
  hideItems = false,
}: {
  sale: SaleResponse;
  isOpen: boolean;
  onToggle: () => void;
  canEdit: boolean;
  canVoid: boolean;
  onVoid: (sale: SaleResponse) => void;
  isVoidPending: boolean;
  hideCustomer?: boolean;
  hideItems?: boolean;
}) {
  return (
    <>
      <tr
        className={cn(
          "border-b border-border-subtle transition-colors duration-150 hover-any:bg-accent-soft/60",
          sale.is_voided && "opacity-60",
        )}
      >
        <td className="px-3 py-2.5">
          <button
            type="button"
            onClick={onToggle}
            className="grid h-7 w-7 place-items-center rounded-md text-text-tertiary hover:bg-bg-sunken hover:text-text-primary"
            aria-label={isOpen ? "Colapsar" : "Expandir"}
          >
            {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </button>
        </td>
        <td className="whitespace-nowrap px-3 py-2.5">
          <div className="flex items-center gap-2">
            <CalendarDays size={14} className="text-text-tertiary" />
            <span className="font-mono text-xs tabular-nums">{formatDate(sale.date)}</span>
          </div>
          <p className="ml-5 text-[11px] text-text-tertiary">#{sale.id}</p>
        </td>
        {hideCustomer ? null : (
          <td className="px-3 py-2.5">
            <p className="truncate font-medium">{sale.customer_name}</p>
            {sale.ruc_ci ? (
              <p className="text-[11px] text-text-tertiary">{sale.ruc_ci}</p>
            ) : null}
          </td>
        )}
        <td className="px-3 py-2.5">
          {sale.license_plate ? (
            <div className="flex flex-col items-start gap-0.5">
              <LicensePlate plate={sale.license_plate} size="sm" />
              {sale.vehicle_type_name ? (
                <p className="text-[11px] text-text-tertiary">{sale.vehicle_type_name}</p>
              ) : null}
            </div>
          ) : (
            <span className="text-text-tertiary">—</span>
          )}
        </td>
        {hideItems ? null : (
          <td className="max-w-[260px] px-3 py-2.5">
            <ItemsSummary sale={sale} />
          </td>
        )}
        <td className="px-3 py-2.5">
          <div className="flex flex-col items-start gap-1">
            <PaymentBadge sale={sale} />
            {sale.is_voided ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-neg-soft px-2 py-0.5 text-[11px] font-medium text-neg">
                <CircleSlash size={11} /> Anulada
              </span>
            ) : null}
            {sale.requires_invoice ? (
              <span className="text-[10px] uppercase tracking-wider text-text-tertiary">
                Con factura
              </span>
            ) : null}
          </div>
        </td>
        <td className="px-3 py-2.5 text-right">
          <span className="font-mono text-sm font-semibold tabular-nums">
            {formatMoney(sale.total)}
          </span>
        </td>
        <td className="px-3 py-2.5 text-right">
          <div className="inline-flex items-center gap-1">
            {canEdit && !sale.is_voided ? (
              <a
                href={`/sales/edit?id=${sale.id}`}
                className="grid h-7 w-7 place-items-center rounded-md text-text-tertiary hover:bg-bg-sunken hover:text-text-primary"
                aria-label="Editar"
                title="Editar"
              >
                <Pencil size={13} />
              </a>
            ) : null}
            {canVoid && !sale.is_voided ? (
              <button
                type="button"
                disabled={isVoidPending}
                onClick={() => onVoid(sale)}
                className="grid h-7 w-7 place-items-center rounded-md text-text-tertiary hover:bg-neg-soft hover:text-neg disabled:opacity-50"
                aria-label="Anular"
                title="Anular"
              >
                <Trash2 size={13} />
              </button>
            ) : null}
          </div>
        </td>
      </tr>
      {isOpen ? (
        <tr className="bg-bg-sunken/40">
          <td></td>
          <td
            colSpan={7 - (hideCustomer ? 1 : 0) - (hideItems ? 1 : 0)}
            className="px-3 py-3"
          >
            <div className="space-y-2">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
                Detalle
              </p>
              <ul className="divide-y divide-border-subtle rounded-lg border border-border-subtle bg-bg-surface">
                {sale.items.map((it) => (
                  <li
                    key={it.id}
                    className="grid grid-cols-12 items-center gap-2 px-3 py-2 text-sm"
                  >
                    <span className="col-span-6 truncate">
                      <span className="text-[10px] uppercase tracking-wider text-text-tertiary">
                        {it.item_type === "Servicio" ? "Servicio" : "Producto"}
                      </span>
                      <span className="ml-2">{it.item_name}</span>
                    </span>
                    <span className="col-span-2 text-center text-text-secondary">
                      {it.quantity}× {formatMoney(it.unit_price)}
                    </span>
                    <span className="col-span-4 text-right font-mono tabular-nums">
                      {formatMoney(it.subtotal)}
                    </span>
                  </li>
                ))}
              </ul>
              {sale.notes ? (
                <p className="text-xs text-text-secondary">
                  <span className="font-semibold">Nota:</span> {sale.notes}
                </p>
              ) : null}
              <p className="text-[11px] text-text-tertiary">
                Registrada por {sale.created_by}
                {sale.created_at ? ` · ${formatDate(sale.created_at)}` : ""}
              </p>
            </div>
          </td>
        </tr>
      ) : null}
    </>
  );
}

export function MovementsView() {
  return (
    <Shell activeKey="movements" title="Movimientos" subtitle="Operación · Ventas">
      <MovementsInner />
    </Shell>
  );
}

function ActiveFilterChip({
  label,
  onRemove,
}: {
  label: string;
  onRemove: () => void;
}) {
  return (
    <span className="inline-flex max-w-[220px] items-center gap-1 rounded-full bg-accent-soft px-2 py-0.5 text-[11px] font-medium text-accent">
      <span className="truncate">{label}</span>
      <button
        type="button"
        onClick={onRemove}
        className="rounded-full p-0.5 hover:bg-accent/15"
        aria-label={`Quitar filtro ${label}`}
      >
        <X size={10} />
      </button>
    </span>
  );
}

function RazonSocialFilter({
  options,
  selected,
  onChange,
  exclude,
  onExcludeChange,
}: {
  options: string[];
  selected: string[];
  onChange: (next: string[]) => void;
  exclude: boolean;
  onExcludeChange: (next: boolean) => void;
}) {
  const [open, setOpen] = useState(false);
  const [filterText, setFilterText] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);

  // Click afuera cierra el panel.
  useEffect(() => {
    if (!open) return;
    function onClickAway(e: MouseEvent) {
      if (!containerRef.current?.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClickAway);
    return () => document.removeEventListener("mousedown", onClickAway);
  }, [open]);

  const visibleOptions = useMemo(() => {
    const term = filterText.trim().toLowerCase();
    if (!term) return options;
    return options.filter((o) => o.toLowerCase().includes(term));
  }, [filterText, options]);

  const toggle = (name: string) => {
    if (selected.includes(name)) {
      onChange(selected.filter((s) => s !== name));
    } else {
      onChange([...selected, name]);
    }
  };

  const triggerLabel =
    selected.length === 0
      ? "Todas"
      : selected.length === 1
        ? selected[0]
        : `${selected.length} seleccionadas`;

  return (
    <div ref={containerRef} className="relative flex min-w-[200px] flex-1 flex-col gap-1 sm:flex-none">
      <label className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
        Razón social
      </label>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        disabled={options.length === 0}
        className={cn(
          "flex h-9 items-center justify-between gap-2 rounded-md border border-border-subtle bg-bg-surface px-3 text-left text-sm",
          "hover:border-border-default focus:border-brand-mint focus:outline-none disabled:cursor-not-allowed disabled:opacity-60",
          selected.length > 0 && "border-accent",
        )}
        aria-expanded={open}
        aria-haspopup="listbox"
      >
        <span className="flex min-w-0 items-center gap-2">
          <Building2 size={14} className="shrink-0 text-text-tertiary" />
          <span className="truncate">{options.length === 0 ? "Sin facturadas" : triggerLabel}</span>
        </span>
        <ChevronDown size={14} className="shrink-0 text-text-tertiary" />
      </button>

      {open ? (
        <div
          className="absolute left-0 top-full z-20 mt-1 w-[280px] overflow-hidden rounded-md border border-border-subtle bg-bg-surface shadow-lg"
          role="listbox"
        >
          <div className="border-b border-border-subtle p-2">
            <Input
              autoFocus
              placeholder="Filtrar..."
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              className="h-8 text-xs"
            />
          </div>
          <ul className="max-h-[240px] overflow-y-auto py-1">
            {visibleOptions.length === 0 ? (
              <li className="px-3 py-2 text-xs text-text-tertiary">Sin resultados.</li>
            ) : (
              visibleOptions.map((name) => {
                const checked = selected.includes(name);
                return (
                  <li key={name}>
                    <label className="flex cursor-pointer items-center gap-2 px-3 py-1.5 text-sm hover:bg-bg-sunken">
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggle(name)}
                        className="size-3.5 accent-accent"
                      />
                      <span className="truncate">{name}</span>
                    </label>
                  </li>
                );
              })
            )}
          </ul>
          {selected.length > 0 ? (
            <div className="flex items-center justify-between border-t border-border-subtle px-3 py-2">
              <label className="flex cursor-pointer items-center gap-2 text-xs text-text-secondary">
                <input
                  type="checkbox"
                  checked={exclude}
                  onChange={(e) => onExcludeChange(e.target.checked)}
                  className="size-3.5 accent-accent"
                />
                Excluir seleccionadas
              </label>
              <button
                type="button"
                onClick={() => {
                  onChange([]);
                  onExcludeChange(false);
                }}
                className="text-xs text-text-tertiary hover:text-text-primary"
              >
                Limpiar
              </button>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
