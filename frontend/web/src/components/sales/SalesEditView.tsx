/**
 * Iter 5 — Editar venta.
 *
 * Lee `?id=` de la URL, hace GET /sales/{id}, mapea a FormValues y reusa
 * SalesFormInner en modo "edit". Submit hace PUT /sales/{id}.
 */

import { AlertCircle, ArrowLeft, CircleSlash, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/shared/EmptyState";
import { Shell } from "@/components/shell/Shell";
import { Button } from "@/components/ui/button";
import { useSale } from "@/lib/api/queries/sales";
import { SalesFormInner, saleToFormValues } from "@/components/sales/SalesNewView";

function readSaleIdFromUrl(): number | null {
  if (typeof window === "undefined") return null;
  const raw = new URLSearchParams(window.location.search).get("id");
  if (!raw) return null;
  const n = Number(raw);
  return Number.isFinite(n) && n > 0 ? n : null;
}

function EditInner() {
  // Mantiene el id en estado para hidratar correctamente del URL del cliente.
  const [saleId, setSaleId] = useState<number | null>(null);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setSaleId(readSaleIdFromUrl());
    setHydrated(true);
  }, []);

  const { data: sale, isLoading, isError, error } = useSale(saleId);

  if (!hydrated || isLoading) {
    return (
      <div className="flex items-center justify-center py-20 text-text-secondary">
        <Loader2 className="mr-2 animate-spin" size={16} />
        Cargando venta…
      </div>
    );
  }

  if (saleId === null) {
    return (
      <EmptyState
        icon={AlertCircle}
        title="Falta el id de la venta"
        description="La URL debe incluir ?id=… para editar una venta existente."
      />
    );
  }

  if (isError || !sale) {
    return (
      <EmptyState
        icon={AlertCircle}
        title="No pudimos cargar la venta"
        description={error instanceof Error ? error.message : "Error desconocido."}
      />
    );
  }

  if (sale.is_voided) {
    return (
      <div className="space-y-3">
        <EmptyState
          icon={CircleSlash}
          title={`Venta #${sale.id} anulada`}
          description="No es posible editar una venta anulada."
        />
        <div className="text-center">
          <Button variant="outline" asChild>
            <a href="/sales">
              <ArrowLeft size={14} /> Volver a movimientos
            </a>
          </Button>
        </div>
      </div>
    );
  }

  return (
    <SalesFormInner
      mode="edit"
      saleId={sale.id}
      defaultValues={saleToFormValues(sale)}
    />
  );
}

export function SalesEditView() {
  return (
    <Shell
      activeKey="movements"
      title="Editar venta"
      subtitle="Operación · Ventas"
      actions={
        <Button variant="outline" size="sm" asChild>
          <a href="/sales">
            <ArrowLeft size={14} /> Movimientos
          </a>
        </Button>
      }
    >
      <EditInner />
    </Shell>
  );
}
