#!/usr/bin/env bash
# ========================================================================
# Phase 5 배포 스크립트 — Cloud Run + Firebase Hosting + Firestore
# ========================================================================
# 사용:
#   bash scripts/deploy.sh            # 전체 배포
#   bash scripts/deploy.sh cloudrun   # Cloud Run 이미지만
#   bash scripts/deploy.sh hosting    # Firebase Hosting rewrite만
#   bash scripts/deploy.sh rules      # Firestore 규칙만
# ========================================================================
set -euo pipefail

PROJECT_ID="${FIREBASE_PROJECT_ID:-mini12-310f5}"
REGION="${GCP_REGION:-asia-northeast3}"
SERVICE_NAME="away-game-companion"
SECRET_GEMINI="gemini-api-key"

log() { printf "\033[1;36m[deploy]\033[0m %s\n" "$*"; }
err() { printf "\033[1;31m[error]\033[0m %s\n" "$*" >&2; }

ensure_gcloud() {
  if ! command -v gcloud >/dev/null 2>&1; then
    err "gcloud CLI 미설치. 설치: brew install --cask google-cloud-sdk"
    exit 1
  fi
}

ensure_firebase() {
  if ! command -v firebase >/dev/null 2>&1; then
    err "firebase CLI 미설치. 설치: npm install -g firebase-tools"
    exit 1
  fi
}

cmd_init_services() {
  log "프로젝트 설정 + 필수 API 활성화"
  gcloud config set project "$PROJECT_ID"
  gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    firestore.googleapis.com \
    secretmanager.googleapis.com \
    storage.googleapis.com \
    artifactregistry.googleapis.com
}

cmd_push_secret() {
  log "Gemini API 키를 Secret Manager에 등록"
  if ! grep -q "GEMINI_API_KEY=" .env; then
    err ".env에 GEMINI_API_KEY가 없습니다."
    exit 1
  fi
  GEMINI_KEY=$(grep '^GEMINI_API_KEY=' .env | head -1 | cut -d= -f2-)
  if [[ -z "$GEMINI_KEY" ]]; then
    err "GEMINI_API_KEY 값이 비어있습니다."
    exit 1
  fi
  if gcloud secrets describe "$SECRET_GEMINI" >/dev/null 2>&1; then
    log "기존 secret 업데이트"
    echo -n "$GEMINI_KEY" | gcloud secrets versions add "$SECRET_GEMINI" --data-file=-
  else
    log "새 secret 생성"
    echo -n "$GEMINI_KEY" | gcloud secrets create "$SECRET_GEMINI" --data-file=- --replication-policy=automatic
  fi
}

cmd_cloudrun() {
  log "Cloud Run 배포 — Cloud Build가 Dockerfile 원격 빌드 (약 3~5분)"
  gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --region "$REGION" \
    --platform managed \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=2 \
    --timeout=300 \
    --min-instances=0 \
    --max-instances=3 \
    --port=8080 \
    --session-affinity \
    --set-env-vars="FIREBASE_PROJECT_ID=$PROJECT_ID,GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION" \
    --set-secrets="GEMINI_API_KEY=$SECRET_GEMINI:latest"
  log "Cloud Run 배포 완료"
  gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format='value(status.url)'
}

cmd_hosting() {
  log "Firebase Hosting rewrite 배포"
  firebase deploy --only hosting --project "$PROJECT_ID"
}

cmd_rules() {
  log "Firestore 규칙 배포"
  firebase deploy --only firestore:rules,firestore:indexes --project "$PROJECT_ID"
}

cmd_upload_rag() {
  log "ChromaDB 스냅샷을 GCS에 업로드 (선택)"
  python3 -m src.db.storage_client
}

cmd_all() {
  ensure_gcloud
  ensure_firebase
  cmd_init_services
  cmd_push_secret
  cmd_cloudrun
  cmd_hosting
  cmd_rules
  log "✅ 전체 배포 완료"
  log "접속 URL: https://${PROJECT_ID}.web.app"
}

main() {
  case "${1:-all}" in
    all) cmd_all ;;
    init) ensure_gcloud && cmd_init_services ;;
    secret) ensure_gcloud && cmd_push_secret ;;
    cloudrun) ensure_gcloud && cmd_cloudrun ;;
    hosting) ensure_firebase && cmd_hosting ;;
    rules) ensure_firebase && cmd_rules ;;
    rag) cmd_upload_rag ;;
    *) err "알 수 없는 명령: $1 (all|init|secret|cloudrun|hosting|rules|rag)"; exit 1 ;;
  esac
}

main "$@"
