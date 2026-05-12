/**
 * Tests de SalesFormInner — flujo crítico:
 *  - tile click agrega item
 *  - tile click repetido incrementa qty
 *  - submit en modo create dispara POST /sales con payload mapeado
 *  - submit en modo edit dispara PUT /sales/{id}
 */

import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";

import { SalesFormInner } from "@/components/sales/SalesNewView";
import type { components } from "@/lib/api/schema";
import { API_BASE } from "./mocks/handlers";
import { server } from "./mocks/server";
import { renderWithProviders } from "./utils/renderWithProviders";

type CatalogItem = components["schemas"]["CatalogItem"];

const SERVICES: CatalogItem[] = [
  {
    id: 5,
    name: "Lavado básico",
    price: 50000,
    is_active: true,
    created_at: null,
    lavanderia_id: 1,
  },
  {
    id: 6,
    name: "Pulido completo",
    price: 200000,
    is_active: true,
    created_at: null,
    lavanderia_id: 1,
  },
];

const PRODUCTS: CatalogItem[] = [
  {
    id: 7,
    name: "Cera",
    price: 15000,
    is_active: true,
    created_at: null,
    lavanderia_id: 1,
  },
  {
    id: 8,
    name: "Perfume sin precio",
    price: 0,
    is_active: true,
    created_at: null,
    lavanderia_id: 1,
  },
];

beforeEach(() => {
  // Stub de redirección para que el test no truene cuando el form intenta navegar.
  Object.defineProperty(window, "location", {
    writable: true,
    value: { href: "" },
  });

  server.use(
    http.get(`${API_BASE}/catalogs/services`, () => HttpResponse.json(SERVICES)),
    http.get(`${API_BASE}/catalogs/products`, () => HttpResponse.json(PRODUCTS)),
    http.get(`${API_BASE}/catalogs/vehicle-types`, () =>
      HttpResponse.json([
        { id: 1, name: "Auto", is_active: true, created_at: null, lavanderia_id: 1 },
      ]),
    ),
    http.get(`${API_BASE}/vehicles/by-plate/:plate`, () =>
      HttpResponse.json(null),
    ),
    http.post(`${API_BASE}/vehicles`, () =>
      HttpResponse.json({ id: 77 }, { status: 201 }),
    ),
  );
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("SalesFormInner — modo create", () => {
  it("agregar el mismo servicio dos veces incrementa qty a 2", async () => {
    const user = userEvent.setup();
    renderWithProviders(<SalesFormInner mode="create" />);

    const tile = await screen.findByRole("button", { name: /Lavado básico/ });
    await user.click(tile);
    await user.click(tile);

    // El subtotal de la línea es 2 × 50.000 = 100.000.
    // El total del resumen también suma 100.000.
    const totals = screen.getAllByText("Gs. 100.000");
    expect(totals.length).toBeGreaterThanOrEqual(1);
  });

  it("submit con solo productos no manda vehiculo_id", async () => {
    const user = userEvent.setup();
    let received: Record<string, unknown> | null = null;

    server.use(
      http.post(`${API_BASE}/sales`, async ({ request }) => {
        received = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ id: 999 }, { status: 201 });
      }),
    );

    renderWithProviders(<SalesFormInner mode="create" />);

    // Solo producto: el campo vehiculo no aplica.
    await user.click(await screen.findByRole("button", { name: /Cera/ }));

    const submitBtn = screen.getAllByRole("button", { name: /Cobrar Gs\. 15\.000/ })[0];
    await user.click(submitBtn);

    await waitFor(() => expect(received).not.toBeNull());

    expect(received).toMatchObject({
      tipo_cobro: "Contado",
      metodo_pago: "Efectivo",
      requiere_factura: false,
      items: [{ producto_id: 7, cantidad: 1, precio_unitario: 15000 }],
    });
    // Sin servicios, no debe ir vehiculo_id.
    expect(received!.vehiculo_id).toBeUndefined();
  });

  it("con servicio y matrícula completa, submit dispara upsert vehículo + POST /sales", async () => {
    const user = userEvent.setup();
    let received: Record<string, unknown> | null = null;
    let upsertCalled = false;

    server.use(
      http.post(`${API_BASE}/vehicles`, () => {
        upsertCalled = true;
        return HttpResponse.json({ id: 77 }, { status: 201 });
      }),
      http.post(`${API_BASE}/sales`, async ({ request }) => {
        received = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ id: 999 }, { status: 201 });
      }),
    );

    renderWithProviders(<SalesFormInner mode="create" />);

    // Servicio en el detalle: la sección "Vehículo" se vuelve obligatoria.
    await user.click(await screen.findByRole("button", { name: /Lavado básico/ }));

    const plateInput = await screen.findByLabelText(/Placa/);
    await user.type(plateInput, "ABC123");

    const typeSelect = screen.getByLabelText(/Tipo de vehículo/);
    await user.selectOptions(typeSelect, "1");

    const submitBtn = screen.getAllByRole("button", { name: /Cobrar Gs\. 50\.000/ })[0];
    await user.click(submitBtn);

    await waitFor(() => expect(received).not.toBeNull());
    expect(upsertCalled).toBe(true);
    expect(received).toMatchObject({
      items: [{ servicio_id: 5, cantidad: 1, precio_unitario: 50000 }],
      vehiculo_id: 77,
    });
  });

  it("con servicio pero sin placa, el submit no dispara POST /sales", async () => {
    const user = userEvent.setup();
    let saleCalled = false;

    server.use(
      http.post(`${API_BASE}/sales`, () => {
        saleCalled = true;
        return HttpResponse.json({ id: 1 }, { status: 201 });
      }),
    );

    renderWithProviders(<SalesFormInner mode="create" />);

    await user.click(await screen.findByRole("button", { name: /Lavado básico/ }));

    const submitBtn = screen.getAllByRole("button", { name: /Cobrar Gs\. 50\.000/ })[0];
    await user.click(submitBtn);

    // El form debe haber bloqueado la submission por validación zod.
    await waitFor(() => {
      expect(screen.getByText(/Ingresá la placa/)).toBeInTheDocument();
    });
    expect(saleCalled).toBe(false);
  });

  it("bloquea el submit si hay un ítem con precio en 0", async () => {
    const user = userEvent.setup();
    let saleCalled = false;

    server.use(
      http.post(`${API_BASE}/sales`, () => {
        saleCalled = true;
        return HttpResponse.json({ id: 1 }, { status: 201 });
      }),
    );

    renderWithProviders(<SalesFormInner mode="create" />);

    // Agregar producto con precio 0 (no requiere vehiculo por ser solo producto).
    await user.click(await screen.findByRole("button", { name: /Perfume sin precio/ }));

    // Mensaje de advertencia visible.
    await waitFor(() => {
      expect(
        screen.getByText(/Hay ítems con precio en Gs\. 0/),
      ).toBeInTheDocument();
    });

    // El botón de cobrar está deshabilitado.
    const submitBtns = screen.getAllByRole("button", { name: /Cobrar|Precio en 0/ });
    expect(submitBtns.length).toBeGreaterThan(0);
    submitBtns.forEach((b) => expect(b).toBeDisabled());

    // Aunque algún click ocurriera, el POST no se dispara.
    await user.click(submitBtns[0]);
    expect(saleCalled).toBe(false);
  });

  it("sección vehículo cambia de inactiva a activa al agregar un servicio", async () => {
    const user = userEvent.setup();
    renderWithProviders(<SalesFormInner mode="create" />);

    // Sin items, ni siquiera con producto: la sección dice que no aplica.
    expect(screen.getByText(/Agregá un servicio al detalle/)).toBeInTheDocument();

    await user.click(await screen.findByRole("button", { name: /Cera/ }));
    expect(screen.getByText(/Agregá un servicio al detalle/)).toBeInTheDocument();

    await user.click(await screen.findByRole("button", { name: /Lavado básico/ }));
    // Ahora la sección debe mostrar inputs de placa + tipo.
    await waitFor(() => {
      expect(screen.getByLabelText(/Placa/)).toBeInTheDocument();
    });
  });

  it("no permite submit sin items (validación Zod)", async () => {
    const user = userEvent.setup();
    let called = false;

    server.use(
      http.post(`${API_BASE}/sales`, () => {
        called = true;
        return HttpResponse.json({ id: 1 }, { status: 201 });
      }),
    );

    renderWithProviders(<SalesFormInner mode="create" />);

    // El botón está disabled mientras no haya items.
    await screen.findByRole("button", { name: /Lavado básico/ });
    const submitBtns = screen.getAllByRole("button", { name: /Cobrar|Sin ítems/ });
    expect(submitBtns.length).toBeGreaterThan(0);
    submitBtns.forEach((b) => expect(b).toBeDisabled());

    expect(called).toBe(false);
  });
});

