import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { ROUTES } from '@/app/routes';

/** Route guard: renders children only for authenticated sessions. */
export default function RequireAuth() {
  const { state } = useAuth();
  const location = useLocation();

  if (state.status === 'loading') {
    return (
      <div className="flex min-h-screen items-center justify-center text-fg-muted" aria-busy="true">
        <Loader2 className="h-6 w-6 animate-spin" aria-label="Loading session" />
      </div>
    );
  }

  if (state.status === 'unauthenticated') {
    return <Navigate to={ROUTES.login} replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}
