import { defineConfig } from "astro/config";
import react from "@astrojs/react";
import tailwindcss from "@tailwindcss/vite";

// Build de demo para GitHub Pages (ver .github/workflows/pages.yml):
// - DEMO_BASE: la app vive bajo /<repo>/ en vez de la raíz del dominio.
// - format "file": genera dashboard.html en vez de dashboard/index.html,
//   así Pages sirve /dashboard sin redirigir (y sin perder el ?id= de editar).
// El build normal (VPS + nginx) no cambia: sin DEMO_BASE todo queda igual.
const demoBase = process.env.DEMO_BASE;

// https://astro.build/config
export default defineConfig({
  output: "static",
  ...(demoBase ? { base: demoBase, build: { format: "file" } } : {}),
  integrations: [react()],
  vite: {
    plugins: [tailwindcss()],
    // Siempre definida: así Vite la reemplaza por una constante y elimina el
    // backend simulado del build de producción (PUBLIC_DEMO sin setear).
    define: {
      "import.meta.env.PUBLIC_DEMO": JSON.stringify(process.env.PUBLIC_DEMO ?? "false"),
    },
  },
  server: {
    host: "localhost",
    port: 4321,
  },
});
