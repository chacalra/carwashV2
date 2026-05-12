/**
 * Iter 3 — Nueva venta.
 *
 * Layout 2 columnas:
 *  - Izquierda: cabecera (fecha, tipo de cobro, método de pago) + tile grids
 *    de servicios/productos + items agregados + vehículo opcional + factura opcional + observación.
 *  - Derecha (sticky): resumen con total y botón "Cobrar Gs. X" (CTA verde).
 *
 * Submit: POST /sales (useCreateSale) → toast + redirect a /dashboard.
 */

import { zodResolver } from "@hookform/resolvers/zod";
import {
  Banknote,
  Car,
  ChevronUp,
  CreditCard,
  FileText,
  Loader2,
  Minus,
  Package,
  Plus,
  Receipt,
  Smartphone,
  Sparkles,
  Trash2,
  Wallet,
  Wrench,
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

function Section({
  title,
  description,
  icon: Icon,
  children,
  right,
}: {
  title: string;
  description?: string;
  icon?: React.ComponentType<{ size?: number; strokeWidth?: number; className?: string }>;
  children: React.ReactNode;
  right?: React.ReactNode;
}) {
  return (
    <section className="overflow-hidden rounded-xl border border-border-subtle bg-bg-surface shadow-card animate-fade-in-up">
      <header className="flex items-start justify-between gap-3 border-b border-border-subtle px-5 py-4">
        <div className="flex items-start gap-3">
          {Icon ? (
            <span className="mt-0.5 inline-flex h-8 w-8 items-center justify-center rounded-md bg-brand-mint/10 text-brand-deep">
              <Icon size={16} strokeWidth={2.25} />
            </span>
          ) : null}
          <div>
            <h3 className="text-sm font-semibold tracking-tight">{title}</h3>
            {description ? (
              <p className="text-xs text-text-tertiary">{description}</p>
            ) : null}
          </div>
        </div>
        {right}
      </header>
      <div className="p-5">{children}</div>
    </section>
  );
}

function SegmentedField<T extends string | number>({
  options,
  value,
  onChange,
  ariaLabel,
}: {
  options: { value: T; label: string; icon?: React.ComponentType<{ size?: number; className?: string }> }[];
  value: T | undefined;
  onChange: (v: T) => void;
  ariaLabel?: string;
}) {
  return (
    <div
      role="radiogroup"
      aria-label={ariaLabel}
      className="inline-flex flex-wrap gap-1.5 rounded-md border border-border-subtle bg-bg-sunken p-1"
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
              "inline-flex items-center gap-1.5 rounded border border-transparent px-3 py-1.5 text-xs font-medium transition-[box-shadow,color,background,border-color] duration-200 ease-out",
              active
                ? "bg-gradient-to-r from-brand-deep/15 via-brand-mint/20 to-brand-sky/15 font-semibold text-brand-deep shadow-glow-mint-active dark:text-text-primary"
                : "text-text-secondary hover-any:text-text-primary hover-any:shadow-glow-mint-soft",
            )}
          >
            {Icon ? <Icon size={14} /> : null}
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

function CatalogTile({
  item,
  onAdd,
}: {
  item: CatalogItem;
  onAdd: (item: CatalogItem) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onAdd(item)}
      className={cn(
        "group relative flex min-h-[68px] flex-col items-start gap-1.5 rounded-lg border border-border-subtle bg-bg-surface p-3 text-left transition-[transform,box-shadow,border-color] duration-300 ease-out",
        "active:scale-[0.98] active:bg-bg-sunken",
        // hover-any: variante custom sin @media (hover: hover). Ver global.css.
        "hover-any:-translate-y-1 hover-any:scale-[1.02] hover-any:border-transparent hover-any:shadow-glow-mint",
        "focus-visible:outline-none focus-visible:border-transparent focus-visible:shadow-glow-mint",
      )}
    >
      <span className="line-clamp-2 text-sm font-medium leading-tight">
        {item.name}
      </span>
      <span className="font-mono text-xs tabular-nums text-text-tertiary">
        {formatMoney(item.price ?? 0)}
      </span>
      <span
        aria-hidden
        className="absolute right-2 top-2 inline-flex h-5 w-5 items-center justify-center rounded-full bg-brand-mint/10 text-brand-deep opacity-0 transition group-hover:opacity-100"
      >
        <Plus size={12} strokeWidth={3} />
      </span>
    </button>
  );
}

