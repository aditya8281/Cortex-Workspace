import React from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { useDispatch, useSelector } from "react-redux";
import { useAuth } from "@/hooks/useAuth";
import { toggleSidebar, setCurrentTab } from "@/state/slices/ui";
import type { RootState } from "@/state/store";
import { Menu, Home, MessageSquare, Settings } from "lucide-react";

export function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const dispatch = useDispatch();
  const { user, logout } = useAuth();
  const { sidebarOpen } = useSelector((state: RootState) => state.ui);

  const isAdmin = user?.role === "admin";

  const userMenuItems = [
    { icon: MessageSquare, label: "Chat", href: "/dashboard/chat" },
    { icon: Home, label: "Models", href: "/dashboard/models" },
    { icon: Home, label: "Memory", href: "/dashboard/memory" },
    { icon: Home, label: "Sync", href: "/dashboard/sync" },
    { icon: Home, label: "Search", href: "/dashboard/search" },
    { icon: Settings, label: "Settings", href: "/dashboard/settings" },
  ];

  const adminMenuItems = [
    { icon: Home, label: "Overview", href: "/admin/dashboard" },
    { icon: Home, label: "Health", href: "/admin/health" },
    { icon: Home, label: "Providers", href: "/admin/providers" },
    { icon: Home, label: "Models", href: "/admin/models" },
    { icon: Home, label: "Users", href: "/admin/users" },
    { icon: Home, label: "Services", href: "/admin/services" },
    { icon: Home, label: "Logs", href: "/admin/logs" },
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
      } bg-background border-r border-border h-screen flex flex-col transition-all duration-300 fixed md:relative`}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        {sidebarOpen && <h1 className="text-xl font-bold text-white">CORTEX</h1>}
        <button
          onClick={() => dispatch(toggleSidebar())}
          className="p-1 hover:bg-surface rounded transition-colors"
        >
          <Menu size={20} className="text-primary" />
        </button>
      </div>

      {/* Menu Items */}
      <nav className="flex-1 overflow-y-auto py-4">
        {menuItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 mx-2 rounded transition-colors ${
                isActive
                  ? "bg-primary text-white"
                  : "text-gray-400 hover:text-white hover:bg-surface"
              }`}
              onClick={() => dispatch(setCurrentTab(item.label.toLowerCase()))}
            >
              <item.icon size={20} />
              {sidebarOpen && <span>{item.label}</span>}
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
