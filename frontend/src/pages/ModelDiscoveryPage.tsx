import React, { useState } from 'react';
import { Search, Download, Check, AlertCircle, Loader, RefreshCw } from 'lucide-react';
import { useOllamaRegistry } from '@/hooks/useOllamaRegistry';

interface ModelCardProps {
  model: any;
  onPull: (modelId: string) => void;
  isDownloading: boolean;
  progress?: number;
}

const ModelCard: React.FC<ModelCardProps> = ({ model, onPull, isDownloading, progress = 0 }) => {
  return (
    <div className="border rounded-lg p-4 hover:shadow-lg transition-shadow bg-white">
      <div className="flex justify-between items-start mb-2">
        <div>
          <h3 className="font-semibold text-lg">{model.display_name}</h3>
          <p className="text-sm text-gray-600">{model.model_id}</p>
        </div>
        {model.is_installed && (
          <span className="flex items-center gap-1 bg-green-100 text-green-700 px-2 py-1 rounded text-xs font-medium">
            <Check size={14} /> Installed
          </span>
        )}
      </div>

      <p className="text-sm text-gray-700 mb-3 line-clamp-2">{model.description}</p>

      <div className="flex flex-wrap gap-2 mb-3">
        {model.tags?.slice(0, 3).map((tag: string, idx: number) => (
          <span key={idx} className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs">
            {tag}
          </span>
        ))}
        {model.tags?.length > 3 && (
          <span className="text-xs text-gray-500">+{model.tags.length - 3} more</span>
        )}
      </div>

      <div className="flex flex-wrap gap-4 text-xs text-gray-600 mb-3">
        {model.parameters && <div>📦 {model.parameters}</div>}
        {model.context_length && <div>📚 {model.context_length}k context</div>}
        <div>⚙️ {model.quantization}</div>
      </div>

      <div className="flex flex-wrap gap-1 mb-3">
        {model.capabilities?.map((cap: string, idx: number) => (
          <span key={idx} className="bg-purple-50 text-purple-700 px-2 py-1 rounded text-xs font-medium">
            {cap}
          </span>
        ))}
      </div>

      {isDownloading ? (
        <div className="w-full">
          <div className="flex justify-between text-xs text-gray-600 mb-1">
            <span>Downloading...</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      ) : (
        <button
          onClick={() => onPull(model.model_id)}
          disabled={model.is_installed}
          className={`w-full py-2 px-3 rounded font-medium flex items-center justify-center gap-2 text-sm transition ${
            model.is_installed
              ? 'bg-gray-100 text-gray-600 cursor-not-allowed'
              : 'bg-blue-500 text-white hover:bg-blue-600 active:scale-95'
          }`}
        >
          <Download size={16} />
          {model.is_installed ? 'Installed' : 'Pull Model'}
        </button>
      )}
    </div>
  );
};

interface TabName {
  id: string;
  label: string;
}

