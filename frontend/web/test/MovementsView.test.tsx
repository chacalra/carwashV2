/**
 * Tests de MovementsInner — filtros, búsqueda, anular.
 *
 * MSW intercepta GET /sales/grouped y DELETE /sales/{id}.
 * El auth store se siembra con permisos para no depender del Shell/AuthGuard.
 */

import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { screen, waitFor, within } from "@testing-library/react";

import { MovementsInner } from "@/components/sales/MovementsView";
import { useAuthStore } from "@/lib/auth/store";
import type { components } from "@/lib/api/schema";
import { API_BASE } from "./mocks/handlers";
import { server } from "./mocks/server";
import { renderWithProviders } from "./utils/renderWithProviders";

type SaleResponse = components["schemas"]["SaleResponse"];

function makeSale(overrides: Partial<SaleResponse>): SaleResponse {
  return {
    id: 1,
    date: "2026-05-09",
    created_at: "2026-05-09T12:00:00Z",
    payment_type: "Contado",
    payment_method: "Efectivo",
    requires_invoice: false,
    total: 50000,
    notes: null,
    is_voided: false,
    customer_id: 99,
    customer_name: "Cliente generico",
    ruc_ci: null,
    vehicle_id: null,
    license_plate: null,
    vehicle_type_id: null,
    vehicle_type_name: null,
    created_by_user_id: 1,
    created_by: "admin",
    lavanderia_id: 1,
    items: [
      {
        id: 1,
        item_type: "Servicio",
        item_name: "Lavado básico",
        service_id: 5,
        product_id: null,
        quantity: 1,
        unit_price: 50000,
        subtotal: 50000,
      },
    ],
    ...overrides,
  };
}

const FIXTURE: SaleResponse[] = [
  makeSale({
    id: 101,
    payment_type: "Contado",
    payment_method: "Efectivo",
    customer_name: "Juan Pérez",
    license_plate: "ABC123",
    vehicle_type_id: 1,
    vehicle_type_name: "Auto",
    total: 80000,
  }),
  makeSale({
    id: 102,
    payment_type: "Credito",
    payment_method: null,
    customer_name: "Empresa S.A.",
    ruc_ci: "80012345-6",
    requires_invoice: true,
    total: 250000,
  }),
  makeSale({
    id: 103,
    payment_type: "Contado",
    payment_method: "Tarjeta",
    customer_name: "María López",
    license_plate: "XYZ789",
    vehicle_type_id: 2,
    vehicle_type_name: "Camioneta",
    total: 120000,
  }),
  makeSale({
    id: 104,
    payment_type: "Contado",
    payment_method: "Transferencia",
    customer_name: "Distribuidora Norte SRL",
    ruc_ci: "80098765-1",
    requires_invoice: true,
    total: 175000,
  }),
];

beforeEach(() => {
  // Sembrar permisos para que aparezcan los botones de editar/anular.
  useAuthStore.setState({
    token: "fake",
    user: {
      id: 1,
      username: "admin",
      role: "admin",
      lavanderiaId: 1,
      lavanderiaName: "Demo",
    },
    permissions: ["movements", "edit_sale", "manage_sales"],
    expiresAt: null,
    hydrated: true,
  });

  server.use(
    http.get(`${API_BASE}/sales/grouped`, () => HttpResponse.json(FIXTURE)),
  );
});

afterEach(() => {
  useAuthStore.getState().logout();
  vi.restoreAllMocks();
});

