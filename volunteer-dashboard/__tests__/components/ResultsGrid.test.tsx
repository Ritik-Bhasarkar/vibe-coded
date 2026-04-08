import { render, screen } from '@testing-library/react';
import ResultsGrid from '@/components/ResultsGrid';
import type { OpportunityResult } from '@/types';

const results: OpportunityResult[] = [
  { title: 'Result 1', snippet: 'Snippet 1', link: 'https://a.com', displayUrl: 'a.com' },
  { title: 'Result 2', snippet: 'Snippet 2', link: 'https://b.com', displayUrl: 'b.com' },
];

describe('ResultsGrid', () => {
  it('shows skeleton cards when loading', () => {
    render(<ResultsGrid results={[]} loading={true} error={null} searched={false} location="" />);
    expect(screen.getAllByTestId('skeleton-card')).toHaveLength(6);
  });

  it('renders result cards when results are present', () => {
    render(<ResultsGrid results={results} loading={false} error={null} searched={true} location="NYC" />);
    expect(screen.getByText('Result 1')).toBeInTheDocument();
    expect(screen.getByText('Result 2')).toBeInTheDocument();
  });

  it('shows empty state when searched with no results', () => {
    render(<ResultsGrid results={[]} loading={false} error={null} searched={true} location="Nowhere" />);
    expect(screen.getByText(/no results/i)).toBeInTheDocument();
    expect(screen.getByText(/Nowhere/i)).toBeInTheDocument();
  });

  it('shows error message when error is present', () => {
    render(<ResultsGrid results={[]} loading={false} error="Search failed" searched={true} location="NYC" />);
    expect(screen.getByText(/search failed/i)).toBeInTheDocument();
  });

  it('shows initial prompt when not yet searched', () => {
    render(<ResultsGrid results={[]} loading={false} error={null} searched={false} location="" />);
    expect(screen.getByText(/enter a location/i)).toBeInTheDocument();
  });
});
