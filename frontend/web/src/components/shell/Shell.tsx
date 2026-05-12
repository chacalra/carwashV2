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
            <main className="flex-1 p-4 md:p-8">
              <div className="mx-auto w-full max-w-6xl">{children}</div>
            </main>
          </SidebarInset>
        </SidebarProvider>
      </AuthGuard>
    </AppProviders>
  );
}
