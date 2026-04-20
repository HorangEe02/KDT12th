# 🔥 Firebase DB 상세 구현 계획 — 인증·권한·사용자 데이터 영속화

> 작성: 2026-04-18 · 부모 문서: `docs/NEXT_SESSION_PLAN.md` (Feature 1·2·3)
> 범위: Firebase Auth + Firestore + Admin SDK + Storage 통합 설계
> 전제: Firebase 프로젝트 `mini12-310f5` 기존 활용, Web SDK v12 + Admin SDK 이미 설치

---

## 0. 한눈에 — 결정 요약

| 영역 | 결정 | 근거 |
|---|---|---|
| 인증 | **Firebase Authentication** (Email + Google + Kakao OIDC) | 기존 프로젝트, 무료 50K MAU, Admin SDK 통합 |
| 데이터베이스 | **Firestore Native Mode** | 실시간 onSnapshot · 보안 규칙 · 오프라인 지원 |
| 권한 | **Custom Claims (보안) + `users/{uid}.role` (UI)** 이중 | JWT 검증 + 목록 조회 양립 |
| 세션 | **Session Cookie (HttpOnly, 5d)** | SSR 시 RSC 에서 직접 검증 가능 |
| 서버 인증 | **Firebase Admin SDK** + Application Default Credentials (App Hosting) | Cloud Run 자동 주입 |
| 클라이언트 상태 | **Zustand + onAuthStateChanged** | 기존 store 패턴 일관성 |
| 데이터 동기화 | **로그인 시 pull → merge → write back** + 부분 onSnapshot | 비용/UX 균형 |
| 보안 | **Firestore Rules 재작성** + **App Check** (배포 후) | 봇/남용 차단 |

---

## 1. Firebase 서비스 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                 Next.js 16 (Cloud Run · App Hosting)         │
│                                                              │
│  ┌─────────────────┐         ┌─────────────────────────┐   │
│  │ Server (RSC/API)│         │ Client (use client)      │   │
│  │                 │         │                          │   │
│  │ admin SDK       │         │ Web SDK v12              │   │
│  │ - verify cookie │         │ - signIn / signUp        │   │
│  │ - admin queries │         │ - onAuthStateChanged     │   │
│  │ - service tasks │         │ - Firestore client SDK   │   │
│  └────────┬────────┘         │ - onSnapshot (limited)   │   │
│           │                  └──────────┬───────────────┘   │
│           │                             │                    │
│           │  ApplicationDefaultCreds    │ apiKey (public)    │
│           ▼                             ▼                    │
└───────────┼─────────────────────────────┼────────────────────┘
            │                             │
            ▼                             ▼
┌──────────────────────────────────────────────────────────────┐
│              Firebase / Google Cloud (mini12-310f5)           │
│                                                                │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ Authentication │  │  Firestore   │  │  Cloud Storage  │  │
│  │ • Email/PW     │  │  (Native)    │  │  • RAG snapshot │  │
│  │ • Google OIDC  │  │              │  │  • user uploads │  │
│  │ • Kakao OIDC   │  │ 6 컬렉션     │  │    (선택)       │  │
│  │ • Custom claim │  │ + 서브컬렉션 │  │                 │  │
│  └────────────────┘  └──────────────┘  └─────────────────┘  │
│                                                                │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ Secret Manager │  │  App Check   │  │  Cloud Logging  │  │
│  │ 9 secrets      │  │  (reCAPTCHA) │  │  audit / errors │  │
│  └────────────────┘  └──────────────┘  └─────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. 인증 (Authentication)

### 2-1. 활성화할 Provider

| Provider | 우선순위 | 사전 액션 | 비용 |
|---|---|---|---|
| **Email/Password** | P0 | Console 에서 사용 설정 1클릭 | 무료 |
| **Google OIDC** | P0 | OAuth 동의 화면 + 지원 이메일 등록 | 무료 |
| **Kakao OIDC** | P1 | Kakao Developers 앱 + Custom OIDC 등록 + Identity Platform 업그레이드 필요 | Identity Platform 종량제 (50K MAU 무료) |

> **MVP**: Email + Google 만으로 출발. Kakao 는 Identity Platform 업그레이드 후 P1 으로.

### 2-2. 회원가입 정책

```typescript
// 비밀번호 정책 (Firebase 기본 + 추가)
{
  minLength: 8,
  requireUppercase: false,        // 한국 사용자 편의
  requireLowercase: true,
  requireNumber: true,
  requireSpecialChar: false,
  blockCommonPasswords: true,     // Firebase Auth 옵션
}

// displayName: 필수 입력 (사이드바/admin 표시용)
// photoURL: Google 로그인 시 자동, Email 가입 시 null
// emailVerified: 발송하지만 강제 차단은 안 함 (UX 우선)
```

### 2-3. Session Cookie 전략 (SSR 핵심)

기존 OMC 프로젝트는 클라이언트 SDK 만 썼으나, 이번엔 **App Router RSC** 에서 인증 상태를 서버에서 알아야 하므로 **session cookie** 도입:

```typescript
// app/api/auth/session/route.ts (POST)
export async function POST(req: Request) {
  const { idToken } = await req.json();
  const expiresIn = 60 * 60 * 24 * 5 * 1000; // 5일
  const sessionCookie = await getAdminAuth().createSessionCookie(idToken, { expiresIn });
  cookies().set("__session", sessionCookie, {
    httpOnly: true,
    secure: true,
    sameSite: "lax",
    maxAge: expiresIn / 1000,
    path: "/",
  });
  return Response.json({ ok: true });
}

// app/api/auth/session/route.ts (DELETE) → 로그아웃
// lib/firebase/server-session.ts → verifySessionCookie(checkRevoked: true)
```

**왜 `__session` 이름?** Firebase App Hosting (Cloud Run) 은 `__session` 쿠키만 캐시 키에서 제외시키도록 사전 설정돼 있음. 다른 이름이면 stale cache 위험.

### 2-4. 인증 플로우 다이어그램

```
[Sign Up] ──────────────────────────────────────────────────────┐
  ↓                                                              │
  createUserWithEmailAndPassword(email, pw)                      │
  ↓                                                              │
  updateProfile({ displayName })                                 │
  ↓                                                              │
  user.getIdToken() → POST /api/auth/session                    │
  ↓                                              ↓               │
  서버: createSessionCookie + verifyIdToken                      │
  ↓                                              ↓               │
  서버: Firestore users/{uid} 도큐먼트 생성                      │
  ↓                                              ↓               │
  클라: setAuthState({ user, profile })                         │
  ↓                                                              │
  router.push(searchParams.next ?? "/")                         │
                                                                 │
[Sign In] ──────────────────────────────────────────────────────┤
  ↓                                                              │
  signInWithEmailAndPassword 또는 signInWithPopup(Google)        │
  ↓                                                              │
  user.getIdToken(true) → POST /api/auth/session                │
  ↓                                                              │
  서버: users/{uid}.lastSignInAt = serverTimestamp()             │
  ↓                                                              │
  클라: syncOnSignIn(uid) → prefs/visits pull · merge · push    │
  ↓                                                              │
  router.push(next || "/")                                      │
                                                                 │
[onAuthStateChanged] ───────────────────────────────────────────┤
  • App 시작 시 listener 등록                                    │
  • token refresh (1h) 자동                                      │
  • Custom claim 변경 시: user.getIdToken(true) 강제 갱신        │
                                                                 │
[Sign Out] ─────────────────────────────────────────────────────┘
  ↓
  signOut(getAuth()) + DELETE /api/auth/session
  ↓
  Zustand reset(), localStorage 유지(빠른 재로그인)
  ↓
  router.push("/login")
```

### 2-5. 보안 강화

| 위협 | 완화 |
|---|---|
| 봇 회원가입 | **App Check (reCAPTCHA v3)** — 배포 후 단계적 enforcement |
| 무차별 로그인 | Firebase 자동 rate limit + email 알림 |
| 세션 탈취 | HttpOnly + Secure + SameSite=Lax · `checkRevoked:true` |
| 비밀번호 평문 노출 | HTTPS 강제 (App Hosting 기본) |
| ID token 위조 | 서버 측 항상 verifyIdToken / verifySessionCookie |
| Custom claim 즉시 무효화 | `revokeRefreshTokens(uid)` + 다음 verify 시 거부 |

---

## 3. Firestore 데이터 모델 (스키마 V2)

### 3-1. 컬렉션 트리 (전체)

