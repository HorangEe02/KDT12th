# 🎤 발표 자료 10장 구성

## 슬라이드 1 — 표지
**원정 응원 플래너 (Away Game Companion)**
> KBO 10개 구단 원정 응원을 위한 AI 기반 여행 큐레이터
>
> 경기 선택 한 번으로 티켓·교통·맛집·숙소·관광 전부 AI가 짜준다.

팀원명·발표일·배포 URL (`https://mini12-310f5.web.app`)

---

## 슬라이드 2 — 문제 정의

### 원정 응원러의 Pain Point
- 경기 일정 → 여행 앱 → 맛집 앱 → 호텔 앱 → 지도 앱 **5개 앱을 왕복**
- 평균 **원정 플래닝 시간 3시간+**
- "광주 가는데 뭐 먹지?" 류의 반복 질문 SNS 폭증

### 현 서비스의 빈틈
- 여행 앱은 **경기 일정**을 모름
- 구단 앱은 **맛집**을 모름
- 챗봇은 **실제 좌표·가격**을 모름

---

## 슬라이드 3 — 시장 근거

- **2024 KBO 상반기 관중 100만 명 돌파** (KBO 공식)
- 고관여 팬 **50%가 MZ세대** (한국프로스포츠협회)
- 2026 시즌: **720경기 × 10구단 × 8개 도시**
- 한국스포츠과학원 2025 트렌드: "팬덤 이코노미", "스포츠 관광"

---

## 슬라이드 4 — 서비스 소개

**원정 응원 플래너** — 5단계 한 번에
1. 응원팀 선택 → 2. 원정 경기 고르기 → 3. AI 코스 생성 → 4. 지도에서 동선 확인 → 5. 뱃지 저장 및 공유

타깃: **MZ 프로야구 원정 응원러** + **지자체** + **숙박·요식업**

---

## 슬라이드 5 — 핵심 기능 시연 (스크린샷)

| 탭 | 기능 | 스크린샷 |
|---|---|---|
| 1 | 승률 게이지 + 구단별 원정 승률 막대 | `/assets/screens/tab1.png` |
| 2 | ⭐ **마커 클릭 → 우측 패널 실시간 UX** | `/assets/screens/tab2.png` |
| 3 | 맛집 거리×평점 산점도 + 카드 | `/assets/screens/tab3.png` |
| 4 | **Multi-Agent 협업 로그** | `/assets/screens/tab4.png` |
| 5 | 10구장 Stadium Tour 뱃지 | `/assets/screens/tab5.png` |

---

## 슬라이드 6 — 기술 아키텍처

```
사용자 → Firebase Hosting → Cloud Run (Streamlit)
                          ↘ Firestore (뱃지·계획)
                          ↘ Cloud Storage (RAG 스냅샷)
                          ↘ Gemini 2.5 Flash Lite (LLM)
                          ↘ Secret Manager (API 키)
```

- **풀 스택 Firebase**: Hosting + Firestore + Rules + Cloud Run rewrite
- **AI 3단계 Fallback**: Ollama(로컬) → Gemini(클라우드) → Mock(안전장치)
- **Multi-Agent**: Supervisor → Schedule/Strategy/Place → Synthesizer
- **Agentic RAG**: 45개 구장 팁 · bge-m3/Gemini 임베딩 · ChromaDB

---

## 슬라이드 7 — 수익 모델 (8단 구조)

1. **티켓 제휴** — 예매 플랫폼 CPC (예: 인터파크 티켓)
2. **숙박 제휴** — 호텔스컴바인·야놀자 CPS
3. **맛집 제휴** — 캐시워크·망고플레이트 쿠폰 CPA
4. **구단 공식 굿즈** — 공식 스토어 링크 수수료
5. **프리미엄 구독** — 연간 코스 추천 + 전용 뱃지 ($4.99/월)
6. **B2B 데이터 라이선스** — 지자체·스포츠브랜드 팬 동선 리포트
7. **광고** — 지역 소상공인 타기팅 배너
8. **이벤트 티켓팅** — 원정 이벤트 자체 기획 (유니폼 드라이브 등)

---

## 슬라이드 8 — 사회적 가치

- 지방 중소도시(광주·대구·창원·수원) **지역경제 활성화**
  - 원정 관중 1인당 평균 지출 **15~30만원** × 720경기 = 연간 **1,000억원+ 시장**
- **스포츠관광 디지털 인프라** 최초 구축
- 한국스포츠과학원 2025 트렌드 과제 "스포츠를 통한 지역경제 활성화"에 직접 기여

---

## 슬라이드 9 — 개발 후기 · 한계

### 배운 점
- **Phase 0~5 순차 설계 + 검증 게이트**로 각 단계 안정성 확보
- **Ollama + Gemini 이중화**로 로컬 개발·클라우드 배포 둘 다 커버
- Streamlit은 **React 버전 병행**을 렌더러 토글로 우아하게 해결

### 한계
- 승률 모델은 더미 데이터 학습 (실제 KBO API 연동 후 재학습 필요)
- POI 평점은 무작위 (TourAPI detailInfo2 연동 예정)
- Cloud Run cold start 5~15초 (min-instances=1로 완화 가능, 비용↑)

---

## 슬라이드 10 — Q&A

### 기대 질문 (사전 준비)
- "실제 야구 팬에게 어떻게 확산할 계획인가요?"
- "경쟁 서비스 대비 차별점은?"
- "Gemini 비용이 늘어나면 어떻게 할지?"
- "Multi-Agent 대신 단일 LLM으로 충분하지 않은가?"

답변 상세: `docs/QA_PREP.md` 참고

---

## 📎 부록 — 배포 URL · GitHub · 팀 소개

- **배포 URL**: https://mini12-310f5.web.app
- **GitHub**: https://github.com/{team}/away-game-companion
- **아키텍처 상세**: `docs/ARCHITECTURE.md`
- **데모 스크립트**: `docs/DEMO_SCRIPT.md`
