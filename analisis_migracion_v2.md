# Análisis de migración a V2

Este documento resume el análisis de transición desde el MVP actual hacia una nueva versión:

- multi-tenant
- PostgreSQL
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
  Cambia de SQLite a PostgreSQL.
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

1. Rehacer `database/schema.py` según el modelo nuevo.
2. Diseñar el esquema físico PostgreSQL.
3. Crear repositorios base nuevos o adaptados para:
   - `lavanderia`
   - `cliente`
   - `venta`
   - `detalle_venta`
   - `vehiculo`
4. Adaptar auth, roles y permisos.
5. Recién después rediseñar formularios y vistas principales.

## 9. Conclusión

La V2 no debe tratarse como un proyecto completamente nuevo ni como un simple parche sobre el MVP.

La mejor lectura es:

- se conserva la arquitectura por capas
- se rediseña el dominio central
- se migra a PostgreSQL
- se adapta el sistema a multi-tenant real

Esto permite avanzar con criterio, reutilizando lo útil del MVP sin quedar atrapado por decisiones que ya no representan bien el negocio.