describe("SalesFormInner — modo edit", () => {
  it("submit dispara PUT /sales/{id} y CTA dice 'Guardar cambios'", async () => {
    const user = userEvent.setup();
    let putBody: unknown = null;
    let putId: string | null = null;

    server.use(
      http.put(`${API_BASE}/sales/:id`, async ({ params, request }) => {
        putId = params.id as string;
        putBody = await request.json();
        return HttpResponse.json({ id: 42 });
      }),
    );

    renderWithProviders(
      <SalesFormInner
        mode="edit"
        saleId={42}
        defaultValues={{
          fecha_venta: "2026-05-09",
          tipo_cobro: "Contado",
          metodo_pago: "Efectivo",
          observacion: "",
          items: [
            {
              kind: "service",
              refId: 5,
              name: "Lavado básico",
              quantity: 1,
              unitPrice: 50000,
            },
          ],
          license_plate: "ABC123",
          vehicle_type_id: 1,
          requiere_factura: false,
          ruc_ci: "",
          razon_social: "",
        }}
      />,
    );

    const submitBtns = await screen.findAllByRole("button", { name: /Guardar/ });
    await user.click(submitBtns[0]);

    await waitFor(() => expect(putId).toBe("42"));
    expect(putBody).toMatchObject({
      tipo_cobro: "Contado",
      items: [{ servicio_id: 5, cantidad: 1, precio_unitario: 50000 }],
    });
  });
});
