# Plan de desarrollo por archivos

## Proyecto: MVP de control operativo para car wash

Este documento traduce la definición funcional y el documento técnico en una guía de implementación concreta por archivos. La idea es que sirva como mapa de trabajo para construir el proyecto sin mezclar responsabilidades y sin perder de vista el alcance del MVP.

---

## 1. Objetivo de este documento

Definir:

* qué archivos tendrá el proyecto,
* qué responsabilidad tendrá cada archivo,
* qué funciones o componentes mínimos debería contener,
* en qué orden conviene implementarlos.

No busca cerrar todos los detalles de código, sino dejar una estructura suficientemente clara para desarrollar con criterio.

---

## 2. Estructura objetivo del proyecto

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

---

## 3. Criterio general de arquitectura

La separación propuesta es esta:

* `database/`: conexión, creación de tablas y carga inicial.
* `repositories/`: acceso directo a SQLite.
* `services/`: reglas de negocio, validaciones y reportes.
* `ui/`: pantallas y formularios de Streamlit.
* `utils/`: helpers reutilizables.
* `app.py`: punto de entrada y navegación principal.

La regla práctica es:

* la UI no debería escribir SQL directo,
* los repositories no deberían contener lógica de presentación,
* los services deberían coordinar validación + repository,
* `app.py` no debería concentrar toda la lógica del sistema.

---

## 4. Entorno de desarrollo

### Decisión de entorno

El proyecto usará `uv` para gestionar el entorno virtual, las dependencias y la ejecución local de la aplicación.

### Qué implica en la práctica

* crear entorno virtual con `uv venv`,
* instalar dependencias con `uv add`,
* ejecutar la app con `uv run streamlit run app.py`,
* mantener una forma simple y reproducible de levantar el proyecto.

### Comandos base esperados

```bash
uv venv
uv add streamlit pandas openpyxl
uv run streamlit run app.py
```

### Observación

Esta decisión afecta la forma de trabajar el proyecto, pero no cambia la arquitectura funcional ni la separación por capas.

---

## 5. Plan por archivos

## 5.1 `app.py`

### Responsabilidad

Ser el punto de entrada principal de Streamlit y coordinar la navegación entre pantallas.

### Qué debería hacer

* inicializar base de datos al arrancar,
* cargar catálogos iniciales si no existen,
* mostrar menú lateral o navegación,
* renderizar la vista seleccionada.

### Funciones mínimas sugeridas

* `main()`
* `initialize_app()`
* `render_navigation()`

### Dependencias principales

* `database.schema`
* `database.seed`
* módulos de `ui/`

### Qué no debería hacer

* consultas SQL directas,
* validaciones de negocio extensas,
* lógica de exportación embebida.

---

## 5.2 `database/connection.py`

### Responsabilidad

Centralizar la conexión a SQLite.

### Qué debería hacer

* crear y devolver la conexión a la base,
* asegurar activación de foreign keys,
* apuntar al archivo `data/carwash.db`.

### Funciones mínimas sugeridas

* `get_connection()`
* `enable_foreign_keys(connection)`

### Decisiones prácticas

* usar `sqlite3`,
* devolver conexiones listas para usarse,
* mantener este archivo pequeño y estable.

---

## 5.3 `database/schema.py`

### Responsabilidad

Crear las tablas del sistema.

### Qué debería hacer

* ejecutar `CREATE TABLE IF NOT EXISTS` para:
  * `services`
  * `expense_categories`
  * `incomes`
  * `expenses`

### Funciones mínimas sugeridas

* `create_tables()`
* `create_services_table(connection)`
* `create_expense_categories_table(connection)`
* `create_incomes_table(connection)`
* `create_expenses_table(connection)`

### Observación

Si se busca simplicidad, también se puede dejar una sola función `create_tables()` que encapsule todo.

---

## 5.4 `database/seed.py`

### Responsabilidad

Insertar los catálogos iniciales por defecto.

### Qué debería hacer

* insertar servicios base,
* insertar categorías de egreso base,
* evitar duplicados si ya existen datos.

