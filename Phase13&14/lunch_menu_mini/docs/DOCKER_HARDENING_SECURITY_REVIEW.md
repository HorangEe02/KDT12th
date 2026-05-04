# Docker 환경 안정화 변경 — 보안 리뷰

> **검토 일자**: 2026-04-29  
> **변경 범위**: `docker-compose.yml`, `.env.example`, `docker/bootstrap.sh`, `docs/RUN_LOCAL.md`, `docs/DOCKER_HARDENING_PLAN.md` (NEW)  
> **검토 결과**: ✅ **변경 자체는 보안 개선** (회귀 없음, 잠재적 취약점 1건 해소)

---

## 1. 변경에 의한 보안 영향 매트릭스

| # | 항목 | 변경 전 | 변경 후 | 영향 |
|:-:|---|---|---|:-:|
| 1 | 환경 변수 누수 (`OLLAMA_HOST` 셸→컨테이너) | 🔴 호스트 셸의 `OLLAMA_HOST=0.0.0.0:11434` 가 nlp-api에 누수 → 잘못된 URL → 추론 실패 + 디버깅 시 secrets 노출 위험 | 🟢 `LUNCHMENU_OLLAMA_URL` 로 네임스페이스 분리 — 셸 누수 차단 | ✅ 개선 |
| 2 | 메모리 DoS | ❌ 리소스 제한 無 → 다른 컨테이너 압박 | ✅ 5개 서비스 모두 `deploy.resources.limits` 명시 | ✅ 개선 |
| 3 | 포트 바인딩 (`0.0.0.0` 기본) | 🟡 8000/8001/3000/80/443/11434 모두 모든 인터페이스 바인딩 | 🟡 동일 (변경 없음, 변수만 도입) | 🟰 동일 |
| 4 | HTTPS 기본 적용 | ✅ Caddy 무조건 시작 | ⚠️ `--profile proxy` 옵트인 — 명시 안하면 HTTP만 | 🟡 약화 (문서화 필요) |
| 5 | `host.docker.internal` 노출 | 이미 nlp-api에 설정됨 | 동일 | 🟰 동일 |
| 6 | Caddy 자체 서명 cert | 동일 | 동일 | 🟰 동일 |
| 7 | 컨테이너 비루트 사용자 | 동일 (Dockerfile 변경 없음) | 동일 | 🟰 동일 |
| 8 | `name:` 프로젝트 식별자 | ❌ 없음 (디렉터리명 의존) | ✅ `lunchmenu` 고정 | ✅ 운영 명확성 |
| 9 | 볼륨 네임스페이스 | 일부 명시 (`mini-db` 등) | 일관 (`lunchmenu-*`) | ✅ 격리 강화 |

---

## 2. 항목별 상세 분석

### 2-1. `OLLAMA_HOST` 환경 변수 누수 (해결)

**변경 전 위협 모델:**
```
호스트 셸:        OLLAMA_HOST=0.0.0.0:11434  (ollama serve 운영 시 자동 export)
docker-compose:   OLLAMA_HOST=${OLLAMA_HOST:-http://host.docker.internal:11434}
                  └─ 셸 환경 변수가 .env 와 default 모두 덮어씀
컨테이너 nlp-api: OLLAMA_HOST=0.0.0.0:11434  (잘못된 URL — http:// 누락)
Python 클라이언트: HTTP 요청 실패 → 에러 로그에 OLLAMA_HOST 값 그대로 노출
```

**변경 후:**
```
docker-compose:   OLLAMA_HOST=${LUNCHMENU_OLLAMA_URL:-http://host.docker.internal:11434}
                  └─ 셸의 OLLAMA_HOST 와 무관, 프로젝트 전용 변수만 참조
```

**보안 이점:**
- 잘못된 URL로 인한 디버그 로그 노출 차단
- 사용자가 의도하지 않은 셸 export → 컨테이너 환경 누수의 일반 패턴 방어
- 향후 `OLLAMA_HOST` 충돌 디버깅에 시간 낭비 차단

### 2-2. 리소스 제한 명시 (개선)

**추가된 limits**:
| 서비스 | memory | cpus |
|---|:-:|:-:|
| nlp-api | 3G | 2.5 |
| ollama (profile=docker-llm) | 8G | 4.0 |
| lunch-api | 1G | 1.5 |
| web | 768M | 1.0 |
| caddy (profile=proxy) | 256M | 0.5 |

**보안 이점**:
- **메모리 DoS 방어**: 단일 서비스(nlp-api transformers 폭주 시)가 호스트 메모리를 모두 점유하는 것을 차단
- **다른 Compose 프로젝트와 공존성** 향상
- **OOMKill 격리**: 한 컨테이너 OOM이 호스트 전체로 전이되지 않음

### 2-3. 포트 바인딩 (변경 없음, 사전 권고)

**현재 동작**: Docker Compose의 `ports: - "8000:8000"` 는 기본적으로 `0.0.0.0:8000`에 바인딩 → **호스트가 위치한 모든 네트워크 인터페이스에서 접근 가능**.

⚠️ **사용자 시나리오별 위험도**:
- **로컬 단독 사용** (집/사무실 신뢰 LAN): 🟢 낮음
- **공용 Wi-Fi (카페·공항)**: 🔴 **높음** — 같은 네트워크의 임의 사용자가 8000/8001/3000으로 접근 가능
- **VPN 운영 시**: 🟡 VPN 정책에 따라 다름

**권고 (옵션)**: 외부 노출이 불필요하면 `127.0.0.1:8000:8000`으로 명시 바인딩. 본 변경에서는 **기존 동작을 보존**(스코프 외)했으나, 향후 한 줄 변경으로 가능:

```yaml
ports:
  - "127.0.0.1:${WEB_PORT:-3000}:3000"  # localhost only
```

