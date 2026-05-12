import { formatMoney } from "@/lib/format";
import { cn } from "@/lib/utils";

interface MoneyTextProps {
  value: number | null | undefined;
  className?: string;
  withSymbol?: boolean;
}

export function MoneyText({ value, className, withSymbol = true }: MoneyTextProps) {
  return (
    <span className={cn("font-mono tabular-nums", className)}>
      {formatMoney(value, { withSymbol })}
    </span>
  );
}
