/**
 * Tests del tema. Cubrimos la lógica del store (la fuente de verdad).
 * El dropdown de Radix no abre fiablemente en happy-dom (PointerEvents
 * incompletos), así que el toggle se valida indirectamente: render del
 * componente sin errores + render del trigger.
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "./utils/renderWithProviders";
import { ThemeToggle } from "@/components/shell/ThemeToggle";
import { resolvedTheme, useThemeStore } from "@/lib/theme/store";

describe("theme store", () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.classList.remove("dark");
    useThemeStore.setState({ theme: "system" });
  });

  it("setTheme('dark') aplica la clase y persiste", () => {
    useThemeStore.getState().setTheme("dark");
    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(window.localStorage.getItem("carwash.theme")).toBe("dark");
    expect(useThemeStore.getState().theme).toBe("dark");
  });

  it("setTheme('light') quita la clase", () => {
    document.documentElement.classList.add("dark");
    useThemeStore.getState().setTheme("light");
    expect(document.documentElement.classList.contains("dark")).toBe(false);
    expect(window.localStorage.getItem("carwash.theme")).toBe("light");
  });

  it("en modo 'system' resuelve según prefers-color-scheme", () => {
    const matchMedia = vi
      .spyOn(window, "matchMedia")
      .mockImplementation(
        (q) =>
          ({
            matches: q.includes("dark"),
            media: q,
            addEventListener: () => {},
            removeEventListener: () => {},
            addListener: () => {},
            removeListener: () => {},
            dispatchEvent: () => false,
            onchange: null,
          }) as unknown as MediaQueryList,
      );

    expect(resolvedTheme("system")).toBe("dark");
    useThemeStore.getState().setTheme("system");
    expect(document.documentElement.classList.contains("dark")).toBe(true);

    matchMedia.mockRestore();
  });
});

describe("ThemeToggle", () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.classList.remove("dark");
    useThemeStore.setState({ theme: "system" });
  });

  it("monta el botón disparador con label accesible", () => {
    renderWithProviders(<ThemeToggle />);
    expect(
      screen.getByRole("button", { name: /cambiar tema/i }),
    ).toBeInTheDocument();
  });
});
