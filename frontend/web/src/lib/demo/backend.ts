/**
 * Backend simulado para la demo pública (GitHub Pages).
 *
 * Responde los mismos endpoints y formas que la API FastAPI, pero en el
 * navegador: los datos se generan con una semilla fija relativa a "hoy" y se
 * guardan en localStorage (cada navegación de Astro recarga la página, así
 * que en memoria se perderían). Lo que el visitante carga queda solo en su
 * navegador. Los datos se regeneran cada día para que el período actual
 * nunca quede vacío.
 *
 * Solo se importa (dinámicamente) cuando PUBLIC_DEMO=true.
 */

import { addDays, format } from "date-fns";

import type { components } from "@/lib/api/schema";

type S = components["schemas"];

const STORAGE_KEY = "carwash.demo.v1";
const TENANT_ID = 1;
const TENANT_NAME = "Lavadero Demo";

// ---------------------------------------------------------------------------
// Modelo
// ---------------------------------------------------------------------------

interface CatalogRow {
  id: number;
  name: string;
  price?: number | null;
  is_active: boolean;
  created_at: string;
}

interface ClientRow {
  id: number;
  name: string;
  client_type: "Generico" | "Particular" | "Empresa";
  ruc_ci: string | null;
  is_active: boolean;
  created_at: string;
}

interface VehicleRow {
  id: number;
  license_plate: string;
  vehicle_type_id: number;
  client_id: number | null;
  is_active: boolean;
  created_at: string;
}

interface SaleItemRow {
  id: number;
  kind: "service" | "product";
  ref_id: number;
  name: string;
  quantity: number;
  unit_price: number;
}

interface SaleRow {
  id: number;
  date: string;
  created_at: string;
  payment_type: "Contado" | "Credito";
  payment_method: string | null;
  requires_invoice: boolean;
  notes: string | null;
  is_voided: boolean;
  customer_id: number;
  vehicle_id: number | null;
  user_id: number;
  items: SaleItemRow[];
}

interface ExpenseRow {
  id: number;
  date: string;
  category_id: number;
  amount: number;
  description: string | null;
  is_voided: boolean;
  user_id: number;
}

interface RoleRow {
  id: number;
  name: string;
  is_active: boolean;
  permissions: string[];
}

interface UserRow {
  id: number;
  username: string;
  role_id: number;
  is_active: boolean;
  created_at: string;
}

interface DemoDb {
  version: 1;
  seededOn: string;
  seq: number;
  services: CatalogRow[];
  products: CatalogRow[];
  vehicleTypes: CatalogRow[];
  expenseCategories: CatalogRow[];
  clients: ClientRow[];
  vehicles: VehicleRow[];
  sales: SaleRow[];
  expenses: ExpenseRow[];
  roles: RoleRow[];
  users: UserRow[];
}

const PERMISSIONS: S["PermissionItem"][] = [
  { code: "dashboard", label: "Dashboard" },
  { code: "register_sale", label: "Registrar ventas" },
  { code: "edit_sale", label: "Editar ventas" },
  { code: "manage_sales", label: "Anular ventas" },
  { code: "register_expense", label: "Registrar egresos" },
  { code: "movements", label: "Ver movimientos" },
  { code: "export", label: "Reportes y exportación" },
  { code: "settings", label: "Ajustes" },
];

// ---------------------------------------------------------------------------
// Semilla
// ---------------------------------------------------------------------------

