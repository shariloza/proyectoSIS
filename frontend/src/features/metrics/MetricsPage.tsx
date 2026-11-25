import { useQuery } from "@tanstack/react-query";

import { api, type ModelDetail } from "../../api/client";
import { ErrorAlert, Loading, StatusBadge } from "../../components/Status";
import { dateTime, decimal, percent } from "../../lib/format";
import { useAuth } from "../auth/useAuth";
import { ClassMetricsChart, ConfusionMatrix, RocChart } from "./Charts";
import { criteria, testMetrics } from "./evaluation";

export function MetricsPage() {
  const active = useQuery({ queryKey: ["models", "active"], queryFn: api.activeModel });
  const { isAdmin } = useAuth();

  return (
    <div className="stack">
      <header className="page-header">
        <h1>Métricas del modelo</h1>
        <p>
          Rendimiento del modelo en producción, medido sobre datos de prueba que nunca vio durante el
          entrenamiento.
        </p>
      </header>
      {active.isPending && <Loading />}
      <ErrorAlert error={active.error} />
      {active.data && <ModelMetrics model={active.data} />}
      {isAdmin && <VersionsTable />}
    </div>
  );
}

export function ModelMetrics({ model }: { model: ModelDetail }) {
  const metrics = testMetrics(model);
  return (
    <div className="stack">
      <div className="grid grid-3">
        <Stat
          label="Versión activa"
          value={model.version}
          note={`${model.algorithm} · ${dateTime(model.activated_at)}`}
        />
        <Stat label="ROC-AUC" value={decimal(metrics.roc_auc)} note="Capacidad de distinguir ambas clases" />
        <Stat
          label="Recall (con depresión)"
          value={percent(metrics.per_class["1"].recall)}
          note="Casos de riesgo detectados"
        />
        <Stat
          label="F1 macro"
          value={decimal(metrics.f1_macro)}
          note={`Exactitud ${percent(metrics.accuracy)}`}
        />
      </div>

      <div className="grid grid-3">
        <section className="card">
          <h2>Métricas por clase</h2>
          <ClassMetricsChart metrics={metrics} />
        </section>
        <section className="card">
          <h2>Curva ROC</h2>
          <RocChart metrics={metrics} />
        </section>
        <section className="card stack">
          <h2>Matriz de confusión</h2>
          <ConfusionMatrix matrix={metrics.confusion_matrix} />
          <p className="small muted">
            Recall por género:{" "}
            {Object.entries(metrics.recall_by_gender)
              .map(([gender, recall]) => `${gender === "Male" ? "hombres" : "mujeres"} ${percent(recall)}`)
              .join(" · ")}
          </p>
        </section>
      </div>

      <section className="card">
        <h2>Criterios de aceptación</h2>
        <AcceptanceTable model={model} />
      </section>
    </div>
  );
}

function Stat({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <div className="card stat">
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value}</span>
      <span className="small muted">{note}</span>
    </div>
  );
}

export function AcceptanceTable({ model }: { model: ModelDetail }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Criterio</th>
            <th className="numeric">Umbral</th>
            <th className="numeric">Obtenido</th>
            <th>Cumple</th>
          </tr>
        </thead>
        <tbody>
          {criteria(model).map((criterion) => (
            <tr key={criterion.code}>
              <td>
                <strong>{criterion.code}</strong> {criterion.description}
              </td>
              <td className="numeric">
                {criterion.operator === ">=" ? "≥" : "≤"} {criterion.threshold.toLocaleString("es")}
              </td>
              <td className="numeric">{criterion.value.toLocaleString("es")}</td>
              <td>
                <span className={`check ${criterion.passed ? "check-ok" : "check-fail"}`}>
                  {criterion.passed ? "✓ Sí" : "✗ No"}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function VersionsTable() {
  const models = useQuery({ queryKey: ["models"], queryFn: api.models });
  return (
    <section className="card stack">
      <h2>Versiones registradas</h2>
      {models.isPending && <Loading />}
      <ErrorAlert error={models.error} />
      {models.data && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Versión</th>
                <th>Algoritmo</th>
                <th>Estado</th>
                <th className="numeric">ROC-AUC</th>
                <th className="numeric">F1 macro</th>
                <th>Entrenado</th>
              </tr>
            </thead>
            <tbody>
              {models.data.map((modelVersion) => (
                <tr key={modelVersion.id}>
                  <td>{modelVersion.version}</td>
                  <td>{modelVersion.algorithm}</td>
                  <td>
                    <StatusBadge status={modelVersion.status} />
                  </td>
                  <td className="numeric">{decimal(modelVersion.roc_auc)}</td>
                  <td className="numeric">{decimal(modelVersion.f1_macro)}</td>
                  <td>{dateTime(modelVersion.trained_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
