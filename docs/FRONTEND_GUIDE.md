# Guia de Integracion Frontend - AutoCare Backend

Este documento es la referencia de integracion para el equipo de frontend. Cubre URL base, autenticacion, endpoints, modelos de datos, CORS y manejo de errores.

---

## 1. URL Base y Documentacion Interactiva

### URL Base

| Entorno | URL |
|---|---|
| Desarrollo local | `http://localhost:8000` |
| Produccion | `https://<subdominio>.carwash.mukusoft.com` |

Cada lavanderia (tenant) tiene su propio subdominio. El subdominio se asigna por administracion, no lo elige el usuario.

### Swagger / Redoc

FastAPI expone documentacion interactiva en dos formatos:

| Tipo | URL | Para que sirve |
|---|---|---|
| Swagger UI | `http://localhost:8000/docs` | Probar endpoints en vivo desde el navegador |
| ReDoc | `http://localhost:8000/redoc` | Lectura mas comoda del contrato |
| OpenAPI JSON | `http://localhost:8000/openapi.json` | Schema crudo para generar clientes automaticos |

> Tip: pueden usar `openapi.json` con generadores como `openapi-typescript` u `openapi-generator` para autogenerar tipos del lado del frontend.

### Healthcheck

Para verificar que el backend esta vivo, sin necesidad de autenticacion:

```http
GET /health
```

Respuesta:
```json
{ "status": "ok" }
```

---

## 2. Modelo Multi-Tenant

Cada lavanderia es un tenant aislado, identificado por su `lavanderia_id`. Hay **dos formas** de indicarle al backend a que tenant pertenece la peticion:

### Opcion A - Por subdominio (produccion)

El backend extrae el subdominio del header `Host` automaticamente:

```http
POST /auth/login
Host: autocare.carwash.mukusoft.com
```

El subdominio `autocare` se mapea internamente al `lavanderia_id` correspondiente. Nginx ya esta configurado para pasar el header `Host` intacto.

### Opcion B - Por campo `subdominio` en el login (desarrollo o testing)

Si el frontend corre en localhost o no tiene un subdominio asignado, se puede mandar `subdominio` directo en el body del login:

```http
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123",
  "subdominio": "autocare"
}
```

**Una vez logueado**, el `lavanderia_id` queda embebido en el token JWT. No hace falta mandar el tenant en cada request.

---

## 3. Autenticacion

### Flujo

1. El frontend envia credenciales a `POST /auth/login`.
2. El backend devuelve un `access_token` (JWT firmado HS256) y la lista de permisos.
3. Para todo endpoint protegido, el frontend envia `Authorization: Bearer <token>`.
4. El token tiene expiracion (default 60 minutos). Cuando expira, hay que hacer login de nuevo.

### Login - Request

```http
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123",
  "subdominio": "autocare"
}
```

> El campo `subdominio` es opcional si el host ya identifica al tenant.

### Login - Response

```json
{
  "user": {
    "id": 7,
    "username": "admin",
    "role": "admin",
    "lavanderia_id": 3,
    "lavanderia_name": "Autocare Demo"
  },
  "permissions": [
    "dashboard",
    "register_sale",
    "edit_sale",
    "manage_sales",
    "register_expense",
    "movements",
    "export",
    "settings"
  ],
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ...",
  "token_type": "bearer",
  "expires_at": "2026-05-06T20:30:00+00:00"
}
```

### Enviar el token en peticiones autenticadas

```http
GET /sales/grouped?start_date=2026-05-01&end_date=2026-05-31
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ...
```

### Permisos disponibles

| Permiso | Para que sirve |
|---|---|
| `dashboard` | Ver el dashboard |
| `register_sale` | Crear ventas y vehiculos |
| `edit_sale` | Editar ventas existentes |
| `manage_sales` | Anular ventas |
| `register_expense` | Crear, editar y anular egresos |
| `movements` | Ver listados de ventas y egresos |
| `export` | Acceder a reportes y exportes |
| `settings` | Administrar catalogos, clientes, vehiculos |

El frontend debe usar la lista `permissions` recibida en login para mostrar/ocultar opciones de menu y botones.

---

## 4. CORS

El backend usa `fastapi.middleware.cors.CORSMiddleware` con configuracion via variable de entorno `CORS_ALLOW_ORIGIN_REGEX`.

### Configuracion actual

