/**
 * Sidebar principal — basada en shadcn `sidebar` primitive.
 * - Items se filtran por permisos del usuario.
 * - El item activo se detecta por el pathname actual.
 * - Footer con avatar + dropdown de logout.
 */

import { LogOut } from "lucide-react";
import { useEffect, useState } from "react";
import { TenantLogo } from "@/components/branding/Logos";
import { useBrandStore } from "@/lib/branding/store";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuthStore } from "@/lib/auth/store";
import { cn } from "@/lib/utils";
import { NAV_ITEMS } from "@/components/shell/nav-config";

interface AppSidebarProps {
  activeKey?: string;
}

export function AppSidebar({ activeKey }: AppSidebarProps) {
  const user = useAuthStore((s) => s.user);
  const permissions = useAuthStore((s) => s.permissions);
  const logout = useAuthStore((s) => s.logout);
  const brand = useBrandStore((s) => s.brand);
  const [pathname, setPathname] = useState("");

  useEffect(() => {
    setPathname(window.location.pathname);
  }, []);

  const visibleItems = NAV_ITEMS.filter((item) => permissions.includes(item.permission));

  const isActive = (item: (typeof NAV_ITEMS)[number]) => {
    if (activeKey) return item.key === activeKey;
    return pathname === item.href || pathname.startsWith(`${item.href}/`);
  };

  const initial = (user?.username ?? "?").charAt(0).toUpperCase();

  const onLogout = () => {
    logout();
    window.location.href = "/login";
  };

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <div className="flex items-center gap-2 px-2 py-2">
          <TenantLogo
            className="size-8 shrink-0 rounded-md object-contain"
            alt={user?.lavanderiaName ?? "Logo"}
          />
          <div className="leading-tight group-data-[collapsible=icon]:hidden">
            {/* Sin logo propio del tenant: mostramos wordmark Carwash + by Mukusoft. */}
            {!brand.logoUrl ? (
              <>
                <p className="text-sm font-semibold tracking-tight">
                  <span className="text-brand-sky">C</span>
                  <span className="text-brand-deep">arwash</span>
                </p>
                <p className="text-[10px] font-medium uppercase tracking-wider text-text-tertiary">
                  by Mukusoft
                </p>
              </>
            ) : (
              <p className="truncate text-sm font-semibold tracking-tight">
                {user?.lavanderiaName ?? ""}
              </p>
            )}
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Operación</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {visibleItems.map((item) => (
                <SidebarMenuItem key={item.key}>
                  <SidebarMenuButton
                    asChild
                    isActive={isActive(item)}
                    tooltip={item.label}
                    className={cn(
                      "relative",
                      // Item activo: degradado de marca diluido + texto deep teal
                      // + rail vertical 3px mint a la izquierda. Sobreescribimos
                      // el `bg-sidebar-accent` que viene del primitive.
                      "data-[active=true]:bg-gradient-to-r data-[active=true]:from-brand-deep/12 data-[active=true]:via-brand-mint/15 data-[active=true]:to-transparent",
                      "data-[active=true]:text-brand-deep data-[active=true]:font-semibold dark:data-[active=true]:text-brand-mint",
                      "data-[active=true]:before:absolute data-[active=true]:before:left-0 data-[active=true]:before:top-1.5 data-[active=true]:before:bottom-1.5 data-[active=true]:before:w-[3px] data-[active=true]:before:rounded-r-full data-[active=true]:before:bg-gradient-to-b data-[active=true]:before:from-brand-deep data-[active=true]:before:via-brand-mint data-[active=true]:before:to-brand-sky",
                    )}
                  >
                    <a href={item.href}>
                      <item.icon />
                      <span>{item.label}</span>
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t border-sidebar-border">
        <SidebarMenu>
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton size="lg" className="cursor-pointer">
                  <Avatar className="size-7 rounded-md ring-1 ring-black/5">
                    <AvatarFallback className="rounded-md bg-gradient-to-br from-brand-deep via-brand-mint to-brand-sky text-xs font-bold text-white">
                      {initial}
                    </AvatarFallback>
                  </Avatar>
                  <div className="grid flex-1 text-left leading-tight">
                    <span className="truncate text-sm font-medium">
                      {user?.username ?? "Sin sesión"}
                    </span>
                    <span className="truncate text-xs text-text-tertiary">
                      {user?.lavanderiaName ?? ""}
                    </span>
                  </div>
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                side="top"
                align="end"
                className="w-56"
              >
                <DropdownMenuLabel>
                  <p className="text-sm font-medium">{user?.username ?? "—"}</p>
                  <p className="text-xs text-text-tertiary">{user?.role ?? "—"}</p>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={onLogout} variant="destructive">
                  <LogOut />
                  Salir
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
