/**
 * KPI card reutilizable: label + value + delta opcional + sparkline opcional.
 * Tone determina el color del valor y los íconos.
 */

import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import type { ReactNode } from "react";
import { useId } from "react";
import { MoneyText } from "@/components/shared/MoneyText";
import { cn } from "@/lib/utils";

type Tone = "pos" | "neg" | "neutral";

interface SparklineProps {
  data: number[];
  color: string;
  className?: string;
}

export function Sparkline({ data, color, className }: SparklineProps) {
  const id = useId().replace(/:/g, "");
  const W = 100;
  const H = 32;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const stepX = data.length > 1 ? W / (data.length - 1) : W;

  const points = data.map((v, i) => {
    const x = i * stepX;
    const y = H - ((v - min) / range) * (H - 4) - 2;
    return `${x.toFixed(2)},${y.toFixed(2)}`;
  });

  const linePath = `M ${points.join(" L ")}`;
  const areaPath = `${linePath} L ${W},${H} L 0,${H} Z`;

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      preserveAspectRatio="none"
      className={cn("h-10 w-full", className)}
      aria-hidden="true"
    >
      <defs>
        <linearGradient id={`spark-${id}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.32" />
          <stop offset="100%" stopColor={color} stopOpacity="0.04" />
        </linearGradient>
      </defs>
      <path d={areaPath} fill={`url(#spark-${id})`} />
      <path
        d={linePath}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}

interface DeltaChipProps {
  value: string;
  tone: "pos" | "neg";
}

function DeltaChip({ value, tone }: DeltaChipProps) {
  const Icon = tone === "pos" ? ArrowUpRight : ArrowDownRight;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-0.5 rounded-md px-1.5 py-0.5 text-[11px] font-semibold tabular-nums",
        tone === "pos" ? "bg-pos-soft text-pos" : "bg-neg-soft text-neg",
      )}
    >
      <Icon size={11} strokeWidth={2.5} />
      {value}
    </span>
  );
}

export interface StatCardProps {
  label: string;
  value: number | null | undefined;
  icon: ReactNode;
  tone?: Tone;
  delta?: { value: string; tone: "pos" | "neg" };
  hint?: string;
  spark?: { data: number[]; color: string };
  /** Si es true, formatea con `Gs.`. Si false, lo muestra como número plano. */
  money?: boolean;
  /** Animación de entrada. */
  delay?: number;
}

export function StatCard({
  label,
  value,
  icon,
  tone = "neutral",
  delta,
  hint,
  spark,
  money = true,
  delay = 0,
}: StatCardProps) {
  const valueClass = {
    pos: "text-pos",
    neg: "text-neg",
    neutral: "text-text-primary",
  }[tone];

  const iconBg = {
    pos: "bg-pos-soft text-pos",
    neg: "bg-neg-soft text-neg",
    neutral: "bg-accent-soft text-accent",
  }[tone];

  const renderValue = () => {
    if (value === null || value === undefined) {
      return <span className="text-text-tertiary">—</span>;
    }
    if (money) {
      return <MoneyText value={value} />;
    }
    return <span className="font-mono tabular-nums">{value.toLocaleString("es-PY")}</span>;
  };

  return (
    <div
      style={{ animationDelay: `${delay}ms` }}
      className={cn(
        "animate-fade-in-up group relative overflow-hidden rounded-xl",
        "border border-border-subtle bg-bg-surface",
        "shadow-card transition-all duration-200",
        "hover:-translate-y-0.5 hover:shadow-card-hover",
      )}
    >
      <div className="p-5 pb-3">
        <div className="flex items-start justify-between">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
            {label}
          </p>
          <div
            className={cn(
              "inline-flex h-7 w-7 items-center justify-center rounded-md ring-1 ring-black/5",
              iconBg,
            )}
          >
            {icon}
          </div>
        </div>

        <div
          className={cn(
            "mt-3 block text-[22px] font-semibold tracking-tight leading-none sm:text-[28px]",
            valueClass,
          )}
        >
          {renderValue()}
        </div>

        <div className="mt-3 flex items-center gap-2">
          {delta && <DeltaChip {...delta} />}
          {hint && <span className="text-xs text-text-tertiary">{hint}</span>}
        </div>
      </div>

      {spark && <Sparkline data={spark.data} color={spark.color} className="mt-1" />}
    </div>
  );
}
