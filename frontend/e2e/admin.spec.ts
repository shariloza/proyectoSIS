import { expect, test, type Page } from "@playwright/test";

import { capture, datasetSample, loginAsAdmin } from "./support";

const TRAINING_TIMEOUT = 5 * 60_000;

async function upload(page: Page, name: string, content: Buffer) {
  await page.goto("/admin/datasets");
  await page.getByLabel(/Archivo CSV/).setInputFiles({ name, mimeType: "text/csv", buffer: content });
  await page.getByRole("button", { name: "Subir y validar" }).click();
}

async function activeVersion(page: Page): Promise<string> {
  const response = await page.request.get("/api/v1/models/active");
  return (await response.json()).version as string;
}

test.describe.serial("administración", () => {
  test.beforeEach(async ({ page }) => loginAsAdmin(page));

  test("el historial muestra la predicción con datos enviados, resultado y versión", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "Estimar mi nivel de riesgo" }).click();
    const version = await page.getByText(/Probabilidad estimada por el modelo/).textContent();

    await page.goto("/admin/historial");
    const firstRow = page.getByRole("row").nth(1);
    await expect(firstRow).toContainText("Edad: 21");
    await expect(firstRow).toContainText(version?.split(" ").at(-1) ?? "v");
    await capture(page, "04-historial");
  });

  test("un archivo con columnas faltantes se rechaza explicando el problema", async ({ page }) => {
    const withoutCgpa = datasetSample(600, (line) => line.split(",").slice(0, 7).join(","));

    await upload(page, "incompleto.csv", withoutCgpa);

    await expect(page.getByRole("alert")).toContainText("El archivo no cumple el formato esperado.");
    await expect(page.getByRole("alert")).toContainText("faltan columnas");
    await capture(page, "05-dataset-invalido");
  });

  test("ciclo completo: subir, re-entrenar, comparar, activar y hacer rollback", async ({ page }) => {
    test.setTimeout(TRAINING_TIMEOUT + 60_000);
    const before = await activeVersion(page);

    await upload(page, "actualizado.csv", datasetSample(12000));
    await expect(page.getByRole("status")).toContainText("Archivo aceptado");
    await capture(page, "06-dataset-aceptado");

    await page.getByRole("link", { name: "Usarlo para re-entrenar →" }).click();
    const enqueued = page.waitForResponse(
      (response) =>
        response.url().endsWith("/api/v1/training-jobs") && response.request().method() === "POST",
    );
    await page.getByRole("button", { name: "Re-entrenar" }).click();
    expect((await enqueued).status()).toBe(202);
    await expect(page.getByText(/En cola|Entrenando/).first()).toBeVisible();
    await capture(page, "07-reentrenamiento-en-curso");

    await expect(page.getByText("Terminado").first()).toBeVisible({ timeout: TRAINING_TIMEOUT });
    const comparison = page.getByRole("heading", { name: /^3\. Candidato v\d+ frente al activo/ });
    await expect(comparison).toBeVisible();
    await capture(page, "08-comparacion-candidato");

    const candidate = (await comparison.textContent())?.match(/Candidato (v\d+)/)?.[1] ?? "";
    const activateButton = page.getByRole("button", { name: `Activar ${candidate}` });
    if (await activateButton.isDisabled()) {
      // El candidato no cumplió los criterios: se verifica que no se pueda activar.
      await expect(page.getByText("no cumplió los criterios de aceptación")).toBeVisible();
      expect(await activeVersion(page)).toBe(before);
      return;
    }

    page.once("dialog", (dialog) => dialog.accept());
    await activateButton.click();
    await expect(page.getByText(`El modelo ${candidate} está activo.`)).toBeVisible();
    expect(await activeVersion(page)).toBe(candidate);

    page.once("dialog", (dialog) => dialog.accept());
    await page.getByRole("button", { name: "↩ Volver a la versión anterior" }).click();
    await expect(page.getByText(`Rollback realizado: ${before} vuelve a estar activo.`)).toBeVisible();
    expect(await activeVersion(page)).toBe(before);
    await capture(page, "09-rollback");
  });
});
