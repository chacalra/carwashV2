# Progreso del frontend web (Carwash by Mukusoft)

> Snapshot del estado del frontend nuevo en `frontend/web/`. Sirve como handoff
> para próximos agentes. Para el plan original ver
> [PLAN_FRONTEND.md](./PLAN_FRONTEND.md).

## Resumen rápido

- **Stack**: Astro 5 (static-only) + React 19 islands + Tailwind v4 + shadcn/ui +
  TanStack Query v5 + Zustand + RHF + Zod + openapi-typescript + sonner + date-fns
  + Lucide + Recharts. **bun** como package manager y runtime de tests.
- **Branding**: Mukusoft (deep teal `#0F4C4C`, sky `#5FB6E5`, mint `#3DA89F`).
  Tokens en `src/styles/global.css`.
- **Multi-tenant**: subdominio en prod (`<tenant>.carwash.mukusoft.com`), campo
  `subdominio` en login en dev (`localhost`/`127.0.0.1`).
- **Auth**: JWT en localStorage (`carwash.session`), Zustand store, `AuthGuard`
  redirige a `/login`.
- **Tests**: 67 frontend (Vitest + RTL + MSW + happy-dom) + 222 backend
  (pytest) verde. JSON report en `frontend/web/test-results/last-run.json`
  para que un agente lea fallos.
- **Dark mode**: toggle light / dark / system en el TopBar, persiste en
  `localStorage.carwash.theme`, anti-flash en `Base.astro`. Tokens dark
  alineados con `ds-foundations` (con accent en mint Mukusoft, no en azul
  genérico).

## Estado de producción (live desde 2026-05-12)

- **URLs vivas**:
  - `https://demo.carwash.mukusoft.com` — tenant demo con datos seed (30 ventas + 10 egresos).
  - `https://autocare.carwash.mukusoft.com` — cliente real Rafael Almada (479 ventas + 64 egresos importados del legacy SQLite via `scripts/import_autocare_legacy.py`).
- **Infra**: VPS Contabo `mukusoft` (164.68.127.94, Ubuntu 24.04). Stack en Docker en `/home/ramon/projects/carwash-v2/`. NGINX Proxy Manager hace de reverse proxy + SSL Let's Encrypt por subdominio.
- **Credenciales admin**: `Demo#2026` y `Autocare#2026` (guardadas en KeePassXC ~/Documents/keepassXC/muku.kdbx pendiente de configurar; la maestra de la base creada nueva fue elegida por el usuario).
- **CD activo**: push a `main` dispara workflow `.github/workflows/deploy.yml` → corre tests backend+frontend → SSH al VPS → `git pull` + `docker compose up -d --build` → smoke test `/api/health`. Tiempo total ~2 min. Secrets `SSH_HOST/USER/PORT/PRIVATE_KEY` en GitHub. Deploy key dedicada (la privada vive solo en GitHub Secrets desde el cleanup).
- **Backup automático**: cron diario 03:00 hora VPS, dump comprimido en `~/backups/`, retención 30 días, log en `~/backups/backup.log`. Script `scripts/backup_db.sh`.
- **Doc de deploy**: `docs/DEPLOY.md` con 12 secciones (manual bootstrap, alta cliente, troubleshooting).

### Pendientes operativos (no urgentes)

1. Guardar `.env` de prod en KeePassXC. La base `muku.kdbx` está creada pero el usuario no recuerda la maestra que recién fijó (probablemente la confundió con otra). Si se pierde, regenerar la base es trivial (es vacía). El `.env` vive seguro en el VPS hoy.
2. Avisarle a Rafael por canal seguro con URL `https://autocare.carwash.mukusoft.com` + `admin/Autocare#2026`, pedirle que cambie password al primer login.
3. Sentry / monitoreo de errores en runtime (opcional, no bloqueante).

## Iteraciones — estado

