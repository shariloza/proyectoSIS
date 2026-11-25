/** Solo permite redirigir a rutas internas de la app (evita open redirects como "//evil.com"). */
export function safeInternalPath(candidate: unknown, fallback: string): string {
  if (typeof candidate !== "string") return fallback;
  const isInternal = candidate.startsWith("/") && !candidate.startsWith("//") && !candidate.includes("\\");
  return isInternal ? candidate : fallback;
}
