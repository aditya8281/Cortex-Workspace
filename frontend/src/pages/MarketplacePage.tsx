import React, { useState, useMemo } from 'react';
import {
  Search,
  Download,
  Check,
  Zap,
  Code,
  Eye,
  Database,
  TrendingUp,
  X,
  Copy,
  ExternalLink,
  Cpu,
  Gauge,
} from 'lucide-react';
import { useOllamaRegistry } from '@/hooks/useOllamaRegistry';
import styles from '@/styles/MarketplacePage.module.css';

type SortBy = 'popular' | 'smallest' | 'newest' | 'for-coding';

interface ModelDetailsPanel {
  modelId: string;
  isOpen: boolean;
}

const CAPABILITY_ICONS: Record<string, React.ReactNode> = {
  chat: <Zap size={16} />,
  coding: <Code size={16} />,
  vision: <Eye size={16} />,
  embedding: <Database size={16} />,
  reasoning: <TrendingUp size={16} />,
  fast: <Gauge size={16} />,
};

const ModelCard: React.FC<{
  model: any;
  isInstalled: boolean;
  isDownloading: boolean;
  onDownload: (modelId: string) => void;
  onDetails: (modelId: string) => void;
}> = ({ model, isInstalled, isDownloading, onDownload, onDetails }) => {
  const getPerformanceHint = (params?: string): string => {
    if (!params) return 'Balanced';
    const sizeStr = params.replace('B', '');
    const size = parseFloat(sizeStr);
    if (size < 10) return 'Fast';
    if (size < 30) return 'Balanced';
    return 'Heavy';
  };

  const performanceHint = getPerformanceHint(model.parameters);
  const performanceColor =
    performanceHint === 'Fast' ? '#10b981' : performanceHint === 'Balanced' ? '#3b82f6' : '#f59e0b';

  return (
    <div
      className={`${styles.modelCard} ${isInstalled ? styles.modelCardInstalled : ''} ${
        isDownloading ? styles.modelCardDownloading : ''
      }`}
    >
      <div className={styles.cardGradient}></div>
      <div className={styles.cardContent}>
        <div className={styles.cardHeader}>
          <div className={styles.cardTitle}>{model.display_name || model.model_id}</div>
          {isInstalled && (
            <div className={styles.installedBadge}>
              <Check size={14} />
              Installed
            </div>
          )}
        </div>

        <div className={styles.modelId}>{model.model_id}</div>
        <p className={styles.description}>{model.description || 'No description available'}</p>

        {model.capabilities && model.capabilities.length > 0 && (
          <div className={styles.capabilities}>
            {model.capabilities.slice(0, 3).map((cap: string) => (
              <div key={cap} className={styles.capabilityTag} title={cap}>
                {CAPABILITY_ICONS[cap] || <Zap size={14} />}
                <span>{cap}</span>
              </div>
            ))}
            {model.capabilities.length > 3 && (
              <div className={styles.capabilityMore}>+{model.capabilities.length - 3}</div>
            )}
          </div>
        )}

        <div className={styles.specs}>
          {model.parameters && (
            <div className={styles.spec}>
              <span className={styles.specLabel}>Size</span>
              <span className={styles.specValue}>{model.parameters}</span>
            </div>
          )}
          <div className={styles.spec}>
            <span className={styles.specLabel}>Performance</span>
            <span className={styles.specValue} style={{ color: performanceColor }}>
              {performanceHint}
            </span>
          </div>
          {model.quantization && (
            <div className={styles.spec}>
              <span className={styles.specLabel}>Quant</span>
              <span className={styles.specValue}>{model.quantization}</span>
            </div>
          )}
        </div>

        <div className={styles.actions}>
          {isDownloading ? (
            <button className={styles.buttonLoading} disabled>
              <div className={styles.loadingSpinner}></div>
              Installing...
            </button>
          ) : isInstalled ? (
            <button className={styles.buttonInstalled} disabled>
              <Check size={16} />
              Open
            </button>
          ) : (
            <button className={styles.buttonPrimary} onClick={() => onDownload(model.model_id)}>
              <Download size={16} />
              Download
            </button>
          )}
          <button className={styles.buttonSecondary} onClick={() => onDetails(model.model_id)}>
            Details
          </button>
        </div>
      </div>
    </div>
  );
};

