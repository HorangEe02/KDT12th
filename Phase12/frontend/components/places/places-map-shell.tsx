"use client";

import dynamic from "next/dynamic";
import type { POI, Stadium } from "@/lib/types";

const PlacesMiniMap = dynamic(
  () => import("./places-mini-map").then((m) => m.PlacesMiniMap),
  {
    ssr: false,
    loading: () => (
      <div
        className="flex items-center justify-center rounded-2xl border border-se-outline-variant bg-se-surface-container-low"
        style={{ height: 380 }}
      >
        <div className="flex flex-col items-center gap-2 text-se-on-surface-variant">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-se-primary border-t-transparent" />
          <span className="font-display text-xs font-bold uppercase tracking-wider">
            지도 로딩 중...
          </span>
        </div>
      </div>
    ),
  },
);

interface PlacesMapShellProps {
  stadium: Stadium;
  pois: POI[];
  category: "food" | "stay" | "tour";
  selectedId?: string;
  height?: number;
}

export function PlacesMapShell(props: PlacesMapShellProps) {
  return <PlacesMiniMap {...props} />;
}
