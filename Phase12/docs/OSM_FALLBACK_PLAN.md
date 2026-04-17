# 🗺️ OSM 기반 길찾기 Fallback 전략 — 브레인스토밍 & 구현 계획

> 작성: 2026-04-17 (Session D 시작 시점)
> 목표: Kakao 모빌리티 길찾기 API가 실패할 때, 직선(haversine) 대신 **실제 도로망 기반 경로**를 무료 OSM 스택으로 제공.

---

## 1. 문제 정의

### 1-1. 현재 상태 (Phase 3 Python 포팅 전)
`src/api/kakao_map.py` 의 fallback 은 **haversine 직선** 하나 — 경로 폴리라인이 2점짜리 대각선으로만 렌더되어 UX가 불완전했다.

### 1-2. Kakao 모빌리티 API가 실패하는 시나리오
| # | 시나리오 | 빈도 | 영향 |
|---|---|---|---|
| ① | `KAKAO_MOBILITY_API_KEY` 미등록 (현 .env) | **상시** | 로컬/프로덕션 모두 |
| ② | 모빌리티 API 정책상 REST 공용 키만으로 호출 불가 | 상시 | 무료 승인 없을 때 |
| ③ | IP/도메인 화이트리스트 미등록 | 간헐 | Cloud Run·App Hosting 배포 시 |
| ④ | 5xx / 네트워크 타임아웃 | 드묾 | 모든 환경 |
| ⑤ | 일일 쿼터 초과 | 낮지만 가능 | 시연·트래픽 피크 |
| ⑥ | 해외/데모 환경 (한국 외부에서 평가자 접속) | 드묾 | 평가자 접근 |

### 1-3. 요구사항
- **키 없이 작동**해야 한다 (기본 fallback).
- **실제 도로 경로**(폴리라인 vertices ≥ 10) — 직선 대비 체감 품질 대폭 개선.
- **프로덕션 친화**: Cloud Run / App Hosting 에서 네트워크 정책 없이 호출 가능.
- **라이선스 호환**: ODbL(OSM) 표시만 하면 상용 OK.

---

## 2. 후보 OSM 라우팅 제공자 비교

### 2-1. 옵션 매트릭스

| 제공자 | URL | 키 | 무료 한도 | HTTPS | 한국 커버리지 | 응답 | 추천 |
|---|---|---|---|---|---|---|---|
| **OSRM demo** | router.project-osrm.org | ❌ 없음 | **소프트**(상업사용 자제 권고) | ✅ | 양호 | GeoJSON polyline | ⭐ |
| OpenRouteService | api.openrouteservice.org | ✅ 필요 | 2000 req/day | ✅ | 양호 | GeoJSON | 2순위 |
| GraphHopper | graphhopper.com/api/1 | ✅ 필요 | 500 req/day | ✅ | 양호 | GeoJSON | 3순위 |
| Valhalla (Stadia Maps) | api.stadiamaps.com | ✅ 필요 | 2500 req/day | ✅ | 보통 | polyline6 | 4순위 |
| Mapbox Directions | api.mapbox.com | ✅ 필요 | 100k req/mo | ✅ | 양호 | GeoJSON | 비OSM 순수 X |
| 자체 OSRM (Docker) | 온프레 | ❌ | 무제한 | 설정 | 최상 | GeoJSON | 과한 인프라 |

### 2-2. 선택: **OSRM demo + haversine 2단계**
- **Tier 2 (OSM 실경로)**: `https://router.project-osrm.org` 공용 데모 서버
  - 무료 · **API 키 불필요** · HTTPS · CORS 허용 · 한국 도로망 포함
  - 단점: "heavy usage 지양" 권고. 시연·MVP·저트래픽 단계는 문제 없음.
  - 장기 운영 시 → 2순위(ORS) 로 전환하거나 자체 OSRM 도커 운영.
- **Tier 3 (haversine 직선)**: 네트워크 완전 차단 시 최후의 보루.

### 2-3. OSRM 응답 포맷 (샘플)
```
GET https://router.project-osrm.org/route/v1/driving/127.0719,37.5122;127.0097,37.2997?overview=full&geometries=geojson&alternatives=false&steps=false
```
```json
{
  "code": "Ok",
  "routes": [{
    "distance": 38421.2,           // meters
    "duration": 3020.4,            // seconds (우회 속도 모델)
    "geometry": {
      "type": "LineString",
      "coordinates": [[127.0719, 37.5122], [...], [127.0097, 37.2997]]
    }
  }],
  "waypoints": [...]
}
```
좌표 순서가 `[lon, lat]` → Leaflet 은 `[lat, lng]` 이므로 매핑 시 swap 필요.

