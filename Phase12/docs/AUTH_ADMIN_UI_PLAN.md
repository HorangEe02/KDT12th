# 🎨 Login/Signup + Admin Dashboard UI 구현 계획 (uiux 매핑)

> 작성: 2026-04-18 · 부모 문서: `docs/NEXT_SESSION_PLAN.md` · 짝 문서: `docs/FIREBASE_DB_PLAN.md`
> 디자인 출처:
> - Web Login: `uiux/web_uiux/login_signup/{code.html,screen.png}`
> - Web Admin: `uiux/web_uiux/admin_dashboard/{code.html,screen.png}`
> - Mobile Login: `uiux/mobile_uiux/login_signup_mobile/{code.html,screen.png}`
> - Mobile Admin: `uiux/mobile_uiux/admin_dashboard_mobile/{code.html,screen.png}`
> 전제: SE Theme(Stadium Editorial) 토큰 + Tailwind v4 + Plus Jakarta Sans/Manrope/Noto Sans KR

---

## 0. 디자인 시스템 정합성 점검

| 토큰 | 디자인 mock 값 | 기존 SE 토큰 (`globals.css`) | 매핑 |
|---|---|---|---|
| Primary | `#00193c` | `--se-primary: #00193c` ✅ | `bg-se-primary` |
| Secondary | `#1b6d24` | `--se-secondary: #1b6d24` ✅ | `bg-se-secondary` |
| Surface | `#f8f9fa` | `--se-surface: #f8f9fa` ✅ | `bg-se-surface` |
| Surface Container Lowest | `#ffffff` | `--se-surface-container-lowest` ✅ | `bg-se-surface-container-lowest` |
| Outline Variant | `#c4c6d1` | `--se-outline-variant` ✅ | `border-se-outline-variant` |
| Headline Font | Plus Jakarta Sans | 이미 layout.tsx 등록 ✅ | `font-display` |
| Body Font | Manrope | 이미 등록 ✅ | `font-body` |

> **결론**: 디자인 mock 의 모든 토큰이 SE 시스템과 호환. 추가 토큰 정의 불필요.

추가 색상 (디자인에 등장):
- Kakao Yellow: `#FEE500` → 신규 토큰 `--se-brand-kakao` 1줄 추가
- Google: 기본 white surface + outline → 기존 토큰으로 표현 가능

---

## 1. Web Login 페이지 (`/login`)

### 1-1. 디자인 분해 (mock 분석)

```
┌──────────────────────────────────────────────────────────────┐
│  [Stadium 배경 풀스크린 + primary/90 그라디언트 오버레이]      │
│                                                                │
│  ┌──────────────────────┐    ┌─────────────────────────────┐ │
│  │ Hero Text (좌측)     │    │ Form Card (우측 · max-md)   │ │
│  │                      │    │ glassmorphism 95% bg-white  │ │
│  │ "The Stadium         │    │ rounded-[2rem] shadow XL    │ │
│  │  Editorial"          │    │                             │ │
│  │ (60-72px black)      │    │ Welcome Back                │ │
│  │                      │    │ Sign in to ...              │ │
│  │ Curating your        │    │                             │ │
│  │ ultimate away game.. │    │ EMAIL                       │ │
│  │                      │    │ [📧 input pill]             │ │
│  │ (md: 보임,           │    │                             │ │
│  │  sm: 숨김)           │    │ PASSWORD       Forgot pw?   │ │
│  │                      │    │ [🔒 input pill] [eye toggle]│ │
│  │                      │    │                             │ │
│  │                      │    │ [Sign In] (primary CTA)    │ │
│  │                      │    │                             │ │
│  │                      │    │ ─── OR CONTINUE WITH ───   │ │
│  │                      │    │ [💬 Kakao (yellow)]         │ │
│  │                      │    │ [📧 Google (white border)]  │ │
│  │                      │    │                             │ │
│  │                      │    │ Don't have an account?Sign Up│ │
│  └──────────────────────┘    └─────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### 1-2. Next.js 컴포넌트 트리

```
app/login/page.tsx (server component, redirect if already auth)
└── components/auth/
    ├── login-shell.tsx          (배경 + Hero + Card 래퍼)
    │   ├── login-hero.tsx       (좌측 hero text · md+ only)
    │   └── login-card.tsx       (우측 form 카드 · client)
    │       ├── login-form.tsx   (email/pw + 제출 · "use client")
    │       ├── social-buttons.tsx (Kakao + Google)
    │       └── auth-footer.tsx   (Sign Up 링크)
