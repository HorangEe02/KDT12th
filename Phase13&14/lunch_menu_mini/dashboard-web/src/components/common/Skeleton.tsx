"use client";

/**
 * Skeleton placeholders shared across pages.
 *
 * Style keeps the existing surface-1 / outline tokens so it blends with the
 * rest of the UI. All variants use Tailwind `animate-pulse`.
 */
import { cn } from "@/lib/cn";

interface BaseProps {
  className?: string;
}

export function SkeletonBlock({ className }: BaseProps) {
  return (
    <div
      className={cn(
        "animate-pulse bg-surface-2 border border-outline/10 rounded-sm",
        className,
      )}
      aria-hidden
    />
  );
}

export function SkeletonCard({ className }: BaseProps) {
  return (
    <div
      className={cn(
        "bg-surface-1 border border-outline/15 rounded-sm p-5 animate-pulse",
        className,
      )}
      aria-hidden
    >
      <div className="h-4 w-32 bg-surface-2 rounded-sm mb-3" />
      <div className="h-3 w-20 bg-surface-2 rounded-sm mb-5" />
      <div className="space-y-2">
        <div className="h-3 w-full bg-surface-2 rounded-sm" />
        <div className="h-3 w-5/6 bg-surface-2 rounded-sm" />
        <div className="h-3 w-3/4 bg-surface-2 rounded-sm" />
      </div>
    </div>
  );
}

export function SkeletonList({
  count = 5,
  className,
}: BaseProps & { count?: number }) {
  return (
    <div className={cn("space-y-2", className)} aria-hidden>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="bg-surface-1 border border-outline/15 rounded-sm p-4 animate-pulse flex items-center gap-3"
        >
          <div className="h-10 w-10 rounded-full bg-surface-2 flex-shrink-0" />
          <div className="flex-1 space-y-2">
            <div className="h-3 w-1/2 bg-surface-2 rounded-sm" />
            <div className="h-2.5 w-1/3 bg-surface-2 rounded-sm" />
          </div>
          <div className="h-6 w-12 bg-surface-2 rounded-sm" />
        </div>
      ))}
    </div>
  );
}

export function SkeletonChart({
  height = 240,
  className,
}: BaseProps & { height?: number }) {
  return (
    <div
      className={cn(
        "bg-surface-1 border border-outline/15 rounded-sm p-5 animate-pulse",
        className,
      )}
      aria-hidden
    >
      <div className="h-4 w-40 bg-surface-2 rounded-sm mb-3" />
      <div className="h-3 w-24 bg-surface-2 rounded-sm mb-4" />
      <div
        className="w-full bg-surface-2 rounded-sm"
        style={{ height }}
      />
    </div>
  );
}

export function SkeletonMap({
  height = 340,
  className,
}: BaseProps & { height?: number }) {
  return (
    <div
      className={cn(
        "relative overflow-hidden bg-surface-1 border border-outline/15 rounded-sm animate-pulse",
        className,
      )}
      style={{ height }}
      aria-hidden
    >
      <div className="absolute inset-0 bg-gradient-to-br from-surface-2 via-surface-1 to-surface-2" />
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-[11px] font-mono text-text-tertiary uppercase tracking-[0.1em]">
          Loading map…
        </div>
      </div>
    </div>
  );
}
