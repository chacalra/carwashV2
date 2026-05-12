/**
 * Iter 8 — Settings (catálogos).
 *
 * Tabs para los 4 catálogos. Reusa CatalogManager con distintos resources.
 */

import { Car, FolderOpen, Package, ShieldCheck, Users, Wrench } from "lucide-react";
import { useState } from "react";

import { CatalogManager } from "@/components/settings/CatalogManager";
import { RolesManager } from "@/components/settings/RolesManager";
import { UsersManager } from "@/components/settings/UsersManager";
import { Shell } from "@/components/shell/Shell";
import { cn } from "@/lib/utils";

type TabKey =
  | "services"
  | "products"
  | "expense-categories"
  | "vehicle-types"
  | "roles"
  | "users";

interface TabDef {
  key: TabKey;
  label: string;
  icon: React.ComponentType<{ size?: number }>;
}

const TABS: TabDef[] = [
  { key: "services", label: "Servicios", icon: Wrench },
  { key: "products", label: "Productos", icon: Package },
  { key: "expense-categories", label: "Cat. egresos", icon: FolderOpen },
  { key: "vehicle-types", label: "Tipos de vehículo", icon: Car },
  { key: "roles", label: "Roles", icon: ShieldCheck },
  { key: "users", label: "Usuarios", icon: Users },
];

function SettingsInner() {
  const [active, setActive] = useState<TabKey>("services");

  return (
    <div className="space-y-5">
      {/* Tab bar */}
      <nav
        role="tablist"
        aria-label="Catálogos"
        className="flex flex-wrap gap-1 rounded-md border border-border-subtle bg-bg-sunken p-1"
      >
        {TABS.map((t) => {
          const Icon = t.icon;
          const isActive = active === t.key;
          return (
            <button
              key={t.key}
              type="button"
              role="tab"
              aria-selected={isActive}
              onClick={() => setActive(t.key)}
              className={cn(
                "inline-flex items-center gap-1.5 rounded px-3 py-1.5 text-sm font-medium transition",
                isActive
                  ? "bg-bg-surface text-text-primary shadow-sm ring-1 ring-black/5"
                  : "text-text-secondary hover:text-text-primary",
              )}
            >
              <Icon size={14} />
              {t.label}
            </button>
          );
        })}
      </nav>

      {/* Panel activo — un único CatalogManager por tab */}
      <div className="animate-fade-in-up">
        {active === "services" ? (
          <CatalogManager
            title="Servicios"
            description="Lo que se ofrece en el lavadero (lavados, pulidos, etc.)."
            resource="services"
            withPrice
            emptyLabel="Sin servicios cargados."
            itemSingular="Servicio"
          />
        ) : null}

        {active === "products" ? (
          <CatalogManager
            title="Productos"
            description="Productos físicos a la venta (ceras, ambientadores, etc.)."
            resource="products"
            withPrice
            emptyLabel="Sin productos cargados."
            itemSingular="Producto"
          />
        ) : null}

        {active === "expense-categories" ? (
          <CatalogManager
            title="Categorías de egresos"
            description="Para clasificar gastos en los reportes."
            resource="expense-categories"
            withPrice={false}
            emptyLabel="Sin categorías de egreso."
            itemSingular="Categoría"
          />
        ) : null}

        {active === "vehicle-types" ? (
          <CatalogManager
            title="Tipos de vehículo"
            description="Auto, camioneta, moto, etc."
            resource="vehicle-types"
            withPrice={false}
            emptyLabel="Sin tipos de vehículo."
            itemSingular="Tipo"
          />
        ) : null}

        {active === "roles" ? <RolesManager /> : null}
        {active === "users" ? <UsersManager /> : null}
      </div>
    </div>
  );
}

export function SettingsView() {
  return (
    <Shell activeKey="settings" title="Ajustes" subtitle="Configuración · Catálogos">
      <SettingsInner />
    </Shell>
  );
}
