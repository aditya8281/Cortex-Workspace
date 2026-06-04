import React from 'react';
import { useOllamaRegistry } from '@/hooks/useOllamaRegistry';
import styles from '@/styles/HomePage.module.css';
import { Activity, Cpu, Zap, TrendingUp } from 'lucide-react';

export const HomePage: React.FC = () => {
  const registry = useOllamaRegistry();
  const installedQuery = registry.useInstalledModels();
  const allModelsQuery = registry.useAllModels();

  const installedCount = installedQuery.data?.models?.length || 0;
  const totalModels = allModelsQuery.data?.models?.length || 0;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>Command Center</h1>
        <p className={styles.subtitle}>Welcome back. Your AI workspace awaits.</p>
      </div>

      {/* Quick Stats */}
      <div className={styles.statsGrid}>
        <div className={styles.statCard}>
          <div className={styles.statIcon} style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)' }}>
            <Cpu size={20} style={{ color: '#10b981' }} />
          </div>
          <div className={styles.statContent}>
            <div className={styles.statLabel}>Models Installed</div>
            <div className={styles.statValue}>{installedCount}</div>
          </div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statIcon} style={{ backgroundColor: 'rgba(59, 130, 246, 0.1)' }}>
            <Zap size={20} style={{ color: '#3b82f6' }} />
          </div>
          <div className={styles.statContent}>
            <div className={styles.statLabel}>Available Models</div>
            <div className={styles.statValue}>{totalModels}</div>
          </div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statIcon} style={{ backgroundColor: 'rgba(245, 158, 11, 0.1)' }}>
            <TrendingUp size={20} style={{ color: '#f59e0b' }} />
          </div>
          <div className={styles.statContent}>
            <div className={styles.statLabel}>System Status</div>
            <div className={styles.statValue}>Healthy</div>
          </div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statIcon} style={{ backgroundColor: 'rgba(6, 182, 212, 0.1)' }}>
            <Activity size={20} style={{ color: '#06b6d4' }} />
          </div>
          <div className={styles.statContent}>
            <div className={styles.statLabel}>GPU Utilization</div>
            <div className={styles.statValue}>Idle</div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>Quick Actions</h2>
        <div className={styles.actionGrid}>
          <button className={styles.actionButton}>
            <div className={styles.actionIcon}>▶</div>
            <div className={styles.actionLabel}>Run a Model</div>
          </button>
          <button className={styles.actionButton}>
            <div className={styles.actionIcon}>🔍</div>
            <div className={styles.actionLabel}>Browse Models</div>
          </button>
          <button className={styles.actionButton}>
            <div className={styles.actionIcon}>⚙️</div>
            <div className={styles.actionLabel}>System Settings</div>
          </button>
          <button className={styles.actionButton}>
            <div className={styles.actionIcon}>📚</div>
            <div className={styles.actionLabel}>Documentation</div>
          </button>
        </div>
      </div>

      {/* Recent Models */}
      {installedQuery.data?.models && installedQuery.data.models.length > 0 && (
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>Installed Models</h2>
          <div className={styles.modelsList}>
            {installedQuery.data.models.slice(0, 3).map((model: any) => (
              <div key={model.model_id} className={styles.modelItem}>
                <div className={styles.modelIcon}>🤖</div>
                <div className={styles.modelInfo}>
                  <div className={styles.modelName}>{model.display_name}</div>
                  <div className={styles.modelDesc}>{model.model_id}</div>
                </div>
                <button className={styles.launchButton}>Launch</button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default HomePage;