function CatalogGrid({
  title,
  icon: Icon,
  items,
  loading,
  emptyLabel,
  onAdd,
}: {
  title: string;
  icon: React.ComponentType<{ size?: number; strokeWidth?: number; className?: string }>;
  items: CatalogItem[] | undefined;
  loading: boolean;
  emptyLabel: string;
  onAdd: (item: CatalogItem) => void;
}) {
  return (
    <Section title={title} icon={Icon}>
      {loading ? (
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-[68px] rounded-lg" />
          ))}
        </div>
      ) : !items || items.length === 0 ? (
        <p className="text-sm text-text-tertiary">{emptyLabel}</p>
      ) : (
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-3 xl:grid-cols-4">
          {items.map((it) => (
            <CatalogTile key={it.id} item={it} onAdd={onAdd} />
          ))}
        </div>
      )}
    </Section>
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
      <div className="rounded-lg border border-dashed border-border-subtle bg-bg-sunken/40 px-4 py-8 text-center">
        <p className="text-sm text-text-secondary">
          Tocá un servicio o producto arriba para empezar la venta.
        </p>
      </div>
    );
  }
  return (
    <ul className="divide-y divide-border-subtle rounded-lg border border-border-subtle">
      {fields.map((field, i) => {
        const it = watched[i] ?? field;
        const subtotal = (it.quantity || 0) * (it.unitPrice || 0);
        const isZeroPrice = (Number(it.unitPrice) || 0) <= 0;
        return (
          <li
            key={field.id}
            className={cn(
              "flex flex-col gap-2 px-3 py-3 sm:grid sm:grid-cols-12 sm:items-center",
              // Sutil fondo warn para que la fila con precio 0 se note de lejos.
              isZeroPrice && "bg-warn-soft/40",
            )}
          >
            {/* Fila 1 mobile / col 1 desktop: nombre + borrar */}
            <div className="flex items-start justify-between gap-2 sm:col-span-5 sm:block">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">{it.name}</p>
                <p className="text-[11px] uppercase tracking-wider text-text-tertiary">
                  {it.kind === "service" ? "Servicio" : "Producto"}
                </p>
              </div>
              <button
                type="button"
                onClick={() => remove(i)}
                className="inline-flex h-9 w-9 items-center justify-center rounded-md text-text-tertiary hover:bg-neg-soft hover:text-neg sm:hidden"
                aria-label="Quitar"
              >
                <Trash2 size={16} />
              </button>
            </div>

            {/* Fila 2 mobile / cols 2-4 desktop: stepper + precio + subtotal */}
            <div className="flex items-center justify-between gap-2 sm:contents">
              {/* qty stepper */}
              <div className="sm:col-span-3">
                <div className="inline-flex items-center rounded-md border border-border-subtle">
                  <button
                    type="button"
                    className="grid h-9 w-9 place-items-center text-text-secondary hover:text-text-primary disabled:opacity-40 sm:h-8 sm:w-8"
                    disabled={(it.quantity || 1) <= 1}
                    onClick={() =>
                      setValue(`items.${i}.quantity`, Math.max(1, (it.quantity || 1) - 1), {
                        shouldValidate: true,
                      })
                    }
                    aria-label="Disminuir"
                  >
                    <Minus size={14} />
                  </button>
                  <Controller
                    control={control}
                    name={`items.${i}.quantity`}
                    render={({ field }) => (
                      <input
                        type="number"
                        inputMode="numeric"
                        min={1}
                        value={field.value ?? 1}
                        onChange={(e) => field.onChange(Number(e.target.value) || 1)}
                        className="h-9 w-12 border-x border-border-subtle bg-transparent text-center text-sm tabular-nums focus:outline-none sm:h-8"
                      />
                    )}
                  />
                  <button
                    type="button"
                    className="grid h-9 w-9 place-items-center text-text-secondary hover:text-text-primary sm:h-8 sm:w-8"
                    onClick={() =>
                      setValue(`items.${i}.quantity`, (it.quantity || 1) + 1, {
                        shouldValidate: true,
                      })
                    }
                    aria-label="Aumentar"
                  >
                    <Plus size={14} />
                  </button>
                </div>
              </div>

              {/* unit price */}
              <div className="sm:col-span-2">
                <Controller
                  control={control}
                  name={`items.${i}.unitPrice`}
                  render={({ field }) => (
                    <input
                      type="number"
                      inputMode="numeric"
                      min={0}
                      step={1}
                      value={field.value ?? 0}
                      onChange={(e) => field.onChange(Number(e.target.value) || 0)}
                      aria-invalid={isZeroPrice}
                      title={isZeroPrice ? "Precio en 0. Editá antes de cobrar." : undefined}
                      className={cn(
                        "h-9 w-24 rounded-md border bg-bg-surface px-2 text-right text-sm tabular-nums focus:outline-none sm:h-8 sm:w-full",
                        isZeroPrice
                          ? "border-warn text-warn-fg focus:border-warn"
                          : "border-border-subtle focus:border-brand-mint",
                      )}
                    />
                  )}
                />
              </div>

              {/* subtotal */}
              <div
                className={cn(
                  "text-right font-mono text-sm font-semibold tabular-nums sm:col-span-1",
                  isZeroPrice && "text-warn-fg",
                )}
              >
                {formatMoney(subtotal)}
              </div>

              {/* trash desktop only */}
              <div className="hidden sm:col-span-1 sm:block sm:text-right">
                <button
                  type="button"
                  onClick={() => remove(i)}
                  className="inline-flex h-8 w-8 items-center justify-center rounded-md text-text-tertiary hover:bg-neg-soft hover:text-neg"
                  aria-label="Quitar"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          </li>
        );
      })}
    </ul>
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
          window.location.href = "/sales";
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
          window.location.href = "/dashboard";
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

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="grid gap-4 pb-[120px] lg:grid-cols-3 lg:pb-0"
      >
        <div className="space-y-4 lg:col-span-2">
          {/* Header — fecha, tipo cobro, método pago */}
          <Section title="Datos del cobro" icon={Receipt}>
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="fecha_venta"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Fecha</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormItem>
                <FormLabel>Tipo de cobro</FormLabel>
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
              </FormItem>
            </div>

            {tipoCobro === "Contado" ? (
              <div className="mt-4">
                <FormItem>
                  <FormLabel>Método de pago</FormLabel>
                  <Controller
                    control={form.control}
                    name="metodo_pago"
                    render={({ field }) => (
                      <SegmentedField
                        ariaLabel="Método de pago"
                        value={field.value}
                        onChange={field.onChange}
                        options={PAYMENT_METHODS.map((m) => ({
                          value: m.value,
                          label: m.label,
                          icon: m.icon,
                        }))}
                      />
                    )}
                  />
                </FormItem>
              </div>
            ) : null}
          </Section>

          {/* Servicios */}
          <CatalogGrid
            title="Servicios"
            icon={Wrench}
            items={services.data}
            loading={services.isLoading}
            emptyLabel="Sin servicios activos. Configurá el catálogo en Ajustes."
            onAdd={(it) => addCatalogItem(it, "service")}
          />

          {/* Productos */}
          <CatalogGrid
            title="Productos"
            icon={Package}
            items={products.data}
            loading={products.isLoading}
            emptyLabel="Sin productos activos."
            onAdd={(it) => addCatalogItem(it, "product")}
          />

          {/* Items */}
          <Section
            title="Detalle"
            description="Tocá ± para ajustar cantidad o editá el precio."
            icon={Sparkles}
          >
            <ItemsList
              control={form.control}
              fields={itemsField.fields}
              remove={itemsField.remove}
              setValue={form.setValue}
            />
            {form.formState.errors.items?.message ? (
              <p className="mt-2 text-xs text-neg">
                {form.formState.errors.items.message}
              </p>
            ) : null}
            {watchedItems.length > 0 &&
            watchedItems.some((it) => (Number(it?.unitPrice) || 0) <= 0) ? (
              <p className="mt-2 text-xs text-warn-fg">
                Hay ítems con precio en Gs. 0. Editá el precio antes de cobrar.
              </p>
            ) : null}
          </Section>

          {/* Vehículo: acoplado a servicios. */}
          <Section
            title="Vehículo"
            description={
              hasService
                ? "Obligatorio cuando la venta incluye un servicio."
                : "No aplica para ventas de solo productos."
            }
            icon={Car}
          >
            {hasService ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <FormField
                  control={form.control}
                  name="license_plate"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Placa</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="ABC123"
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
                    <FormItem>
                      <FormLabel>Tipo de vehículo</FormLabel>
                      <FormControl>
                        <select
                          value={field.value ?? ""}
                          onChange={(e) =>
                            field.onChange(e.target.value ? Number(e.target.value) : undefined)
                          }
                          className="h-9 w-full rounded-md border border-border-subtle bg-bg-surface px-2 text-sm focus:border-brand-mint focus:outline-none"
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
              <p className="text-sm text-text-tertiary">
                Agregá un servicio al detalle para habilitar el vehículo.
              </p>
            )}
          </Section>

          {/* Factura */}
          <Section
            title="Facturación"
            description="Activá si esta venta requiere factura."
            icon={FileText}
            right={
              <Controller
                control={form.control}
                name="requiere_factura"
                render={({ field }) => (
                  <ToggleSwitch checked={field.value} onCheckedChange={field.onChange} label="Requiere factura" />
                )}
              />
            }
          >
            {requiereFactura ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <FormField
                  control={form.control}
                  name="ruc_ci"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>RUC / CI</FormLabel>
                      <FormControl>
                        <Input placeholder="80012345-6" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="razon_social"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Razón social</FormLabel>
                      <FormControl>
                        <Input placeholder="Cliente S.A." {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            ) : (
              <p className="text-sm text-text-tertiary">
                Se registrará sin factura. Podés activar en cualquier momento.
              </p>
            )}
          </Section>

          {/* Observación */}
          <Section title="Observación" icon={FileText}>
            <FormField
              control={form.control}
              name="observacion"
              render={({ field }) => (
                <FormItem>
                  <FormControl>
                    <textarea
                      {...field}
                      rows={3}
                      placeholder="Notas internas opcionales…"
                      className="w-full rounded-md border border-border-subtle bg-bg-surface px-3 py-2 text-sm focus:border-brand-mint focus:outline-none"
                    />
                  </FormControl>
                </FormItem>
              )}
            />
          </Section>
        </div>

        {/* Sidebar resumen — sólo desktop */}
        <aside className="hidden lg:col-span-1 lg:block">
          <SummaryPanel
            total={total}
            items={watchedItems}
            isSubmitting={isSubmitting}
            mode={mode}
            hasZeroPrice={hasZeroPrice}
          />
        </aside>

        {/* Bottom bar sticky — sólo mobile/tablet */}
        <MobileSummaryBar
          total={total}
          items={watchedItems}
          isSubmitting={isSubmitting}
          mode={mode}
          hasZeroPrice={hasZeroPrice}
        />
      </form>
    </Form>
  );
}

