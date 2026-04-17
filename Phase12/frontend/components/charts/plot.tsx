"use client";

import dynamic from "next/dynamic";
import type { ComponentProps } from "react";
import type Plot from "react-plotly.js";

/**
 * react-plotly.js + plotly.js-dist-min 동적 로드 (ssr: false).
 * Plotly 번들이 크므로 반드시 client에서만 로드.
 */
const PlotNoSSR = dynamic(
  () =>
    import("react-plotly.js").then((m) => m.default) as Promise<typeof Plot>,
  { ssr: false, loading: () => <PlotSkeleton /> },
) as typeof Plot;

export function PlotSkeleton({ height = 300 }: { height?: number }) {
  return (
    <div
      className="flex w-full animate-pulse items-center justify-center rounded-2xl border border-se-outline-variant bg-se-surface-container-low text-xs text-se-on-surface-variant"
      style={{ height }}
    >
      차트 로딩 중…
    </div>
  );
}

export function Plotly(props: ComponentProps<typeof Plot>) {
  return <PlotNoSSR {...props} />;
}
