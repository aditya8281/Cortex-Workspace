import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AppShell } from "@/components/layout/AppShell";
import { DashboardPage } from "@/pages/DashboardPage";
import { ChatPage } from "@/pages/ChatPage";
import { SyncPage } from "@/pages/SyncPage";
import { RepositoriesPage } from "@/pages/RepositoriesPage";
import { RepositoryDetailPage } from "@/pages/RepositoryDetailPage";
import { MemoryPage } from "@/pages/MemoryPage";
import { KnowledgeGraphPage } from "@/pages/KnowledgeGraphPage";
import { ActivityPage } from "@/pages/ActivityPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { ProjectsPage } from "@/pages/ProjectsPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<DashboardPage />} />
            <Route path="chat" element={<ChatPage />} />
            <Route path="sync" element={<SyncPage />} />
            <Route path="repositories" element={<RepositoriesPage />} />
            <Route path="repositories/:path" element={<RepositoryDetailPage />} />
            <Route path="memory" element={<MemoryPage />} />
            <Route path="graph" element={<KnowledgeGraphPage />} />
            <Route path="activity" element={<ActivityPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="projects" element={<ProjectsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
