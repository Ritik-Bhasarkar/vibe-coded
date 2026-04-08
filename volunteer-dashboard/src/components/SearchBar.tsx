'use client';

import { useState, KeyboardEvent } from 'react';
import type { SearchParams } from '@/types';

type Props = {
  onSearch: (params: SearchParams) => void;
  loading: boolean;
};

const CATEGORIES = [
  { label: 'All Categories', value: '' },
  { label: 'Community', value: 'community' },
  { label: 'Environment', value: 'environment' },
  { label: 'Animals', value: 'animals' },
  { label: 'Education', value: 'education' },
  { label: 'Healthcare', value: 'healthcare' },
];

export default function SearchBar({ onSearch, loading }: Props) {
  const [location, setLocation] = useState('');
  const [category, setCategory] = useState('');
  const [error, setError] = useState('');

  function handleSearch() {
    if (!location.trim()) {
      setError('Please enter a location');
      return;
    }
    setError('');
    onSearch({ location: location.trim(), category });
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') handleSearch();
  }

  return (
    <div className="flex flex-col gap-2 w-full max-w-2xl">
      <div className="flex gap-2">
        <input
          type="text"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Enter city, zip, or address"
          disabled={loading}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 disabled:bg-gray-100"
        />
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          disabled={loading}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 disabled:bg-gray-100"
        >
          {CATEGORIES.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </select>
        <button
          onClick={handleSearch}
          disabled={loading}
          className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>
      {error && <p className="text-red-500 text-sm">{error}</p>}
    </div>
  );
}
