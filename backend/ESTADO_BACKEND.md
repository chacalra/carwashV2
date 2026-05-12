# Estado del Backend

Este documento resume el estado actual del backend V2 y lo pendiente para considerarlo terminado al 100%.

## Hecho

### Estructura

- La capa backend quedó agrupada en `backend/`.
- `database/`, `repositories/`, `services/`, `utils/` y `alembic/` fueron movidos dentro de `backend/`.
- `alembic.ini` sigue en la raíz y apunta a `backend/alembic`.
- `compose.yml` sigue en la raíz para levantar PostgreSQL con `docker compose`.

### Base de datos

- Persistencia migrada a PostgreSQL con SQLAlchemy 2.0.
- Migraciones con Alembic funcionando.
- Esquema V2 modelado con:
  - lavanderías
  - roles
  - permisos
  - usuarios
  - clientes
  - productos
  - tipos de vehículo
  - vehículos
  - servicios
  - ventas
  - detalles de venta
  - categorías de egreso
  - egresos
- Seed inicial con lavandería demo, admin, rol admin, permisos y cliente genérico.
- Compatibilidad de permisos legacy en seed: copia `register_income`, `edit_income` y `void_income` hacia permisos nativos de ventas.

### Dominio

- El dominio viejo basado en `income` fue retirado del código V2.
- Se eliminaron:
  - `income_service.py`
  - `incomes_repository.py`
  - vistas heredadas de ingresos
  - tests legacy de ingresos
  - importador histórico SQLite
- El flujo actual usa:
  - `sale_service.py`
  - `sales_repository.py`
  - `sale_items_repository.py`
  - `venta + detalle_venta`
- Reportes, dashboard y exportación ya usan ventas nativas.

### Multi-Tenant

- La entidad `lavanderia` tiene `subdominio`.
- `tenant_service.py` resuelve tenant por subdominio o host.
- Repositories y services principales filtran por `lavanderia_id`.
- `POST /auth/login` resuelve tenant por `subdominio` o `Host`.
- Los endpoints protegidos toman `lavanderia_id` desde el token y validan el `Host` cuando aplica.

### Autenticación y Autorización API

- `POST /auth/login` ya devuelve `access_token` tipo Bearer con expiración.
- El token firmado incluye:
  - `user_id`
  - `lavanderia_id`
  - permisos
  - `iat`
  - `exp`
- Existe dependencia `get_current_user` para validar:
  - token Bearer
  - firma
  - expiración
  - usuario activo
  - tenant del `Host` cuando corresponde
- Existen dependencias `require_permission(...)` y `require_any_permission(...)`.
- Los endpoints protegidos actuales ya exigen autenticación y permiso:
  - ventas:
    - `GET /sales` -> `movements`
    - `POST /sales` -> `register_sale`
    - `PATCH /sales/{sale_id}/payment-type` -> `edit_sale`
    - `DELETE /sales/{sale_id}` -> `manage_sales`
  - egresos:
    - `GET /expenses` -> `movements`
    - `POST /expenses` -> `register_expense`
    - `GET /expenses/{expense_id}` -> `movements`
    - `PUT /expenses/{expense_id}` -> `register_expense`
    - `DELETE /expenses/{expense_id}` -> `register_expense`
  - vehículos:
    - `GET /vehicles` -> permisos operativos o `settings`
    - `GET /vehicles/by-plate/{license_plate}` -> `register_sale`
    - `GET /vehicles/{vehicle_id}` -> permisos operativos o `settings`
    - `POST /vehicles` -> `register_sale`
    - `PUT /vehicles/{vehicle_id}` -> `settings`
    - `PATCH /vehicles/{vehicle_id}/status` -> `settings`
  - reportes:
    - `GET /reports/sales-summary` -> `export`
  - catálogos:
    - `GET /catalogs/services` -> permisos operativos o `settings`
    - `POST /catalogs/services` -> `settings`
    - `PUT /catalogs/services/{service_id}` -> `settings`
    - `PATCH /catalogs/services/{service_id}/status` -> `settings`
    - `DELETE /catalogs/services/{service_id}` -> `settings`
    - `GET /catalogs/products` -> permisos operativos o `settings`
    - `POST /catalogs/products` -> `settings`
    - `PUT /catalogs/products/{product_id}` -> `settings`
    - `PATCH /catalogs/products/{product_id}/status` -> `settings`
    - `DELETE /catalogs/products/{product_id}` -> `settings`
    - `GET /catalogs/expense-categories` -> permisos operativos o `settings`
    - `POST /catalogs/expense-categories` -> `settings`
    - `PUT /catalogs/expense-categories/{category_id}` -> `settings`
    - `PATCH /catalogs/expense-categories/{category_id}/status` -> `settings`
    - `DELETE /catalogs/expense-categories/{category_id}` -> `settings`
    - `GET /catalogs/vehicle-types` -> permisos operativos o `settings`
    - `POST /catalogs/vehicle-types` -> `settings`
    - `PUT /catalogs/vehicle-types/{vehicle_type_id}` -> `settings`
    - `PATCH /catalogs/vehicle-types/{vehicle_type_id}/status` -> `settings`
    - `DELETE /catalogs/vehicle-types/{vehicle_type_id}` -> `settings`
  - clientes:
    - `GET /clients` -> permisos operativos o `settings`
    - `GET /clients/by-ruc-ci/{ruc_ci}` -> permisos operativos o `settings`
    - `POST /clients` -> `settings`
    - `PUT /clients/{client_id}` -> `settings`
    - `PATCH /clients/{client_id}/status` -> `settings`