/** PRNG determinístico (mulberry32): la demo se ve igual en cada visita del día. */
function prng(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function iso(d: Date) {
  return format(d, "yyyy-MM-dd");
}

function todayISO() {
  return iso(new Date());
}

function seed(): DemoDb {
  const rnd = prng(20261113);
  const pick = <T,>(arr: readonly T[]) => arr[Math.floor(rnd() * arr.length)];
  const weighted = <T,>(pairs: readonly (readonly [T, number])[]) => {
    const total = pairs.reduce((a, [, w]) => a + w, 0);
    let r = rnd() * total;
    for (const [v, w] of pairs) {
      r -= w;
      if (r <= 0) return v;
    }
    return pairs[pairs.length - 1][0];
  };

  let seq = 1;
  const nextId = () => seq++;
  const now = new Date();
  const created = now.toISOString();

  const cat = (name: string, price?: number): CatalogRow => ({
    id: nextId(),
    name,
    price: price ?? null,
    is_active: true,
    created_at: created,
  });

  const services = [
    cat("Lavado básico", 35000),
    cat("Lavado completo", 50000),
    cat("Lavado premium", 80000),
    cat("Aspirado", 15000),
    cat("Encerado", 70000),
    cat("Lavado de motor", 60000),
    cat("Limpieza de tapizado", 120000),
  ];
  const products = [
    cat("Aromatizante", 12000),
    cat("Cera líquida", 25000),
    cat("Limpiavidrios", 20000),
    cat("Paño de microfibra", 18000),
    cat("Shampoo automotor", 35000),
    cat("Silicona para tablero", 22000),
  ];
  const vehicleTypes = ["Auto", "Camioneta", "SUV", "Moto", "Camión pequeño"].map((n) => cat(n));
  const expenseCategories = [
    "Insumos",
    "Sueldos",
    "Servicios básicos",
    "Alquiler",
    "Mantenimiento",
    "Otros",
  ].map((n) => cat(n));

  const client = (
    name: string,
    client_type: ClientRow["client_type"],
    ruc_ci: string | null,
  ): ClientRow => ({ id: nextId(), name, client_type, ruc_ci, is_active: true, created_at: created });

  const generic = client("Sin nombre", "Generico", null);
  const companies = [
    client("AutoFlota S.A.", "Empresa", "80012345-6"),
    client("Transportes del Sur S.R.L.", "Empresa", "80055544-3"),
    client("Distribuidora Norte S.A.", "Empresa", "80099887-1"),
  ];
  const people = [
    client("Juan Pérez", "Particular", "4567890"),
    client("María González", "Particular", "3214567"),
  ];
  const clients = [generic, ...companies, ...people];

  // Placas formato Mercosur Paraguay (4 letras + 3 números).
  const letters = "ABCDEFGHJKLMNPRSTUVWXYZ";
  const plate = () =>
    `${Array.from({ length: 4 }, () => pick(letters.split(""))).join("")}${Math.floor(100 + rnd() * 900)}`;
  const vtAuto = vehicleTypes[0].id;
  const vehicles: VehicleRow[] = Array.from({ length: 34 }, (_, i) => {
    const typeId = weighted([
      [vtAuto, 50],
      [vehicleTypes[1].id, 20],
      [vehicleTypes[2].id, 18],
      [vehicleTypes[3].id, 6],
      [vehicleTypes[4].id, 6],
    ] as const);
    // Las primeras placas pertenecen a las empresas (flota).
    const owner = i < 6 ? companies[i % 3].id : i < 8 ? people[i - 6].id : null;
    return {
      id: nextId(),
      license_plate: plate(),
      vehicle_type_id: typeId,
      client_id: owner,
      is_active: true,
      created_at: created,
    };
  });

  const roles: RoleRow[] = [
    { id: nextId(), name: "Administrador", is_active: true, permissions: PERMISSIONS.map((p) => p.code) },
    {
      id: nextId(),
      name: "Cajero",
      is_active: true,
      permissions: ["register_sale", "movements", "register_expense"],
    },
  ];
  const users: UserRow[] = [
    { id: nextId(), username: "admin", role_id: roles[0].id, is_active: true, created_at: created },
    { id: nextId(), username: "cajero", role_id: roles[1].id, is_active: true, created_at: created },
  ];

  // --- Ventas: últimos 62 días (cubre "este mes" y el mes anterior) ---
  const sales: SaleRow[] = [];
  const DAYS = 62;
  const mainService = [
    [services[0], 34],
    [services[1], 30],
    [services[2], 14],
    [services[4], 6],
    [services[5], 6],
    [services[6], 5],
    [services[3], 5],
  ] as const;
  const methods = [
    ["Efectivo", 55],
    ["Transferencia", 20],
    ["Tarjeta", 15],
    ["QR", 10],
  ] as const;
  const notes = ["Cliente pidió cera extra", "Dejar el auto en la sombra", "Retira a la tarde", null];

  for (let back = DAYS; back >= 0; back--) {
    const day = addDays(now, -back);
    const dow = day.getDay(); // 0 = domingo
    if (dow === 0 && rnd() < 0.7) continue; // domingos casi siempre cerrado
    const base = dow === 6 ? 13 : dow === 5 ? 11 : 8;
    const count = Math.max(2, Math.round(base + (rnd() - 0.5) * 6));
    for (let k = 0; k < count; k++) {
      const items: SaleItemRow[] = [];
      const productOnly = rnd() < 0.08;
      const fleet = !productOnly && rnd() < 0.14;
      if (!productOnly) {
        const svc = weighted(mainService);
        items.push({ id: nextId(), kind: "service", ref_id: svc.id, name: svc.name, quantity: 1, unit_price: svc.price ?? 0 });
        if (svc !== services[3] && rnd() < 0.28) {
          const asp = services[3];
          items.push({ id: nextId(), kind: "service", ref_id: asp.id, name: asp.name, quantity: 1, unit_price: asp.price ?? 0 });
        }
      }
      if (productOnly || rnd() < 0.18) {
        const prod = pick(products);
        items.push({
          id: nextId(),
          kind: "product",
          ref_id: prod.id,
          name: prod.name,
          quantity: rnd() < 0.2 ? 2 : 1,
          unit_price: prod.price ?? 0,
        });
      }
      let customerId = generic.id;
      let vehicleId: number | null = null;
      let invoice = false;
      if (fleet) {
        const company = pick(companies);
        customerId = company.id;
        invoice = true;
        const fleetCars = vehicles.filter((v) => v.client_id === company.id);
        vehicleId = pick(fleetCars).id;
      } else if (!productOnly) {
        // Algunos clientes vuelven (recurrentes): sesgamos hacia las primeras placas.
        const idx = Math.floor(Math.pow(rnd(), 1.6) * vehicles.length);
        vehicleId = vehicles[idx].id;
        const owner = vehicles[idx].client_id;
        if (owner && people.some((p) => p.id === owner) && rnd() < 0.5) {
          customerId = owner;
          invoice = true;
        }
      }
      const credit = fleet && rnd() < 0.45;
      const hour = 8 + Math.floor(rnd() * 10);
      const createdAt = new Date(day);
      createdAt.setHours(hour, Math.floor(rnd() * 60), 0, 0);
      sales.push({
        id: nextId(),
        date: iso(day),
        created_at: createdAt.toISOString(),
        payment_type: credit ? "Credito" : "Contado",
        payment_method: credit ? null : weighted(methods),
        requires_invoice: invoice,
        notes: rnd() < 0.06 ? pick(notes) : null,
        is_voided: rnd() < 0.015,
        customer_id: customerId,
        vehicle_id: vehicleId,
        user_id: rnd() < 0.7 ? users[1].id : users[0].id,
        items,
      });
    }
  }

  // --- Egresos ---
  const expenses: ExpenseRow[] = [];
  const catId = (name: string) => expenseCategories.find((c) => c.name === name)?.id ?? expenseCategories[0].id;
  const addExpense = (d: Date, cat: string, amount: number, description: string) =>
    expenses.push({
      id: nextId(),
      date: iso(d),
      category_id: catId(cat),
      amount: Math.round(amount / 1000) * 1000,
      description,
      is_voided: false,
      user_id: users[0].id,
    });
  for (let back = DAYS; back >= 0; back--) {
    const d = addDays(now, -back);
    const dom = d.getDate();
    if (dom === 5) addExpense(d, "Alquiler", 2500000, "Alquiler del local");
    if (dom === 15 || dom === 30) addExpense(d, "Sueldos", 2800000, "Quincena del personal");
    if (dom === 10) addExpense(d, "Servicios básicos", 380000 + rnd() * 120000, "ANDE y ESSAP");
    if (d.getDay() === 1) addExpense(d, "Insumos", 320000 + rnd() * 280000, "Shampoo, cera y paños");
    if (rnd() < 0.05) addExpense(d, "Mantenimiento", 150000 + rnd() * 350000, "Repuesto de hidrolavadora");
    if (rnd() < 0.04) addExpense(d, "Otros", 40000 + rnd() * 90000, "Gastos varios");
  }

  return {
    version: 1,
    seededOn: todayISO(),
    seq,
    services,
    products,
    vehicleTypes,
    expenseCategories,
    clients,
    vehicles,
    sales,
    expenses,
    roles,
    users,
  };
}

// ---------------------------------------------------------------------------
// Persistencia
// ---------------------------------------------------------------------------

let cache: DemoDb | null = null;

function load(): DemoDb {
  if (cache && cache.seededOn === todayISO()) return cache;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as DemoDb;
      if (parsed.version === 1 && parsed.seededOn === todayISO()) {
        cache = parsed;
        return parsed;
      }
    }
  } catch {
    /* storage bloqueado o corrupto: regeneramos */
  }
  cache = seed();
  save();
  return cache;
}

