# ====================================================================
# Streamlit + Phase 1~5 전체 앱 컨테이너 (Cloud Run 대상)
# ====================================================================
FROM python:3.11-slim AS base

# 시스템 패키지 (folium/chromadb/빌드 도구용)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 의존성만 먼저 복사하여 레이어 캐싱
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 앱 코드 복사
COPY . .

# Streamlit 디렉토리
RUN mkdir -p ~/.streamlit && echo "\
[server]\n\
headless = true\n\
enableCORS = false\n\
enableXsrfProtection = false\n\
[browser]\n\
gatherUsageStats = false\n\
" > ~/.streamlit/config.toml

# Cloud Run 기본 PORT=8080 수신
ENV PORT=8080
EXPOSE 8080

# 헬스체크 (Cloud Run은 HTTP 200이면 OK)
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
    CMD curl -f http://localhost:${PORT}/_stcore/health || exit 1

CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT} --server.address=0.0.0.0"]