### Funciones mínimas sugeridas

* `seed_initial_data()`
* `seed_services(connection)`
* `seed_expense_categories(connection)`

### Datos por defecto

#### Servicios

* Lavado básico
* Lavado completo
* Aspirado
* Encerado
* Otro

#### Categorías

* Insumos
* Personal
* Combustible
* Mantenimiento
* Otros

---

## 5.5 `repositories/services_repository.py`

### Responsabilidad

Gestionar el acceso a datos del catálogo de servicios.

### Qué debería hacer

* listar servicios activos,
* buscar servicio por id,
* crear nuevos servicios si más adelante se habilita mantenimiento de catálogos.

### Funciones mínimas sugeridas

* `get_all_services()`
* `get_active_services()`
* `get_service_by_id(service_id)`

### Nota

Para el MVP inicial, con lectura del catálogo podría alcanzar.

---

## 5.6 `repositories/expense_categories_repository.py`

### Responsabilidad

Gestionar el acceso a datos del catálogo de categorías de egreso.

### Funciones mínimas sugeridas

* `get_all_categories()`
* `get_active_categories()`
* `get_category_by_id(category_id)`

### Nota

Misma lógica que servicios, pero aplicada a egresos.

---

## 5.7 `repositories/incomes_repository.py`

### Responsabilidad

Persistir y consultar ingresos.

### Qué debería hacer

* insertar ingresos,
* listar ingresos,
* filtrar por fechas,
* actualizar ingresos,
* eliminar ingresos,
* agrupar ingresos por servicio.

### Funciones mínimas sugeridas

* `create_income(date, service_id, amount, payment_method, notes, created_at)`
* `get_incomes(start_date=None, end_date=None)`
* `get_income_by_id(income_id)`
* `update_income(income_id, date, service_id, amount, payment_method, notes)`
* `delete_income(income_id)`
* `get_income_totals_by_period(start_date, end_date)`
* `get_income_grouped_by_service(start_date, end_date)`

---

## 5.8 `repositories/expenses_repository.py`

### Responsabilidad

Persistir y consultar egresos.

### Qué debería hacer

* insertar egresos,
* listar egresos,
* filtrar por fechas,
* actualizar egresos,
* eliminar egresos,
* agrupar egresos por categoría.

### Funciones mínimas sugeridas

* `create_expense(date, category_id, amount, description, created_at)`
* `get_expenses(start_date=None, end_date=None)`
* `get_expense_by_id(expense_id)`
* `update_expense(expense_id, date, category_id, amount, description)`
* `delete_expense(expense_id)`
* `get_expense_totals_by_period(start_date, end_date)`
* `get_expenses_grouped_by_category(start_date, end_date)`

---

## 5.9 `services/income_service.py`

### Responsabilidad

Aplicar reglas de negocio sobre ingresos antes de guardar o modificar datos.

### Qué debería hacer

* validar monto mayor a 0,
* validar que exista el servicio,
* validar fecha obligatoria,
* delegar persistencia al repository.

### Funciones mínimas sugeridas

* `register_income(...)`
* `edit_income(...)`
* `remove_income(income_id)`
* `validate_income_data(...)`

### Beneficio

Evita meter validaciones en la UI o en SQL suelto.

---

## 5.10 `services/expense_service.py`

### Responsabilidad

Aplicar reglas de negocio sobre egresos.

### Qué debería hacer

* validar monto mayor a 0,
* validar que exista la categoría,
* validar fecha obligatoria,
* delegar persistencia al repository.

### Funciones mínimas sugeridas

* `register_expense(...)`
* `edit_expense(...)`
* `remove_expense(expense_id)`
* `validate_expense_data(...)`

---

## 5.11 `services/report_service.py`

### Responsabilidad

Centralizar cálculos y reportes operativos.

### Qué debería hacer

* calcular total de ingresos,
* calcular total de egresos,
* calcular balance neto,
* contar servicios registrados,
* obtener agrupaciones por servicio y categoría.

