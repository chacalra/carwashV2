import { describe, expect, it } from "vitest";
import {
  firstDayOfMonthISO,
  formatDate,
  formatMoney,
  todayISO,
} from "@/lib/format";

describe("formatMoney", () => {
  it("formatea positivos con símbolo Gs.", () => {
    expect(formatMoney(50000)).toBe("Gs. 50.000");
  });

  it("formatea negativos con guión delante", () => {
    expect(formatMoney(-650000)).toBe("-Gs. 650.000");
  });

  it("redondea decimales (medio guaraní no existe)", () => {
    expect(formatMoney(1234.6)).toBe("Gs. 1.235");
  });

  it("devuelve em dash para null/undefined/NaN", () => {
    expect(formatMoney(null)).toBe("—");
    expect(formatMoney(undefined)).toBe("—");
    expect(formatMoney(Number.NaN)).toBe("—");
  });

  it("withSymbol:false omite el prefijo Gs.", () => {
    expect(formatMoney(50000, { withSymbol: false })).toBe("50.000");
    expect(formatMoney(-50000, { withSymbol: false })).toBe("-50.000");
  });

  it("formatea 0 sin signo", () => {
    expect(formatMoney(0)).toBe("Gs. 0");
  });
});

describe("formatDate", () => {
  it("convierte ISO yyyy-MM-dd a dd/MM/yyyy", () => {
    expect(formatDate("2026-05-09")).toBe("09/05/2026");
  });

  it("devuelve em dash si es null/undefined", () => {
    expect(formatDate(null)).toBe("—");
    expect(formatDate(undefined)).toBe("—");
  });

  it("devuelve el input crudo si no parsea", () => {
    expect(formatDate("no-es-una-fecha")).toBe("no-es-una-fecha");
  });
});

describe("todayISO / firstDayOfMonthISO", () => {
  it("todayISO matchea formato yyyy-MM-dd", () => {
    expect(todayISO()).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });

  it("firstDayOfMonthISO termina en -01", () => {
    expect(firstDayOfMonthISO()).toMatch(/^\d{4}-\d{2}-01$/);
  });
});
