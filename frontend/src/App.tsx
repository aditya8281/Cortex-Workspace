import { lazy, Suspense, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MainLayout } from "@/components/layout/MainLayout";

// Pages - lazy loaded
const HomePage = lazy(() =>
  import("@/pages/HomePage").then((m) => ({ default: m.HomePage })),
);
const MarketplacePage = lazy(() =>
  import("@/pages/MarketplacePage").then((m) => ({ default: m.MarketplacePage })),
);
const ChatPage = lazy(() => import("@/pages/ChatPage").then((m) => ({ default: m.ChatPage })));
const SyncPage = lazy(() => import("@/pages/SyncPage").then((m) => ({ default: m.SyncPage })));
const MemoryPage = lazy(() => import("@/pages/MemoryPage").then((m) => ({ default: m.MemoryPage })));
const SettingsPage = lazy(() =>
  import("@/pages/SettingsPage").then((m) => ({ default: m.SettingsPage })),
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

type TabId = 'home' | 'marketplace' | 'workspaces' | 'memory' | 'settings';

function AppContent() {
  const [activeTab, setActiveTab] = useState<TabId>('home');

  const renderTabContent = () => {
    switch (activeTab) {
      case 'home':
        return (
          <Suspense fallback={<PageLoader />}>
            <HomePage />
          </Suspense>
        );
      case 'marketplace':
        return (
          <Suspense fallback={<PageLoader />}>
            <MarketplacePage />
          </Suspense>
        );
      case 'workspaces':
        return (
          <Suspense fallback={<PageLoader />}>
            <SyncPage />
          </Suspense>
        );
      case 'memory':
        return (
          <Suspense fallback={<PageLoader />}>
            <MemoryPage />
          </Suspense>
        );
      case 'settings':
        return (
          <Suspense fallback={<PageLoader />}>
            <SettingsPage />
          </Suspense>
        );
      default:
        return null;
    }
  };

  return (
    <MainLayout activeTab={activeTab} onTabChange={setActiveTab}>
      {renderTabContent()}
    </MainLayout>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppContent />} />
          <Route path="/chat" element={<Suspense fallback={<PageLoader />}><ChatPage /></Suspense>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
