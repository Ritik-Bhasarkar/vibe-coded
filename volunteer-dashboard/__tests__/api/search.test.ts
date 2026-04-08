/**
 * @jest-environment node
 */
import { GET } from '@/app/api/search/route';
import * as serper from '@/lib/serper';

jest.mock('@/lib/serper');

const mockSearchVolunteers = serper.searchVolunteers as jest.MockedFunction<
  typeof serper.searchVolunteers
>;

function makeRequest(params: Record<string, string>) {
  const url = new URL('http://localhost/api/search');
  Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  return new Request(url.toString());
}

describe('GET /api/search', () => {
  beforeEach(() => jest.resetAllMocks());

  it('returns 400 when location is missing', async () => {
    const res = await GET(makeRequest({}));
    expect(res.status).toBe(400);
    const body = await res.json();
    expect(body.error).toMatch(/location/i);
  });

  it('returns results on success', async () => {
    mockSearchVolunteers.mockResolvedValue([
      {
        title: 'Park Clean-up',
        snippet: 'Join our weekly clean-up.',
        link: 'https://example.com',
        displayUrl: 'example.com',
      },
    ]);

    const res = await GET(makeRequest({ location: 'Austin' }));
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.results).toHaveLength(1);
    expect(body.results[0].title).toBe('Park Clean-up');
    expect(mockSearchVolunteers).toHaveBeenCalledWith({
      location: 'Austin',
      category: undefined,
      platform: undefined,
      hostelsOnly: false,
    });
  });

  it('passes category param to searchVolunteers', async () => {
    mockSearchVolunteers.mockResolvedValue([]);
    await GET(makeRequest({ location: 'Denver', category: 'animals' }));
    expect(mockSearchVolunteers).toHaveBeenCalledWith({
      location: 'Denver',
      category: 'animals',
      platform: undefined,
      hostelsOnly: false,
    });
  });

  it('returns 500 when searchVolunteers throws', async () => {
    mockSearchVolunteers.mockRejectedValue(new Error('API down'));
    const res = await GET(makeRequest({ location: 'NYC' }));
    expect(res.status).toBe(500);
    const body = await res.json();
    expect(body.error).toBeDefined();
  });
});
