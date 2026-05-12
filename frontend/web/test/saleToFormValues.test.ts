import { describe, expect, it } from "vitest";
import { saleToFormValues } from "@/components/sales/SalesNewView";
import type { components } from "@/lib/api/schema";

type SaleResponse = components["schemas"]["SaleResponse"];

function makeSale(overrides: Partial<SaleResponse> = {}): SaleResponse {
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
        id: 10,
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

describe("saleToFormValues", () => {
  it("mapea fecha, tipo de cobro y método", () => {
    const v = saleToFormValues(makeSale());
    expect(v.fecha_venta).toBe("2026-05-09");
    expect(v.tipo_cobro).toBe("Contado");
    expect(v.metodo_pago).toBe("Efectivo");
  });

  it("normaliza tipo de cobro Credito", () => {
    const v = saleToFormValues(makeSale({ payment_type: "Credito" }));
    expect(v.tipo_cobro).toBe("Credito");
  });

  it("usa Efectivo por defecto si payment_method es null", () => {
    const v = saleToFormValues(makeSale({ payment_method: null }));
    expect(v.metodo_pago).toBe("Efectivo");
  });

  it("convierte items service a kind=service y refId=service_id", () => {
    const v = saleToFormValues(makeSale());
    expect(v.items).toHaveLength(1);
    expect(v.items[0]).toEqual({
      kind: "service",
      refId: 5,
      name: "Lavado básico",
      quantity: 1,
      unitPrice: 50000,
    });
  });

  it("convierte items product a kind=product y refId=product_id", () => {
    const v = saleToFormValues(
      makeSale({
        items: [
          {
            id: 11,
            item_type: "Producto",
            item_name: "Cera",
            service_id: null,
            product_id: 7,
            quantity: 2,
            unit_price: 15000,
            subtotal: 30000,
          },
        ],
      }),
    );
    expect(v.items[0]).toEqual({
      kind: "product",
      refId: 7,
      name: "Cera",
      quantity: 2,
      unitPrice: 15000,
    });
  });

  it("propaga placa y tipo de vehículo cuando vienen en la venta", () => {
    const v = saleToFormValues(
      makeSale({
        license_plate: "ABC123",
        vehicle_id: 42,
        vehicle_type_id: 3,
        vehicle_type_name: "Auto",
      }),
    );
    expect(v.license_plate).toBe("ABC123");
    expect(v.vehicle_type_id).toBe(3);
  });

  it("deja placa vacía y tipo undefined si la venta no tiene vehículo", () => {
    const v = saleToFormValues(makeSale({}));
    expect(v.license_plate).toBe("");
    expect(v.vehicle_type_id).toBeUndefined();
  });

  it("propaga factura con razon_social desde customer_name", () => {
    const v = saleToFormValues(
      makeSale({
        requires_invoice: true,
        customer_name: "Empresa S.A.",
        ruc_ci: "80012345-6",
      }),
    );
    expect(v.requiere_factura).toBe(true);
    expect(v.ruc_ci).toBe("80012345-6");
    expect(v.razon_social).toBe("Empresa S.A.");
  });

  it("sin factura deja razon_social vacío aunque haya customer_name", () => {
    const v = saleToFormValues(
      makeSale({ requires_invoice: false, customer_name: "Pepe" }),
    );
    expect(v.razon_social).toBe("");
  });

  it("notes null se vuelve string vacío", () => {
    const v = saleToFormValues(makeSale({ notes: null }));
    expect(v.observacion).toBe("");
  });
});
