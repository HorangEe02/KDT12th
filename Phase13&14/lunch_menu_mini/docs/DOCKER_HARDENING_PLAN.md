# Docker 환경 충돌 해소 및 호스트 Ollama 통합 — 상세 구현 계획서

> **목표**: Mac 네이티브 Ollama(Metal GPU 가속)를 기본 채택하고, 다른 Docker Compose 프로젝트와 동시 실행 시 발생하는 포트·볼륨·네트워크·메모리 충돌을 제거한다.
>
> **범위**: `docker-compose.yml`, `.env.example`, `docker/bootstrap.sh`, `docs/RUN_LOCAL.md`. 애플리케이션 코드(Python/TypeScript)는 변경 없음.
>
> **계획 작성일**: 2026-04-29

---

## 1. 현재 상태 진단 (실측)

### 1-1. 검증된 사실
- `docker-compose.yml` 최상단 `name:` 지시어 **부재** → 프로젝트 식별이 디렉터리명에 의존
- 5개 서비스(`ollama`, `lunch-api`, `nlp-api`, `web`, `caddy`) 모두 **profile 없이 무조건 시작**
- 호스트 포트 노출이 **하드코딩**: `11434`, `8000`, `8001`, `3000`, `80`, `443`
- `nlp-api`는 이미 `extra_hosts: host.docker.internal:host-gateway` 설정되어 있음 (✅ 호스트 Ollama 준비 완료)
- `nlp-api.depends_on.ollama: service_healthy` → ollama를 profile로 옵셔널화 시 시작 실패 위험
- 모든 서비스에 **resource limits 없음**
- 볼륨은 `name:` 명시되어 다른 프로젝트와 격리는 OK (`mini-db`, `mini-ollama-models` 등)
- 네트워크 `mini-net`은 다른 프로젝트와 충돌 가능 (`name: mini-net` 하드코딩)
- `OLLAMA_HOST` 디폴트는 컨테이너 모드(`http://ollama:11434`) — 호스트 모드 전환은 .env에서 가능

### 1-2. 충돌 시나리오 우선순위
| # | 충돌 | 발생 빈도 | 영향도 |
|:-:|---|:-:|:-:|
| 1 | Caddy 80/443 점유 (다른 프록시와 동시 실행 불가) | 🔴 높음 | 🔴 치명 |
| 2 | 메모리 압박 — 다른 컨테이너와 합산 시 OOMKill | 🟡 중간 | 🔴 치명 |
| 3 | 호스트 포트 점유(3000/8000/8001) | 🟡 중간 | 🟡 중간 |
| 4 | Ollama 컨테이너가 호스트 11434 점유 | 🟡 중간 | 🟡 중간 |
| 5 | 네트워크명 `mini-net` 충돌 | 🟢 낮음 | 🟢 경미 |

---

## 2. 변경 설계

### 2-1. `docker-compose.yml`

#### A. 프로젝트 네임스페이스
```yaml
name: lunchmenu  # 최상단 추가
```
→ 다른 프로젝트와 자원 격리. `docker compose ls`에서 명확히 식별.

#### B. Profile 도입 — 4종 모드
```
[기본 모드]                docker compose up -d
  → web + lunch-api + nlp-api + caddy (호스트 Ollama 사용)

[Docker Ollama 모드]        docker compose --profile docker-llm up -d
  → 위 + ollama 컨테이너 (Mac에서 Ollama 미설치 시)

[프록시 없음 모드]           docker compose --profile no-proxy up -d
  ※ 실제로는 caddy를 profile에 둬서 기본 빠짐 → 단일 모드로 단순화

[전체 모드]                  docker compose --profile docker-llm --profile proxy up -d
```

**최종 정책:**
- `ollama` → `profiles: ["docker-llm"]` (기본 미시작)
- `caddy` → `profiles: ["proxy"]` (기본 미시작 — LAN 공유 시만 켜기)
- `lunch-api`, `nlp-api`, `web` → 항상 시작

