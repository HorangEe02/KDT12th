/**
 * Filters ↔ URLSearchParams 직렬화.
 * MVP 공유: Firestore 없이 URL 쿼리로 전체 상태 전달.
 */
import type { PartyType, TransportType } from "@/lib/types";

interface ShareableFilters {
  team?: string;
  start?: string;
  end?: string;
  budget?: number;
  party?: PartyType;
  transport?: TransportType;
  device?: "web" | "mobile";
}

export function serializeFilters(
  f: Partial<ShareableFilters>,
): URLSearchParams {
  const p = new URLSearchParams();
  if (f.team) p.set("team", f.team);
  if (f.start) p.set("start", f.start);
  if (f.end) p.set("end", f.end);
  if (typeof f.budget === "number") p.set("budget", String(f.budget));
  if (f.party) p.set("party", f.party);
  if (f.transport) p.set("transport", f.transport);
  if (f.device) p.set("device", f.device);
  return p;
}

export function parseShareFilters(
  params: URLSearchParams,
): ShareableFilters {
  const budget = Number(params.get("budget"));
  const party = params.get("party");
  const transport = params.get("transport");
  const device = params.get("device");
  return {
    team: params.get("team") ?? undefined,
    start: params.get("start") ?? undefined,
    end: params.get("end") ?? undefined,
    budget: Number.isFinite(budget) && budget > 0 ? budget : undefined,
    party:
      party === "solo" || party === "couple" || party === "family" || party === "friends"
        ? (party as PartyType)
        : undefined,
    transport:
      transport === "train" || transport === "car" || transport === "bus"
        ? (transport as TransportType)
        : undefined,
    device: device === "mobile" ? "mobile" : device === "web" ? "web" : undefined,
  };
}

export function buildShareUrl(
  origin: string,
  pathname: string,
  filters: Partial<ShareableFilters>,
): string {
  const qs = serializeFilters(filters).toString();
  return `${origin}${pathname}${qs ? `?${qs}` : ""}`;
}
