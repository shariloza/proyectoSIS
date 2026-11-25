import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ServiceStatus } from "./ServiceStatus";

function respond(responses: Record<string, [number, unknown]>) {
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const path = String(input).replace(/^.*\/api\/v1/, "");
    const [status, body] = responses[path] ?? [404, {}];
    return new Response(JSON.stringify(body), { status });
  });
}

function renderStatus() {
  render(
    <QueryClientProvider client={new QueryClient()}>
      <ServiceStatus />
    </QueryClientProvider>,
  );
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("ServiceStatus", () => {
  it("consulta /health/live y /health/ready y muestra el modelo listo", async () => {
    respond({
      "/health/live": [200, { status: "ok" }],
      "/health/ready": [200, { status: "ok", model_version: "v1" }],
    });

    renderStatus();

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Servicio de IA en línea · base de datos y modelo v1 listos",
    );
  });

  it("muestra el motivo cuando el servicio no está listo", async () => {
    respond({
      "/health/live": [200, { status: "ok" }],
      "/health/ready": [503, { error: { code: "SERVICE_UNAVAILABLE", message: "No hay un modelo activo." } }],
    });

    renderStatus();

    expect(await screen.findByRole("status")).toHaveTextContent("No hay un modelo activo.");
  });
});