export const ModelDiscoveryPage: React.FC = () => {
  const registry = useOllamaRegistry();

  const [activeTab, setActiveTab] = useState<string>('explore');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCapability, setSelectedCapability] = useState<string | undefined>();
  const [selectedSize, setSelectedSize] = useState<string | undefined>();
  const [selectedTask, setSelectedTask] = useState<string | undefined>();
  const [downloadingModel, setDownloadingModel] = useState<string | null>(null);
  const [downloadProgress, setDownloadProgress] = useState<Record<string, number>>({});

  // Query data
  const allModelsQuery = registry.useAllModels();
  const searchQuery_result = registry.useSearchModels(searchQuery, selectedCapability, undefined, selectedSize);
  const installedModelsQuery = registry.useInstalledModels();
  const recommendationsQuery = registry.useRecommendations(selectedTask);

  // Mutations
  const syncMutation = registry.useSyncRegistry();
  const pullMutation = registry.usePullModel();

  const handlePullModel = async (modelId: string) => {
    try {
      setDownloadingModel(modelId);
      await pullMutation.mutateAsync(modelId);
      // TODO: Set up WebSocket/polling for progress updates
      setDownloadProgress((prev) => ({ ...prev, [modelId]: 0 }));
    } catch (error) {
      console.error('Failed to pull model:', error);
      setDownloadingModel(null);
    }
  };

  const handleSync = async () => {
    try {
      await syncMutation.mutateAsync(true);
    } catch (error) {
      console.error('Sync failed:', error);
    }
  };

  const tabs: TabName[] = [
    { id: 'explore', label: 'Explore Models' },
    { id: 'installed', label: 'Installed' },
    { id: 'recommendations', label: 'Recommended' },
  ];

  const capabilities = ['chat', 'coding', 'vision', 'reasoning', 'embedding', 'fast', 'long-context'];
  const sizes = ['small', 'medium', 'large'];
  const tasks = ['chat', 'coding', 'vision', 'reasoning', 'fast', 'embedding'];

  // Determine which data to show based on active tab
  let displayModels: any[] = [];
  let isLoading = false;

  if (activeTab === 'explore') {
    if (searchQuery) {
      displayModels = searchQuery_result.data?.models || [];
      isLoading = searchQuery_result.isLoading;
    } else {
      displayModels = allModelsQuery.data?.models || [];
      isLoading = allModelsQuery.isLoading;
    }
  } else if (activeTab === 'installed') {
    displayModels = installedModelsQuery.data?.models || [];
    isLoading = installedModelsQuery.isLoading;
  } else if (activeTab === 'recommendations') {
    displayModels = recommendationsQuery.data?.recommendations || [];
    isLoading = recommendationsQuery.isLoading;
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Model Discovery</h1>
          <p className="text-gray-600">Browse and download AI models from Ollama library</p>
        </div>
        <button
          onClick={handleSync}
          disabled={syncMutation.isPending}
          className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
        >
          <RefreshCw size={18} className={syncMutation.isPending ? 'animate-spin' : ''} />
          Sync
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === tab.id
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Search and Filters - only show in Explore tab */}
      {activeTab === 'explore' && (
        <div className="space-y-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-3 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search models by name, capability, or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Filter buttons */}
          <div className="space-y-3">
            {/* Capabilities */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Capabilities</label>
              <div className="flex flex-wrap gap-2">
                {capabilities.map((cap) => (
                  <button
                    key={cap}
                    onClick={() => setSelectedCapability(selectedCapability === cap ? undefined : cap)}
                    className={`px-3 py-1 rounded text-sm font-medium transition ${
                      selectedCapability === cap
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {cap}
                  </button>
                ))}
              </div>
            </div>

            {/* Size filters */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Model Size</label>
              <div className="flex flex-wrap gap-2">
                {sizes.map((size) => (
                  <button
                    key={size}
                    onClick={() => setSelectedSize(selectedSize === size ? undefined : size)}
                    className={`px-3 py-1 rounded text-sm font-medium transition ${
                      selectedSize === size
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {size}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recommendations task selector */}
      {activeTab === 'recommendations' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Task</label>
          <div className="flex flex-wrap gap-2">
            {tasks.map((task) => (
              <button
                key={task}
                onClick={() => setSelectedTask(selectedTask === task ? undefined : task)}
                className={`px-3 py-1 rounded text-sm font-medium transition ${
                  selectedTask === task
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {task}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Models Grid */}
      {isLoading ? (
        <div className="flex justify-center items-center py-12">
          <Loader className="animate-spin text-blue-500" size={32} />
        </div>
      ) : displayModels.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <AlertCircle className="mx-auto text-gray-400 mb-2" size={32} />
          <p className="text-gray-600">
            {activeTab === 'installed'
              ? 'No models installed. Explore and download some models!'
              : activeTab === 'recommendations'
              ? 'Select a task to see recommendations'
              : 'No models found. Try adjusting your filters.'}
          </p>
        </div>
      ) : (
        <div>
          <p className="text-sm text-gray-600 mb-4">
            Found {displayModels.length} model{displayModels.length !== 1 ? 's' : ''}
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {displayModels.map((model) => (
              <ModelCard
                key={model.model_id}
                model={model}
                onPull={handlePullModel}
                isDownloading={downloadingModel === model.model_id}
                progress={downloadProgress[model.model_id] || 0}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelDiscoveryPage;
