import { defineConfig } from "vite"
import { svelte } from "@sveltejs/vite-plugin-svelte"

// In development the app runs on Vite and talks to the Python API on 8008.
// The build goes into the Python package, which serves it on the same port.
export default defineConfig({
  plugins: [svelte()],
  server: {
    port: 5173,
    proxy: { "/api": "http://127.0.0.1:8008" },
  },
  build: {
    outDir: "../sourdough/interface/static",
    emptyOutDir: true,
  },
})
