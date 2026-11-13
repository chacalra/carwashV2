/**
 * Iter 6 — Nuevo egreso.
 *
 * Form simple (fecha, categoría, monto, descripción) → POST /expenses →
 * toast + redirect /dashboard. Categorías desde /catalogs/expense-categories.
 */

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
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
      <form onSubmit={form.handleSubmit(onSubmit)} className="mx-auto w-full max-w-xl">
        <section className="overflow-hidden rounded-lg border border-border-default bg-bg-surface animate-fade-in-up">
          <header className="border-b border-border-subtle px-5 py-4">
            <h2 className="text-[15px] font-semibold tracking-tight">Datos del egreso</h2>
            <p className="text-[13px] text-text-tertiary">
              Registralo con su categoría para que aparezca en los reportes.
            </p>
          </header>

          <div className="space-y-5 p-5">
            {/* El monto es el dato principal: va primero y en grande. */}
            <FormField
              control={form.control}
              name="monto"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-xs font-normal text-text-secondary">Monto</FormLabel>
                  <FormControl>
                    <div className="relative">
                      <span className="absolute left-4 top-1/2 -translate-y-1/2 text-lg text-text-tertiary">
                        Gs.
                      </span>
                      <Input
                        type="number"
                        min={0}
                        step={1}
                        className="h-14 pl-14 text-2xl font-semibold tracking-tight tabular-nums [appearance:textfield] md:text-2xl [&::-webkit-inner-spin-button]:appearance-none"
                        {...field}
                        onChange={(e) => field.onChange(Number(e.target.value) || 0)}
                      />
                    </div>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="fecha"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-xs font-normal text-text-secondary">Fecha</FormLabel>
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
                    <FormLabel className="text-xs font-normal text-text-secondary">
                      Categoría
                    </FormLabel>
                    <FormControl>
                      {categories.isLoading ? (
                        <Skeleton className="h-9 w-full" />
                      ) : (
                        <select
                          value={field.value || ""}
                          onChange={(e) =>
                            field.onChange(e.target.value ? Number(e.target.value) : 0)
                          }
                          className="h-9 w-full rounded-md border border-input bg-bg-field px-2 text-sm focus:border-accent focus:outline-none"
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
              name="descripcion"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-xs font-normal text-text-secondary">
                    Descripción
                  </FormLabel>
                  <FormControl>
                    <textarea
                      {...field}
                      rows={3}
                      placeholder="Ej: Compra de jabón industrial al proveedor X…"
                      className="w-full rounded-md border border-input bg-bg-field px-3 py-2 text-sm focus:border-accent focus:outline-none"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-border-default bg-white/25 px-5 py-4 dark:bg-white/[0.02]">
            <p className="text-[13px] text-text-secondary">
              {monto > 0 ? (
                <>
                  Se descuenta{" "}
                  <span className="font-semibold tabular-nums text-neg-fg">
                    {formatMoney(monto)}
                  </span>{" "}
                  del balance.
                </>
              ) : (
                "Ingresá el monto del gasto."
              )}
            </p>
            <Button
              type="submit"
              size="lg"
              disabled={isSubmitting}
              className="h-11 min-w-[180px] bg-accent font-medium text-white hover:bg-accent-hover dark:text-bg-app"
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
          </footer>
        </section>
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
