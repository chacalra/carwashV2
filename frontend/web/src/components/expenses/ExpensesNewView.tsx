/**
 * Iter 6 — Nuevo egreso.
 *
 * Form simple (fecha, categoría, monto, descripción) → POST /expenses →
 * toast + redirect /dashboard. Categorías desde /catalogs/expense-categories.
 */

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, Receipt, Wallet } from "lucide-react";
import { useForm } from "react-hook-form";
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
import { useExpenseCategories } from "@/lib/api/queries/catalogs";
import { useCreateExpense } from "@/lib/api/queries/expenses";
import { formatMoney, todayISO } from "@/lib/format";
import { cn } from "@/lib/utils";

const formSchema = z.object({
  fecha: z.string().min(1, "Requerido"),
  categoria_egreso_id: z.number().int().positive("Seleccioná una categoría"),
  monto: z.number().positive("Debe ser mayor a cero"),
  descripcion: z.string().optional(),
});

type FormValues = z.infer<typeof formSchema>;

function ExpensesNewInner() {
  const categories = useExpenseCategories(true);
  const createExpense = useCreateExpense();

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      fecha: todayISO(),
      categoria_egreso_id: 0,
      monto: 0,
      descripcion: "",
    },
    mode: "onSubmit",
  });

  const monto = form.watch("monto");

  const onSubmit = (values: FormValues) => {
    const payload = {
      fecha: values.fecha,
      categoria_egreso_id: values.categoria_egreso_id,
      monto: values.monto,
      descripcion: values.descripcion?.trim() || undefined,
    };

    createExpense.mutate(payload, {
      onSuccess: () => {
        toast.success("Egreso registrado", {
          description: `Total ${formatMoney(values.monto)}.`,
        });
        window.location.href = "/dashboard";
      },
      onError: (err) => {
        const msg = err instanceof ApiError ? err.message : "No se pudo registrar el egreso.";
        toast.error("Error al registrar", { description: msg });
      },
    });
  };

  const isSubmitting = createExpense.isPending;

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="grid gap-4 lg:grid-cols-3"
      >
        <div className="space-y-4 lg:col-span-2">
          <section className="overflow-hidden rounded-xl border border-border-subtle bg-bg-surface shadow-card animate-fade-in-up">
            <header className="flex items-start gap-3 border-b border-border-subtle px-5 py-4">
              <span className="mt-0.5 inline-flex h-8 w-8 items-center justify-center rounded-md bg-brand-mint/10 text-brand-deep">
                <Receipt size={16} strokeWidth={2.25} />
              </span>
              <div>
                <h3 className="text-sm font-semibold tracking-tight">Datos del egreso</h3>
                <p className="text-xs text-text-tertiary">
                  Registralo con su categoría para que aparezca en los reportes.
                </p>
              </div>
            </header>

            <div className="space-y-4 p-5">
              <div className="grid gap-4 sm:grid-cols-2">
                <FormField
                  control={form.control}
                  name="fecha"
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

                <FormField
                  control={form.control}
                  name="categoria_egreso_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Categoría</FormLabel>
                      <FormControl>
                        {categories.isLoading ? (
                          <Skeleton className="h-9 w-full" />
                        ) : (
                          <select
                            value={field.value || ""}
                            onChange={(e) =>
                              field.onChange(
                                e.target.value ? Number(e.target.value) : 0,
                              )
                            }
                            className="h-9 w-full rounded-md border border-border-subtle bg-bg-surface px-2 text-sm focus:border-brand-mint focus:outline-none"
                          >
                            <option value="">Seleccioná…</option>
                            {(categories.data ?? []).map((cat) => (
                              <option key={cat.id} value={cat.id}>
                                {cat.name}
                              </option>
                            ))}
                          </select>
                        )}
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="monto"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Monto</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-text-tertiary">
                          Gs.
                        </span>
                        <Input
                          type="number"
                          min={0}
                          step={1}
                          className="pl-10 font-mono tabular-nums"
                          {...field}
                          onChange={(e) =>
                            field.onChange(Number(e.target.value) || 0)
                          }
                        />
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="descripcion"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Descripción</FormLabel>
                    <FormControl>
                      <textarea
                        {...field}
                        rows={3}
                        placeholder="Ej: Compra de jabón industrial al proveedor X…"
                        className="w-full rounded-md border border-border-subtle bg-bg-surface px-3 py-2 text-sm focus:border-brand-mint focus:outline-none"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          </section>
        </div>

        <aside className="lg:col-span-1">
          <div className="sticky top-20 overflow-hidden rounded-xl border border-border-subtle bg-bg-surface shadow-elevated animate-fade-in-up">
            <div
              aria-hidden
              className="h-1 bg-gradient-to-r from-brand-deep via-brand-mint to-brand-sky"
            />
            <div className="p-5">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
                Resumen
              </p>
              <div className="mt-4 flex items-center gap-3">
                <span className="inline-flex h-10 w-10 items-center justify-center rounded-md bg-neg-soft text-neg">
                  <Wallet size={18} />
                </span>
                <div>
                  <p className="text-[11px] uppercase tracking-wider text-text-tertiary">
                    Egreso
                  </p>
                  <p className="font-mono text-2xl font-semibold tabular-nums text-neg">
                    {monto > 0 ? `-${formatMoney(monto)}` : formatMoney(0)}
                  </p>
                </div>
              </div>

              <Button
                type="submit"
                size="lg"
                disabled={isSubmitting}
                className={cn(
                  "mt-6 w-full font-semibold",
                  "bg-accent text-white hover:bg-accent-hover",
                )}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="animate-spin" />
                    Registrando…
                  </>
                ) : (
                  <>Registrar egreso</>
                )}
              </Button>
            </div>
          </div>
        </aside>
      </form>
    </Form>
  );
}

export function ExpensesNewView() {
  return (
    <Shell
      activeKey="expense_form"
      title="Nuevo egreso"
      subtitle="Operación · Egresos"
    >
      <ExpensesNewInner />
    </Shell>
  );
}
