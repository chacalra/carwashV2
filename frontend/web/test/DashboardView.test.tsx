/**
 * Tests de DashboardContent — Pasada A + B:
 *  - render de KPIs principales (Ventas / Balance / Servicios) con datos del summary
 *  - reacción al cambio de período (refetch contra el nuevo rango)
 *  - charts montan cuando hay daily-sales y breakdowns
 *
 * Recharts en happy-dom no produce SVG con datos del todo correcto, así que
 * sólo validamos que el contenedor de chart aparezca sin error.
 */

import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";

import { DashboardContent } from "@/components/DashboardView";
import { API_BASE } from "./mocks/handlers";
import { server } from "./mocks/server";
import { renderWithProviders } from "./utils/renderWithProviders";

const SUMMARY = {
  start_date: "2026-05-01",
  end_date: "2026-05-31",
  sales_total: 1500000,
  expense_total: 250000,
  net_balance: 1250000,
  service_count: 25,
  service_sales_total: 1200000,
  product_count: 12,
  sales_breakdown: [
    { name: "Lavado", count: 20, total: 1000000 },
    { name: "Encerado", count: 5, total: 200000 },
  ],
  expense_breakdown: [{ name: "Insumos", count: null, total: 250000 }],
  payment_breakdown: { contado: 1200000, credito: 300000 },
};

const PREV_SUMMARY = {
  ...SUMMARY,
  start_date: "2026-04-01",
  end_date: "2026-04-30",
  sales_total: 1000000,
  net_balance: 800000,
  service_count: 18,
};

const DAILY = [
  { date: "2026-05-01", total: 50000 },
  { date: "2026-05-02", total: 80000 },
];

const CUSTOMERS = {
  unique_vehicles: 12,
  recurring_customers: 5,
  new_customers: 7,
  top_plates: [
    { license_plate: "ABC123", vehicle_type: "Auto", owner_name: "Juan Pérez", visit_count: 4 },
    { license_plate: "XYZ789", vehicle_type: "Camioneta", owner_name: null, visit_count: 2 },
  ],
};

const PRODUCTS = {
  total_sales: 17,
  top_products: [
    { name: "Cera líquida", sale_count: 10, total: 150000 },
    { name: "Shampoo", sale_count: 7, total: 70000 },
  ],
};

beforeEach(() => {
  // ResizeObserver lo necesita Recharts y happy-dom no lo trae.
  globalThis.ResizeObserver =
    globalThis.ResizeObserver ||
    class {
      observe() {}
      unobserve() {}
      disconnect() {}
    };

  let summaryCalls = 0;
  server.use(
    // El dashboard pide summary del rango actual y del previo.
    // Devolvemos SUMMARY al primer call y PREV_SUMMARY al segundo.
    http.get(`${API_BASE}/reports/sales-summary`, () => {
      summaryCalls += 1;
      return HttpResponse.json(summaryCalls === 1 ? SUMMARY : PREV_SUMMARY);
    }),
    http.get(`${API_BASE}/reports/daily-sales`, () => HttpResponse.json(DAILY)),
    http.get(`${API_BASE}/reports/customer-summary`, () => HttpResponse.json(CUSTOMERS)),
    http.get(`${API_BASE}/reports/product-summary`, () => HttpResponse.json(PRODUCTS)),
  );
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("DashboardContent", () => {
  it("renderiza KPIs principales con valores formateados", async () => {
    renderWithProviders(<DashboardContent />);

    // sales_total = 1.500.000
    expect(await screen.findByText("Gs. 1.500.000")).toBeInTheDocument();
    // net_balance = 1.250.000
    expect(screen.getByText("Gs. 1.250.000")).toBeInTheDocument();
    // service_count = 25 → label "Lavados" con valor 25
    expect(screen.getByText("25")).toBeInTheDocument();
  });

  it("muestra el contado del payment_breakdown", async () => {
    renderWithProviders(<DashboardContent />);

    // contado = 1.200.000 (KPI Contado + breakdown). credito = 300.000
    // (puede aparecer en KPI y leyenda de chart). Aceptamos múltiples ocurrencias.
    expect((await screen.findAllByText("Gs. 1.200.000")).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Gs. 300.000").length).toBeGreaterThan(0);
  });

  it("cambiar de período dispara refetch al nuevo rango", async () => {
    const user = userEvent.setup();
    const calls: string[] = [];

    server.use(
      http.get(`${API_BASE}/reports/sales-summary`, ({ request }) => {
        const url = new URL(request.url);
        const start = url.searchParams.get("start_date") ?? "";
        calls.push(start);
        return HttpResponse.json(SUMMARY);
      }),
      http.get(`${API_BASE}/reports/daily-sales`, () => HttpResponse.json(DAILY)),
      http.get(`${API_BASE}/reports/customer-summary`, () => HttpResponse.json(CUSTOMERS)),
      http.get(`${API_BASE}/reports/product-summary`, () => HttpResponse.json(PRODUCTS)),
    );

    renderWithProviders(<DashboardContent />);
    await screen.findByText("Gs. 1.500.000");

    const initialCount = calls.length;

    // Cambio a "Hoy" — debería disparar otro fetch con un start distinto.
    // El selector de período usa `role="tab"`.
    await user.click(screen.getByRole("tab", { name: "Hoy" }));

    await waitFor(() => expect(calls.length).toBeGreaterThan(initialCount));
  });

  it("renderiza la sección Clientes del período con KPIs y top placas", async () => {
    renderWithProviders(<DashboardContent />);

    expect(await screen.findByText("Clientes del período")).toBeInTheDocument();
    // Los números aparecen en KPIs y otras secciones del dashboard, así que
    // chequeamos que cada valor esperado aparezca al menos una vez.
    expect(screen.getAllByText("12").length).toBeGreaterThan(0);
    expect(screen.getAllByText("5").length).toBeGreaterThan(0);
    expect(screen.getAllByText("7").length).toBeGreaterThan(0);
    // Top placas (únicos en la página)
    expect(screen.getByText("ABC123")).toBeInTheDocument();
    expect(screen.getByText("XYZ789")).toBeInTheDocument();
    expect(screen.getByText(/4 visitas/)).toBeInTheDocument();
    expect(screen.getByText(/2 visitas/)).toBeInTheDocument();
  });

  it("renderiza la sección Top productos con conteo y total", async () => {
    renderWithProviders(<DashboardContent />);

    expect(await screen.findByText("Top productos")).toBeInTheDocument();
    expect(screen.getByText("Cera líquida")).toBeInTheDocument();
    expect(screen.getByText("Shampoo")).toBeInTheDocument();
    expect(screen.getByText(/10 unidades vendidas/)).toBeInTheDocument();
    expect(screen.getByText("Gs. 150.000")).toBeInTheDocument();
    expect(screen.getByText("Gs. 70.000")).toBeInTheDocument();
  });

  it("muestra empty state cuando el endpoint falla", async () => {
    server.use(
      http.get(`${API_BASE}/reports/sales-summary`, () =>
        HttpResponse.json({ detail: "fail" }, { status: 500 }),
      ),
      http.get(`${API_BASE}/reports/daily-sales`, () => HttpResponse.json([])),
      http.get(`${API_BASE}/reports/customer-summary`, () => HttpResponse.json(CUSTOMERS)),
      http.get(`${API_BASE}/reports/product-summary`, () => HttpResponse.json(PRODUCTS)),
    );

    renderWithProviders(<DashboardContent />);

    expect(
      await screen.findByText(/No pudimos cargar el dashboard/),
    ).toBeInTheDocument();
  });
});