function SummaryPanel({
  total,
  items,
  isSubmitting,
  mode,
  hasZeroPrice,
}: {
  total: number;
  items: FormValues["items"];
  isSubmitting: boolean;
  mode: SalesFormMode;
  hasZeroPrice: boolean;
}) {
  const ctaLabel =
    mode === "edit" ? "Guardar cambios" : `Cobrar ${formatMoney(total)}`;
  const submittingLabel = mode === "edit" ? "Guardando…" : "Registrando…";
  const blockedByZero = hasZeroPrice && mode !== "edit";
  return (
    <div className="sticky top-20 overflow-hidden rounded-xl border border-border-subtle bg-bg-surface shadow-elevated animate-fade-in-up">
      <div
        aria-hidden
        className="h-1 bg-gradient-to-r from-brand-deep via-brand-mint to-brand-sky"
      />
      <div className="p-5">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
          Resumen
        </p>
        <CartSummary items={items} className="mt-4" />

        <div className="mt-5 border-t border-border-subtle pt-4">
          <div className="flex items-end justify-between">
            <span className="text-xs uppercase tracking-wider text-text-tertiary">
              Total
            </span>
            <span
              className={cn(
                "font-mono text-2xl font-semibold tabular-nums",
                total > 0
                  ? "bg-gradient-to-r from-brand-deep via-brand-mint to-brand-sky bg-clip-text text-transparent"
                  : "text-text-tertiary",
              )}
            >
              {formatMoney(total)}
            </span>
          </div>
        </div>

        {blockedByZero ? (
          <p className="mt-4 rounded-md border border-warn/40 bg-warn-soft px-3 py-2 text-xs text-warn-fg">
            No se puede cobrar mientras haya ítems con precio en Gs. 0. Editá los precios en el detalle.
          </p>
        ) : null}

        <Button
          type="submit"
          size="lg"
          disabled={isSubmitting || items.length === 0 || blockedByZero}
          className={cn(
            "mt-5 w-full font-semibold transition-all duration-200",
            // Sin items: muy opaco, sin sombra. UX: "no se puede cobrar todavía".
            // Con items: verde pleno + ring sutil que comunica "listo para cobrar".
            items.length === 0 || blockedByZero
              ? "bg-pos/30 text-white/80"
              : "bg-pos text-white shadow-md ring-2 ring-pos/30 hover:bg-pos/90 hover:ring-pos/40",
          )}
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

/**
 * Resumen del carrito agrupado por tipo (servicios / productos) con
 * subtotales por grupo. Pensado para que el usuario entienda de un vistazo
 * "qué pidió y cuánto cuesta cada tipo", sin tener que sumar mentalmente.
 *
 * Convenciones:
 *  - El bloque de servicios va arriba (el lavado es el motivo de la venta).
 *  - Si un grupo está vacío no se renderiza.
 *  - La cantidad solo aparece cuando es > 1 (el "1×" omnipresente es ruido).
 */
function CartSummary({
  items,
  className,
}: {
  items: FormValues["items"];
  className?: string;
}) {
  if (!items || items.length === 0) {
    return (
      <p className={cn("text-sm text-text-tertiary", className)}>Sin ítems aún.</p>
    );
  }
  const groups: { kind: "service" | "product"; label: string; icon: typeof Wrench }[] = [
    { kind: "service", label: "Servicios", icon: Wrench },
    { kind: "product", label: "Productos", icon: Package },
  ];
  return (
    <div className={cn("space-y-4 text-sm", className)}>
      {groups.map((g) => {
        const groupItems = items.filter((it) => it.kind === g.kind);
        if (groupItems.length === 0) return null;
        // Contamos unidades totales (sumando cantidades), no lineas distintas.
        // Si el usuario vende 4 AREON + 6 Perfume el header debe decir 10, no 2.
        const unitCount = groupItems.reduce(
          (acc, it) => acc + (Number(it.quantity) || 0),
          0,
        );
        const subtotal = groupItems.reduce(
          (acc, it) => acc + (Number(it.quantity) || 0) * (Number(it.unitPrice) || 0),
          0,
        );
        const Icon = g.icon;
        return (
          <div key={g.kind}>
            <div className="mb-1.5 flex items-baseline justify-between gap-2 border-b border-border-subtle pb-1">
              <span className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
                <Icon
                  size={12}
                  className={cn(
                    g.kind === "service" ? "text-brand-deep" : "text-brand-sky",
                  )}
                  aria-hidden
                />
                {g.label}
                <span className="text-text-tertiary">({unitCount})</span>
              </span>
              <span className="font-mono text-xs font-semibold tabular-nums text-text-secondary">
                {formatMoney(subtotal)}
              </span>
            </div>
            <ul className="space-y-1">
              {groupItems.map((it) => {
                const lineTotal = it.quantity * it.unitPrice;
                const isZeroPrice = it.unitPrice <= 0;
                return (
                  <li
                    key={`${it.kind}-${it.refId}`}
                    className="flex items-baseline justify-between gap-2"
                  >
                    <span className="truncate text-text-secondary">
                      {it.quantity > 1 ? (
                        <span className="mr-1 text-text-tertiary">{it.quantity}×</span>
                      ) : null}
                      {it.name}
                    </span>
                    <span
                      className={cn(
                        "font-mono text-xs tabular-nums",
                        isZeroPrice ? "text-warn-fg" : "text-text-tertiary",
                      )}
                      title={isZeroPrice ? "Precio en 0. Editá el precio en el detalle antes de cobrar." : undefined}
                    >
                      {formatMoney(lineTotal)}
                    </span>
                  </li>
                );
              })}
            </ul>
          </div>
        );
      })}
    </div>
  );
}

/**
 * Resumen + CTA en mobile/tablet. Stick al fondo de la pantalla con safe-area.
 * Tap en la barra abre un drawer con el detalle de items.
 * Se oculta en `lg:` donde el sidebar derecho hace el mismo trabajo.
 */
function MobileSummaryBar({
  total,
  items,
  isSubmitting,
  mode,
  hasZeroPrice,
}: {
  total: number;
  items: FormValues["items"];
  isSubmitting: boolean;
  mode: SalesFormMode;
  hasZeroPrice: boolean;
}) {
  const [open, setOpen] = useState(false);
  const blockedByZero = hasZeroPrice && mode !== "edit";
  const ctaLabel =
    mode === "edit"
      ? "Guardar"
      : items.length === 0
        ? "Sin ítems"
        : blockedByZero
          ? "Precio en 0"
          : `Cobrar ${formatMoney(total)}`;
  const submittingLabel = mode === "edit" ? "Guardando…" : "Registrando…";
  const itemCount = items.reduce((acc, it) => acc + (it.quantity || 0), 0);

  return (
    <>
      {open && (
        <button
          type="button"
          aria-label="Cerrar resumen"
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden"
          onClick={() => setOpen(false)}
        />
      )}
      <div
        className={cn(
          "fixed inset-x-0 bottom-0 z-50 lg:hidden",
          "border-t border-border-subtle bg-bg-surface shadow-elevated",
          "pb-[env(safe-area-inset-bottom)]",
          "transition-transform duration-200",
        )}
      >
        {/* Drawer expandible con el detalle */}
        {open && (
          <div className="max-h-[55vh] overflow-y-auto border-b border-border-subtle px-4 py-3">
            <div className="mb-2 flex items-center justify-between">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
                Detalle ({itemCount})
              </p>
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="text-xs text-text-tertiary"
              >
                Cerrar
              </button>
            </div>
            <CartSummary items={items} />
          </div>
        )}

        {/* Barra principal */}
        <div className="flex items-center gap-3 px-4 py-3">
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            className="flex flex-1 items-center gap-2 text-left"
            aria-expanded={open}
            aria-label="Ver detalle del cobro"
          >
            <ChevronUp
              size={16}
              className={cn(
                "text-text-tertiary transition-transform",
                open && "rotate-180",
              )}
            />
            <div className="min-w-0">
              <p className="text-[11px] uppercase tracking-wider text-text-tertiary">
                Total {itemCount > 0 ? `· ${itemCount} ítem${itemCount === 1 ? "" : "s"}` : ""}
              </p>
              <p
                className={cn(
                  "font-mono text-lg font-semibold tabular-nums leading-tight",
                  total > 0
                    ? "bg-gradient-to-r from-brand-deep via-brand-mint to-brand-sky bg-clip-text text-transparent"
                    : "text-text-tertiary",
                )}
              >
                {formatMoney(total)}
              </p>
            </div>
          </button>
          <Button
            type="submit"
            size="lg"
            disabled={isSubmitting || items.length === 0 || blockedByZero}
            className={cn(
              "h-12 min-w-[140px] font-semibold transition-all duration-200",
              items.length === 0 || blockedByZero
                ? "bg-pos/30 text-white/80"
                : "bg-pos text-white shadow-md ring-2 ring-pos/30 hover:bg-pos/90 hover:ring-pos/40",
            )}
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
    </>
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
        "inline-flex h-5 w-9 items-center rounded-full border transition",
        checked
          ? "border-brand-mint bg-brand-mint"
          : "border-border-default bg-bg-muted",
      )}
    >
      <span
        className={cn(
          "ml-0.5 h-4 w-4 rounded-full bg-white shadow transition",
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