| Entorno | Origen permitido | Como se setea |
|---|---|---|
| Desarrollo | `http://localhost` y `https://localhost` con cualquier puerto | Default si no hay env var |
| Produccion | `https://<subdominio>.carwash.mukusoft.com` | `CORS_ALLOW_ORIGIN_REGEX=https://[a-z0-9-]+\.carwash\.mukusoft\.com` |

### Que esto significa para el frontend

- En desarrollo: el frontend puede correr en **cualquier puerto** de localhost (3000, 5173, 8080, lo que sea). Funciona out of the box.
- Metodos permitidos: `GET, POST, PUT, PATCH, DELETE, OPTIONS`
- Headers permitidos: `Authorization, Content-Type`
- Credentials: habilitado (necesario para mandar el `Authorization` header)

---

## 5. Endpoints Principales

Todos los endpoints (excepto `/health` y `/auth/login`) requieren `Authorization: Bearer <token>`.

### 5.1 Auth

| Metodo | Ruta | Permiso | Descripcion |
|---|---|---|---|
| `POST` | `/auth/login` | publico | Devuelve token JWT |

### 5.2 Sales (Ventas)

| Metodo | Ruta | Permiso | Descripcion |
|---|---|---|---|
| `GET` | `/sales` | `movements` | Lista plana para exportar |
| `GET` | `/sales/grouped` | `movements` | Ventas agrupadas con detalles |
| `GET` | `/sales/{id}` | `movements` | Detalle completo de una venta |
| `POST` | `/sales` | `register_sale` | Crear venta con detalles |
| `PUT` | `/sales/{id}` | `edit_sale` | Editar venta completa |
| `PATCH` | `/sales/{id}/payment-type` | `edit_sale` | Cambiar tipo de cobro |
| `DELETE` | `/sales/{id}` | `manage_sales` | Anular venta (soft delete) |

**Ejemplo respuesta `GET /sales/grouped`:**

```json
[
  {
    "id": 10,
    "date": "2026-05-01",
    "created_at": "2026-05-01T14:30:00+00:00",
    "payment_type": "Contado",
    "payment_method": "Efectivo",
    "requires_invoice": false,
    "total": 62000.0,
    "notes": "Cliente frecuente",
    "is_voided": false,
    "customer_id": 4,
    "customer_name": "Ana Perez",
    "ruc_ci": null,
    "vehicle_id": 9,
    "license_plate": "ABC123",
    "vehicle_type_id": 1,
    "vehicle_type_name": "Auto",
    "created_by_user_id": 2,
    "created_by": "operador1",
    "lavanderia_id": 3,
    "items": [
      {
        "id": 100,
        "item_type": "Servicio",
        "item_name": "Lavado",
        "service_id": 5,
        "product_id": null,
        "quantity": 1,
        "unit_price": 50000.0,
        "subtotal": 50000.0
      },
      {
        "id": 101,
        "item_type": "Producto",
        "item_name": "Cera",
        "service_id": null,
        "product_id": 7,
        "quantity": 1,
        "unit_price": 12000.0,
        "subtotal": 12000.0
      }
    ]
  }
]
```

**Ejemplo request `POST /sales`:**

```json
{
  "fecha_venta": "2026-05-01",
  "tipo_cobro": "Contado",
  "metodo_pago": "Efectivo",
  "items": [
    { "servicio_id": 5, "cantidad": 1 },
    { "producto_id": 7, "cantidad": 2 }
  ],
  "vehiculo_id": 9,
  "cliente_id": 4,
  "observacion": "Cliente frecuente"
}
```

> El `usuario_id` se toma del token. Si se manda y no coincide con el usuario autenticado, devuelve **403**.

### 5.3 Expenses (Egresos)

| Metodo | Ruta | Permiso | Descripcion |
|---|---|---|---|
| `GET` | `/expenses` | `movements` | Lista de egresos |
| `GET` | `/expenses/{id}` | `movements` | Detalle de un egreso |
| `POST` | `/expenses` | `register_expense` | Crear egreso |
| `PUT` | `/expenses/{id}` | `register_expense` | Editar egreso |
| `DELETE` | `/expenses/{id}` | `register_expense` | Anular egreso (soft delete) |

**Ejemplo respuesta `GET /expenses/{id}`:**

```json
{
  "id": 88,
  "date": "2026-05-01",
  "category_id": 4,
  "category": "Insumos",
  "amount": 25000.0,
  "description": "Compra de jabon",
  "created_by": "admin",
  "user_id": 2,
  "created_at": "2026-05-01T10:15:00+00:00",
  "lavanderia_id": 3,
  "estado": true
}
```