| # | Nombre | Estado | Archivos clave |
|---|---|---|---|
| 0 | Andamiaje (config, tokens, fonts) | ✅ | `astro.config.mjs`, `global.css`, `lib/api/client.ts` |
| 1 | Login | ✅ | `components/auth/LoginForm.tsx`, `lib/auth/store.ts` |
| 2 | Shell + Dashboard básico | ✅ | `components/shell/*`, `components/DashboardView.tsx` |
| 3 | Nueva venta | ✅ | `components/sales/SalesNewView.tsx`, `lib/api/queries/sales.ts` |
| 4 | Movimientos (lista) | ✅ | `components/sales/MovementsView.tsx` |
| 5 | Editar venta | ✅ | `components/sales/SalesEditView.tsx` (reusa `SalesFormInner`) |
| 6 | Egresos (form) | ✅ | `components/expenses/ExpensesNewView.tsx` |
| 7 | Reportes / Export | ⏭️ saltado — el contenido valioso fue al dashboard |
| 8 | Settings / Catálogos | ✅ | `components/settings/CatalogManager.tsx`, `SettingsView.tsx` |
| **Dashboard A** | KPIs + period selector + deltas | ✅ | `DashboardView.tsx`, `lib/periods.ts` |
| **Dashboard B** | Trend bar + 2 donuts (Recharts) | ✅ | `components/dashboard/Charts.tsx`, endpoint `/reports/daily-sales` |
| **Tokens DS** | Alineación con ds-foundations (pos-fg/neg-fg/warn-fg, overlay, glass, pill) + bloque `.dark` semántico | ✅ | `src/styles/global.css` |
| 9 | Dark mode toggle | ✅ | `lib/theme/store.ts`, `components/shell/ThemeToggle.tsx`, `layouts/Base.astro` |
| 9b | Responsive review (SalesNew bottom bar, Movements cards, Dashboard 2x2) | ✅ | `SalesNewView.tsx`, `MovementsView.tsx`, `DashboardView.tsx` |
| **Tests core** | ExpensesNewView, CatalogManager, DashboardView | ✅ | `test/*.test.tsx` (56 tests) |
| **Dashboard C** | Clientes del período + Top productos | ✅ | `backend/api/routers/reports.py`, `DashboardView.tsx` |
| 9c | Error boundary global + AlertDialog (glass) + filter badge + toast borde lateral | ✅ | `components/ErrorBoundary.tsx`, `components/ui/alert-dialog.tsx`, `AppProviders.tsx`, `MovementsView.tsx` |
| 10 | Marco de marca: store de branding + slots de logo (login + sidebar) listos para tematización por tenant | ✅ | `lib/branding/store.ts`, `components/branding/Logos.tsx`, `LoginForm.tsx`, `AppSidebar.tsx`, `public/brand/*.png` |
| B1 | Backend: campos de branding en `lavanderia` + `tenant` anidado en login + `setBrand` enganchado en frontend | ✅ | `database/schema.py`, `alembic/versions/d4f2a1c8e3b9_*`, `api/schemas/auth.py`, `api/routers/auth.py`, `lib/api/queries/auth.ts` |
| B1 CLI | CLI de branding por tenant (`set-branding`, `clear-branding`, `show-tenant`) con validación hex/URL | ✅ | `backend/cli/__main__.py`, `backend/cli/branding.py`, `tests/test_cli_branding.py` |
| B2 CLI | `create-tenant` atómico: lavandería + rol admin + todos los permisos + usuario admin en una transacción. Subdominio normalizado y validado (`^[a-z0-9-]+$`). Rollback completo si falla cualquier paso. | ✅ | `backend/cli/create_tenant.py`, `backend/cli/__main__.py`, `tests/test_cli_create_tenant.py` (13 tests) |
| D1 containerización | Stack docker completo: `backend.Dockerfile` (Python 3.13 + uv + entrypoint que migra + sembra permisos + arranca uvicorn), `frontend/web/Dockerfile` (multi-stage Bun build + nginx alpine), `docker-compose.yml` (db + backend + frontend con red interna). Login y CRUD verificados en `localhost:8080`. | ✅ | `backend.Dockerfile`, `frontend/web/Dockerfile`, `frontend/web/nginx.conf`, `docker-compose.yml`, `scripts/docker_entrypoint.sh`, `.dockerignore`, `.env.example` |
| D2 seed demo | Script `scripts/seed_demo.py` idempotente: pobla un tenant con catálogo genérico de lavadero (5 servicios, 6 productos, 4 tipos vehículo, 5 categorías egreso), ~30 ventas y 10 egresos en últimos 30 días, distribución 70/20/10 (servicio solo / mezcla / producto solo), ~20% con factura. Soporta `--reset`. | ✅ | `scripts/seed_demo.py` |
| D3 doc deploy | `docs/DEPLOY.md` con 12 secciones: inventario VPS, DNS, apagar legacy, clonar repo, .env de prod, build + up con override, configurar NPM, crear tenants, smoke test, operación, troubleshooting, alta de cliente. Cubre el flujo manual completo. CD automático con GitHub Actions queda para iteración siguiente. | ✅ | `docs/DEPLOY.md`, `docker-compose.prod.yml` |
| D4 deploy real | Bootstrap manual completo del VPS ejecutado siguiendo `DEPLOY.md`: carwash viejo apagado, repo clonado, `.env` generado con secrets aleatorios (permisos 600), stack levantado con `docker-compose.prod.yml`, NPM con dos Proxy Hosts (`demo.` y `autocare.`) + SSL Let's Encrypt, tenants `demo` y `autocare` creados, seed demo aplicado, import legacy de AutoCare ejecutado (479 ventas + 64 egresos). Smoke test login + `/api/reports/sales-summary` verde contra prod. | ✅ | en VPS `/home/ramon/projects/carwash-v2/` |
| D5 CD GitHub Actions | Workflow `deploy.yml` con dos jobs (`test`: pytest + bun test + bun build; `deploy`: SSH al VPS + `git reset --hard` + `docker compose up -d --build` + health check). Actions bumpeadas a Node 24 (`checkout@v6`, `setup-uv@v8.1.0`, `setup-bun@v2.2.0`) salvando el deadline de junio 2026. Script `scripts/deploy.sh` corre dentro del VPS. Deploy key dedicada (privada solo en GitHub Secrets). Tiempo total push→prod ~2 min. Validado tres deploys consecutivos verdes. | ✅ | `.github/workflows/deploy.yml`, `scripts/deploy.sh` |
| D6 backup diario | Script `scripts/backup_db.sh` que hace `pg_dump` del Postgres del stack, comprime con gzip, retención de 30 días (los más viejos se borran solos), log en `~/backups/backup.log`. Cron instalado en el VPS: `0 3 * * * .../backup_db.sh`. Validado manualmente. | ✅ | `scripts/backup_db.sh`, crontab del usuario `ramon` en VPS |
| B11 precio 0 hard-stop | El form bloquea el submit en modo `create` cuando alguna línea tiene `unitPrice <= 0`. Zod schema cambió de `min(0)` a `positive()`. UI: botón "Cobrar" deshabilitado, label vuelve a "Precio en 0", banner warn en el sidebar del resumen explicando por qué. Modo `edit` no bloquea (data legacy con precio 0 sigue editable). Resumen del carrito: conteo del header pasó a unidades totales (no líneas distintas). | ✅ | `frontend/web/src/components/sales/SalesNewView.tsx`, `frontend/web/test/SalesFormInner.test.tsx` (+1 test) |
| B10 cart summary | Nuevo componente `<CartSummary>` para el resumen del form de venta (sidebar desktop + drawer mobile). Agrupa por tipo (Servicios / Productos) con encabezado, conteo y subtotal por grupo. La cantidad solo aparece cuando es > 1 (evita el "1×" omnipresente). Patrón estilo Amazon. Reemplaza la lista plana que costaba leer. | ✅ | `frontend/web/src/components/sales/SalesNewView.tsx` |
| B9 items UX | Columna ITEMS rediseñada: nuevo `<ItemsSummary>` con ícono + nombre principal + chip "+N" para extras (servicio en mint deep, producto en sky). Cuando todas las filas filtradas comparten exactamente los mismos items, la columna se colapsa y los items aparecen en el banner contextual junto al cliente. Reduce la repetición visual cuando se filtra por una empresa que siempre compra el mismo lavado. | ✅ | `frontend/web/src/components/sales/MovementsView.tsx`, `frontend/web/test/MovementsView.test.tsx` (+1 test) |
| B8 movements UX | Tres mejoras de lectura sobre la tabla de ventas: (1) banner del cliente único + columna Cliente colapsada cuando todas las filas comparten cliente (típico al filtrar 1 razón social); (2) breakdown de totales por razón social cuando hay 2+ empresas seleccionadas; (3) chips removibles individuales por filtro (tipo de cobro, búsqueda, cada razón social) en lugar del contador genérico "N filtros activos". | ✅ | `frontend/web/src/components/sales/MovementsView.tsx`, `frontend/web/test/MovementsView.test.tsx` (+3 tests) |
| B7 filtro razón social | Multiselect "Razón social" en `MovementsView` con opciones derivadas de las ventas facturadas del rango. Toggle "Excluir seleccionadas" dentro del popover (aparece cuando hay alguna elegida). Combina con search, tipo de cobro y rango. Limpia automáticamente selecciones obsoletas si cambia el rango. Migración de paridad con legacy Streamlit. | ✅ | `frontend/web/src/components/sales/MovementsView.tsx`, `frontend/web/test/MovementsView.test.tsx` (+3 tests) |
| B6 import legacy | Script `scripts/import_autocare_legacy.py`: importa SQLite legacy → V2 en transacción única. Mapea catalogos, vehículos (excluye placeholder `0000`, conserva `9999` como histórico de matrícula no registrada), egresos y ventas (1 income legacy = 1 venta + 1 detalle). Facturas crean cliente particular por RUC; sin factura van al genérico "Sin nombre". Servicio "Perfume" descartado (sin uso). Soporta `--dry-run` y `--force`. Ejecutado contra local: 468 ventas + 64 egresos importados. | ✅ | `scripts/import_autocare_legacy.py`, datos en `datos/autocare_legacy.db` (gitignored) |
| B5 vehículo acoplado | Regla nueva: vehículo obligatorio si la venta incluye servicio, prohibido si no. Backend valida en `validate_sale_data` (create + edit) con 400 ante mismatch. Frontend deriva `hasService` de los items: muestra inputs de placa + tipo solo cuando hay servicio, los limpia silenciosamente al sacar el último servicio. Reemplaza el toggle manual `vehiculo_enabled` por estado derivado. Documentado en `reglas_modelo_negocio.md` §6. | ✅ | `backend/services/sale_service.py`, `tests/test_sale_service.py` (+6), `frontend/web/src/components/sales/SalesNewView.tsx`, `frontend/web/test/SalesFormInner.test.tsx`, `frontend/web/test/saleToFormValues.test.ts`, `docs/reglas_modelo_negocio.md` |
| B3 | CRUD roles + usuarios + permisos en backend y frontend (paridad con legacy Streamlit) + redirect post-login según permisos | ✅ | `api/routers/{permissions,roles,users}.py`, `components/settings/{RolesManager,UsersManager}.tsx`, `nav-config.ts`, `LoginForm.tsx` |
| B3 guard | Guard "último administrador": no permite desactivar usuario/rol ni quitar `settings` si dejaría al tenant sin admins. Mensajes humanos. | ✅ | `services/access_service.py`, `api/routers/{roles,users}.py` |
| 11 pulido visual | Glow mint en CatalogTile, SegmentedField con degradado de marca activo, total con `bg-clip-text`, LicensePlate como matrícula real, hover de filas en mint, sparklines más visibles, sidebar item activo con rail, avatar con degradado, botón Cobrar con estados | ✅ | `global.css` (`@utility shadow-glow-mint*`, `@custom-variant hover-any`), `SalesNewView.tsx`, `MovementsView.tsx`, `DashboardView.tsx`, `AppSidebar.tsx`, `StatCard.tsx`, `LicensePlate.tsx` |
| 12 brand runtime | Tematización completa por tenant: `--brand-deep/sky/mint` referenciales en `:root`, sobreescritas por `applyTenantBrand`. Charts 1/2/3 también. `refine()` con `color-mix(oklch)` desatura colores crudos del cliente. Tu paleta Mukusoft default queda sin transformación (intencional). | ✅ | `lib/branding/store.ts` (`refine()`, `REFINE_RATIO=78`), `styles/global.css` (vars referenciales) |

