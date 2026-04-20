# 🔐 세션 B 사전 액션 가이드 — Firebase Auth 활성화

> 작성: 2026-04-18 · 짝 문서: `docs/FIREBASE_DB_PLAN.md`, `docs/AUTH_ADMIN_UI_PLAN.md`
> 대상: 사용자 (수동 수행) · 소요: 약 15~20분
> 완료 후 알려주시면 코드 통합 단계로 진행합니다.

---

## ✅ 진행 상태 체크 (위에서 아래로)

각 단계 완료 시 ✅ 로 변경해 주세요.

### 1. Firebase Console — Authentication 활성화

- [ ] 1-1. https://console.firebase.google.com/project/mini12-310f5/authentication 접속
- [ ] 1-2. **시작하기** 클릭 (이미 활성화돼 있으면 통과)
- [ ] 1-3. **로그인 방법** 탭 → 신규 제공업체 추가:
  - [ ] **이메일/비밀번호** → 사용 설정 → 저장
    - "이메일 링크 (비밀번호 없는 로그인)" 은 **비활성** 유지
  - [ ] **Google** → 사용 설정
    - 프로젝트 지원 이메일: `catlife9029@gmail.com` 선택
    - 저장

> **선택 (P1 — Kakao OIDC)**: Identity Platform 업그레이드가 필요해 MVP 에서는 건너뜁니다. 나중에 추가 가능.

### 2. Firebase Console — 웹 앱 SDK Config 확인

- [ ] 2-1. https://console.firebase.google.com/project/mini12-310f5/settings/general 접속
- [ ] 2-2. **내 앱** 섹션 → 웹 앱(`</>`) 항목의 **SDK 설정 및 구성** 펼치기
- [ ] 2-3. `Config` 형식 선택 → 다음 6 값을 복사해 두기 (안전한 메모장에 붙여넣기):
  ```javascript
  const firebaseConfig = {
    apiKey: "AIzaSy...",                          // ← ⓐ 필요
    authDomain: "mini12-310f5.firebaseapp.com",   // (이미 yaml hardcode)
    projectId: "mini12-310f5",                    // (이미 hardcode)
    storageBucket: "mini12-310f5.appspot.com",    // (이미 hardcode)
    messagingSenderId: "262552815882",            // ← ⓑ 필요
    appId: "1:262552815882:web:..."               // ← ⓒ 필요
  };
  ```

### 3. 로컬 `.env.local` 추가

- [ ] 3-1. `frontend/.env.local` 파일 열기
- [ ] 3-2. 아래 3 줄 추가 (위에서 복사한 값 사용):
  ```bash
  NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSy...           # ⓐ
  NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=262552815882  # ⓑ
  NEXT_PUBLIC_FIREBASE_APP_ID=1:262552815882:web:...     # ⓒ
  ```
- [ ] 3-3. 파일 저장
- [ ] 3-4. (이미 .gitignore 에 `.env.local` 포함 — 확인만)

### 4. 프로덕션 Secret Manager 등록 (3개)

- [ ] 4-1. 터미널에서 프로젝트 루트로 이동:
  ```bash
  cd "/Volumes/Corsair EX300U Media/00_work_out/01_complete/Phase12"
  ```
- [ ] 4-2. (Firebase CLI 로그인이 안돼 있다면) `firebase login`
- [ ] 4-3. 시크릿 3종 등록 — 각각 실행 후 값 입력 프롬프트:
  ```bash
  firebase apphosting:secrets:set NEXT_PUBLIC_FIREBASE_API_KEY \
    --project mini12-310f5
  # → ⓐ 값 붙여넣기 + Enter

  firebase apphosting:secrets:set NEXT_PUBLIC_FIREBASE_APP_ID \
    --project mini12-310f5
  # → ⓒ 값 붙여넣기 + Enter

  firebase apphosting:secrets:set NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID \
    --project mini12-310f5
  # → ⓑ 값 붙여넣기 + Enter
  ```

> 각 명령은 "Grant the App Hosting backend access?" 묻습니다 → **Y** 선택.

### 5. (선택) 로컬 admin SDK 테스트용 서비스 계정

