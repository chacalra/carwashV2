/**
 * Iter 8 — Gestor genérico de catálogo.
 *
 * Reusable para los 4 recursos: servicios, productos, categorías de egresos,
 * tipos de vehículo. Si `withPrice=true` renderiza columna y campo de precio.
 *
 * Patrón: form inline arriba (crear) + tabla (listar) con edición inline,
 * toggle activo/inactivo y eliminar. Optimismo: useMutation + invalidación.
 */

import {
  Check,
  Loader2,
  Pencil,
  Plus,
  Power,
  Trash2,
  X,
} from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

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
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiError } from "@/lib/api/client";
import {
  useCatalogMutations,
  useExpenseCategories,
  useProducts,
  useServices,
  useVehicleTypes,
  type CatalogResource,
} from "@/lib/api/queries/catalogs";
import { formatMoney } from "@/lib/format";
import { cn } from "@/lib/utils";

interface RowItem {
  id: number;
  name: string;
  is_active: boolean;
  price?: number | null;
}

interface CatalogManagerProps {
  title: string;
  description: string;
  resource: CatalogResource;
  withPrice: boolean;
  emptyLabel: string;
  itemSingular: string;
}

function useCatalogList(resource: CatalogResource) {
  // El query con only_active=false trae todos para gestión.
  const services = useServices(false);
  const products = useProducts(false);
  const categories = useExpenseCategories(false);
  const vehicleTypes = useVehicleTypes(false);

  switch (resource) {
    case "services":
      return services;
    case "products":
      return products;
    case "expense-categories":
      return categories;
    case "vehicle-types":
      return vehicleTypes;
  }
}