```

### 1-3. login-shell.tsx 골격

```tsx
// app/login/page.tsx
import { redirect } from "next/navigation";
import { getOptionalUser } from "@/lib/firebase/server-session";
import { LoginShell } from "@/components/auth/login-shell";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string; error?: string }>;
}) {
  const sp = await searchParams;
  const user = await getOptionalUser();
  if (user) redirect(sp.next ?? "/");
  return <LoginShell next={sp.next} initialError={sp.error} />;
}
```

```tsx
// components/auth/login-shell.tsx
export function LoginShell({ next, initialError }: Props) {
  return (
    <div className="relative min-h-screen w-full flex items-center justify-center overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 z-0">
        <Image
          src="/images/login-stadium-bg.jpg"  // 사전 다운로드 또는 unsplash 정적 이미지
          alt="원정 야구장 야경"
          fill
          priority
          className="object-cover opacity-40"
        />
        <div className="absolute inset-0 bg-gradient-to-br from-se-primary/90 to-se-primary-container/80 backdrop-blur-sm mix-blend-multiply" />
      </div>

      {/* Foreground */}
      <main className="relative z-10 w-full max-w-5xl p-6 md:p-12 flex flex-col md:flex-row items-center gap-12">
        <LoginHero />        {/* hidden md:flex */}
        <LoginCard next={next} initialError={initialError} />
      </main>
    </div>
  );
}
```

### 1-4. login-hero.tsx (한국어 카피 적용)

```tsx
export function LoginHero() {
  return (
    <div className="hidden md:flex flex-1 flex-col justify-center gap-6 text-white">
      <h1 className="font-display text-5xl md:text-7xl font-black tracking-tighter leading-tight drop-shadow-2xl">
        원정 응원<br />
        플래너
      </h1>
      <p className="font-body text-lg md:text-xl text-se-primary-fixed-dim max-w-md font-medium leading-relaxed">
        경기 한 번 선택하면 티켓·교통·맛집·숙소·관광지를 한 번에.
        KBO 10개 구단 원정 응원러를 위한 AI 컴패니언.
      </p>
    </div>
  );
}
```

### 1-5. login-form.tsx 핵심

```tsx
"use client";
import { signInWithEmailAndPassword } from "firebase/auth";
import { getAuth } from "firebase/auth";
import { getClientApp } from "@/lib/firebase/client";

export function LoginForm({ next }: { next?: string }) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true); setError(null);
    try {
      const cred = await signInWithEmailAndPassword(
        getAuth(getClientApp()), email, password
      );
      const idToken = await cred.user.getIdToken();
      await fetch("/api/auth/session", {
        method: "POST",
        body: JSON.stringify({ idToken }),
      });
      await syncOnSignIn(cred.user.uid);
      router.push(next ?? "/");
    } catch (err) {
      setError(translateAuthError(err));  // Firebase 에러 → 한국어 매핑
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-5">
      <FieldEmail value={email} onChange={setEmail} />
      <FieldPassword
        value={password}
        onChange={setPassword}
        show={showPw}
        onToggle={() => setShowPw((v) => !v)}
      />
      {error && <ErrorBanner message={error} />}
      <SubmitButton loading={loading} label="로그인" />
    </form>
  );
}
```

### 1-6. 입력 필드 (mock 의 pill 스타일 정확 재현)

```tsx
function FieldEmail({ value, onChange }: ...) {
  return (
    <div>
      <label
        htmlFor="email"
        className="block font-display text-xs font-bold uppercase tracking-widest text-se-on-surface-variant mb-2 ml-1"
      >
        이메일
      </label>
      <div className="relative">
        <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-se-outline-variant text-[20px]">
          mail
        </span>
        <input
          id="email"
          type="email"
          required
          autoComplete="email"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="name@example.com"
          className="w-full bg-se-surface-container-low border-none rounded-xl py-3.5 pl-12 pr-4 text-se-on-surface font-body text-sm focus:ring-2 focus:ring-se-primary focus:bg-se-surface-container-lowest transition-all"
        />
      </div>
    </div>
  );
}
```

> Material Symbols 폰트는 layout.tsx 에 이미 CDN 링크 있음 → 추가 작업 불필요.

### 1-7. social-buttons.tsx (Kakao + Google)

```tsx
"use client";
export function SocialButtons() {
  return (
    <div className="space-y-3">
      <KakaoButton />
      <GoogleButton />
    </div>
  );
}

function KakaoButton() {
  // MVP: Identity Platform 미가입 시 비활성화 + 안내 토스트
  const onClick = () => {
    if (!ENABLED) {
      toast.info("Kakao 로그인은 곧 지원됩니다.");
      return;
    }
    signInWithKakao();  // OIDCProvider("oidc.kakao")
  };
  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full flex items-center justify-center gap-3 bg-[#FEE500] hover:bg-[#E5CE00] text-black font-body font-semibold text-sm py-3.5 rounded-xl transition-colors disabled:opacity-50"
    >
      <span className="material-symbols-outlined text-[20px]" style={{ fontVariationSettings: "'FILL' 1" }}>
        chat
      </span>
      카카오로 계속하기
    </button>
  );
}

