import { buildSearchQuery, searchVolunteers } from '@/lib/serper';

const SITE_FILTER = '(site:workaway.info OR site:worldpackers.com OR site:volunteeryatra.com OR site:instagram.com)';
const BLOG_EXCL = '-inurl:blog -inurl:/blog/ -inurl:article -inurl:post';

describe('buildSearchQuery', () => {
  it('builds query with location only', () => {
    expect(buildSearchQuery({ location: 'New York' }))
      .toBe(`volunteer near New York ${SITE_FILTER} ${BLOG_EXCL}`);
  });

  it('builds query with location and category', () => {
    expect(buildSearchQuery({ location: 'London', category: 'environment' }))
      .toBe(`volunteer environment near London ${SITE_FILTER} ${BLOG_EXCL}`);
  });

  it('ignores empty category', () => {
    expect(buildSearchQuery({ location: 'Austin', category: '' }))
      .toBe(`volunteer near Austin ${SITE_FILTER} ${BLOG_EXCL}`);
  });

  it('includes all target platform sites', () => {
    const query = buildSearchQuery({ location: 'NYC' });
    expect(query).toContain('site:workaway.info');
    expect(query).toContain('site:worldpackers.com');
    expect(query).toContain('site:volunteeryatra.com');
    expect(query).toContain('site:instagram.com');
  });

  it('excludes blog paths', () => {
    const query = buildSearchQuery({ location: 'NYC' });
    expect(query).toContain('-inurl:blog');
  });
});

describe('searchVolunteers', () => {
  beforeEach(() => {
    jest.resetAllMocks();
    process.env.SERPER_API_KEY = 'test-key';
  });

  it('calls Serper API and returns normalized results', async () => {
    const mockResponse = {
      organic: [
        {
          title: 'Help at Food Bank',
          snippet: 'Join us every Saturday.',
          link: 'https://example.com/food-bank',
          displayLink: 'example.com',
        },
      ],
    };

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    } as Response);

    const results = await searchVolunteers({ location: 'New York' });

    expect(fetch).toHaveBeenCalledWith(
      'https://google.serper.dev/search',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'X-API-KEY': 'test-key',
        }),
        body: expect.stringContaining('New York'),
      })
    );

    expect(results).toEqual([
      {
        title: 'Help at Food Bank',
        snippet: 'Join us every Saturday.',
        link: 'https://example.com/food-bank',
        displayUrl: 'example.com',
      },
    ]);
  });

  it('throws when API responds with non-ok status', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 403,
    } as Response);

    await expect(searchVolunteers({ location: 'NYC' })).rejects.toThrow(
      'Serper API error: 403'
    );
  });

  it('returns empty array when organic is missing', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({}),
    } as Response);

    const results = await searchVolunteers({ location: 'NYC' });
    expect(results).toEqual([]);
  });
});
