import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import { api, SESSION_EXPIRED_EVENT, tokenStore } from "../../api/client";
import { AuthContext } from "./useAuth";

/**
 * Solo guarda si hay un token. Quién es administrador lo decide SIEMPRE el backend:
 * si el token no es válido, la API responde 401 y la sesión se cierra aquí.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAdmin, setIsAdmin] = useState(() => tokenStore.get() !== null);

  useEffect(() => {
    const expire = () => setIsAdmin(false);
    window.addEventListener(SESSION_EXPIRED_EVENT, expire);
    return () => window.removeEventListener(SESSION_EXPIRED_EVENT, expire);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await api.login(email, password);
    tokenStore.set(access_token);
    setIsAdmin(true);
  }, []);

  const logout = useCallback(() => {
    tokenStore.clear();
    setIsAdmin(false);
  }, []);

  const value = useMemo(() => ({ isAdmin, login, logout }), [isAdmin, login, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
