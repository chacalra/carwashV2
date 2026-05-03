Sí. Ese es el siguiente paso correcto.

Te dejo un **documento técnico corto**, aterrizado al MVP, sin sobreingeniería.

---

# Documento técnico corto

## Proyecto: MVP de control operativo para car wash

## 1. Objetivo técnico

Construir una aplicación interna simple en **Streamlit + SQLite** que permita:

* registrar ingresos,
* registrar egresos,
* consultar movimientos,
* calcular balance operativo,
* exportar información.

La aplicación no busca resolver contabilidad formal, sino brindar **visibilidad operativa y rentabilidad acumulada**.

---

# 2. Stack técnico

## Interfaz

* **Streamlit**

## Persistencia

* **SQLite**

## Manipulación de datos y reportes

* **pandas**

## Exportación a Excel

* **openpyxl**

---

# 3. Modelo de datos

Para el MVP, yo usaría **4 tablas**:

1. `services`
2. `expense_categories`
3. `incomes`
4. `expenses`

---

## 3.1 Tabla `services`

Catálogo de servicios disponibles para registrar ingresos.

### Campos

* `id` INTEGER PRIMARY KEY AUTOINCREMENT
* `name` TEXT NOT NULL UNIQUE
* `is_active` INTEGER NOT NULL DEFAULT 1
* `created_at` TEXT NOT NULL

### Propósito

Evitar que el tipo de servicio sea texto totalmente libre y poder agrupar ingresos por servicio.

---

## 3.2 Tabla `expense_categories`

Catálogo de categorías de egreso.

### Campos

* `id` INTEGER PRIMARY KEY AUTOINCREMENT
* `name` TEXT NOT NULL UNIQUE
* `is_active` INTEGER NOT NULL DEFAULT 1
* `created_at` TEXT NOT NULL

### Propósito

Poder analizar en qué se gasta el dinero.

---

## 3.3 Tabla `incomes`

Registra los ingresos del negocio.

### Campos

* `id` INTEGER PRIMARY KEY AUTOINCREMENT
* `date` TEXT NOT NULL
* `service_id` INTEGER NOT NULL
* `amount` REAL NOT NULL
* `payment_method` TEXT
* `notes` TEXT
* `created_at` TEXT NOT NULL

### Claves

* FOREIGN KEY (`service_id`) REFERENCES `services`(`id`)

### Propósito

Registrar cada ingreso asociado a un servicio.

---

## 3.4 Tabla `expenses`

Registra los egresos del negocio.

### Campos

* `id` INTEGER PRIMARY KEY AUTOINCREMENT
* `date` TEXT NOT NULL
* `category_id` INTEGER NOT NULL
* `amount` REAL NOT NULL
* `description` TEXT
* `created_at` TEXT NOT NULL

### Claves

* FOREIGN KEY (`category_id`) REFERENCES `expense_categories`(`id`)

### Propósito

Registrar cada gasto asociado a una categoría.

---

# 4. Tipos de datos: decisión práctica

En SQLite los tipos son flexibles, pero para este MVP conviene esta convención:

* **INTEGER**: ids, flags
* **REAL**: montos
* **TEXT**: fechas, nombres, observaciones

## Fechas

Usaría fechas como texto en formato:

```text
YYYY-MM-DD
```

Ejemplo:

```text
2026-03-29
```

Eso simplifica filtros y evita complejidad innecesaria con datetime.

## Timestamps

Para `created_at`, usaría:

```text
YYYY-MM-DD HH:MM:SS
```

Ejemplo:

```text
2026-03-29 14:32:10
```

---

# 5. Relaciones

Las relaciones son simples:

## `services` → `incomes`

Un servicio puede estar asociado a muchos ingresos.

```text
services (1) ---- (N) incomes
```

## `expense_categories` → `expenses`

Una categoría puede estar asociada a muchos egresos.

```text
expense_categories (1) ---- (N) expenses
```

No necesitas más relaciones para esta primera versión.

---

# 6. Datos iniciales por defecto

## 6.1 Servicios iniciales

* Lavado básico
* Lavado completo
* Aspirado
* Encerado
* Otro

## 6.2 Categorías iniciales

* Insumos
* Personal
* Combustible
* Mantenimiento
* Otros

Esto se inserta automáticamente al inicializar la base.

---

# 7. Reglas técnicas y validaciones

## Ingresos

* `amount` debe ser mayor a 0
* `service_id` debe existir
* `date` no puede estar vacío

## Egresos

* `amount` debe ser mayor a 0
* `category_id` debe existir
* `date` no puede estar vacío

## Catálogos

* `name` debe ser único
* `name` no puede ser vacío

---

# 8. SQL propuesto

## 8.1 Crear tabla `services`

```sql
CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);
```

## 8.2 Crear tabla `expense_categories`

```sql
CREATE TABLE IF NOT EXISTS expense_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);
```

## 8.3 Crear tabla `incomes`

```sql
CREATE TABLE IF NOT EXISTS incomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    service_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    payment_method TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (service_id) REFERENCES services(id)
);
```

## 8.4 Crear tabla `expenses`

```sql
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (category_id) REFERENCES expense_categories(id)
);
```

---

# 9. Consultas principales que necesitará el sistema

## 9.1 Insertar ingreso

```sql
INSERT INTO incomes (date, service_id, amount, payment_method, notes, created_at)
VALUES (?, ?, ?, ?, ?, ?);
```

## 9.2 Insertar egreso

