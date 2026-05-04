# 항목 2 — 관리자 계정 + 사용자 CRUD 상세 구현 계획

> **작성일**: 2026-04-29
> **목표**: 관리자(role=admin) 계정 도입 + 가입자 관리(수정/비활성/복원/삭제) 기능 완성
> **사용자 결정**: NextAuth + Postgres role 도 OK라고 했으나, **기술 제약 발견** → 대안 채택 (§1)
> **예상 규모**: 백엔드 ~600 LOC, 프런트 ~400 LOC, 테스트 ~300 LOC, 총 1.5–2일

---

## 1. 인증 라이브러리 선택 — 재평가

### ⚠ 발견: NextAuth 정적 export 비호환

방금(Phase 1) `dashboard-web`을 정적 export로 마이그레이션했는데, **NextAuth.js / Auth.js v5는 Next.js Route Handlers (서버 측 `/api/auth/[...nextauth]`)에 의존**한다. 정적 export는 이를 만들 수 없으므로 NextAuth 직접 사용 불가.

### 후보 비교

| 후보 | 정적 export | 학습 가치(Docker/FastAPI/REST) | 외부 의존 | 비용 | 평가 |
|---|:-:|:-:|:-:|:-:|---|
| NextAuth/Auth.js v5 | ❌ | 🟡 (Node API routes 학습) | 없음 | $0 | 정적 호환 X → 제외 |
| Firebase Auth (클라 SDK) | ✅ | 🟡 Firebase 생태 | Firebase 의존 | $0 | 사용자 이미 Firebase 사용 中 |
| Clerk (외부 SaaS) | ✅ | 🔴 (학습 의도와 불일치) | Clerk 의존 | $0(무료 한도) | 학습 의도 X → 제외 |
| **자체 JWT (FastAPI 백엔드)** | ✅ | 🟢 **최고** (FastAPI/REST/JWT/bcrypt 학습) | 없음 | $0 | ⭐ **권장** |

### ✅ 결정: 자체 JWT (FastAPI Native)

**이유**:
- 사용자 학습 의도(**Docker, FastAPI, REST API**)와 100% 부합
- 정적 export `dashboard-web` 호환 (백엔드만 호출)
- 외부 SaaS 의존 0
- bcrypt + JWT (HS256) 패턴 — 업계 표준, 이력서에 가치
- 이미 가지고 있는 SQLAlchemy + Pydantic 인프라 그대로 활용
- 향후 OAuth/SSO 통합도 백엔드에서 단계 추가 가능

**구현 도구**:
- `passlib[bcrypt]` — 비밀번호 해싱
- `python-jose[cryptography]` — JWT 발급/검증
- `python-multipart` (form 데이터, OAuth2PasswordBearer 호환)
- (선택) `email-validator` — 이메일 형식 검증

---

## 2. 현재 인증 상태 (실측)

| 영역 | 현재 상태 |
|---|---|
| User 테이블 컬럼 | `id, name, team_id, avatar_emoji, dislike_categories, allergy_info, is_active, created_at` (8개) |
| 누락된 인증 컬럼 | `email, password_hash, role, last_login_at, updated_at` |
| 백엔드 인증 미들웨어 | 없음 (모든 엔드포인트 공개) |
| JWT/세션/쿠키 | 없음 |
| 프런트 토큰 | 없음 (`p11_current_user` localStorage 만) |
| 비밀번호 개념 | 없음 (사용자가 ID + 이름만 입력하면 바로 등록) |
| Admin 구분 | 없음 (모든 사용자 동등) |
| DELETE /api/users 엔드포인트 | 없음 |
| Rate limiting (/api/users) | 없음 (스팸 가능) |
| 일회성 사용자 정리 | ✅ 완료 (Phase 1에서 archive 후 삭제) |

---

## 3. 변경 설계 (5단계)

### Phase A — 백엔드 인증 인프라 (반일)

#### A-1. DB 스키마 마이그레이션

`lunch-optimizer/database/models.py` User 모델 확장:

```python
class User(Base):
    __tablename__ = "users"

    id = Column(String(50), primary_key=True)
    email = Column(String(120), unique=True, nullable=True, index=True)  # NEW
    password_hash = Column(String(255), nullable=True)                    # NEW
    role = Column(String(20), default="user", nullable=False, index=True) # NEW: admin|user
    name = Column(String(50), nullable=False)
    team_id = Column(String(50), ForeignKey("teams.id"), index=True)
    avatar_emoji = Column(String(10), default="🧑‍💻")
    dislike_categories = Column(String(200), nullable=True)
    allergy_info = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # NEW
    last_login_at = Column(DateTime, nullable=True)                       # NEW

    team = relationship("Team", back_populates="users")
```