- `POST /sales` y `POST /expenses` usan el usuario autenticado del token y rechazan operar en nombre de otro usuario.

### FastAPI

- Existe app FastAPI en `backend/api/main.py`.
- Routers implementados:
  - `GET /health`
  - `POST /auth/login`
  - `GET /catalogs/services`
  - `POST /catalogs/services`
  - `PUT /catalogs/services/{service_id}`
  - `PATCH /catalogs/services/{service_id}/status`
  - `DELETE /catalogs/services/{service_id}`
  - `GET /catalogs/products`
  - `POST /catalogs/products`
  - `PUT /catalogs/products/{product_id}`
  - `PATCH /catalogs/products/{product_id}/status`
  - `DELETE /catalogs/products/{product_id}`
  - `GET /catalogs/expense-categories`
  - `POST /catalogs/expense-categories`
  - `PUT /catalogs/expense-categories/{category_id}`
  - `PATCH /catalogs/expense-categories/{category_id}/status`
  - `DELETE /catalogs/expense-categories/{category_id}`
  - `GET /catalogs/vehicle-types`
  - `POST /catalogs/vehicle-types`
  - `PUT /catalogs/vehicle-types/{vehicle_type_id}`
  - `PATCH /catalogs/vehicle-types/{vehicle_type_id}/status`
  - `DELETE /catalogs/vehicle-types/{vehicle_type_id}`
  - `GET /clients`
  - `GET /clients/by-ruc-ci/{ruc_ci}`
  - `POST /clients`
  - `PUT /clients/{client_id}`
  - `PATCH /clients/{client_id}/status`
  - `GET /sales`
  - `GET /sales/grouped`
  - `GET /sales/{sale_id}`
  - `POST /sales`
  - `PUT /sales/{sale_id}`
  - `PATCH /sales/{sale_id}/payment-type`
  - `DELETE /sales/{sale_id}`
  - `GET /expenses`
  - `POST /expenses`
  - `GET /expenses/{expense_id}`
  - `PUT /expenses/{expense_id}`
  - `DELETE /expenses/{expense_id}`
  - `GET /vehicles`
  - `GET /vehicles/by-plate/{license_plate}`
  - `GET /vehicles/{vehicle_id}`
  - `POST /vehicles`
  - `PUT /vehicles/{vehicle_id}`
  - `PATCH /vehicles/{vehicle_id}/status`
  - `GET /reports/sales-summary`
- Schemas Pydantic iniciales creados en `backend/api/schemas/`.
- Dependencias compartidas en `backend/api/deps.py`.
- El servidor corre con:

```bash
uv run uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

### Tests

- Suite actual pasando:

```text
uv run pytest -> 204 passed
uv run python -m compileall -q backend ui app.py -> ok
uv run alembic heads -> c7d3f0a1b2e4 (head)
```

- Tests existentes cubren:
  - API inicial
  - auth service
  - catálogos
  - clientes
  - egresos
  - reportes
  - ventas
  - UI Streamlit principal de ventas
  - seguridad
  - vehículos

### Contrato de Ventas

- `GET /sales` mantiene la respuesta plana orientada a exportación y compatibilidad.
- `GET /sales/grouped` devuelve ventas agrupadas con detalles anidados.
- `GET /sales/{sale_id}` devuelve el detalle completo de una venta.
- `PUT /sales/{sale_id}` permite edición completa de cabecera + detalles.
- `DELETE /sales/{sale_id}` anula la venta de forma lógica; devuelve 409 si ya estaba anulada.
- `PUT /sales/{sale_id}` y `PATCH /sales/{sale_id}/payment-type` bloquean ventas anuladas con 409.
- `POST /sales` y `PUT /sales/{sale_id}` usan el usuario autenticado del token.
- Las ventas anuladas no aparecen en listados ni en reportes; `GET /sales/{id}` las devuelve con `is_voided=true`.

### Contrato de Clientes

- `GET /clients` lista clientes del tenant y permite `only_active`.
- `GET /clients/by-ruc-ci/{ruc_ci}` busca cliente por documento dentro del tenant.
- `POST /clients` crea clientes desde API.
- `PUT /clients/{client_id}` actualiza clientes existentes.
- `PATCH /clients/{client_id}/status` activa o desactiva clientes.

### Contrato de Catálogos

- `GET /catalogs/services`, `GET /catalogs/products`, `GET /catalogs/expense-categories` y `GET /catalogs/vehicle-types` aceptan `only_active=true|false`.
- Servicios y productos ya permiten creación y edición con precio desde API.
- Los cuatro catálogos administrables ya soportan:
  - crear
  - editar
  - activar/desactivar
  - eliminar

### Contrato de Egresos

- `GET /expenses` lista egresos activos por tenant.
- `GET /expenses/{expense_id}` devuelve el detalle completo de un egreso.
- `PUT /expenses/{expense_id}` permite edición completa.
- `DELETE /expenses/{expense_id}` ahora anula el egreso de forma lógica; no hace borrado físico.
- La edición y la anulación devuelven conflicto si el egreso ya estaba anulado.

### Contrato de Vehículos

- `GET /vehicles` lista vehículos del tenant; acepta `only_active` y `search` por matrícula.
- `GET /vehicles/by-plate/{license_plate}` busca por matrícula exacta.
- `GET /vehicles/{vehicle_id}` devuelve el detalle completo de un vehículo.
- `POST /vehicles` crea o actualiza un vehículo por matrícula (upsert operativo).
- `PUT /vehicles/{vehicle_id}` edita tipo de vehículo y datos del propietario.
- `PATCH /vehicles/{vehicle_id}/status` activa o desactiva un vehículo.

## Falta Para Backend 100%

### 1. Completar Contratos API

- Ventas: ✓ anulación lógica completada
- Usuarios/roles:
  - endpoints administrativos si la app los va a manejar desde API.

### 2. Manejo de Errores ✓ completado

- `raise_service_error(exc)` en `backend/api/routers/_errors.py` centraliza el mapeo:
  - "no existe" en el mensaje → 404
  - "ya fue anulado/a" o "ya existe" → 409
  - cualquier otro `ValueError` → 400
- Todos los routers usan esta helper; no hay más string-matching disperso.
- Handler global de `IntegrityError` → 409 genérico (sin exponer detalles de BD).
- Handler global de `Exception` → 500 genérico (safety net).

### 3. Transacciones y Sesiones API ✓ completado (egresos)

- `get_db()` en `connection.py` gestiona commit/rollback automático por request.
- `DbSession = Annotated[Session, Depends(get_db)]` en `deps.py`.
- Los write endpoints de egresos (`POST`, `PUT`, `DELETE`) ya reciben sesión por inyección.
- Los services de escritura (`register_expense`, `edit_expense`, `remove_expense`) y sus repositorios aceptan `session` como primer argumento.
- Los reads siguen abriendo su propia `SessionLocal`; la migración fue progresiva para minimizar el alcance.
- Pendiente: aplicar el mismo patrón a ventas si se requiere.

### 4. Paginación y Filtros

- Agregar paginación a listados grandes:
  - ventas
  - egresos
  - vehículos
  - clientes
- Agregar filtros por fecha, texto, estado, tipo de cobro y cliente.

### 5. Migraciones Futuras

- Si se cambian permisos o estructuras de datos, crear migraciones Alembic.
- Considerar migración formal para permisos nuevos si la base ya tiene datos reales.
- El seed hoy cubre compatibilidad básica, pero producción debería depender menos de lógica correctiva en seed.

### 6. Tests de Integración API

- Agregar tests con base temporal o PostgreSQL de test para endpoints reales.
- Cubrir:
  - login real
  - creación de venta completa
  - aislamiento multi-tenant
  - permisos por endpoint
  - reportes por tenant
  - egresos por tenant

### 7. Producción

- Definir `startCommand` para FastAPI si el backend se despliega separado de Streamlit.
- ~~Configurar CORS según el frontend real.~~ ✓ completado
- ~~Configurar variables de entorno obligatorias, especialmente `AUTH_TOKEN_SECRET`.~~ ✓ advertencia en arranque
- Revisar logging.
- Agregar healthcheck de base de datos si hace falta.
- Agregar documentación de despliegue y variables de entorno.

---

## Checklist de Deploy (hacer cuando se vaya a producción)

### Variables de entorno obligatorias en el servidor

```bash
AUTH_TOKEN_SECRET=<clave larga y aleatoria>          # openssl rand -hex 32
CORS_ALLOW_ORIGIN_REGEX=https://[a-z0-9-]+\.carwash\.mukusoft\.com
DATABASE_URL=postgresql+psycopg://user:pass@host:5432/carwash
```

Opcionales:
```bash
AUTH_TOKEN_EXPIRES_MINUTES=60   # default 60
```

### Arrancar el backend

```bash
uv run uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

### Nginx — bloque por subdominio

```nginx
server {
    listen 443 ssl;
    server_name *.carwash.mukusoft.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

El header `Host` debe llegar intacto al backend para que el tenant se resuelva correctamente.

### Verificar al arrancar

- Los logs no deben mostrar el warning de `AUTH_TOKEN_SECRET`.
- `GET /health` debe responder `{"status": "ok"}`.
- Un login real debe devolver token válido.

## Prioridad Recomendada

1. ~~Mejorar semántica de borrado/anulación de ventas.~~ ✓ completado
2. ~~Vehículos: listado y edición desde API.~~ ✓ completado
3. Usuarios/roles administrativos por API, si van a salir de la UI actual.
4. Tests de integración multi-tenant.
5. ~~Estandarización final de errores HTTP.~~ ✓ completado
6. ~~Migración progresiva a sesión por request en FastAPI.~~ ✓ completado (egresos)
7. Preparación de deploy FastAPI.