function GoogleButton() {
  return (
    <button
      type="button"
      onClick={signInWithGoogle}
      className="w-full flex items-center justify-center gap-3 bg-se-surface hover:bg-se-surface-container-low text-se-on-surface font-body font-semibold text-sm py-3.5 rounded-xl border border-se-outline-variant transition-colors"
    >
      <GoogleLogoSvg className="h-5 w-5" />
      Google로 계속하기
    </button>
  );
}
```

### 1-8. 에러 메시지 한국어 매핑 (`lib/firebase/auth-errors.ts`)

```typescript
const MAP: Record<string, string> = {
  "auth/invalid-email":           "이메일 형식이 올바르지 않습니다.",
  "auth/user-disabled":           "비활성화된 계정입니다. 관리자에게 문의해 주세요.",
  "auth/user-not-found":          "등록되지 않은 이메일입니다.",
  "auth/wrong-password":          "비밀번호가 일치하지 않습니다.",
  "auth/email-already-in-use":    "이미 가입된 이메일입니다.",
  "auth/weak-password":           "비밀번호는 최소 8자 이상이어야 합니다.",
  "auth/popup-closed-by-user":    "로그인 창이 닫혔습니다. 다시 시도해 주세요.",
  "auth/network-request-failed":  "네트워크 오류입니다. 연결을 확인해 주세요.",
  "auth/too-many-requests":       "잠시 후 다시 시도해 주세요.",
};
export function translateAuthError(err: unknown): string {
  const code = (err as any)?.code as string | undefined;
  return (code && MAP[code]) || "로그인 중 오류가 발생했습니다.";
}
```

---

## 2. Mobile Login 페이지

### 2-1. 디자인 분해

```
┌─────────────────────────┐
│ [stadium 풀스크린 배경]  │
│                         │
│ (상단 30% — 배경만)     │
│                         │
│                         │
├─────────────────────────┤  ← rounded-t-[2.5rem] glass card
│                         │
│ THE STADIUM EDITORIAL   │
│                         │
│ Curate Your             │
│ Matchday.               │
│ (3xl black primary)     │
│                         │
│ EMAIL                   │
│ [input pill]            │
│                         │
│ PASSWORD       Forgot?  │
│ [input pill] [eye]      │
│                         │
│ [SIGN IN] CTA           │
│                         │
│ ─── OR CONTINUE WITH ─── │
│ [Kakao] [Google] (가로) │
│                         │
│ Don't have? Sign Up     │
└─────────────────────────┘
```

### 2-2. 반응형 분기 전략

**옵션 A** — 단일 컴포넌트 + Tailwind 분기:
```tsx
<div className="md:hidden">{/* mobile slideup */}</div>
<div className="hidden md:block">{/* web 좌우 split */}</div>
```

**옵션 B** — `useViewport()` 훅 + 별도 컴포넌트.

**선택**: **옵션 A (Tailwind only)**. 이유:
- 기존 사이드바 viewport 토글 (`?device=mobile`) 이 page-level 분기 → login 은 어차피 사이드바 없음
- SSR 친화 (CSS 만으로 분기 → hydration mismatch 없음)
- 한 컴포넌트 안에서 form/state 공유 → 코드 중복 최소

### 2-3. 모바일 슬라이드업 카드

```tsx
// components/auth/login-shell.tsx (확장)
<main className="relative ...">
  {/* 모바일: 풀스크린 배경 + 하단 슬라이드업 */}
  <div className="md:hidden relative h-dvh w-full max-w-md mx-auto flex flex-col justify-end overflow-hidden">
    <div className="absolute inset-0 bg-gradient-to-t from-se-primary/90 via-se-primary/40 to-transparent pointer-events-none" />
    <section className="relative z-10 w-full bg-se-surface/90 backdrop-blur-2xl rounded-t-[2.5rem] pt-10 px-8 pb-12 shadow-[0_-12px_40px_rgba(0,25,60,0.15)] flex flex-col gap-8 animate-[slideUp_.5s_ease-out]">
      <header className="flex flex-col gap-2">
        <span className="font-display text-[10px] font-extrabold uppercase tracking-[0.2em] text-se-secondary">
          원정 응원 플래너
        </span>
        <h1 className="font-display text-3xl font-extrabold text-se-primary tracking-tight">
          경기를 골라봐요.
        </h1>
      </header>
      <LoginForm next={next} />
      <SocialButtonsHorizontal />   {/* Kakao + Google 가로 분할 */}
      <SignUpFooter />
    </section>
  </div>

  {/* 데스크톱: 좌우 split */}
  <div className="hidden md:flex w-full max-w-5xl p-12 flex-row items-center gap-12">
    <LoginHero />
    <LoginCard next={next} />
  </div>
