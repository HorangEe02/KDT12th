# 🎯 차기 세션 기능 확장 — 브레인스토밍 & 상세 계획

> 작성: 2026-04-18 (Phase 6 배포 + KBO 실데이터 통합 이후)
> 범위: 6 개 신규 기능 요청
> 산출물: feature 별 실현 가능성·우선순위·구현 경로 · 사용자 사전 액션

---

## 0. 요약 (한눈에)

| # | 기능 | 실현 가능? | 난이도 | 예상 시간 | 필수 사전 액션 |
|---|---|---|---|---|---|
| 1 | 로그인/회원가입 | ✅ | 중 | 3~4h | Firebase Auth 활성화 + Web SDK 키 등록 |
| 2 | 관리자 계정 | ✅ | 중 | 2~3h | #1 선행 + 초기 admin 이메일 지정 |
| 3 | 사용자별 세션 영속화 | ✅ | 중 | 2~3h | #1 선행 + Firestore 규칙 수정 |
| 4 | 코스 내보내기 (CSV/Word/PPT/PDF) | ✅ | 중상 | 4~6h | 한글 폰트 에셋 추가 |
| 5 | 출발지 프리셋 확장 | ✅ | 하 | 0.5h | 없음 (즉시 가능) |
| 6 | Places 레이아웃 재배치 + 지도 | ✅ | 중 | 2~3h | 없음 (즉시 가능) |

**총 소요**: 14~20시간 · **3 세션 분할 권장**

---

## 1. 로그인 / 회원가입 페이지

### 1-1. 실현 가능성 ✅
Firebase 프로젝트 `mini12-310f5` 존재 + Firebase SDK v12 설치됨 + `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` 이미 apphosting.yaml 에 선언돼 있음.

### 1-2. 기술 선택: **Firebase Authentication**
**이유**:
- 기존 Firebase 프로젝트 재활용 (계정 통합)
- Email/Password + Google OAuth + Kakao 등 소셜 로그인 쉬움
- `firebase-admin` 으로 서버 검증 용이 (이미 설치됨)
- 무료 쿼터: 50K MAU 까지 (데모 용도로 차고 넘침)

**대안 (비추)**:
- NextAuth.js → 추가 의존성 · 설정 복잡
- Supabase → 이미 Firebase 생태계 결정된 상황
- 자체 구현 → 보안 리스크

### 1-3. 파일 트리
```
frontend/
├── lib/firebase/
│   ├── client.ts (기존)
│   ├── auth.ts                 # 🆕 signIn·signUp·signOut·onAuth
│   └── user-session.ts         # 🆕 서버 세션 쿠키 (HttpOnly)
├── lib/store/
│   └── auth.ts                 # 🆕 Zustand: user | loading | error
├── components/auth/
│   ├── auth-provider.tsx       # 🆕 context 제공 · onAuthStateChanged 구독
│   ├── login-form.tsx          # 🆕 email/pw + Google 버튼
│   ├── signup-form.tsx         # 🆕 email/pw/displayName
│   └── user-badge.tsx          # 🆕 사이드바/nav 우상단
├── app/
│   ├── login/page.tsx          # 🆕
│   ├── signup/page.tsx         # 🆕
│   └── api/auth/
│       └── session/route.ts    # 🆕 id token → 세션 쿠키 (SSR용)
```

### 1-4. 흐름

```
[Signup] → createUserWithEmailAndPassword
         → Firestore users/{uid} 도큐먼트 생성
         → 사이드바 자동 로그인 + "/" 리다이렉트

[Login]  → signInWithEmailAndPassword
         → onAuthStateChanged → Zustand setUser
         → 마지막 사용 경로로 리다이렉트 (?next=/ai)

[Logout] → signOut + router.push('/login')
```

### 1-5. 사용자 사전 액션
1. Firebase Console → Authentication → 시작하기 → **이메일/비밀번호 제공업체 활성화** + **Google 제공업체 활성화**
2. 설정 → 일반 → 웹 앱 → 구성 복사:
   - `apiKey` → `NEXT_PUBLIC_FIREBASE_API_KEY` secret 등록
   - `messagingSenderId` → `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID` secret
   - `appId` → `NEXT_PUBLIC_FIREBASE_APP_ID` secret
