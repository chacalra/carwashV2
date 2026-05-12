# Plan Frontend — Astro + React (iterativo, view por view)

Este documento describe cómo construir el frontend web para el backend ya migrado (ver [FRONTEND_GUIDE.md](FRONTEND_GUIDE.md)) respetando el design system de [DesignGuide/carhwas-handoff](../DesignGuide/carhwas-handoff/carhwas/project).

El método es **iterativo**: una pantalla por entrega, validación visual y funcional, recién después la siguiente.

> Versiones anteriores de este plan apuntaban a Streamlit y luego a Flet. La decisión actual (2026-05-09) es migrar a un stack web estándar; ver §1 y §8 para el porqué.

---

## 1. Stack y decisiones de base

| Tema | Decisión | Razón |
|---|---|---|
| Framework / orquestador | **Astro 5** | Static-first, file-based routing, islas de interactividad, mínimo JS por página |
| UI components | **React 19** dentro de islas Astro | Estado dinámico para forms, dashboards, filtros |
| Lenguaje | **TypeScript 5.x** (strict) | Tipado end-to-end, los tipos vienen del backend (ver más abajo) |
| Estilos | **Tailwind CSS v4** | Utility-first, peso mínimo, integra con tokens del DS |
| Componentes UI | **shadcn/ui** (Radix primitives + Tailwind) | Copy-paste, vivos en el repo, modificables. Trae `Dialog`, `Select`, `Calendar`, `DataTable`, `Form`, `Toast`, etc. |
| Iconos | **Lucide React** | Set consistente, tree-shakable |
| Estado servidor | **TanStack Query v5** | Cache, refetch, sincronización con FastAPI |
| Estado cliente | **Zustand** | Sesión, permisos, tema. Liviano. |
| Forms | **React Hook Form + @hookform/resolvers/zod** | Form state + validación con esquemas Zod |
| Validación | **Zod** | Schemas para inputs y respuestas API |
| Tipos del backend | **`openapi-typescript`** | Genera `.d.ts` desde `openapi.json` de FastAPI. Nada de tipear schemas a mano. |
| Toasts/notifs | **sonner** | Snackbars one-liner |
| Fechas | **date-fns** + locale `es` | Formateo, locale español |
| Charts (Iter 9) | **Recharts** o **Tremor** (sobre Recharts) | KPIs, sparklines, barras |
| Build target | **Static-only** (`@astrojs/static`, default) | Frontend deployable como bundle estático servido por nginx |
| Package manager | **bun** | Install y dev rápidos; runtime + PM combinado |
| Lint/format | **Biome** | Reemplaza ESLint + Prettier; menos config, más rápido |
| Testing | **Vitest + Playwright** (opcional) | Unit + e2e si llegamos |

Dependencias principales (`package.json`):

```json
{
  "dependencies": {
    "astro": "^5",
    "@astrojs/react": "^4",
    "@astrojs/tailwind": "^6",
    "react": "^19",
    "react-dom": "^19",
    "@tanstack/react-query": "^5",
    "react-hook-form": "^7",
    "@hookform/resolvers": "^3",
    "zod": "^3",
    "zustand": "^5",
    "lucide-react": "latest",
    "sonner": "latest",
    "date-fns": "^4",
    "tailwindcss": "^4",
    "tailwind-merge": "latest",
    "clsx": "latest",
    "class-variance-authority": "latest"
  },
  "devDependencies": {
    "typescript": "^5",
    "openapi-typescript": "^7"
  }
}
```

> El backend ya expone `openapi.json` (ver [FRONTEND_GUIDE.md §1](FRONTEND_GUIDE.md)). Un script en `frontend/web/scripts/gen-api-types.sh` lo descarga y genera `src/lib/api/schema.d.ts` automáticamente.

> El intento previo en Flet **se eliminó del repo**. Solo queda `frontend/streamlit/` como referencia funcional hasta alcanzar paridad.

---

## 2. Layout de carpetas propuesto