## Archivos creados/modificados en esta sesión

### Frontend (`frontend/web/`)
- `src/lib/theme/store.ts` — Zustand `light | dark | system`, persiste en `localStorage.carwash.theme`, listener `prefers-color-scheme`.
- `src/components/shell/ThemeToggle.tsx` — dropdown shadcn (Sol/Luna/Monitor) con ícono animado en el trigger.
- `src/components/shell/TopBar.tsx` — monta `<ThemeToggle />` a la derecha.
- `src/layouts/Base.astro` — script `is:inline` anti-flash que aplica `.dark` antes del primer paint.
- `src/styles/global.css` — bloque `.dark` con tokens semánticos del DS, agregados `--color-pos-fg/--color-neg-fg/--color-warn-fg`, `--color-bg-overlay`, `--shadow-glass`, `--radius-pill`. Sidebar dark migrado de azul Tailwind genérico a paleta Mukusoft.
- `src/components/dashboard/Charts.tsx` — hex hardcodeados → `var(--…)` para que Recharts reaccione al cambio de tema.
- `test/ThemeToggle.test.tsx` — 4 tests (store + montaje del trigger).
- `package.json` — agregado `recharts`, vitest stack, scripts `test`/`test:watch`.
- `vitest.config.ts`, `test/setup.ts`, `test/mocks/{server,handlers}.ts`, `test/utils/renderWithProviders.tsx`.
- `test/format.test.ts`, `test/saleToFormValues.test.ts`, `test/MovementsView.test.tsx`, `test/SalesFormInner.test.tsx`, `test/smoke.test.ts`.
- `src/lib/api/queries/{auth,reports,catalogs,clients,vehicles,sales,expenses}.ts`.
- `src/lib/{format,periods}.ts`.
- `src/lib/auth/store.ts`.
- `src/components/AppProviders.tsx`.
- `src/components/auth/{LoginForm,AuthGuard}.tsx`.
- `src/components/shell/{Shell,AppSidebar,TopBar,nav-config}.ts(x)`.
- `src/components/shared/{StatCard,EmptyState,MoneyText}.tsx`.
- `src/components/dashboard/Charts.tsx` (TrendChart + DonutChart con Recharts).
- `src/components/sales/{SalesNewView,MovementsView,SalesEditView}.tsx`.
- `src/components/expenses/ExpensesNewView.tsx`.
- `src/components/settings/{CatalogManager,SettingsView}.tsx`.
- `src/components/PendingPage.tsx` (placeholder para rutas sin implementar — ya casi no se usa).
- `src/pages/{index,login,dashboard}.astro`, `src/pages/sales/{new,index,edit}.astro`, `src/pages/expenses/new.astro`, `src/pages/reports.astro`, `src/pages/settings/index.astro`.
- `src/styles/global.css` (tokens Mukusoft + shadcn compat + sidebar tokens).
- `.gitignore` — agregado `test-results/` y `coverage/`.

