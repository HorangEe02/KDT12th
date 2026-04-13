#!/bin/bash
# 헬창지피티 서버 종료
echo "🛑 헬창지피티 서버 종료 중..."

pkill -f "uvicorn api.main:app" 2>/dev/null && echo "  ✅ 백엔드 종료"
pkill -f "vite" 2>/dev/null && echo "  ✅ 프론트엔드 종료"
pkill -f "ngrok" 2>/dev/null && echo "  ✅ ngrok 종료"

echo "✨ 모든 서버가 종료되었습니다."
