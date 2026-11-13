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
import { stripBase, withBase } from "@/lib/paths";
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
    const path = stripBase(pathname);
    return path === item.href || path.startsWith(`${item.href}/`);
  };

  const initial = (user?.username ?? "?").charAt(0).toUpperCase();

  const onLogout = () => {
    logout();
    window.location.href = withBase("/login");
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
                <p className="text-sm font-semibold tracking-tight text-text-primary">
                  Carwash
                </p>
                <p className="text-[11px] text-text-tertiary">by Mukusoft</p>
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
                      "h-8 text-text-secondary [&>svg]:text-text-tertiary",
                      // Item activo: superficie blanca con borde fino (como una
                      // pestaña levantada). El color de marca queda solo en el ícono.
                      "data-[active=true]:bg-white/80 data-[active=true]:font-medium data-[active=true]:text-text-primary dark:data-[active=true]:bg-white/10",
                      "data-[active=true]:shadow-[0_0_0_1px_var(--color-border-default),0_1px_2px_0_rgb(0_0_0/0.04)]",
                      "data-[active=true]:[&>svg]:text-accent",
                    )}
                  >
                    <a href={withBase(item.href)}>
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
                  <Avatar className="size-7 rounded-md">
                    <AvatarFallback className="rounded-md bg-accent text-xs font-semibold text-white dark:text-bg-app">
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
