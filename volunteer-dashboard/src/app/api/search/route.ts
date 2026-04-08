import { NextResponse } from 'next/server';
import { searchVolunteers } from '@/lib/serper';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const location = searchParams.get('location')?.trim();
  const category = searchParams.get('category') ?? undefined;
  const platform = searchParams.get('platform') ?? undefined;
  const hostelsOnly = searchParams.get('hostelsOnly') === 'true';

  if (!location) {
    return NextResponse.json(
      { error: 'location parameter is required' },
      { status: 400 }
    );
  }

  try {
    const results = await searchVolunteers({ location, category, platform, hostelsOnly });
    return NextResponse.json({ results });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
