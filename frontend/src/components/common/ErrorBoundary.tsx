import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';
import Button from '@/components/ui/Button';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

/**
 * Error boundaries must be class components (React has no hook equivalent).
 * Technical details are logged, never rendered to the user.
 */
export default class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    if (import.meta.env.DEV) console.error('Unhandled UI error', error, info.componentStack);
  }

  handleReset = (): void => {
    this.setState({ hasError: false });
    window.location.assign('/');
  };

  render(): ReactNode {
    if (!this.state.hasError) return this.props.children;
    return (
      <div className="flex min-h-screen items-center justify-center p-6">
        <div role="alert" className="max-w-md rounded-xl border bg-surface p-8 text-center shadow-card">
          <AlertTriangle className="mx-auto mb-3 h-8 w-8 text-danger" aria-hidden="true" />
          <h1 className="text-lg font-semibold">Something went wrong</h1>
          <p className="mt-1 text-sm text-fg-muted">An unexpected error occurred in the interface. Your data is safe.</p>
          <Button className="mt-5" onClick={this.handleReset}>
            Back to dashboard
          </Button>
        </div>
      </div>
    );
  }
}
