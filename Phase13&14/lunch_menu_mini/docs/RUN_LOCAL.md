# 로컬 실행 가이드 (RUN_LOCAL)

`lunch_menu_mini` 프로젝트를 로컬 macOS 환경에서 실행하기 위한 전체 명령 모음입니다.

> 📁 **프로젝트 위치 (기본 가정)** — 이 가이드는 프로젝트 루트가 `~/Downloads/lunch_menu_mini`라고 가정합니다.
> - 2026-05-04 이후 외장 SSD(`/Volumes/Corsair EX300U Media/...`)에서 내장 SSD로 이동 운영 중. Docker bind mount stale·I/O 속도·디렉터리명의 `&` 이스케이프 이슈 해소 목적.
> - 다른 경로(예: `~/work/lunch_menu_mini`)에서 운영하는 경우 본문의 `cd ~/Downloads/lunch_menu_mini` 명령을 본인 경로로 치환하면 됩니다.
> - 코드 베이스(`docker-compose.yml`, `scripts/*`)는 모두 상대경로 기반이라 경로 이동 자체에는 코드 수정이 필요 없습니다.

> ⚠️ **2026-04-29 변경 사항** — Docker Compose 구조를 옵션화했습니다.
> - 기본 `docker compose up -d` 는 **`web` + `lunch-api` + `nlp-api` 3개 서비스만** 시작합니다.
> - **호스트 Mac의 Ollama**(Metal GPU)를 기본으로 사용합니다.
> - **Caddy(HTTPS)** 는 `--profile proxy` 로 옵트인합니다.
> - **컨테이너 Ollama** 는 `--profile docker-llm` 으로 옵트인합니다.
> - 기존 동작이 필요하면: `docker compose --profile docker-llm --profile proxy up -d`
>
> 🔧 **`.env` 마이그레이션 필요** — 기존 사용자는 `.env`에서 다음 변경 권장:
> 1. 기존 `OLLAMA_HOST=...` 라인을 `LUNCHMENU_OLLAMA_URL=...` 로 **이름 변경**
>    (호스트에서 `ollama serve` 운영 시 셸 `OLLAMA_HOST=0.0.0.0:11434` 가 누수되는 문제 차단)
> 2. 새 변수 추가 (선택 — 다른 프로젝트와 포트 충돌 시):
>    ```
>    WEB_PORT=3000
>    LUNCH_API_PORT=8000
>    NLP_API_PORT=8011
>    ```

---

## 🚀 빠른 실행

### 모드 A — 권장 (Mac 호스트 Ollama + HTTPS)

```bash
# 0. 호스트 Ollama 준비 (한 번만)
brew install ollama
brew services start ollama
ollama pull qwen2.5:7b-instruct

# 1. 프로젝트 디렉터리 진입
cd ~/Downloads/lunch_menu_mini

# 2. .env 파일 존재 확인
ls -la .env

# 3. 기본 3개 서비스 + Caddy 기동
docker compose --profile proxy up -d

# 4. healthy 대기 (3개 서비스만 healthcheck 등록)
until [ "$(docker compose ps --format json | grep -c '"Health":"healthy"')" -eq 3 ]; do
  echo "waiting... ($(docker compose ps --format '{{.Name}}\t{{.Status}}'))"
  sleep 5
done
docker compose ps

# 5. 브라우저 접속
open https://localhost
```

### 모드 B — 컨테이너 Ollama (Linux 또는 호스트 Ollama 미설치)

```bash
# .env에서 OLLAMA_HOST 변경
sed -i.bak 's|OLLAMA_HOST=http://host.docker.internal:11434|OLLAMA_HOST=http://ollama:11434|' .env

# 전체 기동 (Ollama + Caddy 포함)
docker compose --profile docker-llm --profile proxy up -d

# 모델 pull
./docker/bootstrap.sh
```

### 모드 C — 최소 모드 (HTTP만, Caddy 없이)

```bash
# 다른 Compose 프로젝트와 80/443 충돌 시 / 로컬 단독 테스트
docker compose up -d
open http://localhost:3000
```

---

## 🧪 동작 검증

