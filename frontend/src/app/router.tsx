import { lazy, Suspense } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import AppShell from '@/components/layout/AppShell';
import RequireAuth from '@/components/common/RequireAuth';
import { SkeletonText } from '@/components/ui';
import { ROUTES } from './routes';

const DashboardPage = lazy(() => import('@/features/dashboard'));
const LoginPage = lazy(() => import('@/features/auth'));
const ApplicationsPage = lazy(() => import('@/features/applications'));
const UploadPage = lazy(() => import('@/features/upload'));
const AnalysisPage = lazy(() => import('@/features/analysis'));
const ResultPage = lazy(() => import('@/features/result'));
const ReviewPage = lazy(() => import('@/features/review'));
const AssistantPage = lazy(() => import('@/features/assistant'));
const AuditPage = lazy(() => import('@/features/audit'));
const AnalyticsPage = lazy(() => import('@/features/analytics'));

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
          { path: ROUTES.applications, element: withSuspense(<ApplicationsPage />) },
          { path: '/applications/:id', element: withSuspense(<AnalysisPage />) },
          { path: '/applications/:id/result', element: withSuspense(<ResultPage />) },
          { path: ROUTES.upload, element: withSuspense(<UploadPage />) },
          { path: ROUTES.review, element: withSuspense(<ReviewPage />) },
          { path: ROUTES.assistant, element: withSuspense(<AssistantPage />) },
          { path: ROUTES.audit, element: withSuspense(<AuditPage />) },
          { path: ROUTES.analytics, element: withSuspense(<AnalyticsPage />) },
        ],
      },
    ],
  },
  { path: '*', element: <Navigate to={ROUTES.dashboard} replace /> },
]);