</main>
```

### 2-4. 모바일 social buttons (가로 2분할)

```tsx
function SocialButtonsHorizontal() {
  return (
    <div className="flex gap-4">
      <button className="flex-1 bg-[#FEE500]/10 hover:bg-[#FEE500]/20 text-se-on-surface py-3.5 rounded-2xl flex justify-center items-center gap-2 ring-1 ring-[#FEE500]/50 active:scale-[0.97] transition-all">
        <div className="w-5 h-5 bg-[#FEE500] rounded-full flex items-center justify-center text-black font-extrabold text-[10px] font-display">K</div>
        <span className="font-display text-xs font-bold">Kakao</span>
      </button>
      <button className="flex-1 bg-se-surface-container-lowest hover:bg-se-surface-container-low text-se-on-surface py-3.5 rounded-2xl flex justify-center items-center gap-2 ring-1 ring-se-outline-variant/40 active:scale-[0.97] transition-all shadow-sm">
        <GoogleLogoSvg className="h-5 w-5" />
        <span className="font-display text-xs font-bold">Google</span>
      </button>
    </div>
  );
}
```

### 2-5. 백그라운드 이미지 처리

| 옵션 | 장단 |
|---|---|
| Unsplash 직접 임베드 (mock 그대로) | 장: 즉시. 단: 외부 의존 + 트래킹 |
| `/public/images/login-stadium-bg.jpg` 다운로드 | **선택 ✅** — 자체 호스팅 + Next/Image LCP 최적화 |
| CSS 그라디언트만 | 가벼움. 분위기↓ |

**작업**: 자유 라이선스 KBO 야구장 야경 사진 1장 다운로드 → `frontend/public/images/login-stadium-bg.jpg` (≤ 200KB WebP).

---

## 3. Web Signup 페이지 (`/signup`)

### 3-1. 디자인 결정

mock 에 별도 signup 화면 없음 → **Login 과 동일 shell + 카드 콘텐츠만 변경**:

```tsx
// app/signup/page.tsx
export default async function SignupPage(...) {
  // ... auth check
  return <LoginShell mode="signup" />;
}

// login-shell.tsx 에 mode prop 추가 → SignupForm 분기
```

### 3-2. SignupForm 추가 필드

| 필드 | mock 적용 | 비고 |
|---|---|---|
| 이메일 | 동일 | required |
| 비밀번호 | 동일 + show/hide | min 8 |
| 비밀번호 확인 | 추가 | 클라이언트 일치 검증 |
| **닉네임 (displayName)** | 추가 | 사이드바·admin 표시 |
| **응원팀 (favoriteTeam)** | 추가 (선택) | 기존 TeamSelector 미니 버전 재활용 |
| **이용약관 동의** | 추가 (필수) | tos + privacy 체크박스 |
| **마케팅 수신 동의** | 추가 (선택) | |

### 3-3. SignupForm 흐름

```typescript
async function onSignup(values: SignupValues) {
  // 1. 클라이언트 검증
  if (values.password !== values.passwordConfirm) {
    throw new Error("비밀번호가 일치하지 않습니다.");
  }
  if (!values.consentTos || !values.consentPrivacy) {
    throw new Error("필수 약관에 동의해 주세요.");
  }

  // 2. Firebase Auth 가입
  const cred = await createUserWithEmailAndPassword(auth, values.email, values.password);
  await updateProfile(cred.user, { displayName: values.displayName });

  // 3. 세션 쿠키 + Firestore users/{uid}
  const idToken = await cred.user.getIdToken();
  await fetch("/api/auth/session", {
    method: "POST",
    body: JSON.stringify({
      idToken,
      profile: {
        displayName: values.displayName,
        favoriteTeam: values.favoriteTeam,
        consent: {
          tos: true, tosVersion: "v1", tosAt: Date.now(),
          privacy: true, privacyAt: Date.now(),
          marketing: values.consentMarketing,
        },
      },
    }),
  });

  // 4. 응원팀이 있으면 useFilters 에 즉시 반영
  if (values.favoriteTeam) {
    useFilters.setState({ team: values.favoriteTeam });
  }

  router.push("/?welcome=1");
}
```

---

## 4. Web Admin Dashboard (`/admin`)

### 4-1. 디자인 분해 (mock screenshot 기준)

```
┌─────────────────┬──────────────────────────────────────────┐
│ SideNav 256px   │ Main Canvas (flex-1)                     │
│ bg-surface-     │                                          │
│ container-low   │ ┌─ Overview ──────────────────────────┐ │
│                 │ │ "Overview"   [search] [bell]         │ │
│ Stadium         │ │ Platform performance...              │ │
│ Editorial       │ ├──────────────────────────────────────┤ │
│                 │ │ Bento Grid 4-col (lg:grid-cols-4)    │ │
│ ┌─Admin─────┐   │ │                                      │ │
│ │👤 Admin   │   │ │ ┌─ Total Users (col-span-2) ─────┐  │ │
│ │   Portal  │   │ │ │ 142,890       [+12.5% green]   │  │ │
│ └───────────┘   │ │ │ [mini bar chart 7 bars]        │  │ │
│                 │ │ └────────────────────────────────┘  │ │
│ ▣ Dashboard     │ │ ┌─ Active Trips (col-1)──┐          │ │
│ ▢ User Manage   │ │ │ ✈ ACTIVE TRIPS         │          │ │
│ ▢ Stadium Stats │ │ │ 8,432                  │          │ │
│ ▢ AI Analytics  │ │ │ Across 5 stadiums      │          │ │
│                 │ │ └────────────────────────┘          │ │
│                 │ │ ┌─ MRR (col-1)──────────┐           │ │
│                 │ │ │ 💰 MRR                 │           │ │
│                 │ │ │ $1.2M                  │           │ │
│                 │ │ │ This month             │           │ │
│ ┌Generate Rep.┐ │ │ └────────────────────────┘           │ │
│ └─────────────┘ │ ├──────────────────────────────────────┤ │
└─────────────────┤ │ ┌─ User Engagement (col-2) ──┬─Live  │ │
                  │ │ │  68k peak [30D|90D]        │ Feed  │ │
                  │ │ │  [12 bar abstract chart]   │       │ │
                  │ │ └────────────────────────────┴───────┘ │
                  │ └──────────────────────────────────────┘ │
                  └──────────────────────────────────────────┘