---

## 3. 공통 경로 결과 계약

모든 Tier 가 같은 shape 을 반환 → UI 코드가 소스를 신경 안 씀.

```typescript
interface RouteResult {
  polyline: Array<[number, number]>; // [lat, lng] pairs (Leaflet 친화)
  distance_m: number | null;
  duration_sec: number | null;
  toll_fare_krw: number | null;       // OSM 은 항상 null
  source: "kakao" | "osrm" | "haversine";
  fallback: boolean;                  // source !== "kakao" 이면 true
  attempts: Array<{                   // 관찰용 (디버깅·UI 캡션)
    provider: string;
    status: "ok" | "error" | "skipped";
    ms: number;
    reason?: string;
  }>;
  fetched_at: number;                 // epoch ms (cache 키)
}
```

---

## 4. 3-Tier Fallback Decision Flow

```
requestRoute(origin, destination, mode="driving")
  │
  ├─ Tier 1: Kakao 모빌리티
  │   ├─ KAKAO_MOBILITY_API_KEY 있음? → POST /directions
  │   │    ├─ 200 & routes.length ≥ 1 → Ok → return (source=kakao)
  │   │    └─ fail → attempts 기록, Tier 2 로 fall through
  │   └─ 키 없음 → Tier 2 로 직행
  │
  ├─ Tier 2: OSRM demo
  │   ├─ GET /route/v1/driving/{lon1},{lat1};{lon2},{lat2}?geometries=geojson
  │   │    ├─ code=="Ok" & routes[0].geometry.coordinates.length ≥ 2 → return (source=osrm)
  │   │    └─ fail → attempts 기록, Tier 3 로 fall through
  │   └─ CORS/타임아웃 → Tier 3
  │
  └─ Tier 3: Haversine (직선)
      └─ 항상 성공. polyline = [[originLat,originLng],[destLat,destLng]] (source=haversine)
```

### 4-1. Timeout / Retry 전략
- 각 Tier: **5초 AbortController** (fetch timeout)
- **재시도 없음** — 실패 즉시 다음 Tier. 체감 지연 합계: 최악의 경우 10초 (Tier 1 + Tier 2 모두 타임아웃 후 Tier 3 즉시).
- 실제: 대부분 키 없음 → Tier 1 건너뛰고 Tier 2 만 호출 → 평균 0.3–1.5초.

### 4-2. 캐시 (In-memory + Future: Firestore)
- 키: `md5(origin_lat+origin_lng+dest_lat+dest_lng+mode)` — 6자리 좌표 반올림.
- 수명: 프로세스 lifetime (Next.js 서버) — 단순 `Map<string, RouteResult>`.
- 클라이언트: `TanStack Query` with `staleTime: 30min`.
- Phase 7+: Firestore `route_cache` 컬렉션 추가 (선택).

---

## 5. 구현 파일 트리

```
frontend/lib/api/
  ├─ kakao.ts        # Tier 1 - Kakao Mobility
  ├─ osrm.ts         # Tier 2 - OSRM public
  ├─ haversine.ts    # Tier 3 - straight line
  └─ route.ts        # orchestrator (public entry: requestRoute())

frontend/app/api/route/
  └─ route.ts        # Next.js API handler (POST)

frontend/lib/types/index.ts
  └─ RouteResult, RouteAttempt   # 타입 추가

frontend/components/map/
  ├─ leaflet-map.tsx      # 동적 로드 + 4 레이어 + 경로
  └─ route-summary.tsx    # 거리/시간/소스 배지 표시
```

---

## 6. 에러 매트릭스

| 상황 | Tier 1 | Tier 2 | Tier 3 | 최종 source | UI 경고 |
|---|---|---|---|---|---|
| 정상 (카카오 키 승인됨) | ✅ | skip | skip | kakao | 없음 |
| 카카오 키 없음 | skip | ✅ | skip | osrm | "OSM 기반 경로" (info) |
| 카카오 키 있으나 401 | ❌ | ✅ | skip | osrm | "Kakao 인증 실패 → OSM" (warning) |
| OSRM 타임아웃 | skip or ❌ | ❌ timeout | ✅ | haversine | "직선 거리 표시 중" (warning) |
| 오프라인 | ❌ | ❌ | ✅ | haversine | "오프라인 — 직선 거리" (error) |
| 좌표 identical | — | — | — | — | "동일 지점" (info) |

