import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { api } from "../../api/client";
import { ErrorAlert, Loading } from "../../components/Status";
import { dateTime } from "../../lib/format";

const MAX_MB = 10;

export function DatasetsPage() {
  const queryClient = useQueryClient();
  const datasets = useQuery({ queryKey: ["datasets"], queryFn: api.datasets });
  const [file, setFile] = useState<File | null>(null);
  const [clientError, setClientError] = useState<string | null>(null);
  const upload = useMutation({
    mutationFn: api.uploadDataset,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["datasets"] }),
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!file) return;
    // Validación rápida para la UX; la validación completa la hace la API.
    if (!file.name.toLowerCase().endsWith(".csv")) return setClientError("El archivo debe ser .csv.");
    if (file.size > MAX_MB * 1024 * 1024) return setClientError(`El archivo supera ${MAX_MB} MB.`);
    setClientError(null);
    upload.mutate(file);
  };

  return (
    <div className="stack">
      <header className="page-header">
        <h1>Datasets de entrenamiento</h1>
        <p>
          Sube un CSV con las mismas columnas que el dataset original. Antes de aceptarlo se valida su
          formato, tamaño, columnas, tipos y valores permitidos, y se guarda versionado con su huella SHA-256.
        </p>
      </header>

      <form className="card stack" onSubmit={submit}>
        <h2>Subir archivo</h2>
        <div className="field">
          <label htmlFor="file">Archivo CSV (máx. {MAX_MB} MB)</label>
          <input
            id="file"
            type="file"
            accept=".csv,text/csv"
            onChange={(event) => {
              setFile(event.target.files?.[0] ?? null);
              upload.reset();
            }}
          />
        </div>
        {clientError && (
          <div className="alert alert-error" role="alert">
            {clientError}
          </div>
        )}
        <ErrorAlert error={upload.error} />
        {upload.data && (
          <div className="alert alert-success" role="status">
            <strong>Archivo aceptado:</strong> {upload.data.row_count.toLocaleString("es")} filas,{" "}
            {upload.data.validation_report.kept_rows as number} válidas para entrenar.{" "}
            <Link to="/admin/modelos">Usarlo para re-entrenar →</Link>
          </div>
        )}
        <button className="button button-primary" type="submit" disabled={!file || upload.isPending}>
          {upload.isPending ? "Validando…" : "Subir y validar"}
        </button>
      </form>

      <section className="card stack">
        <h2>Archivos registrados</h2>
        {datasets.isPending && <Loading />}
        <ErrorAlert error={datasets.error} />
        {datasets.data && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Archivo</th>
                  <th className="numeric">Filas</th>
                  <th className="numeric">Tamaño</th>
                  <th>SHA-256</th>
                  <th>Subido</th>
                </tr>
              </thead>
              <tbody>
                {datasets.data.map((dataset) => (
                  <tr key={dataset.id}>
                    <td>{dataset.original_filename}</td>
                    <td className="numeric">{dataset.row_count.toLocaleString("es")}</td>
                    <td className="numeric">{(dataset.size_bytes / 1024 / 1024).toFixed(2)} MB</td>
                    <td className="small">
                      <code title={dataset.sha256}>{dataset.sha256.slice(0, 12)}…</code>
                    </td>
                    <td>{dateTime(dataset.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
