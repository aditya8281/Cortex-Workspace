import { useRef } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { useNavigate } from "react-router-dom";
import { Archive, MoreHorizontal, Pin, PinOff, Pencil, Trash2 } from "lucide-react";
import { cn, formatRelativeGroup } from "@/lib/utils";
import { useChatStore } from "@/stores/chatStore";
import { useAppStore } from "@/stores/appStore";
import { useState } from "react";
import type { ChatSession } from "@/types/cortex";

const GROUP_ORDER = ["pinned", "today", "yesterday", "week", "month", "older"] as const;
const GROUP_LABELS: Record<string, string> = {
  pinned: "Pinned",
  today: "Today",
  yesterday: "Yesterday",
  week: "Last 7 days",
  month: "Last 30 days",
  older: "Older",
};

type FlatItem =
  | { type: "header"; key: string; label: string }
  | { type: "session"; key: string; session: ChatSession };

type Props = {
  search: string;
  mobile?: boolean;
};

export function SessionList({ search, mobile }: Props) {
  const navigate = useNavigate();
  const setMobileOpen = useAppStore((s) => s.setMobileSidebarOpen);
  const sessions = useChatStore((s) => s.sessions) ?? [];
  const activeId = useChatStore((s) => s.activeSessionId);
  const setActive = useChatStore((s) => s.setActiveSession);
  const pinSession = useChatStore((s) => s.pinSession);
  const archiveSession = useChatStore((s) => s.archiveSession);
  const deleteSession = useChatStore((s) => s.deleteSession);
  const setRenaming = useChatStore((s) => s.setRenaming);
  const renameValue = useChatStore((s) => s.renameValue);
  const commitRename = useChatStore((s) => s.commitRename);
  const renamingSessionId = useChatStore((s) => s.renamingId);
  const [menuId, setMenuId] = useState<string | null>(null);

  const filtered = sessions.filter(
    (s) => !s.archived && s.title.toLowerCase().includes(search.toLowerCase()),
  );

  const flat: FlatItem[] = [];
  const pinned = filtered.filter((s) => s.pinned);
  const rest = filtered.filter((s) => !s.pinned);
  const buckets: Record<string, ChatSession[]> = {
    pinned: [],
    today: [],
    yesterday: [],
    week: [],
    month: [],
    older: [],
  };
  buckets.pinned = pinned;
  for (const s of rest) {
    const g = formatRelativeGroup(s.createdAt);
    if (buckets[g]) buckets[g].push(s);
  }

  for (const key of GROUP_ORDER) {
    const items = buckets[key];
    if (!items?.length) continue;
    flat.push({ type: "header", key: `h-${key}`, label: GROUP_LABELS[key] });
    for (const session of items) {
      flat.push({ type: "session", key: session.id, session });
    }
  }

  const parentRef = useRef<HTMLDivElement>(null);
  const virtualizer = useVirtualizer({
    count: flat.length,
    getScrollElement: () => parentRef.current,
    estimateSize: (i) => (flat[i].type === "header" ? 28 : 40),
    overscan: 8,
  });

  return (
    <div ref={parentRef} className="min-h-0 flex-1 overflow-y-auto pb-4">
      <div style={{ height: virtualizer.getTotalSize(), position: "relative" }}>
        {virtualizer.getVirtualItems().map((virtualRow) => {
          const item = flat[virtualRow.index];
          return (
            <div
              key={item.key}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                transform: `translateY(${virtualRow.start}px)`,
              }}
            >
              {item.type === "header" ? (
                <p className="mb-1 px-2 pt-2 text-[10px] font-semibold uppercase tracking-wider text-cortex-muted">
                  {item.label}
                </p>
              ) : (
                <div className="relative px-1">
                  {renamingSessionId === item.session.id ? (
                    <input
                      className="w-full rounded-xl border border-cortex-border/80 bg-cortex-elevated/85 px-2 py-1.5 text-sm shadow-sm focus:border-cortex-accent/30 focus:ring-2 focus:ring-cortex-accent/20"
                      value={renameValue}
                      onChange={(e) => setRenaming(item.session.id, e.target.value)}
                      onBlur={() => commitRename(item.session.id)}
                      onKeyDown={(e) => e.key === "Enter" && commitRename(item.session.id)}
                      autoFocus
                    />
                  ) : (
                    <button
                      type="button"
                      onClick={() => {
                        setActive(item.session.id);
                        navigate("/chat");
                        if (mobile) setMobileOpen(false);
                      }}
                      className={cn(
                        "group relative flex w-full items-center gap-2 rounded-xl px-2 py-2 text-left text-sm transition-all duration-200 ease-out hover:-translate-y-0.5",
                        activeId === item.session.id
                          ? "bg-cortex-accent-soft/80 text-cortex-text shadow-[0_0_0_1px_rgba(109,156,255,0.12)]"
                          : "text-cortex-muted hover:bg-white/6 hover:text-cortex-text",
                      )}
                    >
                      {activeId === item.session.id && (
                        <span className="absolute left-0 top-2 bottom-2 w-1 rounded-full bg-cortex-accent shadow-[0_0_16px_rgba(109,156,255,0.55)]" />
                      )}
                      <span className="flex-1 truncate">{item.session.title}</span>
                      {item.session.pinned && <Pin className="h-3 w-3 shrink-0 opacity-60" />}
                      <button
                        type="button"
                        className="opacity-0 group-hover:opacity-100"
                        onClick={(e) => {
                          e.stopPropagation();
                          setMenuId(menuId === item.session.id ? null : item.session.id);
                        }}
                      >
                        <MoreHorizontal className="h-3.5 w-3.5" />
                      </button>
                    </button>
                  )}
                  {menuId === item.session.id && (
                    <div className="absolute right-2 top-9 z-20 min-w-[140px] rounded-lg border border-cortex-border bg-cortex-elevated py-1 shadow-lg">
                      <MenuBtn
                        icon={Pencil}
                        label="Rename"
                        onClick={() => {
                          setRenaming(item.session.id, item.session.title);
                          setMenuId(null);
                        }}
                      />
                      <MenuBtn
                        icon={item.session.pinned ? PinOff : Pin}
                        label={item.session.pinned ? "Unpin" : "Pin"}
                        onClick={() => {
                          pinSession(item.session.id, !item.session.pinned);
                          setMenuId(null);
                        }}
                      />
                      <MenuBtn
                        icon={Archive}
                        label="Archive"
                        onClick={() => {
                          archiveSession(item.session.id, true);
                          setMenuId(null);
                        }}
                      />
                      <MenuBtn
                        icon={Trash2}
                        label="Delete"
                        onClick={() => {
                          if (window.confirm("Delete this chat?")) deleteSession(item.session.id);
                          setMenuId(null);
                        }}
                      />
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function MenuBtn({
  icon: Icon,
  label,
  onClick,
}: {
  icon: typeof Pencil;
  label: string;
  onClick: () => void;
}) {
  return (
      <button
      type="button"
      className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs transition hover:bg-white/6 hover:text-cortex-text"
      onClick={onClick}
    >
      <Icon className="h-3.5 w-3.5" />
      {label}
    </button>
  );
}
