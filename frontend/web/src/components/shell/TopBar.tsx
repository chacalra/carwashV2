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
    <header className="sticky top-0 z-10 flex h-16 shrink-0 items-center gap-3 border-b border-border-subtle bg-bg-app/80 px-4 backdrop-blur-sm md:px-8">
      <SidebarTrigger className="-ml-1" />
      <Separator orientation="vertical" className="mx-1 h-5" />
      <div className="flex-1 leading-tight">
        {subtitle && <p className="text-xs text-text-tertiary">{subtitle}</p>}
        <h1 className="text-lg font-semibold tracking-tight">{title}</h1>
      </div>
      <div className="flex items-center gap-2">
        {actions}
        <ThemeToggle />
      </div>
    </header>
  );
}
