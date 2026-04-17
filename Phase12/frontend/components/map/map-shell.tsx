"use client";

import dynamic from "next/dynamic";
import type { ComponentProps } from "react";
import type { LeafletMap as LeafletMapComponent } from "./leaflet-map";

const LeafletMap = dynamic(
  () => import("./leaflet-map").then((m) => m.LeafletMap),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-[560px] animate-pulse items-center justify-center rounded-2xl border border-se-outline-variant bg-se-surface-container-low text-sm text-se-on-surface-variant">
        🗺️ 지도 로딩 중…
      </div>
    ),
  },
) as typeof LeafletMapComponent;

export function MapShell(props: ComponentProps<typeof LeafletMapComponent>) {
  return <LeafletMap {...props} />;
}
