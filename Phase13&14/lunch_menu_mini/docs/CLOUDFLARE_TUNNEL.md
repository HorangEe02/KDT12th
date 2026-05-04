# Cloudflare Tunnel 운영 가이드

> **목적**: Mac 호스트에서 동작 중인 Docker 백엔드(`lunch-api`, `nlp-api`)를 외부에서 안전하게 접근 가능하도록 노출.
> **비용**: $0 (Cloudflare 무료 계정)
> **전제**: 항목 3 작업으로 Caddy(`--profile proxy`)가 80/443에서 동작 중이거나, 직접 8000/8001 포트 노출.

---

## 0. 준비물

| 항목 | 필수 | 비고 |
|---|:-:|---|
| Cloudflare 계정 | ✅ | 무료, 즉시 가입 가능 (https://dash.cloudflare.com/sign-up) |
| `cloudflared` CLI | ✅ | `brew install cloudflared` |
| 도메인 | ⚠ 선택 | 없으면 임시 `*.trycloudflare.com` URL (재시작마다 변경) |

도메인 권장 이유: Firebase Hosting의 `your-app.web.app` 에서 호출하는 API URL이 매번 바뀌면 CORS 화이트리스트와 빌드 환경변수도 매번 갱신해야 함.

---

## 1. 설치 및 초기 인증 (10분)

```bash
brew install cloudflared
cloudflared --version  # 확인

# Cloudflare 계정에 로그인 (브라우저 자동 열림)
cloudflared tunnel login
```

→ `~/.cloudflared/cert.pem` 생성됨.

---

## 2. 두 가지 경로 — 상황별 선택

### 경로 A — **도메인 보유 시 (권장, 영구 URL)**

도메인 등록처: Cloudflare Registrar(권장, 원가) / 가비아 / Namecheap / Cloudflare 외부 → DNS만 Cloudflare로 위임.

```bash
# Tunnel 생성
cloudflared tunnel create lunchmenu
# → ~/.cloudflared/<TUNNEL_ID>.json 생성됨 (자격증명)
# → 출력에 표시되는 TUNNEL_ID 메모

# DNS 레코드 자동 생성 (옵션 1: 분리 도메인)
cloudflared tunnel route dns lunchmenu api.your-domain.com
cloudflared tunnel route dns lunchmenu nlp.your-domain.com

# 또는 (옵션 2: 단일 도메인 + Caddy 라우팅)
cloudflared tunnel route dns lunchmenu lunchmenu.your-domain.com
```

설정 파일 `~/.cloudflared/config.yml`:

#### 옵션 1 — 분리 도메인 (Caddy 우회, 직접 백엔드 연결)
```yaml
tunnel: <TUNNEL_ID>
credentials-file: /Users/yeong/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: api.your-domain.com
    service: http://localhost:8000
  - hostname: nlp.your-domain.com
    service: http://localhost:8001
  - service: http_status:404
```

#### 옵션 2 — 단일 도메인 + Caddy 통합 (권장)
```yaml
tunnel: <TUNNEL_ID>
credentials-file: /Users/yeong/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: lunchmenu.your-domain.com
    service: https://localhost:443
    originRequest:
      noTLSVerify: true       # Caddy 자체 서명 cert 무시
      originServerName: localhost
  - service: http_status:404
```

옵션 2의 장점: Caddy의 `/api/*`, `/nlp/*` 라우팅이 그대로 외부에 노출됨 → 프런트엔드 환경변수도 `https://lunchmenu.your-domain.com/api`, `/nlp` 단일 도메인으로 단순화.

```bash
# 시작
cloudflared tunnel run lunchmenu

# 또는 macOS 서비스로 등록 (부팅 시 자동 시작)
sudo cloudflared service install
sudo launchctl start com.cloudflare.cloudflared
```

---

### 경로 B — **도메인 없이 임시 URL (데모용, 재시작마다 변경)**

```bash
# Caddy를 통해서 (HTTPS, 단일 진입점)
cloudflared tunnel --url https://localhost:443 --no-tls-verify

# 또는 직접 백엔드 노출
cloudflared tunnel --url http://localhost:8000   # lunch-api 만
```

출력 예:
```
+--------------------------------------------------------------------------------------------+
|  Your quick Tunnel has been created! Visit it at (it may take a few seconds to be reachable):
|  https://random-words-here.trycloudflare.com
+--------------------------------------------------------------------------------------------+
```

이 URL을 `.env.production`의 `NEXT_PUBLIC_LUNCH_API` / `NEXT_PUBLIC_NLP_API`에 입력 후 재빌드+재배포.

⚠ 단점: 프로세스 종료 시 URL 사라짐 → 매번 재빌드 필요.

---

## 3. 동작 확인

```bash
# 외부에서 (또는 셀룰러 데이터로)
curl -i https://api.your-domain.com/api/health
# → HTTP/2 200, {"status":"ok",...} 기대

curl -i https://nlp.your-domain.com/nlp/health
# → HTTP/2 200, NLP 모듈 상태

# Cloudflare Tunnel 로그
tail -f ~/.cloudflared/cloudflared.log
# 또는: launchctl 등록 시
log stream --predicate 'process == "cloudflared"' --info
```

---

## 4. 보안 권장사항

### 4-1. 백엔드 직접 포트(8000/8001) 비공개
- `~/.cloudflared/config.yml` 에서 `service: http://localhost:8000` 으로 지정 → 외부에서 8000 직접 접근 불가
- 추가 안전장치: `lsof -nP -iTCP:8000 -sTCP:LISTEN` 으로 0.0.0.0 바인딩 확인 후 필요시 `127.0.0.1:8000:8000` 으로 제한 (이미 항목 3 후속 권고에 포함)

### 4-2. Cloudflare Access (선택, 무료 50명까지)
- Tunnel 위에 SSO/이메일 OTP 인증 레이어 추가
- `dashboard-web`은 공개, 백엔드 API는 Access로 보호 → 토큰 검증 후만 통과

### 4-3. Rate limiting
- Cloudflare 무료: 페이지 룰 + WAF로 기본 봇 차단
- 본 백엔드는 자체 `slowapi` rate limit 보유 (`NLP_RATE_LIMIT_ENABLED=1`)

### 4-4. `Origin` 헤더 화이트리스트
- 백엔드 CORS_ORIGINS / NLP_API_CORS_ORIGINS 에 Firebase Hosting 도메인만 등록 → CSRF 방어

---

## 5. 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| `connection refused` | 백엔드 컨테이너 미기동 | `docker compose ps` 확인 → `docker compose --profile proxy up -d` |
| 502 Bad Gateway | Tunnel은 살아있지만 백엔드가 죽음 | `docker logs mini-lunch-api` |
| CORS 에러 | 백엔드 CORS_ORIGINS에 Firebase 도메인 미등록 | `.env` 갱신 → `--force-recreate` |
| Mixed content | HTTPS 페이지(`web.app`)에서 HTTP API 호출 | `NEXT_PUBLIC_*_API` 모두 `https://` 로 통일 |
| Mac 절전 → Tunnel 다운 | 절전 모드 진입 시 네트워크 대기 | `caffeinate -dimsu` 또는 시스템 설정 → 절전 → "디스플레이 끌 때 컴퓨터를 자동으로 잠자기 모드로 두지 않기" |
| Tunnel 자동 재시작 실패 | service 등록 안됨 | `sudo cloudflared service install` 재실행 |
| Cloudflare 인증서 만료 | `cert.pem` 1년 만료 | `cloudflared tunnel login` 재실행 |
| 임시 URL 끊김 | quick tunnel 프로세스 종료 | `cloudflared tunnel --url ...` 다시 띄움 |

---

## 6. 비용·한도 참고

| 항목 | 무료 한도 | 본 프로젝트 사용량 |
|---|---|---|
| Cloudflare Tunnel | 트래픽 무제한 | 데모 수준 |
| Cloudflare Access | 50명 / 월 | (사용 시) |
| `*.trycloudflare.com` | 무제한, 임시 URL | 영구 사용 비권장 |
| Cloudflare Pages | 빌드 500회/월 | (이번 계획에선 Firebase 사용) |

---

## 7. 본 프로젝트 권장 조합

### 시연 / 포트폴리오용 (최저 비용)
```
Frontend:  Firebase Hosting (your-app.web.app, 무료)
Backend:   Cloudflare Tunnel quick URL (도메인 없이 시작)
DB:        Mac 호스트의 mini.db (Docker volume)
LLM:       Mac 호스트 Ollama (Metal 가속)
```
**총 비용: $0**

### 정식 운영 (도메인 보유 시)
```
Frontend:  Firebase Hosting + 도메인 CNAME
Backend:   Cloudflare Tunnel + 도메인 (영구 URL)
DB:        동일
LLM:       동일
```
**총 비용: $11/년 (도메인만)**

---

## 8. 참고 링크
- Cloudflare Tunnel 공식: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/
- 무료 Tunnel 한도: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/create-remote-tunnel/
- Firebase Hosting 한도: https://firebase.google.com/docs/hosting/usage-quotas-pricing
