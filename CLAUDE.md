# CLAUDE.md

## Running the App

```bash
uv run streamlit run app.py
uv run pytest tests/ -q
```

Database path in production (Render): `/var/data/carwash.db/carwash.db`
Database path local: auto-created on first run via `database/connection.py` (reads `DATA_DIR` env var, defaults to `data/`)

## Architecture

Strict unidirectional layering: `ui/` → `services/` → `repositories/` → `database/`

- **`app.py`**: Entry point. Calls `initialize_app()` (schema + seed) on every run, then routes to UI views via sidebar radio. Calls `show_notifications()` after login check.
- **`database/schema.py`**: `create_tables()` creates all tables + runs all migrations (migrate_v2 through migrate_v5). Each migration uses `PRAGMA table_info` to check before `ALTER TABLE`.
- **`database/seed.py`**: Seeds roles/permissions and user `rafael/admin` (role `maximo`). No catalog data seeded — client configures own services/categories/vehicle types.
- **`repositories/`**: Pure data access. Each function opens its own connection with `try/finally` close. Never contains business logic.
- **`services/`**: Business logic and validation. Raises `ValueError` for invalid inputs.
- **`ui/`**: Streamlit views. Each is a `render_*()` function. Catches `ValueError` and shows `st.error()`. Never writes SQL directly.
- **`utils/notifications.py`**: `notify(msg)` queues a toast in session_state. `show_notifications()` in app.py flushes the queue with `st.toast()` on each render.

## Key Conventions

- Dates: `TEXT` in `YYYY-MM-DD`. Timestamps: `YYYY-MM-DD HH:MM:SS`.
- Amounts: Paraguayan Guaraní (Gs.), stored as `REAL`.
- Soft deletes via `is_active` on catalog tables.
- `connection.row_factory = sqlite3.Row` — access by column name.
- Streamlit `st.form()` does not allow interactive widgets inside. Fields needing dynamic behavior (plate lookup, invoice checkbox) go **outside** the form using `st.session_state`.
- New DB columns always via `migrate_vN()` in `schema.py`, called at end of `create_tables()`.
- All tables: no IDs shown to users in dataframes (`hide_index=True`, ID columns excluded).

## Database Schema (current)

### Catalog tables (all have `id`, `name UNIQUE`, `is_active`, `created_at`)
- `services` — car wash services
- `expense_categories` — expense categories
- `vehicle_types` — vehicle types
- `roles` — user roles

### `role_permissions` (`id`, `role_name`, `permission` — UNIQUE together)

### `users` (`id`, `name`, `role`, `password_hash`, `is_active`, `created_at`)

### `vehicles` (`id`, `license_plate UNIQUE`, `vehicle_type_id FK→vehicle_types`, `owner_name`, `phone`, `created_at`)

### `incomes`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| date | TEXT | YYYY-MM-DD |
| service_id | FK→services | |
| amount | REAL | |
| payment_method | TEXT | nullable — Efectivo/Transferencia/Tarjeta/QR |
| notes | TEXT | nullable |
| vehicle_id | FK→vehicles | nullable (migrate_v2) |
| payment_type | TEXT | Contado/Credito, default Contado (migrate_v3) |
| requires_invoice | INTEGER | 0/1, default 0 (migrate_v3) |
| ruc_ci | TEXT | nullable (migrate_v3) |
| razon_social | TEXT | nullable (migrate_v3) |
| created_by | TEXT | nullable — user_name who registered (migrate_v4) |
| created_at | TEXT | |

### `expenses`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| date | TEXT | YYYY-MM-DD |
| category_id | FK→expense_categories | |
| amount | REAL | |
| description | TEXT | nullable |
| has_iva | INTEGER | 0/1, default 0 (migrate_v5) |
| created_by | TEXT | nullable — user_name who registered (migrate_v4) |
| created_at | TEXT | |

## Views (sidebar navigation)

