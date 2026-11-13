/**
 * Iter 3 — Nueva venta.
 *
 * Layout de punto de venta:
 *  - Izquierda: catálogo de servicios y productos en tiles. Cada tile muestra
 *    cuántas unidades ya están en la venta.
 *  - Derecha (sticky en desktop): ticket con ítems editables, vehículo
 *    (solo si hay servicio), cobro, factura, observación, total y "Cobrar".
 *  - Mobile: el ticket va debajo del catálogo y el total + CTA quedan en una
 *    barra fija inferior.
 *
 * Submit: POST /sales (useCreateSale) → toast + redirect a /dashboard.
 */

import { zodResolver } from "@hookform/resolvers/zod";
import {
  Banknote,
  CreditCard,
  Loader2,
  Minus,
  Plus,
  Smartphone,
  Trash2,
  Wallet,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  Controller,
  useFieldArray,
  useForm,
  useWatch,
  type Control,
  type UseFormReturn,
} from "react-hook-form";
import { toast } from "sonner";
import * as z from "zod";

import { Shell } from "@/components/shell/Shell";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api/client";
import { useProducts, useServices, useVehicleTypes } from "@/lib/api/queries/catalogs";
import { useCreateSale, useUpdateSale } from "@/lib/api/queries/sales";
import { useUpsertVehicle, findVehicleByPlate } from "@/lib/api/queries/vehicles";
import type { components } from "@/lib/api/schema";
import { formatMoney, todayISO } from "@/lib/format";
import { cn } from "@/lib/utils";
import { withBase } from "@/lib/paths";

type CatalogItem = components["schemas"]["CatalogItem"];
type SaleResponse = components["schemas"]["SaleResponse"];

export type SalesFormMode = "create" | "edit";

// ----- schema -----

const itemSchema = z.object({
  kind: z.enum(["service", "product"]),
  refId: z.number().int().positive(),
  name: z.string(),
  quantity: z.number().int().min(1, "Mínimo 1"),
  // Forzamos precio > 0: no se puede cobrar una venta con líneas en Gs. 0.
  // El UI ya marca la fila en warn antes de submit para guiar al usuario.
  unitPrice: z.number().positive("El precio debe ser mayor a 0"),
});

const formSchema = z
  .object({
    fecha_venta: z.string().min(1, "Requerido"),
    tipo_cobro: z.enum(["Contado", "Credito"]),
    metodo_pago: z.string().optional(),
    observacion: z.string().optional(),
    items: z.array(itemSchema).min(1, "Agregá al menos un servicio o producto"),
    license_plate: z.string().optional(),
    vehicle_type_id: z.number().int().positive().optional(),
    requiere_factura: z.boolean(),
    ruc_ci: z.string().optional(),
    razon_social: z.string().optional(),
  })
  .superRefine((v, ctx) => {
    // Regla: vehiculo acoplado a servicios. Con servicio -> obligatorio,
    // sin servicio -> ni siquiera se puede ingresar.
    const hasService = v.items.some((it) => it.kind === "service");
    if (hasService) {
      if (!v.license_plate || v.license_plate.trim() === "") {
        ctx.addIssue({
          path: ["license_plate"],
          code: z.ZodIssueCode.custom,
          message: "Ingresá la placa",
        });
      }
      if (!v.vehicle_type_id) {
        ctx.addIssue({
          path: ["vehicle_type_id"],
          code: z.ZodIssueCode.custom,
          message: "Seleccioná un tipo",
        });
      }
    }
    if (v.requiere_factura) {
      if (!v.ruc_ci || v.ruc_ci.trim() === "") {
        ctx.addIssue({
          path: ["ruc_ci"],
          code: z.ZodIssueCode.custom,
          message: "Requerido para factura",
        });
      }
      if (!v.razon_social || v.razon_social.trim() === "") {
        ctx.addIssue({
          path: ["razon_social"],
          code: z.ZodIssueCode.custom,
          message: "Requerido para factura",
        });
      }
    }
  });

type FormValues = z.infer<typeof formSchema>;