### Backend
- `backend/api/main.py` — CORS regex incluye `127.0.0.1`.
- `backend/api/schemas/reports.py` — agregado `DailySalesItem`.
- `backend/api/routers/reports.py` — agregado `GET /reports/daily-sales`.

## Decisiones tomadas

- **Astro static-only** (sin SSR). Para rutas dinámicas como `/sales/edit?id=X`,
  el id se lee del URL en el cliente.
- **shadcn/ui copy-paste** (no librería). Vive en `src/components/ui/`.
- **openapi-typescript** para tipos del backend. Regenerar con `bun run gen:api`
  cuando cambia el backend.
- **Donuts en lugar de listados** en el dashboard, pero los listados detallados
  se mantienen abajo con barra horizontal de %.
- **Dashboard default**: período "Esta mes". Igual que el legacy Streamlit.
- **`window.location.href`** para navegar entre páginas (Astro static; no hay
  router cliente). Cada navegación hidrata su Island.
- **Tests con MSW**: handlers vacíos por default; cada test agrega los suyos
  con `server.use(...)`. `API_BASE` = `http://localhost:8000`.
- **Auth en tests**: `useAuthStore.setState(...)` en `beforeEach` para sembrar
  permisos sin pasar por login real.
- **Catalog mutations factory**: `useCatalogMutations(resource)` para evitar
  duplicar 20 hooks. Una sola función con switch de path.
