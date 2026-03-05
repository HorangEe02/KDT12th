#!/bin/bash
# =============================================================================
# Smoking Stroke Analysis - 터미널 실행 스크립트
# =============================================================================

echo "=========================================="
echo "🏥 흡연-뇌졸중 분석 프로젝트 실행"
echo "=========================================="

# 스크립트 위치로 이동
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
echo "📂 작업 디렉토리: $SCRIPT_DIR"

# Python 버전 확인
echo ""
echo "🐍 Python 환경 확인..."
python3 --version

# 가상환경 확인 및 생성
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 가상환경 생성 중..."
    python3 -m venv venv
fi

# 가상환경 활성화
echo "🔄 가상환경 활성화..."
source venv/bin/activate

# 필수 패키지 설치
echo ""
echo "📥 필수 패키지 확인 및 설치..."
pip install --upgrade pip -q

pip install -q \
    pandas \
    numpy \
    matplotlib \
    seaborn \
    scipy \
    statsmodels \
    scikit-learn \
    xgboost \
    imbalanced-learn \
    torch \
    torchvision \
    jupyter \
    nbconvert

echo "✅ 패키지 설치 완료!"

# 데이터 파일 확인
echo ""
echo "📊 데이터 파일 확인..."
if [ -f "data/2020/heart_2020_cleaned.csv" ]; then
    echo "✅ 데이터 파일 발견: data/2020/heart_2020_cleaned.csv"
elif [ -f "heart_2020_cleaned.csv" ]; then
    echo "✅ 데이터 파일 발견: heart_2020_cleaned.csv"
    # data/2020 디렉토리 생성 및 복사
    mkdir -p data/2020
    cp heart_2020_cleaned.csv data/2020/
    echo "   → data/2020/ 폴더로 복사됨"
else
    echo "❌ 데이터 파일을 찾을 수 없습니다!"
    echo "   heart_2020_cleaned.csv 파일을 현재 폴더에 배치해주세요."
    exit 1
fi

# 실행 옵션 선택
echo ""
echo "=========================================="
echo "실행 방식을 선택하세요:"
echo "  1) Jupyter Notebook 실행 (브라우저)"
echo "  2) 터미널에서 직접 실행 (nbconvert)"
echo "  3) Python 스크립트로 변환 후 실행"
echo "=========================================="
read -p "선택 (1/2/3): " choice

case $choice in
    1)
        echo ""
        echo "🚀 Jupyter Notebook 실행..."
        jupyter notebook smoking_stroke_analysis.ipynb
        ;;
    2)
        echo ""
        echo "🚀 노트북 직접 실행 중..."
        jupyter nbconvert --to notebook --execute --inplace smoking_stroke_analysis.ipynb
        echo "✅ 실행 완료! 결과가 노트북에 저장되었습니다."
        ;;
    3)
        echo ""
        echo "🔄 Python 스크립트로 변환 중..."
        jupyter nbconvert --to script smoking_stroke_analysis.ipynb
        echo "🚀 스크립트 실행 중..."
        python3 smoking_stroke_analysis.py
        ;;
    *)
        echo "잘못된 선택입니다. 기본값(1)으로 실행합니다."
        jupyter notebook smoking_stroke_analysis.ipynb
        ;;
esac

echo ""
echo "=========================================="
echo "✅ 완료!"
echo "=========================================="
