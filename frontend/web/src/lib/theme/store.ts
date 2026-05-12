/**
 * Store de tema (light / dark / system).
 * - Persiste preferencia en `localStorage` bajo `carwash.theme`.
 * - Aplica/quita la clase `dark` en `<html>`.
 * - En modo `system`, escucha `prefers-color-scheme` y reacciona a cambios.
 *
 * Hidratación inicial: el script anti-flash en `Base.astro` aplica la clase
 * antes del primer paint. Acá nos ocupamos de mantenerla sincronizada.
 */

import { create } from "zustand";

export type Theme = "light" | "dark" | "system";

const STORAGE_KEY = "carwash.theme";

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

function readStored(): Theme {
  if (!isBrowser()) return "system";
  const v = window.localStorage.getItem(STORAGE_KEY);
  if (v === "light" || v === "dark" || v === "system") return v;
  return "system";
}

function systemPrefersDark(): boolean {
  if (!isBrowser()) return false;
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export function resolvedTheme(theme: Theme): "light" | "dark" {
  if (theme === "system") return systemPrefersDark() ? "dark" : "light";
  return theme;
}

function applyClass(theme: Theme) {
  if (!isBrowser()) return;
  const root = document.documentElement;
  if (resolvedTheme(theme) === "dark") root.classList.add("dark");
  else root.classList.remove("dark");
}

interface ThemeState {
  theme: Theme;
  setTheme: (t: Theme) => void;
}

export const useThemeStore = create<ThemeState>((set) => ({
  theme: readStored(),
  setTheme: (t) => {
    if (isBrowser()) window.localStorage.setItem(STORAGE_KEY, t);
    applyClass(t);
    set({ theme: t });
  },
}));

/**
 * Suscripción al cambio de `prefers-color-scheme` para refrescar cuando
 * el usuario está en modo "system". Se invoca una vez al cargar el cliente.
 */
let mediaListenerBound = false;
export function bindSystemThemeListener() {
  if (!isBrowser() || mediaListenerBound) return;
  mediaListenerBound = true;
  const mq = window.matchMedia("(prefers-color-scheme: dark)");
  mq.addEventListener("change", () => {
    if (useThemeStore.getState().theme === "system") {
      applyClass("system");
    }
  });
}
