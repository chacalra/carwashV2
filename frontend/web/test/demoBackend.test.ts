/**
 * Backend simulado de la demo pública (GitHub Pages).
 * Verifica que responda con las formas de la API real y que los reportes
 * sean coherentes con las ventas que devuelve.
 */

import { beforeEach, describe, expect, it } from "vitest";

import { demoFetch, resetDemo } from "@/lib/demo/backend";
import { todayISO } from "@/lib/format";

async function call<T>(method: string, path: string, body?: unknown): Promise<{ status: number; data: T }> {
  const res = await demoFetch(path, {
    method,
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  });
  return { status: res.status, data: (await res.json()) as T };
}

const monthStart = () => `${todayISO().slice(0, 8)}01`;

beforeEach(() => {
  resetDemo();
});

describe("demo backend", () => {
  it("login de admin devuelve todos los permisos y el tenant demo", async () => {
    const { status, data } = await call<{ permissions: string[]; tenant: { subdominio: string } }>(
      "POST",
      "/auth/login",
      { username: "admin", password: "x" },
    );
    expect(status).toBe(200);
    expect(data.permissions).toContain("settings");
    expect(data.tenant.subdominio).toBe("demo");
  });

  it("usuario inexistente falla sin disparar 'sesión expirada' (no 401)", async () => {
    const { status } = await call("POST", "/auth/login", { username: "nadie", password: "x" });
    expect(status).toBe(400);
  });

  it("el resumen del mes cuadra con contado + crédito y con los egresos", async () => {
    const q = `?start_date=${monthStart()}&end_date=${todayISO()}`;
    const { data: s } = await call<{
      sales_total: number;
      expense_total: number;
      net_balance: number;
      payment_breakdown: { contado: number; credito: number };
      sales_breakdown: { total: number }[];
    }>("GET", `/reports/sales-summary${q}`);
    expect(s.sales_total).toBeGreaterThan(0);
    expect(s.payment_breakdown.contado + s.payment_breakdown.credito).toBe(s.sales_total);
    expect(s.net_balance).toBe(s.sales_total - s.expense_total);
    expect(s.sales_breakdown.reduce((a, i) => a + i.total, 0)).toBe(s.sales_total);
  });

  it("una venta nueva aparece en movimientos y se puede anular", async () => {
    const { data: services } = await call<{ id: number; price: number }[]>(
      "GET",
      "/catalogs/services?only_active=true",
    );
    const { data: vehicle } = await call<{ id: number }>("POST", "/vehicles", {
      license_plate: "TEST123",
      vehicle_type_id: 1,
    });
    // vehicle_type_id 1 puede no existir como tipo; el upsert lo acepta igual.
    const { status, data: created } = await call<{ id: number }>("POST", "/sales", {
      fecha_venta: todayISO(),
      tipo_cobro: "Contado",
      metodo_pago: "Efectivo",
      requiere_factura: false,
      vehiculo_id: vehicle.id,
      items: [{ servicio_id: services[0].id, cantidad: 2, precio_unitario: 40000 }],
    });
    expect(status).toBe(201);

    const q = `?start_date=${todayISO()}&end_date=${todayISO()}`;
    const { data: list } = await call<{ id: number; total: number; license_plate: string }[]>(
      "GET",
      `/sales/grouped${q}`,
    );
    const mine = list.find((s) => s.id === created.id);
    expect(mine?.total).toBe(80000);
    expect(mine?.license_plate).toBe("TEST123");

    await call("DELETE", `/sales/${created.id}`);
    const { data: after } = await call<{ id: number }[]>("GET", `/sales/grouped${q}`);
    expect(after.some((s) => s.id === created.id)).toBe(false);
  });

  it("servicio sin vehículo se rechaza como en el backend real", async () => {
    const { data: services } = await call<{ id: number }[]>("GET", "/catalogs/services?only_active=true");
    const { status } = await call("POST", "/sales", {
      fecha_venta: todayISO(),
      tipo_cobro: "Contado",
      requiere_factura: false,
      items: [{ servicio_id: services[0].id, cantidad: 1 }],
    });
    expect(status).toBe(400);
  });
});