### 5.4 Vehicles (Vehiculos)

| Metodo | Ruta | Permiso | Descripcion |
|---|---|---|---|
| `GET` | `/vehicles` | `register_sale` o `settings` | Lista vehiculos (filtros: `only_active`, `search`) |
| `GET` | `/vehicles/by-plate/{plate}` | `register_sale` | Buscar por matricula |
| `GET` | `/vehicles/{id}` | `register_sale` o `settings` | Detalle |
| `POST` | `/vehicles` | `register_sale` | Crear o actualizar (upsert por matricula) |
| `PUT` | `/vehicles/{id}` | `settings` | Editar tipo y datos |
| `PATCH` | `/vehicles/{id}/status` | `settings` | Activar/desactivar |

### 5.5 Clients (Clientes)

| Metodo | Ruta | Permiso | Descripcion |
|---|---|---|---|
| `GET` | `/clients?only_active=true` | varios (operativos o `settings`) | Lista de clientes |
| `GET` | `/clients/by-ruc-ci/{ruc_ci}` | varios | Buscar por RUC/CI |
| `POST` | `/clients` | `settings` | Crear cliente |
| `PUT` | `/clients/{id}` | `settings` | Editar cliente |
| `PATCH` | `/clients/{id}/status` | `settings` | Activar/desactivar |

### 5.6 Catalogs (Catalogos)

Cuatro catalogos con la misma estructura: `services`, `products`, `expense-categories`, `vehicle-types`.

| Metodo | Ruta | Permiso | Descripcion |
|---|---|---|---|
| `GET` | `/catalogs/{tipo}?only_active=true` | varios | Listar |
| `POST` | `/catalogs/{tipo}` | `settings` | Crear |
| `PUT` | `/catalogs/{tipo}/{id}` | `settings` | Editar |
| `PATCH` | `/catalogs/{tipo}/{id}/status` | `settings` | Activar/desactivar |
| `DELETE` | `/catalogs/{tipo}/{id}` | `settings` | Eliminar (si no esta referenciado) |

> `services` y `products` aceptan `price` en el body. Las categorias de egreso y tipos de vehiculo solo aceptan `name`.

### 5.7 Reports (Reportes)

| Metodo | Ruta | Permiso | Descripcion |
|---|---|---|---|
| `GET` | `/reports/sales-summary?start_date=&end_date=` | `export` | Resumen de ventas y egresos por periodo |

**Ejemplo respuesta:**

```json
{
  "start_date": "2026-05-01",
  "end_date": "2026-05-31",
  "sales_total": 1500000.0,
  "expense_total": 250000.0,
  "net_balance": 1250000.0,
  "service_count": 25,
  "service_sales_total": 1200000.0,
  "product_count": 12,
  "sales_breakdown": [
    { "name": "Lavado", "count": 20, "total": 1000000.0 },
    { "name": "Encerado", "count": 5, "total": 200000.0 }
  ],
  "expense_breakdown": [
    { "name": "Insumos", "count": null, "total": 200000.0 },
    { "name": "Sueldos", "count": null, "total": 50000.0 }
  ],
  "payment_breakdown": {
    "contado": 1200000.0,
    "credito": 300000.0
  }
}
```

---

## 6. Modelos de Datos

Los schemas vienen de `backend/api/schemas/*.py` (Pydantic v2). Esta es una referencia rapida de los principales.

### `UserResponse`

```typescript
{
  id: number
  username: string
  role: string | null
  lavanderia_id: number
  lavanderia_name: string | null
}
```

### `LoginResponse`

```typescript
{
  user: UserResponse
  permissions: string[]
  access_token: string
  token_type: "bearer"
  expires_at: string  // ISO 8601 datetime
}
```

### `SaleResponse` (venta agrupada)

```typescript
{
  id: number
  date: string                  // ISO date "YYYY-MM-DD"
  created_at: string | null     // ISO datetime
  payment_type: string          // "Contado" | "Credito"
  payment_method: string | null // "Efectivo" | "Transferencia" | etc.
  requires_invoice: boolean
  total: number
  notes: string | null
  is_voided: boolean            // true si fue anulada
  customer_id: number
  customer_name: string
  ruc_ci: string | null
  vehicle_id: number | null
  license_plate: string | null
  vehicle_type_id: number | null
  vehicle_type_name: string | null
  created_by_user_id: number
  created_by: string
  lavanderia_id: number
  items: SaleItemResponse[]
}
```