function save() {
  try {
    if (cache) window.localStorage.setItem(STORAGE_KEY, JSON.stringify(cache));
  } catch {
    /* sin storage la demo sigue funcionando en memoria */
  }
}

/** Borra lo cargado por el visitante y vuelve a los datos de ejemplo. */
export function resetDemo() {
  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    /* noop */
  }
  cache = null;
}

// ---------------------------------------------------------------------------
// Serializadores (fila interna -> forma de la API)
// ---------------------------------------------------------------------------

function toSale(db: DemoDb, s: SaleRow): S["SaleResponse"] {
  const customer = db.clients.find((c) => c.id === s.customer_id);
  const vehicle = s.vehicle_id ? db.vehicles.find((v) => v.id === s.vehicle_id) : undefined;
  const vtype = vehicle ? db.vehicleTypes.find((t) => t.id === vehicle.vehicle_type_id) : undefined;
  const user = db.users.find((u) => u.id === s.user_id);
  const items = s.items.map((it) => ({
    id: it.id,
    item_type: it.kind === "service" ? "Servicio" : "Producto",
    item_name: it.name,
    service_id: it.kind === "service" ? it.ref_id : null,
    product_id: it.kind === "product" ? it.ref_id : null,
    quantity: it.quantity,
    unit_price: it.unit_price,
    subtotal: it.quantity * it.unit_price,
  }));
  return {
    id: s.id,
    date: s.date,
    created_at: s.created_at,
    payment_type: s.payment_type,
    payment_method: s.payment_method,
    requires_invoice: s.requires_invoice,
    total: items.reduce((a, i) => a + i.subtotal, 0),
    notes: s.notes,
    is_voided: s.is_voided,
    customer_id: s.customer_id,
    customer_name: customer?.name ?? "Sin nombre",
    ruc_ci: customer?.ruc_ci ?? null,
    vehicle_id: vehicle?.id ?? null,
    license_plate: vehicle?.license_plate ?? null,
    vehicle_type_id: vehicle?.vehicle_type_id ?? null,
    vehicle_type_name: vtype?.name ?? null,
    created_by_user_id: s.user_id,
    created_by: user?.username ?? "admin",
    lavanderia_id: TENANT_ID,
    items,
  };
}

