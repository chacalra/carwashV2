/**
 * Tests de CatalogManager — la factory genérica de Iter 8.
 *  - lista items desde GET /catalogs/services?only_active=false
 *  - crear: POST /catalogs/services con { name, price }
 *  - editar inline: PUT /catalogs/services/:id
 *  - toggle activo: PATCH /catalogs/services/:id/status
 *  - delete con confirm: DELETE /catalogs/services/:id
 *
 * Probamos `services` (con precio) para cubrir `withPrice=true` y un caso
 * sin precio (`expense-categories`) en otro test.
 */

import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from "vitest";
import userEvent from "@testing-library/user-event";
import { screen, waitFor, within } from "@testing-library/react";

import { CatalogManager } from "@/components/settings/CatalogManager";
import { API_BASE } from "./mocks/handlers";
import { server } from "./mocks/server";
import { renderWithProviders } from "./utils/renderWithProviders";

const SERVICES = [
  { id: 1, name: "Lavado básico", price: 50000, is_active: true, created_at: null, lavanderia_id: 1 },
  { id: 2, name: "Pulido", price: 200000, is_active: false, created_at: null, lavanderia_id: 1 },
];

beforeEach(() => {
  // El hook `useCatalogList` instancia los 4 queries aunque sólo use uno;
  // sembramos handlers vacíos para los otros tres y evitar warnings de MSW.
  server.use(
    http.get(`${API_BASE}/catalogs/services`, () => HttpResponse.json(SERVICES)),
    http.get(`${API_BASE}/catalogs/products`, () => HttpResponse.json([])),
    http.get(`${API_BASE}/catalogs/expense-categories`, () => HttpResponse.json([])),
    http.get(`${API_BASE}/catalogs/vehicle-types`, () => HttpResponse.json([])),
  );
});

afterEach(() => {
  vi.restoreAllMocks();
});

const baseProps = {
  title: "Servicios",
  description: "Catálogo del lavadero",
  resource: "services" as const,
  withPrice: true,
  emptyLabel: "Sin servicios",
  itemSingular: "Servicio",
};