```
frontend/
├── streamlit/                 # legacy, no se toca
└── web/                       # ← stack nuevo (Astro + React)
    ├── astro.config.mjs
    ├── tsconfig.json
    ├── package.json
    ├── components.json        # config de shadcn/ui
    ├── public/
    │   └── fonts/             # Geist y Geist Mono variable .ttf
    ├── scripts/
    │   └── gen-api-types.sh   # curl openapi.json | openapi-typescript
    ├── src/
    │   ├── pages/             # routing Astro (file-based)
    │   │   ├── index.astro
    │   │   ├── login.astro
    │   │   ├── dashboard.astro
    │   │   ├── sales/
    │   │   │   ├── index.astro       # /sales (movimientos)
    │   │   │   ├── new.astro
    │   │   │   └── [id]/edit.astro
    │   │   ├── expenses/
    │   │   ├── reports.astro
    │   │   └── settings/
    │   ├── layouts/
    │   │   └── Shell.astro    # sidebar + topbar wrapper
    │   ├── components/
    │   │   ├── ui/            # shadcn components (button, dialog, select, etc.)
    │   │   ├── shell/
    │   │   │   ├── Sidebar.tsx
    │   │   │   ├── TopBar.tsx
    │   │   │   └── AuthGuard.tsx
    │   │   ├── dashboard/
    │   │   ├── sales/
    │   │   ├── expenses/
    │   │   └── shared/        # KpiCard, EmptyState, MoneyText, etc.
    │   ├── lib/
    │   │   ├── api/
    │   │   │   ├── client.ts          # fetch wrapper + auth + 401 handling
    │   │   │   ├── schema.d.ts        # autogenerado, no editar
    │   │   │   └── queries/           # hooks TanStack Query por recurso
    │   │   ├── auth/
    │   │   │   ├── store.ts           # Zustand store
    │   │   │   └── permissions.ts     # has(perm), required(perm)
    │   │   ├── format.ts              # formatMoney, formatDate, etc.
    │   │   └── utils.ts               # cn, helpers genéricos
    │   └── styles/
    │       └── global.css             # Tailwind v4 @theme + custom CSS
    └── README.md
```

---

## 3. Mapeo backend → views

Las views reproducen la **esencia** de las que existían en Streamlit, ajustadas al backend nuevo (ver [FRONTEND_GUIDE.md §5](FRONTEND_GUIDE.md)):

| Ruta Astro | Endpoints | Permiso |
|---|---|---|
| `/login` | `POST /auth/login` | público |
| `/dashboard` | `GET /reports/sales-summary` (rango = hoy / mes) | `dashboard` |
| `/sales/new` | `GET /catalogs/services`, `/catalogs/products`, `/vehicles`, `/clients`, `POST /sales` | `register_sale` |
| `/sales` | `GET /sales/grouped` | `movements` |
| `/sales/[id]/edit` | `GET /sales/{id}`, `PUT /sales/{id}`, `PATCH /sales/{id}/payment-type`, `DELETE /sales/{id}` | `edit_sale`, `manage_sales` |
| `/expenses/new` | `GET /catalogs/expense-categories`, `POST /expenses` | `register_expense` |
| `/expenses` | `GET /expenses`, `PUT /expenses/{id}`, `DELETE /expenses/{id}` | `register_expense`, `movements` |
| `/reports` | `GET /reports/sales-summary` + `GET /sales` (lista plana para CSV) | `export` |
| `/settings/*` | CRUD de `clients`, `vehicles`, `catalogs/*` | `settings` |

El `<Sidebar />` se filtra por `permissions` recibido en el login.

---

## 4. Design system → Tailwind (mapeo concreto)

Los tokens vienen de `DesignGuide/.../ds-foundations.jsx`. Se traducen a custom properties CSS via `@theme` de Tailwind v4 (config CSS-first).

### `src/styles/global.css` — esqueleto