```bash
# Caddy HTTPS 진입점 (-k: 자체 서명 cert 무시)
curl -sk -o /dev/null -w "web HTTPS:        %{http_code}\n" https://172.30.1.39/
curl -sk -o /dev/null -w "lunch-api HTTPS:  %{http_code}\n" https://172.30.1.39/api/health
curl -sk -o /dev/null -w "nlp-api HTTPS:    %{http_code}\n" https://172.30.1.39/nlp/health
curl -sk -o /dev/null -w "localhost HTTPS:  %{http_code}\n" https://localhost/

# 디버그용 직접 포트 (HTTP, 컨테이너 직통)
curl -s http://localhost:8000/api/health   ; echo   # lunch-api
curl -s http://localhost:8001/nlp/health   ; echo   # nlp-api
curl -s -o /dev/null -w "web HTTP %{http_code}\n" http://localhost:3000
curl -s http://localhost:11434/api/tags    | head    # ollama 모델 목록
```

### 🌐 권장 접속 (HTTPS via Caddy) — Geolocation/GPS 작동

| 용도 | URL |
|---|---|
| **로컬 PC** | `https://localhost` 또는 `https://172.30.1.39` |
| **LAN 다른 기기 (모바일 포함)** | `https://172.30.1.39` |

### 🛠 디버그용 직접 포트 접근 (HTTP, 컨테이너 직통)

| 서비스 | 로컬 URL | LAN URL |
|---|---|---|
| 대시보드 (Next.js) | http://localhost:3000 | http://172.30.1.39:3000 |
| Lunch API (FastAPI) | http://localhost:8000 | http://172.30.1.39:8000 |
| NLP API (FastAPI) | http://localhost:8001 | http://172.30.1.39:8001 |
| Ollama API | http://localhost:11434 | http://172.30.1.39:11434 |

> ⚠️ **브라우저로는 HTTPS(`https://...`)를 사용할 것.** HTTP + LAN IP는 Secure Context가 아니라 Geolocation/Kakao Maps 등 보안 API가 차단됨.
> ⚠️ `http://0.0.0.0:3000`은 절대 사용 금지 (`0.0.0.0`은 서버 listen 표시이지 클라이언트 주소가 아님, CORS 거부됨).

---

## 🌐 LAN 다른 기기에서 접속 (HTTPS via Caddy)

같은 Wi-Fi에 연결된 노트북·태블릿·스마트폰 브라우저에서:

```
https://172.30.1.39
```

Caddy가 모든 요청을 HTTPS로 종단(Termination)하고 내부적으로 라우팅합니다:
- `/api/*` → `lunch-api:8000`
- `/nlp/*` → `nlp-api:8001`
- `/*` → `web:3000`

### 첫 접속 시 인증서 경고 처리

Caddy의 자체 서명(self-signed) 인증서이므로 첫 접속에서 경고가 표시됩니다:

| 브라우저 | 절차 |
|---|---|
| Chrome/Edge | "고급" → "172.30.1.39(안전하지 않음)으로 이동" |
| Safari (macOS/iOS) | "고급 사항 표시" → "이 웹사이트 방문" |
| Firefox | "고급" → "위험을 감수하고 계속" |

한 번만 통과하면 같은 도메인은 이후 자동 통과됩니다.

### (선택) 인증서 경고를 영구 제거 — Caddy root CA 신뢰 추가

```bash
# 호스트 macOS에서 root CA 추출
docker exec mini-caddy cat /data/caddy/pki/authorities/local/root.crt > caddy-root.crt

# macOS Keychain에 시스템 신뢰로 추가
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain caddy-root.crt

# 모바일: caddy-root.crt를 AirDrop/이메일로 전송 후
# 설정 → 일반 → VPN 및 기기 관리 → 프로필 설치
# 설정 → 일반 → 정보 → 인증서 신뢰 설정에서 활성화 (iOS)
```

### LAN 접속에 필요한 4가지 설정 (이미 적용됨)

| 항목 | 위치 | 현재 값 |
|---|---|---|
| **Caddy 리버스 프록시** | `Caddyfile` + compose `caddy` 서비스 | 443/80 노출, internal CA |
| **NEXT_PUBLIC_LUNCH_API / NEXT_PUBLIC_NLP_API** | `.env` (빌드 타임 주입) | `https://172.30.1.39/api`, `https://172.30.1.39` |
| **NLP_API_CORS_ORIGINS** | `.env` + `docker-compose.yml` | `172.30.1.39` http/https 포함 |
| **CORS_ORIGINS** (lunch-api) | `.env` | `172.30.1.39` http/https 포함 |

