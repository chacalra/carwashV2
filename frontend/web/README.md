# Carwash Web (frontend)

Frontend web del producto Carwash de [Mukusoft](https://mukusoft.com), construido con
Astro + React + Tailwind v4 + shadcn/ui.

> Plan completo y estado del proyecto: [`docs/PLAN_FRONTEND.md`](../../docs/PLAN_FRONTEND.md)

## Requisitos

- **Bun** ≥ 1.1 (https://bun.sh)
- Backend Carwash corriendo localmente en `http://localhost:8000` (FastAPI)

## Setup inicial (única vez)

```bash
cd frontend/web
bun install
bun run gen:api      # genera src/lib/api/schema.d.ts desde el openapi.json del backend
```

> El backend tiene que estar levantado para que `gen:api` funcione.

## Comandos día a día

| Comando | Qué hace |
|---|---|
| `bun dev` | Levanta el dev server en `http://127.0.0.1:4321` con hot reload |
| `bun run build` | Genera el bundle estático en `dist/` |
| `bun run preview` | Sirve el bundle build localmente para QA |
| `bun run check` | Lint + format con Biome (autofix) |
| `bun run lint` | Solo lint |
| `bun run format` | Solo format |
| `bun run type-check` | `astro check` + `tsc --noEmit` |
| `bun run gen:api` | Regenera tipos desde `openapi.json` (re-correr cuando cambia el backend) |

## Configuración del backend

Por defecto el cliente apunta a `http://localhost:8000`. Para cambiar:

```bash
echo 'PUBLIC_API_BASE_URL=http://otro-host:8000' > .env
```

## Estructura

```
frontend/web/
├── public/fonts/         # Geist y Geist Mono variable
├── scripts/gen-api-types.sh
├── src/
│   ├── pages/            # routing Astro (file-based)
│   ├── layouts/          # Base.astro, Shell.astro (próximamente)
│   ├── components/
│   │   ├── ui/           # shadcn (init pendiente, ver abajo)
│   │   ├── shell/
│   │   ├── shared/
│   │   └── HelloCarwash.tsx   # placeholder de Iter 0
│   ├── lib/
│   │   ├── api/          # client.ts + schema.d.ts (autogen)
│   │   ├── auth/         # store Zustand
│   │   ├── format.ts
│   │   └── utils.ts      # cn helper
│   └── styles/global.css # tokens Mukusoft con @theme de Tailwind v4
├── astro.config.mjs
├── biome.json
├── components.json       # config shadcn/ui
├── package.json
└── tsconfig.json
```

## shadcn/ui

`components.json` ya está configurado. Para sumar componentes:

```bash
bunx shadcn@canary add button   # canary porque soporta Tailwind v4
bunx shadcn@canary add dialog
# ...etc
```

Los componentes se copian a `src/components/ui/` y los podés modificar libremente.

## Branding

Logo Mukusoft (parent brand): `/DesignGuide/...`
Iso de Carwash (draft): pendiente de finalizar (ver §1 de PLAN_FRONTEND.md).