describe("MovementsInner", () => {
  // En mobile el listado se renderiza como cards y en desktop como tabla.
  // happy-dom no aplica media queries → los dos están en el DOM, así que
  // chequeamos que cada nombre aparezca al menos una vez (>=1 instancia).
  it("renderiza las filas de ventas devueltas por la API", async () => {
    renderWithProviders(<MovementsInner />);

    expect((await screen.findAllByText("Juan Pérez")).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Empresa S.A.").length).toBeGreaterThan(0);
    expect(screen.getAllByText("María López").length).toBeGreaterThan(0);
  });

  it("muestra stats: 4 ventas, total 625.000", async () => {
    renderWithProviders(<MovementsInner />);

    await screen.findAllByText("Juan Pérez");

    // Total: 80000 + 250000 + 120000 + 175000 = 625000
    expect(screen.getByText("Gs. 625.000")).toBeInTheDocument();
  });

  it("filtra por tipo de cobro Crédito", async () => {
    const user = userEvent.setup();
    renderWithProviders(<MovementsInner />);

    await screen.findAllByText("Juan Pérez");

    await user.click(screen.getByRole("button", { name: "Crédito" }));

    expect(screen.getAllByText("Empresa S.A.").length).toBeGreaterThan(0);
    expect(screen.queryByText("Juan Pérez")).not.toBeInTheDocument();
    expect(screen.queryByText("María López")).not.toBeInTheDocument();
  });

  it("busca por placa", async () => {
    const user = userEvent.setup();
    renderWithProviders(<MovementsInner />);

    await screen.findAllByText("Juan Pérez");

    await user.type(
      screen.getByPlaceholderText("Cliente, RUC, placa…"),
      "XYZ789",
    );

    expect(screen.getAllByText("María López").length).toBeGreaterThan(0);
    expect(screen.queryByText("Juan Pérez")).not.toBeInTheDocument();
    expect(screen.queryByText("Empresa S.A.")).not.toBeInTheDocument();
  });

  it("muestra empty state cuando no hay coincidencias", async () => {
    const user = userEvent.setup();
    renderWithProviders(<MovementsInner />);

    await screen.findAllByText("Juan Pérez");

    await user.type(
      screen.getByPlaceholderText("Cliente, RUC, placa…"),
      "no-existe-nada",
    );

    expect(await screen.findByText("Sin coincidencias")).toBeInTheDocument();
  });

  // El popover (role="listbox") rendea los nombres en sus checkboxes, y el
  // trigger del filtro (button con haspopup) muestra el nombre cuando hay 1
  // seleccionada. Filtramos ambos para quedarnos solo con las apariciones en
  // la tabla/cards de resultados.
  function inResultsOnly(name: string): HTMLElement[] {
    return screen
      .queryAllByText(name)
      .filter((el) => !el.closest('[role="listbox"]'))
      .filter((el) => !el.closest('button[aria-haspopup="listbox"]'));
  }

  it("filtro razón social: incluir una empresa muestra solo sus ventas", async () => {
    const user = userEvent.setup();
    renderWithProviders(<MovementsInner />);

    await screen.findAllByText("Juan Pérez");

    // Abrir popover desde el trigger.
    await user.click(screen.getByRole("button", { name: /Todas/ }));

    // Seleccionar Empresa S.A.
    const empresaCheckbox = await screen.findByRole("checkbox", { name: /Empresa S\.A\./ });
    await user.click(empresaCheckbox);

    expect(inResultsOnly("Empresa S.A.").length).toBeGreaterThan(0);
    expect(inResultsOnly("Juan Pérez")).toHaveLength(0);
    expect(inResultsOnly("María López")).toHaveLength(0);
    expect(inResultsOnly("Distribuidora Norte SRL")).toHaveLength(0);
  });

  it("filtro razón social: excluir oculta solo las seleccionadas", async () => {
    const user = userEvent.setup();
    renderWithProviders(<MovementsInner />);

    await screen.findAllByText("Juan Pérez");

    await user.click(screen.getByRole("button", { name: /Todas/ }));
    await user.click(await screen.findByRole("checkbox", { name: /Empresa S\.A\./ }));
    await user.click(screen.getByRole("checkbox", { name: /Excluir seleccionadas/ }));

    expect(inResultsOnly("Empresa S.A.")).toHaveLength(0);
    expect(inResultsOnly("Juan Pérez").length).toBeGreaterThan(0);
    expect(inResultsOnly("Distribuidora Norte SRL").length).toBeGreaterThan(0);
  });

  it("filtro razón social: opciones solo incluyen ventas con factura", async () => {
    const user = userEvent.setup();
    renderWithProviders(<MovementsInner />);

    await screen.findAllByText("Juan Pérez");

    await user.click(screen.getByRole("button", { name: /Todas/ }));

    // Solo aparecen las facturadas (Empresa S.A. y Distribuidora). Juan y María
    // no facturaron en el fixture, así que NO deben estar como opción.
    expect(await screen.findByRole("checkbox", { name: /Empresa S\.A\./ })).toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: /Distribuidora Norte SRL/ })).toBeInTheDocument();
    expect(screen.queryByRole("checkbox", { name: /Juan Pérez/ })).not.toBeInTheDocument();
  });

  it("filtros activos se muestran como chips removibles individuales", async () => {
    const user = userEvent.setup();
    renderWithProviders(<MovementsInner />);

    await screen.findAllByText("Juan Pérez");

    // Activar tipo de cobro Crédito + búsqueda + razón social.
    await user.click(screen.getByRole("button", { name: "Crédito" }));
    await user.type(screen.getByPlaceholderText("Cliente, RUC, placa…"), "abc");
    await user.click(screen.getByRole("button", { name: /Todas/ }));
    await user.click(await screen.findByRole("checkbox", { name: /Empresa S\.A\./ }));

    // Cada filtro tiene su propio chip removible.
    expect(screen.getByLabelText('Quitar filtro Credito')).toBeInTheDocument();
    expect(screen.getByLabelText('Quitar filtro "abc"')).toBeInTheDocument();
    expect(screen.getByLabelText("Quitar filtro Empresa S.A.")).toBeInTheDocument();

    // Quitar solo el de búsqueda no afecta a los otros.
    await user.click(screen.getByLabelText('Quitar filtro "abc"'));
    expect(screen.queryByLabelText('Quitar filtro "abc"')).not.toBeInTheDocument();
    expect(screen.getByLabelText("Quitar filtro Credito")).toBeInTheDocument();
  });

  it("colapsa columna Cliente cuando todas las filas son del mismo cliente", async () => {
    const user = userEvent.setup();
    renderWithProviders(<MovementsInner />);

    await screen.findAllByText("Juan Pérez");

    // Sin filtro: la columna Cliente está visible en el thead.
    expect(screen.getByRole("columnheader", { name: "Cliente" })).toBeInTheDocument();

    // Filtro razón social = Empresa S.A. (queda 1 sola venta, mismo cliente).
    await user.click(screen.getByRole("button", { name: /Todas/ }));
    await user.click(await screen.findByRole("checkbox", { name: /Empresa S\.A\./ }));

    // La columna desaparece del header.
    await waitFor(() => {
      expect(screen.queryByRole("columnheader", { name: "Cliente" })).not.toBeInTheDocument();
    });

    // Aparece el banner del cliente único con su RUC.
    expect(screen.getAllByText("Empresa S.A.").length).toBeGreaterThan(0);
    expect(screen.getByText(/80012345-6/)).toBeInTheDocument();
  });

  it("breakdown por razón social aparece cuando hay 2+ empresas seleccionadas", async () => {
    const user = userEvent.setup();
    renderWithProviders(<MovementsInner />);

    await screen.findAllByText("Juan Pérez");

    await user.click(screen.getByRole("button", { name: /Todas/ }));
    await user.click(await screen.findByRole("checkbox", { name: /Empresa S\.A\./ }));
    await user.click(screen.getByRole("checkbox", { name: /Distribuidora Norte SRL/ }));

    // Sección de breakdown visible.
    expect(screen.getByText("Por razón social")).toBeInTheDocument();
    // El monto por empresa puede aparecer en el breakdown y en la fila;
    // alcanza con que esté presente al menos una vez (en el breakdown).
    expect(screen.getAllByText("Gs. 250.000").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Gs. 175.000").length).toBeGreaterThan(0);
  });

  it("colapsa columna Items cuando todas las filas tienen exactamente los mismos items", async () => {
    renderWithProviders(<MovementsInner />);

    await screen.findAllByText("Juan Pérez");

    // El fixture tiene 4 ventas con el mismo item ("Lavado básico" qty 1).
    // Por eso la columna Items debe estar colapsada y aparecer en el banner.
    expect(screen.queryByRole("columnheader", { name: "Items" })).not.toBeInTheDocument();
    // El banner muestra el item común (puede aparecer también en cards mobile).
    expect(screen.getAllByText(/Lavado básico/).length).toBeGreaterThan(0);
  });

  it("anular abre dialog y confirma DELETE /sales/{id}", async () => {
    const user = userEvent.setup();
    let deletedId: string | null = null;

    server.use(
      http.delete(`${API_BASE}/sales/:id`, ({ params }) => {
        deletedId = params.id as string;
        return HttpResponse.json({ message: "Venta anulada." });
      }),
    );

    renderWithProviders(<MovementsInner />);

    await screen.findAllByText("Juan Pérez");

    // Tomamos la fila desktop (`tr`) — el botón ahí tiene aria-label "Anular".
    const tr = screen.getAllByText("Juan Pérez").map((n) => n.closest("tr")).find(Boolean);
    expect(tr).not.toBeNull();
    const voidBtn = within(tr as HTMLElement).getByLabelText("Anular");
    await user.click(voidBtn);

    // El dialog se abre. Confirmamos la acción.
    const confirmBtn = await screen.findByRole("button", { name: /^Anular$/ });
    await user.click(confirmBtn);

    await waitFor(() => expect(deletedId).toBe("101"));
  });

  it("cancelar el dialog no dispara DELETE", async () => {
    const user = userEvent.setup();
    let called = false;

    server.use(
      http.delete(`${API_BASE}/sales/:id`, () => {
        called = true;
        return HttpResponse.json({ message: "Venta anulada." });
      }),
    );

    renderWithProviders(<MovementsInner />);

    await screen.findAllByText("Juan Pérez");

    const tr = screen.getAllByText("Juan Pérez").map((n) => n.closest("tr")).find(Boolean);
    const voidBtn = within(tr as HTMLElement).getByLabelText("Anular");
    await user.click(voidBtn);

    const cancelBtn = await screen.findByRole("button", { name: /Cancelar/ });
    await user.click(cancelBtn);

    await new Promise((r) => setTimeout(r, 30));
    expect(called).toBe(false);
  });

  it("oculta acción de anular si el usuario no tiene permission manage_sales", async () => {
    useAuthStore.setState({ permissions: ["movements"] });

    renderWithProviders(<MovementsInner />);

    await screen.findAllByText("Juan Pérez");

    expect(screen.queryByLabelText("Anular")).not.toBeInTheDocument();
  });
});