### Funciones mínimas sugeridas

* `get_summary(start_date, end_date)`
* `get_income_total(start_date, end_date)`
* `get_expense_total(start_date, end_date)`
* `get_net_balance(start_date, end_date)`
* `get_income_breakdown(start_date, end_date)`
* `get_expense_breakdown(start_date, end_date)`

### Salida esperada

Idealmente un diccionario simple o estructuras fáciles de consumir desde Streamlit.

---

## 5.12 `ui/dashboard.py`

### Responsabilidad

Mostrar el resumen operativo principal del negocio.

### Qué debería hacer

* permitir seleccionar período,
* mostrar total de ingresos,
* mostrar total de egresos,
* mostrar balance neto,
* mostrar tablas o gráficos simples por servicio y categoría.

### Funciones mínimas sugeridas

* `render_dashboard()`
* `render_summary_cards(summary)`
* `render_breakdowns(summary)`

---

## 5.13 `ui/incomes_form.py`

### Responsabilidad

Mostrar formulario para registrar y eventualmente editar ingresos.

### Qué debería hacer

* cargar catálogo de servicios,
* recibir fecha, servicio, monto, método de pago y nota,
* validar entradas de usuario,
* llamar a `income_service`.

### Funciones mínimas sugeridas

* `render_income_form()`
* `render_income_edit_form(income_id)`

### Nota

En la primera versión podría existir solo el formulario de alta.

---

## 5.14 `ui/expenses_form.py`

### Responsabilidad

Mostrar formulario para registrar y eventualmente editar egresos.

### Qué debería hacer

* cargar categorías,
* recibir fecha, categoría, monto y descripción,
* validar entradas de usuario,
* llamar a `expense_service`.

### Funciones mínimas sugeridas

* `render_expense_form()`
* `render_expense_edit_form(expense_id)`

---

## 5.15 `ui/movements_view.py`

### Responsabilidad

Mostrar la consulta de movimientos registrados.

### Qué debería hacer

* listar ingresos,
* listar egresos,
* permitir filtro por rango de fechas,
* ofrecer acciones de editar y eliminar.

### Funciones mínimas sugeridas

* `render_movements_view()`
* `render_incomes_table(start_date, end_date)`
* `render_expenses_table(start_date, end_date)`

### Observación

Si Streamlit complica demasiado la edición inline, puede resolverse con selección de registro + formulario aparte.

---

## 5.16 `ui/export_view.py`

### Responsabilidad

Mostrar opciones de exportación de datos.

### Qué debería hacer

* permitir elegir período,
* exportar ingresos,
* exportar egresos,
* exportar resumen si se desea,
* descargar CSV o Excel.

### Funciones mínimas sugeridas

* `render_export_view()`
* `render_csv_export()`
* `render_excel_export()`

---

## 5.17 `utils/dates.py`

### Responsabilidad

Agrupar utilidades de manejo de fechas para no repetir lógica.

### Qué debería hacer

* obtener fecha actual,
* calcular rangos predefinidos,
* normalizar formato de fechas.

### Funciones mínimas sugeridas

* `get_today()`
* `get_current_week_range()`
* `get_current_month_range()`
* `format_date(date_value)`

---

## 5.18 `utils/export.py`

### Responsabilidad

Generar archivos exportables a partir de DataFrames o listas de registros.

### Qué debería hacer

* convertir datos a CSV,
* convertir datos a Excel,
* preparar nombres de archivo.

### Funciones mínimas sugeridas

* `export_dataframe_to_csv(df)`
* `export_dataframe_to_excel(df_dict)`
* `build_export_filename(prefix, start_date, end_date, extension)`

### Nota

Para Excel puede convenir soportar varias hojas, por ejemplo:

* `Ingresos`
* `Egresos`
* `Resumen`

---

## 5.19 `requirements.txt`

### Responsabilidad

Declarar dependencias necesarias del proyecto.

### Contenido mínimo esperado

```text
streamlit
pandas
openpyxl
```

### Nota

