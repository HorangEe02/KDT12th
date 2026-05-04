# 외부 공개 배포 — 재평가 및 상세 구현 계획

> **작성일**: 2026-04-29
> **사용자 결정 사항**:
> 1. Firebase 호스팅만 가능하면 충분 — 외부 접속 문제 해결이 핵심
> 2. SSR → 정적 export 다운그레이드 OK
> 3. Auth는 NextAuth + Postgres role 가능 (Firebase Auth 강제 X)
> 4. 기존 일회성 사용자 데이터: 삭제 진행
> 5. 포트 옵션화 OK (이미 항목 3에서 완료)
>
> **프로젝트 목표 재확인**: **최소 비용** + Docker · FastAPI · REST API · 웹 호스팅 학습 가치 보존

---

## 1. 본질 재정의

지금까지 "Firebase 마이그레이션"으로 묶었던 항목 1을 사용자의 진짜 니즈로 분해하면:

| 표면 요구 | 진짜 니즈 |
|---|---|
| Firebase Hosting | 외부 접속 가능한 **공개 URL** |
| Realtime Database | (선택사항 — 강제 아님) |
| 외부 접속 | 친구/포트폴리오 시연용 HTTPS 공유 |

→ **DB와 백엔드는 그대로 두고 프런트엔드만 공개 호스팅하는 것이 정답.** 백엔드는 Cloudflare Tunnel로 무료 노출.

---

## 2. 배포 아키텍처 — 옵션 비교

### 후보 A — **Firebase Hosting + Cloudflare Tunnel (강력 추천)**

```
[브라우저, 어디서나]
        ↓ HTTPS (자동)
[Firebase Hosting]              ← 정적 dashboard-web/out
        ↓ NEXT_PUBLIC_*_API (빌드 타임 주입)
[Cloudflare Tunnel — *.trycloudflare.com or 도메인]
        ↓
[Mac 호스트]
    ├── Caddy (HTTPS 리버스 프록시)
    │     ├── /api/* → lunch-api:8000 (Docker)
    │     └── /nlp/* → nlp-api:8001 (Docker)
    └── Ollama:11434 (호스트, Metal 가속)
```

**비용**: $0 (도메인 미사용 시 `your-app.web.app` + `your-tunnel.trycloudflare.com`)

**학습 가치**:
- ✅ Firebase Hosting (사용자 명시 학습 목표)
- ✅ Next.js 정적 export 빌드 워크플로우
- ✅ Cloudflare Tunnel (실무 가치 매우 높음)
- ✅ CORS 설정, NEXT_PUBLIC 환경변수 관리
- ✅ 기존 Docker/FastAPI/REST 그대로 활용

**제약**:
- Firebase Hosting 무료: 10GB 호스팅, 360MB/일 전송 (충분)
- Mac 항시 가동 (Tunnel은 Mac이 살아있어야 동작)
- Ollama가 호스트라서 다른 Mac으로 마이그레이션 시 모델 재다운 필요

### 후보 B — Vercel + Cloudflare Tunnel
- Firebase 학습 가치 X → 사용자 의도 미충족 → **제외**

### 후보 C — GitHub Pages + Cloudflare Tunnel
- Firebase 학습 가치 X → **제외**

### 후보 D — 모든 것을 PaaS로 (Render/Railway)
- 무료 티어 제약 큼 (Render: 15분 idle 슬립 + 90초 콜드 스타트)
- NLP-api 2.5GB 메모리 → 무료 티어 부족
- Ollama 미지원
- 비용 절감 의도와 어긋남 → **제외**

### ✅ 결정: **후보 A (Firebase Hosting + Cloudflare Tunnel)**

---

## 3. 구현 단계 (총 약 4시간)

### Phase 1 — Next.js 정적 export 변환 (30분)

**파일 변경:**
- `dashboard-web/next.config.ts`
  - `output: "standalone"` → `output: "export"`
  - `trailingSlash: true` 추가 (Firebase Hosting 호환)
  - `images.unoptimized: true` (next/image 미사용이지만 안전망)

**빌드 검증:**
```bash
cd dashboard-web
npm run build
ls out/  # 정적 HTML 파일들 확인
npx serve out  # 로컬에서 테스트
```

**위험**: 거의 없음 (Explore 진단 결과 9개 페이지 모두 클라이언트 컴포넌트)

---

### Phase 2 — Firebase Hosting 프로젝트 설정 (1시간)

**사용자 작업:**
```bash
# Firebase CLI 설치
npm install -g firebase-tools
firebase login

# 프로젝트 생성 (https://console.firebase.google.com → "프로젝트 추가")
# 프로젝트 ID 메모, 예: lunchmenu-mini
```

**파일 생성:**
- `dashboard-web/firebase.json`
  ```json
  {
    "hosting": {
      "public": "out",
      "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
      "cleanUrls": true,
      "trailingSlash": true,
      "headers": [
        {
          "source": "**/*.@(js|css|woff2|svg)",
          "headers": [{"key": "Cache-Control", "value": "public, max-age=31536000, immutable"}]
        }
      ],
      "rewrites": [{"source": "**", "destination": "/index.html"}]
    }
  }
  ```
