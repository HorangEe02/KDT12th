# 항목 2 — Auth + RBAC 변경 보안 리뷰

> **검토일**: 2026-04-29
> **변경 범위**: 백엔드 ~720 LOC + 프런트엔드 ~520 LOC + 테스트 ~360 LOC
> **검증 결과**: ✅ **27/27 pytest 통과**, E2E 인증 흐름 정상, 회귀 0건

---

## 1. 변경 보안 영향 매트릭스

| # | 항목 | 변경 전 | 변경 후 | 영향 |
|:-:|---|---|---|:-:|
| 1 | 비밀번호 저장 | ❌ 비밀번호 개념 자체 없음 (id+name 만으로 로그인) | ✅ bcrypt cost=12 해시 | ✅ 신규 보호 |
| 2 | 인증 토큰 | ❌ 없음 (localStorage 평문 user-id) | ✅ JWT HS256, 24h 만료 | ✅ 신규 보호 |
| 3 | 권한 분리 | ❌ 모든 사용자 동등 | ✅ admin/user RBAC | ✅ 신규 보호 |
| 4 | 인증 미들웨어 | ❌ 모든 엔드포인트 공개 | ✅ /auth, /admin 가드 | ✅ 신규 보호 |
| 5 | 세션 만료 | ❌ 영구 (localStorage) | ✅ JWT exp 검증 | ✅ 신규 보호 |
| 6 | last admin 보호 | ❌ | ✅ 마지막 admin 강등/비활성 차단 | ✅ 신규 보호 |
| 7 | self-deactivate 차단 | ❌ | ✅ 본인 비활성 거부 | ✅ 신규 보호 |
| 8 | 이메일 enumeration | — | ✅ 로그인 실패 메시지 통일 | ✅ |
| 9 | 비밀번호 정책 | — | ✅ 최소 8자, bcrypt 72byte cap | ✅ |
| 10 | 일회성 사용자 정리 | ⚠ DB에 잔존 | ✅ Phase 1에서 archive 후 삭제 | ✅ |
| 11 | DB 데이터-코드 격리 | ❌ /app/database 통합 | ✅ /app/data + /app/database 분리 | ✅ 운영 안정 |

---

## 2. 핵심 컴포넌트별 분석

### 2-1. 비밀번호 해싱 (`auth/passwords.py`)

**구현**:
- bcrypt 4.2.0 직접 사용 (passlib 1.7.4 제거 — bcrypt 4.x 호환 깨짐)
- 비용 인자 12 (~250ms, 무차별 대입 충분히 방어)
- 72바이트 제한 명시적 처리 (`_to_bytes` 자동 자르기)
- 해시 + verify 라운드트립 단위 테스트 통과

**주의**: 한글 비밀번호는 1자=3바이트, 영문은 1자=1바이트 → 한글 24자 / 영문 72자가 실효 한계 (bcrypt 본질적 제약).

### 2-2. JWT (`auth/jwt_utils.py`)

**구현**:
- python-jose 3.3.0, HS256 알고리즘
- 시크릿: `JWT_SECRET` 환경변수 (32바이트 url-safe random 생성됨)
- 만료: 24시간 (운영) / 1초 (테스트 — `expires_in_seconds`)
- 페이로드: `sub` + `email` + `role` + `iat` + `exp`

**검증된 시나리오**:
- ✅ 정상 발급/검증
- ✅ 만료 토큰 거부 (`JWTError` 발생)
- ✅ 변조된 토큰 거부 (서명 불일치)
- ✅ 시크릿 미설정 시 임시 발급 + 경고 (재시작 시 모든 토큰 무효화 — 운영 안전 디폴트)

**개선 여지**:
- RS256 비대칭 키로 전환 시 토큰 검증을 외부 서비스에 위임 가능
- Refresh token 분리 (현재는 access token 단일 — 24h 후 재로그인)

### 2-3. RBAC 가드 (`auth/deps.py`)

**구현**:
- `OAuth2PasswordBearer(auto_error=False)` — 헤더 없을 때 None
- `get_current_user` — 401 발생 (필수 인증)
- `optional_current_user` — None 허용 (게스트 호환)
- `require_admin` — 403 (인증 후 권한 분기)

