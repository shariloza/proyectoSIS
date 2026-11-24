import type { Prediction } from "../../api/client";
import { dateTime, percent, RISK_LABEL } from "../../lib/format";

const GUIDANCE = {
  LOW: "Tus respuestas se parecen a las de estudiantes que no reportaron depresión. Cuidar el sueño, la alimentación y tus vínculos sigue siendo importante.",
  MODERATE:
    "Algunas de tus respuestas se asocian con mayor riesgo. Conversar con alguien de confianza o con el servicio de bienestar de tu universidad puede ayudarte.",
  HIGH: "Tus respuestas se parecen a las de estudiantes que reportaron depresión. Te recomendamos buscar apoyo de un profesional de la salud mental.",
} as const;

export function RiskResult({ result }: { result: Prediction }) {
  const band = result.risk_band;
  return (
    <section className={`card result result-${band} stack`} aria-live="polite" aria-labelledby="resultado">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h2 id="resultado">Resultado de la estimación</h2>
        <span className={`badge badge-${band}`}>{RISK_LABEL[band]}</span>
      </div>

      <div>
        <div className="big-number">{percent(result.probability)}</div>
        <div className="muted small">Probabilidad estimada por el modelo {result.model_version}</div>
        <div
          className="meter"
          role="meter"
          aria-label="Probabilidad estimada"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={Math.round(result.probability * 100)}
        >
          <span className="meter-marker" style={{ left: `${result.probability * 100}%` }} />
        </div>
        <div className="meter-scale" aria-hidden="true">
          <span>Bajo</span>
          <span>Moderado (40 %)</span>
          <span>Alto (70 %)</span>
        </div>
      </div>

      <p>{GUIDANCE[band]}</p>

      <div className="disclaimer" role="note">
        <strong>Importante: </strong>
        {result.disclaimer}
      </div>
      <p className="small muted">
        Registrado el {dateTime(result.created_at)}. No se guarda tu nombre ni ningún dato que te identifique.
      </p>
    </section>
  );
}