```
firestore/
│
├── users/{uid}                              ★ 사용자 프로필
│   ├── email: string
│   ├── displayName: string
│   ├── photoURL: string|null
│   ├── role: "user" | "admin"
│   ├── status: "active" | "disabled"
│   ├── favoriteTeam: string|null            (예: "LG")
│   ├── createdAt: Timestamp
│   ├── lastSignInAt: Timestamp
│   ├── lastActiveAt: Timestamp              (페이지 방문 시 갱신)
│   ├── stats: {                             (admin 통계용 비정규화)
│   │     visitedCount: number,
│   │     planCount: number,
│   │     chatSessionCount: number,
│   │     lastPlanAt: Timestamp|null,
│   │   }
│   └── consent: {                           (개인정보 동의 이력)
│         tos: boolean, tosVersion: string, tosAt: Timestamp,
│         privacy: boolean, privacyAt: Timestamp,
│         marketing: boolean,
│       }
│
├── user_visits/{uid}                        ★ 뱃지 (방문 구장)
│   ├── visited: string[]                    (["잠실","수원",...])
│   ├── updatedAt: Timestamp
│   └── perStadium: {                        (방문 횟수)
│         "잠실": { firstAt: Ts, lastAt: Ts, count: 3 },
│         ...
│       }
│
├── user_prefs/{uid}                         ★ 사이드바 필터
│   ├── team: string|null
│   ├── startDate: string                    ("2026-04-01")
│   ├── endDate: string
│   ├── budgetMax: number                    (KRW)
│   ├── partySize: number                    (1~6)
│   ├── transport: "car" | "transit"
│   ├── demoMode: boolean
│   └── updatedAt: Timestamp
│
├── user_chats/{uid}/sessions/{sessionId}    ★ AI 챗 히스토리
│   ├── title: string                        (첫 메시지 30자 요약)
│   ├── createdAt: Timestamp
│   ├── updatedAt: Timestamp
│   ├── messageCount: number
│   ├── pinned: boolean
│   └── messages/{messageId}                 (서브 컬렉션)
│       ├── role: "user" | "assistant" | "tool"
│       ├── content: string
│       ├── parts: any[]                     (Vercel AI SDK message.parts)
│       ├── createdAt: Timestamp
│       └── toolName: string|null
│
├── user_plans/{uid}/items/{planId}          ★ 사용자 코스 (개인 보관)
│   ├── name: string                         ("LG 첫 원정 2박3일")
│   ├── filters: {team,start,end,budget,party,transport}
│   ├── gameId: string
│   ├── stadium: string
│   ├── route: object|null
│   ├── pois: { food[], stay[], tour[] }
│   ├── weather: object|null
│   ├── aiSummary: string|null
│   ├── winProb: number|null
│   ├── createdAt: Timestamp
│   ├── updatedAt: Timestamp
│   ├── public: boolean                      (공유 여부)
│   ├── sharedPlanId: string|null            (shared_plans 참조)
│   └── exports: { csv?: count, pdf?: count, docx?: count, pptx?: count }
│
├── shared_plans/{planId}                    ★ 공개 공유 (변경: ownerUid 추가)
│   ├── ownerUid: string|null
│   ├── ownerDisplayName: string|null
│   ├── data: object                         (Plan 스냅샷)
│   ├── createdAt: Timestamp
│   ├── viewCount: number                    (조회수, server-only 증가)
│   └── expiresAt: Timestamp|null            (선택 — 30일)
│
├── admin_audit/{eventId}                    ★ 관리자 액션 감사 로그
│   ├── adminUid: string
│   ├── adminEmail: string
│   ├── action: "grant_admin"|"revoke_admin"|"disable"|"enable"|"delete_user"
│   ├── targetUid: string
│   ├── targetEmail: string
│   ├── reason: string
│   ├── createdAt: Timestamp
│   └── ip: string|null
│
├── system_metrics/{day}                     ★ 일일 집계 (Cloud Function)
│   ├── date: "2026-04-18"
│   ├── totalUsers: number
│   ├── newUsers: number
│   ├── activeUsers: number
│   ├── totalPlans: number
│   ├── newPlans: number
│   ├── chatSessions: number
│   └── byTeam: { LG: 23, KT: 14, ... }      (응원팀 분포)
│
└── feedback/{feedbackId}                    ★ (선택) 사용자 피드백
    ├── uid: string|null                     (비로그인 OK)
    ├── type: "bug"|"feature"|"general"
    ├── content: string
    ├── url: string                          (제출 시 페이지)
    └── createdAt: Timestamp
```

### 3-2. 비정규화 결정

| 필드 | 위치 | 이유 |
|---|---|---|
| `users.stats.visitedCount` | users 안 | admin 목록 정렬에 즉시 사용 (count() 쿼리 비용↓) |
| `users.favoriteTeam` | users 안 (prefs 와 중복) | admin 통계 + 인덱스 가능 |
| `shared_plans.ownerDisplayName` | 스냅샷 | owner 닉네임 변경되어도 공유 페이지엔 당시 이름 유지 |
| `user_plans.exports.{format}` | 카운터 | 인기 export 포맷 분석 |

**원칙**: 자주 읽고 가끔 쓰는 데이터는 **부모 도큐먼트로 비정규화**, 일관성은 Cloud Function trigger 로 유지.

### 3-3. 인덱스 (firestore.indexes.json)

```json
{
  "indexes": [
    {
      "collectionGroup": "users",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "role", "order": "ASCENDING" },
        { "fieldPath": "createdAt", "order": "DESCENDING" }
      ]
    },
    {
      "collectionGroup": "users",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "status", "order": "ASCENDING" },
        { "fieldPath": "lastSignInAt", "order": "DESCENDING" }
      ]
    },
    {
      "collectionGroup": "users",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "favoriteTeam", "order": "ASCENDING" },
        { "fieldPath": "createdAt", "order": "DESCENDING" }
      ]
    },
    {
      "collectionGroup": "sessions",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "pinned", "order": "DESCENDING" },
        { "fieldPath": "updatedAt", "order": "DESCENDING" }
      ]
    },
    {
      "collectionGroup": "items",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "public", "order": "ASCENDING" },
        { "fieldPath": "updatedAt", "order": "DESCENDING" }
      ]
    },
    {
      "collectionGroup": "admin_audit",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "action", "order": "ASCENDING" },
        { "fieldPath": "createdAt", "order": "DESCENDING" }
      ]
    }
  ]
}
```

### 3-4. Firestore Security Rules (전면 재작성)

