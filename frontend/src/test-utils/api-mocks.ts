import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

export const handlers = [
  http.get('/api/v1/memory/search', () => {
    return HttpResponse.json({
      data: [
        { id: '1', content: 'Test memory', score: 0.95 },
        { id: '2', content: 'Another memory', score: 0.87 },
      ],
    });
  }),
  http.get('/api/v1/memory/stats', () => {
    return HttpResponse.json({
      data: { totalItems: 100, totalSize: 50000, lastIndexed: '2026-01-01' },
    });
  }),
  http.get('/api/v1/auth/me', () => {
    return HttpResponse.json({
      data: { id: 'test_user', email: 'test@example.com', name: 'Test User' },
    });
  }),
  http.all('*', ({ request }) => {
    console.warn(`Unhandled request: ${request.method} ${request.url}`);
    return HttpResponse.json({ error: 'Not mocked' }, { status: 404 });
  }),
];

export const server = setupServer(...handlers);

export function overrideHandler(
  method: 'get' | 'post' | 'put' | 'delete',
  url: string,
  response: unknown,
) {
  server.use(http[method](url, () => HttpResponse.json(response)));
}
