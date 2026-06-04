import React, { useState, useMemo } from 'react';
import styles from '@/styles/MemoryPage.module.css';
import { Search, Brain, TrendingUp, Zap } from 'lucide-react';

interface MemoryItem {
  id: string;
  title: string;
  preview: string;
  category: string;
  relevance: number;
  timestamp: string;
  tags: string[];
}

const MOCK_MEMORIES: MemoryItem[] = [
  {
    id: '1',
    title: 'Model Performance Benchmarks',
    preview: 'Comparison of different model sizes for coding tasks...',
    category: 'Research',
    relevance: 0.95,
    timestamp: '2 days ago',
    tags: ['models', 'performance', 'coding'],
  },
  {
    id: '2',
    title: 'LLM Fine-tuning Guide',
    preview: 'Complete guide on fine-tuning language models with LoRA...',
    category: 'Knowledge',
    relevance: 0.88,
    timestamp: '1 week ago',
    tags: ['training', 'llm', 'guide'],
  },
  {
    id: '3',
    title: 'API Integration Notes',
    preview: 'Notes on integrating multiple LLM providers...',
    category: 'Notes',
    relevance: 0.72,
    timestamp: '3 weeks ago',
    tags: ['api', 'integration', 'providers'],
  },
];

export const MemoryPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const categories = ['Research', 'Knowledge', 'Notes', 'Code', 'Ideas'];

  const filteredMemories = useMemo(() => {
    return MOCK_MEMORIES.filter((memory) => {
      const matchesSearch =
        searchQuery === '' ||
        memory.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        memory.preview.toLowerCase().includes(searchQuery.toLowerCase()) ||
        memory.tags.some((tag) => tag.toLowerCase().includes(searchQuery.toLowerCase()));

      const matchesCategory = selectedCategory === null || memory.category === selectedCategory;

      return matchesSearch && matchesCategory;
    });
  }, [searchQuery, selectedCategory]);

  const totalMemories = MOCK_MEMORIES.length;
  const avgRelevance = (
    MOCK_MEMORIES.reduce((sum, m) => sum + m.relevance, 0) / MOCK_MEMORIES.length * 100
  ).toFixed(0);

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>Memory</h1>
        <p className={styles.subtitle}>Searchable knowledge graph with semantic search</p>
      </div>

      {/* Stats */}
      <div className={styles.statsRow}>
        <div className={styles.statSmall}>
          <Brain size={16} style={{ color: '#3b82f6' }} />
          <div>
            <div className={styles.statSmallLabel}>Total Memories</div>
            <div className={styles.statSmallValue}>{totalMemories}</div>
          </div>
        </div>
        <div className={styles.statSmall}>
          <TrendingUp size={16} style={{ color: '#10b981' }} />
          <div>
            <div className={styles.statSmallLabel}>Avg Relevance</div>
            <div className={styles.statSmallValue}>{avgRelevance}%</div>
          </div>
        </div>
        <div className={styles.statSmall}>
          <Zap size={16} style={{ color: '#f59e0b' }} />
          <div>
            <div className={styles.statSmallLabel}>Last Updated</div>
            <div className={styles.statSmallValue}>2 days ago</div>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className={styles.searchSection}>
        <div className={styles.searchContainer}>
          <Search size={16} className={styles.searchIcon} />
          <input
            type="text"
            placeholder="Search memories, tags, notes..."
            className={styles.searchInput}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className={styles.filterRow}>
          <button
            className={`${styles.filterButton} ${selectedCategory === null ? styles.filterButtonActive : ''}`}
            onClick={() => setSelectedCategory(null)}
          >
            All
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              className={`${styles.filterButton} ${selectedCategory === cat ? styles.filterButtonActive : ''}`}
              onClick={() => setSelectedCategory(cat)}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      <div className={styles.content}>
        {filteredMemories.length === 0 ? (
          <div className={styles.emptyState}>
            <Brain size={40} style={{ color: '#606060' }} />
            <h3>No memories found</h3>
            <p>Try adjusting your search or filters</p>
          </div>
        ) : (
          <div className={styles.memoryList}>
            {filteredMemories.map((memory) => (
              <div key={memory.id} className={styles.memoryCard}>
                <div className={styles.cardHeader}>
                  <h3 className={styles.cardTitle}>{memory.title}</h3>
                  <div className={styles.relevanceBadge}>
                    {(memory.relevance * 100).toFixed(0)}% match
                  </div>
                </div>

                <p className={styles.cardPreview}>{memory.preview}</p>

                <div className={styles.cardFooter}>
                  <div className={styles.categoryBadge}>{memory.category}</div>
                  <span className={styles.timestamp}>{memory.timestamp}</span>
                </div>

                <div className={styles.tagsList}>
                  {memory.tags.map((tag) => (
                    <span key={tag} className={styles.tag}>
                      #{tag}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MemoryPage;
