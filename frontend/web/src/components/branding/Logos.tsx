/**
 * Componentes de marca.
 *
 * - `MukusoftMark`: logo de Mukusoft (siempre el mismo). Se usa como
 *   "powered by" en el login.
 * - `CarwashMark`: logo de Carwash (fallback cuando el tenant no tiene logo).
 * - `TenantLogo`: lee del store de branding; cae a `CarwashMark` si el
 *   tenant no subió un logo propio.
 *
 * Dark mode: el logo Mukusoft tiene texto deep teal, ilegible sobre fondo
 * oscuro. Aplicamos `dark:invert dark:brightness-200` para invertirlo a
 * blanco-azulado. Los logos de tenant y Carwash usan gradientes y se
 * sostienen mejor en dark sin ajuste.
 */

import { useBrandStore } from "@/lib/branding/store";
import { cn } from "@/lib/utils";

const MUKUSOFT_SRC = "/brand/logo_mukusoft_sinfondo.png";
const CARWASH_SRC = "/brand/logo_carwash_sinfondo.png";

interface LogoProps {
  className?: string;
  alt?: string;
}

export function MukusoftMark({ className, alt = "Mukusoft" }: LogoProps) {
  return (
    <img
      src={MUKUSOFT_SRC}
      alt={alt}
      className={cn(
        "block h-auto w-auto object-contain select-none",
        // En dark mode el texto deep teal del logo se pierde — invertimos.
        "dark:brightness-0 dark:invert",
        className,
      )}
      draggable={false}
    />
  );
}

export function CarwashMark({ className, alt = "Carwash" }: LogoProps) {
  return (
    <img
      src={CARWASH_SRC}
      alt={alt}
      className={cn("block h-auto w-auto object-contain select-none", className)}
      draggable={false}
    />
  );
}

/**
 * Logo del tenant actual. Si el tenant no tiene `logoUrl` cargado en el
 * branding store, devuelve el logo de Carwash como fallback.
 */
export function TenantLogo({ className, alt }: LogoProps) {
  const brand = useBrandStore((s) => s.brand);
  const src = brand.logoUrl;
  const dark = brand.logoUrlDark;

  if (!src) return <CarwashMark className={className} alt={alt} />;

  return (
    <picture>
      {dark ? <source srcSet={dark} media="(prefers-color-scheme: dark)" /> : null}
      <img
        src={src}
        alt={alt ?? "Logo del tenant"}
        className={cn(
          "block h-auto w-auto object-contain select-none",
          className,
        )}
        draggable={false}
      />
    </picture>
  );
}
