import type { ModelDetail } from "../../api/client";

/**
 * Forma de `metrics` y `acceptance` que produce backend/src/app/ml/evaluation.py.
 * En el contrato OpenAPI son objetos libres; aquí se tipan para la visualización.
 */
export interface ClassMetrics {
  precision: number;
  recall: number;
  f1: number;
  support: number;
}

export interface EvaluationMetrics {
  roc_auc: number;
  f1_macro: number;
  accuracy: number;
  per_class: Record<"0" | "1", ClassMetrics>;
  confusion_matrix: [[number, number], [number, number]];
  roc_curve: { fpr: number[]; tpr: number[] };
  recall_by_gender: Record<string, number>;
}

export interface Criterion {
  code: string;
  description: string;
  threshold: number;
  operator: ">=" | "<=";
  value: number;
  passed: boolean;
}

export const testMetrics = (model: ModelDetail) => (model.metrics as { test: EvaluationMetrics }).test;

export const criteria = (model: ModelDetail) => (model.acceptance as { criteria: Criterion[] }).criteria;
