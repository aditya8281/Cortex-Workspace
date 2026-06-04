import { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AppShell } from "@/components/layout/AppShell";

const DashboardPage = lazy(() =>
  import("@/pages/DashboardPage").then((m) => ({ default: m.DashboardPage })),
);
const ChatPage = lazy(() => import("@/pages/ChatPage").then((m) => ({ default: m.ChatPage })));
const SyncPage = lazy(() => import("@/pages/SyncPage").then((m) => ({ default: m.SyncPage })));
const RepositoriesPage = lazy(() =>
  import("@/pages/RepositoriesPage").then((m) => ({ default: m.RepositoriesPage })),
);
const RepositoryDetailPage = lazy(() =>
  import("@/pages/RepositoryDetailPage").then((m) => ({ default: m.RepositoryDetailPage })),
);
const MemoryPage = lazy(() => import("@/pages/MemoryPage").then((m) => ({ default: m.MemoryPage })));
const KnowledgeGraphPage = lazy(() =>
  import("@/pages/KnowledgeGraphPage").then((m) => ({ default: m.KnowledgeGraphPage })),
);
const ActivityPage = lazy(() =>
  import("@/pages/ActivityPage").then((m) => ({ default: m.ActivityPage })),
);
const SettingsPage = lazy(() =>
  import("@/pages/SettingsPage").then((m) => ({ default: m.SettingsPage })),
);
const ProjectsPage = lazy(() =>
  import("@/pages/ProjectsPage").then((m) => ({ default: m.ProjectsPage })),
);
const ProfilePage = lazy(() =>
  import("@/pages/ProfilePage").then((m) => ({ default: m.ProfilePage })),
);
const ModelsPage = lazy(() =>
  import("@/pages/ModelsPage").then((m) => ({ default: m.ModelsPage })),
);
const MarketplacePage = lazy(() =>
  import("@/pages/MarketplacePage").then((m) => ({ default: m.MarketplacePage })),
);
const ModelDiscoveryPage = lazy(() =>
  import("@/pages/ModelDiscoveryPage").then((m) => ({ default: m.ModelDiscoveryPage })),
);
const PerformancePage = lazy(() =>
  import("@/pages/PerformancePage").then((m) => ({ default: m.PerformancePage })),
);



const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function PageLoader() {
  return (
    <div className="flex h-full min-h-[200px] items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-cortex-accent border-t-transparent" />
        <p className="text-sm text-cortex-muted">Loading…</p>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route
              index
              element={
                <Suspense fallback={<PageLoader />}>
                  <DashboardPage />
                </Suspense>
              }
            />
            <Route
              path="chat"
              element={
                <Suspense fallback={<PageLoader />}>
                  <ChatPage />
                </Suspense>
              }
            />
            <Route
              path="profile"
              element={
                <Suspense fallback={<PageLoader />}>
                  <ProfilePage />
                </Suspense>
              }
            />
            <Route
              path="sync"
              element={
                <Suspense fallback={<PageLoader />}>
                  <SyncPage />
                </Suspense>
              }
            />
            <Route
              path="repositories"
              element={
                <Suspense fallback={<PageLoader />}>
                  <RepositoriesPage />
                </Suspense>
              }
            />
            <Route
              path="repositories/*"
              element={
                <Suspense fallback={<PageLoader />}>
                  <RepositoryDetailPage />
                </Suspense>
              }
            />
            <Route
              path="memory"
              element={
                <Suspense fallback={<PageLoader />}>
                  <MemoryPage />
                </Suspense>
              }
            />
            <Route
              path="graph"
              element={
                <Suspense fallback={<PageLoader />}>
                  <KnowledgeGraphPage />
                </Suspense>
              }
            />
            <Route
              path="activity"
              element={
                <Suspense fallback={<PageLoader />}>
                  <ActivityPage />
                </Suspense>
              }
            />
            <Route
              path="settings"
              element={
                <Suspense fallback={<PageLoader />}>
                  <SettingsPage />
                </Suspense>
              }
            />
            <Route
              path="models"
              element={
                <Suspense fallback={<PageLoader />}>
                  <ModelsPage />
                </Suspense>
              }
            />
            <Route
              path="models/discover"
              element={
                <Suspense fallback={<PageLoader />}>
                  <ModelDiscoveryPage />
                </Suspense>
              }
            />
            <Route
              path="marketplace"
              element={
                <Suspense fallback={<PageLoader />}>
                  <MarketplacePage />
                </Suspense>
              }
            />
            <Route
              path="performance"
              element={
                <Suspense fallback={<PageLoader />}>
                  <PerformancePage />
                </Suspense>
              }
            />
            <Route
              path="projects"
              element={
                <Suspense fallback={<PageLoader />}>
                  <ProjectsPage />
                </Suspense>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