export function saleToFormValues(sale: SaleResponse): FormValues {
  return {
    fecha_venta: sale.date,
    tipo_cobro: sale.payment_type === "Credito" ? "Credito" : "Contado",
    metodo_pago: sale.payment_method ?? "Efectivo",
    observacion: sale.notes ?? "",
    items: sale.items.map((it) => ({
      kind: it.item_type === "Servicio" ? "service" : "product",
      refId: (it.service_id ?? it.product_id) as number,
      name: it.item_name,
      quantity: it.quantity,
      unitPrice: it.unit_price,
    })),
    license_plate: sale.license_plate ?? "",
    vehicle_type_id: sale.vehicle_type_id ?? undefined,
    requiere_factura: sale.requires_invoice,
    ruc_ci: sale.ruc_ci ?? "",
    razon_social: sale.requires_invoice ? sale.customer_name : "",
  };
}

const PAYMENT_METHODS = [
  { value: "Efectivo", label: "Efectivo", icon: Banknote },
  { value: "Tarjeta", label: "Tarjeta", icon: CreditCard },
  { value: "Transferencia", label: "Transferencia", icon: Wallet },
  { value: "QR", label: "QR / Billetera", icon: Smartphone },
] as const;

// ----- helpers UI -----

function SegmentedField<T extends string | number>({
  options,
  value,
  onChange,
  ariaLabel,
  columns,
}: {
  options: { value: T; label: string; icon?: React.ComponentType<{ size?: number; className?: string }> }[];
  value: T | undefined;
  onChange: (v: T) => void;
  ariaLabel?: string;
  columns?: 2 | 4;
}) {
  return (
    <div
      role="radiogroup"
      aria-label={ariaLabel}
      className={cn(
        "grid gap-0.5 rounded-md border border-border-default bg-bg-sunken p-0.5",
        columns === 4 ? "grid-cols-2 sm:grid-cols-4 lg:grid-cols-2" : "grid-cols-2",
      )}
    >
      {options.map((opt) => {
        const active = value === opt.value;
        const Icon = opt.icon;
        return (
          <button
            key={String(opt.value)}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(opt.value)}
            className={cn(
              "inline-flex h-8 items-center justify-center gap-1.5 rounded-[5px] px-2 text-[13px] transition-colors",
              active
                ? "bg-white font-medium text-text-primary shadow-[0_0_0_1px_var(--color-border-default),0_1px_2px_0_rgb(0_0_0/0.06)] dark:bg-white/12"
                : "text-text-secondary hover-any:text-text-primary",
            )}
          >
            {Icon ? (
              <Icon size={14} className={active ? "text-accent" : "text-text-tertiary"} />
            ) : null}
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

function CatalogTile({
  item,
  quantity,
  onAdd,
}: {
  item: CatalogItem;
  quantity: number;
  onAdd: (item: CatalogItem) => void;
}) {
  const inCart = quantity > 0;
  return (
    <button
      type="button"
      onClick={() => onAdd(item)}
      className={cn(
        "relative flex min-h-[76px] flex-col justify-between gap-2 rounded-lg border bg-bg-surface p-3 text-left transition-[border-color,background-color,box-shadow] duration-150",
        "active:bg-bg-sunken",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40",
        inCart
          ? "border-accent shadow-[0_0_0_1px_var(--color-accent)]"
          : "border-border-default hover-any:border-border-strong hover-any:bg-white/75 dark:hover-any:bg-white/[0.09]",
      )}
    >
      <span className="line-clamp-2 pr-6 text-[13px] font-medium leading-snug">{item.name}</span>
      <span className="text-[13px] tabular-nums text-text-secondary">
        {formatMoney(item.price ?? 0)}
      </span>
      {inCart ? (
        <span className="absolute right-2 top-2 grid h-5 min-w-5 place-items-center rounded-full bg-accent px-1.5 text-[11px] font-semibold tabular-nums text-white dark:text-bg-app">
          {quantity}
        </span>
      ) : null}
    </button>
  );
}

function CatalogGrid({
  title,
  items,
  loading,
  emptyLabel,
  quantities,
  onAdd,
}: {
  title: string;
  items: CatalogItem[] | undefined;
  loading: boolean;
  emptyLabel: string;
  quantities: Map<number, number>;
  onAdd: (item: CatalogItem) => void;
}) {
  return (
    <section>
      <h2 className="mb-2 flex items-baseline justify-between text-[13px] font-medium text-text-secondary">
        {title}
        {items && items.length > 0 ? (
          <span className="text-xs font-normal text-text-tertiary">{items.length}</span>
        ) : null}
      </h2>
      {loading ? (
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-[76px] rounded-lg" />
          ))}
        </div>
      ) : !items || items.length === 0 ? (
        <p className="rounded-lg border border-dashed border-border-default px-4 py-6 text-[13px] text-text-tertiary">
          {emptyLabel}
        </p>
      ) : (
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-4">
          {items.map((it) => (
            <CatalogTile
              key={it.id}
              item={it}
              quantity={quantities.get(it.id) ?? 0}
              onAdd={onAdd}
            />
          ))}
        </div>
      )}
    </section>
  );
}

/** Bloque del ticket: separador superior + título chico opcional. */
function TicketBlock({
  title,
  right,
  children,
}: {
  title?: string;
  right?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="border-t border-border-subtle px-4 py-3.5">
      {title || right ? (
        <div className="mb-2.5 flex items-center justify-between gap-2">
          {title ? <p className="text-xs font-medium text-text-secondary">{title}</p> : <span />}
          {right}
        </div>
      ) : null}
      {children}
    </div>
  );
}

function ItemsList({
  control,
  fields,
  remove,
  setValue,
}: {
  control: Control<FormValues>;
  // Pasamos `fields` desde el padre (instancia única de useFieldArray) para
  // que React reciba `key` estable por fila. Esto evita que las celdas se
  // desincronicen cuando se elimina una fila intermedia y al mismo tiempo
  // no rompe la propagación de inserts desde el padre.
  fields: { id: string }[];
  remove: (index: number) => void;
  setValue: UseFormReturn<FormValues>["setValue"];
}) {
  const watched = useWatch({ control, name: "items" }) ?? [];
  if (fields.length === 0) {
    return (
      <p className="px-4 py-8 text-center text-[13px] text-text-tertiary">
        Tocá un servicio o producto para empezar la venta.
      </p>
    );
  }
  return (
    <ul className="divide-y divide-border-subtle">
      {fields.map((field, i) => {
        const it = watched[i] ?? field;
        const subtotal = (it.quantity || 0) * (it.unitPrice || 0);
        const isZeroPrice = (Number(it.unitPrice) || 0) <= 0;
        return (
          <li key={field.id} className={cn("px-4 py-2.5", isZeroPrice && "bg-warn-soft/50")}>
            <div className="flex items-baseline justify-between gap-3">
              <p className="min-w-0 truncate text-[13px] font-medium">
                {it.name}
                <span className="ml-1.5 text-[11px] font-normal text-text-tertiary">
                  {it.kind === "service" ? "Servicio" : "Producto"}
                </span>
              </p>
              <span
                className={cn(
                  "shrink-0 text-[13px] font-medium tabular-nums",
                  isZeroPrice && "text-warn-fg",
                )}
              >
                {formatMoney(subtotal)}
              </span>
            </div>

            <div className="mt-1.5 flex items-center gap-2">
              <div className="inline-flex h-7 items-center rounded-md border border-border-default">
                <button
                  type="button"
                  className="grid h-full w-7 place-items-center text-text-secondary hover:text-text-primary disabled:opacity-40"
                  disabled={(it.quantity || 1) <= 1}
                  onClick={() =>
                    setValue(`items.${i}.quantity`, Math.max(1, (it.quantity || 1) - 1), {
                      shouldValidate: true,
                    })
                  }
                  aria-label="Disminuir"
                >
                  <Minus size={12} />
                </button>
                <Controller
                  control={control}
                  name={`items.${i}.quantity`}
                  render={({ field }) => (
                    <input
                      type="number"
                      inputMode="numeric"
                      min={1}
                      aria-label="Cantidad"
                      value={field.value ?? 1}
                      onChange={(e) => field.onChange(Number(e.target.value) || 1)}
                      className="h-full w-9 border-x border-border-default bg-transparent text-center text-[13px] tabular-nums [appearance:textfield] focus:outline-none [&::-webkit-inner-spin-button]:appearance-none"
                    />
                  )}
                />
                <button
                  type="button"
                  className="grid h-full w-7 place-items-center text-text-secondary hover:text-text-primary"
                  onClick={() =>
                    setValue(`items.${i}.quantity`, (it.quantity || 1) + 1, {
                      shouldValidate: true,
                    })
                  }
                  aria-label="Aumentar"
                >
                  <Plus size={12} />
                </button>
              </div>

              <span className="text-xs text-text-tertiary">×</span>

              <Controller
                control={control}
                name={`items.${i}.unitPrice`}
                render={({ field }) => (
                  <input
                    type="number"
                    inputMode="numeric"
                    min={0}
                    step={1}
                    aria-label="Precio unitario"
                    value={field.value ?? 0}
                    onChange={(e) => field.onChange(Number(e.target.value) || 0)}
                    aria-invalid={isZeroPrice}
                    title={isZeroPrice ? "Precio en 0. Editá antes de cobrar." : undefined}
                    className={cn(
                      "h-7 w-24 rounded-md border bg-bg-field px-2 text-right text-[13px] tabular-nums [appearance:textfield] focus:outline-none [&::-webkit-inner-spin-button]:appearance-none",
                      isZeroPrice
                        ? "border-warn text-warn-fg focus:border-warn"
                        : "border-border-default focus:border-accent",
                    )}
                  />
                )}
              />

              <button
                type="button"
                onClick={() => remove(i)}
                className="ml-auto inline-flex h-7 w-7 items-center justify-center rounded-md text-text-tertiary hover:bg-neg-soft hover:text-neg"
                aria-label="Quitar"
              >
                <Trash2 size={14} />
              </button>
            </div>
          </li>
        );
      })}
    </ul>
  );
}

/** Observación: colapsada por defecto (casi nunca se usa), abierta si ya trae texto. */
function NoteField({ control }: { control: Control<FormValues> }) {
  const initial = useWatch({ control, name: "observacion" });
  const [open, setOpen] = useState(Boolean(initial));
  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="inline-flex items-center gap-1 text-[13px] text-text-secondary hover:text-text-primary"
      >
        <Plus size={14} />
        Agregar observación
      </button>
    );
  }
  return (
    <FormField
      control={control}
      name="observacion"
      render={({ field }) => (
        <FormItem>
          <FormLabel className="text-xs font-medium text-text-secondary">Observación</FormLabel>
          <FormControl>
            <textarea
              {...field}
              rows={2}
              placeholder="Notas internas opcionales…"
              className="w-full rounded-md border border-border-default bg-bg-field px-3 py-2 text-[13px] focus:border-accent focus:outline-none"
            />
          </FormControl>
        </FormItem>
      )}
    />
  );
}

