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
          "group relative flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition-all duration-200 ease-out hover:-translate-y-0.5 active:scale-[0.98]",
          isActive
            ? "bg-cortex-accent-soft/80 text-cortex-accent shadow-[0_0_0_1px_rgba(109,156,255,0.15)] before:absolute before:left-1 before:top-1/2 before:h-5 before:w-1 before:-translate-y-1/2 before:rounded-full before:bg-cortex-accent before:shadow-[0_0_18px_rgba(109,156,255,0.55)]"
            : "text-cortex-muted hover:bg-white/6 hover:text-cortex-text",
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
        "flex h-full flex-col border-r border-cortex-border/70 bg-cortex-surface/85 backdrop-blur-2xl transition-[width] duration-300 ease-out",
        collapsed && !mobile ? "w-[68px]" : "w-[280px]",
        mobile && "w-full",
      )}
    >
      <div className="flex items-center gap-2 border-b border-cortex-border/60 p-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-cortex-accent to-cyan-400 font-bold text-cortex-bg shadow-[0_12px_32px_rgba(109,156,255,0.25)]">
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
          <ChevronLeft className={cn("h-4 w-4 transition-transform duration-200", collapsed && "rotate-180")} />
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
        className="mx-3 mt-3 flex items-center gap-2 rounded-2xl border border-cortex-border/70 bg-cortex-elevated/60 p-2 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-cortex-accent/30 hover:bg-cortex-elevated/80"
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

      <nav className="space-y-1 px-2">{NAV.map((n) => navItem(n.to, n.icon, n.label))}</nav>

      {(!collapsed || mobile) && (
        <div className="mt-4 flex min-h-0 flex-1 flex-col border-t border-cortex-border/60 px-2 pt-3">
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
