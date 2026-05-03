# Tareas hechas V2

Este documento resume lo ya realizado en la transición hacia la V2.

Su objetivo es complementar:

- `reglas_modelo_negocio.md`
- `analisis_migracion_v2.md`
- `plan_v2_por_archivos.md`

La idea es que, leyendo esos documentos junto con este archivo, se pueda entender:

- qué se decidió
- qué ya se ejecutó
- en qué estado quedó el proyecto
- cuál es el siguiente paso natural

## 1. Estado general

La V2 ya salió de la fase puramente conceptual.

Ya no estamos solamente en:

- diagramas
- modelo lógico
- reglas de negocio

Ahora el proyecto ya tiene una primera base técnica real orientada a:

- PostgreSQL
- SQLAlchemy 2.0
- FastAPI
- Alembic
- multi-tenant por `lavanderia`

## 2. Documentación consolidada

Se dejaron como documentos principales de contexto:

- `reglas_modelo_negocio.md`
- `analisis_migracion_v2.md`
- `plan_v2_por_archivos.md`

También se eliminaron documentos heredados del MVP que ya metían ruido para la V2:

- `CLAUDE.md`
- `definicion.md`
- `deifnicion 2.md`
- `plan_desarrollo_por_archivos.md`

## 3. Repo y estructura

- Se creó un repo nuevo para la V2: `carwash`
- Se evitó trabajar encima del repo viejo `carwash_mvp`
- Se reutilizó la estructura general del proyecto:
  - `database/`
  - `repositories/`
  - `services/`
  - `ui/`
  - `utils/`
  - `tests/`

## 4. Stack técnico decidido

Se definió que la V2 apuntará a:

- `FastAPI`
- `SQLAlchemy 2.0`
- `psycopg[binary]`
- `Alembic`
- `python-dotenv`
- `Pydantic`
- PostgreSQL

Esto reemplaza el enfoque del MVP basado en:

- SQLite
- SQL manual
- esquema incremental sobre el mismo diseño viejo

## 5. Cambios realizados en `database/`

### 5.1 `database/connection.py`

Hecho:

- se reemplazó la conexión SQLite
- se configuró conexión basada en `SQLAlchemy 2.0`
- se agregó:
  - `DATABASE_URL`
  - construcción de URL desde variables `PG*`
  - `engine`
  - `SessionLocal`
  - `get_session()`

Resultado:

- el proyecto ya no depende de SQLite
- la base técnica de persistencia ya apunta a PostgreSQL

### 5.2 `database/schema.py`

Hecho:

- se eliminó el esquema viejo basado en SQLite y `income`
- se reescribió el esquema base de la V2 con SQLAlchemy declarativo

Tablas base modeladas:

- `lavanderias`
- `roles`
- `permisos`
- `roles_permisos`
- `usuarios`
- `clientes`
- `productos`
- `tipos_vehiculo`
- `vehiculos`
- `servicios`
- `ventas`
- `detalles_venta`
- `categorias_egreso`
- `egresos`

Además:

- se agregaron `UNIQUE`
- se agregaron `CHECK`
- se agregaron índices básicos
- se incluyó `create_tables()`

### 5.3 Auditoría temporal

Hecho:

- se cambió `created_at` para usar:
  - `DateTime(timezone=True)`
  - `server_default=func.now()`

Aplicado en tablas donde tiene valor de trazabilidad.

Resultado:

- los timestamps quedan mejor alineados con PostgreSQL
- el valor se genera del lado servidor

### 5.4 `database/seed.py`

Hecho:

- se reemplazó el seed viejo del MVP
- se adaptó el seed al nuevo modelo V2

Datos base sembrados:

- permisos globales
- una `lavanderia` demo
- un rol `admin`
- todos los permisos asignados a ese rol
- un usuario inicial:
  - `admin`
  - contraseña `admin123`
- cliente genérico:
  - `Consumidor Final`

Resultado:

- el seed ya es consistente con el nuevo modelo
- la carga inicial es idempotente

## 6. Alembic

Hecho:

- se inicializó Alembic
- se creó:
  - `alembic/`
  - `alembic.ini`
- se conectó Alembic al `Base.metadata` del proyecto
- se configuró para usar la misma `DATABASE_URL` del proyecto
- se agregó `.env.example`
- se agregó `.env` a `.gitignore`

Resultado:

- la infraestructura de migraciones ya está preparada
- todavía no se generó la primera migración porque falta una base PostgreSQL accesible

## 7. Dependencias

Hecho:

Se actualizaron dependencias para el rumbo nuevo del proyecto:

- `fastapi`
- `uvicorn[standard]`
- `sqlalchemy`
- `psycopg[binary]`
- `alembic`
- `python-dotenv`
- `pydantic[email]`

Resultado:

- el proyecto ya está alineado al stack objetivo de la V2

## 8. Qué NO está hecho todavía

Todavía falta:

- levantar PostgreSQL real para desarrollo
- definir `.env` real
- probar conexión efectiva a PostgreSQL
- generar primera migración Alembic
- correr `upgrade`
- rehacer repositories del nuevo dominio
- rehacer services del dominio nuevo
- rediseñar UI orientada a `venta + detalle_venta`

## 9. Punto exacto donde quedó el proyecto

Hoy el proyecto quedó en este estado:

- documentación base lista
- modelo lógico decidido
- reglas de negocio documentadas
- stack técnico decidido
- `database/connection.py` listo
- `database/schema.py` listo como base declarativa
- `database/seed.py` listo como carga inicial
- Alembic inicializado
- falta conectar con una instancia real de PostgreSQL

## 10. Siguiente paso natural

El siguiente paso recomendado ya está claro:

1. levantar PostgreSQL para desarrollo local
2. crear `.env` real
3. probar conexión
4. generar primera migración:

```bash
uv run alembic revision --autogenerate -m "create v2 schema"
```

5. aplicar migración:

```bash
uv run alembic upgrade head
```

6. recién después seguir con:
   - repositories nuevos
   - services nuevos
   - adaptación progresiva del resto del proyecto

## 11. Dirección del proyecto

La dirección actual de la V2 es:

- mantener la arquitectura por capas
- cambiar el núcleo del dominio
- consolidar multi-tenant real
- pasar a PostgreSQL
- apoyar el backend en `FastAPI + SQLAlchemy 2.0 + Alembic`
- modelar correctamente:
  - `cliente`
  - `vehiculo`
  - `venta`
  - `detalle_venta`

En resumen:

La planificación base ya está hecha.
La infraestructura inicial también.
El próximo salto ya no es más análisis, sino levantar PostgreSQL y empezar el versionado real de la base.
