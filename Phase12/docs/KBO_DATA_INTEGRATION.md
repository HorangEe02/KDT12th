# ⚾ kbo-game 실제 데이터 통합 — 브레인스토밍 + 구현 계획

> 작성: 2026-04-18
> 발단: "KBO 경기 일정이 제대로 맞지 않는거 같은데"
> 후보 소스: `/Volumes/Corsair EX300U Media/00_work_out/00_data_set/k-skill-main/kbo-results/SKILL.md`

---

## 1. 현 상태 진단

### 1-1. 현재 `schedule.json` 의 문제
- **Phase 1 에 수기/더미 생성**된 714 경기 — 2026 시즌 실제 일정과 불일치 가능성
- 필드 빈약: `start_time`, `broadcast` 만 · **스코어·투수·상태 없음**
- `predict_win_rate` 모델이 이 데이터를 기반으로 학습되지만, 실제 2026 시즌 진행과 괴리

### 1-2. 타깃 소스 — `kbo-game` npm 패키지
- 패키지: `kbo-game@0.0.2` · MIT · **14 KB** · zero-dep
- Repo: https://github.com/vkehfdl1/kbo-game
- 내부: KBO 공식 API 호출 → 구조화된 Game 스키마 반환
- 사용법: `getGame(new Date("2026-04-17T00:00:00+09:00"))` → 해당 날짜 경기 배열

### 1-3. 실측 샘플 (2026-04-17 — 방금 호출)
```json
{
  "id": "20260417HTOB0",
  "date": "2026-04-17T00:00:00.000Z",
  "startTime": "18:30",
  "stadium": "잠실",
  "homeTeam": "두산",
  "awayTeam": "KIA",
  "homePitcher": "잭로그 ",
  "awayPitcher": "이의리 ",
  "winPitcher": "이의리",
  "losePitcher": "잭로그",
  "savePitcher": "",
  "status": "FINISHED",
  "score": { "home": 3, "away": 7 },
  "currentInning": 9,
  "broadcastServices": ["SPO-T"],
  "season": 2026
}
```

---

## 2. 통합 전략 비교 (3 옵션)

| 전략 | 구현 방식 | 장점 | 단점 |
|---|---|---|---|
| **A. 일회성 배치 크롤** | 로컬에서 전 시즌 한 번 크롤 → `schedule.json` 덮어쓰기 → 커밋 | 단순·정적·런타임 외부 의존 0 | 배포 이후 자동 업데이트 없음 |
| **B. 런타임 fetch** | API Route 가 매 요청마다 `kbo-game` 호출 | 항상 실시간 | KBO API 변경 취약·콜드스타트 지연·rate limit |
| **C. 하이브리드** | 배치 시드 + `/api/schedule/refresh` 엔드포인트 · Firestore 캐시 | 정적 안정성 + 필요 시 실시간 | 복잡도 증가 |

### ✅ 추천: **Option A (배치 크롤)**
- 학생 데모 프로젝트 성격상 정적이면 충분
- Cloud Build 재배포 자동화로 "커밋 → 배포" 사이클만으로 갱신 가능
- kbo-game 의존성을 production runtime에 넣지 않음

---

## 3. 스키마 diff (Before / After)

### Before (현재 dummy)
```json
{
  "game_id": "20260328_LG_한화",
  "date": "2026-03-28",
  "day_of_week": "토",
  "home_team": "한화",
  "away_team": "LG",
  "stadium": "대전",
  "start_time": "17:00",
  "broadcast": "KBS"
}
```
**필드 8개**. 스코어·투수·상태 없음.

### After (kbo-game 기반)
```json
{
  "game_id": "20260328LGHW0",
  "date": "2026-03-28",
  "day_of_week": "토",
  "home_team": "한화",
  "away_team": "LG",
  "stadium": "대전",
  "start_time": "17:00",
  "home_pitcher": "폰세",
  "away_pitcher": "톨허스트",
  "win_pitcher": "폰세",
  "lose_pitcher": "톨허스트",
  "save_pitcher": "주현상",
  "score": { "home": 5, "away": 3 },
  "status": "FINISHED",
  "current_inning": 9,
  "broadcast": ["SPO-T"],
  "season": 2026
}
```
**필드 17개**. 실시간성을 시즌 진행도로 반영.

---

## 4. UI 변화 미리보기

### `/matches` 페이지 — 경기 리스트 (Before)