### IP 변경 시 재설정 절차

`172.30.1.39`는 DHCP가 부여한 현재 IP라 Wi-Fi 재연결·라우터 재시작·다른 네트워크 이동 시 변경될 수 있습니다.

```bash
# 1. 새 IP 확인
NEW_IP=$(ipconfig getifaddr en0); echo "NEW_IP=$NEW_IP"

# 2. 다음 4개 파일에서 172.30.1.39 → $NEW_IP로 일괄 치환
#    - .env (CORS_ORIGINS, NLP_API_CORS_ORIGINS, NEXT_PUBLIC_LUNCH_API, NEXT_PUBLIC_NLP_API)
#    - docker-compose.yml (NLP_API_CORS_ORIGINS, line 131)
#    - Caddyfile (호스트 목록 & default_sni)

# 3. web 재빌드 (NEXT_PUBLIC_*는 빌드 타임에 번들에 박힘)
cd ~/Downloads/lunch_menu_mini
docker compose build web

# 4. 영향받는 서비스 재기동
docker compose up -d --force-recreate web nlp-api lunch-api caddy
```

> **견고한 운영 팁**: 라우터에서 호스트 MAC에 고정 IP(DHCP 예약)를 할당하면 IP가 바뀌지 않아 위 재빌드가 불필요해집니다.

### 🔒 LAN 접속 보안 주의

- LAN 내 모든 기기에서 접근 가능 (방화벽 미적용 시)
- 외부 인터넷에 노출하려면 공식 도메인 + Let's Encrypt cert + 인증(Auth0/OAuth) 추가 필수
- `.env`의 API 키들이 LAN 다른 기기에 노출될 수 있으니 신뢰 가능한 네트워크에서만 사용
- 자체 서명 cert는 *진짜 도메인 신원 검증*을 하지 않음 — LAN 내 mitm 공격에는 취약 (운영 환경에서는 정식 cert 사용)

---

## 🆕 처음부터 셋업 (이미지·모델 없을 때)

```bash
cd ~/Downloads/lunch_menu_mini

# 1. 환경 변수 설정 (이미 있으면 스킵)
[ -f .env ] || cp .env.example .env
# ⚠️ .env 열어서 KAKAO_REST_API_KEY, NEXT_PUBLIC_KAKAO_MAP_KEY 등 API 키 입력

# 2. 이미지 빌드 (~15~20분, M1 Mac 기준)
docker compose build

# 3. Ollama 모델 pull (~5~10분, qwen2.5:7b ~4.7GB)
./docker/bootstrap.sh

# 4. 전체 기동
docker compose up -d

# 5. 로그 확인
docker compose logs -f web
```

### 첫 빌드 소요 예상 (M1/M2 Mac 기준)

| 단계 | 시간 | 비고 |
|---|---|---|
| Docker 이미지 다운로드 (base) | 2~3분 | python:3.11-slim, node:20-alpine |
| lunch-api 빌드 | 1~2분 | pip 의존성 ~30MB |
| nlp-api 빌드 | 8~12분 | torch CPU ~800MB, transformers |
| web 빌드 | 2~3분 | next build + standalone |
| Ollama 모델 pull (qwen2.5:7b) | 5~10분 | ~4.7GB |
| **총** | **~20~30분** | 이후 빌드는 캐시 덕에 <2분 |

---

## 📋 자주 쓰는 운영 명령

```bash
cd ~/Downloads/lunch_menu_mini

# 상태 확인
docker compose ps

# 실시간 로그 (특정 서비스)
docker compose logs -f nlp-api

# 특정 서비스만 재시작
docker compose restart web

# 컨테이너 안에서 쉘 진입
docker compose exec lunch-api bash
docker compose exec nlp-api bash

# Caddy 설정 검증 + 재로드 (Caddyfile 수정 후)
docker compose exec caddy caddy validate --config /etc/caddy/Caddyfile
docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile
docker compose logs caddy --tail 30

# Caddy root CA 추출 (인증서 신뢰 추가용)
docker exec mini-caddy cat /data/caddy/pki/authorities/local/root.crt > caddy-root.crt

# Ollama 모델 추가 설치
docker compose exec ollama ollama pull gemma2:9b
docker compose exec ollama ollama list

# 전체 재빌드 (캐시 무시)
docker compose build --no-cache

# 전체 종료 (볼륨 보존)
docker compose down

# 전체 종료 + 데이터 완전 삭제 (⚠️ 주의)
docker compose down -v
```

