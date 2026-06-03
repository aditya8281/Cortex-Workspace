import { NavLink, useNavigate } from "react-router-dom";
import {
  Activity,
  Brain,
  FolderGit2,
  GitBranch,
  LayoutDashboard,
  MessageSquarePlus,
  MessagesSquare,
  Network,
  RefreshCw,
  Search,
  Settings,
  Pin,
  MoreHorizontal,
  ChevronLeft,
} from "lucide-react";
import { cn, formatRelativeGroup } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAppStore } from "@/stores/appStore";
import { useChatStore } from "@/stores/chatStore";
import { useMemo, useState } from "react";

const NAV = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/chat", icon: MessagesSquare, label: "Chats" },
  { to: "/projects", icon: FolderGit2, label: "Projects" },
  { to: "/repositories", icon: GitBranch, label: "Repositories" },
  { to: "/memory", icon: Brain, label: "Memory" },
  { to: "/graph", icon: Network, label: "Knowledge Graph" },
  { to: "/sync", icon: RefreshCw, label: "Sync Center" },
  { to: "/activity", icon: Activity, label: "Activity" },
  { to: "/settings", icon: Settings, label: "Settings" },
];

const GROUP_LABELS: Record<string, string> = {
  today: "Today",
  yesterday: "Yesterday",
  week: "Last 7 days",
  month: "Last 30 days",
  older: "Older",
  pinned: "Pinned",
};

export function Sidebar({ mobile = false }: { mobile?: boolean }) {
  const navigate = useNavigate();
  const collapsed = useAppStore((s) => s.sidebarCollapsed) && !mobile;
  const setCollapsed = useAppStore((s) => s.setSidebarCollapsed);
  const setMobileOpen = useAppStore((s) => s.setMobileSidebarOpen);
  const sessions = useChatStore((s) => s.sessions.filter((x) => !x.archived));
  const activeId = useChatStore((s) => s.activeSessionId);
  const newSession = useChatStore((s) => s.newSession);
  const setActive = useChatStore((s) => s.setActiveSession);
  const [search, setSearch] = useState("");

  const grouped = useMemo(() => {
    const filtered = sessions.filter((s) =>
      s.title.toLowerCase().includes(search.toLowerCase()),
    );
    const pinned = filtered.filter((s) => s.pinned);
    const rest = filtered.filter((s) => !s.pinned);
    const buckets: Record<string, typeof sessions> = { pinned: [], today: [], yesterday: [], week: [], month: [], older: [] };
    buckets.pinned = pinned;
    for (const s of rest) {
      buckets[formatRelativeGroup(s.createdAt)].push(s);
    }
    return buckets;
  }, [sessions, search]);

  const navItem = (to: string, Icon: typeof LayoutDashboard, label: string) => (
    <NavLink
      key={to}
      to={to}
      end={to === "/"}
      onClick={() => mobile && setMobileOpen(false)}
      className={({ isActive }) =>
        cn(
          "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
          isActive
            ? "bg-cortex-accent-soft text-cortex-accent"
            : "text-cortex-muted hover:bg-white/5 hover:text-cortex-text",
          collapsed && !mobile && "justify-center px-2",
        )
      }
      title={collapsed && !mobile ? label : undefined}
    >
      <Icon className="h-4 w-4 shrink-0" />
      {(!collapsed || mobile) && <span>{label}</span>}
    </NavLink>
  );

  return (
    <aside
      className={cn(
        "flex h-full flex-col border-r border-cortex-border bg-cortex-surface/95 backdrop-blur-md",
        collapsed && !mobile ? "w-[68px]" : "w-[280px]",
        mobile && "w-full",
      )}
    >
      <div className="flex items-center gap-2 border-b border-cortex-border p-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cortex-accent font-bold text-white">
          C
        </div>
        {(!collapsed || mobile) && (
          <div className="min-w-0 flex-1">
            <p className="truncate font-semibold">Cortex</p>
            <p className="text-xs text-cortex-muted">AI Operating System</p>
          </div>
        )}
        {!mobile && (
          <Button variant="ghost" size="icon" onClick={() => setCollapsed(!collapsed)} aria-label="Collapse">
            <ChevronLeft className={cn("h-4 w-4 transition", collapsed && "rotate-180")} />
          </Button>
        )}
      </div>

      <div className="p-3">
        <Button
          className="w-full"
          onClick={() => {
            newSession();
            navigate("/chat");
            if (mobile) setMobileOpen(false);
          }}
        >
          <MessageSquarePlus className="h-4 w-4" />
          {(!collapsed || mobile) && "New chat"}
        </Button>
      </div>

      <nav className="space-y-0.5 px-2">{NAV.map((n) => navItem(n.to, n.icon, n.label))}</nav>

      {(!collapsed || mobile) && (
        <div className="mt-4 flex min-h-0 flex-1 flex-col border-t border-cortex-border px-2 pt-3">
          <div className="mb-2 flex items-center gap-2 px-1">
            <Search className="h-3.5 w-3.5 text-cortex-muted" />
            <Input
              placeholder="Search chats…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="h-8 border-0 bg-transparent px-0 focus-visible:ring-0"
            />
          </div>
          <div className="flex-1 space-y-3 overflow-y-auto pb-4">
            {(["pinned", "today", "yesterday", "week", "month", "older"] as const).map((key) => {
              const items = grouped[key];
              if (!items?.length) return null;
              return (
                <div key={key}>
                  <p className="mb-1 px-2 text-[10px] font-semibold uppercase tracking-wider text-cortex-muted">
                    {GROUP_LABELS[key]}
                  </p>
                  <ul className="space-y-0.5">
                    {items.map((session) => (
                      <li key={session.id}>
                        <button
                          type="button"
                          onClick={() => {
                            setActive(session.id);
                            navigate("/chat");
                            if (mobile) setMobileOpen(false);
                          }}
                          className={cn(
                            "group flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left text-sm transition",
                            activeId === session.id
                              ? "bg-white/10 text-cortex-text"
                              : "text-cortex-muted hover:bg-white/5 hover:text-cortex-text",
                          )}
                        >
                          <span className="flex-1 truncate">{session.title}</span>
                          {session.pinned && <Pin className="h-3 w-3 shrink-0 opacity-60" />}
                          <MoreHorizontal className="h-3 w-3 shrink-0 opacity-0 group-hover:opacity-60" />
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </aside>
  );
}
