/**
 * Iter B3 — Gestión de roles + permisos.
 *
 * Tabla de roles con conteo de permisos. Selección expandible muestra
 * checkboxes de permisos disponibles (catálogo). Reusa el patrón visual
 * de CatalogManager.
 */

import { Check, ChevronDown, ChevronRight, Loader2, Pencil, Plus, Power, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api/client";
import { usePermissions } from "@/lib/api/queries/permissions";
import {
  useCreateRole,
  useRenameRole,
  useRolePermissions,
  useRoles,
  useToggleRoleStatus,
  useUpdateRolePermissions,
} from "@/lib/api/queries/roles";
import { useAuthStore } from "@/lib/auth/store";
import { cn } from "@/lib/utils";

export function RolesManager() {
  const rolesQ = useRoles();
  const permsQ = usePermissions();
  const createMut = useCreateRole();
  const renameMut = useRenameRole();
  const toggleMut = useToggleRoleStatus();

  const currentRole = useAuthStore((s) => s.user?.role ?? null);

  const [newName, setNewName] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const items = rolesQ.data ?? [];
  const permsCatalog = permsQ.data ?? [];

  const onCreate = () => {
    const name = newName.trim();
    if (!name) {
      toast.error("Falta el nombre");
      return;
    }
    createMut.mutate(
      { name },
      {
        onSuccess: () => {
          toast.success("Rol creado", { description: name });
          setNewName("");
        },
        onError: (err) => {
          const msg = err instanceof ApiError ? err.message : "No se pudo crear.";
          toast.error("Error al crear", { description: msg });
        },
      },
    );
  };

  const startEdit = (id: number, name: string) => {
    setEditingId(id);
    setEditName(name);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditName("");
  };

  const saveEdit = (id: number) => {
    const name = editName.trim();
    if (!name) {
      toast.error("Falta el nombre");
      return;
    }
    renameMut.mutate(
      { id, name },
      {
        onSuccess: () => {
          toast.success("Rol actualizado");
          cancelEdit();
        },
        onError: (err) => {
          const msg = err instanceof ApiError ? err.message : "No se pudo guardar.";
          toast.error("Error al guardar", { description: msg });
        },
      },
    );
  };

  const onToggle = (id: number, name: string) => {
    if (name === currentRole) {
      toast.error("No podés desactivar tu propio rol.");
      return;
    }
    toggleMut.mutate(id, {
      onError: (err) => {
        const msg = err instanceof ApiError ? err.message : "No se pudo cambiar.";
        toast.error("Error", { description: msg });
      },
    });
  };

  const toggleExpand = (id: number) => {
    setExpandedId((cur) => (cur === id ? null : id));
  };

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-base font-semibold tracking-tight">Roles y permisos</h3>
        <p className="text-sm text-text-tertiary">
          Definí roles del equipo y qué partes de la app puede ver cada uno.
        </p>
      </div>

      {/* Form crear */}
      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-border-subtle bg-bg-surface p-4 shadow-card">
        <div className="flex flex-1 min-w-[200px] flex-col gap-1">
          <label className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
            Nombre del rol
          </label>
          <Input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="ej: operario"
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                onCreate();
              }
            }}
          />
        </div>
        <Button
          type="button"
          onClick={onCreate}
          disabled={createMut.isPending}
          className="bg-accent text-white hover:bg-accent-hover"
        >
          {createMut.isPending ? (
            <Loader2 className="animate-spin" size={14} />
          ) : (
            <Plus size={14} />
          )}
          Crear rol
        </Button>
      </div>

      {/* Tabla */}
      <div className="overflow-hidden rounded-xl border border-border-subtle bg-bg-surface shadow-card">
        {rolesQ.isLoading ? (
          <div className="space-y-2 p-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full rounded-md" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <p className="px-5 py-8 text-center text-sm text-text-tertiary">
            Sin roles. Creá el primero arriba.
          </p>
        ) : (
          <ul className="divide-y divide-border-subtle">
            {items.map((r) => {
              const isEditing = editingId === r.id;
              const isExpanded = expandedId === r.id;
              const isSelfRole = r.name === currentRole;
              return (
                <li key={r.id} className={cn(!r.is_active && "opacity-60")}>
                  <div className="flex items-center gap-2 px-4 py-3">
                    <button
                      type="button"
                      onClick={() => toggleExpand(r.id)}
                      className="grid size-7 place-items-center rounded-md text-text-tertiary hover:bg-bg-sunken hover:text-text-primary"
                      aria-label={isExpanded ? "Colapsar" : "Expandir"}
                    >
                      {isExpanded ? (
                        <ChevronDown size={14} />
                      ) : (
                        <ChevronRight size={14} />
                      )}
                    </button>

                    <div className="min-w-0 flex-1">
                      {isEditing ? (
                        <Input
                          value={editName}
                          onChange={(e) => setEditName(e.target.value)}
                          autoFocus
                          className="h-8"
                        />
                      ) : (
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{r.name}</span>
                          {isSelfRole ? (
                            <span
                              className="rounded-full bg-accent-soft px-2 py-0.5 text-[10px] font-medium text-accent"
                              title="Es tu rol actual"
                            >
                              tu rol
                            </span>
                          ) : null}
                        </div>
                      )}
                    </div>

                    <span
                      className={cn(
                        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium",
                        r.is_active
                          ? "bg-pos-soft text-pos"
                          : "bg-bg-sunken text-text-tertiary",
                      )}
                    >
                      {r.is_active ? "Activo" : "Inactivo"}
                    </span>

                    <span className="rounded-full bg-bg-sunken px-2 py-0.5 text-[11px] font-medium text-text-secondary">
                      {r.permission_count}{" "}
                      {r.permission_count === 1 ? "permiso" : "permisos"}
                    </span>

                    <div className="flex items-center gap-1">
                      {isEditing ? (
                        <>
                          <button
                            type="button"
                            onClick={() => saveEdit(r.id)}
                            disabled={renameMut.isPending}
                            className="grid size-7 place-items-center rounded-md text-pos hover:bg-pos-soft disabled:opacity-50"
                            aria-label="Guardar"
                          >
                            {renameMut.isPending ? (
                              <Loader2 size={13} className="animate-spin" />
                            ) : (
                              <Check size={14} />
                            )}
                          </button>
                          <button
                            type="button"
                            onClick={cancelEdit}
                            className="grid size-7 place-items-center rounded-md text-text-tertiary hover:bg-bg-sunken hover:text-text-primary"
                            aria-label="Cancelar"
                          >
                            <X size={14} />
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            type="button"
                            onClick={() => startEdit(r.id, r.name)}
                            className="grid size-7 place-items-center rounded-md text-text-tertiary hover:bg-bg-sunken hover:text-text-primary"
                            aria-label="Editar nombre"
                            title="Editar nombre"
                          >
                            <Pencil size={13} />
                          </button>
                          <button
                            type="button"
                            disabled={isSelfRole || toggleMut.isPending}
                            onClick={() => onToggle(r.id, r.name)}
                            className="grid size-7 place-items-center rounded-md text-text-tertiary hover:bg-bg-sunken hover:text-text-primary disabled:cursor-not-allowed disabled:opacity-40"
                            aria-label={r.is_active ? "Desactivar" : "Activar"}
                            title={
                              isSelfRole
                                ? "No podés desactivar tu propio rol"
                                : r.is_active
                                  ? "Desactivar"
                                  : "Activar"
                            }
                          >
                            <Power size={13} />
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  {isExpanded ? (
                    <RolePermissionsPanel
                      roleId={r.id}
                      roleName={r.name}
                      isSelfRole={isSelfRole}
                      catalog={permsCatalog}
                      catalogLoading={permsQ.isLoading}
                    />
                  ) : null}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}

interface RolePermissionsPanelProps {
  roleId: number;
  roleName: string;
  isSelfRole: boolean;
  catalog: { code: string; label: string }[];
  catalogLoading: boolean;
}

function RolePermissionsPanel({
  roleId,
  roleName,
  isSelfRole,
  catalog,
  catalogLoading,
}: RolePermissionsPanelProps) {
  const permsQ = useRolePermissions(roleId);
  const updateMut = useUpdateRolePermissions();

  const [selected, setSelected] = useState<Set<string>>(new Set());

  // Sembramos el set local cuando llegan los datos del rol.
  useEffect(() => {
    if (permsQ.data) setSelected(new Set(permsQ.data));
  }, [permsQ.data]);

  const initial = useMemo(
    () => new Set(permsQ.data ?? []),
    [permsQ.data],
  );
  const dirty = useMemo(() => {
    if (selected.size !== initial.size) return true;
    for (const code of selected) if (!initial.has(code)) return true;
    return false;
  }, [selected, initial]);

  const toggle = (code: string) => {
    setSelected((cur) => {
      const next = new Set(cur);
      if (next.has(code)) next.delete(code);
      else next.add(code);
      return next;
    });
  };

  const reset = () => setSelected(new Set(initial));

  const onSave = () => {
    if (isSelfRole && !selected.has("settings")) {
      toast.error(
        "No podés sacarle 'settings' a tu propio rol. Pediselo a otro admin.",
      );
      return;
    }
    updateMut.mutate(
      { id: roleId, permissions: Array.from(selected) },
      {
        onSuccess: () => toast.success("Permisos actualizados"),
        onError: (err) => {
          const msg = err instanceof ApiError ? err.message : "No se pudo guardar.";
          toast.error("Error al guardar", { description: msg });
        },
      },
    );
  };

  return (
    <div className="border-t border-border-subtle bg-bg-sunken/30 px-4 py-4">
      <p className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
        Permisos para {roleName}
      </p>
      {catalogLoading || permsQ.isLoading ? (
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-9 rounded-md" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 md:grid-cols-3">
          {catalog.map((p) => {
            const checked = selected.has(p.code);
            return (
              <label
                key={p.code}
                className={cn(
                  "flex cursor-pointer items-center gap-2 rounded-md border px-3 py-2 text-sm transition",
                  checked
                    ? "border-accent bg-accent-soft text-text-primary"
                    : "border-border-subtle bg-bg-surface text-text-secondary hover:border-border-default",
                )}
              >
                <input
                  type="checkbox"
                  className="size-4 accent-accent"
                  checked={checked}
                  onChange={() => toggle(p.code)}
                />
                <span className="font-medium">{p.label}</span>
                <span className="ml-auto font-mono text-[10px] text-text-tertiary">
                  {p.code}
                </span>
              </label>
            );
          })}
        </div>
      )}

      <div className="mt-4 flex items-center justify-end gap-2">
        {dirty ? (
          <Button type="button" variant="ghost" size="sm" onClick={reset}>
            Descartar cambios
          </Button>
        ) : null}
        <Button
          type="button"
          size="sm"
          onClick={onSave}
          disabled={!dirty || updateMut.isPending}
          className="bg-accent text-white hover:bg-accent-hover"
        >
          {updateMut.isPending ? (
            <>
              <Loader2 size={14} className="animate-spin" />
              Guardando…
            </>
          ) : (
            <>Guardar permisos</>
          )}
        </Button>
      </div>
    </div>
  );
}
