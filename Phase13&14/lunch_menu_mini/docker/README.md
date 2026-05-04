# Mini — Docker Compose 배포

> **Phase 4 완료** — 4개 서비스 (ollama + lunch-api + nlp-api + web) 를 단일 `docker compose up` 으로 기동.

> 📁 **운영 위치 (2026-05-04~)**: `~/Downloads/lunch_menu_mini` (내장 SSD).
> 외장 SSD에서 운영하던 시기에는 Docker bind mount stale(`mkdir /host_mnt/Volumes/...: file exists`)이 빈번해 force-recreate 시마다 `mini-nlp-api`만 시작 실패했고, 이를 해결하기 위해 내장 SSD로 이동했습니다. 마이그레이션 절차와 트러블슈팅 표는 [`../docs/RUN_LOCAL.md`](../docs/RUN_LOCAL.md) "운영 변경 이력" 섹션 참조.

## 구성

| 서비스 | 포트 | 이미지 | 역할 |
|---|---|---|---|
| `ollama` | 11434 | `ollama/ollama:latest` | LLM 런타임 (Qwen 2.5 / Gemma 3 등) |
| `lunch-api` | 8000 | `mini/lunch-optimizer` | FastAPI 음식점/날씨/영양/투표 |
| `nlp-api` | 8001 | `mini/nlp-api` | FastAPI NLP MVP + Research v2 |
| `web` | 3000 | `mini/dashboard-web` | Next.js 16 대시보드 |

**공유 볼륨:**
- `mini-db` — `mini.db` (lunch-api 와 nlp-api 둘 다 접근)
- `mini-chroma` — RAG 벡터 스토어
- `mini-hf` — Hugging Face 모델 캐시 (~1.5GB)
- `mini-ollama-models` — Ollama 모델 blob (~5GB/모델)
- `mini-logs` — 로그 회전

**네트워크:** `mini-net` (bridge) — 컨테이너 끼리는 서비스명으로 통신 (`http://ollama:11434`, `http://lunch-api:8000`).

---

## 빠른 시작

```bash
cd Mini
cp .env.example .env          # API 키 입력
docker compose build          # ~15분 (nlp-api 의 torch/transformers 가 가장 오래 걸림)
./docker/bootstrap.sh         # Ollama 모델 pull
docker compose up -d
docker compose logs -f web    # 실시간 로그
```

브라우저: <http://localhost:3000>

### 첫 빌드 소요 예상 (M1/M2 Mac 기준)
| 단계 | 시간 | 비고 |
|---|---|---|
| Docker 이미지 다운로드 (base) | 2~3분 | python:3.11-slim, node:20-alpine 등 |
| lunch-api 빌드 | 1~2분 | pip 의존성 ~30MB |
| nlp-api 빌드 | 8~12분 | torch CPU ~800MB, transformers 등 |
| web 빌드 | 2~3분 | next build + standalone |
| Ollama 모델 pull (qwen2.5:7b) | 5~10분 | ~4.7GB |
| **총** | **~20~30분** | 이후 빌드는 캐시 덕에 <2분 |

---

## 자주 쓰는 명령

```bash
# 전체 재빌드 (캐시 무시)
docker compose build --no-cache

# 특정 서비스만 재시작
docker compose restart nlp-api

# 로그 따라가기
docker compose logs -f nlp-api

# 컨테이너 안에 쉘 진입
docker compose exec lunch-api bash
docker compose exec nlp-api bash

# Ollama 모델 추가 설치
docker compose exec ollama ollama pull qwen3:4b
docker compose exec ollama ollama list

# 스택 완전 제거 (볼륨까지)
docker compose down -v
```

---

## 환경 변수 매트릭스

