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
- se generó la primera migración base:
  - `alembic/versions/8a982724c18c_create_v2_schema.py`
- se aplicó `uv run alembic upgrade head`

Resultado:

- la infraestructura de migraciones ya está preparada
- el esquema V2 ya quedó versionado y aplicado sobre PostgreSQL

## 7. PostgreSQL local

Hecho:

- se agregó `compose.yml`
- se configuró PostgreSQL con `postgres:16`
- se evitó conflicto con otro servicio local usando el puerto `5433`
- se creó `.env` local de desarrollo
- se validó conexión real desde SQLAlchemy

Resultado:

- la V2 ya tiene una base local reproducible
- el entorno de desarrollo ya puede levantarse con:

```bash
docker compose up -d
```

## 8. Dependencias

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

## 9. Seed inicial verificado

Hecho:

- se ejecutó `seed_initial_data()`
- se verificó carga inicial sobre PostgreSQL

Datos confirmados:

- `8` permisos
- `1` lavandería demo
- `1` usuario administrador
- `1` cliente genérico

## 10. Qué NO está hecho todavía

Todavía falta:

- rehacer repositories del nuevo dominio
- rehacer services del dominio nuevo
- rediseñar UI orientada a `venta + detalle_venta`
- adaptar auth y flujo de usuarios/roles al nuevo esquema
- reemplazar definitivamente el corazón del MVP basado en `income`

## 11. Punto exacto donde quedó el proyecto

Hoy el proyecto quedó en este estado:

- documentación base lista
- modelo lógico decidido
- reglas de negocio documentadas
- stack técnico decidido
- `database/connection.py` listo
- `database/schema.py` listo como base declarativa
- `database/seed.py` listo como carga inicial
- Alembic inicializado
- PostgreSQL local levantado en Docker
- primera migración generada
- primera migración aplicada
- seed inicial verificado

## 12. Siguiente paso natural

El siguiente paso recomendado ya está claro:

1. empezar los repositories nuevos del dominio
2. construir los services nuevos sobre esa base
3. recién después adaptar UI y tests

## 13. Dirección del proyecto

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
El próximo salto ya no es más análisis ni setup de base, sino construir el dominio nuevo sobre repositories y services.