3. `apphosting.yaml` 의 해당 시크릿 주석 해제

---

## 2. 관리자 계정

### 2-1. 실현 가능성 ✅ (#1 선행 필요)

### 2-2. 기술 선택: **Custom Claims + Firestore `users` 컬렉션**
- Custom Claims (보안) — 서버 검증용 (JWT 내장, 변조 불가)
- Firestore users 컬렉션 (UI 편의) — 목록 조회, 메타 정보

### 2-3. 스키마
```typescript
// Firestore: users/{uid}
{
  uid: string,
  email: string,
  displayName: string,
  role: "user" | "admin",       // UI 표시용 · 실 권한은 custom claim
  createdAt: Timestamp,
  lastSignInAt: Timestamp,
  photoURL?: string,
}
```

### 2-4. 초기 admin 지정
```bash
# scripts/grant-admin.mjs (새로 작성)
node scripts/grant-admin.mjs --email catlife9029@gmail.com
# 내부: firebase-admin 으로 setCustomUserClaims({admin:true})
#       + Firestore users/{uid}.role = "admin" 동기화
```

### 2-5. `/admin` 페이지 구성
- **유저 테이블**: email · displayName · role · 가입일 · 최근 접속 · 저장한 코스 수
- **액션**: 관리자 권한 부여/회수 · 계정 비활성화
- **통계**: 전체 가입자 수 · 최근 7일 가입 · 평균 세션 수
- 서버 보호:
  ```typescript
  // app/admin/layout.tsx
  const claims = await verifySessionCookie(cookie);
  if (!claims.admin) redirect('/');
  ```

### 2-6. 파일
```
app/admin/
├── layout.tsx                  # 🆕 admin 클레임 체크
├── page.tsx                    # 🆕 대시보드
├── users/page.tsx              # 🆕 유저 목록
└── api/
    ├── users/route.ts          # 🆕 GET list + PATCH role
    └── users/[uid]/route.ts    # 🆕 DELETE · disable
components/admin/
├── user-table.tsx
├── role-toggle.tsx
└── admin-stats.tsx
scripts/
└── grant-admin.mjs             # 🆕 초기 admin 지정 CLI
```

---

## 3. 사용자 활동 저장 + 재로그인 복원

### 3-1. 실현 가능성 ✅ (#1 선행 + Firestore 규칙 수정)

### 3-2. 저장 대상 정의

| 항목 | 현재 위치 | 이전 대상 |
|---|---|---|
| 방문 구장 (뱃지) | localStorage (anon UUID) | Firestore `user_visits/{uid}` |
| 사이드바 필터 (팀·기간·예산·인원·이동수단) | localStorage (Zustand persist) | Firestore `user_prefs/{uid}` |
| AI 챗 히스토리 | 메모리 (페이지 새로고침 시 소실) | Firestore `user_chats/{uid}/sessions/{sessionId}` |
| 생성된 코스 (공유 전 초안 포함) | shared_plans (anon) | Firestore `user_plans/{uid}/{planId}` |

### 3-3. 동기화 로직

```typescript
// lib/firebase/user-sync.ts
export async function syncOnSignIn(uid: string) {
  const [localPrefs, localVisits] = [useFilters.getState(), useBadges.getState()];
  const [remotePrefs, remoteVisits] = await Promise.all([
    loadUserPrefs(uid), loadUserVisits(uid),
  ]);
  // merge 전략: remote 우선 (다른 기기에서 업데이트됐을 수 있음)
  // 단, local 에 remote 보다 최신 데이터가 있으면 local 유지 (updatedAt 비교)
  const merged = { ...localPrefs, ...remotePrefs };
  useFilters.setState(merged);
  useBadges.setVisited([...new Set([...localVisits.visited, ...remoteVisits])]);
  // 서버에도 반영
  await saveUserPrefs(uid, merged);
}
```

### 3-4. Firestore 규칙 업데이트

