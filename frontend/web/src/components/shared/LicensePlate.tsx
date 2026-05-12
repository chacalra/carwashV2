/**
 * Renderiza una matrícula de vehículo con tratamiento visual de "placa real".
 *
 * - Mono + tabular-nums + tracking expandido para que sea identificable a la
 *   velocidad que un operador la lee en mostrador.
 * - Fondo `bg-bg-sunken` con borde sutil. Sin colores fuertes para no robar
 *   atención de KPIs/montos. La identidad la da el formato, no el color.
 *
 * Tres tamaños:
 * - `xs`: para chips densos en cards mobile.
 * - `sm` (default): para tablas y listas.
 * - `md`: para detalles, modales o el form de edición.
 */

import { cn } from "@/lib/utils";

interface LicensePlateProps {
  plate: string | null | undefined;
  size?: "xs" | "sm" | "md";
  className?: string;
}

const SIZE_CLASSES: Record<NonNullable<LicensePlateProps["size"]>, string> = {
  xs: "h-5 px-2 text-[11px] tracking-[0.1em]",
  sm: "h-7 px-2.5 text-xs tracking-[0.12em]",
  md: "h-9 px-3.5 text-sm tracking-[0.14em]",
};

export function LicensePlate({ plate, size = "sm", className }: LicensePlateProps) {
  if (!plate) {
    return <span className={cn("text-xs text-text-tertiary", className)}>—</span>;
  }
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border border-border-strong bg-bg-sunken font-mono font-semibold tabular-nums uppercase text-text-primary shadow-[inset_0_1px_0_rgb(255_255_255_/_0.5),inset_0_-1px_0_rgb(0_0_0_/_0.04)]",
        SIZE_CLASSES[size],
        className,
      )}
      aria-label={`Placa ${plate}`}
    >
      {plate}
    </span>
  );
}