```

### 4-2. 한국어 + KBO 데이터 매핑

| Mock 영문 | 한국어 + 적용 데이터 |
|---|---|
| Total Users | 전체 회원 수 (실데이터: Firebase Auth count) |
| Active Trips | 진행 중 코스 (user_plans 중 시작일 ≤ 오늘 ≤ 종료일) |
| MRR | **삭제** — 무료 서비스. 대체: **누적 코스 수** 또는 **AI 챗 횟수** |
| Across 5 stadiums | 활성 구장 수 — `Set(user_plans.stadium).size` |
| User Engagement Growth (30D) | 일일 활성 사용자 (`system_metrics.activeUsers` 30일) |
| Live Feed (Tickets/Registration/Itinerary/VIP) | 실제 이벤트 — 신규 가입, 코스 생성, 공유 링크, AI 챗 |

### 4-3. 컴포넌트 트리

```
app/admin/
├── layout.tsx                 (admin claim 검증 → 비admin redirect)
├── page.tsx                   (Dashboard — KPI + Chart + Live Feed)
├── users/
│   ├── page.tsx               (사용자 목록 + 검색 + 페이지네이션)
│   └── [uid]/page.tsx         (단일 사용자 상세 + 액션)
├── stadiums/page.tsx          (구장별 통계)
├── ai/page.tsx                (AI 챗 분석)
├── audit/page.tsx             (감사 로그)
└── reports/page.tsx           (Generate Report 결과)

components/admin/
├── admin-shell.tsx            (Side nav + Top nav 통합)
├── admin-side-nav.tsx         (256px sidebar · md+)
├── admin-mobile-nav.tsx       (bottom nav · md hidden)
├── admin-top-bar.tsx          (search + bell + user)
│
├── kpi-card.tsx               (단일 KPI · 3-style 변형)
├── kpi-hero-card.tsx          (Total Users 큰 카드 + mini chart)
├── engagement-chart.tsx       (30D bar chart · Plotly dynamic)
├── live-feed.tsx              (실시간 활동 리스트)
├── live-feed-item.tsx
│
├── user-table.tsx             (paginated 25/page)
├── user-row.tsx
├── user-row-actions.tsx       (role/disable/delete dropdown)
├── role-badge.tsx
├── audit-table.tsx
└── generate-report-button.tsx (CSV/PDF 내보내기)
```

### 4-4. admin-side-nav.tsx (mock 정확 재현)

```tsx
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/admin",           label: "대시보드",     icon: "dashboard" },
  { href: "/admin/users",     label: "회원 관리",    icon: "group" },
  { href: "/admin/stadiums",  label: "구장 통계",    icon: "stadium" },
  { href: "/admin/ai",        label: "AI 분석",      icon: "smart_toy" },
  { href: "/admin/audit",     label: "감사 로그",    icon: "history" },
];

