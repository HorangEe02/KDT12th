"use client";

import type { ReactNode } from "react";
import type { UseQueryResult } from "@tanstack/react-query";
import ErrorBanner from "./ErrorBanner";
import { isNetworkError, isWarmingUp, formatError } from "@/lib/errors";

interface QueryBoundaryProps<T> {
  query: UseQueryResult<T>;
  skeleton: ReactNode;
  children: (data: T) => ReactNode;
  /** Suppress error UI and use fallback instead (typical when query has
   * a built-in mock fallback — errors should be silent but we still want to
   * show a skeleton during initial load). */
  silentError?: boolean;
  errorTitle?: string;
  className?: string;
}

/**
 * Thin wrapper to unify loading/error/success rendering around a TanStack
 * Query result. Handles the three UX states:
 *
 *  - initial pending (no data yet) → skeleton
 *  - error without fallback → ErrorBanner (warming variant for NLP 503)
 *  - success → children(data)
 *
 * Pages that already use mock fallback in the query function can pass
 * `silentError` so errors only show after the first successful load fails.
 */
export default function QueryBoundary<T>({
  query,
  skeleton,
  children,
  silentError = false,
  errorTitle,
  className,
}: QueryBoundaryProps<T>) {
  const { data, isPending, isError, error, refetch } = query;

  if (isPending && data == null) {
    return <div className={className}>{skeleton}</div>;
  }

  if (isError && !silentError && data == null) {
    const warming = isWarmingUp(error);
    const offline = isNetworkError(error);
    return (
      <div className={className}>
        <ErrorBanner
          variant={warming ? "warming" : offline ? "offline" : "error"}
          title={errorTitle}
          message={warming ? undefined : formatError(error)}
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  // data is defined past the pending guard
  return <div className={className}>{children(data as T)}</div>;
}
