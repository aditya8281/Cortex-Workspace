import React from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { useDispatch, useSelector } from "react-redux";
import { useAuth } from "@/hooks/useAuth";
import { toggleSidebar, setCurrentTab, toggleCommandPalette } from "@/state/slices/ui";
import type { RootState } from "@/state/store";
import { 
  Menu, Home, MessageSquare, Settings, Brain, Cpu, RefreshCw, Search, 
  Activity, Users, ShieldAlert, Key, ScrollText
} from "lucide-react";

export function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const dispatch = useDispatch();
  const { user, logout } = useAuth();
  const { sidebarOpen } = useSelector((state: RootState) => state.ui);

  const isAdmin = user?.role === "admin";

  const userMenuItems = [
    { icon: MessageSquare, label: "Chat", href: "/dashboard/chat" },
    { icon: Cpu, label: "Models", href: "/dashboard/models" },
    { icon: Brain, label: "Memory", href: "/dashboard/memory" },
    { icon: RefreshCw, label: "Sync", href: "/dashboard/sync" },
    { icon: Search, label: "Search", href: "/dashboard/search" },
    { icon: Settings, label: "Settings", href: "/dashboard/settings" },
  ];

  const adminMenuItems = [
    { icon: Home, label: "Overview", href: "/admin/dashboard" },
    { icon: Activity, label: "Health", href: "/admin/health" },
    { icon: Key, label: "Providers", href: "/admin/providers" },
    { icon: Cpu, label: "Models", href: "/admin/models" },
    { icon: Users, label: "Users", href: "/admin/users" },
    { icon: Settings, label: "Services", href: "/admin/services" },
    { icon: ScrollText, label: "Logs", href: "/admin/logs" },
    { icon: Settings, label: "Config", href: "/admin/config" },
  ];

  const menuItems = isAdmin ? adminMenuItems : userMenuItems;

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <aside
      className={`${
        sidebarOpen ? "w-64" : "w-20"
      } bg-slate-950 border-r border-slate-800/80 h-screen flex flex-col transition-all duration-300 fixed md:relative`}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-800/80">
        {sidebarOpen && <h1 className="text-xl font-mono font-bold text-white tracking-widest bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">CORTEX</h1>}
        <button
          onClick={() => dispatch(toggleSidebar())}
          className="p-1.5 hover:bg-slate-900 rounded transition-colors text-slate-400 hover:text-white"
        >
          <Menu size={18} />
        </button>
      </div>

      {/* Quick Search trigger for Command Palette */}
      {sidebarOpen && (
        <div className="px-3 pt-4 pb-1">
          <button
            onClick={() => dispatch(toggleCommandPalette())}
            className="w-full flex items-center justify-between px-3 py-2 bg-slate-900 border border-slate-800/80 hover:border-slate-700/80 rounded-lg text-slate-500 hover:text-slate-400 transition-all text-[11px] font-sans"
          >
            <span className="flex items-center gap-2">
              <Search size={12} />
              <span>Search commands...</span>
            </span>
            <kbd className="text-[9px] bg-slate-950 border border-slate-800 px-1 py-0.5 rounded text-slate-500 font-mono">Ctrl K</kbd>
          </button>
        </div>
      )}

      {/* Menu Items */}
      <nav className="flex-1 overflow-y-auto py-4">
        {menuItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 mx-2 rounded-lg transition-all duration-150 ${
                isActive
                  ? "bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)] font-medium"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent"
              }`}
              onClick={() => dispatch(setCurrentTab(item.label.toLowerCase()))}
            >
              <item.icon size={18} className={isActive ? "text-cyan-400" : "text-slate-400"} />
              {sidebarOpen && <span className="text-xs font-sans font-medium tracking-wide">{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Footer - User Info & Logout */}
      <div className="border-t border-border p-4 space-y-2">
        {sidebarOpen && (
          <div className="text-sm">
            <p className="text-gray-400">Logged in as</p>
            <p className="text-white font-medium truncate">{user?.full_name}</p>
          </div>
        )}
        <button
          onClick={handleLogout}
          className="w-full px-3 py-2 bg-danger hover:bg-red-700 text-white rounded text-sm transition-colors"
        >
          {sidebarOpen ? "Logout" : "↓"}
        </button>
      </div>
    </aside>
  );
}
