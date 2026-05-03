# Análisis de migración a V2

Este documento resume el análisis de transición desde el MVP actual hacia una nueva versión:

- multi-tenant
- PostgreSQL
- FastAPI
- SQLAlchemy 2.0
- Alembic
- modelo de `venta + detalle_venta`
- separación más clara entre `cliente`, `vehiculo` y `venta`

La idea es mantener contexto de arquitectura para no rediscutir desde cero qué conviene conservar, adaptar o reemplazar.

## 1. Idea general

La V2 no implica tirar todo el proyecto actual.
El cambio fuerte está en:

- base de datos
- modelo de negocio
- aislamiento por `lavanderia`
- evolución de `income` hacia `venta`
- adopción de un stack moderno de backend y persistencia

La estructura por capas del MVP sigue siendo válida:

- `database/`
- `repositories/`
- `services/`
- `ui/`
- `utils/`
- `tests/`

## 2. Decisión principal

La estrategia recomendada para la V2 es:

- mantener el esqueleto del proyecto
- rediseñar el dominio central
- adaptar gradualmente módulos reutilizables
- reemplazar los módulos cuyo diseño depende demasiado de `income` como unidad única
- usar PostgreSQL mediante `SQLAlchemy 2.0` sobre `psycopg`
- preparar la base técnica para `FastAPI` y migraciones con `Alembic`

## 3. Matriz de migración

### Se mantiene

- `ui/`
  Como capa de presentación.
- `services/`
  Como capa de reglas de negocio.
- `repositories/`
  Como capa de acceso a datos.
- `utils/`
  Como conjunto de helpers reutilizables.
- `tests/`
  Como práctica y estructura de calidad.
- `app.py`
  Como punto de entrada y composición general.

### Se adapta

- `database/connection.py`
  Cambia de SQLite a PostgreSQL y pasa a usar `SQLAlchemy 2.0`.
- `database/schema.py`
  Debe rehacerse según el nuevo modelo multi-tenant.
- `database/seed.py`
  Pasa a sembrar permisos globales, datos base y quizá cliente genérico.
- `services/auth_service.py`
  Debe respetar tenant, roles por lavandería y permisos globales.
- `services/catalog_service.py`
  Debe operar por `lavanderia`.
- `services/report_service.py`
  Debe recalcularse sobre `venta`, `detalle_venta`, `cliente`, `vehiculo` y `egreso`.
- `ui/login_view.py`
  Debe adaptarse al nuevo modelo de usuarios por tenant.
- `ui/settings_view.py`
  Debe administrar catálogos y roles por lavandería.
- `ui/dashboard.py`
  Se mantiene, pero con nuevas métricas y filtros por tenant.
- `ui/export_view.py`
  Se mantiene, pero con nuevas consultas y estructura de datos.
- buena parte de `tests/`
  La idea se mantiene, aunque varios casos habrá que reescribir.

### Se reemplaza

- `repositories/incomes_repository.py`
  Debería evolucionar a algo tipo `sales_repository`.
- `services/income_service.py`
  Debería evolucionar a `sale_service` o equivalente.
- `ui/incomes_form.py`
  Debería pasar a registro de `venta` con múltiples `detalle_venta`.
- `ui/edit_income_view.py`
  Debería pasar a edición de venta o edición de detalles.
- `ui/void_incomes_view.py`
  Debería rediseñarse alrededor del concepto de venta.
- toda lógica centrada en `service_id` único por ingreso
  Ya no representa bien una operación real.
- toda lógica que trate datos del propietario dentro de `vehiculo`
  Ahora esos datos deberían vivir principalmente en `cliente`.

### Se revisa con cuidado

- `repositories/users_repository.py`
  Porque usuarios y roles ahora dependen de `lavanderia`.
- `repositories/roles_repository.py`
  Porque el rol deja de ser global.
- `repositories/role_permissions_repository.py`
  La lógica sigue, pero el modelo debe alinearse a permisos globales y roles por tenant.
- `repositories/vehicles_repository.py`
  Porque `vehiculo` ahora se relaciona con `cliente`.
- `repositories/services_repository.py`
  Porque `servicio` es por tenant y participa en `detalle_venta`.
- `repositories/products_repository.py`
  Igual que `servicio`.
- `repositories/vehicle_types_repository.py`
  Porque `tipo_vehiculo` es por lavandería.
- `repositories/expense_categories_repository.py`
  Porque categoría también es por tenant.
- `repositories/expenses_repository.py`
  Se mantiene mejor que ingresos, pero debe adaptarse al tenant.

## 4. Impacto por dominio

### Bajo impacto

- `utils/`
- parte de exportación
- parte del dashboard

### Impacto medio

