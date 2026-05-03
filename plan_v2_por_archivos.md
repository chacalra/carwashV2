# Plan V2 por archivos

Este documento traduce el análisis de migración y el nuevo modelo de datos en una guía práctica de implementación.

La idea es responder:

- qué se conserva
- qué se adapta
- qué se crea desde cero
- en qué orden conviene trabajar

## 1. Objetivo de la V2

Construir una nueva versión del sistema con estas diferencias principales respecto al MVP:

- soporte multi-tenant mediante `lavanderia`
- PostgreSQL como base de datos principal
- `FastAPI` como stack objetivo de backend
- `SQLAlchemy 2.0` como capa principal de persistencia
- `Alembic` para migraciones
- reemplazo del concepto `income` por `venta + detalle_venta`
- separación más clara entre `cliente`, `vehiculo` y `venta`
- roles por lavandería y permisos globales

## 2. Estructura objetivo

La estructura general del proyecto puede mantenerse:

```text
carwash/
├── app.py
├── database/
│   ├── connection.py
│   ├── schema.py
│   └── seed.py
├── repositories/
├── services/
├── ui/
├── utils/
├── tests/
├── reglas_modelo_negocio.md
├── analisis_migracion_v2.md
└── plan_v2_por_archivos.md
```

## 3. Orden recomendado

El orden sugerido de trabajo es:

1. `database/`
2. `repositories/`
3. `services/`
4. `ui/`
5. `tests/`

No conviene empezar por la UI.
La V2 depende primero de que el dominio y la persistencia queden bien resueltos.

## 4. Plan por área

## 4.1 `database/connection.py`

### Estado

Adaptar.

### Objetivo

Definir la base técnica de persistencia sobre PostgreSQL usando `SQLAlchemy 2.0` y `psycopg`.

### Tareas

- definir conexión a PostgreSQL
- usar variables de entorno
- preparar `engine`
- preparar `SessionLocal`
- preparar `get_session()`
- dejar la base lista para `FastAPI`

### Resultado esperado

Una base técnica estable lista para repositories, services, tests y futura API.

## 4.2 `database/schema.py`

### Estado

Rehacer casi completo.

### Objetivo

Implementar el modelo nuevo:

- `lavanderia`
- `rol`
- `permiso`
- `rol_permiso`
- `usuario`
- `cliente`
- `producto`
- `tipo_vehiculo`
- `vehiculo`
- `servicio`
- `venta`
- `detalle_venta`
- `categoria_egreso`
- `egreso`

### Tareas

- definir tablas
- decidir si la definición vivirá primero como SQLAlchemy ORM, SQLAlchemy Core o SQL de migración
- definir PK y FK
- definir `UNIQUE`
- definir `CHECK`
- definir campos opcionales y obligatorios

### Resultado esperado

Esquema físico inicial de PostgreSQL alineado con el modelo aprobado.

## 4.3 `database/seed.py`

### Estado

Adaptar fuerte.

### Objetivo

Sembrar datos base mínimos para que el sistema arranque.

### Tareas

- sembrar permisos globales
- definir si conviene sembrar una `lavanderia` demo
- definir si conviene sembrar un cliente genérico tipo `Consumidor Final`
- sembrar usuario administrador inicial si aplica

### Resultado esperado

Sistema arrancable sin depender de carga manual total.

## 4.4 `alembic/`

### Estado

Crear.

### Objetivo

Gestionar el esquema y sus cambios de forma versionada.

### Tareas

- inicializar Alembic
- configurar conexión a PostgreSQL
- preparar la primera migración base
- dejar el proyecto listo para futuras migraciones incrementales

### Resultado esperado

Migraciones repetibles, auditables y alineadas con el modelo nuevo.

## 5. Plan de repositories

## 5.1 Repositories que pueden adaptarse

- `users_repository.py`
- `roles_repository.py`
- `role_permissions_repository.py`
- `products_repository.py`
- `services_repository.py`
- `vehicle_types_repository.py`
- `vehicles_repository.py`
- `expense_categories_repository.py`
- `expenses_repository.py`

### Motivo

La idea de acceso a datos sigue siendo útil, pero debe cambiar para trabajar:

- con PostgreSQL
- con `lavanderia_id`
- con el nuevo modelo relacional

## 5.2 Repositories a crear o rediseñar

- `lavanderias_repository.py`
- `clients_repository.py`
- `sales_repository.py`
- `sale_items_repository.py`
- opcionalmente `permissions_repository.py`

### Motivo

La V2 necesita repositorios nuevos para el corazón del dominio.

## 5.3 Repositories a reemplazar

- `incomes_repository.py`

### Motivo

El concepto actual de ingreso aislado ya no representa bien la operación real.
Debe ser reemplazado por `venta` y `detalle_venta`.

## 6. Plan de services

## 6.1 Services que pueden adaptarse

- `auth_service.py`
- `catalog_service.py`
- `expense_service.py`
- `report_service.py`
- `vehicle_service.py`

### Motivo

La capa de negocio se mantiene, pero con nuevas reglas y relaciones.

## 6.2 Services a crear o rediseñar

- `sale_service.py`
- `client_service.py`
- `tenant_service.py` si más adelante hace falta centralizar lógica de `lavanderia`

### Motivo

La lógica central ya no debe girar en torno a `income`, sino a `venta`.

## 6.3 Services a reemplazar

- `income_service.py`

### Motivo

Debe evolucionar a un servicio orientado a ventas con múltiples detalles.

## 7. Plan de UI

## 7.1 Vistas que pueden mantenerse como concepto

- `dashboard.py`
- `export_view.py`
- `login_view.py`
- `settings_view.py`
- `movements_view.py`

### Motivo

Siguen existiendo en la V2, pero con otro backend y otra estructura de datos.

## 7.2 Vistas que deben rediseñarse fuerte

- `incomes_form.py`
- `edit_income_view.py`
- `void_incomes_view.py`

### Motivo

Hoy dependen de `income`.
La V2 debe registrar ventas con uno o muchos detalles.

## 7.3 Vistas nuevas probables

- `sales_form.py`
- `sales_edit_view.py`
- `clients_view.py` o mantenimiento básico de clientes

### Motivo

El nuevo dominio va a pedir UI específica para ventas y clientes.

## 8. Plan de utils

## Estado

Mantener y adaptar según necesidad.

### Archivos útiles como base

- `formatters.py`
- `export.py`
- `notifications.py`
- `security.py`
- `date_shortcuts.py`

### Motivo

No están atados tan profundamente al modelo actual.

## 9. Plan de tests

## Estado

Mantener la carpeta y rediseñar casos.

### Tareas

- mantener estrategia de testeo
- adaptar tests de auth y catálogos
- reemplazar tests de incomes por tests de sales
- agregar tests del modelo multi-tenant
- agregar tests de integridad de `detalle_venta`

### Resultado esperado

La V2 debe crecer con tests acordes a las nuevas reglas del dominio.

## 10. Primer sprint recomendado

Si hubiera que empezar ya, el primer bloque de trabajo sería:

1. base técnica con `FastAPI + SQLAlchemy 2.0 + psycopg + dotenv`
2. Alembic listo para migraciones
3. nuevo esquema en `database/schema.py`
4. nuevo `seed.py`
5. crear:
   - `lavanderias_repository.py`
   - `clients_repository.py`
   - `sales_repository.py`
   - `sale_items_repository.py`
6. crear:
   - `sale_service.py`
   - `client_service.py`
7. dejar para después la UI nueva

## 11. Prioridad por impacto

### Alta prioridad

- conexión PostgreSQL
- base técnica con SQLAlchemy
- Alembic
- esquema nuevo
- `venta`
- `detalle_venta`
- `cliente`
- multi-tenant real

### Prioridad media

- auth
- roles por lavandería
- permisos globales
- egresos por tenant
- dashboard y reportes

### Prioridad baja

- refinamientos de UI
- mejoras de experiencia
- exportaciones avanzadas
- decisiones futuras de suscripción

## 12. Criterio general

La V2 no debe construirse como “MVP parcheado”.

Tampoco hace falta tirar todo.

El criterio recomendado es:

- conservar la arquitectura por capas
- rehacer el núcleo del dominio
- migrar la persistencia
- adaptar módulos útiles
- reemplazar lo que ya no representa bien el negocio