### `SaleItemResponse`

```typescript
{
  id: number
  item_type: "Servicio" | "Producto"
  item_name: string
  service_id: number | null
  product_id: number | null
  quantity: number
  unit_price: number
  subtotal: number
}
```

### `SaleCreateRequest`

```typescript
{
  fecha_venta: string           // "YYYY-MM-DD"
  tipo_cobro: "Contado" | "Credito"
  items: SaleItemRequest[]      // min 1
  metodo_pago?: string
  cliente_id?: number
  vehiculo_id?: number
  observacion?: string
  requiere_factura?: boolean    // default false
  ruc_ci?: string               // requerido si requiere_factura=true
  razon_social?: string         // requerido si requiere_factura=true
  usuario_id?: number           // se ignora si != usuario autenticado
}
```

### `ExpenseResponse`

```typescript
{
  id: number
  date: string
  category_id: number
  category: string | null
  amount: number
  description: string | null
  created_by: string | null
  user_id: number
  created_at: string | null
  lavanderia_id: number
  estado: boolean               // false si fue anulado
}
```

### `VehicleResponse`

```typescript
{
  id: number
  license_plate: string | null
  vehicle_type_id: number
  vehicle_type_name: string | null
  owner_name: string | null
  phone: string | null
  client_id: number | null
  is_active: boolean
  created_at: string | null
  lavanderia_id: number
}
```

### `ClientResponse`

```typescript
{
  id: number
  name: string
  client_type: "particular" | "empresa" | "generico"
  ruc_ci: string | null
  phone: string | null
  email: string | null
  is_active: boolean
  created_at: string | null
  lavanderia_id: number
}
```

### `CatalogItem` (servicios y productos)

```typescript
{
  id: number
  name: string
  price: number | null
  is_active: boolean
  created_at: string | null
  lavanderia_id: number
}
```

### `CreatedResponse` y `MessageResponse`

```typescript
// Genericos para creaciones y operaciones
{ id: number }
{ message: string }
```

---

## 7. Manejo de Errores

Todas las respuestas de error siguen el formato estandar de FastAPI:

```json
{ "detail": "<mensaje legible para el usuario>" }
```

### Codigos HTTP usados

| Codigo | Cuando | Ejemplo de `detail` |
|---|---|---|
| **400** | Validacion de dominio fallida (regla de negocio) | `"El monto del egreso debe ser mayor que cero."` |
| **401** | Token ausente, invalido o expirado | `"Hace falta un token Bearer."` / `"Token expirado."` |
| **403** | Token valido pero falta el permiso, o tenant equivocado | `"No tiene permiso para esta accion."` |
| **404** | Recurso no encontrado | `"El egreso indicado no existe."` |
| **409** | Conflicto: recurso ya anulado, duplicado, restriccion DB | `"La venta ya fue anulada."` |
| **422** | Validacion de Pydantic fallida (formato del JSON) | Detalle estructurado por campo |
| **500** | Error interno no manejado | `"Error interno del servidor."` |

### 400 - Bad Request (ejemplo)

```http
POST /sales
{
  "fecha_venta": "2026-05-01",
  "tipo_cobro": "Pix",
  "items": []
}
```

```json
HTTP/1.1 400 Bad Request
{ "detail": "El tipo de cobro debe ser Contado o Credito." }
```

### 401 - Unauthorized (ejemplo)

```http
GET /sales
```
(sin Authorization header)

```json
HTTP/1.1 401 Unauthorized
{ "detail": "Hace falta un token Bearer." }
```

```http
GET /sales
Authorization: Bearer <token-expirado>
```

```json
HTTP/1.1 401 Unauthorized
{ "detail": "Token expirado." }
```

### 403 - Forbidden (ejemplo)

```http
GET /reports/sales-summary?start_date=2026-05-01&end_date=2026-05-31
Authorization: Bearer <token-sin-permiso-export>
```

```json
HTTP/1.1 403 Forbidden
{ "detail": "No tiene permiso para esta accion." }
```

### 404 - Not Found (ejemplo)

```http
GET /sales/9999
Authorization: Bearer <token>
```

```json
HTTP/1.1 404 Not Found
{ "detail": "La venta indicada no existe en esta lavanderia." }
```

### 409 - Conflict (ejemplo)

