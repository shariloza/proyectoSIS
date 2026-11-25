/**
 * Pruebas end-to-end contra el sistema completo levantado con `docker compose up -d`.
 * Ejecutar con `npm run e2e` (lee las credenciales de administración del .env de la raíz).
 */
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "e2e",
  timeout: 60_000,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://127.0.0.1:8080",
    locale: "es-ES",
    trace: "retain-on-failure",
    ...devices["Desktop Chrome"],
  },
});