```css
@import "tailwindcss";

@theme {
  /* Surface */
  --color-bg-app: #FAFAF9;
  --color-bg-surface: #FFFFFF;
  --color-bg-sunken: #F4F4F2;

  /* Text */
  --color-text-primary: #0A0A0A;
  --color-text-secondary: #525252;
  --color-text-tertiary: #737373;
  --color-text-disabled: #A3A3A3;

  /* Borders */
  --color-border-subtle: #EDEDEA;
  --color-border-default: #E4E4E0;
  --color-border-strong: #D4D4D0;

  /* Accent */
  --color-accent: #3B82F6;
  --color-accent-hover: #2563EB;
  --color-accent-soft: #EFF6FF;

  /* Estado financiero */
  --color-pos: #059669;
  --color-pos-soft: #ECFDF5;
  --color-neg: #DC2626;
  --color-neg-soft: #FEF2F2;
  --color-warn: #D97706;
  --color-warn-soft: #FFFBEB;

  /* Tipografía */
  --font-sans: "Geist", system-ui, sans-serif;
  --font-mono: "Geist Mono", ui-monospace, monospace;

  /* Radii */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
}

/* Geist como font-face */
@font-face {
  font-family: "Geist";
  src: url("/fonts/Geist-Variable.ttf") format("truetype-variations");
  font-weight: 100 900;
}
@font-face {
  font-family: "Geist Mono";
  src: url("/fonts/GeistMono-Variable.ttf") format("truetype-variations");
  font-weight: 100 900;
}
```

Tailwind autoexpone `bg-bg-app`, `text-text-primary`, `border-border-default`, `text-pos`, `bg-accent-soft`, etc. Las clases responsive (`sm:`, `md:`, `lg:`, `xl:`) usan los breakpoints de Tailwind directamente.

### Breakpoints — Tailwind v4 default

| Tailwind | Min width |
|---|---|
| `sm` | 640px |
| `md` | 768px |
| `lg` | 1024px |
| `xl` | 1280px |
| `2xl` | 1536px |

Se pueden ajustar para coincidir con los del DS (`xs<600 sm 600-904 md 905-1239 lg 1240-1439 xl≥1440`) si hace falta. Por defecto vamos con los de Tailwind.

### Tipografía

- Sans: **Geist** (variable, font-weight 100-900).
- Mono: **Geist Mono** para todos los montos `Gs.` y números financieros.
- Helper sugerido: `<MoneyText value={n} />` que aplica `font-mono tabular-nums` y formatea con `formatMoney(value)`.

---

## 5. Patrones transversales (definir antes de la primera view)

### 5.1 API client

`src/lib/api/client.ts`:

```ts
import { useAuthStore } from "@/lib/auth/store";

const BASE_URL = import.meta.env.PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, message: string, public payload?: unknown) {
    super(message);
  }
}

export async function apiFetch<T = unknown>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const token = useAuthStore.getState().token;
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers ?? {}),
    },
  });

  if (res.status === 401) {
    useAuthStore.getState().logout();
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new ApiError(401, "Sesion expirada");
  }

  if (!res.ok) {
    let detail: unknown = await res.text();
    try { detail = JSON.parse(detail as string); } catch {}
    const message = typeof detail === "string"
      ? detail
      : Array.isArray((detail as any)?.detail)
        ? (detail as any).detail.map((d: any) => d.msg).join("; ")
        : (detail as any)?.detail ?? "Error desconocido";
    throw new ApiError(res.status, message, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}
```

### 5.2 Auth store (Zustand)

`src/lib/auth/store.ts` con `token`, `user`, `permissions`, `expiresAt`. Hidrata desde `localStorage` al inicio. Métodos `login(payload)`, `logout()`, `hasPermission(perm)`.

### 5.3 Tipos del backend

Script en `scripts/gen-api-types.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
URL="${1:-http://localhost:8000/openapi.json}"
mkdir -p src/lib/api
curl -fsSL "$URL" | npx openapi-typescript - -o src/lib/api/schema.d.ts
echo "OK -> src/lib/api/schema.d.ts"
```

