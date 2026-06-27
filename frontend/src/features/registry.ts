// Feature Registry — Centralized feature registration for routing and navigation.
// Each feature module exports a FEATURE constant. This file aggregates them.

import { lazy, type ComponentType, type LazyExoticComponent } from 'react';

export interface FeatureMetadata {
  id: string;
  name: string;
  description: string;
  icon?: string;
  routes: Array<{ path: string; label: string }>;
  sidebarOrder: number;
  enabled: boolean;
}

export interface RegisteredFeature extends FeatureMetadata {
  component: LazyExoticComponent<ComponentType>;
}

// Lazy-loaded feature components
const LazyMemory = lazy(() => import('./memory'));
const LazyAwareness = lazy(() => import('./awareness'));
const LazyConversations = lazy(() => import('./conversations'));
const LazyRepositories = lazy(() => import('./repositories'));
const LazyDocuments = lazy(() => import('./documents'));
const LazySearch = lazy(() => import('./search'));
const LazyAgents = lazy(() => import('./agents'));
const LazyNotifications = lazy(() => import('./notifications'));
const LazySettings = lazy(() => import('./settings'));
const LazySystem = lazy(() => import('./system'));
const LazyUtility = lazy(() => import('./utility'));
const LazyIntegration = lazy(() => import('./integration'));

// Feature registry — single source of truth for all features
export const FEATURES: RegisteredFeature[] = [
  {
    id: 'memory',
    name: 'Memory',
    description: 'Long-term memory management and search',
    routes: [{ path: '/memory', label: 'Memory' }],
    sidebarOrder: 1,
    enabled: true,
    component: LazyMemory,
  },
  {
    id: 'awareness',
    name: 'Awareness',
    description: 'File system awareness and indexing',
    routes: [{ path: '/awareness', label: 'Awareness' }],
    sidebarOrder: 2,
    enabled: true,
    component: LazyAwareness,
  },
  {
    id: 'conversations',
    name: 'Conversations',
    description: 'Chat and conversation management',
    routes: [{ path: '/conversations', label: 'Conversations' }],
    sidebarOrder: 3,
    enabled: true,
    component: LazyConversations,
  },
  {
    id: 'repositories',
    name: 'Repositories',
    description: 'Repository browsing and management',
    routes: [{ path: '/repositories', label: 'Repositories' }],
    sidebarOrder: 4,
    enabled: true,
    component: LazyRepositories,
  },
  {
    id: 'documents',
    name: 'Documents',
    description: 'Document viewing and editing',
    routes: [{ path: '/documents', label: 'Documents' }],
    sidebarOrder: 5,
    enabled: true,
    component: LazyDocuments,
  },
  {
    id: 'search',
    name: 'Search',
    description: 'Search functionality',
    routes: [{ path: '/search', label: 'Search' }],
    sidebarOrder: 6,
    enabled: true,
    component: LazySearch,
  },
  {
    id: 'agents',
    name: 'Agents',
    description: 'Agent management and status',
    routes: [{ path: '/agents', label: 'Agents' }],
    sidebarOrder: 7,
    enabled: true,
    component: LazyAgents,
  },
  {
    id: 'notifications',
    name: 'Notifications',
    description: 'Notification center',
    routes: [{ path: '/notifications', label: 'Notifications' }],
    sidebarOrder: 8,
    enabled: true,
    component: LazyNotifications,
  },
  {
    id: 'settings',
    name: 'Settings',
    description: 'User settings and preferences',
    routes: [{ path: '/settings', label: 'Settings' }],
    sidebarOrder: 9,
    enabled: true,
    component: LazySettings,
  },
  {
    id: 'system',
    name: 'System',
    description: 'System health and monitoring',
    routes: [{ path: '/system', label: 'System' }],
    sidebarOrder: 10,
    enabled: true,
    component: LazySystem,
  },
  {
    id: 'utility',
    name: 'Utility',
    description: 'Utility tools and helpers',
    routes: [{ path: '/utility', label: 'Utility' }],
    sidebarOrder: 11,
    enabled: true,
    component: LazyUtility,
  },
  {
    id: 'integration',
    name: 'Integration',
    description: 'External integrations',
    routes: [{ path: '/integration', label: 'Integration' }],
    sidebarOrder: 12,
    enabled: true,
    component: LazyIntegration,
  },
];

// Utility functions
export function getFeatureById(id: string): RegisteredFeature | undefined {
  return FEATURES.find(f => f.id === id);
}

export function getEnabledFeatures(): RegisteredFeature[] {
  return FEATURES.filter(f => f.enabled);
}

export function getSidebarFeatures(): RegisteredFeature[] {
  return getEnabledFeatures().sort((a, b) => a.sidebarOrder - b.sidebarOrder);
}

export function getRoutes(): Array<{ path: string; component: LazyExoticComponent<ComponentType> }> {
  return getEnabledFeatures().flatMap(feature =>
    feature.routes.map(route => ({
      path: route.path,
      component: feature.component,
    }))
  );
}
