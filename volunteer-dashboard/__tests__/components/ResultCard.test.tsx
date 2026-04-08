import { render, screen } from '@testing-library/react';
import ResultCard from '@/components/ResultCard';
import type { OpportunityResult } from '@/types';

const result: OpportunityResult = {
  title: 'Food Bank Volunteer',
  snippet: 'Help sort donations every Saturday morning.',
  link: 'https://foodbank.org/volunteer',
  displayUrl: 'foodbank.org',
};

describe('ResultCard', () => {
  it('renders title as a link', () => {
    render(<ResultCard result={result} />);
    const link = screen.getByRole('link', { name: result.title });
    expect(link).toHaveAttribute('href', result.link);
    expect(link).toHaveAttribute('target', '_blank');
  });

  it('renders snippet text', () => {
    render(<ResultCard result={result} />);
    expect(screen.getByText(result.snippet)).toBeInTheDocument();
  });

  it('renders displayUrl as source', () => {
    render(<ResultCard result={result} />);
    expect(screen.getByText(result.displayUrl)).toBeInTheDocument();
  });

  it('renders Visit button linking to opportunity', () => {
    render(<ResultCard result={result} />);
    const visitBtn = screen.getByRole('link', { name: /visit/i });
    expect(visitBtn).toHaveAttribute('href', result.link);
    expect(visitBtn).toHaveAttribute('target', '_blank');
  });
});