describe("CatalogManager", () => {
  it("lista los items con precio y estado", async () => {
    renderWithProviders(<CatalogManager {...baseProps} />);

    expect(await screen.findByText("Lavado básico")).toBeInTheDocument();
    expect(screen.getByText("Pulido")).toBeInTheDocument();
    expect(screen.getByText("Gs. 50.000")).toBeInTheDocument();
    expect(screen.getByText("Gs. 200.000")).toBeInTheDocument();
    expect(screen.getByText("Activo")).toBeInTheDocument();
    expect(screen.getByText("Inactivo")).toBeInTheDocument();
  });

  it("crear: POST /catalogs/services con name + price", async () => {
    const user = userEvent.setup();
    let received: unknown = null;

    server.use(
      http.post(`${API_BASE}/catalogs/services`, async ({ request }) => {
        received = await request.json();
        return HttpResponse.json({ id: 3 }, { status: 201 });
      }),
    );

    renderWithProviders(<CatalogManager {...baseProps} />);
    await screen.findByText("Lavado básico");

    await user.type(screen.getByPlaceholderText(/Nuevo servicio/i), "Encerado");

    // Hay 2 spinbuttons en la página: el de crear y los de edición. El primero es el de crear.
    const priceInputs = screen.getAllByRole("spinbutton") as HTMLInputElement[];
    await user.clear(priceInputs[0]);
    await user.type(priceInputs[0], "120000");

    await user.click(screen.getByRole("button", { name: /Crear/ }));

    await waitFor(() => expect(received).not.toBeNull());
    expect(received).toMatchObject({ name: "Encerado", price: 120000 });
  });

  it("editar inline: PUT /catalogs/services/:id con cambios", async () => {
    const user = userEvent.setup();
    let putBody: unknown = null;
    let putId: string | null = null;

    server.use(
      http.put(`${API_BASE}/catalogs/services/:id`, async ({ params, request }) => {
        putId = params.id as string;
        putBody = await request.json();
        return HttpResponse.json({ message: "ok" });
      }),
    );

    renderWithProviders(<CatalogManager {...baseProps} />);
    await screen.findByText("Lavado básico");

    // Localizar la fila de Lavado básico y disparar Editar.
    const row = screen.getByText("Lavado básico").closest("tr") as HTMLElement;
    await user.click(within(row).getByLabelText("Editar"));

    // El input de nombre toma autoFocus dentro de la fila editada.
    const nameInput = within(row).getByDisplayValue("Lavado básico") as HTMLInputElement;
    await user.clear(nameInput);
    await user.type(nameInput, "Lavado express");

    // Dentro de la fila hay un spinbutton de precio editable.
    const priceInput = within(row).getByRole("spinbutton") as HTMLInputElement;
    await user.clear(priceInput);
    await user.type(priceInput, "55000");

    await user.click(within(row).getByLabelText("Guardar"));

    await waitFor(() => expect(putId).toBe("1"));
    expect(putBody).toMatchObject({ name: "Lavado express", price: 55000 });
  });

  it("toggle activo: PATCH /catalogs/services/:id/status", async () => {
    const user = userEvent.setup();
    let patchedId: string | null = null;

    server.use(
      http.patch(`${API_BASE}/catalogs/services/:id/status`, ({ params }) => {
        patchedId = params.id as string;
        return HttpResponse.json({ message: "ok" });
      }),
    );

    renderWithProviders(<CatalogManager {...baseProps} />);
    await screen.findByText("Lavado básico");

    const row = screen.getByText("Lavado básico").closest("tr") as HTMLElement;
    await user.click(within(row).getByLabelText("Desactivar"));

    await waitFor(() => expect(patchedId).toBe("1"));
  });

  it("eliminar abre dialog y confirma DELETE /catalogs/services/:id", async () => {
    const user = userEvent.setup();
    let deletedId: string | null = null;

    server.use(
      http.delete(`${API_BASE}/catalogs/services/:id`, ({ params }) => {
        deletedId = params.id as string;
        return HttpResponse.json({ message: "ok" });
      }),
    );

    renderWithProviders(<CatalogManager {...baseProps} />);
    await screen.findByText("Lavado básico");

    const row = screen.getByText("Lavado básico").closest("tr") as HTMLElement;
    await user.click(within(row).getByLabelText("Eliminar"));

    const confirmBtn = await screen.findByRole("button", { name: /^Eliminar$/ });
    await user.click(confirmBtn);

    await waitFor(() => expect(deletedId).toBe("1"));
  });

  it("cancelar el dialog no dispara DELETE", async () => {
    const user = userEvent.setup();
    let called = false;

    server.use(
      http.delete(`${API_BASE}/catalogs/services/:id`, () => {
        called = true;
        return HttpResponse.json({ message: "ok" });
      }),
    );

    renderWithProviders(<CatalogManager {...baseProps} />);
    await screen.findByText("Lavado básico");

    const row = screen.getByText("Lavado básico").closest("tr") as HTMLElement;
    await user.click(within(row).getByLabelText("Eliminar"));

    const cancelBtn = await screen.findByRole("button", { name: /Cancelar/ });
    await user.click(cancelBtn);

    await new Promise((r) => setTimeout(r, 30));
    expect(called).toBe(false);
  });

  it("no llama crear si el nombre está vacío", async () => {
    const user = userEvent.setup();
    let called = false;

    server.use(
      http.post(`${API_BASE}/catalogs/services`, () => {
        called = true;
        return HttpResponse.json({ id: 1 }, { status: 201 });
      }),
    );

    renderWithProviders(<CatalogManager {...baseProps} />);
    await screen.findByText("Lavado básico");

    await user.click(screen.getByRole("button", { name: /Crear/ }));

    await new Promise((r) => setTimeout(r, 30));
    expect(called).toBe(false);
  });
});

describe("CatalogManager (sin precio)", () => {
  it("oculta columna y campo de precio cuando withPrice=false", async () => {
    server.use(
      http.get(`${API_BASE}/catalogs/services`, () => HttpResponse.json([])),
      http.get(`${API_BASE}/catalogs/products`, () => HttpResponse.json([])),
      http.get(`${API_BASE}/catalogs/vehicle-types`, () => HttpResponse.json([])),
      http.get(`${API_BASE}/catalogs/expense-categories`, () =>
        HttpResponse.json([
          { id: 1, name: "Insumos", is_active: true, created_at: null, lavanderia_id: 1 },
        ]),
      ),
    );

    renderWithProviders(
      <CatalogManager
        title="Categorías"
        description=""
        resource="expense-categories"
        withPrice={false}
        emptyLabel="Sin categorías"
        itemSingular="Categoría"
      />,
    );

    await screen.findByText("Insumos");
    expect(screen.queryByText(/Precio/)).not.toBeInTheDocument();
    // Solo hay 1 spinbutton (el de "Crear precio") cuando withPrice=true.
    // Acá no debería haber ninguno.
    expect(screen.queryAllByRole("spinbutton").length).toBe(0);
  });
});