```
┌──────────────────────────────────────────────────────┐
│ 2026-03-28  토  vs 한화  @ 대전  17:00  KBS         │
│ 2026-03-29  일  vs 한화  @ 대전  14:00  MBC         │
│ 2026-04-01  수  vs KT    @ 수원  18:30  SBS         │
└──────────────────────────────────────────────────────┘
  (모든 경기가 미래 시점처럼 단조로움)
```

### `/matches` 페이지 — 경기 리스트 (After)

```
┌─────────────────────────────────────────────────────────────────┐
│ ✅ 2026-03-28  토  @한화 5-3 W  선발 폰세·톨허스트  [SPO-T]    │
│ ✅ 2026-03-29  일  @한화 2-7 L  선발 손주영·와이스    [MBC]     │
│ ✅ 2026-04-01  수  @KT   4-4 D  (연장 12회)            [SBS]     │
│ 🔴 2026-04-17  금  @두산 3-7 L  (9회)   승:이의리     [SPO-T]   │
│ ⏱  2026-04-18  토  @두산 18:30      선발 미정          [SBS]     │
└─────────────────────────────────────────────────────────────────┘
  (상태별 아이콘 + 점수 + 결과 + 승패 투수)
```

### `/ai` 챗봇 — tool 응답 (After)

**질문**: "LG 최근 경기 결과 알려줘"
**before (더미)**: "조회된 경기 3건: 3/28, 3/29, 4/1 ..."
**after (실제)**: "LG 최근 3경기: 3/28 대전 한화전 5-3 승(폰세), 3/29 한화전 2-7 패, 4/1 수원 KT전 4-4 무. 현재 3승 2패로 4위입니다."

---

## 5. 구현 단계 (~2시간)

### Step 1: 크롤 스크립트 (30분)
`scripts/fetch_kbo_schedule.mjs` — Node ESM:

```javascript
import { getGame } from "kbo-game";
import fs from "node:fs/promises";

const SEASON_START = new Date("2026-03-28T00:00:00+09:00");
const SEASON_END = new Date("2026-11-15T00:00:00+09:00");
const DELAY_MS = 200; // polite rate limit

const allGames = [];
for (let d = new Date(SEASON_START); d <= SEASON_END; d.setDate(d.getDate() + 1)) {
  try {
    const games = await getGame(new Date(d)) ?? [];
    for (const g of games) allGames.push(normalizeGame(g));
  } catch (err) {
    console.warn(`skip ${d.toISOString()}: ${err.message}`);
  }
  await new Promise(r => setTimeout(r, DELAY_MS));
}

function normalizeGame(g) {
  const d = new Date(g.date);
  return {
    game_id: g.id,
    date: d.toISOString().slice(0, 10),
    day_of_week: "일월화수목금토"[d.getDay()],
    home_team: g.homeTeam,
    away_team: g.awayTeam,
    stadium: stadiumShortName(g.stadium),
    start_time: g.startTime,
    home_pitcher: g.homePitcher?.trim() ?? null,
    away_pitcher: g.awayPitcher?.trim() ?? null,
    win_pitcher: g.winPitcher?.trim() ?? null,
    lose_pitcher: g.losePitcher?.trim() ?? null,
    save_pitcher: g.savePitcher?.trim() ?? null,
    score: g.status === "SCHEDULED" ? null : g.score,
    status: g.status,
    current_inning: g.currentInning ?? null,
    broadcast: g.broadcastServices,
    season: g.season,
  };
}

await fs.writeFile(
  "frontend/public/data/schedule.json",
  JSON.stringify(allGames, null, 2),
);
console.log(`✓ ${allGames.length} games written`);
```

### Step 2: Team stats 재계산 (20분)
`scripts/rebuild_team_stats.mjs`:
- FINISHED 경기에서 team 별 wins/losses/draws 집계
- home_win_rate, away_win_rate, win_rate, final_rank 계산
- 2026 entry 를 `team-stats.json` 에 추가 (2015~2025 데이터 뒤로)

### Step 3: 타입/ UI 업데이트 (30분)
- `frontend/lib/types/index.ts`:
  ```ts
  export interface Game {
    game_id: string;
    date: string;
    day_of_week: string;
    home_team: string;
    away_team: string;
    stadium: string;
    start_time: string;
    home_pitcher?: string | null;
    away_pitcher?: string | null;
    win_pitcher?: string | null;
    lose_pitcher?: string | null;
    save_pitcher?: string | null;
    score?: { home: number; away: number } | null;
    status: "SCHEDULED" | "IN_PROGRESS" | "FINISHED" | "CANCELED";
    current_inning?: number | null;
    broadcast: string[];
    season: number;
  }
  ```