```javascript
// firestore.rules (교체)
match /users/{uid} {
  allow read: if request.auth.uid == uid || request.auth.token.admin == true;
  allow write: if request.auth.uid == uid;  // 본인만 수정
}
match /user_visits/{uid} {
  allow read, write: if request.auth.uid == uid;
}
match /user_prefs/{uid} {
  allow read, write: if request.auth.uid == uid;
}
match /user_chats/{uid}/{document=**} {
  allow read, write: if request.auth.uid == uid;
}
match /user_plans/{uid}/{document=**} {
  allow read: if request.auth.uid == uid || resource.data.public == true;
  allow write: if request.auth.uid == uid;
}
match /shared_plans/{planId} {
  allow read: if true;   // 공유 링크 접근용
  allow create: if request.auth.uid != null;
  allow update, delete: if false;
}
```

### 3-5. 로그아웃 후 재로그인 UX
- 로그아웃 시: localStorage 유지 (빠른 재로그인)
- 재로그인 시: Firestore pull → localStorage merge → UI 반영
- 다른 디바이스 변경 감지: onSnapshot 구독 (실시간)

---

## 4. 코스 내보내기 (CSV / Word / PPT / PDF)

### 4-1. 실현 가능성 ✅

### 4-2. 라이브러리 비교 · 모두 클라이언트 사이드 가능

| 포맷 | 라이브러리 | 번들 크기 | 한글 지원 | 권장 |
|---|---|---|---|---|
| **CSV** | Native `Blob` | 0 KB | ✅ UTF-8 BOM | ✅ |
| **Word (.docx)** | `docx` v9 | ~3.5 MB | ✅ 임베드된 폰트 사용 가능 | ✅ |
| **PPT (.pptx)** | `pptxgenjs` v4 | ~2.6 MB | ✅ | ✅ |
| **PDF** | `jspdf` v4 + `jspdf-autotable` | ~30 MB unpacked (!) | ⚠️ 한글 폰트 임베드 필요 (`KBO Dia Gothic` 등) | ✅ |

**대안 PDF**: 서버에서 Puppeteer (Chrome) — 리치하지만 Cloud Run 무겁고 실행 비용↑. MVP 는 jspdf.

### 4-3. 내보낼 코스 데이터 구조

```typescript
interface ExportableCourse {
  user: { email, displayName };
  generatedAt: string;
  filters: { team, dateRange, budget, party, transport };
  game: Game;                    // 선택된 경기
  stadium: Stadium;              // 경기장 정보
  route: RouteResult;            // 길찾기 결과
  pois: { food: POI[], stay: POI[], tour: POI[] };  // TOP 5 각 카테고리
  weather?: Forecast;
  aiSummary?: string;            // AI 챗봇이 생성한 요약
  winProb?: number;
}
```

### 4-4. 파일 트리
```
frontend/
├── lib/export/
│   ├── course-data.ts          # 🆕 ExportableCourse 빌드 (현재 상태 → 구조화)
│   ├── csv.ts                  # 🆕 to CSV blob (papaparse)
│   ├── docx.ts                 # 🆕 to Word docx (docx lib)
│   ├── pptx.ts                 # 🆕 to PowerPoint (pptxgenjs)
│   └── pdf.ts                  # 🆕 to PDF (jspdf + jspdf-autotable + 한글 폰트)
├── components/export/
│   ├── export-button-group.tsx # 🆕 4 포맷 버튼
│   └── export-preview.tsx      # 🆕 내보내기 전 미리보기
├── public/fonts/
│   └── KBO_Dia_Gothic.ttf.base64  # 🆕 PDF 한글 폰트 (base64 직렬화)
```

### 4-5. 배치 위치
- **/ai 페이지**: 챗봇 응답 하단 "이 계획 저장/내보내기" 버튼
- **/badges 페이지**: "공유 계획" 섹션 옆 "내보내기" 드롭다운
- **/share/[id] 페이지**: 공개 공유 링크에서도 내보내기 가능

### 4-6. 한글 폰트 이슈 (PDF)
- `jspdf` 기본 내장 폰트 = Helvetica 계열 → 한글 빈 네모
- 해결: KBO Dia Gothic TTF 를 base64 로 변환 후 `doc.addFileToVFS` + `doc.setFont`
- 대안: Noto Sans KR 사용 (OFL 라이선스)
- 번들 크기 영향: 한글 폰트 ~2MB base64 → 런타임 메모리 부담 약간
- 최적화: 동적 import (`dynamic(() => import('./pdf'))`) 로 PDF 필요 시에만 로드

