import type { OpportunityResult } from '@/types';

type Props = {
  result: OpportunityResult;
};

export default function ResultCard({ result }: Props) {
  return (
    <div className="flex flex-col justify-between bg-white border border-gray-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
      <div>
        <p className="text-xs text-green-700 font-medium mb-1">{result.displayUrl}</p>
        <a
          href={result.link}
          target="_blank"
          rel="noopener noreferrer"
          className="text-gray-900 font-semibold text-base leading-snug hover:text-green-700 line-clamp-2"
        >
          {result.title}
        </a>
        <p className="text-gray-600 text-sm mt-2 line-clamp-3">{result.snippet}</p>
      </div>
      <a
        href={result.link}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-4 inline-block text-center px-4 py-2 bg-green-50 text-green-700 rounded-lg text-sm font-medium hover:bg-green-100 transition-colors"
      >
        Visit
      </a>
    </div>
  );
}