Uso: `pnpm gen:api` (script en `package.json`). Hay que **re-correrlo cuando cambia el backend**. El `.d.ts` se comitea.

### 5.4 Hooks de TanStack Query

Por recurso, en `src/lib/api/queries/`. Ej:

```ts
// queries/sales.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type SaleResponse = components["schemas"]["SaleResponse"];

export function useSalesGrouped(start: string, end: string) {
  return useQuery({
    queryKey: ["sales", "grouped", start, end],
    queryFn: () => apiFetch<SaleResponse[]>(`/sales/grouped?start_date=${start}&end_date=${end}`),
  });
}

export function useCreateSale() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: components["schemas"]["SaleCreateRequest"]) =>
      apiFetch<{ id: number }>("/sales", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sales"] }),
  });
}
```

### 5.5 Auth guard

Cada página privada incluye `<AuthGuard client:load>`. Si `!isAuthenticated` → `window.location.href = "/login"`. Si OK, renderiza children. Esto vive en React (no en Astro middleware) porque somos static-only.

### 5.6 Permission gate

`<PermissionGate perm="settings">{children}</PermissionGate>` o hook `usePermission("settings")`. Centralizado en `src/lib/auth/permissions.ts`.

### 5.7 Toasts

`<Toaster richColors position="top-right" />` montado una vez en el shell. Uso: `toast.success(...)`, `toast.error(...)`.

### 5.8 Helpers de formato

`src/lib/format.ts`:
- `formatMoney(n: number) -> "Gs. 50.000"`
- `formatDate(iso: string) -> "06/05/2026"` (locale es)

---

## 6. Roadmap iterativo (orden propuesto)

Cada paso = una pantalla, demo, feedback, siguiente.

### Iteración 0 — Andamiaje
- Crear `frontend/web/` con Astro + React + Tailwind v4 + TS strict.
- `components.json` para shadcn/ui (init + theme tokens del DS).
- Generar `schema.d.ts` desde `openapi.json` del backend.
- Implementar `apiFetch` + `useAuthStore` + helpers de formato.
- Página única `/` que muestra "Hola Carwash" con Geist + Geist Mono cargadas, KPI dummies con tokens (`text-pos`, `text-neg`).
- **Demo**: pestaña abre, fuentes correctas, colores correctos, responsive.

### Iteración 1 — Login
- `pages/login.astro` con form: usuario, contraseña, subdominio (visible solo en localhost).
- Submit con React Hook Form + Zod.
- `POST /auth/login` → guarda en store + `localStorage` → redirige `/dashboard`.
- Manejo 401/422 con `<Toast />`.

### Iteración 2 — Shell + Dashboard
- `layouts/Shell.astro` + `<Sidebar />` filtrado por permisos + `<TopBar />`.
- `pages/dashboard.astro` con 4 KPI cards desde `GET /reports/sales-summary`.
- Empty state cuando no hay movimientos.
- Responsive: sidebar colapsa en mobile, expande en desktop.

### Iteración 3 — Nueva venta
- `pages/sales/new.astro`.
- Servicios y productos como **tile grids seleccionables** (matching DS desde el principio).
- Cliente search por RUC/CI.
- Vehículo opcional con upsert via `POST /vehicles`.
- Factura toggle.
- Sidebar derecha de "Resumen y cobro" con total + recibido + vuelto.
- Topbar con CTA "Cobrar Gs. X" verde.
- Submit con `useCreateSale()`, redirige a `/dashboard` con toast de éxito.

### Iteración 4 — Movimientos (ventas)
- `pages/sales/index.astro`.
- `<DataTable />` (shadcn) con filtro por rango de fechas (default mes actual).
- Fila expandible (`<Collapsible />`) con items.
- Acciones por fila: editar, anular (con `<AlertDialog />`).

### Iteración 5 — Editar / anular venta
- `pages/sales/[id]/edit.astro` con form precargado.
- `PUT /sales/{id}`, `PATCH /sales/{id}/payment-type`, `DELETE /sales/{id}`.