⚠ `email`, `password_hash` 는 nullable=True — 기존 게스트 계정(이메일 미등록) 호환을 위해. role 만 NOT NULL.

마이그레이션 방식: SQLAlchemy `create_all()` 은 새 컬럼 자동 추가 안 함. 수동 ALTER TABLE 스크립트로 처리:
- `scripts/migrate_auth_columns.py` — IF NOT EXISTS 패턴으로 idempotent 실행

#### A-2. 인증 유틸리티 신규

새 파일 `lunch-optimizer/auth/__init__.py`:
- `hash_password(plain) -> str` (bcrypt cost=12)
- `verify_password(plain, hashed) -> bool`
- `create_access_token(payload, expires=24h) -> str` (JWT HS256)
- `decode_access_token(token) -> dict` (서명 검증, 만료 체크)
- `JWT_SECRET` env 변수 (없으면 `secrets.token_urlsafe(32)` 자동 생성, 단 영속성 X → .env 필수 권장)

#### A-3. 인증 의존성 (Depends)

`lunch-optimizer/auth/deps.py`:
- `get_current_user(token: str = Depends(oauth2_scheme)) -> User` — 401 if invalid
- `require_admin(user: User = Depends(get_current_user)) -> User` — 403 if role != admin
- `optional_current_user(...)` — 게스트 허용 엔드포인트용

#### A-4. /auth 라우터

`lunch-optimizer/api/routers/auth.py`:

| Method | Path | Body | Response | Notes |
|---|---|---|---|---|
| POST | `/api/auth/register` | `{email, password, name, team_id?}` | `{access_token, user}` | password ≥8자, email 검증 |
| POST | `/api/auth/login` | `{email, password}` | `{access_token, user}` | last_login_at 갱신 |
| GET | `/api/auth/me` | — | `User` | JWT 검증, 본인 정보 반환 |
| POST | `/api/auth/change-password` | `{old_password, new_password}` | `{ok: true}` | 본인만 |

#### A-5. Admin 부트스트랩

`scripts/bootstrap_admin.py`:
- `.env` 의 `ADMIN_EMAIL`, `ADMIN_PASSWORD` 읽음
- 해당 이메일이 없으면 admin 계정 생성, 있으면 role=admin 보장
- idempotent 실행 가능

`.env.example` 추가:
```bash
JWT_SECRET=__GENERATE_WITH__python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_EXPIRE_HOURS=24
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=__SET_STRONG_PASSWORD__
```

---

### Phase B — Admin 엔드포인트 (반일)

#### B-1. /api/admin 라우터

`lunch-optimizer/api/routers/admin.py` — 모두 `Depends(require_admin)` 적용:

| Method | Path | 기능 |
|---|---|---|
| GET | `/api/admin/users` | 페이지네이션 (offset/limit, 기본 20), 필터 (role, is_active, q=이름검색) |
| GET | `/api/admin/users/{id}` | 비활성 사용자도 조회 가능 |
| PATCH | `/api/admin/users/{id}` | role, is_active, name, email 변경 |
| DELETE | `/api/admin/users/{id}` | soft-delete (is_active=False, archived_at 갱신) |
| POST | `/api/admin/users/{id}/restore` | 복원 (is_active=True) |
| GET | `/api/admin/audit-log` | (옵션) 관리자 액션 로그 — Phase B-3 |

#### B-2. 자기 자신 보호 가드

- 본인을 admin → user 강등 시 다른 admin 0명이면 거부 (last admin protection)
- 본인 계정 DELETE 거부

#### B-3. (옵션) Audit Log

`AdminAuditLog` 테이블:
- `id, admin_user_id, action, target_user_id, before_json, after_json, created_at`
- PATCH/DELETE/RESTORE 시 자동 기록
- 우선순위 낮음 — 시간 부족 시 Phase 2 후속으로

#### B-4. Rate Limiting

이미 `slowapi` 가 nlp-api에 있음. lunch-optimizer 에도 도입:
- `/api/auth/login`: 5회 / 15분 / IP
- `/api/auth/register`: 10회 / 1시간 / IP
- `/api/admin/*`: 100회 / 1분 / 사용자

---

### Phase C — 프런트엔드 인증 재구성 (반일)

#### C-1. localStorage 스키마 변경

```typescript
// before
localStorage["p11_current_user"] = { id, name, team_id, avatar_emoji }

// after
localStorage["p11_auth_token"] = "eyJhbGc..."   // JWT
// 사용자 정보는 JWT 디코딩으로 즉시 추출 (id, email, role, name 등)
```

#### C-2. `lib/auth.ts` 재작성

