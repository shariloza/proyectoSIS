import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, Navigate, RouterProvider } from "react-router-dom";

import { ApiError } from "./api/client";
import { Layout } from "./components/Layout";
import { AssessmentPage } from "./features/assessment/AssessmentPage";
import { AuthProvider } from "./features/auth/AuthProvider";
import { LoginPage } from "./features/auth/LoginPage";
import { RequireAdmin } from "./features/auth/RequireAdmin";
import "./styles.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Los errores 4xx no se reintentan: repetir no cambia la respuesta.
      retry: (failures, error) => !(error instanceof ApiError && error.status < 500) && failures < 2,
      refetchOnWindowFocus: false,
    },
  },
});

const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { index: true, element: <AssessmentPage /> },
      // Las pantallas con gráficas y de administración se cargan bajo demanda.
      {
        path: "metricas",
        lazy: async () => ({ Component: (await import("./features/metrics/MetricsPage")).MetricsPage }),
      },
      { path: "login", element: <LoginPage /> },
      {
        path: "admin",
        element: <RequireAdmin />,
        children: [
          {
            path: "historial",
            lazy: async () => ({ Component: (await import("./features/history/HistoryPage")).HistoryPage }),
          },
          {
            path: "datasets",
            lazy: async () => ({
              Component: (await import("./features/datasets/DatasetsPage")).DatasetsPage,
            }),
          },
          {
            path: "modelos",
            lazy: async () => ({
              Component: (await import("./features/training/TrainingPage")).TrainingPage,
            }),
          },
        ],
      },
      { path: "*", element: <Navigate to="/" replace /> },
    ],
  },
]);

const container = document.getElementById("root");
if (!container) throw new Error("No se encontró el elemento #root");

createRoot(container).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </QueryClientProvider>
  </StrictMode>,
);
