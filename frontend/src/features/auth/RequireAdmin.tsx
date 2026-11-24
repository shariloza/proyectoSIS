import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "./useAuth";

/** Solo evita mostrar pantallas vacías: la autorización real la aplica la API en cada request. */
export function RequireAdmin() {
  const { isAdmin } = useAuth();
  const location = useLocation();
  return isAdmin ? <Outlet /> : <Navigate to="/login" replace state={{ from: location.pathname }} />;
}