---

## 📁 현재 환경 요약

| 항목 | 값 |
|---|---|
| 프로젝트 경로 | `~/Downloads/lunch_menu_mini` (내장 SSD; 외장 SSD 원본 별도 보존) |
| Compose 프로젝트명 | `lunch_menu_mini` (폴더명에서 자동 유도) |
| 빌드된 이미지 | `mini/dashboard-web`, `mini/lunch-optimizer`, `mini/nlp-api`, `caddy:2-alpine` |
| 보존된 볼륨 | `mini-db`, `mini-logs`, `mini-chroma`, `mini-hf`, `mini-ollama-models`, `mini-caddy-data`, `mini-caddy-config` |
| 호스트 LAN IP | `172.30.1.39` (en0/Wi-Fi, DHCP) |
| HTTPS 진입점 | `https://172.30.1.39` 또는 `https://localhost` (포트 443, Caddy) |
| 웹 번들 박힌 API | `https://172.30.1.39/api`, `https://172.30.1.39` |
| LLM Provider (chat/report/tools) | **gemini** (Phase 14 디폴트), Settings UI에서 ollama 토글 가능 |
| Gemini 모델 | `gemini-2.5-pro` (chat/report/tools 모두) |

---

## 🤖 LLM Provider 설정 (Phase 14)

`AI 상담`(`/concierge`), 주간 NLG 리포트, Tool Calling 모두 **Google Gemini 2.5 Pro API**를 디폴트로 사용합니다. Ollama로의 폴백/토글도 가능합니다.

### `.env`에서 토글

```bash
# Gemini API Key (필수, 발급: https://aistudio.google.com/app/apikey)
GEMINI_API_KEY=YOUR_KEY_HERE
GEMINI_MODEL_CHAT=gemini-2.5-pro       # 품질 우선
GEMINI_MODEL_REPORT=gemini-2.5-pro
GEMINI_MODEL_TOOLS=gemini-2.5-pro

# Provider 선택 (기능별 분리, gemini | ollama)
LLM_PROVIDER_CHAT=gemini    # AI 상담 (/nlp/chatbot/chat, /chat/stream)
LLM_PROVIDER_REPORT=gemini  # 주간 리포트 (/nlp/reports/weekly/...)
LLM_PROVIDER_TOOLS=gemini   # Tool Calling (/nlp/chatbot/chat/tools)
```

### UI에서 토글

`Settings 패널` → `LLM Model` 섹션에서:
- **role 토글**: chat / report / tools / both / all
- **모델 dropdown**: `[gemini] gemini-2.5-pro` / `[ollama] qwen3.5:9b` 등 provider 뱃지 포함 표시
- 선택 후 `Apply to <role>` 클릭 → 즉시 반영 (프로세스 env 덮어쓰기 + 세션 캐시 invalidate)

> ⚠️ UI 변경은 **프로세스 로컬**입니다. nlp-api 컨테이너 재기동 시 `.env` 기본값으로 복귀.

### 환경변수 적용 후 재기동

```bash
cd ~/Downloads/lunch_menu_mini
docker compose up -d --force-recreate nlp-api
```

### 보안 주의

- ⚠️ **`GEMINI_API_KEY`는 절대 `NEXT_PUBLIC_*`로 노출 금지** — 브라우저 번들에 박히면 키 유출
- 백엔드(nlp-api)에서만 사용, 프론트는 `/nlp/chatbot/*`만 호출
- `.env`는 `.gitignore`에 등록되어 Git 커밋 안 됨 ✓

### 비용

- Gemini 2.5 Pro 가격(2026년 4월 기준): 입력 ~$1.25/1M tokens, 출력 ~$10/1M tokens (free tier 제한적)
- 챗봇 1회 호출 ≈ 1-3K tokens 입력 + 0.5-1K tokens 출력
- 백엔드 rate limit: `@rate_limit("10/minute")` 챗봇, `3/minute` 리포트 재생성

