/**
 * Rutas internas conscientes del `base` de Astro.
 *
 * En producción (VPS) la app vive en la raíz del dominio y `BASE_URL` es "/".
 * En la demo de GitHub Pages vive bajo `/<repo>/`, así que todo link,
 * redirect o asset de `public/` tiene que pasar por `withBase()`.
 */

const RAW_BASE: string = import.meta.env.BASE_URL ?? "/";
const BASE = RAW_BASE.endsWith("/") ? RAW_BASE.slice(0, -1) : RAW_BASE;

/** "/dashboard" -> "/carwashV2/dashboard" (o "/dashboard" sin base). */
export function withBase(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${BASE}${p}`;
}

/** Inverso de withBase: quita el prefijo para comparar rutas de la app. */
export function stripBase(pathname: string): string {
  if (BASE && pathname.startsWith(BASE)) {
    const rest = pathname.slice(BASE.length);
    return rest === "" ? "/" : rest;
  }
  return pathname;
}

/** Build de demostración (GitHub Pages): sin backend, datos de ejemplo en el navegador. */
export const IS_DEMO = import.meta.env.PUBLIC_DEMO === "true";
