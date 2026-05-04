#!/usr/bin/env bash
# Production static export with .env.local guard.
#
# Why: Next.js 의 .env 우선순위 — .env.local 이 항상 마지막에 로드되어
#      .env.production 을 덮어씀 (Next 공식 동작). 로컬 개발용
#      127.0.0.1 URL 들이 실수로 production 번들에 박히는 사고가 있어,
#      production export 동안에는 .env.local 을 잠시 옆으로 치워둔다.
#
# 안전장치: trap 으로 종료 시 항상 원상복구 (성공/실패/Ctrl-C 모두).

set -euo pipefail

cd "$(dirname "$0")/.."

BAK=".env.local.devbak"
HAD_LOCAL=0

restore_env_local() {
  if [ "$HAD_LOCAL" = "1" ] && [ -f "$BAK" ]; then
    mv -f "$BAK" .env.local
  fi
}
trap restore_env_local EXIT INT TERM

if [ -f .env.local ]; then
  HAD_LOCAL=1
  mv -f .env.local "$BAK"
  echo "[build-static] .env.local moved to $BAK during build"
fi

NEXT_OUTPUT=export npx next build
