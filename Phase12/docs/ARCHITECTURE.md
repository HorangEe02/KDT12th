# 🏗️ 원정 응원 플래너 — 아키텍처

## 1. 전체 시스템 다이어그램

```mermaid
graph TB
  subgraph Client["👤 사용자 브라우저"]
    UI[Streamlit Web UI]
  end

  subgraph FB["🔥 Firebase Hosting"]
    HOSTING[CDN + *.web.app 도메인]
  end

  subgraph GCP["☁️ Google Cloud"]
    RUN[Cloud Run<br/>Streamlit 컨테이너]
    FS[(Firestore<br/>shared_plans<br/>visited_stadiums<br/>chat_sessions)]
    GCS[Cloud Storage<br/>ChromaDB 스냅샷]
    SM[Secret Manager<br/>GEMINI_API_KEY]
  end

  subgraph LLM["🤖 LLM Layer"]
    OLLAMA[로컬 Ollama<br/>gemma4:e4b]
    GEMINI[Gemini API<br/>2.5-flash-lite]
    MOCK[Mock 응답<br/>시연 안전장치]
  end

  subgraph External["🌐 외부 API"]
    TOUR[한국관광공사 TourAPI]
    KAKAO[카카오 Maps/모빌리티]
    WEATHER[기상청 단기예보]
  end

  UI -->|HTTPS| HOSTING
  HOSTING -->|rewrite| RUN
  RUN <-->|Python SDK| FS
  RUN <-->|Python SDK| GCS
  RUN -->|env| SM
  RUN -->|IS_CLOUD_RUN=True| GEMINI
  RUN -.->|IS_CLOUD_RUN=False| OLLAMA
  RUN -.->|fallback| MOCK
  RUN -->|httpx| TOUR
  RUN -->|httpx| KAKAO
  RUN -->|httpx| WEATHER

  style HOSTING fill:#FFA000,stroke:#FF6F00,color:#fff
  style RUN fill:#4285F4,stroke:#0D47A1,color:#fff
  style FS fill:#FF6D00,stroke:#E65100,color:#fff
  style GCS fill:#34A853,stroke:#1B5E20,color:#fff
  style GEMINI fill:#8E24AA,stroke:#4A148C,color:#fff
  style OLLAMA fill:#546E7A,stroke:#263238,color:#fff
```

## 2. AI 레이어 — 3단계 Fallback

```mermaid
flowchart LR
  Q[사용자 질문] --> D{환경 감지}
  D -->|IS_CLOUD_RUN=False<br/>로컬 개발| O[Ollama<br/>gemma4:e4b]
  D -->|IS_CLOUD_RUN=True<br/>배포| G[Gemini<br/>2.5-flash-lite]
  O -->|실패| G
  G -->|쿼터 초과/오류| M[Mock 응답<br/>사전 녹화 3종]
  O --> R[최종 답변]
  G --> R
  M --> R

  style O fill:#546E7A,color:#fff
  style G fill:#8E24AA,color:#fff
  style M fill:#F57C00,color:#fff
```

## 3. Multi-Agent 오케스트레이션

```mermaid
sequenceDiagram
  participant U as 사용자
  participant S as Supervisor
  participant SC as Schedule Agent
  participant ST as Strategy Agent
  participant P as Place Agent
  participant Y as Synthesizer

  U->>S: "KIA 원정 1박 2일, 아이랑"
  S->>S: JSON 응답으로<br/>호출 에이전트 결정
  S->>SC: schedule 활성화
  SC->>SC: search_game() 도구 호출
  SC-->>Y: 경기 일정 발견
  S->>P: place 활성화
  P->>P: find_places() 도구 호출
  P->>P: search_knowledge() RAG 검색
  P-->>Y: 맛집·숙소·팁 반환
  Y->>U: 통합 답변 생성
```

## 4. 데이터 흐름 — Phase별 누적

| Phase | 데이터 | 저장 위치 |
|---|---|---|
| 1 | KBO 일정·구장·전적 CSV | `data/*.csv` (앱 번들) |
| 1 | POI 캐시 (TourAPI) | `data/poi_cache/*.json` |
| 3 | 카카오 경로 캐시 | `data/route_cache/*.json` (ephemeral) |
| 4 | 승률 예측 모델 | `models/win_rate_model.pkl` (앱 번들) |
| 4 | RAG 인덱스 (ChromaDB) | Cloud Storage `gs://{bucket}/rag/chroma_snapshot.tar.gz` |
| 5 | 사용자 방문 구장 | Firestore `visited_stadiums/{user_id}` |
| 5 | 공유 원정 계획 | Firestore `shared_plans/{plan_id}` |
| 5 | 챗봇 대화 백업 | Firestore `chat_sessions/{session_id}` |

## 5. 요청 처리 순서 (사용자가 앱 접속 시)

1. 브라우저 → `https://mini12-310f5.web.app` → **Firebase Hosting CDN**
2. rewrite rule → `Cloud Run` 컨테이너 (asia-northeast3)
3. 첫 요청 시 **Cold start 5~15초** (컨테이너 부팅 + Streamlit 초기화)
4. 컨테이너 내부:
   - `K_SERVICE` 환경변수 감지 → `IS_CLOUD_RUN=True`
   - `llm_client`가 Gemini로 자동 라우팅
   - Firestore Admin SDK 초기화 (ADC 자동 사용)
   - ChromaDB는 `data/chroma_db/` 부재 시 GCS에서 다운로드
5. Streamlit 앱 렌더 → WebSocket 유지로 인터랙티브 세션

## 6. 비용 아키텍처 (월간 시연 기준)

| 항목 | 무료 tier | 예상 사용량 | 비용 |
|---|---|---|---|
| Firebase Hosting | 10GB 저장, 360MB/일 전송 | < 50MB | $0 |
| Cloud Run | 2M 요청, 180K vCPU-초/월 | ~10K 요청 | $0 |
| Cloud Build | 120분 빌드/일 | 배포당 3분 | $0 |
| Firestore | 50K reads, 20K writes/일 | 시연 수준 | $0 |
| Cloud Storage | 5GB 저장, 1GB 전송 | ~50MB | $0 |
| Secret Manager | 6개 시크릿 무료 | 1개 | $0 |
| Gemini API | 2.5-flash-lite 무료 tier | ~500 호출/일 | $0 |
| **합계** | | | **$0/월** |
