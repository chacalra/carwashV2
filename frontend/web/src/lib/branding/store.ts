/**
 * Branding por tenant.
 *
 * Hoy el backend no devuelve estos campos. Cuando se agreguen a `lavanderia`
 * (logo_url, color_primario, color_secundario, mostrar_marca_mukusoft),
 * el LoginForm los va a setear acá tras un login exitoso.
 *
 * `applyTenantBrand()` inyecta colores como CSS vars en `<html>`. Componentes
 * y tokens del DS leen `--color-accent` / `--color-brand-deep` / etc., así que
 * el cambio es global sin tocar componentes individuales.
 *
 * Persistido en localStorage (`carwash.brand`) para sobrevivir reload sin
 * volver a llamar al backend.
 */

import { create } from "zustand";

export interface TenantBrand {
  logoUrl: string | null;
  logoUrlDark: string | null;
  /** Color primario del tenant (hex). Reemplaza `--color-accent`. */
  colorPrimary: string | null;
  /** Color secundario (hex). Reemplaza `--color-brand-sky`. */
  colorSecondary: string | null;
  /** Si false, oculta "powered by Mukusoft" del login. */
  showMukusoft: boolean;
}

const STORAGE_KEY = "carwash.brand";
const DEFAULT_BRAND: TenantBrand = {
  logoUrl: null,
  logoUrlDark: null,
  colorPrimary: null,
  colorSecondary: null,
  showMukusoft: true,
};

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

function readStored(): TenantBrand {
  if (!isBrowser()) return DEFAULT_BRAND;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_BRAND;
    const parsed = JSON.parse(raw) as Partial<TenantBrand>;
    return { ...DEFAULT_BRAND, ...parsed };
  } catch {
    return DEFAULT_BRAND;
  }
}

function persist(brand: TenantBrand) {
  if (!isBrowser()) return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(brand));
  } catch {
    /* noop */
  }
}

/**
 * Refina un color crudo del tenant para que se vea "elegante" en pantalla.
 *
 * Mezcla el color con un gris medio en espacio OKLCH para bajar la saturación
 * sin oscurecer demasiado. Un rojo `#DC2626` saturado pasa a un rojo más
 * "diseñado". Funciona para cualquier color de entrada.
 *
 * Constante única: la proporción 78/22 es nuestro "transformador". Subir el
 * primer número (ej. 85) preserva más el color original; bajarlo (ej. 70) lo
 * apaga más. Cambiá acá y todo el branding del tenant se ajusta.
 */
const REFINE_RATIO = 78;

function refine(hex: string): string {
  return `color-mix(in oklch, ${hex} ${REFINE_RATIO}%, #888 ${100 - REFINE_RATIO}%)`;
}

/**
 * Inyecta los colores del tenant como CSS vars en `<html>`.
 *
 * Sobreescribimos `--brand-deep`, `--brand-sky`, `--brand-mint` (referenciales,
 * declaradas en `:root` de global.css). Los tokens de Tailwind (`--color-brand-*`,
 * `--color-accent`, `--color-chart-*`) leen estas vars con `var()`, así que las
 * utilidades de Tailwind se actualizan automáticamente — incluso las que tienen
 * opacity (ej. `from-brand-deep/12`).
 *
 * Mapeo:
 *  - colorPrimary    → refine() → --brand-deep
 *  - colorSecondary  → refine() → --brand-sky
 *  - punto medio     → mezcla refinados → --brand-mint
 *
 * Sin branding cargado: removeProperty restaura los defaults Mukusoft.
 */
export function applyTenantBrand(brand: TenantBrand) {
  if (!isBrowser()) return;
  const root = document.documentElement;
  const primary = brand.colorPrimary;
  const secondary = brand.colorSecondary;

  if (primary) {
    root.style.setProperty("--brand-deep", refine(primary));
  } else {
    root.style.removeProperty("--brand-deep");
  }

  if (secondary) {
    root.style.setProperty("--brand-sky", refine(secondary));
  } else {
    root.style.removeProperty("--brand-sky");
  }

  if (primary && secondary) {
    // Mezcla ya sobre los hex crudos y después se refina, para que el
    // intermedio respete la misma estética que los extremos.
    root.style.setProperty(
      "--brand-mint",
      refine(`color-mix(in oklab, ${primary} 50%, ${secondary} 50%)`),
    );
  } else if (primary) {
    // Sin secondary, el "medio" cae al primary refinado.
    root.style.setProperty("--brand-mint", refine(primary));
  } else {
    root.style.removeProperty("--brand-mint");
  }
}

interface BrandState {
  brand: TenantBrand;
  setBrand: (b: Partial<TenantBrand>) => void;
  resetBrand: () => void;
}

// Hidratamos desde localStorage Y aplicamos las CSS vars antes de crear el
// store. Sino, al recargar una página dentro de la app las vars del branding
// no se setean hasta que algo dispare `setBrand`, y el primer paint sale
// con los defaults Mukusoft.
const initialBrand = readStored();
applyTenantBrand(initialBrand);

export const useBrandStore = create<BrandState>((set, get) => ({
  brand: initialBrand,
  setBrand: (b) => {
    const next = { ...get().brand, ...b };
    persist(next);
    applyTenantBrand(next);
    set({ brand: next });
  },
  resetBrand: () => {
    if (isBrowser()) window.localStorage.removeItem(STORAGE_KEY);
    applyTenantBrand(DEFAULT_BRAND);
    set({ brand: DEFAULT_BRAND });
  },
}));