export function AdminSideNav() {
  const pathname = usePathname();
  return (
    <aside className="bg-se-surface-container-low text-se-primary font-body text-sm font-semibold h-screen w-64 fixed left-0 top-0 hidden md:flex flex-col gap-4 p-6 border-r border-transparent z-40">
      {/* Brand + Admin Portal badge */}
      <div className="mb-8">
        <div className="text-lg font-bold text-se-primary font-display tracking-tight mb-6">
          원정 응원 플래너
        </div>
        <div className="flex items-center gap-3 p-3 bg-se-surface-container-lowest rounded-xl shadow-[0_4px_24px_0_rgba(0,0,0,0.02)]">
          <div className="w-10 h-10 rounded-full bg-se-primary-fixed-dim flex items-center justify-center text-se-primary font-bold">
            <span className="material-symbols-outlined">admin_panel_settings</span>
          </div>
          <div>
            <div className="text-sm font-bold text-se-on-surface">관리자 콘솔</div>
            <div className="text-xs text-se-on-surface-variant font-medium">시스템 운영</div>
          </div>
        </div>
      </div>

      {/* Navigation links */}
      <nav className="flex flex-col gap-2 flex-grow">
        {NAV.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-all",
                active
                  ? "bg-white text-se-primary shadow-sm font-display font-bold"
                  : "text-slate-600 hover:bg-slate-200/50 hover:translate-x-1"
              )}
            >
              <span className={cn("material-symbols-outlined", active && "fill")}>
                {item.icon}
              </span>
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Generate Report CTA */}
      <div className="mt-auto pt-6">
        <button className="w-full bg-gradient-to-br from-se-primary to-se-primary-container text-white rounded-xl py-3 px-4 font-display font-bold flex items-center justify-center gap-2 hover:shadow-[0_4px_20px_rgba(0,25,60,0.15)] transition-all active:scale-95">
          <span className="material-symbols-outlined text-[20px]">description</span>
          <span>리포트 생성</span>
        </button>
      </div>
    </aside>
  );
}
```

### 4-5. KPI Hero Card (Total Users)

```tsx
export function KpiHeroCard({ value, delta, sparkline }: ...) {
  return (
    <div className="col-span-1 md:col-span-2 lg:col-span-2 bg-se-surface-container-lowest rounded-[1.5rem] p-6 lg:p-8 flex flex-col justify-between relative overflow-hidden group">
      <div className="absolute -right-10 -top-10 w-48 h-48 bg-se-primary-fixed/30 rounded-full blur-3xl group-hover:bg-se-primary-fixed/50 transition-colors duration-500" />
      <div className="relative z-10 flex justify-between items-start mb-8">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="material-symbols-outlined text-se-primary text-[20px]">group</span>
            <h2 className="font-display font-bold text-se-on-surface-variant text-sm uppercase tracking-wider">
              전체 회원 수
            </h2>
          </div>
          <div className="font-display text-5xl font-black text-se-on-surface tracking-tighter">
            {value.toLocaleString("ko-KR")}
          </div>
        </div>
        <DeltaBadge value={delta} />
      </div>
      <div className="relative z-10 mt-auto">
        <SparklineMiniBars data={sparkline} />
      </div>
    </div>
  );
}
```

### 4-6. Engagement Chart (30D bar)

mock 의 abstract bar 를 **실제 Plotly 차트**로 대체:
```tsx
// components/admin/engagement-chart.tsx
import { Plot } from "@/components/charts/plot";

export function EngagementChart({ data }: { data: { date: string; activeUsers: number }[] }) {
  return (
    <Plot
      data={[{
        type: "bar",
        x: data.map((d) => d.date),
        y: data.map((d) => d.activeUsers),
        marker: {
          color: data.map((_, i, arr) => i === arr.length - 1 ? "#00193c" : "#abc7ff"),
          line: { width: 0 },
        },
        hovertemplate: "%{x|%m월 %d일}<br>%{y:,} DAU<extra></extra>",
      }]}
      layout={{
        margin: { t: 10, r: 10, b: 30, l: 40 },
        height: 280,
        plot_bgcolor: "transparent",
        paper_bgcolor: "transparent",
        xaxis: { showgrid: false },
        yaxis: { gridcolor: "#c4c6d1", gridwidth: 0.5 },
      }}
      config={{ displayModeBar: false }}
    />
  );
}
```

### 4-7. Live Feed (실데이터 매핑)

| mock | 실데이터 소스 |
|---|---|
| Tickets Booked: Lions vs Twins | user_plans `created` 이벤트 |
| New User Registration | users `created` |
| Concierge Itinerary Generated | user_chats `session created` |
| VIP Upgrade Processed | shared_plans `created` (공유 발생) |

```tsx
// 단순화: 최근 20개 cross-collection 이벤트를 system_metrics 일일 집계로 미리 비정규화
// (Cloud Function 도입 전엔: 클라이언트에서 4 collection limit(5) 병렬 조회 + 시간 정렬)
```

### 4-8. 모바일 admin (bottom nav)

mock 기준:
- 4 탭: Dashboard / Bookings / Analytics / Settings
- 한국어: 대시보드 / 코스 / 분석 / 설정
- 활성 탭: pill 스타일 (bg-secondary-container/30 + text-se-secondary)

```tsx
// components/admin/admin-mobile-nav.tsx
const MOBILE_NAV = [
  { href: "/admin",          label: "대시보드", icon: "dashboard" },
  { href: "/admin/users",    label: "회원",     icon: "group" },
  { href: "/admin/audit",    label: "분석",     icon: "leaderboard" },
  { href: "/admin/settings", label: "설정",     icon: "admin_panel_settings" },
];
```

---

## 5. 사용자 관리 페이지 (`/admin/users`)

### 5-1. 화면 구성 (mock 의 디자인 시스템 응용)

mock 에 별도 user management 화면 없음 → **dashboard 의 카드 + 테이블 패턴 재활용**:

```
┌─────────────────────────────────────────────────────────┐
│ 회원 관리                          [🔍 검색] [+필터]    │
│ 142,890명 등록 · 이번 주 +1,247명                        │
├─────────────────────────────────────────────────────────┤
│ [Stat Bar: All 142,890 | Active 138,221 | Disabled 4,669 │
│            | Admin 12 ]                                  │
├─────────────────────────────────────────────────────────┤
│ ┌──┬─────────┬──────────────┬────────┬─────┬──────┬───┐│
│ │  │ 이메일  │ 닉네임       │ 가입일 │ 권한│ 상태 │ ⋯ ││
│ ├──┼─────────┼──────────────┼────────┼─────┼──────┼───┤│
│ │👤│ ...     │ ...          │ 4/15   │ 회원│ ● 활성│⋯ ││
│ │👤│ ...     │ ...          │ 4/14   │ 관리│ ● 활성│⋯ ││
│ │👤│ ...     │ ...          │ 4/12   │ 회원│ ○ 정지│⋯ ││
│ └──┴─────────┴──────────────┴────────┴─────┴──────┴───┘│
│              [‹ 이전]  1 2 3 4 5  [다음 ›]              │
└─────────────────────────────────────────────────────────┘
```

### 5-2. 필터/검색

- 검색: email + displayName 부분 일치 (Firestore 한계: prefix only → email/displayName 모두 lowercase 비정규화 필드 추가)
- 필터:
  - 권한: 전체 / 회원 / 관리자
  - 상태: 활성 / 비활성
  - 응원팀: KBO 10팀
  - 가입일: 7일 / 30일 / 전체

### 5-3. 행 액션 메뉴

```
⋯ 클릭 시 dropdown:
  • 상세 보기 → /admin/users/{uid}
  • 권한 변경 → 모달 (회원 ↔ 관리자)
  • 계정 비활성화 → 확인 모달
  • 계정 삭제 → 2단계 확인 (이메일 재입력)
  • 임시 비밀번호 재설정 메일 발송