### Iteración 6 — Egresos (form + lista)
- `pages/expenses/new.astro` y `pages/expenses/index.astro`. Análogo a ventas pero más simple.

### Iteración 7 — Reportes / Export
- `pages/reports.astro`: rango, KPIs, breakdown por servicio / categoría / método de pago. Export CSV.
- Charts (Recharts/Tremor) si el tiempo da.

### Iteración 8 — Settings
- `pages/settings/*` con tabs: clientes, vehículos, catálogos. PATCH activar/desactivar.

### Iteración 9 — Pulido y empaquetado
- Estados de carga (`<Skeleton />`), manejo refresco al expirar token.
- Verificación responsive end-to-end.
- `astro build` → bundle estático.
- Decisión de dónde se sirve (mismo nginx que el backend, o subdomain dedicado).
- Pulido visual: charts en dashboard, sparklines en KPI, micro-animaciones, etc. Con Tailwind/shadcn esto es mucho más natural — no hace falta una iteración 10 separada como en Flet.

---

## 7. Cómo trabajamos cada iteración

1. Antes de codear, alineamos el **alcance exacto** de la pantalla.
2. Implemento solamente esa pantalla + lo mínimo de componentes que necesite.
3. Te paso instrucciones (`pnpm dev` o `bun dev`).
4. Vos validás visualmente y funcionalmente.
5. Anoto feedback, ajusto, recién después arrancamos la siguiente.

No avanzo a la siguiente sin tu OK explícito.

---

## 8. Decisiones confirmadas (2026-05-09)

- [x] **Stack base**: Astro 5 + React 19 + TypeScript + Tailwind v4 + shadcn/ui.
- [x] **Estado**: TanStack Query (server) + Zustand (client).
- [x] **Forms**: React Hook Form + Zod.
- [x] **Tipos del backend**: autogenerados con **`openapi-typescript`** (sin hooks autogenerados, los escribimos a mano para tener control del cache).
- [x] **Build target**: **static-only** (`@astrojs/static`). Sin SSR, sin Astro middleware.
- [x] **Library de componentes**: **shadcn/ui** (Radix primitives + Tailwind).
- [x] **Iconos**: Lucide React.
- [x] **Toasts**: sonner.
- [x] **Fechas**: date-fns con locale `es`.
- [x] **Theme inicial**: claro fijo. Toggle dark/light en Iter 9.
- [x] **Geist fonts en repo**: `frontend/web/public/fonts/` (variable TTF).
- [x] **Subdominio en login**: visible y editable en dev (`localhost`); oculto en prod (`<tenant>.carwash.mukusoft.com`).
- [x] **Multi-tenant**: el frontend nunca manda `lavanderia_id`, se deduce del token o del Host.
- [x] **Auth storage**: JWT en `localStorage`. Auto-redirect a `/login` en 401.
- [x] **Legacy**: `frontend/streamlit/` queda en el repo como referencia funcional. `frontend/flet/` se eliminó.

### Decisiones operativas confirmadas

- [x] **Package manager**: **bun**. Comandos `bun install`, `bun dev`, `bun run gen:api`, etc.
- [x] **Lint/format**: **Biome**. Un único `biome.json` + `bun run format` / `bun run lint`.

### Pendientes (no bloquea Iter 0)

- [ ] **Charts library**: Recharts vs Tremor. Decidir cuando lleguemos a Iter 7.
- [ ] **Toggle dark mode**: en Iter 9 se decide si seguimos al SO o agregamos un switch manual.

---

## 9. Consideraciones del stack

### 9.1 Astro static-only — qué implica

- Todas las páginas se prerrenderizan en build. **No hay servidor Node corriendo** en runtime.
- Auth, fetch a backend, todo eso vive en JS del cliente (islas React).
- Ventaja: deployment trivial — `astro build` da un `dist/` estático que sirve cualquier nginx, S3, Cloudflare Pages, etc.
- Limitación: no podés leer cookies en SSR (las leés desde JS del cliente). Para nuestro caso (JWT en localStorage, multi-tenant por subdominio), no es problema.