```javascript
rules_version = '2';

service cloud.firestore {
  match /databases/{database}/documents {

    // ===== Helpers =====
    function isSignedIn() { return request.auth != null; }
    function isOwner(uid) { return isSignedIn() && request.auth.uid == uid; }
    function isAdmin() { return isSignedIn() && request.auth.token.admin == true; }
    function isActive() {
      return isSignedIn() && (request.auth.token.disabled != true);
    }
    function validProfileData() {
      let d = request.resource.data;
      return d.email is string && d.email.size() <= 254
          && d.displayName is string && d.displayName.size() <= 50
          && d.role in ["user", "admin"]
          && d.status in ["active", "disabled"];
    }

    // ===== Users =====
    match /users/{uid} {
      allow get:    if isOwner(uid) || isAdmin();
      allow list:   if isAdmin();
      allow create: if isOwner(uid) && validProfileData()
                       && request.resource.data.role == "user"
                       && request.resource.data.status == "active";
      // 일반 사용자: role/status 변경 금지, 자기 프로필 일부만 수정
      allow update: if (isOwner(uid)
                        && request.resource.data.role == resource.data.role
                        && request.resource.data.status == resource.data.status
                        && request.resource.data.email == resource.data.email
                        && request.resource.data.createdAt == resource.data.createdAt)
                    || isAdmin();
      allow delete: if isAdmin();
    }

    // ===== User Visits / Prefs =====
    match /user_visits/{uid} {
      allow read:  if isOwner(uid) || isAdmin();
      allow write: if isOwner(uid) && isActive();
    }
    match /user_prefs/{uid} {
      allow read:  if isOwner(uid);
      allow write: if isOwner(uid) && isActive();
    }

    // ===== User Chats =====
    match /user_chats/{uid}/sessions/{sessionId} {
      allow read, write: if isOwner(uid) && isActive();
      match /messages/{messageId} {
        allow read, write: if isOwner(uid) && isActive();
      }
    }

    // ===== User Plans =====
    match /user_plans/{uid}/items/{planId} {
      allow read:  if isOwner(uid)
                   || (resource.data.public == true)
                   || isAdmin();
      allow create, update: if isOwner(uid) && isActive()
                              && request.resource.data.exports.size() <= 10;
      allow delete: if isOwner(uid) || isAdmin();
    }

    // ===== Shared Plans (공개 read) =====
    match /shared_plans/{planId} {
      allow read:   if true;
      allow create: if isSignedIn() && isActive()
                       && request.resource.data.ownerUid == request.auth.uid;
      allow update: if false;   // 서버 only (viewCount 증가)
      allow delete: if isAdmin() || (isSignedIn()
                       && resource.data.ownerUid == request.auth.uid);
    }

    // ===== Admin Audit =====
    match /admin_audit/{eventId} {
      allow read:   if isAdmin();
      allow write:  if false;   // 서버 only (Admin SDK)
    }

    // ===== System Metrics =====
    match /system_metrics/{day} {
      allow read:   if isAdmin();
      allow write:  if false;   // 서버 only (Cloud Function)
    }

    // ===== Feedback =====
    match /feedback/{feedbackId} {
      allow create: if request.resource.data.content is string
                       && request.resource.data.content.size() < 2000;
      allow read:   if isAdmin();
      allow update, delete: if false;
    }

    // ===== Default deny =====
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```

> **테스트**: `firestore-emulator` 의 rules unit test 로 8 개 시나리오 (owner GET, other GET, admin LIST, anon CREATE, role escalation, expired session, etc.) 검증.

---

## 4. Custom Claims (관리자 권한)

### 4-1. 설계

```typescript
// JWT 에 들어가는 claim
interface UserClaims {
  admin?: true;          // 관리자 여부
  disabled?: true;       // 계정 비활성화
  role?: "admin"|"user"; // (UI hint, 실제 검증은 admin 사용)
}
```

### 4-2. 부여 흐름

```typescript
// scripts/grant-admin.mjs (CLI)
import admin from "firebase-admin";
admin.initializeApp({ credential: admin.credential.applicationDefault() });

const targetEmail = process.argv[2];
const user = await admin.auth().getUserByEmail(targetEmail);
await admin.auth().setCustomUserClaims(user.uid, { admin: true, role: "admin" });
await admin.firestore().doc(`users/${user.uid}`).update({
  role: "admin",
  updatedAt: admin.firestore.FieldValue.serverTimestamp(),
});
await admin.firestore().collection("admin_audit").add({
  adminUid: "system",
  adminEmail: "system",
  action: "grant_admin",
  targetUid: user.uid,
  targetEmail: user.email,
  reason: "initial bootstrap CLI",
  createdAt: admin.firestore.FieldValue.serverTimestamp(),
});
console.log(`✅ ${targetEmail} → admin`);

// 사용:
// gcloud auth application-default login
// node scripts/grant-admin.mjs catlife9029@gmail.com
```

### 4-3. 즉시 반영 패턴

Custom claim 은 다음 토큰 갱신 (1시간 후) 까지 미반영 → **즉시 반영을 위해**:

```typescript
// 부여 직후 (서버)
await getAdminAuth().revokeRefreshTokens(targetUid);

// 클라이언트 (관리자 페이지)
await user.getIdToken(true); // force refresh
// 그래도 미반영이면 signOut → signIn 안내
```

### 4-4. 관리자 API

