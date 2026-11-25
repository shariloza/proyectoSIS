/**
 * Único punto de comunicación con la API. Los tipos vienen de `schema.d.ts`,
 * generado desde docs/openapi.json (`npm run gen:api`).
 */
import type { components } from "./schema";

export type Schemas = components["schemas"];
export type StudentProfile = Schemas["StudentProfileIn"];
export type Prediction = Schemas["PredictionOut"];
export type PredictionPage = Schemas["PredictionPage"];
export type ModelDetail = Schemas["ModelDetail"];
export type ModelSummary = Schemas["ModelSummary"];
export type Dataset = Schemas["DatasetOut"];
export type TrainingJob = Schemas["TrainingJobOut"];

const BASE_URL = "/api/v1";
const TOKEN_KEY = "depression-risk.admin-token";
export const SESSION_EXPIRED_EVENT = "auth:expired";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly details: unknown = null,
    readonly requestId: string | null = null,
  ) {
    super(message);
  }
}

/** El token vive en sessionStorage: se pierde al cerrar la pestaña. */
export const tokenStore = {
  get(): string | null {
    try {
      return sessionStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },
  set(token: string): void {
    try {
      sessionStorage.setItem(TOKEN_KEY, token);
    } catch {
      /* almacenamiento no disponible: la sesión dura lo que la página */
    }
  },
  clear(): void {
    try {
      sessionStorage.removeItem(TOKEN_KEY);
    } catch {
      /* nada que limpiar */
    }
  },
};

interface RequestOptions {
  json?: unknown;
  form?: FormData;
  query?: Record<string, string | number | undefined>;
}

async function request<T>(method: string, path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers({ Accept: "application/json" });
  const token = tokenStore.get();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let body: BodyInit | undefined;
  if (options.json !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(options.json);
  } else if (options.form) {
    body = options.form;
  }

  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(options.query ?? {})) {
    if (value !== undefined) query.set(key, String(value));
  }
  const url = `${BASE_URL}${path}${query.size ? `?${query}` : ""}`;

  let response: Response;
  try {
    response = await fetch(url, { method, headers, body });
  } catch {
    throw new ApiError(0, "NETWORK_ERROR", "No se pudo conectar con el servidor.");
  }

  if (!response.ok) throw await toApiError(response, Boolean(token));
  return (await response.json()) as T;
}

async function toApiError(response: Response, hadToken: boolean): Promise<ApiError> {
  if (response.status === 401 && hadToken) {
    tokenStore.clear();
    window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
  }
  try {
    const { error } = (await response.json()) as { error: Schemas["ErrorBody"] };
    return new ApiError(response.status, error.code, error.message, error.details, error.request_id ?? null);
  } catch {
    return new ApiError(response.status, "HTTP_ERROR", `Error ${response.status} del servidor.`);
  }
}

export const api = {
  live: () => request<Schemas["HealthOut"]>("GET", "/health/live"),
  ready: () => request<Schemas["HealthOut"]>("GET", "/health/ready"),

  login: (email: string, password: string) =>
    request<Schemas["TokenOut"]>("POST", "/auth/login", { json: { email, password } }),

  predict: (profile: StudentProfile) => request<Prediction>("POST", "/predictions", { json: profile }),
  history: (page: number, size: number, modelVersionId?: string) =>
    request<PredictionPage>("GET", "/predictions", {
      query: { page, size, model_version_id: modelVersionId },
    }),

  activeModel: () => request<ModelDetail>("GET", "/models/active"),
  models: () => request<ModelSummary[]>("GET", "/models"),
  model: (id: string) => request<ModelDetail>("GET", `/models/${id}`),
  activate: (id: string) => request<ModelDetail>("POST", `/models/${id}/activate`),
  rollback: () => request<ModelDetail>("POST", "/models/rollback"),

  datasets: () => request<Dataset[]>("GET", "/datasets"),
  uploadDataset: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<Dataset>("POST", "/datasets", { form });
  },

  trainingJobs: () => request<TrainingJob[]>("GET", "/training-jobs"),
  trainingJob: (id: string) => request<TrainingJob>("GET", `/training-jobs/${id}`),
  enqueueTraining: (datasetId: string) =>
    request<TrainingJob>("POST", "/training-jobs", { json: { dataset_id: datasetId } }),
};