### 빠른 검증

```bash
# 통합 모델 목록 (Ollama + Gemini)
curl -sk https://172.30.1.39/nlp/models | python3 -m json.tool

# 활성 provider 확인
curl -sk https://172.30.1.39/nlp/settings | python3 -m json.tool

# Gemini 챗봇 직호출
curl -sk -X POST https://172.30.1.39/nlp/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"query":"오늘 점심 한식 추천해줘"}' | python3 -m json.tool
```

---

## 🧱 서비스 구성

| 서비스 | 컨테이너명 | 포트 | 이미지 | 역할 |
|---|---|---|---|---|
| `caddy` | `mini-caddy` | 80, 443 | `caddy:2-alpine` | HTTPS 리버스 프록시 + 자체 서명 cert (internal CA) |
| `ollama` | `mini-ollama` | 11434 | `ollama/ollama:latest` | LLM 런타임 (Qwen 2.5 / Gemma 등) |
| `lunch-api` | `mini-lunch-api` | 8000 | `mini/lunch-optimizer` | FastAPI 음식점/날씨/영양/투표 |
| `nlp-api` | `mini-nlp-api` | 8001 | `mini/nlp-api` | FastAPI NLP MVP + Research v2 |
| `web` | `mini-web` | 3000 | `mini/dashboard-web` | Next.js 16 대시보드 |

**공유 볼륨:**
- `mini-db` — `mini.db` (lunch-api ↔ nlp-api 공용)
- `mini-chroma` — RAG 벡터 스토어
- `mini-hf` — Hugging Face 모델 캐시 (~1.5GB)
- `mini-ollama-models` — Ollama 모델 blob (~5GB/모델)
- `mini-logs` — 로그 회전
- `mini-caddy-data` — Caddy internal CA root cert + 발급 cert 저장
- `mini-caddy-config` — Caddy 런타임 설정 자동 저장

**네트워크:** `mini-net` (bridge) — 컨테이너 간에는 서비스명으로 통신 (`http://ollama:11434`, `http://lunch-api:8000`, `http://web:3000`).

**Caddy 라우팅 (Caddyfile 참조):**
- `/api/*` → `lunch-api:8000`
- `/nlp/*` → `nlp-api:8001`
- `/*` → `web:3000`

---

