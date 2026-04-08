import { render, screen, fireEvent } from '@testing-library/react';
import FilterBar from '@/components/FilterBar';

describe('FilterBar', () => {
  const categories = ['All', 'Community', 'Environment', 'Animals'];

  it('renders all category pills', () => {
    render(<FilterBar categories={categories} active="All" onSelect={jest.fn()} />);
    categories.forEach((cat) =>
      expect(screen.getByRole('button', { name: cat })).toBeInTheDocument()
    );
  });

  it('highlights the active category', () => {
    render(<FilterBar categories={categories} active="Environment" onSelect={jest.fn()} />);
    const activeBtn = screen.getByRole('button', { name: 'Environment' });
    expect(activeBtn).toHaveClass('bg-green-600');
  });

  it('calls onSelect when a pill is clicked', () => {
    const onSelect = jest.fn();
    render(<FilterBar categories={categories} active="All" onSelect={onSelect} />);
    fireEvent.click(screen.getByRole('button', { name: 'Animals' }));
    expect(onSelect).toHaveBeenCalledWith('Animals');
  });
});