```

각 액션 → POST/PATCH/DELETE API → 성공 시 toast + 행 낙관적 업데이트.

---

## 6. 사용자 상세 (`/admin/users/[uid]`)

### 6-1. 화면 구성

```
[← 회원 목록]                          [Disable] [Delete] [Save]
─────────────────────────────────────────────────────────
┌─ 프로필 ─────────────────────────────────────────────┐
│ [🖼 photoURL]  김수민                                  │
│                catlife9029@gmail.com                  │
│                가입 2026-04-12 · 마지막 접속 1시간 전 │
│                                                       │
│ [관리자 권한 ◯] [활성 ●] [응원팀 LG ▼]               │
└──────────────────────────────────────────────────────┘
┌─ 활동 통계 ─────┬─ 방문 구장 ──┬─ 코스 ─────┬─ AI 챗 ┐
│ 12 plans        │ 7 / 10        │ 3 공유     │ 24회    │
└─────────────────┴──────────────┴────────────┴─────────┘
┌─ 최근 코스 ──────────────────────────────────────────┐
│ • LG vs KT 잠실 4/22         3박4일 · ₩285,000  [열기]│
│ • SSG 인천 원정 4/15          1박2일 · ₩180,000  [열기]│
│ ...                                                   │
└──────────────────────────────────────────────────────┘
┌─ 최근 액션 (audit) ──────────────────────────────────┐
│ 2026-04-17  로그인 (Google)                           │
│ 2026-04-15  코스 생성 plan_xxx                         │
│ ...                                                   │
└──────────────────────────────────────────────────────┘
```

---

## 7. 라우팅 + 레이아웃 통합

### 7-1. 인증 가드 패턴

```tsx
// app/admin/layout.tsx
import { redirect } from "next/navigation";
import { requireAdmin } from "@/lib/firebase/server-session";

export default async function AdminLayout({ children }: { children: ReactNode }) {
  try {
    const admin = await requireAdmin();
    return <AdminShell user={admin}>{children}</AdminShell>;
  } catch {
    redirect("/login?next=/admin");
  }
}
```

```tsx
// app/(shell)/account/layout.tsx
export default async function AccountLayout({ children }) {
  const user = await getOptionalUser();
  if (!user) redirect("/login?next=/account");
  return <>{children}</>;
}
```

### 7-2. AuthProvider (top-level)

```tsx
// app/layout.tsx (수정)
import { AuthProvider } from "@/components/auth/auth-provider";

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
```

```tsx
// components/auth/auth-provider.tsx
"use client";
export function AuthProvider({ children }) {
  useEffect(() => {
    const unsub = onAuthStateChanged(getAuth(getClientApp()), async (user) => {
      useAuthStore.setState({ user, loading: false });
      if (user) {
        const idTokenResult = await user.getIdTokenResult();
        useAuthStore.setState({ claims: idTokenResult.claims });
      } else {
        useAuthStore.setState({ claims: null });
      }
    });
    return unsub;
  }, []);
  return children;
}
```

### 7-3. 사이드바 user badge (기존 shell 에 추가)

```tsx
// components/sidebar/filter-sidebar.tsx (상단에 추가)
<div className="border-b border-se-outline-variant pb-4 mb-4">
  <UserBadge />   {/* 로그인 → 닉네임 + 메뉴, 비로그인 → 로그인 버튼 */}