**검증**:
- ✅ 토큰 없음 → 401
- ✅ 잘못된 토큰 → 401
- ✅ 일반 user 토큰으로 admin 호출 → 403
- ✅ admin 토큰으로 admin 호출 → 200

### 2-4. /auth 엔드포인트

| Method | Path | 보안 사항 |
|---|---|---|
| POST | `/api/auth/register` | 이메일 중복 → 409 / 약한 비밀번호 → 422 / Pydantic 검증 |
| POST | `/api/auth/login` | enumeration 방지 (실패 메시지 통일), inactive 거부 |
| GET | `/api/auth/me` | 토큰 필수 |
| POST | `/api/auth/change-password` | 현재 비밀번호 검증 후 갱신 |

### 2-5. /admin 엔드포인트

모두 `Depends(require_admin)` 통과:

| Method | Path | 보안 가드 |
|---|---|---|
| GET | `/api/admin/users` | offset/limit 0–100, q는 100자 제한 |
| GET | `/api/admin/users/{id}` | 비활성 사용자도 조회 가능 |
| PATCH | `/api/admin/users/{id}` | last admin 보호 + self-deactivate 거부 + 비밀번호 재설정 |
| DELETE | `/api/admin/users/{id}` | soft-delete (is_active=False), self/last-admin 차단 |
| POST | `/api/admin/users/{id}/restore` | 복원 |
| GET | `/api/admin/stats` | 사용자/admin 카운트 |

**DELETE는 soft-delete만**: 데이터 보존 + 복원 가능. 하드 삭제는 의도적으로 미구현 (감사 추적성 우선).

---

## 3. 펜테스트 시나리오 검증

### 3-1. 회피된 공격 벡터

| 공격 | 차단 경로 |
|---|---|
| **SQL 주입** (이메일/이름 입력) | SQLAlchemy ORM 파라미터 바인딩 (raw SQL 미사용) |
| **무차별 대입** | bcrypt 12 → 1초당 4건 미만 (실용적 차단) |
| **JWT 위조** | HS256 서명 검증 실패 → 401 |
| **JWT 만료** | exp 검증 강제 |
| **이메일 enumeration** | 로그인 실패 메시지 단일 ("이메일 또는 비밀번호 불일치") |
| **권한 상승** | role==admin 가드, JWT의 role 클레임 검증 |
| **마지막 admin lockout** | last admin 보호 가드 (test_admin.py 검증) |
| **본인 계정 자살** | self-DELETE 거부 |
| **CSRF (토큰)** | Authorization 헤더 + CORS 화이트리스트 (Cookie 미사용 → 자동 첨부 X) |
| **XSS → 토큰 탈취** | localStorage 사용 (이론적 위험). 프런트 측 입력 sanitization 의존 — 향후 httpOnly cookie 검토 |

### 3-2. 잠재 위험 (의도적 트레이드오프)

| 위험 | 결정 사유 | 완화 |
|---|---|---|
| localStorage 토큰 (XSS) | 정적 export 환경 + Cloudflare Tunnel은 cookie 도메인 제약 | CSP 헤더 강화 가능 (Phase X+1) |
| /admin 클라이언트 가드만 | 정적 export는 server-side middleware 불가 | 모든 보호 엔드포인트가 서버 401/403 — 클라 가드는 UX 일 뿐 |
| Self-service 회원가입 무제한 | 데모/포트폴리오 목적 | rate limit (slowapi) 추가 가능 (Phase F) |
| RS256 미사용 | HS256 단일 서비스에 충분 | 다중 서비스 확장 시 키 회전 가능 |
| 비밀번호 재시도 횟수 무제한 | bcrypt가 자체 지연 부과 | rate limit 도입 시 명시적 카운터 가능 |

---

## 4. 회귀 테스트 결과

### 4-1. pytest (백엔드)
```
tests/test_auth.py  — 15/15 PASSED
tests/test_admin.py — 12/12 PASSED
27 passed in 12.70s
```

