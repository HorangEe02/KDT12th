#!/bin/bash
# =============================================================================
# 초기 설정 스크립트 - 1회만 실행
# =============================================================================

echo "=========================================="
echo "🔧 환경 설정 시작"
echo "=========================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. 가상환경 생성
echo ""
echo "📦 가상환경 생성..."
python3 -m venv venv
source venv/bin/activate

# 2. pip 업그레이드
echo ""
echo "⬆️ pip 업그레이드..."
pip install --upgrade pip

# 3. 패키지 설치
echo ""
echo "📥 패키지 설치 중... (시간이 걸릴 수 있습니다)"
pip install -r requirements.txt

# 4. Jupyter 커널 등록
echo ""
echo "📓 Jupyter 커널 등록..."
python -m ipykernel install --user --name=stroke_analysis --display-name="Stroke Analysis (venv)"

# 5. 데이터 폴더 구조 생성
echo ""
echo "📁 데이터 폴더 구조 생성..."
mkdir -p data/2020

# 데이터 파일 이동 (루트에 있는 경우)
if [ -f "heart_2020_cleaned.csv" ] && [ ! -f "data/2020/heart_2020_cleaned.csv" ]; then
    cp heart_2020_cleaned.csv data/2020/
    echo "   → 데이터 파일을 data/2020/으로 복사"
fi

echo ""
echo "=========================================="
echo "✅ 설정 완료!"
echo ""
echo "📌 실행 방법:"
echo "   1. source venv/bin/activate"
echo "   2. jupyter notebook smoking_stroke_analysis.ipynb"
echo ""
echo "   또는: ./run_analysis.sh"
echo "=========================================="