- `register({email, password, name, team_id?})` → POST /api/auth/register
- `login({email, password})` → POST /api/auth/login → 토큰 저장
- `logout()` → 토큰 삭제, 이벤트 발행
- `getToken()`, `getCurrentUser()` (JWT decode)
- `hasRole("admin")` 헬퍼

#### C-3. `lib/api.ts` Authorization 헤더 자동 부착

```typescript
async function apiFetchLunch<T>(path, opts) {
  const token = getToken();
  const headers = { ...opts.headers };
  if (token) headers.Authorization = `Bearer ${token}`;
  // ...기존 로직
}
```

401 응답 시 토큰 만료로 간주 → logout + /login 리다이렉트.

#### C-4. 페이지 갱신

- `/login` 페이지: email + password 필드 추가, "회원가입" 토글
- `/onboarding`: 가입 후 자동 진입 (변경 없음)
- 새 페이지 `/register` 옵션 (또는 /login 안에서 토글)

---

### Phase D — Admin UI (반일)

#### D-1. `/admin` 라우트 — 권한 가드

`src/app/admin/layout.tsx`:
- `useAuth()` 로 role 검사 → admin 아니면 `/login` 리다이렉트
- 정적 export 환경이라 클라이언트 가드만 가능 → **실제 보안은 백엔드 401/403 으로 보장**

#### D-2. `/admin/page.tsx` — 사용자 테이블

- 검색 (name 부분 일치)
- 필터 (role, is_active)
- 페이지네이션 (20행/페이지)
- 행 동작: 편집(PATCH) / 비활성(DELETE soft) / 복원
- 테이블 컬럼: avatar | name | email | role | team | created | last_login | active | actions

#### D-3. `/admin/users/[id]/page.tsx` — 정적 export 호환

⚠ Next.js 정적 export 는 dynamic route (`[id]`) 에 `generateStaticParams` 필요. 두 가지 옵션:
- (A) 동적 라우트 X → query param `?id=xxx` 로 처리 (`/admin/edit?id=xxx`)
- (B) `generateStaticParams` 로 빈 배열 반환 + `dynamicParams=true` ⛔ 정적 export 무효

→ **옵션 A 채택**: `/admin/edit?id=xxx` 형태, useSearchParams 활용.

#### D-4. 모달 동작

- 비활성 시 confirm("정말 비활성화? 데이터는 보존됩니다.")
- 자기 자신 admin 강등 차단 UI (last admin protection 미러링)
- 패스워드 초기화 옵션 (관리자가 임시 비밀번호 설정 → 사용자 이메일 미사용이라 화면에 표시)

---

### Phase E — 검증 + 보안 리뷰 (반일)

#### E-1. pytest 단위 테스트

`lunch-optimizer/tests/test_auth.py`:
- 비밀번호 해시 라운드트립
- JWT 발급/검증/만료
- /auth/register 정상 + 이메일 중복 + 약한 비밀번호
- /auth/login 정상 + 잘못된 비밀번호 + 비활성 사용자 거부
- /api/auth/me 토큰 검증
- last admin protection
- soft-delete + restore

