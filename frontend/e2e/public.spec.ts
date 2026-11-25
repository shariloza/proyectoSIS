import { expect, test } from "@playwright/test";

import { capture } from "./support";

test("un estudiante completa la evaluación y ve su riesgo con el aviso ético", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "¿Cómo estás llevando tus estudios?" })).toBeVisible();
  await capture(page, "01-evaluacion-formulario");

  await page.getByLabel("Edad", { exact: true }).fill("22");
  await page
    .getByRole("group", { name: "¿Cuánta presión académica sientes?" })
    .getByText("5", { exact: true })
    .click();
  await page
    .getByRole("group", { name: "¿Cuánto estrés te generan tus finanzas?" })
    .getByText("5", { exact: true })
    .click();
  await page.getByLabel("¿Cuántas horas duermes por noche?").selectOption({ label: "Menos de 5 horas" });
  await page.getByLabel("¿Cómo describirías tu alimentación?").selectOption({ label: "Poco saludable" });
  await page.getByRole("button", { name: "Estimar mi nivel de riesgo" }).click();

  const result = page.getByRole("region", { name: "Resultado de la estimación" });
  await expect(result).toBeVisible();
  await expect(result.getByText("Riesgo alto")).toBeVisible();
  await expect(result.getByRole("note")).toContainText("NO es un diagnóstico");
  await expect(result.getByRole("meter")).toHaveAttribute("aria-valuenow", /\d+/);
  await capture(page, "02-evaluacion-resultado");
});

test("los datos fuera de rango se rechazan con un mensaje claro del backend", async ({ page }) => {
  await page.goto("/");
  // Se quita la validación del navegador para comprobar que la API también la aplica.
  await page
    .getByLabel("Edad", { exact: true })
    .evaluate((input: HTMLInputElement) => input.removeAttribute("min"));
  await page.getByLabel("Edad", { exact: true }).fill("12");
  await page.getByRole("button", { name: "Estimar mi nivel de riesgo" }).click();

  const alert = page.getByRole("alert");
  await expect(alert).toContainText("Los datos enviados no son válidos.");
  await expect(alert).toContainText("age");
});

test("las métricas del modelo activo son públicas", async ({ page }) => {
  await page.goto("/metricas");

  await expect(page.getByText("Versión activa")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Matriz de confusión" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Curva ROC" })).toBeVisible();
  await expect(page.getByText("C1", { exact: true })).toBeVisible();
  await capture(page, "03-metricas");
});

test("las pantallas de administración exigen iniciar sesión", async ({ page, request }) => {
  await page.goto("/admin/historial");
  await expect(page).toHaveURL(/\/login$/);

  // Aunque se saltee la interfaz, la API rechaza el acceso.
  const response = await request.get("/api/v1/predictions");
  expect(response.status()).toBe(401);
  expect((await response.json()).error.code).toBe("UNAUTHORIZED");
});

test("una contraseña incorrecta muestra un error genérico", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Correo").fill("admin@example.com");
  await page.getByLabel("Contraseña").fill("contraseña-incorrecta");
  await page.getByRole("button", { name: "Ingresar" }).click();

  await expect(page.getByRole("alert")).toContainText("Correo o contraseña incorrectos.");
});