| 엔드포인트 | 메서드 | 권한 | 동작 |
|---|---|---|---|
| `/api/admin/users` | GET | admin | 페이지네이션 사용자 목록 (cursor + 25/page) |
| `/api/admin/users/[uid]` | GET | admin | 단일 사용자 + 통계 (visits, plans count) |
| `/api/admin/users/[uid]/role` | PATCH | admin | role 변경 + claim 변경 + audit 기록 |
| `/api/admin/users/[uid]/status` | PATCH | admin | active/disabled 토글 + Auth 비활성화 |
| `/api/admin/users/[uid]` | DELETE | admin | 계정 삭제 + 데이터 cascade (Cloud Function) |
| `/api/admin/metrics` | GET | admin | 대시보드 KPI (Total/Active/MRR/Trips) |
| `/api/admin/audit` | GET | admin | audit log 페이지네이션 |

모든 핸들러:
```typescript
import { requireAdmin } from "@/lib/firebase/server-session";
export async function PATCH(req: NextRequest, { params }) {
  const { uid: adminUid, email: adminEmail } = await requireAdmin();
  // ... 작업 수행
  await logAuditEvent({ adminUid, adminEmail, action, targetUid, targetEmail, reason });
}
```

---

## 5. 데이터 동기화 (Local ↔ Cloud)

### 5-1. 마이그레이션 (anon → 로그인)

기존 익명 사용자가 localStorage 에 가진 데이터:
- `useFilters` (Zustand persist) — 필터 5종
- `useBadges` (Zustand persist) — visited[] + anonId
- `useChat` 등은 메모리 only

**로그인 시 첫 1회 마이그레이션**:

```typescript
// lib/firebase/sync-on-signin.ts
export async function syncOnSignIn(uid: string) {
  const localPrefs = useFilters.getState();
  const localVisited = useBadges.getState().visited;
  const [remotePrefs, remoteVisits] = await Promise.all([
    getDoc(doc(db, "user_prefs", uid)),
    getDoc(doc(db, "user_visits", uid)),
  ]);

  // === Prefs 머지 (last-writer-wins by updatedAt) ===
  const mergedPrefs = chooseFresher(localPrefs, remotePrefs.data());
  useFilters.setState(mergedPrefs);
  await setDoc(doc(db, "user_prefs", uid), {
    ...mergedPrefs,
    updatedAt: serverTimestamp(),
  });

  // === Visits 머지 (set union — 보수적) ===
  const remoteSet = new Set<string>(remoteVisits.data()?.visited ?? []);
  const localSet = new Set<string>(localVisited);
  const merged = [...new Set([...remoteSet, ...localSet])];
  useBadges.setState({ visited: merged });
  await setDoc(
    doc(db, "user_visits", uid),
    { visited: merged, updatedAt: serverTimestamp() },
    { merge: true }
  );

  // === stats 갱신 (users 도큐먼트 비정규화 카운터) ===
  await updateDoc(doc(db, "users", uid), {
    "stats.visitedCount": merged.length,
    lastActiveAt: serverTimestamp(),
  });
}

function chooseFresher<T extends { updatedAt?: any }>(local: T, remote?: T): T {
  if (!remote) return local;
  const lt = local.updatedAt instanceof Date ? local.updatedAt.getTime() : 0;
  const rt = remote.updatedAt?.toMillis?.() ?? 0;
  return rt > lt ? remote : local;
}
```

### 5-2. 실시간 구독 정책 (비용 관리)

| 경로 | onSnapshot? | 이유 |
|---|---|---|
| `user_prefs/{uid}` | ❌ getDoc 만 | 본인 단일 클라이언트 변경 → 실시간 불필요 |
| `user_visits/{uid}` | ⚠️ 페이지 마운트 시 1회 + 쓰기 시 낙관적 업데이트 | |
| `user_plans/{uid}/items` | ✅ /badges 페이지 한정 | 다른 디바이스 동기화 UX 가치 |
| `user_chats/{uid}/sessions` | ⚠️ /ai 페이지에서 limit(20) | 비용 통제 |
| `users` (admin 목록) | ❌ 페이지네이션 + refresh | 50K 도큐먼트 onSnapshot = 폭탄 |

### 5-3. 쓰기 패턴

| 시나리오 | 패턴 | 비고 |
|---|---|---|
| 사이드바 필터 변경 | Zustand → debounce 1.5초 → setDoc(merge:true) | 과도 쓰기 방지 |
| 뱃지 토글 | 즉시 setDoc + Zustand 동시 | 원자적 |
| 코스 저장 (My Plans) | addDoc → addDoc 결과 ID 로 navigate | UX 즉시 |
| 공유 링크 생성 | server addDoc(shared_plans) + user_plans 업데이트 | 트랜잭션 |
| AI 챗 메시지 | 메시지 finish 후 batch.write (sessions doc + messages 서브) | 토큰 낭비 방지 |

### 5-4. 충돌 해결

다중 디바이스 시나리오:
```
디바이스 A (오프라인) → 필터 X 변경
디바이스 B (온라인)   → 필터 Y 변경 → Firestore 쓰기 성공
디바이스 A 온라인 복귀 → 무엇이 우선?
```