---

## 5. 지도 출발지 프리셋 확장

### 5-1. 실현 가능성 ✅ (즉시 가능)

### 5-2. 현재 (4개)
`lib/map/origins.ts`:
- 서울역 (37.5547, 126.9707)
- 강남역 (37.4979, 127.0276)
- 수원역 (37.2657, 127.0009)
- 대전역 (36.3322, 127.4342)

### 5-3. 확장안 (13개 + geolocation)

**수도권** (5):
- 서울역 · 강남역 · 용산역 · 청량리역 · 수원역

**중부** (3):
- 천안아산역 · 오송역 · 대전역

**영남** (4):
- 동대구역 · 포항역 · 부산역 · 울산역 · 진영역 (창원 NC 가까움)

**호남** (3):
- 광주송정역 · 여수엑스포역 · 목포역

**특수 (2)**:
- 📍 **내 위치** — `navigator.geolocation.getCurrentPosition` (HTTPS 필수)
- 🛫 **공항** 3종: 인천공항 · 김포공항 · 제주공항 (원정 응원 팬 일부 항공 이용)

### 5-4. UI 개선
현재: 수평 pill 버튼 4개  
신규: 지역별 그룹 드롭다운 또는 accordion

```tsx
<details open>
  <summary className="font-bold">🚄 수도권</summary>
  {SEOUL_STATIONS.map(...)}
</details>
<details>
  <summary>🚅 중부</summary>
  ...
</details>
```

또는 **"가까운 역 자동 추천"**: Geolocation 으로 가장 가까운 역 표시.

### 5-5. 파일
```
lib/map/origins.ts  (변경: 13개 역 + REGION_GROUPS + 좌표)
components/map/map-controls.tsx  (변경: accordion UI)
```

### 5-6. Effort: 30분

---

## 6. Places 페이지 레이아웃 재구성 + 지도 추가

### 6-1. 실현 가능성 ✅

### 6-2. 레이아웃 변경

**현재 순서**:
1. Stadium picker + metrics
2. Category tabs
3. Scatter chart (거리 × 평점)
4. TOP 10 cards

**요청된 순서**:
1. Stadium picker + metrics
2. Category tabs
3. **🆕 지도** — 구장 + TOP 10 POI 마커
4. TOP 10 cards (중간)
5. Scatter chart (최하단)

### 6-3. 신규 컴포넌트

```
components/places/
├── places-mini-map.tsx         # 🆕 React-Leaflet · ssr:false
│                               # 구장 마커 + TOP 10 POI + 구장 반경원(500m)
│                               # 마커 클릭 → 아래 TOP 10 카드 리스트 스크롤
├── places-map-shell.tsx        # 🆕 dynamic 래퍼
```

### 6-4. 상호작용 (값 추가)
- 지도의 POI 마커 클릭 → 해당 카드로 스무스 스크롤 + 2초 하이라이트
- TOP 10 카드의 "지도에서 보기" 버튼 → 지도 해당 마커로 pan + popup open
- 상태 관리: `selectedPoiId` URL query (`?p=CONTENT_ID`)

### 6-5. app/(shell)/places/page.tsx 변경
```tsx
return (
  <section className="space-y-5">
    {/* 1. 헤더 + 구장 선택 + metrics + 카테고리 탭 — 유지 */}
    <header>...</header>
    <StadiumPicker ... />
    <Metric ... />
    <CategoryTabs ... />

    {/* 2. 🆕 지도 — 최상단 */}
    <section>
      <h3>📍 TOP 10 위치 지도</h3>
      <PlacesMapShell stadium={stadium} pois={active.slice(0,10)} selected={p.p} />
    </section>

    {/* 3. TOP 10 카드 — 중간 (기존 그리드) */}
    <section>
      <h3>🧾 가까운 ... TOP 10</h3>
      <PoiCardGrid pois={active.slice(0,10)} />
    </section>

    {/* 4. 산점도 — 최하단 (기존) */}
    <section>
      <h3>📊 거리 × 평점 산점도</h3>
      <ScatterPlaces ... />
    </section>
  </section>
);
```

### 6-6. Effort: 2~3시간

