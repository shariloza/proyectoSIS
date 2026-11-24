import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { api, type ModelDetail, type TrainingJob } from "../../api/client";
import { ErrorAlert, Loading, StatusBadge } from "../../components/Status";
import { dateTime, decimal } from "../../lib/format";
import { AcceptanceTable } from "../metrics/MetricsPage";
import { testMetrics } from "../metrics/evaluation";

const POLL_MS = 3000;
const IN_PROGRESS = new Set(["PENDING", "RUNNING"]);
const ACTIVATABLE = new Set(["APPROVED", "RETIRED"]);

export function TrainingPage() {
  const queryClient = useQueryClient();
  const refreshModels = () => queryClient.invalidateQueries({ queryKey: ["models"] });

  const datasets = useQuery({ queryKey: ["datasets"], queryFn: api.datasets });
  const jobs = useQuery({
    queryKey: ["training-jobs"],
    queryFn: api.trainingJobs,
    // Mientras haya un trabajo en curso se consulta su estado periódicamente.
    refetchInterval: (query) =>
      query.state.data?.some((job) => IN_PROGRESS.has(job.status)) ? POLL_MS : false,
  });
  const [datasetId, setDatasetId] = useState("");
  const enqueue = useMutation({
    mutationFn: api.enqueueTraining,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["training-jobs"] }),
  });

  const latest = jobs.data?.[0];
  const submit = (event: FormEvent) => {
    event.preventDefault();
    const chosen = datasetId || datasets.data?.[0]?.id;
    if (chosen) enqueue.mutate(chosen);
  };

  return (
    <div className="stack">
      <header className="page-header">
        <h1>Re-entrenamiento del modelo</h1>
        <p>
          El entrenamiento corre en segundo plano. El modelo resultante queda como <strong>candidato</strong>:
          solo se activa si cumple los criterios de aceptación y tú lo confirmas. Siempre puedes volver a la
          versión anterior.
        </p>
      </header>

      <form className="card stack" onSubmit={submit}>
        <h2>1. Lanzar un re-entrenamiento</h2>
        {datasets.isPending && <Loading />}
        <ErrorAlert error={datasets.error} />
        {datasets.data && (
          <div className="field">
            <label htmlFor="dataset">Dataset</label>
            <select id="dataset" value={datasetId} onChange={(e) => setDatasetId(e.target.value)}>
              {datasets.data.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.original_filename} · {d.row_count.toLocaleString("es")} filas · {dateTime(d.created_at)}
                </option>
              ))}
            </select>
          </div>
        )}
        <ErrorAlert error={enqueue.error} />
        <button
          className="btn btn-primary"
          type="submit"
          disabled={enqueue.isPending || !datasets.data?.length}
        >
          {enqueue.isPending ? "Enviando…" : "Re-entrenar"}
        </button>
      </form>

      <section className="card stack" aria-live="polite">
        <h2>2. Estado del último trabajo</h2>
        {jobs.isPending && <Loading />}
        <ErrorAlert error={jobs.error} />
        {jobs.data && !latest && <p className="muted">Aún no se ha solicitado ningún re-entrenamiento.</p>}
        {latest && <JobStatus job={latest} />}
      </section>

      {latest?.result_model && (
        <CandidateComparison candidateId={latest.result_model.id} onChanged={refreshModels} />
      )}

      <Versions onChanged={refreshModels} />
    </div>
  );
}

function JobStatus({ job }: { job: TrainingJob }) {
  return (
    <div className="stack">
      <div className="row">
        <StatusBadge status={job.status} />
        {IN_PROGRESS.has(job.status) && <Loading label="El worker está entrenando y evaluando modelos…" />}
      </div>
      <dl className="grid grid-3 small" style={{ margin: 0 }}>
        <div>
          <dt className="muted">Solicitado</dt>
          <dd>{dateTime(job.created_at)}</dd>
        </div>
        <div>
          <dt className="muted">Inicio</dt>
          <dd>{dateTime(job.started_at)}</dd>
        </div>
        <div>
          <dt className="muted">Fin</dt>
          <dd>{dateTime(job.finished_at)}</dd>
        </div>
      </dl>
      {job.error_message && (
        <div className="alert alert-error" role="alert">
          {job.error_message}
        </div>
      )}
    </div>
  );
}