| 변수 | 기본값 | 사용 서비스 | 설명 |
|---|---|---|---|
| `KAKAO_REST_API_KEY` | — | lunch-api | 카카오 로컬 검색 |
| `DATA_GO_KR_API_KEY_DECODED` | — | lunch-api | 기상청 + 에어코리아 + 식약처 |
| `SLACK_WEBHOOK_URL` | — | lunch-api | `/api/notify/slack` |
| `OLLAMA_MODEL_CHAT` | `qwen2.5:7b-instruct` | nlp-api | D3 RAG 챗봇 |
| `OLLAMA_MODEL_REPORT` | `qwen2.5:7b-instruct` | nlp-api | D5 NLG 리포트 |
| `NEXT_PUBLIC_LUNCH_API` | `http://localhost:8000/api` | web (build-time) | 브라우저에서 접근할 lunch-api URL |
| `NEXT_PUBLIC_NLP_API` | `http://localhost:8001` | web (build-time) | 브라우저에서 접근할 NLP URL |

> **중요:** `NEXT_PUBLIC_*` 은 **빌드 타임** 에 번들에 박힌다. 프로덕션 배포 시 `docker compose build --build-arg NEXT_PUBLIC_LUNCH_API=https://api.your-domain.com` 식으로 주입할 것.

---

## 헬스체크

모든 서비스에 HTTP 헬스체크가 정의되어 있어 `docker compose ps` 로 상태 확인 가능:

```bash
docker compose ps
# NAME               STATUS
# mini-ollama     Up 2 minutes (healthy)
# mini-lunch-api  Up 2 minutes (healthy)
# mini-nlp-api    Up 1 minute (healthy)
# mini-web        Up 1 minute (healthy)
```

- `lunch-api` — `curl http://127.0.0.1:8000/api/health`
- `nlp-api` — `curl http://127.0.0.1:8001/nlp/health` (start-period 90s for warm-up)
- `web` — `curl http://127.0.0.1:3000`
- `ollama` — `ollama list` 호출 성공 여부

---

## 프로덕션 팁

1. **TLS** — Compose 앞에 Caddy / Traefik / Nginx 리버스 프록시를 두고 3000 포트를 443 으로 노출.
2. **외부 DB** — SQLite 대신 PostgreSQL 로 교체하려면 `lunch-api` `nlp-api` 양쪽의 `MINI_DB_PATH` / `DB_URL` 을 업데이트. 이 경우 `mini-db` 볼륨은 불필요.
3. **GPU Ollama** — Mac 에선 CPU/Metal 이지만 Linux 호스트에선 `docker run --gpus all` 옵션을 추가해야 CUDA 사용. compose 파일 ollama 서비스에 `deploy.resources.reservations.devices` 추가.
4. **CORS** — `NLP_API_CORS_ORIGINS`, `CORS_ORIGINS` env 로 프로덕션 도메인 허용.
5. **빌드 캐시** — CI 에서는 BuildKit + `--cache-from` 으로 nlp-api 의 torch 레이어를 재사용.

---

## 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| `web` 가 API 를 못 찾음 | `NEXT_PUBLIC_*` 미주입 | `docker compose build --build-arg NEXT_PUBLIC_LUNCH_API=...` 로 재빌드 |
| `nlp-api` health check 실패 | Ollama 가 아직 준비 안 됨 | `docker compose logs nlp-api` — start-period 90s 기다리기 |
| `nlp-api` 가 OOM | transformers + torch 가 ~3GB RAM | Docker Desktop 메모리 6GB 이상 할당 |
| Ollama 모델 없음 | `bootstrap.sh` 실행 안 함 | `./docker/bootstrap.sh` 또는 `docker compose exec ollama ollama pull qwen2.5:7b-instruct` |
| `mini-db` 권한 에러 | 바인드 마운트 UID 불일치 | named volume 사용 (현재 기본) |
| `web` 빌드 실패 | `output: "standalone"` 없음 | `dashboard-web/next.config.ts` 에 `output: "standalone"` 추가 (이미 적용됨) |

---

## 이미지 크기 참고

| 이미지 | 크기 | 주요 구성 |
|---|---|---|
| `mini/lunch-optimizer` | ~260 MB | python:3.11-slim + FastAPI + SQLAlchemy |
| `mini/nlp-api` | ~2.5 GB | torch CPU + transformers + sentence-transformers |
| `mini/dashboard-web` | ~180 MB | node:20-alpine + Next.js standalone |
| `ollama/ollama` | ~1 GB | 실행기 (모델 blob은 볼륨 별도) |
| **합계** | **~4 GB** (모델 제외) | |