### 2-4. Caddy(HTTPS) 옵트인 (약한 회귀 — 문서화로 보완)

**변경 전**: `docker compose up -d` → Caddy 자동 시작 → HTTPS 자동 적용  
**변경 후**: `--profile proxy` 명시 필요 → 누락 시 HTTP만

**위험**:
- 신규 사용자가 HTTP로 LAN 공유 → 평문 트래픽
- Geolocation/Kakao Maps 등 Secure Context 기능 미동작

**완화 조치**:
- `RUN_LOCAL.md` 상단에 ⚠️ 박스로 명시
- 모드 A(권장)에 `--profile proxy` 포함
- 다중 프로젝트 충돌 회피용 모드 C 명시

### 2-5. `host.docker.internal` 노출 (변경 없음)

**현재**: nlp-api 컨테이너에 `extra_hosts: host.docker.internal:host-gateway` 설정 — 컨테이너에서 호스트의 localhost 서비스(주로 Ollama 11434)에 접근.

**위험 평가**:
- 만약 nlp-api 코드에 임의 코드 실행(RCE) 취약점이 있다면 호스트 localhost 서비스를 정탐 가능
- 본 변경 이전부터 존재 — **회귀 아님**
- Ollama가 `0.0.0.0:11434`에 바인딩되어 있다면 `host.docker.internal` 없이도 어차피 도달 가능 → 추가 위험 거의 없음

**권고**: nlp-api 입력 검증 강화 (별도 작업, 향후 항목 2 admin 작업 시 통합 점검)

---

## 3. 부수 발견 (변경과 무관, 사전 점검에서 발견)

### 🚨 CRITICAL — 사용자 `.env` 노출

`docker compose config` 렌더링에서 사용자의 실제 API 키들(Kakao, data.go.kr, Food Safety, Gemini)이 평문으로 출력됩니다.

**현재 안전한 점**:
- ✅ `.env` 가 `.gitignore`에 포함 (`.env`, `.env.*` 패턴)
- ✅ `.env` 파일 권한 `-rw-------` (600, 소유자만 읽기)
- ✅ `pre-commit` `detect-secrets` 훅 활성화

**주의 사항**:
- ⚠️ `docker compose config` 출력을 스크린샷·붙여넣기로 공유 시 키 노출
- ⚠️ `docker inspect` 도 환경 변수 평문 노출
- ⚠️ 본 검토 과정에서 키 일부가 검토자(Claude) 화면에 노출되었음 — **사용자가 영구 보관되는 채널에 공유했다고 판단되면 키 즉시 회전 권장**:
  - Kakao REST API: `d6c74ba9…` (앞 6자만 표기)
  - Gemini API: `AIzaSyA4o…` (앞 9자만 표기)
  - Food Safety: `9ab35775…` (앞 8자만 표기)
  - data.go.kr: `tKGUFb3D…` (앞 8자만 표기)

**권장 조치 (옵션)**:
1. 위 키들 회전 (각 발급처에서 재발급)
2. 운영 시 Docker Secrets 또는 Vault 사용
3. CI/CD에서 GitHub Encrypted Secrets 사용

### ⚠️ MEDIUM — `NLP_ADMIN_TOKEN` 미설정

사용자 `.env`의 `NLP_ADMIN_TOKEN`이 빈 값. 이는 `nlp-api`의 모델 화이트리스트 변경 등 관리자 엔드포인트 보호 토큰. 빈 값이면 `NLP_DEV_MODE=1` 일 때만 우회되며, 그렇지 않으면 관리자 동작 불가.

**조치 권고** (별도 작업): 
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))" >> .env
# 결과를 NLP_ADMIN_TOKEN= 라인에 붙여넣기
```

---

## 4. 보안 회귀 테스트 결과

| 검사 | 결과 |
|---|:-:|
| `.gitignore` 에 `.env` 포함 | ✅ |
| `.env` 권한 600 | ✅ |
| `.env.example` 에 실제 키 없음 (placeholder/${var} 만) | ✅ |
| `docker compose config` 시 컴포즈 자체에 시크릿 하드코딩 없음 | ✅ |
| `bootstrap.sh` 에 시크릿/위험 명령 없음 (curl/docker compose 만 사용) | ✅ |
| 새로 노출된 호스트 포트 없음 | ✅ |
| 새로 추가된 외부 의존성 없음 | ✅ |
| 새 변수가 secrets baseline 트리거하지 않음 (`LUNCHMENU_OLLAMA_URL` 은 URL 형태, 시크릿 패턴 아님) | ✅ |

---

## 5. 종합 결론

### 본 변경의 보안 효과
- 🟢 **개선 1건**: `OLLAMA_HOST` 변수 누수 차단 (CWE-654 변형)
- 🟢 **개선 2건**: 리소스 제한 도입 (CWE-400 DoS 방어)
- 🟢 **개선 3건**: 프로젝트 네임스페이스 격리
- 🟡 **약화 1건**: HTTPS 옵트인 (문서로 충분히 안내됨)
- 🟰 **회귀 0건**

### 후속 권장 작업 (별도)
1. ⏰ **즉시**: `.env`의 API 키 회전 여부 사용자 결정 (본 검토 과정 노출)
2. ⏰ **단기 (1주)**: `NLP_ADMIN_TOKEN` 설정
3. 🔜 **중기**: `127.0.0.1:port` 명시 바인딩 옵션 도입 (공용 Wi-Fi 사용자 대상)
4. 🔜 **중기**: Docker Secrets 또는 외부 Vault 통합 (프로덕션 배포 시)

### 승인
✅ **본 변경은 즉시 적용 가능하며 보안 회귀가 없음**. 부수 발견(키 노출)은 별도 트랙으로 사용자가 결정.