**전략**: `updatedAt` 기준 last-writer-wins. 충돌 빈도 낮고 (혼자 사용), 잃는 데이터가 사이드바 필터 정도 → 충분.

복잡한 데이터 (코스 편집) 는 **Firestore Transaction** 으로 read-modify-write 보장.

---

## 6. 파일 트리 (`frontend/`)

```
frontend/
├── lib/firebase/
│   ├── client.ts                  (기존, getAuth 추가)
│   ├── auth.ts                    🆕 signUp/signIn/signOut/sendPwReset
│   ├── admin.ts                   (기존)
│   ├── server-session.ts          🆕 createSessionCookie/verifyAndGetUser/requireAdmin
│   ├── sync-on-signin.ts          🆕 마이그레이션 + 머지
│   ├── user-prefs.ts              🆕 user_prefs CRUD
│   ├── user-visits.ts             🆕 user_visits CRUD (기존 visited.ts 확장)
│   ├── user-plans.ts              🆕 user_plans CRUD + share
│   ├── user-chats.ts              🆕 user_chats CRUD + 페이지네이션
│   ├── shared-plans.ts            (기존, ownerUid 추가)
│   ├── admin-users.ts             🆕 list/get/patch role/disable/delete
│   ├── admin-metrics.ts           🆕 KPI 집계
│   ├── admin-audit.ts             🆕 audit log writer/reader
│   └── app-check.ts               🆕 (배포 후 활성화)
│
├── lib/store/
│   ├── auth.ts                    🆕 Zustand: user/profile/loading/error
│   ├── filters.ts                 (기존 + Firestore sync 훅 추가)
│   └── badges.ts                  (기존 + Firestore sync 훅 추가)
│
├── lib/types/
│   └── user.ts                    🆕 UserProfile/UserClaims/AdminAction
│
├── app/
│   ├── login/page.tsx             🆕
│   ├── signup/page.tsx            🆕
│   ├── reset-password/page.tsx    🆕
│   ├── (shell)/
│   │   ├── account/page.tsx       🆕 본인 프로필 + 데이터 다운로드/삭제
│   │   └── ...
│   ├── admin/
│   │   ├── layout.tsx             🆕 admin claim 검증
│   │   ├── page.tsx               🆕 대시보드
│   │   ├── users/page.tsx         🆕 목록 + 검색 + 페이지네이션
│   │   ├── users/[uid]/page.tsx   🆕 상세 + 액션
│   │   ├── audit/page.tsx         🆕
│   │   └── metrics/page.tsx       🆕 (선택)
│   └── api/
│       ├── auth/session/route.ts  🆕 POST/DELETE 세션 쿠키
│       └── admin/
│           ├── users/route.ts                 🆕 GET list
│           ├── users/[uid]/route.ts           🆕 GET/DELETE
│           ├── users/[uid]/role/route.ts      🆕 PATCH
│           ├── users/[uid]/status/route.ts    🆕 PATCH
│           ├── metrics/route.ts               🆕
│           └── audit/route.ts                 🆕
│
├── components/auth/
│   ├── auth-provider.tsx          🆕 onAuthStateChanged context
│   ├── user-badge.tsx             🆕 사이드바 우상단
│   ├── protected-route.tsx        🆕 client-side guard (보조)
│   └── consent-modal.tsx          🆕 약관 동의 (선택)
│
└── components/admin/
    ├── user-table.tsx
    ├── user-row-actions.tsx
    ├── role-badge.tsx
    ├── audit-table.tsx
    └── metric-card.tsx
```

> Login/Signup/Admin 의 **세부 컴포넌트 + 디자인 매핑**은 동행 문서 [`docs/AUTH_ADMIN_UI_PLAN.md`](AUTH_ADMIN_UI_PLAN.md) 참조.

---

## 7. 환경 변수 + Secret Manager

### 7-1. 클라이언트 (NEXT_PUBLIC_*)

| 변수 | 값 출처 | 비고 |
|---|---|---|
| `NEXT_PUBLIC_FIREBASE_API_KEY` | Firebase Console → 웹앱 config | secret 등록 |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | `mini12-310f5.firebaseapp.com` | yaml hardcode |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | `mini12-310f5` | yaml hardcode |
| `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET` | `mini12-310f5.appspot.com` | yaml hardcode |
| `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID` | Console | secret |
| `NEXT_PUBLIC_FIREBASE_APP_ID` | Console | secret |
| `NEXT_PUBLIC_RECAPTCHA_SITE_KEY` | App Check 활성화 후 | secret (배포 단계 P1) |

### 7-2. 서버

| 변수 | 값 | 비고 |
|---|---|---|
| `FIREBASE_PROJECT_ID` | `mini12-310f5` | yaml hardcode |
| `GOOGLE_APPLICATION_CREDENTIALS` | (Cloud Run 자동) | App Hosting 자동 주입 |
| `SESSION_COOKIE_NAME` | `__session` | 캐시 무시 위해 고정 |
| `SESSION_COOKIE_DAYS` | `5` | 5일 |

> 로컬 개발: `secrets/service-account.json` 사용 (`.gitignore` 체크 필수). `admin.ts` 가 자동 감지.