## 🔧 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| **AI 상담 응답 안 옴 / "GEMINI_API_KEY not set"** | `.env`에 키 미입력 또는 placeholder 그대로 | 키 발급 후 `.env`의 `GEMINI_API_KEY` 교체 → `docker compose up -d --force-recreate nlp-api` |
| Gemini auth 401/403 | 키가 잘못되었거나 권한 없음 | https://aistudio.google.com/app/apikey 에서 키 재발급 |
| Gemini quota 초과 | free tier 한도 도달 | 결제 활성화하거나 `LLM_PROVIDER_CHAT=ollama`로 일시 폴백 |
| `/nlp/models`에 gemini 모델 없음 | nlp-api가 google-generativeai 미설치 또는 이전 이미지 | `docker compose build nlp-api && docker compose up -d --force-recreate nlp-api` |
| Settings에서 모델 변경해도 효과 없음 | UI 변경은 프로세스 로컬 (env 덮어쓰기) | 영구 변경은 `.env` 수정 후 컨테이너 재기동 |
| **GPS/Geolocation 미동작 (LAN)** | HTTP + non-localhost는 Secure Context가 아님 → 브라우저가 차단 | `https://172.30.1.39` 사용 (Caddy HTTPS) |
| Caddy cert 경고 | 자체 서명 인증서 | "고급 → 계속 진행" 또는 root CA 신뢰 추가 (위 절차 참조) |
| Caddy cert 경고가 모바일에서 무한 반복 | iOS는 자체 서명 cert를 매 세션 검증 | Caddy root CA를 모바일에 프로필로 설치 + 신뢰 활성화 |
| `tlsv1 alert internal error` (curl) | Caddy가 SNI 없는 IP 요청 처리 안 됨 | Caddyfile에 `default_sni 172.30.1.39` 명시 (이미 적용됨) |
| 포트 443/80 충돌 | 다른 프로세스가 점유 | `lsof -nP -iTCP:443 -sTCP:LISTEN` 확인, 종료 또는 Caddy 포트 변경 |
| `/nlp/models 호출 실패` 알림 | 브라우저가 `0.0.0.0:3000`으로 접속 → CORS 거부 (400) | `https://localhost` 또는 `https://172.30.1.39`로 접속 |
| LAN 다른 기기에서 API 호출 실패 | 웹 번들에 `localhost`가 박혀 있어 그 기기의 localhost 호출 | `.env`의 `NEXT_PUBLIC_*`를 호스트 LAN IP로 설정 후 `docker compose build web` |
| LAN 접속 시 CORS 거부 | CORS 화이트리스트에 LAN IP 미등록 | `.env` `CORS_ORIGINS` / `NLP_API_CORS_ORIGINS`에 `https://<LAN_IP>` 추가 후 `--force-recreate` |
| LAN IP가 바뀜 | DHCP 재할당 | 위 "IP 변경 시 재설정 절차" 참조, 또는 라우터에서 DHCP 예약 설정 |
| Mixed content 차단 | HTTPS 페이지에서 HTTP API 호출 | 모든 `NEXT_PUBLIC_*`를 HTTPS로 통일 (이미 적용됨) |
| `web`가 API를 못 찾음 | `NEXT_PUBLIC_*` 미주입 | `docker compose build --build-arg NEXT_PUBLIC_LUNCH_API=...` 로 재빌드 |
| `nlp-api` health check 실패 | Ollama가 아직 준비 안 됨 | `docker compose logs nlp-api` — start-period 90s 기다리기 |
| `nlp-api`가 OOM | transformers + torch가 ~3GB RAM | Docker Desktop 메모리 6GB 이상 할당 |
| Ollama 모델 없음 | `bootstrap.sh` 실행 안 함 | `./docker/bootstrap.sh` 또는 `docker compose exec ollama ollama pull qwen2.5:7b-instruct` |
| `mini-db` 권한 에러 | 바인드 마운트 UID 불일치 | named volume 사용 (현재 기본) |
| `web` 빌드 실패 | `output: "standalone"` 없음 | `dashboard-web/next.config.ts`에 `output: "standalone"` 추가 (이미 적용됨) |
| 외장 드라이브 경로 인식 실패 | 셸 이스케이프 문제 (`&` · 공백) | 가능한 내장 SSD 경로(`~/Downloads/lunch_menu_mini` 등)로 이동 권장. 외장 유지 시 부모 경로의 `&`·공백을 따옴표로 감쌀 것 |
| `mini-nlp-api`만 컨테이너 시작 실패 (`mkdir /host_mnt/Volumes/...: file exists`) | 외장 SSD 위 bind mount(`./NLP/nlp_research/checkpoints`)에 대한 Docker Desktop VM stale | Docker Desktop GUI에서 `Quit` 후 재시작 → `docker compose --profile proxy up -d`. 재발하면 프로젝트를 내장 SSD로 이동 (이 파일 상단 "프로젝트 위치 (기본 가정)" 참조) |
| Quick tunnel(`*.trycloudflare.com`) URL이 수 시간/일 후 갑자기 끊김 | trycloudflare 익명 quick tunnel은 24~72시간 후 호스트네임이 만료됨 | 새 quick tunnel 발급 후 `./scripts/deploy_demo.sh "<NEW_URL>"` 재실행. 영구 운영은 named tunnel(`docs/CLOUDFLARE_TUNNEL.md`) 권장 |

---

## 📌 참고 사항

- 폴더명이 `04_web_react` → `lunch_menu_mini`로 변경되어 다음 `docker compose up` 시 새 compose 프로젝트로 인식됨
- `container_name`과 named volume이 명시적이라 프로젝트 경로를 옮겨도(외장 → 내장 SSD 등) 기존 데이터(`mini-data`/`mini-chroma`/`mini-hf` 등)는 그대로 매칭되어 데이터 손실 없음
- 2026-05-04 이후 운영 경로는 내장 SSD `~/Downloads/lunch_menu_mini`. 외장 SSD 원본은 백업 용도로 보존 중 (검증 후 정리 가능)

---

## 🔀 다중 Compose 프로젝트 동시 실행