### 9.2 Generación de tipos — workflow

- Cada vez que el backend cambia algún schema o endpoint:
  ```bash
  cd frontend/web
  pnpm gen:api    # corre scripts/gen-api-types.sh contra http://localhost:8000
  ```
- El archivo `src/lib/api/schema.d.ts` se comitea. CI puede chequear que no haya drift entre el código y el openapi.json del backend.
- Si un endpoint cambia el schema, los hooks de TanStack Query van a tirar errores de TS al instante. Mejor que descubrirlo en runtime.

### 9.3 shadcn/ui — qué hay que entender

- **No es un paquete npm normal.** Los componentes se copian al repo con `npx shadcn@latest add button` y viven en `src/components/ui/`. Los modificás a gusto.
- Usa `class-variance-authority` (cva) para variantes y `tailwind-merge` para mergear classes.
- `components.json` define las paths y el tema base. Lo configuramos para usar nuestras tokens del DS.
- Cada componente es **headless por dentro** (Radix UI) + estilado con Tailwind. Accesible por default.

### 9.4 Multi-tenant en el frontend

- **Dev** (`localhost:4321` por defecto en Astro): subdominio en el form de login, mandado en el body del `POST /auth/login`.
- **Prod** (`<tenant>.carwash.mukusoft.com`): el frontend corre en el mismo subdominio. El campo subdominio se oculta. El backend lee del header `Host`.
- Si el frontend se sirve desde un dominio distinto al backend (ej. `app.carwash.mukusoft.com` ↔ `api.carwash.mukusoft.com`): hay que ajustar `CORS_ALLOW_ORIGIN_REGEX` en el backend.

### 9.5 Forma de importar tipos del backend

```ts
import type { components } from "@/lib/api/schema";
type SaleResponse = components["schemas"]["SaleResponse"];
type ExpenseCreate = components["schemas"]["ExpenseCreateRequest"];
```

Pydantic v2 → OpenAPI 3.1 → openapi-typescript → TS 5 strict. Cero esquemas duplicados.

### 9.6 Rutas dinámicas

- `pages/sales/[id]/edit.astro`: client-only fetch. La página es un shell vacío hasta que el JS se hidrata, lee `id` de la URL, hace `GET /sales/{id}` y rellena el form. Con static-only no hay prerender condicional realista para IDs cambiantes.

### 9.7 Reglas para no caer en gotchas de migraciones previas (Streamlit, Flet)

- Cualquier valor que el backend pueda devolver `null` se trata defensivamente en TS.
- 401 → siempre redirige a `/login` desde el client interceptor. Nunca dejes que un componente intente renderizar con sesión expirada.
- Permisos: chequeamos del lado del cliente para esconder UI, pero **siempre** confiamos en lo que devuelve el backend. Una UI escondida no protege; el 403 sí.
- Multi-tenant: nunca mandar `lavanderia_id` desde el frontend. Si en algún payload aparece, es bug.

---

## 10. Aprendizajes que se trasladan del intento Flet

Aunque el código Flet ya no está en el repo, el ejercicio dejó valor que se reusa:

- **Plan iterativo**: idéntico (§6).
- **Decisiones de auth, permisos, multi-tenant**: idénticas (§5, §8).
- **Tokens del DS**: ya estaban definidos como Python dicts; ahora viven como CSS variables (`global.css`).
- **Mapeo de endpoints a views**: idéntico (§3) — sabemos qué endpoint pega cada pantalla, qué validaciones aplican y qué flujos esperan los usuarios.
- **Boceto de UX para cada pantalla**: ya iteramos login, dashboard, sales form, sales list. Esa decisión de UX se reaplica directo en React.
- **Bugs de backend descubiertos** (migration `c7d3f0a1b2e4` pendiente, `coalesce` con GROUP BY) ya quedaron resueltos durante el intento Flet.
