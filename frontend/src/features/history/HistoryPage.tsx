import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../../api/client";
import { ErrorAlert, Loading } from "../../components/Status";
import { dateTime, percent, RISK_LABEL } from "../../lib/format";

const PAGE_SIZE = 15;

const INPUT_LABELS: Record<string, string> = {
  age: "Edad",
  gender: "Género",
  grade_point_average: "Promedio",
  academic_pressure: "Presión académica",
  study_satisfaction: "Satisfacción",
  work_study_hours: "Horas estudio",
  financial_stress: "Estrés financiero",
  sleep_duration: "Sueño",
  dietary_habits: "Alimentación",
  education_level: "Estudios",
  family_history: "Antecedentes",
};

export function HistoryPage() {
  const [page, setPage] = useState(1);
  const history = useQuery({
    queryKey: ["predictions", page],
    queryFn: () => api.history(page, PAGE_SIZE),
    placeholderData: keepPreviousData,
  });
  const totalPages = history.data ? Math.max(1, Math.ceil(history.data.total / PAGE_SIZE)) : 1;

  return (
    <div className="stack">
      <header className="page-header">
        <h1>Historial de predicciones</h1>
        <p>
          Datos enviados, resultado y versión del modelo que lo produjo. Información sensible: acceso solo
          para administración.
        </p>
      </header>
      <section className="card">
        {history.isPending && <Loading />}
        <ErrorAlert error={history.error} />
        {history.data && history.data.items.length === 0 && (
          <p className="muted">Todavía no hay predicciones.</p>
        )}
        {history.data && history.data.items.length > 0 && (
          <>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Datos enviados</th>
                    <th>Resultado</th>
                    <th className="numeric">Probabilidad</th>
                    <th>Modelo</th>
                  </tr>
                </thead>
                <tbody>
                  {history.data.items.map((item) => (
                    <tr key={item.id}>
                      <td>{dateTime(item.created_at)}</td>
                      <td className="small">
                        {Object.entries(item.input)
                          .map(([key, value]) => `${INPUT_LABELS[key] ?? key}: ${String(value)}`)
                          .join(" · ")}
                      </td>
                      <td>
                        <span className={`badge badge-${item.risk_band}`}>{RISK_LABEL[item.risk_band]}</span>
                      </td>
                      <td className="numeric">{percent(item.probability)}</td>
                      <td>{item.model_version}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="pager">
              <span className="muted small">
                {history.data.total} predicciones · página {page} de {totalPages}
              </span>
              <div className="row">
                <button
                  className="button button-secondary"
                  disabled={page <= 1}
                  onClick={() => setPage((current) => current - 1)}
                >
                  ← Anterior
                </button>
                <button
                  className="button button-secondary"
                  disabled={page >= totalPages}
                  onClick={() => setPage((current) => current + 1)}
                >
                  Siguiente →
                </button>
              </div>
            </div>
          </>
        )}
      </section>
    </div>
  );
}
