/**
 * Tests de ExpensesNewView — flujo de Iter 6:
 *  - render del select de categorías desde GET /catalogs/expense-categories
 *  - submit dispara POST /expenses con payload mapeado
 *  - validación: monto > 0 y categoría requerida
 */

import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";

// Importamos el componente interno (sin Shell) para evitar el AuthGuard.
// Re-exporta el inner como default no es viable, así que renderizamos
// la export pública y stubbeamos la sesión via auth store si hace falta.
import { ExpensesNewView } from "@/components/expenses/ExpensesNewView";
import { useAuthStore } from "@/lib/auth/store";
import { API_BASE } from "./mocks/handlers";
import { server } from "./mocks/server";
import { renderWithProviders } from "./utils/renderWithProviders";

const CATEGORIES = [
  { id: 1, name: "Insumos", is_active: true, created_at: null, lavanderia_id: 1 },
  { id: 2, name: "Sueldos", is_active: true, created_at: null, lavanderia_id: 1 },
];

beforeEach(() => {
  // Stub de redirección.
  Object.defineProperty(window, "location", {
    writable: true,
    value: { href: "" },
  });

  // Sesión sembrada con permisos para que AuthGuard / Shell no redirijan.
  useAuthStore.setState({
    token: "test-token",
    user: {
      id: 1,
      username: "admin",
      role: "admin",
      lavanderiaId: 1,
      lavanderiaName: "Demo",
    },
    permissions: ["register_expense", "movements", "settings", "dashboard"],
    expiresAt: new Date(Date.now() + 60_000).toISOString(),
  });

  server.use(
    http.get(`${API_BASE}/catalogs/expense-categories`, () =>
      HttpResponse.json(CATEGORIES),
    ),
  );
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("ExpensesNewView", () => {
  it("renderiza categorías en el select", async () => {
    renderWithProviders(<ExpensesNewView />);

    expect(await screen.findByRole("option", { name: "Insumos" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Sueldos" })).toBeInTheDocument();
  });

  it("submit envía POST /expenses con payload correcto", async () => {
    const user = userEvent.setup();
    let received: unknown = null;

    server.use(
      http.post(`${API_BASE}/expenses`, async ({ request }) => {
        received = await request.json();
        return HttpResponse.json({ id: 99 }, { status: 201 });
      }),
    );

    renderWithProviders(<ExpensesNewView />);

    // Esperamos a que cargue el select.
    await screen.findByRole("option", { name: "Insumos" });

    // Categoría = Insumos
    await user.selectOptions(screen.getByLabelText("Categoría"), "1");

    // Monto = 25000
    // El campo Monto vive dentro de un wrapper con prefix "Gs.", así que
    // el label apunta al div. Buscamos el input directamente.
    const monto = screen.getByRole("spinbutton") as HTMLInputElement;
    await user.clear(monto);
    await user.type(monto, "25000");

    // Descripción
    const desc = screen.getByLabelText("Descripción") as HTMLTextAreaElement;
    await user.type(desc, "Compra de jabón");

    // Submit. Hay un solo botón "Registrar egreso".
    await user.click(screen.getByRole("button", { name: /Registrar egreso/ }));

    await waitFor(() => expect(received).not.toBeNull());

    expect(received).toMatchObject({
      categoria_egreso_id: 1,
      monto: 25000,
      descripcion: "Compra de jabón",
    });
  });

  it("no envía si monto es 0 (Zod: positive)", async () => {
    const user = userEvent.setup();
    let called = false;

    server.use(
      http.post(`${API_BASE}/expenses`, () => {
        called = true;
        return HttpResponse.json({ id: 1 }, { status: 201 });
      }),
    );

    renderWithProviders(<ExpensesNewView />);

    await screen.findByRole("option", { name: "Insumos" });

    // Categoría OK pero monto queda en 0.
    await user.selectOptions(screen.getByLabelText("Categoría"), "1");

    await user.click(screen.getByRole("button", { name: /Registrar egreso/ }));

    // Mensaje del schema y sin POST.
    expect(await screen.findByText(/Debe ser mayor a cero/)).toBeInTheDocument();
    expect(called).toBe(false);
  });

  it("no envía si no se elige categoría", async () => {
    const user = userEvent.setup();
    let called = false;

    server.use(
      http.post(`${API_BASE}/expenses`, () => {
        called = true;
        return HttpResponse.json({ id: 1 }, { status: 201 });
      }),
    );

    renderWithProviders(<ExpensesNewView />);

    await screen.findByRole("option", { name: "Insumos" });

    // El campo Monto vive dentro de un wrapper con prefix "Gs.", así que
    // el label apunta al div. Buscamos el input directamente.
    const monto = screen.getByRole("spinbutton") as HTMLInputElement;
    await user.clear(monto);
    await user.type(monto, "10000");

    await user.click(screen.getByRole("button", { name: /Registrar egreso/ }));

    expect(await screen.findByText(/Seleccioná una categoría/)).toBeInTheDocument();
    expect(called).toBe(false);
  });
});
