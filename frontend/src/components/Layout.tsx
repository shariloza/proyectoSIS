import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../features/auth/useAuth";
import { ServiceStatus } from "./ServiceStatus";

const PUBLIC_LINKS = [
  { to: "/", label: "Evaluación" },
  { to: "/metricas", label: "Métricas del modelo" },
];

const ADMIN_LINKS = [
  { to: "/admin/historial", label: "Historial" },
  { to: "/admin/datasets", label: "Datasets" },
  { to: "/admin/modelos", label: "Re-entrenamiento" },
];

export function Layout() {
  const { isAdmin, logout } = useAuth();
  const links = isAdmin ? [...PUBLIC_LINKS, ...ADMIN_LINKS] : PUBLIC_LINKS;

  return (
    <>
      <a className="skip-link" href="#contenido">
        Saltar al contenido
      </a>
      <header className="topbar">
        <div className="topbar-inner">
          <NavLink to="/" className="brand">
            <span className="brand-mark" aria-hidden="true">
              ♥
            </span>
            Bienestar Estudiantil
          </NavLink>
          <nav className="nav" aria-label="Principal">
            {links.map((link) => (
              <NavLink key={link.to} to={link.to} end={link.to === "/"}>
                {link.label}
              </NavLink>
            ))}
          </nav>
          {isAdmin ? (
            <button className="button button-secondary" onClick={logout}>
              Cerrar sesión
            </button>
          ) : (
            <NavLink to="/login" className="button button-secondary">
              Administración
            </NavLink>
          )}
        </div>
      </header>
      <main id="contenido" className="main">
        <Outlet />
      </main>
      <footer className="footer">
        <ServiceStatus />
        Proyecto académico TALLERSISIA · Estimación estadística, no diagnóstico clínico.
      </footer>
    </>
  );
}