### 7-3. apphosting.yaml 추가 블록

```yaml
# === 인증 활성화 (세션 B 진입 시 추가) ===
- variable: NEXT_PUBLIC_FIREBASE_API_KEY
  secret: NEXT_PUBLIC_FIREBASE_API_KEY
  availability: [BUILD, RUNTIME]
- variable: NEXT_PUBLIC_FIREBASE_APP_ID
  secret: NEXT_PUBLIC_FIREBASE_APP_ID
  availability: [BUILD, RUNTIME]
- variable: NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID
  secret: NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID
  availability: [BUILD, RUNTIME]
- variable: SESSION_COOKIE_NAME
  value: __session
  availability: [RUNTIME]
- variable: SESSION_COOKIE_DAYS
  value: "5"
  availability: [RUNTIME]
```

---

## 8. 에뮬레이터 (개발/테스트)

### 8-1. firebase.json 확장

```json
{
  "emulators": {
    "auth":      { "port": 9099 },
    "firestore": { "port": 8080 },
    "storage":   { "port": 9199 },
    "ui":        { "enabled": true, "port": 4000 }
  }
}
```

### 8-2. 로컬 환경 분기

```typescript
// lib/firebase/client.ts (추가)
if (process.env.NEXT_PUBLIC_USE_FIREBASE_EMULATOR === "1") {
  connectAuthEmulator(getAuth(app), "http://localhost:9099");
  connectFirestoreEmulator(getFirestore(app), "localhost", 8080);
}
```

### 8-3. Rules 단위 테스트

```bash
# scripts/test-rules.sh
firebase emulators:exec \
  "npx vitest run tests/firestore-rules.test.ts" \
  --only firestore --project mini12-310f5
```

---

## 9. 배포 + 마이그레이션 절차

### 9-1. 사용자 사전 액션 (세션 B 진입 전)

- [ ] Firebase Console → Authentication → 시작하기
- [ ] **이메일/비밀번호** 활성화
- [ ] **Google** 활성화 + 프로젝트 지원 이메일 선택
- [ ] (선택) **Identity Platform 업그레이드** (Kakao OIDC 필요 시)
- [ ] 프로젝트 설정 → 일반 → 웹앱 SDK config 복사
- [ ] Secret Manager 등록 3종:
  ```bash
  firebase apphosting:secrets:set NEXT_PUBLIC_FIREBASE_API_KEY --project mini12-310f5
  firebase apphosting:secrets:set NEXT_PUBLIC_FIREBASE_APP_ID --project mini12-310f5
  firebase apphosting:secrets:set NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID --project mini12-310f5
  ```
- [ ] `apphosting.yaml` 의 신규 블록 주석 해제
- [ ] 초기 admin 이메일 결정 (예: `catlife9029@gmail.com`)
- [ ] (선택) `secrets/service-account.json` 다운로드 (로컬 admin SDK 테스트)

### 9-2. 코드 머지 + 배포 순서

1. **PR #1** — 인증 기반 (Auth + Session Cookie + users 컬렉션 + 로그인/회원가입 페이지)
2. **PR #2** — 사용자 데이터 영속화 (sync-on-signin + visits/prefs 마이그레이션 + Firestore Rules)
3. **PR #3** — 관리자 (admin layout + users page + role/status API + audit + grant-admin CLI)
4. **PR #4** — App Check 활성화 (배포 후 안정화 후)

각 PR 후:
```bash
firebase deploy --only firestore --project mini12-310f5  # rules + indexes
firebase deploy --only apphosting --project mini12-310f5 # 코드
```

### 9-3. 데이터 마이그레이션 스크립트

기존 anon 사용자가 share 링크로 만든 `shared_plans` → `ownerUid: null` 로 보존 (소급 적용 X). 신규 가입자만 ownerUid 부여.

```javascript
// scripts/backfill-anon-shared-plans.mjs (선택)
// 기존 shared_plans 에 ownerUid 필드 없으면 null 명시 추가
// ⚠️ 50K 도큐먼트 이상 시 batched 500/회
```

### 9-4. 롤백 전략

| 상황 | 롤백 |
|---|---|
| Rules 배포 후 정상 사용자 차단 | `firebase deploy --only firestore:rules` 이전 버전 재배포 |
| 인증 페이지 배포 후 무한 루프 | 이전 build 의 App Hosting rollback (Console UI 1클릭) |
| Custom claim 실수 부여 | `node scripts/grant-admin.mjs --revoke email@x.com` |

---

## 10. 비용 + 성능 추정

### 10-1. Firebase 가격 (Spark 무료)

| 리소스 | 무료 한도 | MVP 추정 (월 100 활성유저) |
|---|---|---|
| Auth MAU | 50K | 0.2% |
| Firestore 읽기 | 50K/일 | ~10K/일 (10%) |
| Firestore 쓰기 | 20K/일 | ~3K/일 (15%) |
| Firestore 저장 | 1 GiB | ~50 MiB (5%) |
| Storage | 5 GB | ~100 MB |
| Cloud Functions | (Blaze 필요) | 미사용 (선택) |

