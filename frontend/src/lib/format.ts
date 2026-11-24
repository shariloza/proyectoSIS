const percentFormat = new Intl.NumberFormat("es", { style: "percent", maximumFractionDigits: 1 });
const decimalFormat = new Intl.NumberFormat("es", { minimumFractionDigits: 3, maximumFractionDigits: 3 });
const dateFormat = new Intl.DateTimeFormat("es", { dateStyle: "medium", timeStyle: "short" });

export const percent = (value: number) => percentFormat.format(value);
export const decimal = (value: number) => decimalFormat.format(value);
export const dateTime = (iso: string | null | undefined) => (iso ? dateFormat.format(new Date(iso)) : "—");

export const RISK_LABEL = { LOW: "Riesgo bajo", MODERATE: "Riesgo moderado", HIGH: "Riesgo alto" } as const;

export const STATUS_LABEL: Record<string, string> = {
  CANDIDATE: "Candidato",
  APPROVED: "Aprobado",
  REJECTED: "Rechazado",
  ACTIVE: "Activo",
  RETIRED: "Retirado",
  PENDING: "En cola",
  RUNNING: "Entrenando",
  SUCCEEDED: "Terminado",
  FAILED: "Fallido",
  TIMED_OUT: "Tiempo agotado",
};
