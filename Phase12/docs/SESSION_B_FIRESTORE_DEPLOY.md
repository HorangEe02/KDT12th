# 🔐 Firestore Rules + Indexes 배포 가이드 (Step 7)

> 작성: 2026-04-18 · 짝 문서: `docs/FIREBASE_DB_PLAN.md` §3-4
> 적용 범위: `firestore.rules` + `firestore.indexes.json`
> 위험도: **중** — 잘못 적용 시 정상 사용자 차단됨. 단계적으로 검증.

---

## 0. 변경 요약

| 항목 | 이전 | 신규 |
|---|---|---|
| 컬렉션 수 | 3 (`shared_plans`, `visited_stadiums`, `chat_sessions`) | 9 (위 + `users`, `user_visits`, `user_prefs`, `user_chats/...`, `user_plans/items`, `admin_audit`, `system_metrics`, `feedback`) |
| owner 검증 | 없음 (전부 server only) | `request.auth.uid == uid` 매칭 |
| admin 권한 | 없음 | `request.auth.token.admin == true` custom claim |
| 비활성 계정 차단 | 없음 | `request.auth.token.disabled != true` |
| public 공유 | shared_plans 전체 | shared_plans + user_plans `public=true` |
| 익명 visited_stadiums | 클라이언트 deny (실제 미동작) | default deny (정리) |
| 인덱스 | 0 | 6 composite |

---

## 1. 사전 검증 — 로컬 emulator (선택, 권장)

### 1-1. Emulator 시작
```bash
cd "/Volumes/Corsair EX300U Media/00_work_out/01_complete/Phase12"
firebase emulators:start --only firestore --project mini12-310f5
```
브라우저: http://localhost:4000 → Firestore tab

### 1-2. 수동 시나리오 8개 (Console 또는 코드)

| # | 동작 | 기대 결과 |
|---|---|---|
| 1 | 비로그인 → `user_prefs/abc` get | 차단 |
| 2 | 로그인 (uid=abc) → `user_prefs/abc` set | 허용 |
| 3 | 로그인 (uid=abc) → `user_prefs/xyz` set (다른 uid) | 차단 |
| 4 | 로그인 → `users/abc` 생성 + role="admin" 시도 | 차단 (role="user" 강제) |
| 5 | 로그인 (admin claim) → `users` list | 허용 |
| 6 | 비로그인 → `shared_plans/p1` get | 허용 |
| 7 | 로그인 → `admin_audit` write | 차단 (서버 only) |
| 8 | 비로그인 → `feedback` create (content="좋아요") | 허용 |

### 1-3. 자동 unit test (옵션)

`tests/firestore-rules.test.ts` 작성 후:
```bash
pnpm add -D @firebase/rules-unit-testing vitest
firebase emulators:exec --only firestore "vitest run tests/firestore-rules.test.ts" \
  --project mini12-310f5
```
> 본 단계는 시간상 생략. 수동 시나리오 또는 프로덕션 검증으로 대체 가능.

---

## 2. 프로덕션 배포

### 2-1. Rules + Indexes 한 번에
```bash
cd "/Volumes/Corsair EX300U Media/00_work_out/01_complete/Phase12"
firebase deploy --only firestore --project mini12-310f5
```

출력 예시:
```
i  deploying firestore
i  cloud.firestore: checking firestore.rules for compilation errors...
✔ cloud.firestore: rules file firestore.rules compiled successfully
i  firestore: uploading rules firestore.rules...
✔ firestore: released rules firestore.rules to cloud.firestore
i  firestore: deploying indexes...
i  firestore: 6 indexes to deploy. (this may take several minutes...)
✔ firestore: deployed indexes in firestore.indexes.json successfully
✔ Deploy complete!
```

> 인덱스는 **빌드 5~15분** 소요 가능. Console → Firestore → Indexes 탭에서 진행률 확인.

### 2-2. Rules 만 배포 (긴급 패치 시)
```bash
firebase deploy --only firestore:rules --project mini12-310f5
```