function toCatalog(row: CatalogRow) {
  return { ...row, lavanderia_id: TENANT_ID };
}

function toVehicle(db: DemoDb, v: VehicleRow): S["VehicleResponse"] {
  const owner = v.client_id ? db.clients.find((c) => c.id === v.client_id) : undefined;
  return {
    id: v.id,
    license_plate: v.license_plate,
    vehicle_type_id: v.vehicle_type_id,
    vehicle_type_name: db.vehicleTypes.find((t) => t.id === v.vehicle_type_id)?.name ?? null,
    owner_name: owner?.name ?? null,
    phone: null,
    client_id: v.client_id,
    is_active: v.is_active,
    created_at: v.created_at,
    lavanderia_id: TENANT_ID,
  };
}

// ---------------------------------------------------------------------------
// Reportes
// ---------------------------------------------------------------------------

function inRange(date: string, start: string, end: string) {
  return date >= start && date <= end;
}

function saleTotal(s: SaleRow) {
  return s.items.reduce((a, i) => a + i.quantity * i.unit_price, 0);
}

function salesSummary(db: DemoDb, start: string, end: string): S["SalesSummaryResponse"] {
  const sales = db.sales.filter((s) => !s.is_voided && inRange(s.date, start, end));
  const expenses = db.expenses.filter((e) => !e.is_voided && inRange(e.date, start, end));
  const byItem = new Map<string, { count: number; total: number }>();
  let serviceCount = 0;
  let serviceTotal = 0;
  let productCount = 0;
  let contado = 0;
  let credito = 0;
  for (const s of sales) {
    const t = saleTotal(s);
    if (s.payment_type === "Credito") credito += t;
    else contado += t;
    for (const it of s.items) {
      const sub = it.quantity * it.unit_price;
      const cur = byItem.get(it.name) ?? { count: 0, total: 0 };
      cur.count += it.quantity;
      cur.total += sub;
      byItem.set(it.name, cur);
      if (it.kind === "service") {
        serviceCount += it.quantity;
        serviceTotal += sub;
      } else {
        productCount += it.quantity;
      }
    }
  }
  const byCat = new Map<string, number>();
  for (const e of expenses) {
    const name = db.expenseCategories.find((c) => c.id === e.category_id)?.name ?? "Otros";
    byCat.set(name, (byCat.get(name) ?? 0) + e.amount);
  }
  const salesTotal = contado + credito;
  const expenseTotal = expenses.reduce((a, e) => a + e.amount, 0);
  return {
    start_date: start,
    end_date: end,
    sales_total: salesTotal,
    expense_total: expenseTotal,
    net_balance: salesTotal - expenseTotal,
    service_count: serviceCount,
    service_sales_total: serviceTotal,
    product_count: productCount,
    sales_breakdown: [...byItem.entries()]
      .map(([name, v]) => ({ name, count: v.count, total: v.total }))
      .sort((a, b) => b.total - a.total),
    expense_breakdown: [...byCat.entries()]
      .map(([name, total]) => ({ name, count: null, total }))
      .sort((a, b) => b.total - a.total),
    payment_breakdown: { contado, credito },
  };
}

