import type { OpportunityResult, SearchParams } from '@/types';

const ALL_PLATFORM_SITES = [
  'site:workaway.info',
  'site:worldpackers.com',
  'site:volunteeryatra.com',
  'site:instagram.com',
].join(' OR ');

const PLATFORM_SITE_MAP: Record<string, string> = {
  Workaway: 'site:workaway.info',
  Worldpackers: 'site:worldpackers.com',
  VolunteerYatra: 'site:volunteeryatra.com',
  Instagram: 'site:instagram.com',
};

const BLOG_EXCLUSIONS = '-inurl:blog -inurl:/blog/ -inurl:article -inurl:post';

export function buildSearchQuery({ location, category, platform, hostelsOnly }: SearchParams): string {
  const cat = category?.trim() ? `${category.trim()} ` : '';
  const hostel = hostelsOnly ? 'hostel ' : '';
  const sites =
    platform && platform !== 'All' && PLATFORM_SITE_MAP[platform]
      ? PLATFORM_SITE_MAP[platform]
      : ALL_PLATFORM_SITES;
  return `volunteer ${cat}${hostel}near ${location} (${sites}) ${BLOG_EXCLUSIONS}`;
}

export async function searchVolunteers(
  params: SearchParams
): Promise<OpportunityResult[]> {
  const query = buildSearchQuery(params);
  const apiKey = process.env.SERPER_API_KEY;

  const response = await fetch('https://google.serper.dev/search', {
    method: 'POST',
    headers: {
      'X-API-KEY': apiKey ?? '',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ q: query, num: 10 }),
  });

  if (!response.ok) {
    throw new Error(`Serper API error: ${response.status}`);
  }

  const data = await response.json();
  const organic: Record<string, string>[] = data.organic ?? [];

  return organic.map((item) => ({
    title: item.title ?? '',
    snippet: item.snippet ?? '',
    link: item.link ?? '',
    displayUrl: item.displayLink ?? '',
  }));
}
