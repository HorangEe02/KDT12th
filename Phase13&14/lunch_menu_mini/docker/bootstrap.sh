#!/usr/bin/env bash
# =============================================================================
# Mini Docker Compose bootstrap
# =============================================================================
# 자동으로 두 가지 Ollama 모드를 감지·지원:
#   [1] 호스트 모드 (권장, Mac Metal GPU 가속)
#       - brew install ollama && brew services start ollama
#       - ollama가 localhost:11434 에서 응답하면 자동 선택
#   [2] Docker 컨테이너 모드
#       - docker compose --profile docker-llm up -d ollama
#       - profile=docker-llm 컨테이너 ollama가 떠 있으면 자동 선택
#
# Usage:
#   ./docker/bootstrap.sh                  # 기본 모델 pull
#   ./docker/bootstrap.sh qwen3:4b         # 추가 모델 지정
#   FORCE_MODE=docker ./docker/bootstrap.sh   # 호스트 무시, 컨테이너 강제
#   FORCE_MODE=host   ./docker/bootstrap.sh   # 컨테이너 무시, 호스트 강제
# =============================================================================
set -euo pipefail

DEFAULT_MODELS=("qwen2.5:7b-instruct")
EXTRA_MODELS=("$@")
HOST_OLLAMA_PORT="${OLLAMA_PORT:-11434}"
HOST_OLLAMA_URL="http://localhost:${HOST_OLLAMA_PORT}"

cecho() { printf "\033[1;32m[bootstrap]\033[0m %s\n" "$*"; }
winfo() { printf "\033[1;36m[bootstrap]\033[0m %s\n" "$*"; }
werr()  { printf "\033[1;31m[bootstrap]\033[0m %s\n" "$*" >&2; }

# -----------------------------------------------------------------------------
# 1. Ollama 모드 감지
# -----------------------------------------------------------------------------
MODE=""

# 사용자 강제 모드
if [[ "${FORCE_MODE:-}" == "host" ]]; then
  MODE="host"
elif [[ "${FORCE_MODE:-}" == "docker" ]]; then
  MODE="docker"
else
  # 자동 감지: 호스트 Ollama 우선
  if curl -fsS "${HOST_OLLAMA_URL}/api/tags" > /dev/null 2>&1; then
    MODE="host"
    winfo "host Ollama detected at ${HOST_OLLAMA_URL}"
  elif docker compose --profile docker-llm ps --services --filter "status=running" 2>/dev/null | grep -q '^ollama$'; then
    MODE="docker"
    winfo "container Ollama detected (profile=docker-llm)"
  else
    werr "no Ollama runtime detected."
    echo
    werr "Choose one:"
    werr "  [1] (recommended on Mac) start host Ollama:"
    werr "      brew install ollama && brew services start ollama"
    werr "  [2] start containerized Ollama:"
    werr "      docker compose --profile docker-llm up -d ollama"
    echo
    werr "Then re-run: ./docker/bootstrap.sh"
    exit 1
  fi
fi

cecho "mode: ${MODE}"

# -----------------------------------------------------------------------------
# 2. Docker 컨테이너 모드: ollama 컨테이너 보장
# -----------------------------------------------------------------------------
if [[ "${MODE}" == "docker" ]]; then
  if ! docker compose --profile docker-llm ps --services --filter "status=running" 2>/dev/null | grep -q '^ollama$'; then
    cecho "starting docker ollama (profile=docker-llm)..."
    docker compose --profile docker-llm up -d ollama
    cecho "waiting 10s for ollama to boot..."
    sleep 10
  fi
fi

# -----------------------------------------------------------------------------
# 3. 모델 pull
# -----------------------------------------------------------------------------
ALL_MODELS=("${DEFAULT_MODELS[@]}" "${EXTRA_MODELS[@]}")

pull_model() {
  local model="$1"
  cecho "pulling: ${model}"
  if [[ "${MODE}" == "host" ]]; then
    if ! command -v ollama > /dev/null 2>&1; then
      werr "host mode but 'ollama' CLI not found. Install: brew install ollama"
      exit 1
    fi
    ollama pull "${model}"
  else
    docker compose --profile docker-llm exec -T ollama ollama pull "${model}"
  fi
}

for m in "${ALL_MODELS[@]}"; do
  pull_model "${m}" || {
    werr "failed to pull ${m}"
    exit 1
  }
done

# -----------------------------------------------------------------------------
# 4. 설치된 모델 목록
# -----------------------------------------------------------------------------
cecho "installed models:"
if [[ "${MODE}" == "host" ]]; then
  ollama list
else
  docker compose --profile docker-llm exec -T ollama ollama list
fi

cecho "✅ bootstrap complete (mode=${MODE})"
echo
echo "Next steps:"
echo "  docker compose up -d                          # default services"
echo "  docker compose --profile proxy up -d          # + Caddy (HTTPS)"
echo "  open http://localhost:${WEB_PORT:-3000}"