`tests/test_admin.py`:
- 일반 사용자가 /admin/* 호출 시 403
- admin 정상 동작
- rate limit 작동 (5회 초과)

#### E-2. E2E

- 정적 빌드 + 로컬 serve → /login 회원가입 → /onboarding → /
- Admin 부트스트랩 후 /admin → 사용자 목록 → 비활성/복원
- Cloudflare Tunnel + Firebase 배포 시 외부에서 동일 검증

#### E-3. 보안 리뷰 체크리스트

| 항목 | 검증 방법 |
|---|---|
| 비밀번호 평문 저장 X | DB 직접 조회 → bcrypt 해시 확인 |
| JWT 시크릿 강도 | 32바이트 이상 (urlsafe_b64) |
| 토큰 만료 작동 | 짧은 만료(60초) 토큰으로 401 트리거 |
| Rate limit 작동 | 5회 초과 후 429 |
| Admin 엔드포인트 가드 | 일반 토큰으로 403 |
| Last admin 보호 | 단일 admin 강등 시 거부 |
| Soft-delete 후 인증 차단 | is_active=False 사용자 토큰 발급 거부 |
| Self DELETE 차단 | 본인 ID DELETE 시 거부 |
| Email enumeration 방지 | 회원가입 실패 메시지 일반화 |
| CORS 화이트리스트 | Firebase 도메인 + Tunnel 도메인만 |
| HTTPS 강제 | Cloudflare Tunnel 자동 처리 |
| 비밀번호 정책 | 최소 8자, 향후 zxcvbn 점수 확장 가능 |

---

## 4. 영향 범위

### 변경되는 파일
- `lunch-optimizer/database/models.py` (User 클래스)
- `lunch-optimizer/api/main.py` (router include + CORS)
- `lunch-optimizer/requirements.txt` (passlib, python-jose, slowapi)
- `dashboard-web/src/lib/auth.ts`, `useAuth.ts`, `api.ts`
- `dashboard-web/src/app/login/page.tsx`
- `.env.example` (JWT_SECRET, ADMIN_EMAIL, ADMIN_PASSWORD)

### 새로 추가되는 파일 (백엔드)
- `lunch-optimizer/auth/__init__.py`, `auth/deps.py`, `auth/jwt_utils.py`, `auth/passwords.py`
- `lunch-optimizer/api/routers/auth.py`, `routers/admin.py`
- `lunch-optimizer/scripts/migrate_auth_columns.py`
- `lunch-optimizer/scripts/bootstrap_admin.py`
- `lunch-optimizer/tests/test_auth.py`, `tests/test_admin.py`

### 새로 추가되는 파일 (프런트)
- `dashboard-web/src/app/admin/layout.tsx`, `page.tsx`, `edit/page.tsx`
- `dashboard-web/src/components/admin/*`

### Breaking changes
- 기존 `/api/users` POST 는 게스트 모드로 살리거나 (옵셔널) deprecate
- localStorage `p11_current_user` → `p11_auth_token` 마이그레이션 코드 필요 (1회성)
- 사용자 데이터는 이미 정리됨(Phase 1에서) → 마이그레이션 부담 거의 없음

---

## 5. 위험 매트릭스

| 위험 | 가능성 | 영향 | 완화 |
|---|:-:|:-:|---|
| 정적 export + dynamic route 비호환 | 🟡 | 🟡 | query-param 방식(`/admin/edit?id=`)으로 회피 |
| JWT secret 누출 | 🟢 | 🔴 | .env, 100% 백엔드, gitignore |
| bcrypt 비용 12 → 로그인 지연 | 🟢 | 🟢 | 비용 12는 ~250ms — UX 허용 범위 |
| last admin lockout | 🟡 | 🔴 | 가드 + 테스트 |
| `slowapi` 미설치 시 import 실패 | 🟢 | 🟡 | 옵셔널 import + try/except (이미 nlp-api 패턴 활용) |
| Firebase deploy 시 NEXT_PUBLIC env 미주입 | 🟡 | 🟡 | deploy_demo.sh 가 .env.production 자동 갱신 |
| 기존 `/api/users` 호출이 토큰 없어 401 | 🔴 | 🟡 | 호환 모드: optional_current_user 사용, 점진 deprecate |

---

## 6. 단계별 산출물 체크리스트

### Phase A
- [ ] `database/models.py` User 확장
- [ ] `scripts/migrate_auth_columns.py` 실행 가능
- [ ] `auth/passwords.py`, `auth/jwt_utils.py`, `auth/deps.py`
- [ ] `api/routers/auth.py` 4 엔드포인트
- [ ] `scripts/bootstrap_admin.py` 실행 가능
- [ ] `.env.example` 갱신

### Phase B
- [ ] `api/routers/admin.py` 6 엔드포인트
- [ ] `slowapi` 통합 (lunch-optimizer)
- [ ] last admin / self-delete 가드

### Phase C
- [ ] `lib/auth.ts` 재작성 (register/login/logout/getCurrentUser/hasRole)
- [ ] `lib/api.ts` Bearer 자동 부착
- [ ] `/login` 페이지 email/password 추가
- [ ] localStorage 마이그레이션 (`p11_current_user` → `p11_auth_token`)

### Phase D
- [ ] `/admin/layout.tsx` role 가드
- [ ] `/admin/page.tsx` 사용자 테이블
- [ ] `/admin/edit?id=...` 편집/비활성/복원 모달

### Phase E
- [ ] pytest test_auth.py, test_admin.py 통과
- [ ] 정적 빌드 통과
- [ ] 외부 데모 (Firebase + Tunnel) 검증
- [ ] 보안 리뷰 보고서 (DOCKER 보고서와 같은 형식)

---

## 7. 일정

| Phase | 시간 |
|---|:-:|
| A — 백엔드 인증 인프라 | 4–5h |
| B — Admin 엔드포인트 + 가드 | 3h |
| C — 프런트 인증 재구성 | 3h |
| D — Admin UI | 3h |
| E — 검증 + 보안 리뷰 | 3h |
| **합계** | **약 16–17h (1.5–2일)** |

본 계획서 승인 시 즉시 Phase A 부터 자율 진행 (auto mode).
