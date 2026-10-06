import { lazy, Suspense } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import AppShell from '@/components/layout/AppShell';
import RequireAuth from '@/components/common/RequireAuth';
import ComingSoon from '@/components/common/ComingSoon';
import { SkeletonText } from '@/components/ui';
import { ROUTES } from './routes';

const DashboardPage = lazy(() => import('@/features/dashboard'));
const LoginPage = lazy(() => import('@/features/auth'));

function PageFallback() {
  return (
    <div className="p-2">
      <SkeletonText lines={6} />
    </div>
  );
}

function withSuspense(element: React.ReactNode) {
  return <Suspense fallback={<PageFallback />}>{element}</Suspense>;
}

export const router = createBrowserRouter([
  { path: ROUTES.login, element: withSuspense(<LoginPage />) },
  {
    element: <RequireAuth />,
    children: [
      {
        element: <AppShell />,
        children: [
          { path: ROUTES.dashboard, element: withSuspense(<DashboardPage />) },
          {
            path: ROUTES.applications,
            element: <ComingSoon title="Applications" description="All processed KYC applications." phase="Phase 2" />,
          },
          {
            path: '/applications/:id',
            element: <ComingSoon title="Document Analysis" description="Extracted fields, validation and AI explanation." phase="Phase 3" />,
          },
          {
            path: '/applications/:id/result',
            element: <ComingSoon title="Verification Result" description="Final decision with evidence." phase="Phase 4" />,
          },
          {
            path: ROUTES.upload,
            element: <ComingSoon title="Upload Document" description="Submit a synthetic KYC document for analysis." phase="Phase 3" />,
          },
          {
            path: ROUTES.review,
            element: <ComingSoon title="Human Review" description="Applications waiting for a reviewer decision." phase="Phase 8" />,
          },
          {
            path: ROUTES.assistant,
            element: <ComingSoon title="Knowledge Assistant" description="Ask questions about KYC policy with cited sources." phase="Phase 7" />,
          },
          {
            path: ROUTES.audit,
            element: <ComingSoon title="Audit Logs" description="Immutable trail of every system and reviewer action." phase="Phase 8" />,
          },
          {
            path: ROUTES.analytics,
            element: <ComingSoon title="Analytics" description="Pipeline performance and AI evaluation metrics." phase="Phase 8" />,
          },
        ],
      },
    ],
  },
  { path: '*', element: <Navigate to={ROUTES.dashboard} replace /> },
]);