### 4-2. E2E (수동, production)
| 시나리오 | 결과 |
|---|:-:|
| `POST /api/auth/register` | ✅ 201, 토큰 발급 + DB persist |
| `POST /api/auth/login` | ✅ 200, last_login_at 갱신 |
| `GET /api/auth/me` (with token) | ✅ 본인 정보 |
| `GET /api/admin/users` (user role) | ✅ 403 |
| `GET /api/admin/users` (no token) | ✅ 401 |
| `POST /api/auth/login` (잘못된 비밀번호) | ✅ 401, 동일 메시지 |
| `POST /api/auth/login` (없는 이메일) | ✅ 401, 동일 메시지 |
| `POST /api/auth/login` (inactive 사용자) | ✅ 401 |

### 4-3. 정적 빌드
- `npm run build:static` — 12개 라우트 prerender 통과 (`/admin` 포함)
- 출력 3.7MB

### 4-4. 환경 통합
- Cloudflare Tunnel via Caddy: `*.trycloudflare.com` 와일드카드 매칭 적용
- HTTPS 강제 (Cloudflare 자동)
- CORS: Firebase Hosting 도메인 화이트리스트만

---

## 5. 운영 권장 사항

### 5-1. 즉시
1. **`.env`에 ADMIN_EMAIL/ADMIN_PASSWORD 추가** 후 `bootstrap_admin.py` 실행으로 첫 admin 계정 생성
2. **`.env`의 JWT_SECRET 백업** — 분실 시 모든 사용자 강제 로그아웃됨

### 5-2. 단기 (1주)
3. **Rate limiting 활성화** — 이미 `slowapi` 의존성 추가됨. `/api/auth/login` 5회/15분/IP 권장
4. **CORS 화이트리스트 정리** — 임시 Tunnel URL 주기적 정리 (or 영구 도메인 마이그레이션)
5. **mini-db 외부 볼륨 정리** — Phase 1의 옛 데이터 보존이지만, 새 mini-data로 이주 완료 후 archive 가능

### 5-3. 중기 (1달)
6. **Refresh token 도입** — access 1h + refresh 30d 패턴
7. **HttpOnly cookie 옵션** — XSS 위협 완화
8. **Audit log 테이블** — 관리자 액션 추적 (계획서 §B-3)
9. **Email verification** — 회원가입 시 이메일 링크 검증
10. **Password reset flow** — `/auth/forgot-password` + 토큰 + 이메일 전송

### 5-4. 장기
11. **OAuth2 통합** — Google/GitHub 로그인
12. **MFA** — TOTP 또는 WebAuthn

---

## 6. 부수 발견

- 🔧 **버그 수정 1건**: `get_session()` 컨텍스트 매니저가 자동 commit 하지 않음 → 라우터에 `session.commit()` 추가 (auth.register/login/change_password, admin.update/deactivate/restore)
- 🔧 **인프라 수정 1건**: named volume이 코드 디렉토리(`/app/database/`)를 가려 image 코드 변경이 무효 → 데이터 디렉토리 분리 (`/app/data/mini.db`)
- 🔧 **의존성 수정 1건**: passlib 1.7.4 + bcrypt 4.x 호환 깨짐 → bcrypt 4.x 직접 사용으로 전환
- ⚠ **건강성 이슈 0건**: 회귀 없음

---

## 7. 보안 체크리스트 (요약)

- [x] 비밀번호 평문 저장 X
- [x] JWT 시크릿 32바이트+ url-safe random
- [x] 토큰 만료 작동
- [x] Admin 엔드포인트 가드
- [x] Last admin 보호
- [x] Self-deactivate 차단
- [x] Email enumeration 방지
- [x] CORS 명시 화이트리스트
- [x] HTTPS 강제 (Cloudflare 자동)
- [x] 비밀번호 최소 8자
- [x] DB 데이터/코드 디렉토리 분리
- [x] 27/27 pytest 통과
- [ ] Rate limiting (slowapi 도입됨, 적용 보류)
- [ ] HttpOnly cookie (현재 localStorage)
- [ ] Audit log
- [ ] Email verification

---

## 8. 결론

✅ **본 변경은 즉시 운영 가능**:
- 기능적 회귀 0건
- 새로 추가된 보안 보호 11건
- 의도적 트레이드오프 5건 (모두 문서화)
- 단위 + 종단 테스트 100% 통과
