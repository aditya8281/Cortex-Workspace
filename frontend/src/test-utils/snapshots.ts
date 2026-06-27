import { waitFor } from '@testing-library/react';

export async function expectSnapshotWhenReady(
  container: HTMLElement,
  options?: { timeout?: number },
) {
  await waitFor(
    () => {
      expect(container).toMatchSnapshot();
    },
    { timeout: options?.timeout ?? 5000 },
  );
}

export function normalizeForSnapshot(obj: unknown): unknown {
  if (typeof obj === 'string') {
    return obj.replace(/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z/g, '<TIMESTAMP>');
  }
  if (Array.isArray(obj)) {
    return obj.map(normalizeForSnapshot);
  }
  if (typeof obj === 'object' && obj !== null) {
    const normalized: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(obj)) {
      if (key === 'id' && typeof value === 'string') {
        normalized[key] = '<ID>';
      } else {
        normalized[key] = normalizeForSnapshot(value);
      }
    }
    return normalized;
  }
  return obj;
}