const ModelDetailsPanel: React.FC<{
  model: any | null;
  isOpen: boolean;
  onClose: () => void;
  isInstalled: boolean;
  onDownload: (modelId: string) => void;
}> = ({ model, isOpen, onClose, isInstalled, onDownload }) => {
  if (!model) return null;

  return (
    <>
      {isOpen && <div className={styles.panelOverlay} onClick={onClose}></div>}
      <div className={`${styles.detailsPanel} ${isOpen ? styles.detailsPanelOpen : ''}`}>
        <div className={styles.panelHeader}>
          <div>
            <h2 className={styles.panelTitle}>{model.display_name}</h2>
            <p className={styles.panelSubtitle}>{model.model_id}</p>
          </div>
          <button className={styles.closeButton} onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className={styles.panelContent}>
          <section className={styles.panelSection}>
            <h3 className={styles.panelSectionTitle}>Description</h3>
            <p className={styles.panelText}>{model.description || 'No description available'}</p>
          </section>

          <section className={styles.panelSection}>
            <h3 className={styles.panelSectionTitle}>Specifications</h3>
            <div className={styles.specGrid}>
              {model.parameters && (
                <div className={styles.specItem}>
                  <span className={styles.specItemLabel}>Parameters</span>
                  <span className={styles.specItemValue}>{model.parameters}</span>
                </div>
              )}
              {model.context_length && (
                <div className={styles.specItem}>
                  <span className={styles.specItemLabel}>Context Length</span>
                  <span className={styles.specItemValue}>{model.context_length.toLocaleString()} tokens</span>
                </div>
              )}
              {model.quantization && (
                <div className={styles.specItem}>
                  <span className={styles.specItemLabel}>Quantization</span>
                  <span className={styles.specItemValue}>{model.quantization}</span>
                </div>
              )}
              {model.family && (
                <div className={styles.specItem}>
                  <span className={styles.specItemLabel}>Family</span>
                  <span className={styles.specItemValue}>{model.family}</span>
                </div>
              )}
            </div>
          </section>

          {model.capabilities && model.capabilities.length > 0 && (
            <section className={styles.panelSection}>
              <h3 className={styles.panelSectionTitle}>Capabilities</h3>
              <div className={styles.capabilityGrid}>
                {model.capabilities.map((cap: string) => (
                  <div key={cap} className={styles.capabilityItem}>
                    {CAPABILITY_ICONS[cap] || <Zap size={16} />}
                    <span>{cap}</span>
                  </div>
                ))}
              </div>
            </section>
          )}

          <section className={styles.panelSection}>
            <h3 className={styles.panelSectionTitle}>Hardware Estimate</h3>
            <div className={styles.hardwareEstimate}>
              <div className={styles.hardwareItem}>
                <Cpu size={16} />
                <span>GPU: ~{model.parameters?.replace('B', '') || '8'}GB VRAM minimum</span>
              </div>
              <div className={styles.hardwareItem}>
                <Database size={16} />
                <span>Disk: ~{((parseInt(model.parameters || '8') * 4) / 1000).toFixed(1)}GB space</span>
              </div>
            </div>
          </section>

          <section className={styles.panelSection}>
            <h3 className={styles.panelSectionTitle}>Installation Command</h3>
            <div className={styles.commandBox}>
              <code>{model.pull_command || `ollama pull ${model.model_id}`}</code>
              <button
                className={styles.copyButton}
                onClick={() => {
                  navigator.clipboard.writeText(model.pull_command || `ollama pull ${model.model_id}`);
                }}
              >
                <Copy size={14} />
              </button>
            </div>
          </section>

          {model.source_url && (
            <section className={styles.panelSection}>
              <a href={model.source_url} target="_blank" rel="noopener noreferrer" className={styles.sourceLink}>
                View on Ollama Library
                <ExternalLink size={14} />
              </a>
            </section>
          )}
        </div>

        <div className={styles.panelFooter}>
          {isInstalled ? (
            <button className={styles.buttonInstalled} disabled>
              <Check size={16} />
              Installed
            </button>
          ) : (
            <button className={styles.buttonPrimary} onClick={() => onDownload(model.model_id)}>
              <Download size={16} />
              Download Model
            </button>
          )}
        </div>
      </div>
    </>
  );
};