function dailySales(db: DemoDb, start: string, end: string): S["DailySalesItem"][] {
  const byDay = new Map<string, number>();
  for (const s of db.sales) {
    if (s.is_voided || !inRange(s.date, start, end)) continue;
    byDay.set(s.date, (byDay.get(s.date) ?? 0) + saleTotal(s));
  }
  return [...byDay.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([date, total]) => ({ date, total }));
}

function customerSummary(db: DemoDb, start: string, end: string): S["CustomerSummaryResponse"] {
  const visits = new Map<number, number>();
  for (const s of db.sales) {
    if (s.is_voided || !s.vehicle_id || !inRange(s.date, start, end)) continue;
    visits.set(s.vehicle_id, (visits.get(s.vehicle_id) ?? 0) + 1);
  }
  const seenBefore = new Set(
    db.sales.filter((s) => !s.is_voided && s.vehicle_id && s.date < start).map((s) => s.vehicle_id),
  );
  const recurring = [...visits.keys()].filter((id) => seenBefore.has(id)).length;
  const top = [...visits.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([id, count]) => {
      const v = db.vehicles.find((x) => x.id === id);
      const vr = v ? toVehicle(db, v) : undefined;
      return {
        license_plate: vr?.license_plate ?? null,
        vehicle_type: vr?.vehicle_type_name ?? null,
        owner_name: vr?.owner_name ?? null,
        visit_count: count,
      };
    });
  return {
    unique_vehicles: visits.size,
    recurring_customers: recurring,
    new_customers: visits.size - recurring,
    top_plates: top,
  };
}

function productSummary(db: DemoDb, start: string, end: string): S["ProductSummaryResponse"] {
  const byName = new Map<string, { count: number; total: number }>();
  for (const s of db.sales) {
    if (s.is_voided || !inRange(s.date, start, end)) continue;
    for (const it of s.items) {
      if (it.kind !== "product") continue;
      const cur = byName.get(it.name) ?? { count: 0, total: 0 };
      cur.count += it.quantity;
      cur.total += it.quantity * it.unit_price;
      byName.set(it.name, cur);
    }
  }
  const top = [...byName.entries()]
    .map(([name, v]) => ({ name, sale_count: v.count, total: v.total }))
    .sort((a, b) => b.total - a.total);
  return { total_sales: top.reduce((a, p) => a + p.sale_count, 0), top_products: top };
}

// ---------------------------------------------------------------------------
// Escrituras de ventas
// ---------------------------------------------------------------------------

class HttpError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