- `dashboard-web/.firebaserc` (프로젝트 ID 매핑)

**npm scripts 추가** (`package.json`):
```json
{
  "scripts": {
    "deploy": "next build && firebase deploy --only hosting",
    "deploy:preview": "next build && firebase hosting:channel:deploy preview"
  }
}
```

**첫 배포:**
```bash
npm run deploy
# → https://lunchmenu-mini.web.app 발급
```

---

### Phase 3 — Cloudflare Tunnel 백엔드 노출 (1시간)

**사용자 작업:**
```bash
# cloudflared 설치
brew install cloudflared

# 로그인 (Cloudflare 무료 계정 필요 — 가입 즉시 사용 가능)
cloudflared tunnel login

# Tunnel 생성
cloudflared tunnel create lunchmenu

# DNS/공개 주소 설정 — 두 가지 옵션:
# (A) 도메인 보유 시: cloudflared tunnel route dns lunchmenu api.your-domain.com
# (B) 도메인 없을 때: 임시 URL 사용 (트레이드오프: URL 매번 바뀜)
```

**파일 생성:**
- `~/.cloudflared/config.yml`
  ```yaml
  tunnel: lunchmenu
  credentials-file: /Users/yeong/.cloudflared/<tunnel-id>.json

  ingress:
    - hostname: api.your-domain.com
      service: http://localhost:8000
    - hostname: nlp.your-domain.com
      service: http://localhost:8001
    - service: http_status:404
  ```

**또는 Caddy 통합 단일 도메인:**
```yaml
ingress:
  - hostname: lunchmenu.your-domain.com
    service: https://localhost
    originRequest:
      noTLSVerify: true  # Caddy 자체 서명 cert
  - service: http_status:404
```

**서비스 등록 (자동 시작):**
```bash
sudo cloudflared service install
# Mac 부팅 시 자동 실행
```

**대안 (도메인 없을 때): 무료 임시 URL**
```bash
cloudflared tunnel --url http://localhost:8000
# 매 실행마다 새 URL 발급 → 데모용 임시 권장, 시연 시 안 끊기게 유지
```

---

### Phase 4 — CORS/환경변수 동기화 (30분)

**`.env` 갱신:**
```bash
# 백엔드 CORS — Firebase Hosting 도메인 허용
CORS_ORIGINS=https://lunchmenu-mini.web.app,http://localhost:3000
NLP_API_CORS_ORIGINS=https://lunchmenu-mini.web.app,http://localhost:3000

# Kakao Maps allowed origins
KAKAO_KA_ORIGIN=https://lunchmenu-mini.web.app
```

**프런트엔드 빌드 환경변수** (`dashboard-web/.env.production`):
```bash
NEXT_PUBLIC_LUNCH_API=https://api.your-domain.com/api
NEXT_PUBLIC_NLP_API=https://nlp.your-domain.com
NEXT_PUBLIC_DEFAULT_USER_ID=1
NEXT_PUBLIC_KAKAO_MAP_KEY=...
```

**백엔드 재기동:**
```bash
docker compose --profile proxy up -d --force-recreate lunch-api nlp-api
```

---

### Phase 5 — 데이터 정리 (30분)

