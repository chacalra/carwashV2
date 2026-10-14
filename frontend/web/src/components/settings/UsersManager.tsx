/**
 * Iter B3 — Gestión de usuarios.
 *
 * Tabla con username, rol, estado. Form de crear arriba (con select de rol).
 * Edición inline (rename + cambio de rol). Toggle activo. Reset password
 * via dialog separado.
 *
 * El usuario logueado se ve igual en la lista pero sus controles destructivos
 * quedan disabled con tooltip "Sos vos".
 */

import { Check, KeyRound, Loader2, Pencil, Plus, Power, X } from "lucide-react";
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
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api/client";
import { useRoles } from "@/lib/api/queries/roles";
import {
  useCreateUser,
  useResetUserPassword,
  useToggleUserStatus,
  useUpdateUser,
  useUsers,
} from "@/lib/api/queries/users";
import { useAuthStore } from "@/lib/auth/store";
import { cn } from "@/lib/utils";

export function UsersManager() {
  const usersQ = useUsers();
  const rolesQ = useRoles();
  const createMut = useCreateUser();
  const updateMut = useUpdateUser();
  const toggleMut = useToggleUserStatus();
  const passwordMut = useResetUserPassword();

  const currentUserId = useAuthStore((s) => s.user?.id ?? null);

  const activeRoles = (rolesQ.data ?? []).filter((r) => r.is_active);

  const [newUsername, setNewUsername] = useState("");
  const [newRoleId, setNewRoleId] = useState<number | "">("");
  const [newPassword, setNewPassword] = useState("");

  const [editingId, setEditingId] = useState<number | null>(null);
  const [editUsername, setEditUsername] = useState("");
  const [editRoleId, setEditRoleId] = useState<number | "">("");

  const [passwordTarget, setPasswordTarget] = useState<{
    id: number;
    username: string;
  } | null>(null);
  const [passwordValue, setPasswordValue] = useState("");

  const items = usersQ.data ?? [];

  const onCreate = () => {
    const username = newUsername.trim();
    if (!username) {
      toast.error("Falta el nombre de usuario");
      return;
    }
    if (!newRoleId) {
      toast.error("Seleccioná un rol");
      return;
    }
    if (newPassword.length < 6) {
      toast.error("La contraseña debe tener al menos 6 caracteres");
      return;
    }
    createMut.mutate(
      { username, role_id: Number(newRoleId), password: newPassword },
      {
        onSuccess: () => {
          toast.success("Usuario creado", { description: username });
          setNewUsername("");
          setNewRoleId("");
          setNewPassword("");
        },
        onError: (err) => {
          const msg = err instanceof ApiError ? err.message : "No se pudo crear.";
          toast.error("Error al crear", { description: msg });
        },
      },
    );
  };

  const startEdit = (u: { id: number; username: string; role_id?: number | null }) => {
    setEditingId(u.id);
    setEditUsername(u.username);
    setEditRoleId(u.role_id ?? "");
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditUsername("");
    setEditRoleId("");
  };

  const saveEdit = (id: number) => {
    const username = editUsername.trim();
    if (!username) {
      toast.error("Falta el nombre de usuario");
      return;
    }
    if (!editRoleId) {
      toast.error("Seleccioná un rol");
      return;
    }
    updateMut.mutate(
      { id, body: { username, role_id: Number(editRoleId) } },
      {
        onSuccess: () => {
          toast.success("Usuario actualizado");
          cancelEdit();
        },
        onError: (err) => {
          const msg = err instanceof ApiError ? err.message : "No se pudo guardar.";
          toast.error("Error al guardar", { description: msg });
        },
      },
    );
  };

  const onToggle = (id: number) => {
    toggleMut.mutate(id, {
      onError: (err) => {
        const msg = err instanceof ApiError ? err.message : "No se pudo cambiar.";
        toast.error("Error", { description: msg });
      },
    });
  };

  const onConfirmPassword = () => {
    if (!passwordTarget) return;
    if (passwordValue.length < 6) {
      toast.error("La contraseña debe tener al menos 6 caracteres");
      return;
    }
    passwordMut.mutate(
      { id: passwordTarget.id, password: passwordValue },
      {
        onSuccess: () => {
          toast.success("Contraseña actualizada", {
            description: passwordTarget.username,
          });
          setPasswordTarget(null);
          setPasswordValue("");
        },
        onError: (err) => {
          const msg = err instanceof ApiError ? err.message : "No se pudo cambiar.";
          toast.error("Error al cambiar", { description: msg });
        },
      },
    );
  };

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-base font-semibold tracking-tight">Usuarios</h3>
        <p className="text-sm text-text-tertiary">
          Equipo del lavadero. Cada usuario tiene un rol que define sus permisos.
        </p>
      </div>

      {/* Form crear */}
      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-border-subtle bg-bg-surface p-4 shadow-card">
        <div className="flex flex-1 min-w-[160px] flex-col gap-1">
          <label className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
            Usuario
          </label>
          <Input
            value={newUsername}
            onChange={(e) => setNewUsername(e.target.value)}
            placeholder="ana"
          />
        </div>
        <div className="flex w-[180px] flex-col gap-1">
          <label className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
            Rol
          </label>
          <select
            value={newRoleId}
            onChange={(e) =>
              setNewRoleId(e.target.value ? Number(e.target.value) : "")
            }
            className="h-9 rounded-md border border-border-subtle bg-bg-surface px-2 text-sm focus:border-brand-mint focus:outline-none"
          >
            <option value="">Seleccioná…</option>
            {activeRoles.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
        </div>
        <div className="flex w-[180px] flex-col gap-1">
          <label className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
            Contraseña
          </label>
          <Input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="Mínimo 6 caracteres"
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
          Crear usuario
        </Button>
      </div>

      {/* Tabla */}
      <div className="overflow-hidden rounded-xl border border-border-subtle bg-bg-surface shadow-card">
        {usersQ.isLoading ? (
          <div className="space-y-2 p-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full rounded-md" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <p className="px-5 py-8 text-center text-sm text-text-tertiary">
            Sin usuarios. Creá el primero arriba.
          </p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border-subtle bg-bg-sunken/60 text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
                <th className="px-3 py-2.5 text-left">Usuario</th>
                <th className="px-3 py-2.5 text-left">Rol</th>
                <th className="px-3 py-2.5 text-left">Estado</th>
                <th className="px-3 py-2.5 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {items.map((u) => {
                const isEditing = editingId === u.id;
                const isSelf = u.id === currentUserId;
                return (
                  <tr
                    key={u.id}
                    className={cn(
                      "border-b border-border-subtle transition hover:bg-bg-sunken/30",
                      !u.is_active && "opacity-60",
                    )}
                  >
                    <td className="px-3 py-2.5">
                      {isEditing ? (
                        <Input
                          value={editUsername}
                          onChange={(e) => setEditUsername(e.target.value)}
                          autoFocus
                          className="h-8"
                        />
                      ) : (
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{u.username}</span>
                          {isSelf ? (
                            <span className="rounded-full bg-accent-soft px-2 py-0.5 text-[10px] font-medium text-accent">
                              vos
                            </span>
                          ) : null}
                        </div>
                      )}
                    </td>
                    <td className="px-3 py-2.5">
                      {isEditing ? (
                        <select
                          value={editRoleId}
                          onChange={(e) =>
                            setEditRoleId(
                              e.target.value ? Number(e.target.value) : "",
                            )
                          }
                          className="h-8 rounded-md border border-border-subtle bg-bg-surface px-2 text-sm focus:border-brand-mint focus:outline-none"
                        >
                          <option value="">Seleccioná…</option>
                          {activeRoles.map((r) => (
                            <option key={r.id} value={r.id}>
                              {r.name}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <span className="text-text-secondary">{u.role ?? "—"}</span>
                      )}
                    </td>
                    <td className="px-3 py-2.5">
                      <span
                        className={cn(
                          "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium",
                          u.is_active
                            ? "bg-pos-soft text-pos"
                            : "bg-bg-sunken text-text-tertiary",
                        )}
                      >
                        {u.is_active ? "Activo" : "Inactivo"}
                      </span>
                    </td>
                    <td className="px-3 py-2.5">
                      <div className="flex items-center justify-end gap-1">
                        {isEditing ? (
                          <>
                            <button
                              type="button"
                              onClick={() => saveEdit(u.id)}
                              disabled={updateMut.isPending}
                              className="grid size-7 place-items-center rounded-md text-pos hover:bg-pos-soft disabled:opacity-50"
                              aria-label="Guardar"
                            >
                              {updateMut.isPending ? (
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
                              onClick={() => startEdit(u)}
                              disabled={isSelf}
                              className="grid size-7 place-items-center rounded-md text-text-tertiary hover:bg-bg-sunken hover:text-text-primary disabled:cursor-not-allowed disabled:opacity-40"
                              aria-label="Editar"
                              title={isSelf ? "Sos vos" : "Editar"}
                            >
                              <Pencil size={13} />
                            </button>
                            <button
                              type="button"
                              onClick={() =>
                                setPasswordTarget({
                                  id: u.id,
                                  username: u.username,
                                })
                              }
                              disabled={isSelf}
                              className="grid size-7 place-items-center rounded-md text-text-tertiary hover:bg-bg-sunken hover:text-text-primary disabled:cursor-not-allowed disabled:opacity-40"
                              aria-label="Cambiar contraseña"
                              title={
                                isSelf
                                  ? "No podés cambiar tu propia contraseña desde acá"
                                  : "Cambiar contraseña"
                              }
                            >
                              <KeyRound size={13} />
                            </button>
                            <button
                              type="button"
                              onClick={() => onToggle(u.id)}
                              disabled={isSelf || toggleMut.isPending}
                              className="grid size-7 place-items-center rounded-md text-text-tertiary hover:bg-bg-sunken hover:text-text-primary disabled:cursor-not-allowed disabled:opacity-40"
                              aria-label={u.is_active ? "Desactivar" : "Activar"}
                              title={
                                isSelf
                                  ? "Sos vos"
                                  : u.is_active
                                    ? "Desactivar"
                                    : "Activar"
                              }
                            >
                              <Power size={13} />
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

      {/* Dialog reset password */}
      <AlertDialog
        open={passwordTarget !== null}
        onOpenChange={(open) => {
          if (!open) {
            setPasswordTarget(null);
            setPasswordValue("");
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cambiar contraseña</AlertDialogTitle>
            <AlertDialogDescription>
              {passwordTarget
                ? `Definí una nueva contraseña para ${passwordTarget.username}. Tomá nota: no podemos verla después.`
                : ""}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <Input
            type="password"
            value={passwordValue}
            onChange={(e) => setPasswordValue(e.target.value)}
            placeholder="Mínimo 6 caracteres"
            className="mt-2"
          />
          <AlertDialogFooter>
            <AlertDialogCancel disabled={passwordMut.isPending}>
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={(e) => {
                e.preventDefault();
                onConfirmPassword();
              }}
              disabled={passwordMut.isPending}
              className="bg-accent text-white hover:bg-accent-hover"
            >
              {passwordMut.isPending ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  Guardando…
                </>
              ) : (
                <>Cambiar</>
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