function applySalePayload(db: DemoDb, body: S["SaleCreateRequest"], target: SaleRow) {
  const items: SaleItemRow[] = body.items.map((it) => {
    const isService = it.servicio_id != null;
    const source = isService
      ? db.services.find((x) => x.id === it.servicio_id)
      : db.products.find((x) => x.id === it.producto_id);
    if (!source) throw new HttpError(400, "Ítem inexistente en el catálogo.");
    return {
      id: db.seq++,
      kind: isService ? "service" : "product",
      ref_id: source.id,
      name: source.name,
      quantity: it.cantidad,
      unit_price: it.precio_unitario ?? source.price ?? 0,
    };
  });
  const hasService = items.some((i) => i.kind === "service");
  if (hasService && !body.vehiculo_id) {
    throw new HttpError(400, "La venta incluye un servicio: el vehículo es obligatorio.");
  }
  let customerId = db.clients.find((c) => c.client_type === "Generico")?.id ?? 0;
  if (body.requiere_factura) {
    const ruc = (body.ruc_ci ?? "").trim();
    const name = (body.razon_social ?? "").trim();
    let c = db.clients.find((x) => x.ruc_ci === ruc);
    if (!c) {
      c = {
        id: db.seq++,
        name,
        client_type: ruc.includes("-") ? "Empresa" : "Particular",
        ruc_ci: ruc,
        is_active: true,
        created_at: new Date().toISOString(),
      };
      db.clients.push(c);
    } else if (name) {
      c.name = name;
    }
    customerId = c.id;
  }
  target.date = body.fecha_venta;
  target.payment_type = body.tipo_cobro === "Credito" ? "Credito" : "Contado";
  target.payment_method = target.payment_type === "Credito" ? null : (body.metodo_pago ?? null);
  target.requires_invoice = body.requiere_factura;
  target.notes = body.observacion ?? null;
  target.customer_id = customerId;
  target.vehicle_id = hasService ? (body.vehiculo_id ?? null) : null;
  target.items = items;
}

// ---------------------------------------------------------------------------
// Router
// ---------------------------------------------------------------------------

type Json = unknown;

const CATALOG_KEYS = {
  services: "services",
  products: "products",
  "vehicle-types": "vehicleTypes",
  "expense-categories": "expenseCategories",
} as const;