다른 Docker Compose 프로젝트와 동시 실행 시 충돌을 피하는 방법.

### 포트 충돌 해소 — `.env` 변수로 모두 변경 가능

| 변수 | 기본값 | 사용처 |
|---|:-:|---|
| `WEB_PORT` | 3000 | Next.js |
| `LUNCH_API_PORT` | 8000 | FastAPI lunch-optimizer |
| `NLP_API_PORT` | 8001 | FastAPI NLP |
| `OLLAMA_PORT` | 11434 | 컨테이너 Ollama (profile=docker-llm) |
| `HTTP_PORT` | 80 | Caddy (profile=proxy) |
| `HTTPS_PORT` | 443 | Caddy (profile=proxy) |

```bash
# 예: 다른 프로젝트가 3000/8000을 사용 중일 때
echo "WEB_PORT=3010" >> .env
echo "LUNCH_API_PORT=8010" >> .env
echo "NLP_API_PORT=8011" >> .env

# 웹은 NEXT_PUBLIC_* 가 빌드타임 주입이므로 함께 변경 후 재빌드
echo "NEXT_PUBLIC_LUNCH_API=http://localhost:8010/api" >> .env
echo "NEXT_PUBLIC_NLP_API=http://localhost:8011" >> .env
docker compose build web
docker compose up -d
```

### 80/443 포트 충돌 — Caddy 옵트아웃

```bash
# Caddy 미시작 (가장 흔한 충돌 회피)
docker compose up -d  # --profile proxy 생략 → Caddy 안 뜸

# HTTP로 직접 접속
open http://localhost:3000

# ※ Geolocation/Kakao Maps 등 Secure Context 필요 기능은 localhost에서만 동작.
#    LAN 공유가 필요 없으면 이 모드가 가장 충돌 적음.
```

### 메모리 압박 진단

```bash
# 현재 컨테이너 메모리 사용량 실시간
docker stats --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.CPUPerc}}"

# 본 프로젝트 자원 한도 (compose 정의)
#   nlp-api  : 3G  / cpu 2.5
#   ollama   : 8G  / cpu 4.0  (profile=docker-llm)
#   lunch-api: 1G  / cpu 1.5
#   web      : 768M / cpu 1.0
#   caddy    : 256M / cpu 0.5 (profile=proxy)
#
# Mac 24GB + Docker Desktop 12GB 환경에서 다른 프로젝트와 동시 실행 시
# 호스트 Ollama 모드(권장)면 Docker는 ~5GB만 사용 → 여유 충분.
```

### 프로젝트 식별

```bash
# 본 프로젝트는 name: lunchmenu 로 고정됨 → ls에서 명확히 구분
docker compose ls

# 자원 격리:
#   - 네트워크 : lunchmenu-net
#   - 볼륨    : lunchmenu-mini-db, lunchmenu-mini-chroma, ...
```

### 충돌 발생 시 빠른 진단

```bash
# 포트 점유자 확인
lsof -nP -iTCP:3000 -sTCP:LISTEN
lsof -nP -iTCP:443  -sTCP:LISTEN
lsof -nP -iTCP:11434 -sTCP:LISTEN

# 다른 Compose 프로젝트 목록
docker compose ls

# 본 프로젝트만 정리 (다른 프로젝트 영향 없음)
docker compose --profile docker-llm --profile proxy down
```

---

## 🗂 운영 변경 이력 — 인프라/디플로이

### 2026-05-04 — 외장 SSD → 내장 SSD 이동 + Quick tunnel 갱신 자동화

**배경**
- 기존 운영 경로: `/Volumes/Corsair EX300U Media/00_work_out/01_complete/Phase13&14/lunch_menu_mini`
- 증상: `docker compose --force-recreate` 시 `mini-nlp-api`만 마운트 실패
  ```
  error while creating mount source path '/host_mnt/Volumes/Corsair EX300U Media/.../checkpoints':
  mkdir /host_mnt/Volumes/Corsair EX300U Media: file exists
  ```
- 원인: 외장 SSD + Docker Desktop VM의 `/host_mnt` 매핑 stale + 디렉터리명의 `&`/공백 이스케이프 취약점이 결합 (다른 컨테이너는 named volume만 써서 영향 없음)

**복구 + 영구 해결 절차** (본 가이드의 표준 운영 위치 = 내장 SSD)