#### C. 변수형 포트 매핑
모든 서비스 포트를 `.env` 변수로 추출:
```yaml
lunch-api:
  ports:
    - "${LUNCH_API_PORT:-8000}:8000"
nlp-api:
  ports:
    - "${NLP_API_PORT:-8001}:8001"
web:
  ports:
    - "${WEB_PORT:-3000}:3000"
ollama:
  ports:
    - "${OLLAMA_PORT:-11434}:11434"
caddy:
  ports:
    - "${HTTP_PORT:-80}:80"
    - "${HTTPS_PORT:-443}:443"
```

#### D. 조건부 depends_on (Profile 안전)
`nlp-api.depends_on`에서 ollama 의존 **제거** — 헬스체크는 nlp-api 자체가 lazy load로 처리하므로 문제없음. 호스트 Ollama 모드에서 컨테이너 ollama가 없어도 동작 가능해야 함.

```yaml
nlp-api:
  depends_on:
    lunch-api:
      condition: service_started
    # ollama 의존 제거: 호스트 Ollama 모드에서 작동하도록
```

#### E. 리소스 제한 명시
```yaml
nlp-api:
  deploy:
    resources:
      limits: { memory: 3G, cpus: "2.5" }
      reservations: { memory: 1.5G }

lunch-api:
  deploy:
    resources:
      limits: { memory: 1G, cpus: "1.5" }

web:
  deploy:
    resources:
      limits: { memory: 768M, cpus: "1.0" }

ollama:
  deploy:
    resources:
      limits: { memory: 8G, cpus: "4.0" }
      reservations: { memory: 4G }
```

⚠️ Compose v2에서 `deploy.resources.limits`는 swarm 모드 외에서도 적용됨 (Docker Desktop 4.x+).

#### F. 네트워크 네임스페이스
```yaml
networks:
  mini:
    name: lunchmenu-net  # 충돌 방지를 위해 프로젝트명 prefix
```

#### G. `OLLAMA_HOST` 기본값 변경
```yaml
nlp-api:
  environment:
    # 기본을 호스트 Ollama로 전환 (Mac 사용자 다수 케이스)
    - OLLAMA_HOST=${OLLAMA_HOST:-http://host.docker.internal:11434}
```

### 2-2. `.env.example`

새 변수 추가:
```bash
# -----------------------------------------------------------------------------
# Docker 포트 매핑 (충돌 방지용)
# -----------------------------------------------------------------------------
WEB_PORT=3000
LUNCH_API_PORT=8000
NLP_API_PORT=8001
OLLAMA_PORT=11434
HTTP_PORT=80
HTTPS_PORT=443

# -----------------------------------------------------------------------------
# Ollama 모드 선택
# -----------------------------------------------------------------------------
# 기본: 호스트 Mac에 설치된 Ollama 사용 (Metal GPU 가속, 5–10배 빠름)
#   - brew install ollama && brew services start ollama
#   - ollama pull qwen2.5:7b-instruct
# Docker 컨테이너 ollama를 쓰려면:
#   - docker compose --profile docker-llm up -d
#   - OLLAMA_HOST=http://ollama:11434 으로 변경
OLLAMA_HOST=http://host.docker.internal:11434
```

### 2-3. `docker/bootstrap.sh`

호스트/컨테이너 두 모드 자동 감지:
```bash
# 호스트 Ollama 우선 시도
if curl -fsS http://localhost:11434/api/tags > /dev/null 2>&1; then
  cecho "✅ host Ollama detected (port 11434)"
  MODE="host"
elif docker compose --profile docker-llm ps ollama 2>/dev/null | grep -q running; then
  MODE="docker"
else
  cecho "host Ollama not running. Choose:"
  cecho "  [1] start host Ollama: brew services start ollama"
  cecho "  [2] use docker ollama: docker compose --profile docker-llm up -d ollama"
  exit 1
fi

# 모드별 pull 명령 분기
if [ "$MODE" = "host" ]; then
  ollama pull "$model"
else
  docker compose exec -T ollama ollama pull "$model"
fi
```

### 2-4. `docs/RUN_LOCAL.md`

다음 섹션 추가:
- **Ollama 모드 선택 가이드** (호스트 vs 컨테이너)
- **다중 프로젝트 동시 실행 가이드** (포트 변경 예제)
- **메모리 압박 트러블슈팅** (`docker stats` 확인법)