- **`SalesFormInner`** acepta `mode: "create" | "edit"` + `defaultValues` para
  reutilizarse en `/sales/new` y `/sales/edit`.
- **Accent en dark = mint Mukusoft** (`#3DA89F`), no el `#3B82F6` del DS
  genérico. Decisión consciente para mantener marca; documentada acá como
  divergencia intencional.
- **Halo radial del body** (gradientes brand-sky/brand-deep) es divergencia
  intencional respecto al DS para reforzar marca. En dark se intensifica.
- **Branding runtime**: la app entera se viste del tenant cuando hay
  `color_primario`/`color_secundario` cargados. Mecanismo: `:root` declara
  `--brand-deep/sky/mint` (defaults Mukusoft); `applyTenantBrand` (en
  `lib/branding/store.ts`) sobreescribe esas vars con los colores del
  tenant pasados por `refine()` (desatura con `color-mix(oklch, X 78%,
  #888 22%)`). Charts 1/2/3 también heredan el branding; charts 4/5
  (`pos`, `warn`) quedan fijos por ser semánticos. Tu paleta Mukusoft
  default NO pasa por `refine()` (es decisión consciente: tu marca ya está
  pulida; el transformador es para colores random de clientes).
- **Botón "Cobrar" en `bg-pos` (verde) NO sigue el branding**. Es
  semántico (verde = ingreso financiero), no de marca. Cuando `total === 0`
  se desatura (`bg-pos/30 text-white/80`) para comunicar "no se puede
  cobrar todavía". Cuando hay total: `bg-pos` pleno + ring + shadow.