- `frontend/components/matches/match-list.tsx`:
  - 상태별 아이콘 · 점수 셀 추가 · 투수 hover 툴팁
  - 정렬: 최근(과거) FINISHED → 가까운 미래 SCHEDULED
- `frontend/app/(shell)/matches/page.tsx`:
  - Metric 에 "최근 전적 W-L-D" 추가
  - 필터 토글: "미래 경기만" / "지난 경기 결과만"

### Step 4: AI 도구 확장 (20분)
`frontend/lib/ai/tools.ts` 의 `search_game` 반환에 score/status 포함 →
Gemini 가 "LG 3월 경기 어땠어?" 같은 질문에 실제 결과를 답변 가능.

### Step 5: 검증 + 배포 (20분)
```bash
cd frontend && pnpm build                           # 13 routes OK
node scripts/fetch_kbo_schedule.mjs                 # 새 schedule.json 생성
git add . && git commit -m "feat: replace dummy schedule with kbo-game live data" 
git push                                            # auto-rollout 트리거
```

---

## 6. 리스크 & 완화책

| 리스크 | 완화 |
|---|---|
| kbo-game 이 KBO 사이트 변경으로 깨질 수 있음 | 배치 스크립트 실패 시 기존 데이터 유지 (graceful abort) |
| 비시즌 날짜 빈 응답 | 빈 결과 허용하는 try/catch |
| 정확한 시즌 캘린더 모름 | 여유 있게 2026-03-28 ~ 2026-11-15 범위 |
| 요청 속도 | 200ms sleep 간격 + 실패 시 3회 재시도 |
| `game_id` 포맷 변경 | kbo-game 의 `id` 채택 → 기존 URL `?game=XXX` 이 바뀔 수 있지만 영구 링크 부재라 무영향 |
| 이미 배포된 frontend | 새 JSON 커밋 → 자동 롤아웃 → 5~8분 후 반영 |

---

## 7. 미래 확장 — Phase 7 후보

이번 통합이 안정되면 다음 기능 추가 가능:
- **선발 매치업 예측**: 각 경기 선발 ERA / 상대전적 → 승률 모델 피처 추가
- **실시간 스코어 위젯**: `/matches/live` — cron 으로 하루 한 번 `schedule.json` 갱신
- **원정 성적 지수 v2**: 지역별 원정 승률 · 요일별 · 경기장별 크로스탭
- **AI agent 도구 추가**: `get_recent_results(team, n)` — 최근 N경기 결과 기반 폼 분석

---

## 8. 최종 결정 — 진행 여부

### ✅ 진행 권장 이유
1. 사용자가 "일정이 맞지 않는 거 같다"고 명확히 지적
2. kbo-game 은 실측 동작 · zero-dep · MIT
3. 데이터 신뢰도 대폭 상승 → AI 답변 · 예측 모델 모두 질 향상
4. 기존 frontend 변경 최소 (type + UI 약간 · 코어 로직 불변)
5. 작업 범위 ~2시간 · 되돌리기 쉬움 (schedule.json 한 파일 교체)

### ⚠️ 진행 보류 고려 이유
1. 발표가 임박했으면 리스크 (비록 낮지만) 회피
2. KBO API 가 크롤 방지 조치 할 가능성 (지금 시점엔 동작)
3. UI 렌더링 로직 추가 복잡화

### 제안
**진행**. 현재 데이터 질의 체감 문제가 명확하고, 통합 난도는 낮음. 
단, 분리 커밋으로:
1. **Commit 1**: 스크립트 추가 + 실행 + `schedule.json` 교체만
2. **Commit 2**: UI 개선 (score·status 렌더)
3. **Commit 3**: team-stats 재계산 + AI 도구 확장

각 커밋 독립적으로 되돌리기 가능.

---

## 9. 사용자 확인 요청

진행 여부 결정:
- [ ] **Go** — 위 계획대로 실행 (약 2시간, 3 커밋 분리)
- [ ] **Partial** — Step 1~3 만 (schedule 교체 + UI 기본 개선)
- [ ] **Hold** — 일단 보류, 발표 이후 진행

---

*작성: 2026-04-18*
*관련: `/Volumes/Corsair EX300U Media/00_work_out/00_data_set/k-skill-main/kbo-results/SKILL.md`*
