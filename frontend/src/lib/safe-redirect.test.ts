import { describe, expect, it } from "vitest";

import { safeInternalPath } from "./safe-redirect";

describe("safeInternalPath (regresión: open redirect tras el login)", () => {
  it("acepta rutas internas", () => {
    expect(safeInternalPath("/admin/datasets", "/")).toBe("/admin/datasets");
  });

  it.each(["//evil.com", "https://evil.com", "/\\evil.com", "javascript:alert(1)", 42, null])(
    "rechaza %s y usa el destino por defecto",
    (candidate) => {
      expect(safeInternalPath(candidate, "/admin/historial")).toBe("/admin/historial");
    },
  );
});
