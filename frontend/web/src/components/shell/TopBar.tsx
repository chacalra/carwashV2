/**
 * TopBar — header de cada página dentro del shell.
 * Incluye el SidebarTrigger (para colapsar) + título + subtítulo + slot de acciones.
 */

import type { ReactNode } from "react";
import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { ThemeToggle } from "@/components/shell/ThemeToggle";

interface TopBarProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}

export function TopBar({ title, subtitle, actions }: TopBarProps) {
  return (
    <header className="sticky top-0 z-10 flex h-14 shrink-0 items-center gap-3 border-b border-border-default glass-bar px-4 md:px-6">
      <SidebarTrigger className="-ml-1 text-text-tertiary" />
      <Separator orientation="vertical" className="h-4" />
      <div className="flex min-w-0 flex-1 items-baseline gap-2 leading-tight">
        <h1 className="truncate text-[15px] font-semibold tracking-tight">{title}</h1>
        {subtitle && (
          <p className="hidden truncate text-[13px] text-text-tertiary sm:block">{subtitle}</p>
        )}
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {actions}
        <ThemeToggle />
      </div>
    </header>
  );
}