export const MarketplacePage: React.FC = () => {
  const registry = useOllamaRegistry();

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCapability, setSelectedCapability] = useState<string | null>(null);
  const [selectedSize, setSelectedSize] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<SortBy>('popular');
  const [detailsPanel, setDetailsPanel] = useState<ModelDetailsPanel>({ modelId: '', isOpen: false });

  const allModelsQuery = registry.useAllModels();
  const installedModelsQuery = registry.useInstalledModels();
  const pullMutation = registry.usePullModel();
  const syncMutation = registry.useSyncRegistry();

  const installedModelIds = useMemo(
    () => new Set(installedModelsQuery.data?.models?.map((m: any) => m.model_id) || []),
    [installedModelsQuery.data],
  );

  const displayModels = useMemo(() => {
    let models = allModelsQuery.data?.models || [];

    if (selectedCapability) {
      const capLower = selectedCapability.toLowerCase();
      models = models.filter((m: any) =>
        m.capabilities?.some((c: string) => c.toLowerCase().includes(capLower)),
      );
    }

    if (selectedSize) {
      if (selectedSize === 'small') {
        models = models.filter((m: any) => {
          const size = parseInt(m.parameters || '0');
          return size < 10;
        });
      } else if (selectedSize === 'large') {
        models = models.filter((m: any) => {
          const size = parseInt(m.parameters || '0');
          return size > 30;
        });
      }
    }

    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      models = models.filter(
        (m: any) =>
          m.model_id.toLowerCase().includes(q) ||
          m.display_name.toLowerCase().includes(q) ||
          (m.description || '').toLowerCase().includes(q),
      );
    }

    if (sortBy === 'smallest') {
      models = [...models].sort((a: any, b: any) => {
        const aSize = parseInt(a.parameters || '999');
        const bSize = parseInt(b.parameters || '999');
        return aSize - bSize;
      });
    } else if (sortBy === 'newest') {
      models = [...models].sort(
        (a: any, b: any) =>
          new Date(b.last_synced_at || 0).getTime() - new Date(a.last_synced_at || 0).getTime(),
      );
    }

    return models;
  }, [allModelsQuery.data?.models, selectedCapability, selectedSize, searchQuery, sortBy]);

  const detailModel = useMemo(
    () => displayModels.find((m: any) => m.model_id === detailsPanel.modelId),
    [displayModels, detailsPanel.modelId],
  );

  const handleDownload = async (modelId: string) => {
    try {
      await pullMutation.mutateAsync(modelId);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const handleSync = async () => {
    try {
      await syncMutation.mutateAsync(true);
    } catch (error) {
      console.error('Sync failed:', error);
    }
  };

  const isLoading = allModelsQuery.isLoading || installedModelsQuery.isLoading;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.headerTop}>
          <div>
            <h1 className={styles.title}>Model Marketplace</h1>
            <p className={styles.subtitle}>Browse and download AI models from Ollama library</p>
          </div>
          <button className={styles.syncButton} onClick={handleSync} disabled={syncMutation.isPending}>
            {syncMutation.isPending ? (
              <>
                <div className={styles.syncSpinner}></div>
                Syncing...
              </>
            ) : (
              <>Sync Library</>
            )}
          </button>
        </div>

        <div className={styles.searchContainer}>
          <Search className={styles.searchIcon} size={20} />
          <input
            type="text"
            placeholder="Search models by name, capability, or description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={styles.searchInput}
          />
        </div>

        <div className={styles.filtersRow}>
          <div className={styles.filterGroup}>
            {['chat', 'coding', 'vision'].map((cap) => (
              <button
                key={cap}
                className={`${styles.filterChip} ${
                  selectedCapability?.toLowerCase() === cap ? styles.filterChipActive : ''
                }`}
                onClick={() =>
                  setSelectedCapability(selectedCapability?.toLowerCase() === cap ? null : cap)
                }
              >
                {cap.charAt(0).toUpperCase() + cap.slice(1)}
              </button>
            ))}
          </div>

          <div className={styles.filterGroup}>
            {['small', 'large'].map((size) => (
              <button
                key={size}
                className={`${styles.filterChip} ${
                  selectedSize?.toLowerCase() === size ? styles.filterChipActive : ''
                }`}
                onClick={() => setSelectedSize(selectedSize?.toLowerCase() === size ? null : size)}
              >
                {size === 'small' ? 'Small / Fast' : 'Large / Powerful'}
              </button>
            ))}
          </div>

          <select value={sortBy} onChange={(e) => setSortBy(e.target.value as SortBy)} className={styles.sortDropdown}>
            <option value="popular">Most Popular</option>
            <option value="smallest">Smallest First</option>
            <option value="newest">Newest</option>
            <option value="for-coding">Best for Coding</option>
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className={styles.loadingState}>
          <div className={styles.loadingSpinner}></div>
          <p>Loading models...</p>
        </div>
      ) : displayModels.length === 0 ? (
        <div className={styles.emptyState}>
          <Search size={48} />
          <h3>No models found</h3>
          <p>Try adjusting your filters or search terms</p>
        </div>
      ) : (
        <>
          <div className={styles.resultsInfo}>
            Found {displayModels.length} model{displayModels.length !== 1 ? 's' : ''}
          </div>

          <div className={styles.grid}>
            {displayModels.map((model: any) => (
              <ModelCard
                key={model.model_id}
                model={model}
                isInstalled={installedModelIds.has(model.model_id)}
                isDownloading={false}
                onDownload={handleDownload}
                onDetails={(modelId) => setDetailsPanel({ modelId, isOpen: true })}
              />
            ))}
          </div>
        </>
      )}

      <ModelDetailsPanel
        model={detailModel}
        isOpen={detailsPanel.isOpen}
        onClose={() => setDetailsPanel({ modelId: '', isOpen: false })}
        isInstalled={installedModelIds.has(detailsPanel.modelId)}
        onDownload={handleDownload}
      />
    </div>
  );
};

export default MarketplacePage;
