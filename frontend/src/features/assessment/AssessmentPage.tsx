import { useMutation } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { api, type StudentProfile } from "../../api/client";
import { SelectField } from "../../components/SelectField";
import { ErrorAlert } from "../../components/Status";
import { DIET, EDUCATION, FAMILY_HISTORY, GENDER, INITIAL_PROFILE, SCALES, SLEEP } from "./questions";
import { RiskResult } from "./RiskResult";

export function AssessmentPage() {
  const [profile, setProfile] = useState<StudentProfile>(INITIAL_PROFILE);
  const prediction = useMutation({ mutationFn: api.predict });

  const set = <K extends keyof StudentProfile>(key: K, value: StudentProfile[K]) =>
    setProfile((current) => ({ ...current, [key]: value }));

  const submit = (event: FormEvent) => {
    event.preventDefault();
    prediction.mutate(profile);
  };

  return (
    <div className="stack">
      <header className="page-header">
        <h1>¿Cómo estás llevando tus estudios?</h1>
        <p>
          Responde 11 preguntas breves sobre tu vida académica y tus hábitos. Un modelo de aprendizaje
          automático estima qué tanto se parecen tus respuestas a las de estudiantes que reportaron depresión.{" "}
          <strong>Es una herramienta académica, no un diagnóstico.</strong>
        </p>
      </header>

      <div className="grid grid-2" style={{ alignItems: "start" }}>
        <form className="card stack" onSubmit={submit} aria-describedby="privacidad">
          <h2>Tus respuestas</h2>
          <p id="privacidad" className="small muted">
            No pedimos tu nombre ni datos de contacto.
          </p>

          <div className="form-grid">
            <div className="field">
              <label htmlFor="age">Edad</label>
              <input
                id="age"
                type="number"
                min={18}
                max={60}
                required
                value={profile.age}
                onChange={(event) => set("age", Number(event.target.value))}
              />
            </div>
            <SelectField
              id="gender"
              label="Género"
              value={profile.gender}
              options={GENDER}
              onChange={(value) => set("gender", value)}
            />
            <SelectField
              id="education"
              label="Nivel de estudios"
              value={profile.education_level}
              options={EDUCATION}
              onChange={(value) => set("education_level", value)}
            />
            <div className="field">
              <label htmlFor="grade_point_average">Promedio académico (0 a 10)</label>
              <input
                id="grade_point_average"
                type="number"
                min={0.01}
                max={10}
                step={0.01}
                required
                value={profile.grade_point_average}
                onChange={(event) => set("grade_point_average", Number(event.target.value))}
              />
            </div>
          </div>

          {SCALES.map((scale) => (
            <fieldset key={scale.name} className="field">
              <legend>{scale.label}</legend>
              <div className="scale">
                {[1, 2, 3, 4, 5].map((value) => (
                  <label key={value}>
                    <input
                      type="radio"
                      name={scale.name}
                      value={value}
                      checked={profile[scale.name] === value}
                      onChange={() => set(scale.name, value)}
                    />
                    <span>{value}</span>
                  </label>
                ))}
              </div>
              <div className="row small muted" style={{ justifyContent: "space-between" }}>
                <span>1 · {scale.low}</span>
                <span>5 · {scale.high}</span>
              </div>
            </fieldset>
          ))}

          <div className="field">
            <label htmlFor="hours">
              Horas diarias de estudio o trabajo: <strong>{profile.work_study_hours} h</strong>
            </label>
            <input
              id="hours"
              type="range"
              min={0}
              max={12}
              value={profile.work_study_hours}
              onChange={(event) => set("work_study_hours", Number(event.target.value))}
            />
          </div>

          <div className="form-grid">
            <SelectField
              id="sleep"
              label="¿Cuántas horas duermes por noche?"
              value={profile.sleep_duration}
              options={SLEEP}
              onChange={(value) => set("sleep_duration", value)}
            />
            <SelectField
              id="diet"
              label="¿Cómo describirías tu alimentación?"
              value={profile.dietary_habits}
              options={DIET}
              onChange={(value) => set("dietary_habits", value)}
            />
            <SelectField
              id="family"
              label="¿Hay antecedentes de enfermedad mental en tu familia?"
              value={profile.family_history}
              options={FAMILY_HISTORY}
              onChange={(value) => set("family_history", value)}
            />
          </div>

          <ErrorAlert error={prediction.error} />
          <button className="button button-primary" type="submit" disabled={prediction.isPending}>
            {prediction.isPending ? "Calculando…" : "Estimar mi nivel de riesgo"}
          </button>
        </form>

        <div className="stack">
          {prediction.data ? (
            <RiskResult result={prediction.data} />
          ) : (
            <section className="card stack">
              <h2>¿Cómo funciona?</h2>
              <p>
                El modelo fue entrenado con respuestas de casi 28 000 estudiantes, siguiendo la metodología
                CRISP-ML(Q). Considera factores como la presión académica, el estrés financiero, el sueño y la
                alimentación.
              </p>
              <p className="muted small">
                Por razones éticas, el modelo <strong>no</strong> usa preguntas sobre pensamientos suicidas.
              </p>
            </section>
          )}
          <section className="card alert-info stack" aria-labelledby="ayuda">
            <h2 id="ayuda">¿Necesitas hablar con alguien?</h2>
            <p>
              Si sientes malestar emocional, acércate al servicio de bienestar o psicología de tu universidad,
              o a un profesional de la salud mental. Si estás en peligro, comunícate con los servicios de
              emergencia de tu país.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
