Perfecto. Te dejo una **mini especificación funcional realista**, pensada como base de desarrollo de un MVP freelance, sin inflarla de más.

---

# Mini especificación funcional

## Proyecto: MVP de control operativo para car wash

## 1. Contexto del problema

Actualmente, el negocio registra parte de su operación de manera manual en cuaderno y luego transfiere la información a Excel. Este flujo genera trabajo duplicado y hace que el dueño no tenga visibilidad inmediata sobre el estado económico del negocio.

El principal problema no es la contabilidad formal de la empresa, sino la falta de un control operativo simple que permita conocer, durante la semana o el mes, si el negocio está generando ganancias o pérdidas.

Se busca una solución liviana que permita registrar ingresos y egresos diarios y visualizar un balance operativo actualizado.

---

## 2. Objetivo del MVP

Desarrollar una aplicación interna simple que permita registrar ingresos y egresos de un car wash y consultar el balance operativo del negocio en tiempo casi real.

---

## 3. Usuarios

### Usuario principal

* Dueño o encargado del negocio.

### Usuario operativo

* Trabajador o persona encargada de registrar servicios y gastos.

---

## 4. Alcance del MVP

## Incluye

* Registro de ingresos.
* Registro de egresos.
* Consulta de movimientos.
* Visualización de resumen operativo.
* Cálculo automático de balance.
* Exportación de datos a Excel o CSV.

## No incluye

* Contabilidad legal o impositiva.
* Facturación electrónica.
* Gestión de inventario.
* Gestión avanzada de clientes.
* Múltiples roles complejos.
* Sistema web público.
* App móvil nativa.
* Integración bancaria.

---

## 5. Flujo general del negocio con el sistema

### Flujo propuesto

1. Ocurre una operación del negocio.
2. Se registra directamente en la app.
3. La app guarda la información.
4. La app actualiza automáticamente los totales.
5. El dueño puede consultar en cualquier momento:

   * ingresos acumulados,
   * egresos acumulados,
   * balance neto.

### Resultado esperado

El negocio deja de depender de cálculos manuales al final de la semana o del mes para saber si está ganando o perdiendo dinero.

---

## 6. Requerimientos funcionales

## RF1. Registro de ingresos

El sistema debe permitir registrar un ingreso asociado a un servicio realizado.

### Datos mínimos del ingreso

* Fecha
* Tipo de servicio
* Monto
* Método de pago
* Observación opcional

---

## RF2. Registro de egresos

El sistema debe permitir registrar un egreso del negocio.

### Datos mínimos del egreso

* Fecha
* Categoría de gasto
* Monto
* Descripción opcional

---

## RF3. Catálogo básico por defecto

El sistema debe incluir una lista inicial de servicios y categorías de gasto para evitar carga completamente libre.

### Servicios por defecto

* Lavado básico
* Lavado completo
* Aspirado
* Encerado
* Otro

### Categorías por defecto

* Insumos
* Personal
* Combustible
* Mantenimiento
* Otros

---

## RF4. Consulta de movimientos

El sistema debe permitir visualizar los ingresos y egresos registrados.

### La consulta debe permitir

* ver lista de ingresos,
* ver lista de egresos,
* filtrar por rango de fechas.

---

## RF5. Resumen operativo

El sistema debe mostrar un resumen del negocio para un período determinado.

### Métricas mínimas

* Total de ingresos
* Total de egresos
* Balance neto
* Cantidad de servicios registrados
* Ingresos por tipo de servicio
* Egresos por categoría

---

## RF6. Balance por período

El sistema debe permitir consultar el balance para:

* hoy,
* esta semana,
* este mes,
* un rango personalizado.

---

## RF7. Exportación de datos

El sistema debe permitir exportar la información registrada a:

* CSV
* Excel

---

## RF8. Edición y eliminación básica

El sistema debe permitir corregir registros cargados por error.

### Alcance mínimo

* editar ingresos,
* editar egresos,
* eliminar registros.

---

## 7. Requerimientos no funcionales

## RNF1. Simplicidad de uso

La interfaz debe ser simple y comprensible para usuarios no técnicos.

## RNF2. Rapidez de carga

Registrar un movimiento debe requerir pocos campos y poco tiempo.

## RNF3. Persistencia

La información debe mantenerse guardada entre sesiones.

## RNF4. Funcionamiento local

El sistema debe poder funcionar localmente sin depender de conexión constante a internet.

## RNF5. Mantenibilidad

La estructura del proyecto debe permitir futuras mejoras sin rehacer todo desde cero.

---

## 8. Reglas de negocio iniciales

### RN1

Todo ingreso debe tener un monto mayor que cero.

### RN2

Todo egreso debe tener un monto mayor que cero.

### RN3

Cada ingreso debe estar asociado a un tipo de servicio.

### RN4

Cada egreso debe estar asociado a una categoría de gasto.

### RN5

El balance neto se calcula como:

**balance = total ingresos - total egresos**

### RN6

Los catálogos iniciales pueden ampliarse en versiones futuras según feedback real del negocio.

---

## 9. Datos mínimos a almacenar

## Ingreso

* id
* fecha
* servicio
* monto
* metodo_pago
* observacion
* created_at

## Egreso

* id
* fecha
* categoria
* monto
* descripcion
* created_at

---

## 10. Pantallas del MVP

## 1. Inicio / Dashboard

Debe mostrar:

* ingresos del día,
* egresos del día,
* balance del día,
* resumen rápido semanal o mensual.

## 2. Registrar ingreso

Formulario para cargar ingresos.

## 3. Registrar egreso

Formulario para cargar egresos.

## 4. Movimientos

Vista tabular con filtros por fecha.

## 5. Reportes

Resumen por período con métricas básicas.

## 6. Exportar

Descarga de CSV o Excel.

---

## 11. Arquitectura propuesta

## Stack

* **Streamlit** para la interfaz
* **SQLite** para persistencia
* **pandas** para manipulación de datos
* **openpyxl** para exportación a Excel

## Justificación

Se prioriza una solución liviana, rápida de desarrollar y adecuada para un MVP interno.

---

## 12. Estructura inicial del proyecto

```text
carwash_mvp/
│
├── app.py
├── database/
│   └── db.py
├── services/
│   ├── ingresos.py
│   ├── egresos.py
│   └── reportes.py
├── models/
│   └── schema.py
├── utils/
│   └── export.py
├── data/
│   └── carwash.db
├── exports/
├── requirements.txt
└── README.md
```

---

## 13. Criterios de éxito del MVP

Se considerará que el MVP cumple su objetivo si permite:

* registrar ingresos sin usar cuaderno,
* registrar egresos del día,
* visualizar cuánto ingresó y gastó el negocio,
* conocer el balance neto sin hacer cálculos manuales,
* exportar la información para revisión externa o archivo.

---

## 14. Posibles mejoras futuras

Estas mejoras no forman parte del MVP inicial, pero pueden incorporarse después de validar uso real:

* administración de servicios y categorías,
* historial por cliente,
* métricas más avanzadas,
* soporte multiusuario,
* carga desde celular más optimizada,
* despliegue en red local o nube,
* cierre diario de caja,
* comparación entre meses.