## Gotchas + workarounds

1. **`z.coerce.number()` rompe inferencia con RHF v7 zodResolver**. Genera tipo
   genérico `TFieldValues` en lugar del shape concreto. Workaround: usar
   `z.number()` y convertir en `onChange`. Visible en
   `ExpensesNewView.tsx`.
2. **Recharts 3.x formatter types**. El callback `formatter` recibe
   `ValueType | undefined`, no `number`. Workaround: dejar params sin tipo
   explícito y `Number(v)` en el body. Ver `Charts.tsx`.
3. **`window.confirm` no existe en happy-dom**. `vi.spyOn(window, "confirm")`
   falla. Workaround: `window.confirm = vi.fn(() => true)`. Ver
   `MovementsView.test.tsx`.
4. **CORS dev**: el backend tiene regex `r"https?://(localhost|127\.0\.0\.1)(:\d+)?"`
   y el frontend corre en `localhost:4321`. Si Astro arranca en `127.0.0.1`,
   incluir ambos.
5. **`useFieldArray` + `form.watch`** no siempre actualiza el padre cuando
   cambian Controller hijos. Workaround: usar `useWatch({ control, name })` para
   suscripciones granulares (importante en `SalesNewView.tsx` para el total).
6. **Ojo con cwd en sesiones largas de bash**: el shell pierde cwd entre
   comandos cuando hay muchos. Siempre `cd frontend/web` antes de `bun run …`
   o usar paths absolutos.
7. **Radix dropdown no abre en happy-dom**: `PointerEvent` no está completo,
   `findByText("Oscuro")` después de `fireEvent.click(trigger)` no encuentra
   el item. Workaround: testear el store directamente (es donde vive la lógica)
   y limitar el test del componente al render del trigger. Visible en
   `test/ThemeToggle.test.tsx`.
8. **Inputs con prefix wrapper**: cuando un Input está envuelto en un `<div>`
   con span de prefijo (ej. `Gs.`), el `<FormLabel htmlFor>` apunta al div en
   vez de al input, y `getByLabelText("Monto")` falla. Workaround:
   `getByRole("spinbutton")` para inputs `type="number"`. Visible en
   `test/ExpensesNewView.test.tsx` y `test/CatalogManager.test.tsx`.
