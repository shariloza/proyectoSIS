import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { Prediction } from "../../api/client";
import { RiskResult } from "./RiskResult";

const prediction: Prediction = {
  id: "1",
  prediction: 1,
  probability: 0.82,
  risk_band: "HIGH",
  model_version: "v1",
  disclaimer: "Este resultado NO es un diagnóstico.",
  created_at: "2026-11-23T12:00:00Z",
};

describe("RiskResult", () => {
  it("muestra el nivel, la probabilidad y siempre el aviso de que no es un diagnóstico", () => {
    render(<RiskResult result={prediction} />);

    expect(screen.getByText("Riesgo alto")).toBeInTheDocument();
    expect(screen.getByRole("meter")).toHaveAttribute("aria-valuenow", "82");
    expect(screen.getByRole("note")).toHaveTextContent("NO es un diagnóstico");
    expect(screen.getByText(/buscar apoyo de un profesional/)).toBeInTheDocument();
  });
});