```http
DELETE /sales/10
Authorization: Bearer <token>
```
(donde la venta 10 ya fue anulada anteriormente)

```json
HTTP/1.1 409 Conflict
{ "detail": "La venta ya fue anulada." }
```

### 422 - Unprocessable Entity (formato distinto, viene de Pydantic)

```http
POST /auth/login
{ "username": "" }
```

```json
HTTP/1.1 422 Unprocessable Entity
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "username"],
      "msg": "String should have at least 1 character",
      "input": ""
    },
    {
      "type": "missing",
      "loc": ["body", "password"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

> **Importante:** los errores 422 tienen un formato distinto (`detail` es un array). El frontend debe manejar ambos casos: `detail: string` y `detail: ValidationError[]`.

### Patron sugerido para el frontend

```typescript
async function apiFetch<T>(url: string, options: RequestInit): Promise<T> {
  const response = await fetch(url, options);

  if (response.status === 401) {
    // Token invalido o expirado: forzar relogin
    redirectToLogin();
    throw new Error("No autenticado");
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: "Error desconocido" }));
    const message = typeof body.detail === "string"
      ? body.detail
      : "Error de validacion";
    throw new Error(message);
  }

  return response.json();
}
```

---

## 8. Notas Operacionales

### Fechas y horarios

- **Fechas**: formato ISO `YYYY-MM-DD` (ej: `"2026-05-01"`).
- **Datetimes**: ISO 8601 con timezone (ej: `"2026-05-01T14:30:00+00:00"`).
- El backend almacena fechas en UTC. El frontend deberia formatear segun la zona horaria del usuario.

### Montos

- Todos los montos vienen como `number` (float). En el dominio de Paraguay son guaranies sin decimales.
- Para mostrar al usuario, formatear con separador de miles (ej: `Gs. 50.000`).

### Soft delete (anulacion logica)

- Ventas y egresos no se eliminan fisicamente. Cuando se "borran" se marcan con `estado=false` (egresos) o `is_voided=true` (ventas).
- Las listas (`GET /sales`, `GET /sales/grouped`, `GET /expenses`) **no devuelven** registros anulados.
- `GET /sales/{id}` y `GET /expenses/{id}` **si devuelven** registros anulados, con la flag correspondiente. Util para mostrar historicos.

### Multi-tenant (recordatorio importante)

- El frontend **nunca** debe enviar `lavanderia_id` en los requests. El tenant se determina del token.
- Si se envia `usuario_id` en POST/PUT y no coincide con el usuario del token, devuelve **403**.

### Paginacion

- **Actualmente no hay paginacion**. Todos los listados devuelven el resultado completo del periodo o filtro.
- Para listados de fechas (ventas, egresos), filtrar siempre por `start_date` y `end_date` para evitar respuestas grandes.

### Permisos en el frontend

- Usar la lista `permissions` del login para mostrar/ocultar acciones, **pero** validar siempre del lado del backend tambien.
- El backend siempre devuelve **403** si falta un permiso, no importa lo que el frontend muestre.

---

## 9. Ejemplo Completo de Flujo

```typescript
// 1. Login
const loginResponse = await fetch("http://localhost:8000/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    username: "admin",
    password: "admin123",
    subdominio: "autocare",
  }),
});

const { access_token, permissions, user } = await loginResponse.json();

// 2. Guardar token (localStorage, secure cookie, lo que decidan)
localStorage.setItem("token", access_token);

// 3. Listar ventas del mes
const salesResponse = await fetch(
  "http://localhost:8000/sales/grouped?start_date=2026-05-01&end_date=2026-05-31",
  {
    headers: { "Authorization": `Bearer ${access_token}` },
  }
);

const sales = await salesResponse.json();

// 4. Crear una venta
const newSaleResponse = await fetch("http://localhost:8000/sales", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${access_token}`,
  },
  body: JSON.stringify({
    fecha_venta: "2026-05-06",
    tipo_cobro: "Contado",
    metodo_pago: "Efectivo",
    items: [{ servicio_id: 5, cantidad: 1 }],
  }),
});

const { id: newSaleId } = await newSaleResponse.json();
```

---

## 10. Contacto y Soporte

Para dudas sobre el contrato del backend o pedir endpoints nuevos, consultar el archivo `backend/ESTADO_BACKEND.md` que documenta el estado actual y los pendientes.

La documentacion interactiva en `/docs` es la fuente de verdad - si hay diferencias entre este documento y Swagger, prevalece Swagger.