| View label | Permission | File | Notes |
|-----------|-----------|------|-------|
| Dashboard | dashboard | `ui/dashboard.py` | Summary cards with delta vs prev period, bar charts, customer stats, contado/credito breakdown |
| Registrar ingreso | register_income | `ui/incomes_form.py` | Plate lookup outside form (on_change), pre-fills ALL fields from last income of that plate |
| Editar ingreso | edit_income | `ui/edit_income_view.py` | Only today/yesterday records; date, plate, amount locked |
| Registrar egreso | register_expense | `ui/expenses_form.py` | IVA checkbox |
| Movimientos | movements | `ui/movements_view.py` | Period selector (Hoy/Esta semana/Este mes/Personalizado), search by plate/owner, Si/No for IVA |
| Exportar | export | `ui/export_view.py` | CSV/Excel export |
| Configuracion | settings | `ui/settings_view.py` | CRUD for services, expense_categories, vehicle_types, roles+permissions, users |

## Permissions system

Defined in `services/auth_service.py`:
- `dashboard`, `register_income`, `edit_income`, `register_expense`, `movements`, `export`, `settings`

Default roles (seeded):
- `maximo`: all permissions
- `operador`: `register_income`, `edit_income`

## Key service logic

### `services/income_service.py`
- `validate_income_data()`: validates date, service (active), amount > 0, payment_type in (Contado/Credito), invoice fields if requires_invoice
- `register_income()`: validates → find_or_create_vehicle → create_income. Accepts `created_by`.
- `edit_income()`: same validation, calls update_income. Does NOT update `created_by`.

### `services/vehicle_service.py`
- `find_or_create_vehicle()`: if plate exists → update vehicle (merges: keeps existing owner/phone if new values are empty). If new → create.
- `normalize_plate()`: strip + uppercase.

### `services/report_service.py`
- `get_summary(start, end)`: income_total, expense_total, net_balance, service_count, income_breakdown, expense_breakdown, payment_breakdown (contado/credito).
- `get_customer_summary(start, end)`: unique_vehicles, recurring_customers, new_customers, top_plates.

### `utils/date_shortcuts.py`
- `get_period_range(period)`: returns (start, end) for "Hoy", "Esta semana", "Este mes".
- `previous_period(start, end)`: returns equivalent prior period for delta comparison.

## Income form — plate pre-fill flow

1. `st.text_input(key="plate_search", on_change=_on_plate_change)` outside form
2. `_on_plate_change` → `find_vehicle_by_plate` → if found: store in `session_state["found_vehicle"]` + `get_last_income_by_vehicle` → store in `session_state["last_income"]` + set `session_state["requires_invoice_cb"]`
3. Form renders with defaults from `found_vehicle` (type/owner/phone) and `last_income` (service/amount/payment_method/payment_type/notes/ruc_ci/razon_social)
4. On success: pop `plate_search`, `found_vehicle`, `last_income`, `requires_invoice_cb` + `st.rerun()`

## Migrations history

| Migration | Columns added | Table |
|-----------|--------------|-------|
| migrate_v2 | vehicle_id | incomes |
| migrate_v3 | payment_type, requires_invoice, ruc_ci, razon_social | incomes |
| migrate_v4 | created_by | incomes + expenses |
| migrate_v5 | has_iva | expenses |
| migrate_users_auth | password_hash (recreate table) | users |

## Customer stats — exclusions

`get_customer_stats()` in `repositories/incomes_repository.py` excludes placeholder plates `9999` and `0000` from Top 5 and recurring customer stats. These plates are used for historical imports where the real plate was unknown.

## Historical data import

Script: `datos/importar_historico.py` — one-time import of Jan/Feb/Mar 2026 from `datos/ramon MVP.xlsx`.

Placeholder plates used:
- `9999` — washing services where real plate was unknown
- `0000` — product sales (e.g. AREON GEL)

Description → service + vehicle_type mapping defined in `MAPPING` dict inside the script.

## Deployment (Render)

- Disk mounted at `/var/data`, DB lives at `/var/data/carwash.db/carwash.db`
- Env var: `DATA_DIR=/var/data/carwash.db`
- To reset DB: `rm /var/data/carwash.db/carwash.db` in Shell → Deploy latest commit
- Config: `render.yaml` + `.streamlit/config.toml`

### Download DB from Render to local
```bash
# Requires SSH key without passphrase added to Render account
scp -i ~/.ssh/render_key srv-d7gee2flk1mc7386jocg@ssh.ohio.render.com:/var/data/carwash.db/carwash.db data/carwash.db
```

### Upload local DB to Render
```bash
scp -i ~/.ssh/render_key data/carwash.db srv-d7gee2flk1mc7386jocg@ssh.ohio.render.com:/var/data/carwash.db/carwash.db
```