### 2-5. Caddyfile
변경 없음 (`lunch-api:8000`, `nlp-api:8001`, `web:3000` 컨테이너명 참조는 유지). Caddy가 profile로 옵셔널이 되더라도 활성화 시 동일 동작.

---

## 3. 검증 계획

### 3-1. 정적 검증
1. `docker compose config` — YAML 유효성, 변수 치환 확인
2. `docker compose --profile docker-llm config` — profile 분기 검증
3. `docker compose --profile proxy config` — Caddy 포함 확인

### 3-2. 충돌 시나리오 시뮬레이션
| # | 시나리오 | 검증 명령 |
|:-:|---|---|
| 1 | 기본 모드 (호스트 Ollama) | `WEB_PORT=3010 docker compose up -d` (충돌 없는 포트로) |
| 2 | 다른 프로젝트와 동시 — Caddy 빠짐 | `docker compose up -d` (caddy 미시작 확인) |
| 3 | 호스트 11434 점유 시 docker-llm | `docker compose --profile docker-llm up -d` (포트 매핑 충돌 감지) |
| 4 | nlp-api ↔ host.docker.internal 통신 | `docker compose exec nlp-api curl http://host.docker.internal:11434/api/tags` |

### 3-3. 보안 점검 항목
- [ ] `host.docker.internal` 노출이 의도한 것인가? (호스트 서비스 접근 허용)
- [ ] OLLAMA_HOST 기본값이 외부 IP로 노출되지 않는가? (localhost binding 권장)
- [ ] 새 환경변수가 secrets baseline 트리거하지 않는가?
- [ ] Caddy가 profile로 빠지면 HTTPS 미적용 → LAN 공유 시 경고 문서화
- [ ] 포트를 외부 IP에 바인딩하지 않는가? (모두 default bridge → 안전)
- [ ] 리소스 limits로 OOM이 다른 컨테이너로 전이되지 않는가?

### 3-4. 회귀 테스트 항목
- [ ] `docker compose up -d` 단일 명령으로 4개 서비스 시작
- [ ] `lunch-api` 헬스체크 통과
- [ ] `nlp-api` 헬스체크 통과 (90초 기다림)
- [ ] `web` 헬스체크 통과
- [ ] `nlp-api`에서 호스트 Ollama 호출 성공
- [ ] `--profile proxy` 추가 시 Caddy 정상 라우팅
- [ ] `docker compose down` 정상 종료 (orphan 없음)

---

## 4. 롤백 계획

만약 테스트 실패 시:
1. `docker-compose.yml.bak`, `.env.example.bak`, `bootstrap.sh.bak`로 즉시 복구
2. `docker compose down -v` (볼륨까지 정리)
3. `docker compose up -d` 원상 복귀
4. 문제점을 별도 이슈로 기록

---

## 5. 영향 범위 명시

### 변경됨
- `docker-compose.yml` (1개)
- `.env.example` (1개)
- `docker/bootstrap.sh` (1개)
- `docs/RUN_LOCAL.md` (1개, 섹션 추가)
- `docs/DOCKER_HARDENING_PLAN.md` (NEW, 본 문서)

### 변경 없음
- 모든 Python 코드 (`lunch-optimizer/`, `NLP/`)
- Next.js 코드 (`dashboard-web/`)
- Dockerfiles (`docker/Dockerfile.*`)
- Caddyfile
- CI 워크플로우 (`.github/workflows/`)
- `.env` (사용자 본인 파일 — 본인이 갱신)

### Breaking Changes
- ⚠️ `docker compose up -d` 결과가 달라짐: **Caddy/Ollama 미시작이 기본**
- ⚠️ HTTPS 접근 필요 시 `--profile proxy` 명시 필요
- ⚠️ 호스트에 Ollama 미설치 사용자는 `--profile docker-llm` 명시 필요

→ **마이그레이션 안내**: README 및 RUN_LOCAL.md 상단에 "변경 사항" 박스로 명시.

---

## 6. 예상 작업 시간

| 단계 | 시간 |
|---|:-:|
| 백업 + 패치 | 30분 |
| 검증 (compose config + 시뮬레이션) | 30분 |
| 보안 리뷰 | 15분 |
| 문서화 | 30분 |
| **합계** | **약 1.5–2시간** |
