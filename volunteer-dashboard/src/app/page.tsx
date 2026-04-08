'use client';

import { useState } from 'react';
import SearchBar from '@/components/SearchBar';
import FilterBar from '@/components/FilterBar';
import ResultsGrid from '@/components/ResultsGrid';
import type { OpportunityResult, SearchParams } from '@/types';

const CATEGORIES = ['All', 'Community', 'Environment', 'Animals', 'Education', 'Healthcare'];
const PLATFORMS = ['All', 'Workaway', 'Worldpackers', 'Instagram', 'VolunteerYatra'];

export default function DashboardPage() {
  const [results, setResults] = useState<OpportunityResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);
  const [activeCategory, setActiveCategory] = useState('All');
  const [activePlatform, setActivePlatform] = useState('All');
  const [hostelsOnly, setHostelsOnly] = useState(false);
  const [currentLocation, setCurrentLocation] = useState('');

  async function handleSearch({ location, category, platform, hostelsOnly: ho }: SearchParams) {
    setLoading(true);
    setError(null);
    setCurrentLocation(location);

    const cat = category && category !== 'All' ? category.toLowerCase() : '';
    const params = new URLSearchParams({
      location,
      ...(cat ? { category: cat } : {}),
      ...(platform && platform !== 'All' ? { platform } : {}),
      ...(ho ? { hostelsOnly: 'true' } : {}),
    });

    try {
      const res = await fetch(`/api/search?${params}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? 'Search failed');
      setResults(data.results);
      setSearched(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed. Please try again.');
      setResults([]);
      setSearched(true);
    } finally {
      setLoading(false);
    }
  }

  function handleCategorySelect(category: string) {
    setActiveCategory(category);
    if (currentLocation) {
      handleSearch({ location: currentLocation, category, platform: activePlatform, hostelsOnly });
    }
  }

  function handlePlatformSelect(platform: string) {
    setActivePlatform(platform);
    if (currentLocation) {
      handleSearch({ location: currentLocation, category: activeCategory, platform, hostelsOnly });
    }
  }

  function handleHostelsToggle() {
    const next = !hostelsOnly;
    setHostelsOnly(next);
    if (currentLocation) {
      handleSearch({ location: currentLocation, category: activeCategory, platform: activePlatform, hostelsOnly: next });
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-green-50 to-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 py-5">
          <h1 className="text-2xl font-bold text-green-700">VolunteerFinder</h1>
          <p className="text-gray-500 text-sm mt-0.5">Discover volunteering opportunities near you</p>
        </div>
      </header>

      {/* Search Section */}
      <section className="bg-white border-b border-gray-100 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 py-6 flex flex-col items-center gap-4">
          <SearchBar onSearch={handleSearch} loading={loading} />
          <FilterBar
            categories={CATEGORIES}
            active={activeCategory}
            onSelect={handleCategorySelect}
          />
          <div className="flex flex-wrap items-center gap-2">
            <FilterBar
              categories={PLATFORMS}
              active={activePlatform}
              onSelect={handlePlatformSelect}
            />
            <button
              onClick={handleHostelsToggle}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                hostelsOnly
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Hostels only
            </button>
          </div>
        </div>
      </section>

      {/* Results Section */}
      <section className="max-w-6xl mx-auto px-4 py-8">
        {searched && !loading && !error && results.length > 0 && (
          <p className="text-sm text-gray-500 mb-4">
            Found {results.length} opportunities near &quot;{currentLocation}&quot;
          </p>
        )}
        <ResultsGrid
          results={results}
          loading={loading}
          error={error}
          searched={searched}
          location={currentLocation}
        />
      </section>

      {/* Footer */}
      <footer className="text-center text-xs text-gray-400 py-8">
        Results powered by Google Search via Serper.dev
      </footer>
    </main>
  );
}
