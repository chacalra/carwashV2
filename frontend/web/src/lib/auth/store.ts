/**
 * Store de sesión (Zustand) — JWT + user + permisos.
 * Persiste el token en localStorage. Hidrata al inicializarse.
 */

import { create } from "zustand";

const STORAGE_KEY = "carwash.session";

export interface SessionUser {
  id: number;
  username: string;
  role: string | null;
  lavanderiaId: number;
  lavanderiaName: string | null;
}

export interface LoginPayload {
  user: SessionUser;
  token: string;
  permissions: string[];
  expiresAt: string | null;
}

interface AuthState {
  token: string | null;
  user: SessionUser | null;
  permissions: string[];
  expiresAt: string | null;
  hydrated: boolean;
  login: (payload: LoginPayload) => void;
  logout: () => void;
  hasPermission: (perm: string) => boolean;
  isAuthenticated: () => boolean;
  hydrate: () => void;
}

function readStorage(): Partial<AuthState> | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function writeStorage(value: unknown) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
  } catch {
    // localStorage lleno o disabled — silencioso
  }
}

function clearStorage() {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    // noop
  }
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: null,
  user: null,
  permissions: [],
  expiresAt: null,
  hydrated: false,

  login: ({ user, token, permissions, expiresAt }) => {
    const payload = { user, token, permissions, expiresAt };
    writeStorage(payload);
    set({ ...payload, hydrated: true });
  },

  logout: () => {
    clearStorage();
    set({ token: null, user: null, permissions: [], expiresAt: null, hydrated: true });
  },

  hasPermission: (perm) => get().permissions.includes(perm),

  isAuthenticated: () => {
    const { token, expiresAt } = get();
    if (!token) return false;
    if (expiresAt) {
      const exp = new Date(expiresAt).getTime();
      if (!Number.isNaN(exp) && exp <= Date.now()) return false;
    }
    return true;
  },

  hydrate: () => {
    const stored = readStorage();
    if (stored?.token && stored.user) {
      set({
        token: stored.token,
        user: stored.user as SessionUser,
        permissions: (stored.permissions as string[]) ?? [],
        expiresAt: (stored.expiresAt as string | null) ?? null,
        hydrated: true,
      });
    } else {
      set({ hydrated: true });
    }
  },
}));

// Auto-hydrate en el cliente.
if (typeof window !== "undefined") {
  useAuthStore.getState().hydrate();
}