Si se trabaja con `uv`, este archivo puede mantenerse solo por compatibilidad o referencia, pero la fuente principal de dependencias pasará a ser la configuración que genere `uv`.

`sqlite3` no se agrega porque ya forma parte de la librería estándar de Python.

---

## 5.20 `data/carwash.db`

### Responsabilidad

Archivo físico de persistencia SQLite.

### Consideraciones

* no se escribe manualmente,
* se crea automáticamente al iniciar la app si no existe,
* conviene mantenerlo fuera de la lógica de código.

---

## 6. Orden recomendado de implementación

Para construir el MVP sin trabarse, este sería el orden correcto:

## Etapa 1. Base del proyecto

1. `requirements.txt`
2. `database/connection.py`
3. `database/schema.py`
4. `database/seed.py`
5. prueba de inicialización desde `app.py`

### Resultado esperado

La app arranca y crea la base correctamente.

---

## Etapa 2. Catálogos y repositories base

6. `repositories/services_repository.py`
7. `repositories/expense_categories_repository.py`
8. `repositories/incomes_repository.py`
9. `repositories/expenses_repository.py`

### Resultado esperado

Ya existe acceso ordenado a los datos.

---

## Etapa 3. Reglas de negocio

10. `services/income_service.py`
11. `services/expense_service.py`
12. `services/report_service.py`

### Resultado esperado

La lógica ya no depende directamente de la UI.

---

## Etapa 4. Pantallas operativas

13. `ui/incomes_form.py`
14. `ui/expenses_form.py`
15. `ui/movements_view.py`
16. `ui/dashboard.py`

### Resultado esperado

El sistema ya permite operar el negocio.

---

## Etapa 5. Exportación y helpers

17. `utils/dates.py`
18. `utils/export.py`
19. `ui/export_view.py`

### Resultado esperado

El usuario puede descargar información útil.

---

## Etapa 6. Ajustes finales del MVP

20. completar edición y eliminación
21. revisar validaciones
22. mejorar mensajes de éxito y error
23. revisar consistencia de navegación

### Resultado esperado

MVP usable, ordenado y presentable.

---

## 7. Dependencias entre archivos

La relación principal entre módulos sería esta:

```text
app.py
  -> ui/*
  -> database/schema.py
  -> database/seed.py

ui/*
  -> services/*
  -> repositories de catálogos cuando haga falta poblar selectores

services/*
  -> repositories/*
  -> utils/*

repositories/*
  -> database/connection.py

database/schema.py
  -> database/connection.py

database/seed.py
  -> database/connection.py
```

La dirección ideal siempre debería ser hacia abajo:

* UI llama services,
* services llama repositories,
* repositories llama database.

---

## 8. Alcance mínimo real para una primera versión usable

Si hay que recortar para terminar rápido, el mínimo recomendable sería:

* creación automática de DB,
* catálogos iniciales,
* formulario de ingresos,
* formulario de egresos,
* vista simple de movimientos,
* dashboard con ingresos, egresos y neto.

Se puede dejar para después:

* edición,
* eliminación,
* exportación Excel,
* gráficos más elaborados,
* administración de catálogos.

---

## 9. Criterios de calidad mínimos

Cada archivo nuevo debería cumplir estas reglas:

* una responsabilidad principal clara,
* nombres de funciones directos,
* no duplicar lógica,
* no meter SQL en la UI,
* no meter todo en `app.py`,
* validar montos y fechas antes de guardar.

---

## 10. Conclusión

La mejor forma de desarrollar este MVP es usar el documento funcional como referencia de alcance, el documento técnico como base de decisiones y este archivo como guía de implementación concreta.

Con esta estructura, el proyecto queda:

* suficientemente simple para terminarse,
* suficientemente ordenado para mantenerse,
* suficientemente profesional para mostrarlo como trabajo real.

El siguiente paso natural, si se quiere pasar de planificación a ejecución, es empezar por:

1. `requirements.txt`
2. `database/connection.py`
3. `database/schema.py`
4. `database/seed.py`
5. `app.py` mínimo para inicializar todo
