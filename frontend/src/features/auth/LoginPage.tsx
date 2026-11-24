import { useMutation } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { ErrorAlert } from "../../components/Status";
import { useAuth } from "./useAuth";

export function LoginPage() {
  const { isAdmin, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const target = (location.state as { from?: string } | null)?.from ?? "/admin/historial";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const attempt = useMutation({
    mutationFn: () => login(email, password),
    onSuccess: () => navigate(target, { replace: true }),
  });

  if (isAdmin) return <Navigate to={target} replace />;

  const submit = (event: FormEvent) => {
    event.preventDefault();
    attempt.mutate();
  };

  return (
    <div style={{ maxWidth: 420, margin: "2rem auto" }}>
      <form className="card stack" onSubmit={submit}>
        <h1>Acceso de administración</h1>
        <p className="muted small">
          Para el historial de predicciones, la carga de datos y el re-entrenamiento del modelo.
        </p>
        <div className="field">
          <label htmlFor="email">Correo</label>
          <input
            id="email"
            type="email"
            autoComplete="username"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="password">Contraseña</label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <ErrorAlert error={attempt.error} />
        <button className="btn btn-primary" type="submit" disabled={attempt.isPending}>
          {attempt.isPending ? "Ingresando…" : "Ingresar"}
        </button>
      </form>
    </div>
  );
}
