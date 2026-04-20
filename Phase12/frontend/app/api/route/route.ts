/**
 * POST /api/route
 *   body: { origin: [lat, lng], destination: [lat, lng], waypoints?: [{lat,lng,name?}] }
 *   200:  RouteResult
 * GET /api/route?originLat=..&originLng=..&destLat=..&destLng=..
 */
import { NextResponse } from "next/server";
import { z } from "zod";
import { requestRoute } from "@/lib/api/route";

export const runtime = "nodejs";

const Coord = z.tuple([
  z.number().min(-90).max(90),
  z.number().min(-180).max(180),
]);
const WaypointSchema = z.object({
  lat: z.number().min(-90).max(90),
  lng: z.number().min(-180).max(180),
  name: z.string().max(80).optional(),
});
const Body = z.object({
  origin: Coord,
  destination: Coord,
  waypoints: z.array(WaypointSchema).max(5).optional(),
});

export async function POST(request: Request) {
  let parsed;
  try {
    parsed = Body.parse(await request.json());
  } catch (err) {
    return NextResponse.json(
      { error: "invalid-body", detail: String(err) },
      { status: 400 },
    );
  }
  const result = await requestRoute(parsed.origin, parsed.destination, {
    waypoints: parsed.waypoints,
  });
  return NextResponse.json(result);
}

export async function GET(request: Request) {
  const u = new URL(request.url);
  const num = (k: string) => Number(u.searchParams.get(k));
  const origin: [number, number] = [num("originLat"), num("originLng")];
  const destination: [number, number] = [num("destLat"), num("destLng")];
  if (origin.some(Number.isNaN) || destination.some(Number.isNaN)) {
    return NextResponse.json(
      { error: "missing-params", expected: ["originLat", "originLng", "destLat", "destLng"] },
      { status: 400 },
    );
  }
  const result = await requestRoute(origin, destination);
  return NextResponse.json(result);
}
