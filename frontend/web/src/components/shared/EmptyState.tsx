import type { LucideIcon } from "lucide-react";
import { Inbox } from "lucide-react";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: LucideIcon;
  className?: string;
}

export function EmptyState({
  title,
  description,
  icon: Icon = Inbox,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center gap-3 rounded-xl border border-border-subtle bg-bg-surface px-8 py-12 text-center shadow-card",
        className,
      )}
    >
      <div className="flex size-10 items-center justify-center rounded-lg bg-bg-sunken text-text-tertiary">
        <Icon className="size-5" />
      </div>
      <p className="text-base font-medium tracking-tight">{title}</p>
      {description && (
        <p className="max-w-sm text-sm text-text-secondary">{description}</p>
      )}
    </div>
  );
}
