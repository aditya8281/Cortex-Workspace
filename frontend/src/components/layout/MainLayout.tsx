import React, { useState } from 'react';
import { Home, ShoppingBag, Zap, Brain, Settings, ChevronRight } from 'lucide-react';
import styles from './MainLayout.module.css';

type TabId = 'home' | 'marketplace' | 'workspaces' | 'memory' | 'settings';

interface MainLayoutProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  children: React.ReactNode;
}

const TABS: { id: TabId; label: string; icon: React.ReactNode; description: string }[] = [
  { id: 'home', label: 'Home', icon: <Home size={20} />, description: 'Command center' },
  {
    id: 'marketplace',
    label: 'Marketplace',
    icon: <ShoppingBag size={20} />,
    description: 'Models & providers',
  },
  { id: 'workspaces', label: 'Workspaces', icon: <Zap size={20} />, description: 'Projects' },
  { id: 'memory', label: 'Memory', icon: <Brain size={20} />, description: 'Knowledge' },
  { id: 'settings', label: 'Settings', icon: <Settings size={20} />, description: 'System' },
];

export const MainLayout: React.FC<MainLayoutProps> = ({ activeTab, onTabChange, children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className={styles.container}>
      {/* Sidebar Navigation */}
      <nav className={`${styles.sidebar} ${!sidebarOpen ? styles.sidebarCollapsed : ''}`}>
        <div className={styles.sidebarContent}>
          {/* Logo */}
          <div className={styles.logo}>
            <div className={styles.logoIcon}>C</div>
            {sidebarOpen && <span className={styles.logoText}>Cortex</span>}
          </div>

          {/* Navigation Items */}
          <div className={styles.navItems}>
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`${styles.navItem} ${activeTab === tab.id ? styles.navItemActive : ''}`}
                title={sidebarOpen ? '' : tab.label}
              >
                <div className={styles.navIcon}>{tab.icon}</div>
                {sidebarOpen && (
                  <>
                    <div className={styles.navLabel}>{tab.label}</div>
                    {activeTab === tab.id && <ChevronRight size={16} className={styles.navChevron} />}
                  </>
                )}
              </button>
            ))}
          </div>

          {/* Footer */}
          <div className={styles.sidebarFooter}>
            <button
              className={styles.toggleButton}
              onClick={() => setSidebarOpen(!sidebarOpen)}
              title={sidebarOpen ? 'Collapse' : 'Expand'}
            >
              <ChevronRight size={16} className={sidebarOpen ? styles.toggleOpen : ''} />
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className={styles.main}>{children}</main>
    </div>
  );
};

export default MainLayout;