- autenticación
- roles y permisos
- catálogos
- egresos

### Impacto alto

- cambio de `income` a `venta`
- `detalle_venta`
- `cliente`
- multi-tenant real
- PostgreSQL
- adopción de `SQLAlchemy 2.0`
- incorporación de `FastAPI` y `Alembic` como stack objetivo

## 5. Razones del rediseño

La V2 aparece por varias necesidades detectadas:

- soportar más de un cliente (`lavanderia`)
- pasar de SQLite a PostgreSQL
- permitir ventas con:
  - solo servicio
  - solo productos
  - servicio más productos
- separar mejor:
  - `cliente`
  - `vehiculo`
  - `venta`
- soportar análisis de cuentas corporativas vs. clientes normales
- preparar el sistema para crecimiento sin rehacerlo por completo

## 6. Decisiones de modelado relevantes

### Multi-tenant

- `lavanderia` es la raíz del tenant.
- Toda entidad operativa debe quedar asociada a una `lavanderia`.
- La resolución del tenant se hará por dominio o subdominio, no por selector manual en el login.
- Eso permite reutilizar usuarios iniciales como `Administrador/admin` en varias lavanderías sin ambigüedad, siempre que cada una entre por su URL propia.

### Resolución de tenant

- Una `lavanderia` debe tener un identificador técnico único para entrada, por ejemplo `subdominio`.
- Ejemplos esperados:
  - `autocare.mukusoft.com`
  - `carwash2.mukusoft.com`
- El backend debe resolver primero el tenant desde el host y después autenticar al usuario dentro de esa lavandería.
- Esto no cambia el modelo base ya implementado de `usuario.lavanderia_id`; cambia cómo se descubre el tenant al iniciar sesión.

### Roles y permisos

- `permiso` es global del sistema.
- `rol` pertenece a una `lavanderia`.
- cada lavandería puede crear sus propios roles y asignar los permisos que quiera.

### Cliente y vehículo

- `cliente` es la cuenta comercial.
- `vehiculo` es la unidad operativa que llega al lavadero.
- un cliente puede tener muchos vehículos.
- una venta puede apuntar a cliente y opcionalmente a vehículo.

### Venta y detalle de venta

- `venta` es la operación completa.
- `detalle_venta` es cada línea.
- un detalle representa un solo ítem.
- ese ítem puede ser:
  - un servicio
  - o un producto
- una venta puede combinar ambos a través de múltiples detalles.

## 7. Reglas prácticas ya detectadas

- `vehiculo.matricula` no puede ser identificador principal.
- si no existe matrícula, debe almacenarse `NULL`, no cadena vacía.
- `precio_unitario` y `subtotal` en `detalle_venta` deben conservarse por historial.
- `venta.vehiculo_id` debe ser opcional.
- `cliente` permite distinguir cuentas corporativas de ventas de mostrador.

## 8. Recomendación de orden de implementación

1. Consolidar la base técnica con `FastAPI + SQLAlchemy 2.0 + psycopg + Alembic`.
2. Rehacer `database/schema.py` según el modelo nuevo.
3. Diseñar el esquema físico PostgreSQL.
4. Crear repositorios base nuevos o adaptados para:
   - `lavanderia`
   - `cliente`
   - `venta`
   - `detalle_venta`
   - `vehiculo`
5. Adaptar auth, roles y permisos.
6. Recién después rediseñar formularios y vistas principales.

## 8.1 Impacto de la decisión por subdominio

Esta decisión no invalida el trabajo ya hecho.

Se mantiene:

- `usuario.lavanderia_id`
- `rol.lavanderia_id`
- la estructura multi-tenant actual
- la base PostgreSQL y Alembic
- repositories y services ya creados para tenant, clientes y ventas

Ya quedó ajustado en esta línea:

- `lavanderias` ahora incluye `subdominio`
- repositories y `tenant_service` ya resuelven tenant por subdominio y por host
- `auth_service` ya consume tenant resuelto por host o subdominio en vez de depender de heurísticas temporales
- la UI local de login ya acepta `subdominio` o host como puente hasta la entrada definitiva por URL

## 9. Conclusión

La V2 no debe tratarse como un proyecto completamente nuevo ni como un simple parche sobre el MVP.

La mejor lectura es:

- se conserva la arquitectura por capas
- se rediseña el dominio central
- se migra a PostgreSQL
- se adopta `SQLAlchemy 2.0` como base de persistencia
- se prepara la base para `FastAPI` y migraciones con `Alembic`
- se adapta el sistema a multi-tenant real
- se orienta la autenticación a resolución de tenant por subdominio

Esto permite avanzar con criterio, reutilizando lo útil del MVP sin quedar atrapado por decisiones que ya no representan bien el negocio.
