import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SearchBar from '@/components/SearchBar';

describe('SearchBar', () => {
  it('renders location input and search button', () => {
    render(<SearchBar onSearch={jest.fn()} loading={false} />);
    expect(screen.getByPlaceholderText(/city/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /search/i })).toBeInTheDocument();
  });

  it('calls onSearch with location on button click', async () => {
    const onSearch = jest.fn();
    render(<SearchBar onSearch={onSearch} loading={false} />);
    await userEvent.type(screen.getByPlaceholderText(/city/i), 'New York');
    fireEvent.click(screen.getByRole('button', { name: /search/i }));
    expect(onSearch).toHaveBeenCalledWith({ location: 'New York', category: '' });
  });

  it('calls onSearch on Enter key press', async () => {
    const onSearch = jest.fn();
    render(<SearchBar onSearch={onSearch} loading={false} />);
    const input = screen.getByPlaceholderText(/city/i);
    await userEvent.type(input, 'Austin{Enter}');
    expect(onSearch).toHaveBeenCalledWith({ location: 'Austin', category: '' });
  });

  it('disables button and input when loading', () => {
    render(<SearchBar onSearch={jest.fn()} loading={true} />);
    expect(screen.getByRole('button', { name: /search/i })).toBeDisabled();
    expect(screen.getByPlaceholderText(/city/i)).toBeDisabled();
  });

  it('does not call onSearch when location is empty', async () => {
    const onSearch = jest.fn();
    render(<SearchBar onSearch={onSearch} loading={false} />);
    fireEvent.click(screen.getByRole('button', { name: /search/i }));
    expect(onSearch).not.toHaveBeenCalled();
  });
});
