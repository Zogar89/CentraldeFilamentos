import { svelte } from "@sveltejs/vite-plugin-svelte";
import { resolve } from "node:path";
import { defineConfig } from "vite";

export default defineConfig({
  base: "/CentraldeFilamentos/",
  plugins: [svelte()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
    rollupOptions: {
      input: {
        inicio: resolve(__dirname, "index.html"),
        colorPicker: resolve(__dirname, "color-picker.html"),
        resumen: resolve(__dirname, "resumen.html"),
        estadisticas: resolve(__dirname, "estadisticas.html"),
      },
    },
  },
});
