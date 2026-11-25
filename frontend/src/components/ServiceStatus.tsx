import { useQuery } from "@tanstack/react-query";

import { api, ApiError } from "../api/client";

const REFRESH_MILLISECONDS = 30_000;

/** Estado del servicio de IA según /health/live (proceso) y /health/ready (base de datos y modelo). */
export function ServiceStatus() {
  const live = useQuery({
    queryKey: ["health", "live"],
    queryFn: api.live,
    refetchInterval: REFRESH_MILLISECONDS,
    retry: false,
  });
  const ready = useQuery({
    queryKey: ["health", "ready"],
    queryFn: api.ready,
    refetchInterval: REFRESH_MILLISECONDS,
    retry: false,
  });

  if (live.isPending || ready.isPending) return null;

  const online = live.isSuccess;
  const detail = ready.isSuccess
    ? `base de datos y modelo ${ready.data.model_version} listos`
    : ready.error instanceof ApiError
      ? ready.error.message
      : "sin respuesta";

  return (
    <p className="service-status" role="status">
      <span
        className={`status-dot ${online && ready.isSuccess ? "status-ok" : "status-fail"}`}
        aria-hidden="true"
      />
      Servicio de IA {online ? "en línea" : "sin conexión"} · {detail}
    </p>
  );
}
