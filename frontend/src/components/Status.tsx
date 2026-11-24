import { ApiError } from "../api/client";
import { STATUS_LABEL } from "../lib/format";

export function Loading({ label = "Cargando…" }: { label?: string }) {
  return (
    <div className="row muted" role="status">
      <span className="spinner" aria-hidden="true" />
      {label}
    </div>
  );
}

/** Muestra el mensaje del backend y, si los hay, los detalles de validación. */
export function ErrorAlert({ error }: { error: unknown }) {
  if (!error) return null;
  const apiError = error instanceof ApiError ? error : null;
  const message = apiError?.message ?? "Ocurrió un error inesperado.";
  const details = Array.isArray(apiError?.details) ? (apiError.details as unknown[]) : [];

  return (
    <div className="alert alert-error" role="alert">
      <strong>{message}</strong>
      {details.length > 0 && (
        <ul>
          {details.map((detail, index) => (
            <li key={index}>{describe(detail)}</li>
          ))}
        </ul>
      )}
      {apiError?.requestId && <div className="small muted">Referencia: {apiError.requestId}</div>}
    </div>
  );
}

function describe(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (detail && typeof detail === "object" && "message" in detail) {
    const { field, message } = detail as { field?: string; message: string };
    return field ? `${field}: ${message}` : message;
  }
  return JSON.stringify(detail);
}

export function StatusBadge({ status }: { status: string }) {
  return <span className={`badge badge-${status}`}>{STATUS_LABEL[status] ?? status}</span>;
}