// ----- inner component -----

interface SalesFormInnerProps {
  mode: SalesFormMode;
  saleId?: number;
  defaultValues?: FormValues;
}

function SalesFormInner({ mode, saleId, defaultValues }: SalesFormInnerProps) {
  const services = useServices(true);
  const products = useProducts(true);
  const vehicleTypes = useVehicleTypes(true);
  const createSale = useCreateSale();
  const updateSale = useUpdateSale(saleId ?? 0);
  const upsertVehicle = useUpsertVehicle();

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: defaultValues ?? {
      fecha_venta: todayISO(),
      tipo_cobro: "Contado",
      metodo_pago: "Efectivo",
      observacion: "",
      items: [],
      license_plate: "",
      vehicle_type_id: undefined,
      requiere_factura: false,
      ruc_ci: "",
      razon_social: "",
    },
    mode: "onSubmit",
  });

  const itemsField = useFieldArray({ control: form.control, name: "items" });
  const watchedItems = useWatch({ control: form.control, name: "items" }) ?? [];
  const tipoCobro = useWatch({ control: form.control, name: "tipo_cobro" });
  const requiereFactura = useWatch({ control: form.control, name: "requiere_factura" });

  // Regla de cobranza: no se puede cobrar una venta con líneas en Gs. 0.
  // El UI ya marca cada fila afectada en warn; aca derivamos el flag para
  // bloquear el boton "Cobrar" y mostrar el mensaje en el resumen.
  const hasZeroPrice =
    watchedItems.length > 0 &&
    watchedItems.some((it) => (Number(it?.unitPrice) || 0) <= 0);

  // Vehiculo acoplado a servicios: si no hay servicios en el detalle,
  // limpiamos placa y tipo automaticamente para mantener el estado coherente
  // con la regla del backend.
  const hasService = watchedItems.some((it) => it?.kind === "service");
  useEffect(() => {
    if (!hasService) {
      const plate = form.getValues("license_plate");
      const typeId = form.getValues("vehicle_type_id");
      if (plate) form.setValue("license_plate", "", { shouldValidate: false });
      if (typeId !== undefined) form.setValue("vehicle_type_id", undefined, { shouldValidate: false });
    }
  }, [hasService, form]);

  const total = useMemo(
    () =>
      watchedItems.reduce(
        (acc, it) => acc + (Number(it?.quantity) || 0) * (Number(it?.unitPrice) || 0),
        0,
      ),
    [watchedItems],
  );

  const addCatalogItem = (item: CatalogItem, kind: "service" | "product") => {
    const current = form.getValues("items") ?? [];
    const idx = current.findIndex(
      (it) => it.kind === kind && it.refId === item.id,
    );
    if (idx >= 0) {
      const cur = current[idx];
      form.setValue(`items.${idx}.quantity`, (cur.quantity || 0) + 1, {
        shouldValidate: true,
      });
    } else {
      itemsField.append({
        kind,
        refId: item.id,
        name: item.name,
        quantity: 1,
        unitPrice: item.price ?? 0,
      });
    }
  };

  const onSubmit = async (values: FormValues) => {
    let vehiculo_id: number | undefined;

    const submitHasService = values.items.some((it) => it.kind === "service");
    if (submitHasService && values.license_plate && values.vehicle_type_id) {
      try {
        const res = await upsertVehicle.mutateAsync({
          license_plate: values.license_plate.trim().toUpperCase(),
          vehicle_type_id: values.vehicle_type_id,
        });
        vehiculo_id = res.id;
      } catch (err) {
        const msg = err instanceof ApiError ? err.message : "No se pudo registrar el vehículo.";
        toast.error("Vehículo", { description: msg });
        return;
      }
    }

    const payload = {
      fecha_venta: values.fecha_venta,
      tipo_cobro: values.tipo_cobro,
      metodo_pago: values.metodo_pago || undefined,
      observacion: values.observacion?.trim() || undefined,
      items: values.items.map((it) => ({
        servicio_id: it.kind === "service" ? it.refId : undefined,
        producto_id: it.kind === "product" ? it.refId : undefined,
        cantidad: it.quantity,
        precio_unitario: it.unitPrice,
      })),
      vehiculo_id,
      requiere_factura: values.requiere_factura,
      ruc_ci: values.requiere_factura ? values.ruc_ci?.trim() : undefined,
      razon_social: values.requiere_factura ? values.razon_social?.trim() : undefined,
    };

    if (mode === "edit" && saleId) {
      updateSale.mutate(payload, {
        onSuccess: () => {
          toast.success("Venta actualizada", {
            description: `#${saleId} · Total ${formatMoney(total)}.`,
          });
          window.location.href = withBase("/sales");
        },
        onError: (err) => {
          const msg = err instanceof ApiError ? err.message : "No se pudo actualizar la venta.";
          toast.error("Error al actualizar", { description: msg });
        },
      });
    } else {
      createSale.mutate(payload, {
        onSuccess: () => {
          toast.success("Venta registrada", {
            description: `Total ${formatMoney(total)} cobrado.`,
          });
          window.location.href = withBase("/dashboard");
        },
        onError: (err) => {
          const msg = err instanceof ApiError ? err.message : "No se pudo registrar la venta.";
          toast.error("Error al registrar", { description: msg });
        },
      });
    }
  };

  const isSubmitting =
    createSale.isPending || updateSale.isPending || upsertVehicle.isPending;

  // Cantidad en carrito por item de catálogo, para el contador de cada tile.
  const serviceQty = new Map<number, number>();
  const productQty = new Map<number, number>();
  for (const it of watchedItems) {
    if (!it) continue;
    const map = it.kind === "service" ? serviceQty : productQty;
    map.set(it.refId, (map.get(it.refId) ?? 0) + (Number(it.quantity) || 0));
  }
  const itemCount = watchedItems.reduce((acc, it) => acc + (Number(it?.quantity) || 0), 0);

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="grid gap-6 pb-[96px] lg:grid-cols-[minmax(0,1fr)_380px] lg:items-start lg:gap-5 lg:pb-0"
      >
        {/* Catálogo */}
        <div className="space-y-6">
          <CatalogGrid
            title="Servicios"
            items={services.data}
            loading={services.isLoading}
            emptyLabel="Sin servicios activos. Configurá el catálogo en Ajustes."
            quantities={serviceQty}
            onAdd={(it) => addCatalogItem(it, "service")}
          />
          <CatalogGrid
            title="Productos"
            items={products.data}
            loading={products.isLoading}
            emptyLabel="Sin productos activos."
            quantities={productQty}
            onAdd={(it) => addCatalogItem(it, "product")}
          />
        </div>

        {/* Ticket */}
        <aside className="lg:sticky lg:top-[4.75rem]">
          <div className="flex flex-col overflow-hidden rounded-lg border border-border-default bg-bg-surface lg:max-h-[calc(100svh-6.25rem)]">
            <header className="flex items-center justify-between gap-3 px-4 py-3">
              <div>
                <p className="text-[13px] font-medium">
                  {mode === "edit" ? `Venta #${saleId ?? ""}` : "Venta"}
                </p>
                <p className="text-xs text-text-tertiary">
                  {itemCount > 0 ? `${itemCount} ítem${itemCount === 1 ? "" : "s"}` : "Sin ítems"}
                </p>
              </div>
              <FormField
                control={form.control}
                name="fecha_venta"
                render={({ field }) => (
                  <FormItem className="gap-0">
                    <FormLabel className="sr-only">Fecha</FormLabel>
                    <FormControl>
                      <Input type="date" className="h-8 w-[140px] text-[13px]" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </header>

            <div className="min-h-0 flex-1 overflow-y-auto">
              <div className="border-t border-border-subtle">
                <ItemsList
                  control={form.control}
                  fields={itemsField.fields}
                  remove={itemsField.remove}
                  setValue={form.setValue}
                />
                {form.formState.errors.items?.message ? (
                  <p className="px-4 pb-3 text-xs text-neg">{form.formState.errors.items.message}</p>
                ) : null}
                {hasZeroPrice ? (
                  <p className="mx-4 mb-3 rounded-md border border-warn/40 bg-warn-soft px-3 py-2 text-xs text-warn-fg">
                    Hay ítems con precio en Gs. 0. Editá el precio antes de cobrar.
                  </p>
                ) : null}
              </div>

              {/* Vehículo: acoplado a servicios. */}
              <TicketBlock title="Vehículo">
                {hasService ? (
                  <div className="grid grid-cols-2 gap-2">
                    <FormField
                      control={form.control}
                      name="license_plate"
                      render={({ field }) => (
                        <FormItem className="gap-1">
                          <FormLabel className="text-xs font-normal text-text-tertiary">
                            Placa
                          </FormLabel>
                          <FormControl>
                            <Input
                              placeholder="ABC123"
                              className="h-8 font-mono text-[13px] uppercase tracking-wider"
                              {...field}
                              onChange={(e) => field.onChange(e.target.value.toUpperCase())}
                              onBlur={async (e) => {
                                field.onBlur();
                                const plate = e.target.value.trim().toUpperCase();
                                if (!plate) return;
                                try {
                                  const v = await findVehicleByPlate(plate);
                                  if (v && v.vehicle_type_id) {
                                    form.setValue("vehicle_type_id", v.vehicle_type_id, {
                                      shouldValidate: true,
                                    });
                                    toast.message("Vehículo encontrado", {
                                      description: `${v.license_plate} · ${v.vehicle_type_name ?? ""}`,
                                    });
                                  }
                                } catch {
                                  /* noop */
                                }
                              }}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name="vehicle_type_id"
                      render={({ field }) => (
                        <FormItem className="gap-1">
                          <FormLabel className="text-xs font-normal text-text-tertiary">
                            Tipo de vehículo
                          </FormLabel>
                          <FormControl>
                            <select
                              value={field.value ?? ""}
                              onChange={(e) =>
                                field.onChange(e.target.value ? Number(e.target.value) : undefined)
                              }
                              className="h-8 w-full rounded-md border border-border-default bg-bg-field px-2 text-[13px] focus:border-accent focus:outline-none"
                            >
                              <option value="">Seleccioná…</option>
                              {(vehicleTypes.data ?? []).map((t) => (
                                <option key={t.id} value={t.id}>
                                  {t.name}
                                </option>
                              ))}
                            </select>
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                ) : (
                  <p className="text-[13px] text-text-tertiary">
                    Agregá un servicio al detalle para habilitar el vehículo.
                  </p>
                )}
              </TicketBlock>

              {/* Cobro */}
              <TicketBlock title="Cobro">
                <div className="space-y-2">
                  <Controller
                    control={form.control}
                    name="tipo_cobro"
                    render={({ field }) => (
                      <SegmentedField
                        ariaLabel="Tipo de cobro"
                        value={field.value}
                        onChange={field.onChange}
                        options={[
                          { value: "Contado", label: "Contado" },
                          { value: "Credito", label: "Crédito" },
                        ]}
                      />
                    )}
                  />
                  {tipoCobro === "Contado" ? (
                    <Controller
                      control={form.control}
                      name="metodo_pago"
                      render={({ field }) => (
                        <SegmentedField
                          ariaLabel="Método de pago"
                          columns={4}
                          value={field.value}
                          onChange={field.onChange}
                          options={PAYMENT_METHODS.map((pm) => ({
                            value: pm.value,
                            label: pm.label,
                            icon: pm.icon,
                          }))}
                        />
                      )}
                    />
                  ) : null}
                </div>
              </TicketBlock>

              {/* Factura */}
              <TicketBlock
                title="Factura"
                right={
                  <Controller
                    control={form.control}
                    name="requiere_factura"
                    render={({ field }) => (
                      <ToggleSwitch
                        checked={field.value}
                        onCheckedChange={field.onChange}
                        label="Requiere factura"
                      />
                    )}
                  />
                }
              >
                {requiereFactura ? (
                  <div className="grid grid-cols-2 gap-2">
                    <FormField
                      control={form.control}
                      name="ruc_ci"
                      render={({ field }) => (
                        <FormItem className="gap-1">
                          <FormLabel className="text-xs font-normal text-text-tertiary">
                            RUC / CI
                          </FormLabel>
                          <FormControl>
                            <Input placeholder="80012345-6" className="h-8 text-[13px]" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name="razon_social"
                      render={({ field }) => (
                        <FormItem className="gap-1">
                          <FormLabel className="text-xs font-normal text-text-tertiary">
                            Razón social
                          </FormLabel>
                          <FormControl>
                            <Input placeholder="Cliente S.A." className="h-8 text-[13px]" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                ) : (
                  <p className="text-[13px] text-text-tertiary">Sin factura.</p>
                )}
              </TicketBlock>

              <TicketBlock>
                <NoteField control={form.control} />
              </TicketBlock>
            </div>

            {/* Total + CTA (desktop). En mobile lo hace la barra inferior. */}
            <TicketFooter
              total={total}
              hasItems={watchedItems.length > 0}
              isSubmitting={isSubmitting}
              mode={mode}
              hasZeroPrice={hasZeroPrice}
            />
          </div>
        </aside>

        <MobileSummaryBar
          total={total}
          itemCount={itemCount}
          isSubmitting={isSubmitting}
          mode={mode}
          hasZeroPrice={hasZeroPrice}
        />
      </form>
    </Form>
  );
}

function submitClasses(enabled: boolean) {
  return enabled
    ? "bg-accent text-white hover:bg-accent-hover dark:text-bg-app"
    : "border border-border-default bg-bg-sunken text-text-tertiary disabled:opacity-100";
}

function TicketFooter({
  total,
  hasItems,
  isSubmitting,
  mode,
  hasZeroPrice,
}: {
  total: number;
  hasItems: boolean;
  isSubmitting: boolean;
  mode: SalesFormMode;
  hasZeroPrice: boolean;
}) {
  const ctaLabel = mode === "edit" ? "Guardar cambios" : `Cobrar ${formatMoney(total)}`;
  const submittingLabel = mode === "edit" ? "Guardando…" : "Registrando…";
  const blockedByZero = hasZeroPrice && mode !== "edit";
  const enabled = !isSubmitting && hasItems && !blockedByZero;
  return (
    <div className="hidden border-t border-border-default bg-white/25 px-4 py-4 dark:bg-white/[0.02] lg:block">
      <div className="flex items-baseline justify-between">
        <span className="text-[13px] text-text-secondary">Total</span>
        <span
          className={cn(
            "text-[26px] font-semibold leading-none tracking-tight tabular-nums",
            total > 0 ? "text-text-primary" : "text-text-tertiary",
          )}
        >
          {formatMoney(total)}
        </span>
      </div>
      <Button
        type="submit"
        size="lg"
        disabled={!enabled}
        className={cn("mt-4 h-11 w-full text-[15px] font-medium", submitClasses(enabled || isSubmitting))}
      >
        {isSubmitting ? (
          <>
            <Loader2 className="animate-spin" />
            {submittingLabel}
          </>
        ) : (
          <>{ctaLabel}</>
        )}
      </Button>
    </div>
  );
}

/**
 * Total + CTA en mobile/tablet, fijo al fondo con safe-area.
 * El detalle ya está visible en el ticket (debajo del catálogo), así que no
 * hace falta drawer.
 */
function MobileSummaryBar({
  total,
  itemCount,
  isSubmitting,
  mode,
  hasZeroPrice,
}: {
  total: number;
  itemCount: number;
  isSubmitting: boolean;
  mode: SalesFormMode;
  hasZeroPrice: boolean;
}) {
  const blockedByZero = hasZeroPrice && mode !== "edit";
  const ctaLabel =
    mode === "edit"
      ? "Guardar"
      : itemCount === 0
        ? "Sin ítems"
        : blockedByZero
          ? "Precio en 0"
          : `Cobrar ${formatMoney(total)}`;
  const submittingLabel = mode === "edit" ? "Guardando…" : "Registrando…";
  const enabled = !isSubmitting && itemCount > 0 && !blockedByZero;

  return (
    <div className="fixed inset-x-0 bottom-0 z-50 border-t border-border-default glass-bar pb-[env(safe-area-inset-bottom)] lg:hidden">
      <div className="flex items-center gap-3 px-4 py-3">
        <div className="min-w-0 flex-1">
          <p className="text-xs text-text-tertiary">
            Total{itemCount > 0 ? ` · ${itemCount} ítem${itemCount === 1 ? "" : "s"}` : ""}
          </p>
          <p className="text-lg font-semibold leading-tight tabular-nums">{formatMoney(total)}</p>
        </div>
        <Button
          type="submit"
          size="lg"
          disabled={!enabled}
          className={cn("h-11 min-w-[150px] font-medium", submitClasses(enabled || isSubmitting))}
        >
          {isSubmitting ? (
            <>
              <Loader2 className="animate-spin" />
              {submittingLabel}
            </>
          ) : (
            <>{ctaLabel}</>
          )}
        </Button>
      </div>
    </div>
  );
}

function ToggleSwitch({
  checked,
  onCheckedChange,
  label,
}: {
  checked: boolean;
  onCheckedChange: (v: boolean) => void;
  label: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onCheckedChange(!checked)}
      className={cn(
        "inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors",
        checked ? "bg-accent" : "bg-border-strong",
      )}
    >
      <span
        className={cn(
          "ml-0.5 h-4 w-4 rounded-full bg-white shadow-sm transition-transform",
          checked ? "translate-x-4" : "translate-x-0",
        )}
      />
    </button>
  );
}

export { SalesFormInner };

export function SalesNewView() {
  return (
    <Shell activeKey="sales_form" title="Nueva venta" subtitle="Operación · Ventas">
      <SalesFormInner mode="create" />
    </Shell>
  );
}
