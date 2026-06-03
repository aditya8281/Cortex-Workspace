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
  User,
  ChevronLeft,
  Cpu,
  ShoppingBag,
  BarChart3,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAppStore } from "@/stores/appStore";
import { useChatStore } from "@/stores/chatStore";
import { useProfileStore } from "@/stores/profileStore";
import { SessionList } from "./SessionList";
import { useState } from "react";

const NAV = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/chat", icon: MessagesSquare, label: "Chats" },
  { to: "/profile", icon: User, label: "Profile" },
  { to: "/projects", icon: FolderGit2, label: "Projects" },
  { to: "/repositories", icon: GitBranch, label: "Repositories" },
  { to: "/memory", icon: Brain, label: "Memory" },
  { to: "/graph", icon: Network, label: "Knowledge Graph" },
  { to: "/sync", icon: RefreshCw, label: "Sync Center" },
  { to: "/activity", icon: Activity, label: "Activity" },
  { to: "/models", icon: Cpu, label: "Models" },
  { to: "/marketplace", icon: ShoppingBag, label: "Marketplace" },
  { to: "/performance", icon: BarChart3, label: "Performance" },
  { to: "/settings", icon: Settings, label: "Settings" },
];

export function Sidebar({ mobile = false }: { mobile?: boolean }) {
  const navigate = useNavigate();
  const collapsed = useAppStore((s) => s.sidebarCollapsed) && !mobile;
  const setCollapsed = useAppStore((s) => s.setSidebarCollapsed);
  const setMobileOpen = useAppStore((s) => s.setMobileSidebarOpen);
  const newSession = useChatStore((s) => s.newSession);
  const profile = useProfileStore((s) => s.profile);
  const completion = useProfileStore((s) => s.completionPercent);
  const [search, setSearch] = useState("");

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

  const displayName = profile.displayName || "Your profile";

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

      {(!collapsed || mobile) && (
        <button
          type="button"
          onClick={() => {
            navigate("/profile");
            if (mobile) setMobileOpen(false);
          }}
          className="mx-3 mt-3 flex items-center gap-2 rounded-lg border border-cortex-border bg-cortex-elevated/60 p-2 text-left transition hover:border-cortex-accent/40"
        >
          <div
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white"
            style={{ background: profile.avatarColor }}
          >
            {displayName.charAt(0).toUpperCase() || "?"}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{displayName}</p>
            <p className="text-[10px] text-cortex-muted">Profile {completion()}% complete</p>
          </div>
        </button>
      )}

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
            <Search className="h-3.5 w-3.5 shrink-0 text-cortex-muted" />
            <Input
              placeholder="Search chats…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="h-8 border-0 bg-transparent px-0 focus-visible:ring-0"
            />
          </div>
          <SessionList search={search} mobile={mobile} />
        </div>
      )}
    </aside>
  );
}