다음 단계의 `grant-admin.mjs` CLI 가 로컬에서 작동하려면 두 옵션 중 하나:

**옵션 A — Application Default Credentials (권장):**
- [ ] 5-A1. `gcloud auth application-default login`
  - 브라우저 열림 → Google 계정 선택 → 권한 허용
- [ ] 5-A2. `gcloud config set project mini12-310f5`

**옵션 B — 서비스 계정 키 파일:**
- [ ] 5-B1. https://console.cloud.google.com/iam-admin/serviceaccounts/details/firebase-adminsdk?project=mini12-310f5 접속
- [ ] 5-B2. **키** 탭 → **키 추가** → JSON → 다운로드
- [ ] 5-B3. 파일을 `frontend/secrets/service-account.json` 로 저장
- [ ] 5-B4. `frontend/.env.local` 에 추가:
  ```bash
  GOOGLE_APPLICATION_CREDENTIALS=./secrets/service-account.json
  ```

> **주의**: 서비스 계정 JSON 은 절대 git 에 커밋 금지 (.gitignore 이미 차단).

### 6. (배포 후 자동) Firestore 규칙 + 인덱스 배포

- [ ] 6-1. 코드 작업 완료 후 자동으로:
  ```bash
  firebase deploy --only firestore --project mini12-310f5
  ```
- [ ] 6-2. App Hosting 신규 빌드:
  ```bash
  firebase deploy --only apphosting --project mini12-310f5
  ```

### 7. 초기 admin 이메일 결정

- [ ] 7-1. 첫 admin 으로 만들 이메일 결정 (기본: `catlife9029@gmail.com`)
- [ ] 7-2. 위 이메일로 회원가입 완료 후 → CLI 로 권한 부여:
  ```bash
  cd frontend
  node scripts/grant-admin.mjs catlife9029@gmail.com
  ```

---

## 🚦 사전 액션 완료 신호

위 1~5 (또는 1~4) 까지 마치셨으면 다음 메시지에 **"사전 액션 완료"** 라고 알려주세요.
그러면 다음 코드 단계로 진행합니다:
- Session Cookie API 라우트 (`/api/auth/session`)
- AuthProvider + AuthStore + UserBadge
- Login/Signup 페이지 (Web + Mobile)
- Firestore Rules 재작성
- Admin Layout + Dashboard + Users 관리
- `grant-admin.mjs` CLI

---

## 🛠 코드는 어디까지 미리 진행됐나? (병렬 진행 중)

사전 액션과 무관하게 진행 가능한 부분은 이미 시작:
- ✅ 의존성 설치 (`react-hook-form`, `@hookform/resolvers`, `sonner`)
- ✅ 한국어 에러 메시지 매핑 (`lib/firebase/auth-errors.ts`)
- ✅ 사용자 타입 정의 (`lib/types/user.ts`)
- ✅ Auth helper 골격 (`lib/firebase/auth.ts`) — Firebase Web SDK 사용
- ✅ Server-session helper (`lib/firebase/server-session.ts`) — Admin SDK 사용
- ✅ Zustand auth store (`lib/store/auth.ts`)
- ✅ Slide-up 애니메이션 + Kakao 색 토큰 (`globals.css`)

이들은 빌드/타입 체크는 통과하지만, 실제 로그인 동작은 Firebase Auth 활성화 후 가능.

---

## ❓ 자주 묻는 질문

**Q. Firebase 콘솔이 처음이라 헤매면?**
A. 1-1 링크 클릭 → "Enable Google Analytics?" 묻는 화면이 나오면 **건너뛰기** OK.

**Q. Secret 값을 잘못 등록했어요.**
A. `firebase apphosting:secrets:set <NAME> --project mini12-310f5` 다시 실행하면 새 버전으로 덮어씁니다.

**Q. `firebase login` 이 거부돼요.**
A. 브라우저 팝업 차단 해제 후 재시도. 또는 `firebase login --no-localhost` 사용.

**Q. 무료 한도 초과 걱정?**
A. Spark 플랜: Auth 50K MAU 무료 · Firestore 50K reads/day 무료. 데모 트래픽 충분.

---

*작성: 2026-04-18 Session B step 0*
