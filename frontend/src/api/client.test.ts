import { afterEach, describe, expect, it, vi } from "vitest";

import { api, ApiError, SESSION_EXPIRED_EVENT, tokenStore } from "./client";

function mockFetch(status: number, body: unknown) {
  return vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify(body), { status }));
}

afterEach(() => {
  vi.restoreAllMocks();
  tokenStore.clear();
});

describe("api client", () => {
  it("convierte el formato de error del backend en ApiError", async () => {
    mockFetch(422, {
      error: {
        code: "VALIDATION_ERROR",
        message: "Datos inválidos",
        details: [{ field: "age" }],
        request_id: "abc",
      },
    });

    const error = await api.activeModel().catch((rejection: unknown) => rejection);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 422,
      code: "VALIDATION_ERROR",
      message: "Datos inválidos",
      requestId: "abc",
    });
  });

  it("envía el token y cierra la sesión si la API responde 401", async () => {
    tokenStore.set("token-123");
    const fetchSpy = mockFetch(401, { error: { code: "UNAUTHORIZED", message: "Token inválido" } });
    const expired = vi.fn();
    window.addEventListener(SESSION_EXPIRED_EVENT, expired);

    await expect(api.models()).rejects.toBeInstanceOf(ApiError);

    const headers = fetchSpy.mock.calls[0]?.[1]?.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer token-123");
    expect(tokenStore.get()).toBeNull();
    expect(expired).toHaveBeenCalledOnce();
  });

  it("informa un error de red legible", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("Failed to fetch"));

    await expect(api.activeModel()).rejects.toMatchObject({ code: "NETWORK_ERROR" });
  });
});
