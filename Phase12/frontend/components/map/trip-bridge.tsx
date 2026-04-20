"use client";

import { useTripStore } from "@/lib/store/trip";
import { TripConfirmationSheet } from "./trip-confirmation-sheet";
import type { POI, Stadium, Game, RouteResult } from "@/lib/types";

/**
 * Trip 데이터 brige — useTripStore (client) 의 waypoints 를
 * Server Component 인 page.tsx 에서는 직접 못 읽으니
 * client wrapper 로 hook 호출 후 TripConfirmationSheet 에 주입.
 */
interface TripBridgeProps {
  origin: { label: string; coords: [number, number] };
  stadium: Stadium;
  selectedGame: Game;
  route: RouteResult;
  pois: { food: POI[]; stay: POI[]; tour: POI[] };
}

export function TripBridge(props: TripBridgeProps) {
  const waypoints = useTripStore((s) => s.waypoints);
  return (
    <TripConfirmationSheet
      origin={props.origin}
      stadium={props.stadium}
      selectedGame={props.selectedGame}
      route={props.route}
      waypoints={waypoints.map((w) => ({
        lat: w.lat,
        lng: w.lng,
        name: w.name,
      }))}
    />
  );
}
