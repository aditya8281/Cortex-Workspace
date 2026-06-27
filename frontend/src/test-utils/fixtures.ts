export const mockMemoryItem = {
  id: 'mem_001',
  content: 'Test memory content for unit testing',
  metadata: { source: 'test', tags: ['testing', 'fixtures'] },
  createdAt: '2026-06-27T10:00:00Z',
  updatedAt: '2026-06-27T10:00:00Z',
};

export const mockMemorySearchResult = {
  item: mockMemoryItem,
  score: 0.95,
  highlights: ['Test memory <mark>content</mark> for unit testing'],
};

export const mockMemoryStats = {
  totalItems: 150,
  totalSize: 75000,
  lastIndexed: '2026-06-27T09:00:00Z',
};

export const mockUser = {
  id: 'test_user_0001',
  email: 'test@corTex.dev',
  name: 'Test User',
  createdAt: '2026-01-01T00:00:00Z',
};

export function createApiSuccessResponse<T>(data: T) {
  return { data, status: 200 };
}

export function createApiErrorResponse(code: string, message: string) {
  return { error: { code, message }, status: 400 };
}
