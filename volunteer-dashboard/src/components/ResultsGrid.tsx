import type { OpportunityResult } from '@/types';
import ResultCard from './ResultCard';
import SkeletonCard from './SkeletonCard';

type Props = {
  results: OpportunityResult[];
  loading: boolean;
  error: string | null;
  searched: boolean;
  location: string;
};

export default function ResultsGrid({ results, loading, error, searched, location }: Props) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 w-full">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} data-testid="skeleton-card">
            <SkeletonCard />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-16 text-gray-500">
        <p className="text-red-500 font-medium">{error}</p>
        <p className="text-sm mt-1">Please try again.</p>
      </div>
    );
  }

  if (!searched) {
    return (
      <div className="text-center py-16 text-gray-400">
        <p className="text-lg">Enter a location above to find volunteer opportunities near you.</p>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="text-center py-16 text-gray-500">
        <p className="text-lg font-medium">No results found for <span className="text-gray-700">{location}</span>.</p>
        <p className="text-sm mt-1">Try a different location or category.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 w-full">
      {results.map((result, i) => (
        <ResultCard key={i} result={result} />
      ))}
    </div>
  );
}
