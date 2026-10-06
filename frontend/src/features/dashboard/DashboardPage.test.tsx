import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import DashboardPage from './DashboardPage';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { mockDashboard } from '@/mocks/data';

vi.mock('@/lib/api/dashboardApi', () => ({
  getDashboardSummary: vi.fn(),
}));

import { getDashboardSummary } from '@/lib/api/dashboardApi';

function renderPage() {
  return render(
    <ThemeProvider>
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe('DashboardPage', () => {
  it('renders key metrics and recent applications after loading', async () => {
    vi.mocked(getDashboardSummary).mockResolvedValueOnce(mockDashboard);
    renderPage();

    expect(screen.getByRole('heading', { name: 'Dashboard' })).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getAllByText(String(mockDashboard.total_applications)).length).toBeGreaterThan(0);
    });
    expect(screen.getByText('Total applications')).toBeInTheDocument();
    expect(screen.getByText('Rahul Sharma')).toBeInTheDocument();
    expect(screen.getByText(/Verification volume/i)).toBeInTheDocument();
  });

  it('shows an error state with retry when the API fails', async () => {
    vi.mocked(getDashboardSummary).mockRejectedValueOnce({
      type: 'network',
      message: 'Unable to reach the server.',
    });
    renderPage();

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('Unable to reach the server.');
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });
});