> 무료 tier 충분. **유료 전환 트리거**: Identity Platform (Kakao OIDC) 또는 Cloud Functions 도입 시.

### 10-2. 읽기 비용 핫스팟

| 경로 | 빈도 | 최적화 |
|---|---|---|
| `users` 페이지 (admin) | 25 reads/페이지 | cursor + 25 limit |
| `user_chats` (페이지 마운트) | 20 sessions × 메시지 | session list 만 + 클릭 시 messages |
| onSnapshot 한 번에 | 첫 read = 컬렉션 크기 | `limit(20)` + `where("pinned","==",true)` 정렬 |

### 10-3. 응답 시간

| 동작 | 목표 | 비고 |
|---|---|---|
| 로그인 (popup → 세션 쿠키) | < 1.5s | RTT + token round trip |
| RSC 페이지 (인증 검증) | < 200ms | verifySessionCookie 캐시 X — 매 요청 |
| Firestore 단일 read | < 100ms | 같은 region (asia-northeast3) |
| Admin 사용자 목록 | < 800ms | 25 docs + composite index |

> **주의**: `verifySessionCookie(checkRevoked: true)` 는 매번 Firebase Auth 호출 → ~80ms. 필요한 페이지만 (admin/account) 적용, 일반 페이지는 `checkRevoked: false`.

---

## 11. 리스크 + 완화

| 리스크 | 확률 | 영향 | 완화 |
|---|---|---|---|
| Firestore Rules 버그로 데이터 노출 | 중 | 치명 | rules unit test 8 시나리오 의무화 + emulator CI |
| Custom claim 즉시 반영 안됨 | 중 | 중 | `revokeRefreshTokens` + `getIdToken(true)` + UX 안내 |
| App Hosting `__session` 캐시 충돌 | 낮 | 중 | 쿠키 이름 `__session` 강제 사용 |
| anon 사용자 마이그레이션 충돌 | 중 | 중 | last-writer-wins + 알림 |
| Identity Platform 비활성화 시 Kakao OIDC 실패 | 중 (P1) | 낮 | MVP 는 Email + Google 만 |
| Cloud Run cold start (admin SDK 초기화) | 중 | 낮 | minInstances=0 유지 (비용↑ 회피) + 첫 요청 ~1초 허용 |
| firebase-admin EOL Node 버전 | 낮 | 낮 | `engines.node` `>=20` 명시 |
| 에뮬레이터-프로덕션 차이 (timestamp) | 낮 | 낮 | serverTimestamp() 쓰기 시 `merge:true` 패턴 통일 |

---

## 12. 검증 체크리스트

### 12-1. PR #1 (Auth) 머지 전

- [ ] `npx tsc --noEmit` 0 에러
- [ ] /login, /signup, /reset-password 200 OK
- [ ] 회원가입 → users/{uid} 도큐먼트 자동 생성 확인
- [ ] 로그인 → `__session` 쿠키 발급 + HttpOnly 검증
- [ ] 로그아웃 → 쿠키 삭제 + onAuthStateChanged null
- [ ] 잘못된 비밀번호 → Firebase 에러 메시지 한국어 처리
- [ ] /login?next=/ai → 로그인 성공 후 /ai 리다이렉트
- [ ] Google 로그인 (popup) → 첫 가입 시 displayName/photoURL 자동 채움
- [ ] 만료된 세션 쿠키 → 자동 /login 리다이렉트
- [ ] 모바일 viewport — 슬라이드업 form 정상 렌더

### 12-2. PR #2 (Sync) 머지 전

- [ ] 익명 사용자 visited[] 보유 → 가입 후 user_visits 에 머지 확인
- [ ] 익명 필터 → user_prefs 에 저장 확인
- [ ] 다른 브라우저로 로그인 → 동일 데이터 풀 확인
- [ ] 오프라인 → 온라인 복귀 시 자동 동기화
- [ ] Firestore Rules unit test 8/8 PASS
- [ ] 본인 user_visits → 200, 타인 user_visits → 403

### 12-3. PR #3 (Admin) 머지 전

- [ ] `node scripts/grant-admin.mjs catlife9029@gmail.com` 성공
- [ ] /admin → 비-admin 접근 시 / 리다이렉트
- [ ] /admin → admin 접근 시 KPI + 리스트 정상
- [ ] role 변경 → audit log 생성 + 대상자 강제 토큰 갱신
- [ ] disable 계정 → 다음 로그인 시 차단 (rules + auth)
- [ ] delete user → 본인 데이터 cascade 삭제
- [ ] 페이지네이션 (cursor) — 25개씩 정상 로드

---

## 13. 다음 단계

1. 사용자가 본 문서 검토 + 사전 액션 9-1 수행
2. 사전 액션 완료되면 **PR #1 (Auth)** 부터 순차 진행
3. PR 단위로 emulator 테스트 → staging 배포 → 프로덕션 배포
4. App Check (PR #4) 는 30일 모니터링 후 활성화

---

*작성: 2026-04-18 · 동행 문서: `docs/NEXT_SESSION_PLAN.md`, `docs/AUTH_ADMIN_UI_PLAN.md`*
