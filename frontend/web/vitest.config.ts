import { defineConfig } from "vitest/config";
import { fileURLToPath } from "node:url";

export default defineConfig({
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  test: {
    environment: "happy-dom",
    globals: true,
    setupFiles: ["./test/setup.ts"],
    include: ["test/**/*.test.{ts,tsx}", "src/**/*.test.{ts,tsx}"],
    css: false,
    // Reporter dual: 'default' para humanos en terminal, 'json' a disco
    // para que agentes (o CI) puedan consumir resultados estructurados.
    reporters: ["default", "json"],
    outputFile: {
      json: "test-results/last-run.json",
    },
  },
});
