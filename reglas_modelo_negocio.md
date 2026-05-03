# Reglas de negocio y constraints del modelo

Este documento complementa el modelo en `dbdiagram.io`.
El diagrama describe entidades, atributos y relaciones.
Acá se documentan las reglas de negocio e integridad que luego pueden implementarse con:

- `NOT NULL`
- `UNIQUE`
- `FOREIGN KEY`
- `CHECK`
- validaciones en backend

## 1. Regla general de tenant

- Toda entidad operativa pertenece a una `lavanderia`.
- Ninguna lavandería debe ver ni modificar datos de otra lavandería.
- Los catálogos `producto`, `servicio`, `tipo_vehiculo`, `categoria_egreso`, `cliente`, `vehiculo`, `rol`, `usuario`, `venta` y `egreso` deben quedar asociados a una `lavanderia`.

## 2. Usuarios, roles y permisos

- Un `usuario` pertenece a una sola `lavanderia`.
- Un `usuario` tiene un solo `rol`.
- Un `rol` pertenece a una sola `lavanderia`.
- Un `permiso` es global del sistema.
- Un `rol` puede tener muchos permisos.
- Un `permiso` puede pertenecer a muchos roles.
- No se debe repetir la misma combinación `rol_id + permiso_id`.
- `nombre_usuario` debe ser único dentro de una misma `lavanderia`.

## 3. Clientes

- Un `cliente` pertenece a una sola `lavanderia`.
- Un `cliente` puede ser `particular`, `empresa` o `generico`.
- Debe existir la posibilidad de usar un cliente genérico, por ejemplo `Consumidor Final`, para ventas rápidas.
- `ruc_ci` puede ser opcional.
- Si `ruc_ci` existe, no debería repetirse dentro de la misma `lavanderia`.

## 4. Vehículos

- Un `vehiculo` pertenece a una sola `lavanderia`.
- Un `vehiculo` puede pertenecer a un `cliente`.
- Un `vehiculo` tiene un solo `tipo_vehiculo`.
- `matricula` es opcional.
- Si no existe matrícula, debe almacenarse `NULL` real, no cadena vacía.
- Si existe matrícula, no debe repetirse dentro de la misma `lavanderia`.
- Un `tipo_vehiculo` pertenece a una sola `lavanderia`.
- `tipo_vehiculo.nombre` no debe repetirse dentro de una misma `lavanderia`.

## 5. Servicios y productos

- Un `servicio` pertenece a una sola `lavanderia`.
- Un `producto` pertenece a una sola `lavanderia`.
- `nombre_servicio` no debe repetirse dentro de una misma `lavanderia`.
- `nombre_producto` no debe repetirse dentro de una misma `lavanderia`.
- El precio actual de `servicio` y `producto` representa el valor vigente del catálogo, no el histórico de ventas pasadas.

## 6. Ventas

- Una `venta` pertenece a una sola `lavanderia`.
- Una `venta` es registrada por un solo `usuario`.
- Una `venta` idealmente debe asociarse a un `cliente`.
- Una `venta` puede asociarse opcionalmente a un `vehiculo`.
- Una venta sin `vehiculo` es válida, por ejemplo cuando solo se venden productos.
- `fecha_venta` representa la fecha operativa del negocio.
- `created_at` representa el momento exacto en que el registro entró al sistema.
- `total` representa el importe final de la venta.

## 7. Facturación

- No todas las ventas requieren factura.
- Si una venta requiere factura, debe existir un `cliente` identificable.
- Para ventas rápidas puede usarse el cliente genérico.
- La facturación debe apoyarse en el `cliente` como memoria comercial para evitar reescribir datos varias veces.

## 8. Detalle de venta

- Una `venta` debe tener uno o muchos `detalle_venta`.
- Cada `detalle_venta` pertenece a una sola `venta`.
- Cada `detalle_venta` representa una sola línea de la venta.
- Un `detalle_venta` puede corresponder a un `servicio` o a un `producto`.
- Exactamente uno entre `servicio_id` y `producto_id` debe tener valor.
- No debe permitirse que ambos estén vacíos.
- No debe permitirse que ambos tengan valor al mismo tiempo.
- `cantidad` permite múltiples unidades del mismo ítem.
- Si se venden productos distintos, deben ir en detalles distintos.
- `precio_unitario` y `subtotal` deben conservarse para mantener el historial aunque cambien los precios del catálogo.

## 9. Egresos

- Un `egreso` pertenece a una sola `lavanderia`.
- Un `egreso` es registrado por un solo `usuario`.
- Un `egreso` tiene una sola `categoria_egreso`.
- `categoria_egreso` pertenece a una sola `lavanderia`.
- `nombre_categoria` no debe repetirse dentro de una misma `lavanderia`.
- `fecha` representa la fecha operativa del gasto.
- `created_at` representa el momento exacto en que el gasto fue registrado en el sistema.

## 10. Estados booleanos

- `estado` se usa como bandera booleana de activo/inactivo.
- Esto aplica a catálogos y entidades administrativas como:
  - `lavanderia`
  - `rol`
  - `permiso`
  - `usuario`
  - `cliente`
  - `producto`
  - `tipo_vehiculo`
  - `vehiculo`
  - `servicio`
  - `categoria_egreso`
  - `egreso` si el negocio decide permitir anulación lógica

## 11. Constraints sugeridos para implementación

- `UNIQUE (lavanderia_id, nombre)` en `rol`
- `UNIQUE (codigo)` en `permiso`
- `UNIQUE (rol_id, permiso_id)` en `rol_permiso`
- `UNIQUE (lavanderia_id, nombre_usuario)` en `usuario`
- `UNIQUE (lavanderia_id, ruc_ci)` en `cliente`
- `UNIQUE (lavanderia_id, nombre_producto)` en `producto`
- `UNIQUE (lavanderia_id, nombre_servicio)` en `servicio`
- `UNIQUE (lavanderia_id, nombre)` en `tipo_vehiculo`
- `UNIQUE (lavanderia_id, matricula)` en `vehiculo`
- `UNIQUE (lavanderia_id, nombre_categoria)` en `categoria_egreso`
- `CHECK` para forzar que en `detalle_venta` exista exactamente uno entre `servicio_id` y `producto_id`

## 12. Decisiones abiertas para más adelante

- Definir si `egreso.estado` se usará para anulación lógica o si conviene quitarlo.
- Definir si `cliente.email` debe tener alguna restricción de unicidad.
- Definir si en el futuro habrá una entidad separada de `factura`.
- Definir si se agregarán límites o planes de suscripción por `lavanderia`.