9. **PeriodSelector usa role="tab"**: en `DashboardView`, los botones de
   período (Hoy / Semana / Mes / Personalizado) tienen `role="tab"`, no
   "button". Para clickearlos en tests: `getByRole("tab", { name: "Hoy" })`.
10. **Recharts en happy-dom necesita `ResizeObserver`**: si no está stubeado,
    `ResponsiveContainer` falla silenciosamente. Workaround: en `beforeEach`,
    `globalThis.ResizeObserver ||= class { observe(){} unobserve(){} disconnect(){} }`.
    Visible en `test/DashboardView.test.tsx`.
11. **Mobile + desktop coexisten en happy-dom**: las clases `hidden md:block`
    son CSS-only y RTL ve ambos en el DOM. Tests que afirman "no está" sobre
    contenido visible en una sola breakpoint pueden romper. Workaround:
    `findAllByText` / `getAllByRole(...)[0]` o filtrar con `closest("tr")`.
    Visible en `test/MovementsView.test.tsx` y `test/SalesFormInner.test.tsx`.
12. **PNGs con "fondo blanco" disfrazado de transparente**: los exports de
    Canva/Photoshop a veces tienen el área "vacía" como `#FFFFFF` sólido en
    vez de transparencia real. `convert -trim` no los recorta. Workaround:
    `convert <in> -fuzz 5% -transparent white -trim +repage <out>` antes de
    cargarlos al repo. Aplicado a `public/brand/logo_*.png`.
13. **Tailwind v4 + `hover:` con `@media (hover: hover)`**: en v4 el variant
    `hover:` se envuelve en `@media (hover: hover)`. Algunos navegadores
    (Firefox + ciertos drivers) detectan mal el input primario y los hovers
    no disparan. Workaround: definir un `@custom-variant hover-any (&:hover)`
    en `global.css` y usar `hover-any:` en lugares críticos. Visible en
    `CatalogTile` y `SegmentedField`.
14. **Tailwind v4: `@utility` vs CSS plano para variants**: utilidades
    declaradas como `.foo { ... }` regular **no** soportan modificadores
    (`hover-any:foo` no se compila). Hay que declararlas con `@utility foo
    { ... }`. Visible en `shadow-glow-mint*`.
15. **Tailwind v4: opacity (`bg-x/10`) compila hex resuelto, no var**: si
    una var del `@theme` apunta a un hex literal, las utilidades con
    opacity (`bg-brand-mint/15`, `from-brand-deep/12`) compilan el hex
    pre-resuelto en la regla principal y solo el `@supports color-mix` usa
    `var()`. Sobreescribir la var en runtime no afecta la regla principal.
    Workaround: declarar las vars del `@theme` como **referenciales**
    (`--color-brand-mint: var(--brand-mint)`) con la "var real" en `:root`.
    Así el hex compilado igual termina apuntando a `var(--brand-mint)` y
    el branding runtime se propaga. Patrón documentado en `global.css`.

## Cómo correr

```bash
# Backend (raíz del repo)
uv run alembic upgrade head
uv run uvicorn backend.api.main:app --reload

# Frontend
cd frontend/web
bun install
bun run dev          # dev server localhost:4321
bun run build        # static build
bun run test         # run-once + JSON en test-results/last-run.json
bun run test:watch   # modo dev
bun run gen:api      # regenera src/lib/api/schema.d.ts desde /openapi.json
bun run type-check   # astro check + tsc --noEmit
bun run check        # biome check --write
```

Login dev: `admin` / `admin123` / subdominio `demo`.

## Permisos del backend (relevantes para UI)

