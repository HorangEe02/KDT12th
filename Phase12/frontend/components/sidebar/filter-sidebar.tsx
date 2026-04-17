"use client";

import { useEffect } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { TEAMS, getTeamPalette } from "@/lib/team-colors";
import { useFilters, SEASON_START, SEASON_END } from "@/lib/store/filters";
import { cn } from "@/lib/utils";
import type { PartyType, TransportType } from "@/lib/types";
import { SharePlanButton } from "@/components/badges/share-plan-button";

const PARTY: Array<{ value: PartyType; label: string; icon: string }> = [
  { value: "solo", label: "혼자", icon: "person" },
  { value: "couple", label: "커플", icon: "favorite" },
  { value: "family", label: "가족", icon: "family_restroom" },
  { value: "friends", label: "친구", icon: "groups" },
];

const TRANSPORT: Array<{ value: TransportType; label: string; icon: string }> =
  [
    { value: "train", label: "KTX/SRT", icon: "train" },
    { value: "car", label: "자차", icon: "directions_car" },
    { value: "bus", label: "고속버스", icon: "directions_bus" },
  ];

export function FilterSidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const f = useFilters();

  // 공유 URL 의 filter 쿼리를 store 로 하이드레이션 (최초 로드 + 외부 링크)
  useEffect(() => {
    const urlTeam = searchParams.get("team");
    if (urlTeam && urlTeam !== f.team) f.setTeam(urlTeam);

    const s = searchParams.get("start");
    const e = searchParams.get("end");
    if (s && e && (s !== f.dateStart || e !== f.dateEnd)) {
      f.setDateRange(s, e);
    }

    const budget = Number(searchParams.get("budget"));
    if (Number.isFinite(budget) && budget > 0 && budget !== f.budget) {
      f.setBudget(budget);
    }

    const party = searchParams.get("party");
    if (
      (party === "solo" || party === "couple" || party === "family" || party === "friends") &&
      party !== f.party
    ) {
      f.setParty(party);
    }

    const transport = searchParams.get("transport");
    if (
      (transport === "train" || transport === "car" || transport === "bus") &&
      transport !== f.transport
    ) {
      f.setTransport(transport);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  function pushTeamToUrl(team: string) {
    const p = new URLSearchParams(searchParams.toString());
    p.set("team", team);
    router.replace(`${pathname}?${p.toString()}`, { scroll: false });
  }

  function onTeamChange(team: string) {
    f.setTeam(team);
    pushTeamToUrl(team);
  }

  return (
    <aside className="sticky top-20 hidden h-[calc(100vh-5rem)] w-[260px] shrink-0 overflow-y-auto border-r border-se-outline-variant bg-se-surface-container-low px-5 py-6 md:block">
      <h2 className="mb-4 font-display text-sm font-extrabold uppercase tracking-[0.14em] text-se-primary">
        🎽 원정 설정
      </h2>

      {/* 응원팀 */}
      <label className="mb-1 block font-display text-[0.72rem] font-bold uppercase tracking-[0.12em] text-se-on-surface-variant">
        응원팀
      </label>
      <select
        value={f.team}
        onChange={(e) => onTeamChange(e.target.value)}
        className="mb-4 w-full rounded-xl border border-se-outline-variant bg-white px-3 py-2 text-sm font-semibold text-se-primary"
      >
        {TEAMS.map((code) => {
          const p = getTeamPalette(code);
          return (
            <option key={code} value={code}>
              {code} · {p.nameKo}
            </option>
          );
        })}
      </select>

      {/* 원정 기간 */}
      <div className="mb-4 space-y-1.5">
        <label className="block font-display text-[0.72rem] font-bold uppercase tracking-[0.12em] text-se-on-surface-variant">
          원정 기간
        </label>
        <input
          type="date"
          value={f.dateStart}
          min={SEASON_START}
          max={SEASON_END}
          onChange={(e) => f.setDateRange(e.target.value, f.dateEnd)}
          className="w-full rounded-xl border border-se-outline-variant bg-white px-3 py-2 text-sm"
        />
        <input
          type="date"
          value={f.dateEnd}
          min={f.dateStart}
          max={SEASON_END}
          onChange={(e) => f.setDateRange(f.dateStart, e.target.value)}
          className="w-full rounded-xl border border-se-outline-variant bg-white px-3 py-2 text-sm"
        />
      </div>

      {/* 예산 */}
      <div className="mb-4">
        <label className="flex items-center justify-between font-display text-[0.72rem] font-bold uppercase tracking-[0.12em] text-se-on-surface-variant">
          <span>예산 (만원)</span>
          <span className="font-display text-sm font-extrabold text-se-primary">
            {f.budget}
          </span>
        </label>
        <input
          type="range"
          min={10}
          max={100}
          step={5}
          value={f.budget}
          onChange={(e) => f.setBudget(Number(e.target.value))}
          className="mt-2 w-full accent-se-primary"
        />
      </div>

      {/* 인원 */}
      <div className="mb-4">
        <span className="mb-1.5 block font-display text-[0.72rem] font-bold uppercase tracking-[0.12em] text-se-on-surface-variant">
          인원 구성
        </span>
        <div className="grid grid-cols-2 gap-1.5">
          {PARTY.map((o) => {
            const active = f.party === o.value;
            return (
              <button
                key={o.value}
                onClick={() => f.setParty(o.value)}
                className={cn(
                  "flex items-center justify-center gap-1 rounded-xl border px-2 py-1.5 text-xs font-bold transition-colors",
                  active
                    ? "border-se-primary bg-se-primary text-white"
                    : "border-se-outline-variant bg-white text-se-on-surface",
                )}
              >
                <span className="material-symbols-outlined text-[16px]">
                  {o.icon}
                </span>
                {o.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* 이동수단 */}
      <div className="mb-4">
        <span className="mb-1.5 block font-display text-[0.72rem] font-bold uppercase tracking-[0.12em] text-se-on-surface-variant">
          이동수단
        </span>
        <div className="grid grid-cols-3 gap-1.5">
          {TRANSPORT.map((o) => {
            const active = f.transport === o.value;
            return (
              <button
                key={o.value}
                onClick={() => f.setTransport(o.value)}
                title={o.label}
                className={cn(
                  "flex flex-col items-center rounded-xl border px-1 py-1.5 text-[0.65rem] font-bold transition-colors",
                  active
                    ? "border-se-primary bg-se-primary text-white"
                    : "border-se-outline-variant bg-white text-se-on-surface",
                )}
              >
                <span className="material-symbols-outlined text-[18px]">
                  {o.icon}
                </span>
                {o.label}
              </button>
            );
          })}
        </div>
      </div>

      <button
        onClick={() => f.triggerGenerate()}
        className="mb-3 w-full rounded-xl bg-[var(--se-signature-gradient)] bg-se-primary px-4 py-2.5 font-display text-sm font-extrabold text-white shadow-[0_6px_16px_rgba(0,25,60,0.2)] transition-transform hover:-translate-y-0.5"
      >
        🎯 코스 생성
      </button>

      <label className="flex cursor-pointer items-center gap-2 rounded-xl border border-se-outline-variant bg-white px-3 py-2 text-xs font-semibold text-se-on-surface">
        <input
          type="checkbox"
          checked={f.demoMode}
          onChange={(e) => f.setDemoMode(e.target.checked)}
          className="accent-se-primary"
        />
        🎬 시연 모드
      </label>
      {f.demoMode && (
        <p className="mt-1.5 text-[0.65rem] text-se-on-surface-variant">
          LLM 호출 없이 mock 응답 반환 (탭 4)
        </p>
      )}

      <hr className="my-4 border-se-outline-variant" />

      <SharePlanButton variant="sidebar" pathname="/" />
    </aside>
  );
}