function CandidateComparison({ candidateId, onChanged }: { candidateId: string; onChanged: () => void }) {
  const candidate = useQuery({ queryKey: ["models", candidateId], queryFn: () => api.model(candidateId) });
  const active = useQuery({ queryKey: ["models", "active"], queryFn: api.activeModel });
  const activate = useMutation({ mutationFn: api.activate, onSuccess: onChanged });

  if (candidate.isPending || active.isPending) return <Loading />;
  if (candidate.error || active.error) return <ErrorAlert error={candidate.error ?? active.error} />;

  const isActive = candidate.data.id === active.data.id;
  return (
    <section className="card stack">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h2>
          3. Candidato {candidate.data.version} frente al activo {active.data.version}
        </h2>
        <StatusBadge status={candidate.data.status} />
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Métrica (test)</th>
              <th className="num">Activo {active.data.version}</th>
              <th className="num">Candidato {candidate.data.version}</th>
              <th className="num">Diferencia</th>
            </tr>
          </thead>
          <tbody>
            {comparisonRows(active.data, candidate.data).map((row) => (
              <tr key={row.label}>
                <td>{row.label}</td>
                <td className="num">{decimal(row.active)}</td>
                <td className="num">{decimal(row.candidate)}</td>
                <td className={`num check ${row.candidate >= row.active ? "check-ok" : "check-fail"}`}>
                  {row.candidate >= row.active ? "+" : ""}
                  {decimal(row.candidate - row.active)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <details>
        <summary>Criterios de aceptación del candidato</summary>
        <AcceptanceTable model={candidate.data} />
      </details>
      <ErrorAlert error={activate.error} />
      {activate.isSuccess && (
        <div className="alert alert-success" role="status">
          El modelo {activate.data.version} está activo. Las nuevas predicciones lo usarán.
        </div>
      )}
      {!isActive && (
        <button
          className="btn btn-primary"
          disabled={!ACTIVATABLE.has(candidate.data.status) || activate.isPending}
          onClick={() => {
            if (
              window.confirm(
                `¿Activar el modelo ${candidate.data.version}? El modelo actual quedará retirado.`,
              )
            ) {
              activate.mutate(candidate.data.id);
            }
          }}
        >
          Activar {candidate.data.version}
        </button>
      )}
      {candidate.data.status === "REJECTED" && (
        <p className="small muted">
          Este candidato no cumplió los criterios de aceptación y no puede activarse.
        </p>
      )}
    </section>
  );
}

function comparisonRows(active: ModelDetail, candidate: ModelDetail) {
  const a = testMetrics(active);
  const c = testMetrics(candidate);
  return [
    { label: "ROC-AUC", active: a.roc_auc, candidate: c.roc_auc },
    { label: "F1 macro", active: a.f1_macro, candidate: c.f1_macro },
    { label: "Recall (con depresión)", active: a.per_class["1"].recall, candidate: c.per_class["1"].recall },
    {
      label: "Precisión (con depresión)",
      active: a.per_class["1"].precision,
      candidate: c.per_class["1"].precision,
    },
  ];
}

function Versions({ onChanged }: { onChanged: () => void }) {
  const models = useQuery({ queryKey: ["models"], queryFn: api.models });
  const activate = useMutation({ mutationFn: api.activate, onSuccess: onChanged });
  const rollback = useMutation({ mutationFn: api.rollback, onSuccess: onChanged });

  return (
    <section className="card stack">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h2>Versiones y rollback</h2>
        <button
          className="btn btn-secondary"
          disabled={rollback.isPending}
          onClick={() => window.confirm("¿Volver a la versión activa anterior?") && rollback.mutate()}
        >
          ↩ Volver a la versión anterior
        </button>
      </div>
      <ErrorAlert error={activate.error ?? rollback.error} />
      {rollback.isSuccess && (
        <div className="alert alert-success" role="status">
          Rollback realizado: {rollback.data.version} vuelve a estar activo.
        </div>
      )}
      {models.isPending && <Loading />}
      <ErrorAlert error={models.error} />
      {models.data && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Versión</th>
                <th>Estado</th>
                <th className="num">ROC-AUC</th>
                <th>Entrenado</th>
                <th>Acción</th>
              </tr>
            </thead>
            <tbody>
              {models.data.map((m) => (
                <tr key={m.id}>
                  <td>
                    {m.version} <span className="small muted">{m.algorithm}</span>
                  </td>
                  <td>
                    <StatusBadge status={m.status} />
                  </td>
                  <td className="num">{decimal(m.roc_auc)}</td>
                  <td>{dateTime(m.trained_at)}</td>
                  <td>
                    {ACTIVATABLE.has(m.status) && (
                      <button
                        className="btn btn-secondary"
                        disabled={activate.isPending}
                        onClick={() => window.confirm(`¿Activar ${m.version}?`) && activate.mutate(m.id)}
                      >
                        Activar
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
