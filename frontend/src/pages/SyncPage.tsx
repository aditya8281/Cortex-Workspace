import React, { useState } from 'react';
import styles from '@/styles/SyncPage.module.css';
import { Plus, Folder, Settings, MoreVertical, Code, MessageSquare } from 'lucide-react';

interface Workspace {
  id: string;
  name: string;
  description: string;
  path: string;
  modelCount: number;
  lastUsed: string;
}

const MOCK_WORKSPACES: Workspace[] = [
  {
    id: '1',
    name: 'Main Project',
    description: 'Primary development workspace',
    path: '/home/user/projects/main',
    modelCount: 3,
    lastUsed: '2 hours ago',
  },
  {
    id: '2',
    name: 'Research & Experiments',
    description: 'Testing new models and frameworks',
    path: '/home/user/research',
    modelCount: 5,
    lastUsed: '1 day ago',
  },
  {
    id: '3',
    name: 'Utilities',
    description: 'Helper scripts and tools',
    path: '/home/user/utils',
    modelCount: 1,
    lastUsed: '3 days ago',
  },
];

export const SyncPage: React.FC = () => {
  const [selectedWorkspace, setSelectedWorkspace] = useState<string | null>(MOCK_WORKSPACES[0]?.id);

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>Workspaces</h1>
        <p className={styles.subtitle}>Project-based agent environments with unified tools</p>
      </div>

      <div className={styles.content}>
        {/* New Workspace Button */}
        <button className={styles.newWorkspaceButton}>
          <Plus size={16} />
          New Workspace
        </button>

        {/* Workspace List */}
        <div className={styles.workspaceGrid}>
          {MOCK_WORKSPACES.map((workspace) => (
            <div
              key={workspace.id}
              className={`${styles.workspaceCard} ${selectedWorkspace === workspace.id ? styles.workspaceCardActive : ''}`}
              onClick={() => setSelectedWorkspace(workspace.id)}
            >
              <div className={styles.cardHeader}>
                <div className={styles.cardIcon}>
                  <Folder size={24} />
                </div>
                <button className={styles.moreButton}>
                  <MoreVertical size={16} />
                </button>
              </div>

              <h3 className={styles.cardTitle}>{workspace.name}</h3>
              <p className={styles.cardDescription}>{workspace.description}</p>

              <div className={styles.cardMeta}>
                <span className={styles.metaItem}>
                  <Code size={14} />
                  {workspace.modelCount} models
                </span>
                <span className={styles.metaItem}>
                  Last used {workspace.lastUsed}
                </span>
              </div>

              <div className={styles.cardActions}>
                <button className={styles.actionButton}>
                  <MessageSquare size={14} />
                  Chat
                </button>
                <button className={styles.actionButton}>
                  <Code size={14} />
                  Files
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Quick Features */}
        <div className={styles.featuresSection}>
          <h2 className={styles.sectionTitle}>Workspace Features</h2>

          <div className={styles.featureGrid}>
            <div className={styles.featureCard}>
              <MessageSquare size={24} style={{ color: '#3b82f6' }} />
              <h4>Unified Chat</h4>
              <p>Interact with all workspace models in one thread</p>
            </div>

            <div className={styles.featureCard}>
              <Folder size={24} style={{ color: '#10b981' }} />
              <h4>File Context</h4>
              <p>Automatically include project files in conversations</p>
            </div>

            <div className={styles.featureCard}>
              <Code size={24} style={{ color: '#f59e0b' }} />
              <h4>Tool Inspector</h4>
              <p>Monitor and control agent tool execution</p>
            </div>

            <div className={styles.featureCard}>
              <Settings size={24} style={{ color: '#06b6d4' }} />
              <h4>Workspace Settings</h4>
              <p>Configure models, tools, and behavior per project</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SyncPage;