- `dashboard` — (no se usa para gating todavía).
- `register_sale` — POST /sales, ve `/sales/new`.
- `edit_sale` — PUT /sales/{id}, ve botón Editar.
- `manage_sales` — DELETE /sales/{id}, ve botón Anular.
- `register_expense` — POST /expenses, ve `/expenses/new`.
- `movements` — GET /sales (lista), ve `/sales`.
- `export` — GET /reports/*, dashboard.
- `settings` — CRUD de catálogos, ve `/settings`.

El sidebar filtra ítems por `permissions.includes(item.permission)`.

## Pendientes / próximas tareas sugeridas

### Iter 9b — pulido restante
- ~~Dark mode toggle~~ ✅ hecho.
- Responsive review (mobile específicamente para tablas).
- Loading states más finos (algunos forms muestran solo el spinner del CTA).
- Error boundary global.
- Detalles del DS aún no aplicados: badge "× filtros activos" en filter bar,
  toast con borde lateral pos (`borderLeft 3px solid var(--pos)`), glass
  overlay para `AlertDialog` usando `--color-bg-overlay` + `--shadow-glass`.

### Dashboard "Pasada C" — ✅ hecho
- `GET /reports/customer-summary` y `GET /reports/product-summary` expuestos
  con permiso `export`.
- Schemas: `CustomerSummaryResponse`, `TopPlateItem`, `ProductSummaryResponse`,
  `TopProductItem`.
- Hooks: `useCustomerSummary`, `useProductSummary`.
- UI: secciones "Clientes del período" (3 StatCards + tabla top placas) y
  "Top productos" (lista con barra horizontal en `bg-brand-sky/60`).
- Si los endpoints fallan, las secciones se ocultan en silencio.

### Tests
- ~~Cubrir `ExpensesNewView`~~ ✅
- ~~Cubrir `CatalogManager`~~ ✅
- ~~Cubrir `DashboardView` con MSW~~ ✅ (incluye Pasada C)
- E2E con Playwright cuando el resto esté estable.

### Próximos pasos pendientes (orden sugerido)

Histórico cerrado:
1. ~~**`create-tenant` en el CLI**~~ ✅
2. ~~**Importación legacy del .db SQLite**~~ ✅ (AutoCare: 479 ventas + 64 egresos en prod, snapshot del 2026-05-12).
3. ~~**Containerización + docker compose**~~ ✅ (D1).
4. ~~**Seed demo idempotente**~~ ✅ (D2).
5. ~~**Doc de deploy `docs/DEPLOY.md`**~~ ✅ (D3).
6. ~~**Bootstrap manual de producción siguiendo el doc**~~ ✅ (D4).
7. ~~**CD con GitHub Actions (push main → deploy)**~~ ✅ (D5).
8. ~~**Backup diario automático**~~ ✅ (D6).

Operativos no urgentes:
- **`.env` de prod en KeePassXC**: pendiente. La base `~/Documents/keepassXC/muku.kdbx` está creada pero el usuario no recuerda la maestra que recién eligió. El `.env` vive en el VPS (permisos 600), regenerable si se pierde (con costo: relogueo masivo por nueva `AUTH_TOKEN_SECRET`).
- **Validación browser de prod por humano**: pendiente. Los dos subdominios responden 200 a `curl`, pero el usuario aún no completó el checklist visual completo (login + dashboard + venta nueva + edit + dark mode).
- **Aviso a Rafael** con URL `https://autocare.carwash.mukusoft.com` + credenciales + pedirle que cambie su password.

Features pendientes (no urgentes):
- **E2E con Playwright**: golden paths "registrar venta" y "registrar egreso" en navegador real.
- **Validación de contraste en CLI** (opcional): `set-branding` advierte si el `color_primario` no pasa AA contra blanco.
- **Sentry / monitoreo de errores en runtime**: hoy si el frontend explota en runtime nadie se entera salvo que Rafael avise.
- **Backups remotos**: hoy los backups viven solo en el mismo VPS. Si el VPS muere, se pierden con la DB.
- **Wildcard SSL** si la cantidad de clientes crece (hoy emitimos un cert por subdominio con HTTP challenge; sostenible hasta ~10-15 clientes).

### Otros
- Logo iso "C" del Carwash sigue como **draft**. El usuario quiere refinarlo
  más adelante (decidió posponer).
- `gen:api` se corre manualmente — considerar pre-commit hook.