**일회성 사용자 archive (사용자 결정 #4):**
```bash
docker exec mini-lunch-api python -c "
from database.connection import get_session
from database.models import User
with get_session() as s:
    # 백업 후 삭제
    users = s.query(User).all()
    print(f'삭제 대상: {len(users)}명')
    for u in users:
        print(f'  - {u.id}: {u.name}')
    confirm = input('삭제 확인 (yes/no): ')
    if confirm == 'yes':
        s.query(User).delete()
        s.commit()
        print('완료')
"
```

또는 SQL 직접:
```bash
docker exec mini-lunch-api sqlite3 /app/database/mini.db \
  "DELETE FROM users; DELETE FROM votes; DELETE FROM vote_sessions; DELETE FROM meal_history WHERE user_id IS NOT NULL;"
```

(관련 테이블 의존성 있을 수 있으니 실행 전 확인 필요)

---

### Phase 6 — E2E 검증 (30분)

```bash
# 1. 로컬 정적 빌드 검증
cd dashboard-web && npm run build && npx serve out -p 3001
open http://localhost:3001

# 2. Firebase 프리뷰 채널 배포 (production 영향 없음)
npm run deploy:preview

# 3. 외부 접속 테스트 (휴대폰 셀룰러 데이터로)
# → Firebase URL 접속 → 식당 목록 → 챗봇 → 음식 추천

# 4. 백엔드 응답 확인
curl https://api.your-domain.com/api/health
curl https://nlp.your-domain.com/nlp/health
```

---

## 4. 비용·성능·운영 평가

| 축 | 평가 |
|---|---|
| **비용** | $0 (도메인 없이 .web.app + .trycloudflare.com 조합 시) |
| | $11/년 (선택 — 깔끔한 도메인) |
| **성능** | Firebase Hosting CDN — 전 세계 캐시, 빠름 |
| | Cloudflare Tunnel — 한국 ↔ 사용자 위치에 따라 RTT 50–200ms |
| | Ollama 호스트 Metal — 추론 1–3초 |
| **외부 노출 보안** | Cloudflare 자동 DDoS 방어, HTTPS, 자동 SNI |
| | 백엔드 직접 포트 노출 X (Tunnel만 트래픽 전달) |
| **가용성** | Mac 가동 시 100% (수면/재부팅 시 다운) |
| | 24/7 필요 시 별도 VPS 검토 |
| **학습 가치** | Firebase Console + CLI ✓ |
| | Cloudflare 대시보드 ✓ |
| | Next.js 정적 빌드 + 환경변수 ✓ |
| | 기존 Docker/FastAPI/REST 그대로 ✓ |

---

## 5. 사용자 결정 필요 (Phase 2/3 진행 전)

### 🔵 즉시 답변 필요
1. **도메인 보유 여부**:
   - **있음** → `cloudflared tunnel route dns` 으로 깔끔한 URL
   - **없음** → 임시 `*.trycloudflare.com` URL (매 재시작마다 변경) 또는 도메인 구입

2. **Mac 가동 정책**:
   - 항시 켜둠 가능? → Cloudflare Tunnel + 호스트 Ollama OK
   - 자주 끔 → 별도 클라우드 백엔드 검토 (비용 발생)

3. **Firebase 계정**:
   - 보유 → 즉시 진행
   - 미보유 → Google 계정으로 5분 가입

### 🟢 답변 보류 가능 (실행 단계에서 결정)
4. 일회성 사용자 데이터 삭제 시점 (Phase 5에서 확인 후 진행)
5. 도메인 사용 시 어떤 sub-domain 구조 (`api.x.com` vs `lunchmenu.x.com/api`)

---

## 6. 즉시 시작할 수 있는 작업 (외부 의존 없음)

다음 작업은 사용자 결정 없이 바로 진행 가능:

1. ✅ Phase 1 — Next.js 정적 export 변환 (코드 변경)
2. ✅ Phase 1 — 빌드 + 로컬 정적 서버 검증
3. ✅ Phase 5 일부 — DB 정리 스크립트 작성 (실행은 보류)
4. ✅ Firebase 설정 파일 생성 (deploy 명령은 사용자가 실행)
5. ✅ Cloudflare Tunnel config 템플릿 작성

→ Auto mode 정책에 따라 **위 5개 작업을 즉시 진행**합니다. 외부 계정 발급/도메인 결정은 사용자에게 동시에 묻습니다.

---

## 7. 위험 및 완화 매트릭스

| 위험 | 가능성 | 영향 | 완화 |
|---|:-:|:-:|---|
| 정적 export 시 미발견 SSR 의존성 | 🟢 낮음 | 🟡 중간 | Phase 1 빌드 + 로컬 검증으로 사전 차단 |
| Firebase 무료 한도 초과 (360MB/일 전송) | 🟢 낮음 | 🟢 낮음 | 데모 트래픽 수준에선 도달 불가. 초과 시 Spark→Blaze 전환 |
| Cloudflare Tunnel 끊김 | 🟡 중간 | 🟡 중간 | `cloudflared service install` 자동 재시작. Mac 절전 모드 비활성화 권장 |
| API 키 외부 노출 (`NEXT_PUBLIC_*`) | 🟡 — | 🔴 높음 | Kakao Map JS 키만 NEXT_PUBLIC. **Gemini/REST 키는 백엔드만, NEVER NEXT_PUBLIC** (이미 적용됨) |
| Mac 부팅 시 백엔드 미시작 | 🟡 중간 | 🟢 낮음 | `docker compose up -d` 자동화. 또는 Docker Desktop "Start on login" 옵션 |
| CORS preflight 실패 | 🟢 낮음 | 🟡 중간 | Phase 4에서 `Vary: Origin` + 명시 화이트리스트 |

---

## 8. 산출물 (이 계획 종료 후)

- ✏️ 변경: `dashboard-web/next.config.ts`, `dashboard-web/package.json`, `.env.example`
- 📄 신규: `dashboard-web/firebase.json`, `dashboard-web/.firebaserc.example`, `dashboard-web/.env.production.example`
- 📄 신규: `docs/CLOUDFLARE_TUNNEL.md` (운영 가이드)
- 📄 신규: `scripts/cleanup_test_users.py` (DB 정리 스크립트)
- 📄 갱신: `docs/RUN_LOCAL.md` — 공개 배포 섹션
- 📄 본 문서

---

## 9. 다음 단계

1. (사용자) 위 §5 결정 1·2·3 답변
2. (Claude) §6 의 5개 즉시 작업 진행 → 산출물 커밋
3. (사용자) Firebase + Cloudflare 계정 정리 후 deploy 명령 실행
4. (Claude) E2E 검증 + 보안 점검
