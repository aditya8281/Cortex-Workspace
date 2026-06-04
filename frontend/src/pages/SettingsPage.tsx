import React, { useState } from 'react';
import styles from '@/styles/SettingsPage.module.css';
import { Save, Plus, Trash2 } from 'lucide-react';

interface Provider {
  id: string;
  name: string;
  type: 'cloud' | 'local';
  url: string;
  apiKey?: string;
  isDefault: boolean;
}

export const SettingsPage: React.FC = () => {
  const [providers, _setProviders] = useState<Provider[]>([
    { id: '1', name: 'Local Ollama', type: 'local', url: 'http://localhost:11434', isDefault: true },
  ]);
  const [_selectedWorkspace, _setSelectedWorkspace] = useState<string | null>(null);
  const [showAddProvider, setShowAddProvider] = useState(false);

  const handleAddProvider = () => {
    setShowAddProvider(true);
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>Settings</h1>
        <p className={styles.subtitle}>Configure your AI workspace</p>
      </div>

      {/* Provider Configuration Section */}
      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>Model Providers</h2>
          <button className={styles.addButton} onClick={handleAddProvider}>
            <Plus size={16} /> Add Provider
          </button>
        </div>

        <div className={styles.providersList}>
          {providers.map((provider) => (
            <div key={provider.id} className={styles.providerCard}>
              <div className={styles.providerInfo}>
                <div className={styles.providerHeader}>
                  <h3 className={styles.providerName}>{provider.name}</h3>
                  {provider.isDefault && (
                    <span className={styles.defaultBadge}>Default</span>
                  )}
                </div>
                <p className={styles.providerType}>{provider.type === 'local' ? 'Local' : 'Cloud API'}</p>
                <p className={styles.providerUrl}>{provider.url}</p>
              </div>
              <div className={styles.providerActions}>
                <button className={styles.editButton}>Edit</button>
                <button className={styles.deleteButton}>
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Add Provider Form */}
        {showAddProvider && (
          <div className={styles.addProviderForm}>
            <h3 className={styles.formTitle}>Add New Provider</h3>

            <div className={styles.formGroup}>
              <label className={styles.label}>Provider Name</label>
              <input type="text" className={styles.input} placeholder="e.g., OpenAI, Anthropic" />
            </div>

            <div className={styles.formGroup}>
              <label className={styles.label}>Provider Type</label>
              <select className={styles.select}>
                <option value="local">Local (Ollama)</option>
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic (Claude)</option>
                <option value="groq">Groq</option>
                <option value="custom">Custom Endpoint</option>
              </select>
            </div>

            <div className={styles.formGroup}>
              <label className={styles.label}>API Endpoint URL</label>
              <input
                type="text"
                className={styles.input}
                placeholder="https://api.openai.com/v1"
              />
            </div>

            <div className={styles.formGroup}>
              <label className={styles.label}>API Key (Optional)</label>
              <input
                type="password"
                className={styles.input}
                placeholder="Your API key"
              />
            </div>

            <div className={styles.formActions}>
              <button className={styles.cancelButton} onClick={() => setShowAddProvider(false)}>
                Cancel
              </button>
              <button className={styles.saveButton}>
                <Save size={16} /> Save Provider
              </button>
            </div>
          </div>
        )}
      </div>

      {/* General Settings Section */}
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>General</h2>

        <div className={styles.settingItem}>
          <div className={styles.settingLabel}>
            <h4>Auto-fetch Models</h4>
            <p>Automatically sync available models every 24 hours</p>
          </div>
          <input type="checkbox" className={styles.toggle} defaultChecked />
        </div>

        <div className={styles.settingItem}>
          <div className={styles.settingLabel}>
            <h4>GPU Acceleration</h4>
            <p>Use GPU for local model inference when available</p>
          </div>
          <input type="checkbox" className={styles.toggle} defaultChecked />
        </div>

        <div className={styles.settingItem}>
          <div className={styles.settingLabel}>
            <h4>Cache Model Metadata</h4>
            <p>Store model information locally to improve search speed</p>
          </div>
          <input type="checkbox" className={styles.toggle} defaultChecked />
        </div>
      </div>

      {/* About Section */}
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>About</h2>
        <div className={styles.aboutContent}>
          <p className={styles.aboutText}>
            <strong>Cortex OS</strong> v1.0.0
          </p>
          <p className={styles.aboutText}>
            A modern, distraction-free AI workspace for developers.
          </p>
          <p className={styles.aboutText}>
            Built with React, FastAPI, and Ollama.
          </p>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
