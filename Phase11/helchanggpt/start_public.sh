#!/bin/bash
# ═══════════════════════════════════════════════
# 헬창지피티 — 공개 서버 실행 스크립트
# Ollama + 백엔드 + 프론트 + ngrok HTTPS
# ═══════════════════════════════════════════════

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "🏋️ 헬창지피티 공개 서버 시작"
echo "📂 프로젝트: $PROJECT_DIR"
echo ""

# ── 1. Ollama 확인 ──
echo "🤖 [1/4] Ollama 확인..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    MODEL_COUNT=$(curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('models',[])))" 2>/dev/null)
    echo "  ✅ Ollama 실행 중 (${MODEL_COUNT}개 모델)"
else
    echo "  ⚠️  Ollama가 실행되지 않았습니다."
    echo "  💡 별도 터미널에서 'ollama serve' 실행 후 다시 시도하세요."
    echo "  💡 또는 Ollama 없이도 데모 모드로 작동합니다."
fi

# ── 2. 백엔드 시작 ──
echo ""
echo "🔧 [2/4] 백엔드 서버 시작 (포트 8002)..."

# 기존 8002 프로세스 정리
lsof -ti :8002 2>/dev/null | xargs kill -9 2>/dev/null
sleep 1

cd "$PROJECT_DIR"
nohup python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8002 --reload > /tmp/helchang-api.log 2>&1 &
API_PID=$!
sleep 3

if curl -s http://localhost:8002/health > /dev/null 2>&1; then
    echo "  ✅ 백엔드 실행 중 (PID: $API_PID)"
else
    echo "  ❌ 백엔드 시작 실패! 로그: cat /tmp/helchang-api.log"
fi

# ── 3. 프론트엔드 시작 ──
echo ""
echo "🎨 [3/4] 프론트엔드 서버 시작 (포트 5173)..."

# 기존 5173 프로세스 정리
lsof -ti :5173 2>/dev/null | xargs kill -9 2>/dev/null
sleep 1

cd "$PROJECT_DIR/frontend"
nohup npx vite --host > /tmp/helchang-web.log 2>&1 &
WEB_PID=$!
sleep 3

if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "  ✅ 프론트엔드 실행 중 (PID: $WEB_PID)"
else
    echo "  ❌ 프론트엔드 시작 실패! 로그: cat /tmp/helchang-web.log"
fi

# ── 4. ngrok 터널 시작 ──
echo ""
echo "🌐 [4/4] ngrok HTTPS 터널 시작..."

# 기존 ngrok 정리
pkill -f ngrok 2>/dev/null
sleep 1

# ngrok 설정 파일 생성 (프론트+백엔드 동시 터널링)
cat > /tmp/ngrok-helchang.yml << 'EOF'
version: 2
tunnels:
  frontend:
    addr: 5173
    proto: http
    inspect: false
  backend:
    addr: 8002
    proto: http
    inspect: false
EOF

# ngrok 유료 플랜이 아니면 동시 터널 불가 → 프론트만 터널링
# 백엔드는 프론트의 vite proxy를 통해 접근
nohup ngrok http 5173 --log=stdout > /tmp/ngrok-helchang.log 2>&1 &
NGROK_PID=$!
sleep 4

# ngrok URL 추출
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
for t in d.get('tunnels',[]):
    if 'https' in t.get('public_url',''):
        print(t['public_url'])
        break
" 2>/dev/null)

if [ -n "$NGROK_URL" ]; then
    echo "  ✅ ngrok 터널 활성화!"
    echo ""
    echo "═══════════════════════════════════════════════"
    echo "🌐 공개 접속 URL (HTTPS):"
    echo ""
    echo "   $NGROK_URL"
    echo ""
    echo "═══════════════════════════════════════════════"
    echo ""
    echo "📋 로컬 접속:"
    echo "   프론트: http://localhost:5173"
    echo "   백엔드: http://localhost:8002"
    echo ""
    echo "🔐 어드민 로그인:"
    echo "   닉네임: admin"
    echo "   비밀번호: helchang2026!"
    echo ""
    echo "🤖 Ollama: http://localhost:11434"
    echo ""
    echo "💡 종료하려면: Ctrl+C 또는 ./stop_public.sh"
else
    echo "  ⚠️  ngrok URL을 가져올 수 없습니다."
    echo "  💡 ngrok 계정이 설정되었는지 확인하세요: ngrok config check"
    echo "  💡 수동 실행: ngrok http 5173"
    echo ""
    echo "📋 로컬 접속은 가능합니다:"
    echo "   프론트: http://localhost:5173"
    echo "   같은 네트워크: http://172.30.1.85:5173"
fi

echo ""
echo "프로세스:"
echo "  백엔드 PID: $API_PID"
echo "  프론트 PID: $WEB_PID"
echo "  ngrok PID:  $NGROK_PID"
echo ""
echo "💪 헬창지피티 서버가 실행 중입니다!"

# 대기 (Ctrl+C로 종료)
wait
