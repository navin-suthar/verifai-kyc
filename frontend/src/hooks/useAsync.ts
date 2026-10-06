import { useCallback, useEffect, useRef, useState } from 'react';
import { toApiError, type ApiError } from '@/lib/api/client';

export type AsyncState<T> =
  | { status: 'idle'; data: null; error: null }
  | { status: 'loading'; data: T | null; error: null }
  | { status: 'success'; data: T; error: null }
  | { status: 'error'; data: T | null; error: ApiError };

interface UseAsyncResult<T> {
  state: AsyncState<T>;
  data: T | null;
  error: ApiError | null;
  isLoading: boolean;
  reload: () => Promise<void>;
}

/**
 * Runs an async loader on mount (and whenever `deps` change), tracking
 * loading / success / error states with cancellation on unmount so a late
 * response never updates an unmounted component.
 */
export function useAsync<T>(loader: () => Promise<T>, deps: readonly unknown[] = []): UseAsyncResult<T> {
  const [state, setState] = useState<AsyncState<T>>({ status: 'idle', data: null, error: null });
  const loaderRef = useRef(loader);
  loaderRef.current = loader;
  const requestId = useRef(0);

  const run = useCallback(async () => {
    const id = ++requestId.current;
    setState((prev) => ({ status: 'loading', data: prev.data, error: null }));
    try {
      const data = await loaderRef.current();
      if (id === requestId.current) setState({ status: 'success', data, error: null });
    } catch (err) {
      if (id === requestId.current) {
        setState((prev) => ({ status: 'error', data: prev.data, error: toApiError(err) }));
      }
    }
  }, []);

  useEffect(() => {
    void run();
    return () => {
      requestId.current += 1; // invalidate in-flight request
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [run, ...deps]);

  return {
    state,
    data: state.data,
    error: state.status === 'error' ? state.error : null,
    isLoading: state.status === 'loading' || state.status === 'idle',
    reload: run,
  };
}