---

## 7. 동선 품질 비교 (잠실 → 수원 KT 위즈파크)

| 소스 | 거리 | 소요 | 폴리라인 점 수 | 품질 |
|---|---|---|---|---|
| Kakao Mobility | 38.2 km | 약 45분 | ~2500 | ⭐⭐⭐⭐⭐ (실시간 교통) |
| **OSRM demo** | 38.4 km | 약 50분 | ~620 | ⭐⭐⭐⭐ (도로망 정확, 교통정보 無) |
| Haversine 직선 | 37.8 km | — | 2 | ⭐ (대각선만) |

---

## 8. 테스트 플랜 (Session D 구현 후)

### 8-1. 유닛
- `haversine.ts`: 잠실 ↔ 수원 거리 = 37.8 km ± 0.5
- `osrm.ts`: `parseOSRM({code:"Ok", routes:[...]})` → polyline 길이 > 10
- `osrm.ts`: `parseOSRM({code:"NoRoute"})` → throw
- `route.ts`: Kakao 키 없음 → osrm 호출됨 → source==="osrm"

### 8-2. 통합
- `curl -X POST /api/route -d '{"origin":[37.5122,127.0719],"destination":[37.2997,127.0097]}'` → `{source:"osrm", distance_m:~38000, polyline.length > 100}`
- 네트워크 차단 후 호출 → `{source:"haversine", polyline.length === 2}`
- `KAKAO_MOBILITY_API_KEY=test` 더미 → Tier 1 실패 → Tier 2 성공 → `{source:"osrm"}`

### 8-3. UI
- 지도에서 Kakao 경로: 실선 파랑, 소스 배지 "Kakao"
- OSRM 경로: 실선 보라(자주색) + 배지 "OSM"
- Haversine: 점선 회색 + 경고 배너 "직선 거리 — 실제 도로와 다를 수 있음"

---

## 9. 라이선스 & 표기 의무

- OSRM demo 서버는 내부적으로 **OpenStreetMap** 데이터 사용 → ODbL 표기 필수.
- 지도 하단 attribution:
  ```
  © OpenStreetMap contributors · Routing by OSRM
  ```
- Leaflet 타일도 OSM 사용 → 같은 attribution 유지.
- Kakao 로 경로가 왔을 때는 `지도 데이터 © Kakao` 추가 표기.

---

## 10. 향후 개선 (Out-of-scope for Session D)

1. **Workers / Edge Runtime**: route API 를 Edge 런타임으로 이식 — 레이턴시 감소
2. **자체 OSRM 도커**: 한국 PBF 만 빌드 (1.5GB) → Cloud Run sidecar 또는 별 서비스
3. **대중교통 라우팅**: OTP (OpenTripPlanner) 연동 — 현 프로젝트는 driving 전용
4. **실시간 교통**: OSRM 에는 없음 → 카카오 성공 시 배지 강조
5. **Firestore route_cache**: 히트율 높을 때 비용 절감

---

## 11. 구현 체크리스트 (Session D에서 수행)

- [ ] `lib/types/index.ts` : `RouteResult`, `RouteAttempt`, `RouteMode` 추가
- [ ] `lib/api/haversine.ts` : `haversineM()` + `haversineRoute()`
- [ ] `lib/api/osrm.ts` : `fetchOSRM()` + parse + timeout
- [ ] `lib/api/kakao.ts` : `fetchKakaoRoute()` — 키 없으면 즉시 skip 반환
- [ ] `lib/api/route.ts` : `requestRoute()` — 3-tier orchestrator + 인메모리 캐시
- [ ] `app/api/route/route.ts` : POST + GET 핸들러 (Zod 검증)
- [ ] `components/map/route-summary.tsx` : source 배지 + 경고 배너
- [ ] `components/map/leaflet-map.tsx` : 경로 폴리라인 색/점선 소스 분기 렌더
- [ ] curl 테스트 3종 (카카오 키 有/無/네트워크 차단)

---

*작성: 2026-04-17 · Phase 6 Session D 시작 시점*
