/**
 * Shell — wrapper completo: Providers + AuthGuard + SidebarProvider + Sidebar + TopBar + main slot.
 * Cada página privada renderiza un Island que usa este Shell con su contenido.
 */

import type { ReactNode } from "react";
import { AppProviders } from "@/components/AppProviders";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { AppSidebar } from "@/components/shell/AppSidebar";
import { TopBar } from "@/components/shell/TopBar";
import {
  SidebarInset,
  SidebarProvider,
} from "@/components/ui/sidebar";

/** Aviso de demo pública: datos de ejemplo + botón para volver a empezar. */
function DemoNotice() {
  const onReset = async () => {
    const { resetDemo } = await import("@/lib/demo/backend");
    resetDemo();
    window.location.reload();
  };
  return (
    <div className="mb-4 flex flex-wrap items-center justify-between gap-x-4 gap-y-1 rounded-md border border-accent/25 bg-accent-soft px-3 py-2 text-[13px] text-text-secondary">
      <span>
        Demo con datos de ejemplo. Lo que cargues se guarda solo en este navegador.
      </span>
      <button
        type="button"
        onClick={onReset}
        className="font-medium text-accent underline-offset-2 hover:underline"
      >
        Restablecer datos
      </button>
    </div>
  );
}

interface ShellProps {
  children: ReactNode;
  activeKey?: string;
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}

export function Shell({ children, activeKey, title, subtitle, actions }: ShellProps) {
  return (
    <AppProviders>
      <AuthGuard>
        <SidebarProvider>
          <AppSidebar activeKey={activeKey} />
          <SidebarInset>
            <TopBar title={title} subtitle={subtitle} actions={actions} />
            <main className="flex-1 px-4 py-5 md:px-6 md:py-6">
              <div className="mx-auto w-full max-w-7xl">
                {import.meta.env.PUBLIC_DEMO === "true" ? <DemoNotice /> : null}
                {children}
              </div>
            </main>
          </SidebarInset>
        </SidebarProvider>
      </AuthGuard>
    </AppProviders>
  );
}