### 2-3. Indexes 만 배포
```bash
firebase deploy --only firestore:indexes --project mini12-310f5
```

---

## 3. 배포 후 검증 (smoke test)

### 3-1. 본인 데이터 read/write
1. 로그인 → `/badges` 잠실 토글
2. Firestore Console → `user_visits/{본인uid}` 도큐먼트 생성/업데이트 확인
3. 사이드바 응원팀 KT → 1.5초 후 `user_prefs/{본인uid}` 의 team="KT" 확인

### 3-2. 타인 데이터 차단
브라우저 콘솔에서:
```javascript
import { doc, getDoc } from "firebase/firestore";
import { getClientDb } from "@/lib/firebase/client";
await getDoc(doc(getClientDb(), "user_prefs", "다른사람uid"));
// → FirebaseError: Missing or insufficient permissions.
```

### 3-3. shared_plans 공개 read
```bash
curl https://firestore.googleapis.com/v1/projects/mini12-310f5/databases/(default)/documents/shared_plans/{planId}
# → 200 OK (anon access 가능)
```

### 3-4. admin_audit write 차단
브라우저 콘솔:
```javascript
import { addDoc, collection } from "firebase/firestore";
await addDoc(collection(getClientDb(), "admin_audit"), { action: "test" });
// → FirebaseError: Missing or insufficient permissions.
```

---

## 4. 롤백 절차 (문제 발생 시)

### 4-1. Rules 이전 버전 재배포
```bash
git checkout HEAD~1 -- firestore.rules
firebase deploy --only firestore:rules --project mini12-310f5
git restore --staged firestore.rules
git checkout HEAD -- firestore.rules
```

### 4-2. Console 에서 롤백 (수동)
1. https://console.firebase.google.com/project/mini12-310f5/firestore/rules
2. **이력** 탭 → 이전 버전 선택 → **재배포**

> 인덱스는 삭제만 가능 (롤백 불가). 신규 인덱스가 문제일 일은 거의 없음 (read 만 영향).

---

## 5. 자주 발생하는 이슈

### 5-1. `Missing or insufficient permissions` (정상 사용자)
**원인**: ID token 갱신 안됨 → custom claim 반영 안됨.
**해결**:
```javascript
await user.getIdToken(true); // force refresh
```
또는 로그아웃/재로그인 안내.

### 5-2. `requires an index`
**원인**: 신규 query 인데 인덱스 없음.
**해결**: 에러 메시지의 링크 클릭 → "Create index" → 5분 대기.
또는 `firestore.indexes.json` 에 추가 후 `firebase deploy --only firestore:indexes`.

### 5-3. Rules 에서 `request.resource.data.field` undefined 에러
**원인**: 신규 도큐먼트에 해당 필드 없음.
**해결**: rules 에 `is string` / `in [...]` 같은 type guard 추가.

---

## 6. 현재 적용된 인덱스 6개

| Collection | 필드 | 용도 |
|---|---|---|
| users | role ASC + createdAt DESC | admin 페이지 회원 목록 (권한별) |
| users | status ASC + lastSignInAt DESC | 활성/비활성 사용자 + 최근 접속순 |
| users | favoriteTeam ASC + createdAt DESC | 응원팀별 회원 분포 |
| sessions (subcoll) | pinned DESC + updatedAt DESC | AI 챗 세션 목록 (고정 + 최근순) |
| items (subcoll) | public ASC + updatedAt DESC | 공개 코스 모음 |
| admin_audit | action ASC + createdAt DESC | 액션별 audit log 검색 |

---

## 7. 다음 단계 — Step 8 (이미 완료) → Step 9 (Admin UI)

- ✅ Step 8 (apphosting.yaml 시크릿 활성화) — 이미 PR #1 에 포함됨
- ⏭ Step 9 — `app/admin/layout.tsx` + AdminShell + SideNav (디자인: `uiux/web_uiux/admin_dashboard/`)

---

*작성: 2026-04-18 Session B Step 7*