export function CatalogManager({
  title,
  description,
  resource,
  withPrice,
  emptyLabel,
  itemSingular,
}: CatalogManagerProps) {
  const list = useCatalogList(resource);
  const { create, update, toggle, remove } = useCatalogMutations(resource);

  const [newName, setNewName] = useState("");
  const [newPrice, setNewPrice] = useState<number>(0);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [editPrice, setEditPrice] = useState<number>(0);
  const [deleteTarget, setDeleteTarget] = useState<RowItem | null>(null);

  const items = (list.data ?? []) as RowItem[];

  const onCreate = () => {
    const name = newName.trim();
    if (!name) {
      toast.error("Falta el nombre");
      return;
    }
    create.mutate(
      withPrice ? { name, price: newPrice } : { name },
      {
        onSuccess: () => {
          toast.success(`${itemSingular} creado`, { description: name });
          setNewName("");
          setNewPrice(0);
        },
        onError: (err) => {
          const msg = err instanceof ApiError ? err.message : "No se pudo crear.";
          toast.error("Error al crear", { description: msg });
        },
      },
    );
  };

  const startEdit = (it: RowItem) => {
    setEditingId(it.id);
    setEditName(it.name);
    setEditPrice(it.price ?? 0);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditName("");
    setEditPrice(0);
  };

  const saveEdit = (id: number) => {
    const name = editName.trim();
    if (!name) {
      toast.error("Falta el nombre");
      return;
    }
    update.mutate(
      { id, body: withPrice ? { name, price: editPrice } : { name } },
      {
        onSuccess: () => {
          toast.success(`${itemSingular} actualizado`);
          cancelEdit();
        },
        onError: (err) => {
          const msg = err instanceof ApiError ? err.message : "No se pudo guardar.";
          toast.error("Error al guardar", { description: msg });
        },
      },
    );
  };

  const onToggle = (it: RowItem) => {
    toggle.mutate(it.id, {
      onError: (err) => {
        const msg = err instanceof ApiError ? err.message : "No se pudo cambiar el estado.";
        toast.error("Error", { description: msg });
      },
    });
  };

  const onDelete = (it: RowItem) => {
    setDeleteTarget(it);
  };

  const confirmDelete = () => {
    if (!deleteTarget) return;
    const target = deleteTarget;
    remove.mutate(target.id, {
      onSuccess: () => {
        toast.success(`${itemSingular} eliminado`, { description: target.name });
        setDeleteTarget(null);
      },
      onError: (err) => {
        const msg = err instanceof ApiError ? err.message : "No se pudo eliminar.";
        toast.error("Error al eliminar", { description: msg });
        setDeleteTarget(null);
      },
    });
  };

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-base font-semibold tracking-tight">{title}</h3>
        <p className="text-sm text-text-tertiary">{description}</p>
      </div>

      {/* Form crear */}
      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-border-subtle bg-bg-surface p-4 shadow-card">
        <div className="flex flex-1 flex-col gap-1 min-w-[200px]">
          <label className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
            Nombre
          </label>
          <Input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder={`Nuevo ${itemSingular.toLowerCase()}…`}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                onCreate();
              }
            }}
          />
        </div>

        {withPrice ? (
          <div className="flex flex-col gap-1 w-[180px]">
            <label className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
              Precio
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-text-tertiary">
                Gs.
              </span>
              <Input
                type="number"
                min={0}
                value={newPrice}
                onChange={(e) => setNewPrice(Number(e.target.value) || 0)}
                className="pl-10 font-mono tabular-nums"
              />
            </div>
          </div>
        ) : null}

        <Button
          type="button"
          onClick={onCreate}
          disabled={create.isPending}
          className="bg-accent text-white hover:bg-accent-hover"
        >
          {create.isPending ? (
            <Loader2 className="animate-spin" size={14} />
          ) : (
            <Plus size={14} />
          )}
          Crear
        </Button>
      </div>

      {/* Tabla */}
      <div className="overflow-hidden rounded-xl border border-border-subtle bg-bg-surface shadow-card">
        {list.isLoading ? (
          <div className="space-y-2 p-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full rounded-md" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <p className="px-5 py-8 text-center text-sm text-text-tertiary">
            {emptyLabel}
          </p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border-subtle bg-bg-sunken/60 text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
                <th className="px-3 py-2.5 text-left">Nombre</th>
                {withPrice ? <th className="px-3 py-2.5 text-right">Precio</th> : null}
                <th className="px-3 py-2.5 text-left">Estado</th>
                <th className="px-3 py-2.5 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {items.map((it) => {
                const isEditing = editingId === it.id;
                return (
                  <tr
                    key={it.id}
                    className={cn(
                      "border-b border-border-subtle transition hover:bg-bg-sunken/30",
                      !it.is_active && "opacity-60",
                    )}
                  >
                    <td className="px-3 py-2.5">
                      {isEditing ? (
                        <Input
                          value={editName}
                          onChange={(e) => setEditName(e.target.value)}
                          autoFocus
                          className="h-8"
                        />
                      ) : (
                        <span className="font-medium">{it.name}</span>
                      )}
                    </td>
                    {withPrice ? (
                      <td className="px-3 py-2.5 text-right">
                        {isEditing ? (
                          <Input
                            type="number"
                            min={0}
                            value={editPrice}
                            onChange={(e) => setEditPrice(Number(e.target.value) || 0)}
                            className="h-8 text-right font-mono tabular-nums"
                          />
                        ) : (
                          <span className="font-mono tabular-nums">
                            {formatMoney(it.price ?? 0)}
                          </span>
                        )}
                      </td>
                    ) : null}
                    <td className="px-3 py-2.5">
                      <span
                        className={cn(
                          "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium",
                          it.is_active
                            ? "bg-pos-soft text-pos"
                            : "bg-bg-sunken text-text-tertiary",
                        )}
                      >
                        {it.is_active ? "Activo" : "Inactivo"}
                      </span>
                    </td>
                    <td className="px-3 py-2.5">
                      <div className="flex items-center justify-end gap-1">
                        {isEditing ? (
                          <>
                            <button
                              type="button"
                              onClick={() => saveEdit(it.id)}
                              disabled={update.isPending}
                              className="grid h-7 w-7 place-items-center rounded-md text-pos hover:bg-pos-soft disabled:opacity-50"
                              aria-label="Guardar"
                            >
                              {update.isPending ? (
                                <Loader2 size={13} className="animate-spin" />
                              ) : (
                                <Check size={14} />
                              )}
                            </button>
                            <button
                              type="button"
                              onClick={cancelEdit}
                              className="grid h-7 w-7 place-items-center rounded-md text-text-tertiary hover:bg-bg-sunken hover:text-text-primary"
                              aria-label="Cancelar"
                            >
                              <X size={14} />
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              type="button"
                              onClick={() => startEdit(it)}
                              className="grid h-7 w-7 place-items-center rounded-md text-text-tertiary hover:bg-bg-sunken hover:text-text-primary"
                              aria-label="Editar"
                              title="Editar"
                            >
                              <Pencil size={13} />
                            </button>
                            <button
                              type="button"
                              onClick={() => onToggle(it)}
                              disabled={toggle.isPending}
                              className="grid h-7 w-7 place-items-center rounded-md text-text-tertiary hover:bg-bg-sunken hover:text-text-primary disabled:opacity-50"
                              aria-label={it.is_active ? "Desactivar" : "Activar"}
                              title={it.is_active ? "Desactivar" : "Activar"}
                            >
                              <Power size={13} />
                            </button>
                            <button
                              type="button"
                              onClick={() => onDelete(it)}
                              disabled={remove.isPending}
                              className="grid h-7 w-7 place-items-center rounded-md text-text-tertiary hover:bg-neg-soft hover:text-neg disabled:opacity-50"
                              aria-label="Eliminar"
                              title="Eliminar"
                            >
                              <Trash2 size={13} />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      <AlertDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => {
          if (!open) setDeleteTarget(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Eliminar {itemSingular.toLowerCase()}?</AlertDialogTitle>
            <AlertDialogDescription>
              {deleteTarget
                ? `"${deleteTarget.name}" se eliminará. Esta acción no se puede deshacer.`
                : ""}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={remove.isPending}>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={(e) => {
                e.preventDefault();
                confirmDelete();
              }}
              disabled={remove.isPending}
              className="bg-neg text-white hover:bg-neg/90"
            >
              {remove.isPending ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  Eliminando…
                </>
              ) : (
                <>Eliminar</>
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