---

## 7. 우선순위 + 세션 분할 제안

### 세션 A: 즉시 실행 가능 (Feature 5 + 6) — 약 3시간
- 사전 액션 없음 · 외부 의존성 없음
- **가장 빠른 사용자 체감 개선**
- 한 번의 커밋·배포로 완료

### 세션 B: 인증 기반 (Feature 1 + 2 + 3) — 약 8~10시간
- 사용자 사전 액션 필요 (Firebase Console Auth 활성화 + 키 등록)
- 3 기능이 서로 의존 → 한 사이클로 진행
- 서브 커밋:
  1. Auth 기본 (Login/Signup/Logout)
  2. Admin 페이지 + 초기 admin CLI
  3. 사용자 데이터 동기화 + Firestore 규칙 업데이트

### 세션 C: 내보내기 (Feature 4) — 약 4~6시간
- 한글 폰트 준비 · 4 포맷 각각 테스트
- 세션 B 의 "코스 저장" 기능과 연결됨 → B 이후 진행 권장
- 서브 커밋:
  1. CSV + 데이터 스키마
  2. Word + PPT
  3. PDF (한글 폰트 포함)

---

## 8. 사용자 사전 액션 체크리스트

세션 B 진입 전 (→ Firebase Auth + DB 기능):

- [ ] Firebase Console → Authentication 섹션 "시작하기" 클릭
- [ ] 로그인 제공업체:
  - [ ] 이메일/비밀번호 → 사용 설정됨 + 비밀번호 없는 로그인은 비활성 유지
  - [ ] Google → 사용 설정 + 프로젝트 지원 이메일 선택
- [ ] Firebase Console → 프로젝트 설정 → 일반 → 웹 앱 "my-web-app" 선택
  - [ ] Firebase SDK snippet 의 config 복사
  - [ ] `apiKey` 를 `NEXT_PUBLIC_FIREBASE_API_KEY` 로 secret 등록:
    ```bash
    firebase apphosting:secrets:set NEXT_PUBLIC_FIREBASE_API_KEY --project mini12-310f5
    ```
  - [ ] `messagingSenderId` → `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID` secret
  - [ ] `appId` → `NEXT_PUBLIC_FIREBASE_APP_ID` secret
- [ ] `frontend/apphosting.yaml` 의 해당 시크릿 주석 해제
- [ ] 초기 admin 이메일 결정 (예: `catlife9029@gmail.com`)
- [ ] (선택) `secrets/service-account.json` 생성 → 로컬 admin SDK 테스트용

---

## 9. 리스크 매트릭스

| 리스크 | 확률 | 영향 | 완화 |
|---|---|---|---|
| Firebase Auth quota (50K MAU) 초과 | 낮음 | 중 | 과금 알림 설정 |
| Firestore 읽기 쿼터 | 낮음 | 중 | `@tanstack/react-query` 캐싱 · onSnapshot 제한 |
| PDF 한글 폰트 로딩 느림 | 중 | 낮 | 동적 import + 로딩 인디케이터 |
| 악성 회원가입 (봇) | 중 | 중 | Firebase App Check 적용 |
| 개인정보 보호법 | 중 | 상 | 최소 수집 원칙 · 이용약관·개인정보처리방침 페이지 작성 |
| Cloud Run 증가 비용 | 낮음 | 중 | minInstances=0 유지 · 모니터링 |
| React-Leaflet + 동적 import SSR 이슈 (재발) | 중 | 중 | Places map 은 이미 해결된 패턴 재사용 |

---

## 10. 다음 행동

사용자가 승인 후:
1. **즉시 가능** — 세션 A (Feature 5 + 6) 바로 시작
2. **계획 검토** — Feature 1~3 흐름 더 세부화 (DB 스키마, UI wireframe)
3. **사전 액션** — Firebase Auth 활성화 + 키 등록 (사용자 수행)

어느 옵션이든 이 문서 기반으로 세부 실행 계획 재확정 후 진행.

---

*작성: 2026-04-18 Session F+*
*참고: `docs/KBO_DATA_INTEGRATION.md`, `docs/CLEANUP_PLAN.md`, `docs/SESSION_F_DEPLOY_RUNBOOK.md`*
