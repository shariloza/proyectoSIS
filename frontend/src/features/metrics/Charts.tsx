import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { decimal } from "../../lib/format";
import type { EvaluationMetrics } from "./evaluation";

const CLASS_NAMES = { "0": "Sin depresión", "1": "Con depresión" } as const;
const AXIS = { stroke: "var(--ink-muted)", fontSize: 12 };

export function ClassMetricsChart({ metrics }: { metrics: EvaluationMetrics }) {
  const data = (["precision", "recall", "f1"] as const).map((key) => ({
    metric: { precision: "Precisión", recall: "Recall", f1: "F1" }[key],
    [CLASS_NAMES["0"]]: metrics.per_class["0"][key],
    [CLASS_NAMES["1"]]: metrics.per_class["1"][key],
  }));
  return (
    <figure className="chart" aria-label="Precisión, recall y F1 por clase">
      <ResponsiveContainer>
        <BarChart data={data} barGap={2}>
          <CartesianGrid vertical={false} stroke="var(--border)" />
          <XAxis dataKey="metric" tick={AXIS} />
          <YAxis domain={[0, 1]} tick={AXIS} />
          <Tooltip formatter={(value: number) => decimal(value)} />
          <Legend />
          <Bar
            dataKey={CLASS_NAMES["0"]}
            fill="var(--chart-1)"
            radius={[4, 4, 0, 0]}
            isAnimationActive={false}
          />
          <Bar
            dataKey={CLASS_NAMES["1"]}
            fill="var(--chart-2)"
            radius={[4, 4, 0, 0]}
            isAnimationActive={false}
          />
        </BarChart>
      </ResponsiveContainer>
    </figure>
  );
}

export function RocChart({ metrics }: { metrics: EvaluationMetrics }) {
  const data = metrics.roc_curve.fpr.map((fpr, index) => ({
    fpr,
    modelo: metrics.roc_curve.tpr[index],
    azar: fpr,
  }));
  return (
    <figure className="chart" aria-label={`Curva ROC, área bajo la curva ${decimal(metrics.roc_auc)}`}>
      <ResponsiveContainer>
        <LineChart data={data}>
          <CartesianGrid stroke="var(--border)" />
          <XAxis
            dataKey="fpr"
            type="number"
            domain={[0, 1]}
            tick={AXIS}
            label={{ value: "Falsos positivos", position: "insideBottom", offset: -2, fontSize: 12 }}
          />
          <YAxis domain={[0, 1]} tick={AXIS} />
          <Tooltip
            formatter={(value: number) => decimal(value)}
            labelFormatter={(fpr: number) => `FPR ${decimal(fpr)}`}
          />
          <Legend verticalAlign="top" />
          <Line
            dataKey="modelo"
            name={`Modelo (AUC ${decimal(metrics.roc_auc)})`}
            stroke="var(--chart-1)"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
          <Line
            dataKey="azar"
            name="Azar"
            stroke="var(--ink-muted)"
            strokeDasharray="5 5"
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </figure>
  );
}

export function ConfusionMatrix({ matrix }: { matrix: EvaluationMetrics["confusion_matrix"] }) {
  const max = Math.max(...matrix.flat());
  const cell = (value: number) => (
    <div
      className="cell"
      style={{
        background: `color-mix(in srgb, var(--chart-1) ${Math.round((value / max) * 70) + 8}%, var(--surface))`,
      }}
    >
      {value.toLocaleString("es")}
    </div>
  );
  return (
    <div
      className="matrix"
      role="group"
      aria-label="Matriz de confusión: filas = valor real, columnas = predicción"
    >
      <span />
      <span className="head">Predicho: sin depresión</span>
      <span className="head">Predicho: con depresión</span>
      <span className="head">Real: sin depresión</span>
      {cell(matrix[0][0])}
      {cell(matrix[0][1])}
      <span className="head">Real: con depresión</span>
      {cell(matrix[1][0])}
      {cell(matrix[1][1])}
    </div>
  );
}
