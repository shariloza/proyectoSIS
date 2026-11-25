import { expect, type Page } from "@playwright/test";
import { mkdirSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const CAPTURES_DIR = resolve(ROOT, "docs", "capturas");

/** Credenciales de E2E_ADMIN_* o, si no están, del .env de la raíz del repositorio. */
export function adminCredentials(): { email: string; password: string } {
  const fromEnvFile = Object.fromEntries(
    readFileSync(resolve(ROOT, ".env"), "utf-8")
      .split(/\r?\n/)
      .filter((line) => /^[A-Z_]+=/.test(line))
      .map((line) => [line.slice(0, line.indexOf("=")), line.slice(line.indexOf("=") + 1)]),
  );
  const email = process.env.E2E_ADMIN_EMAIL ?? fromEnvFile.ADMIN_EMAIL;
  const password = process.env.E2E_ADMIN_PASSWORD ?? fromEnvFile.ADMIN_PASSWORD;
  if (!email || !password) throw new Error("Faltan ADMIN_EMAIL/ADMIN_PASSWORD para las pruebas E2E");
  return { email, password };
}

/**
 * CSV con `rows` filas del dataset original, desde un desplazamiento variable para que su hash
 * sea único. `transform` se aplica a cada línea, encabezado incluido.
 */
export function datasetSample(rows: number, transform: (line: string) => string = (line) => line): Buffer {
  const lines = readFileSync(resolve(ROOT, "data", "raw", "student_depression_dataset.csv"), "utf-8")
    .trim()
    .split(/\r?\n/);
  const offset = 1 + (Date.now() % 5000);
  const selected = [lines[0] ?? "", ...lines.slice(offset, offset + rows)];
  return Buffer.from(selected.map(transform).join("\n") + "\n");
}

export async function loginAsAdmin(page: Page): Promise<void> {
  const { email, password } = adminCredentials();
  await page.goto("/login");
  await page.getByLabel("Correo").fill(email);
  await page.getByLabel("Contraseña").fill(password);
  await page.getByRole("button", { name: "Ingresar" }).click();
  await expect(page.getByRole("heading", { name: "Historial de predicciones" })).toBeVisible();
}

/** Guarda una captura en docs/capturas para el documento final y el video. */
export async function capture(page: Page, name: string): Promise<void> {
  mkdirSync(CAPTURES_DIR, { recursive: true });
  // La barra superior es fija: en una captura de página completa quedaría en medio.
  await page.addStyleTag({ content: ".topbar { position: static !important; }" });
  await page.screenshot({ path: resolve(CAPTURES_DIR, `${name}.png`), fullPage: true });
}