</div>
```

---

## 8. 신규 의존성

```json
{
  "dependencies": {
    "firebase-admin": "^12.x",  // 이미 설치됨
    "firebase": "^12.x",        // 이미 설치됨
    "zod": "^3.x"                // 이미 설치됨
  },
  "// 추가 필요": {
    "react-hook-form": "^7.x",   // login/signup form 상태 관리
    "@hookform/resolvers": "^3.x", // zod 통합
    "sonner": "^1.x"              // 토스트 알림 (admin 액션 피드백)
  }
}
```

> `react-hook-form` + zod resolver 도입 → form 검증 + 에러 메시지 일원화. Mock UI 의 input 디자인은 그대로 유지.

---

## 9. 검증 시나리오 (각 PR 머지 전)

### 9-1. Login/Signup 시각 검증

- [ ] `/login` 데스크톱 ≥ 1024px → 좌우 split + Hero 표시
- [ ] `/login` 모바일 < 768px → 풀스크린 슬라이드업 카드
- [ ] 다크 모드 (시스템 설정 따름) → 색 대비 유지 (mock 은 light only — 본 프로젝트는 light 고정 유지 결정)
- [ ] Tab 키 순회 — 이메일 → 비밀번호 → submit → social → signup link
- [ ] 비밀번호 토글 (eye icon) 작동
- [ ] Material Symbols 폰트 로드 확인 (CSP 차단 없음)

### 9-2. Admin 시각 검증

- [ ] `/admin` 데스크톱 → SideNav 256px 고정 + main flex-1
- [ ] `/admin` 모바일 → SideNav 숨김 + bottom nav 표시
- [ ] KPI 카드 숫자 0 → "데이터 없음" placeholder
- [ ] Chart 데이터 없음 시 → 스켈레톤 + "데이터 수집 중" 메시지
- [ ] Live Feed 빈 상태 → "최근 활동이 없습니다"
- [ ] 사용자 테이블 검색 — "ka" 입력 → 즉시 필터링 (debounce 300ms)
- [ ] role 변경 → toast + 행 업데이트 + audit 기록 확인

---

## 10. 스타일 토큰 추가 (한 번만)

`frontend/app/globals.css` 에 추가:

```css
@theme {
  /* === Brand auxiliaries === */
  --color-se-brand-kakao: #FEE500;
  --color-se-brand-kakao-hover: #E5CE00;

  /* === Animation === */
  --animate-slideUp: slideUp 0.5s ease-out;
}

@keyframes slideUp {
  from { transform: translateY(100%); opacity: 0; }
  to   { transform: translateY(0);    opacity: 1; }
}
```

---

## 11. 구현 순서 (세션 B 안에서 순차)

| # | 작업 | 시간 | 의존 |
|---|---|---|---|
| 1 | 토큰/폰트 추가 + Material Symbols 검증 | 30분 | - |
| 2 | `lib/firebase/auth.ts` + `auth-errors.ts` + `server-session.ts` | 1.5h | - |
| 3 | `app/api/auth/session/route.ts` (POST/DELETE) | 1h | 2 |
| 4 | `AuthProvider` + `useAuthStore` + `UserBadge` (사이드바) | 1h | 2 |
| 5 | Login shell + Hero + Form + Social (web + mobile 통합) | 2h | 4 |
| 6 | Signup form + 약관 모달 + favoriteTeam 미니 selector | 1.5h | 5 |
| 7 | sync-on-signin + visits/prefs Firestore CRUD | 1.5h | 4 |
| 8 | Firestore Rules 재작성 + emulator unit test 8건 | 1h | 7 |
| 9 | `app/admin/layout.tsx` + AdminShell + SideNav + MobileNav | 1h | 2 |
| 10 | Admin Dashboard (KPI cards + chart + live feed) | 2h | 9 |
| 11 | `/admin/users` 목록 + 검색 + 페이지네이션 + 행 액션 | 2h | 10 |
| 12 | `/admin/users/[uid]` 상세 + role/status PATCH API + audit | 1.5h | 11 |
| 13 | `scripts/grant-admin.mjs` CLI + 첫 admin 부여 | 30분 | 12 |

**총: 17시간** (NEXT_SESSION_PLAN 의 8~10h 추정보다 보수적 — UI mock 정밀 재현 + admin 페이지 완성도 반영).

---

## 12. 다음 행동

1. 본 문서 + `docs/FIREBASE_DB_PLAN.md` 사용자 검토
2. 사전 액션 (Firebase Console + Secret Manager) 수행
3. 위 11번 표 1번부터 순차 진행 (PR 단위 분리)
4. 시각 검증 9-1, 9-2 통과 후 배포

---

*작성: 2026-04-18 · 디자인 출처: uiux/web_uiux + uiux/mobile_uiux (login_signup, admin_dashboard)*