```sql
INSERT INTO expenses (date, category_id, amount, description, created_at)
VALUES (?, ?, ?, ?, ?);
```

## 9.3 Listar ingresos con nombre de servicio

```sql
SELECT
    incomes.id,
    incomes.date,
    services.name AS service,
    incomes.amount,
    incomes.payment_method,
    incomes.notes
FROM incomes
JOIN services ON incomes.service_id = services.id
ORDER BY incomes.date DESC, incomes.id DESC;
```

## 9.4 Listar egresos con nombre de categoría

```sql
SELECT
    expenses.id,
    expenses.date,
    expense_categories.name AS category,
    expenses.amount,
    expenses.description
FROM expenses
JOIN expense_categories ON expenses.category_id = expense_categories.id
ORDER BY expenses.date DESC, expenses.id DESC;
```

## 9.5 Total de ingresos por período

```sql
SELECT COALESCE(SUM(amount), 0)
FROM incomes
WHERE date BETWEEN ? AND ?;
```

## 9.6 Total de egresos por período

```sql
SELECT COALESCE(SUM(amount), 0)
FROM expenses
WHERE date BETWEEN ? AND ?;
```

## 9.7 Ingresos agrupados por servicio

```sql
SELECT
    services.name,
    COALESCE(SUM(incomes.amount), 0) AS total
FROM incomes
JOIN services ON incomes.service_id = services.id
WHERE incomes.date BETWEEN ? AND ?
GROUP BY services.name
ORDER BY total DESC;
```

## 9.8 Egresos agrupados por categoría

```sql
SELECT
    expense_categories.name,
    COALESCE(SUM(expenses.amount), 0) AS total
FROM expenses
JOIN expense_categories ON expenses.category_id = expense_categories.id
WHERE expenses.date BETWEEN ? AND ?
GROUP BY expense_categories.name
ORDER BY total DESC;
```

---

# 10. Orden de implementación

Acá está lo importante para que no te pierdas.

## Fase 1 — Base de datos

Primero implementaría:

* conexión SQLite,
* creación de tablas,
* carga de catálogos por defecto.

### Entregable

La base se crea sola al iniciar.

---

## Fase 2 — Registro de ingresos

Luego:

* formulario Streamlit para ingresos,
* validación básica,
* inserción en DB.

### Entregable

Ya se puede registrar ingreso real.

---

## Fase 3 — Registro de egresos

Después:

* formulario Streamlit para egresos,
* validación básica,
* inserción en DB.

### Entregable

Ya se puede registrar gasto real.

---

## Fase 4 — Consulta de movimientos

Luego:

* vista de ingresos,
* vista de egresos,
* filtro por fechas.

### Entregable

Ya se puede revisar información cargada.

---

## Fase 5 — Dashboard y balance

Después:

* ingresos totales,
* egresos totales,
* neto,
* agrupación por servicio,
* agrupación por categoría.

### Entregable

Ya se ve la rentabilidad operativa.

---

## Fase 6 — Edición y eliminación

Después:

* corregir registros,
* eliminar registros cargados por error.

### Entregable

El sistema ya es usable de verdad.

---

## Fase 7 — Exportación

Al final:

* exportar CSV,
* exportar Excel.

### Entregable

Proyecto más sólido para portafolio y útil para el negocio.

---

# 11. Estructura sugerida del código

```text
carwash_mvp/
│
├── app.py
├── database/
│   ├── connection.py
│   ├── schema.py
│   └── seed.py
├── repositories/
│   ├── services_repository.py
│   ├── expense_categories_repository.py
│   ├── incomes_repository.py
│   └── expenses_repository.py
├── services/
│   ├── income_service.py
│   ├── expense_service.py
│   └── report_service.py
├── ui/
│   ├── dashboard.py
│   ├── incomes_form.py
│   ├── expenses_form.py
│   ├── movements_view.py
│   └── export_view.py
├── utils/
│   ├── dates.py
│   └── export.py
├── data/
│   └── carwash.db
└── requirements.txt
```

Esto ya es suficientemente ordenado sin exagerar.

---

# 12. Decisiones técnicas que yo mantendría

## Sí haría

* catálogos separados
* foreign keys
* fechas simples como texto
* lógica separada por responsabilidad
* exportación desde pandas

## No haría todavía

* ORM
* autenticación
* migraciones complejas
* API REST
* PostgreSQL
* Docker
* tests completos desde el primer día

No porque estén mal, sino porque para este MVP bajarían demasiado el ritmo.

---

# 13. Riesgos técnicos a evitar

## Riesgo 1

Dejar servicio y categoría como texto libre total.
Eso destruye los reportes.

## Riesgo 2

Mezclar toda la lógica en `app.py`.
Te funcionará al inicio, pero luego será incómodo mantenerlo.

## Riesgo 3

Intentar meter funcionalidades de ERP.
Te rompe alcance y tiempo.

## Riesgo 4

No validar montos.
Después salen datos inválidos y el balance pierde credibilidad.

---

# Conclusión técnica final

La versión más realista y profesional de este MVP es:

* **Streamlit como interfaz**
* **SQLite como persistencia**
* **catálogos básicos para estructurar datos**
* **registro directo de ingresos y egresos**
* **dashboard operativo con balance acumulado**

Eso es suficiente para que el sistema tenga valor real y, al mismo tiempo, siga siendo terminable.

El siguiente paso correcto sería convertir esto en un **plan de implementación por archivos**, o directamente empezar por el primer bloque: **schema SQLite + seed inicial + conexión**.
