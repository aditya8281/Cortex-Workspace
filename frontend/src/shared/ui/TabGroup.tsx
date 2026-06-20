"use client";

import { useState, type ReactNode } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface Tab {
  id: string;
  label: string;
  icon?: ReactNode;
  count?: number;
}

interface TabGroupProps {
  tabs: Tab[];
  defaultTab?: string;
  onChange?: (tabId: string) => void;
  className?: string;
  children: ReactNode;
}

export function TabGroup({
  tabs,
  defaultTab,
  onChange,
  className,
  children,
}: TabGroupProps) {
  const [activeTab, setActiveTab] = useState(defaultTab || tabs[0]?.id);

  const handleChange = (tabId: string) => {
    setActiveTab(tabId);
    onChange?.(tabId);
  };

  return (
    <div className={className}>
      <div className="flex gap-1 border-b border-border-subtle mb-4">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => handleChange(tab.id)}
            className={cn(
              "relative flex items-center gap-2 px-4 py-2.5 text-sm font-medium",
              "transition-colors duration-150",
              activeTab === tab.id
                ? "text-text"
                : "text-text-secondary hover:text-text"
            )}
          >
            {tab.icon}
            {tab.label}
            {tab.count !== undefined && (
              <span className="text-xs text-text-muted bg-bg-surface px-1.5 py-0.5 rounded-full">
                {tab.count}
              </span>
            )}
            {activeTab === tab.id && (
              <motion.div
                layoutId="tab-indicator"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent"
                transition={{ type: "spring", damping: 30, stiffness: 300 }}
              />
            )}
          </button>
        ))}
      </div>
      <TabContext.Provider value={activeTab}>{children}</TabContext.Provider>
    </div>
  );
}

import { createContext, useContext } from "react";

const TabContext = createContext<string>("");

export function TabPanel({
  tabId,
  children,
  className,
}: {
  tabId: string;
  children: ReactNode;
  className?: string;
}) {
  const activeTab = useContext(TabContext);
  if (activeTab !== tabId) return null;
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