function handle(method: string, path: string, query: URLSearchParams, body: Json): [number, Json] {
  const db = load();
  const seg = path.split("/").filter(Boolean).map(decodeURIComponent);
  const id = (i: number) => Number(seg[i]);
  const range = () => [query.get("start_date") ?? todayISO(), query.get("end_date") ?? todayISO()] as const;

  // --- auth ---
  if (method === "POST" && path === "/auth/login") {
    const b = body as S["LoginRequest"];
    const user = db.users.find((u) => u.username === b.username.trim() && u.is_active);
    if (!user) throw new HttpError(401, "Usuario o contraseña incorrectos.");
    const role = db.roles.find((r) => r.id === user.role_id);
    const expires = addDays(new Date(), 7).toISOString();
    return [
      200,
      {
        user: {
          id: user.id,
          username: user.username,
          role: role?.name ?? null,
          lavanderia_id: TENANT_ID,
          lavanderia_name: TENANT_NAME,
        },
        tenant: {
          id: TENANT_ID,
          name: TENANT_NAME,
          subdominio: "demo",
          logo_url: null,
          logo_url_dark: null,
          color_primario: null,
          color_secundario: null,
          mostrar_marca_mukusoft: true,
        },
        permissions: role?.is_active ? role.permissions : [],
        access_token: `demo-${user.id}`,
        token_type: "bearer",
        expires_at: expires,
      } satisfies S["LoginResponse"],
    ];
  }

  // --- catálogos ---
  if (seg[0] === "catalogs" && seg[1] in CATALOG_KEYS) {
    const key = CATALOG_KEYS[seg[1] as keyof typeof CATALOG_KEYS];
    const rows = db[key];
    if (method === "GET" && seg.length === 2) {
      const onlyActive = query.get("only_active") === "true";
      return [200, rows.filter((r) => !onlyActive || r.is_active).map(toCatalog)];
    }
    if (method === "POST" && seg.length === 2) {
      const b = body as S["CatalogMutationRequest"];
      if (rows.some((r) => r.name.toLowerCase() === b.name.trim().toLowerCase())) {
        throw new HttpError(409, "Ya existe un ítem con ese nombre.");
      }
      const row: CatalogRow = {
        id: db.seq++,
        name: b.name.trim(),
        price: b.price ?? null,
        is_active: true,
        created_at: new Date().toISOString(),
      };
      rows.push(row);
      save();
      return [201, { id: row.id }];
    }
    const row = rows.find((r) => r.id === id(2));
    if (!row) throw new HttpError(404, "No encontrado.");
    if (method === "PUT" && seg.length === 3) {
      const b = body as S["CatalogMutationRequest"];
      row.name = b.name.trim();
      if (b.price !== undefined) row.price = b.price;
      save();
      return [200, { message: "Actualizado" }];
    }
    if (method === "PATCH" && seg[3] === "status") {
      row.is_active = !row.is_active;
      save();
      return [200, { message: row.is_active ? "Activado" : "Desactivado" }];
    }
    if (method === "DELETE" && seg.length === 3) {
      const used =
        (key === "services" || key === "products") &&
        db.sales.some((s) => s.items.some((it) => it.ref_id === row.id));
      if (used) {
        throw new HttpError(409, "Tiene ventas asociadas. Desactivalo en lugar de eliminarlo.");
      }
      db[key] = rows.filter((r) => r.id !== row.id);
      save();
      return [200, { message: "Eliminado" }];
    }
  }

  // --- ventas ---
  if (seg[0] === "sales") {
    if (method === "GET" && seg[1] === "grouped") {
      const [start, end] = range();
      const list = db.sales
        .filter((s) => !s.is_voided && inRange(s.date, start, end))
        .sort((a, b) => b.date.localeCompare(a.date) || b.id - a.id)
        .map((s) => toSale(db, s));
      return [200, list];
    }
    if (method === "POST" && seg.length === 1) {
      const sale: SaleRow = {
        id: db.seq++,
        date: todayISO(),
        created_at: new Date().toISOString(),
        payment_type: "Contado",
        payment_method: null,
        requires_invoice: false,
        notes: null,
        is_voided: false,
        customer_id: 0,
        vehicle_id: null,
        user_id: db.users[0].id,
        items: [],
      };
      applySalePayload(db, body as S["SaleCreateRequest"], sale);
      db.sales.push(sale);
      save();
      return [201, { id: sale.id }];
    }
    const sale = db.sales.find((s) => s.id === id(1));
    if (!sale) throw new HttpError(404, "Venta no encontrada.");
    if (method === "GET") return [200, toSale(db, sale)];
    if (method === "PUT") {
      applySalePayload(db, body as S["SaleCreateRequest"], sale);
      save();
      return [200, toSale(db, sale)];
    }
    if (method === "DELETE") {
      sale.is_voided = true;
      save();
      return [200, { message: "Venta anulada" }];
    }
  }

  // --- egresos ---
  if (seg[0] === "expenses" && method === "POST") {
    const b = body as S["ExpenseCreateRequest"];
    if (!(b.monto > 0)) throw new HttpError(400, "El monto debe ser mayor a cero.");
    const row: ExpenseRow = {
      id: db.seq++,
      date: b.fecha,
      category_id: b.categoria_egreso_id,
      amount: b.monto,
      description: b.descripcion ?? null,
      is_voided: false,
      user_id: db.users[0].id,
    };
    db.expenses.push(row);
    save();
    return [201, { id: row.id }];
  }

  // --- vehículos y clientes ---
  if (seg[0] === "vehicles") {
    if (method === "GET" && seg[1] === "by-plate") {
      const plate = seg[2].replace(/\s+/g, "").toUpperCase();
      const v = db.vehicles.find((x) => x.license_plate === plate);
      return [200, v ? toVehicle(db, v) : null];
    }
    if (method === "POST" && seg.length === 1) {
      const b = body as S["VehicleCreateRequest"];
      const plate = b.license_plate.replace(/\s+/g, "").toUpperCase();
      let v = db.vehicles.find((x) => x.license_plate === plate);
      if (v) {
        v.vehicle_type_id = b.vehicle_type_id;
      } else {
        v = {
          id: db.seq++,
          license_plate: plate,
          vehicle_type_id: b.vehicle_type_id,
          client_id: null,
          is_active: true,
          created_at: new Date().toISOString(),
        };
        db.vehicles.push(v);
      }
      save();
      return [201, { id: v.id }];
    }
  }
  if (seg[0] === "clients" && seg[1] === "by-ruc-ci" && method === "GET") {
    const c = db.clients.find((x) => x.ruc_ci === seg[2]);
    return [200, c ? { ...c, phone: null, email: null, lavanderia_id: TENANT_ID } : null];
  }

  // --- reportes ---
  if (seg[0] === "reports" && method === "GET") {
    const [start, end] = range();
    if (seg[1] === "sales-summary") return [200, salesSummary(db, start, end)];
    if (seg[1] === "daily-sales") return [200, dailySales(db, start, end)];
    if (seg[1] === "customer-summary") return [200, customerSummary(db, start, end)];
    if (seg[1] === "product-summary") return [200, productSummary(db, start, end)];
  }

  // --- permisos, roles, usuarios ---
  if (path === "/permissions" && method === "GET") return [200, PERMISSIONS];

  if (seg[0] === "roles") {
    if (method === "GET" && seg.length === 1) {
      return [
        200,
        db.roles.map((r) => ({
          id: r.id,
          name: r.name,
          is_active: r.is_active,
          permission_count: r.permissions.length,
        })),
      ];
    }
    if (method === "POST" && seg.length === 1) {
      const b = body as S["RoleCreateRequest"];
      const role: RoleRow = { id: db.seq++, name: b.name.trim(), is_active: true, permissions: [] };
      db.roles.push(role);
      save();
      return [201, { id: role.id }];
    }
    const role = db.roles.find((r) => r.id === id(1));
    if (!role) throw new HttpError(404, "Rol no encontrado.");
    if (seg[2] === "permissions") {
      if (method === "GET") return [200, role.permissions];
      if (method === "PUT") {
        const next = (body as S["RolePermissionsRequest"]).permissions ?? [];
        if (role.name === "Administrador" && !next.includes("settings")) {
          throw new HttpError(400, "El tenant quedaría sin administradores.");
        }
        role.permissions = next;
        save();
        return [200, { message: "Permisos actualizados" }];
      }
    }
    if (seg[2] === "status" && method === "PATCH") {
      if (role.name === "Administrador") {
        throw new HttpError(400, "No se puede desactivar el rol de administrador.");
      }
      role.is_active = !role.is_active;
      save();
      return [200, { message: "Estado actualizado" }];
    }
    if (method === "PUT" && seg.length === 2) {
      role.name = (body as { name: string }).name.trim();
      save();
      return [200, { message: "Rol actualizado" }];
    }
  }

  if (seg[0] === "users") {
    if (method === "GET" && seg.length === 1) {
      return [
        200,
        db.users.map((u) => ({
          id: u.id,
          username: u.username,
          role: db.roles.find((r) => r.id === u.role_id)?.name ?? null,
          role_id: u.role_id,
          is_active: u.is_active,
          created_at: u.created_at,
        })),
      ];
    }
    if (method === "POST" && seg.length === 1) {
      const b = body as S["UserCreateRequest"];
      if (db.users.some((u) => u.username === b.username.trim())) {
        throw new HttpError(409, "Ya existe un usuario con ese nombre.");
      }
      const user: UserRow = {
        id: db.seq++,
        username: b.username.trim(),
        role_id: b.role_id,
        is_active: true,
        created_at: new Date().toISOString(),
      };
      db.users.push(user);
      save();
      return [201, { id: user.id }];
    }
    const user = db.users.find((u) => u.id === id(1));
    if (!user) throw new HttpError(404, "Usuario no encontrado.");
    if (seg[2] === "status" && method === "PATCH") {
      if (user.username === "admin") {
        throw new HttpError(400, "No se puede desactivar al último administrador.");
      }
      user.is_active = !user.is_active;
      save();
      return [200, { message: "Estado actualizado" }];
    }
    if (seg[2] === "password" && method === "PATCH") {
      return [200, { message: "Contraseña actualizada" }];
    }
    if (method === "PUT" && seg.length === 2) {
      const b = body as S["UserUpdateRequest"];
      user.username = b.username.trim();
      user.role_id = b.role_id;
      save();
      return [200, { message: "Usuario actualizado" }];
    }
  }

  throw new HttpError(404, "Esta función no está disponible en la demo.");
}

/**
 * Reemplazo de `fetch` para la demo: devuelve un `Response` real para que
 * `apiFetch` lo procese igual que una respuesta del servidor.
 */
export async function demoFetch(path: string, init: RequestInit): Promise<Response> {
  // Pequeña latencia para que los estados de carga se vean como en producción.
  await new Promise((r) => setTimeout(r, 120));
  const url = new URL(path, "http://demo.local");
  const method = (init.method ?? "GET").toUpperCase();
  const body = typeof init.body === "string" ? JSON.parse(init.body) : undefined;
  const headers = { "Content-Type": "application/json" };
  try {
    const [status, data] = handle(method, url.pathname, url.searchParams, body);
    return new Response(JSON.stringify(data), { status, headers });
  } catch (err) {
    const status = err instanceof HttpError ? err.status : 500;
    const detail = err instanceof Error ? err.message : "Error en la demo.";
    // 401 en login no debe disparar el "sesión expirada" de apiFetch.
    const safeStatus = status === 401 && url.pathname === "/auth/login" ? 400 : status;
    return new Response(JSON.stringify({ detail }), { status: safeStatus, headers });
  }
}