```bash
# 1. 외장 경로의 컨테이너만 정리 (named volume은 보존 — 데이터 무손실)
cd "/Volumes/Corsair EX300U Media/00_work_out/01_complete/Phase13&14/lunch_menu_mini"
docker compose --profile proxy down --remove-orphans

# 2. 내장 SSD로 코드 이동 (node_modules·venv·.next·out·__pycache__ 제외)
mkdir -p ~/Downloads/lunch_menu_mini
rsync -av \
  --exclude='node_modules' --exclude='.next' \
  --exclude='dashboard-web/out' --exclude='dashboard-web/.next' \
  --exclude='dashboard-web/tsconfig.tsbuildinfo' \
  --exclude='__pycache__' --exclude='*.pyc' \
  --exclude='venv' --exclude='.venv' --exclude='.omc' \
  "/Volumes/Corsair EX300U Media/00_work_out/01_complete/Phase13&14/lunch_menu_mini/" \
  "$HOME/Downloads/lunch_menu_mini/"

# 3. dashboard-web 의존성 재설치 (lockfile/package.json 불일치 시 npm install로 lockfile 재생성)
cd ~/Downloads/lunch_menu_mini/dashboard-web && npm install --no-audit --no-fund && cd ..

# 4. 새 경로에서 컨테이너 재빌드 + 기동 (named volume 같은 이름이라 데이터 자동 재마운트)
docker compose --profile proxy up -d --build

# 5. quick tunnel 갱신 + Firebase 데모 재배포 (deploy_demo.sh 한 번)
./scripts/deploy_demo.sh "https://<NEW_TUNNEL>.trycloudflare.com"
```

**Named volume 매핑 (전부 보존됨)**

| Volume | 내용 | 손실 시 비용 |
|--------|------|------|
| `mini-data` | SQLite `mini.db` (음식점 17,402건 등) | 🔴 재크롤링 필요 |
| `mini-chroma` | RAG vector store | 🟡 재인덱싱 |
| `mini-hf` | Hugging Face 모델 캐시 | 🟢 자동 재다운 |
| `mini-ollama-models` | Ollama 모델 blob | 🟢 `bootstrap.sh`로 재설치 |
| `mini-caddy-data` / `-config` | Caddy internal CA | 🟢 자동 재발급 |
| `mini-logs` | 운영 로그 | 🟢 자동 회전 |

→ **`docker compose down`(`-v` 없이)** 만 하면 위 데이터 모두 안전. `-v` 플래그 사용 금지(데이터 wipe).

### 2026-05-04 — Cloudflare Quick Tunnel 만료 대응

**현상**: 데모 배포 후 24~72시간 경과 시 `*.trycloudflare.com` 호스트네임이 NXDOMAIN으로 폐기됨. cloudflared 프로세스는 살아있어도 `control stream encountered a failure while serving` 무한 재시도.

**진단 명령**
```bash
# DNS 만료 여부
nslookup <CURRENT_TUNNEL>.trycloudflare.com   # NXDOMAIN이면 만료

# cloudflared 로그 확인 (백그라운드 시작 시 /tmp/cloudflared.log)
tail -30 /tmp/cloudflared.log | grep -E "Registered|control stream"
```

**복구**
```bash
# 1. 죽은 cloudflared 프로세스 종료
pgrep -f "cloudflared tunnel --url https://localhost:443" | xargs -r kill

# 2. 새 quick tunnel 백그라운드 기동 + URL 캡처
: > /tmp/cloudflared.log
nohup cloudflared tunnel --url https://localhost:443 --no-tls-verify \
  > /tmp/cloudflared.log 2>&1 &
sleep 8
NEW_URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' /tmp/cloudflared.log | head -1)
echo "NEW_URL=$NEW_URL"

# 3. 동일 스크립트로 env/CORS/build/firebase 일괄 갱신
cd ~/Downloads/lunch_menu_mini
./scripts/deploy_demo.sh "$NEW_URL"
```

**영구 해결**: `*.trycloudflare.com` quick tunnel은 만료가 정책. 영구 운영은 Cloudflare 계정의 named tunnel(`docs/CLOUDFLARE_TUNNEL.md`) 또는 도메인 + Let's Encrypt 조합 권장.
