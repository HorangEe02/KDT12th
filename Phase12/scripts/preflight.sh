#!/usr/bin/env bash
# ============================================================================
# Firebase App Hosting 배포 전 점검 스크립트.
# 실행: bash scripts/preflight.sh
# ============================================================================
set -e
cd "$(dirname "$0")/.."

fail=0
ok()   { echo "  ✓ $1"; }
warn() { echo "  ⚠️  $1"; fail=$((fail+1)); }
err()  { echo "  ✗ $1"; fail=$((fail+1)); }

echo "🔍 [1/7] 비밀 키 .gitignore 패턴 커버 확인 (git 저장소가 아니어도 동작)"
IS_GIT=0
if git rev-parse --git-dir >/dev/null 2>&1; then IS_GIT=1; fi

check_ignore() {
  local target="$1" pattern="$2"
  if [ "$IS_GIT" = "1" ]; then
    git check-ignore "$target" >/dev/null 2>&1
  else
    grep -qE "^$pattern\$" .gitignore 2>/dev/null
  fi
}

for f in .env .env.local frontend/.env.local; do
  if [ -f "$f" ]; then
    base=$(basename "$f")
    if check_ignore "$f" ".env(\\.local)?"; then ok "$f (gitignored pattern 존재)"; else err "$f — NOT gitignored"; fi
  fi
done
if [ -d secrets ]; then
  if check_ignore "secrets" "secrets/"; then ok "secrets/ (gitignored pattern 존재)"; else err "secrets/ — NOT gitignored"; fi
fi

echo
echo "🔍 [2/7] 하드코딩된 API 키 탐색"
HITS=$(grep -rE 'AIza[A-Za-z0-9_-]{30,}' frontend/lib frontend/app frontend/components 2>/dev/null | wc -l | tr -d ' ')
if [ "$HITS" = "0" ]; then ok "소스 코드에 노출된 키 없음"; else err "$HITS 건 탐지 — 확인 필요"; fi

echo
echo "🔍 [3/7] 필수 배포 파일"
for f in frontend/apphosting.yaml firebase.json .firebaserc firestore.rules firestore.indexes.json frontend/package.json; do
  [ -f "$f" ] && ok "$f" || err "MISSING: $f"
done

echo
echo "🔍 [4/7] 데이터 에셋"
for d in frontend/public/data frontend/public/logos; do
  [ -d "$d" ] && ok "$d ($(du -sh "$d" | awk '{print $1}'))" || err "MISSING: $d"
done

echo
echo "🔍 [5/7] Node · pnpm · firebase CLI 버전"
ok "node $(node -v)"
ok "pnpm $(pnpm -v)"
ok "firebase $(firebase --version 2>/dev/null | head -1 || echo '미설치')"

echo
echo "🔍 [6/7] 프로덕션 빌드 가능성 (pnpm build 결과 존재 여부)"
if [ -d frontend/.next ]; then
  ok "frontend/.next/ 존재 ($(du -sh frontend/.next | awk '{print $1}')) — 최근 빌드 확인"
else
  warn "frontend/.next/ 없음 — `pnpm build` 실행 권장"
fi

echo
echo "🔍 [7/7] Firebase 프로젝트 연결"
PROJECT=$(cat .firebaserc | python3 -c "import json,sys; print(json.load(sys.stdin)['projects']['default'])" 2>/dev/null)
ok "project = $PROJECT"

echo
if [ "$fail" = "0" ]; then
  echo "✅ 배포 준비 완료. 다음: docs/SESSION_F_DEPLOY_RUNBOOK.md 따라 진행"
  exit 0
else
  echo "⚠️  $fail 건 경고 — 위 내용 확인 후 재실행"
  exit 1
fi
