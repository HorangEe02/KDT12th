# 🚀 Session F — Firebase App Hosting 배포 런북

> 작성: 2026-04-17 · Phase 6 Session F 종료 시점
> 전제: 모든 코드 작업 완료 (Session A~E). 이제 **사용자가 직접 실행**하는 배포 단계.

---

## 🎯 배포 목표

| 항목 | 값 |
|---|---|
| 대상 | Next.js 16 앱 (`frontend/`) |
| 플랫폼 | Firebase App Hosting (Cloud Run + Cloud Build + CDN) |
| 프로젝트 | `mini12-310f5` |
| 리전 | `asia-northeast3` (서울) |
| 백엔드 ID | `away-game-companion` |
| 도메인 | `https://away-game-companion--mini12-310f5.us-central1.hosted.app` (기본) |
| 커스텀 도메인 | 선택 (생략 가능) |

---

## 📋 0. 사전 체크 (2분)

```bash
cd "/Volumes/Corsair EX300U Media/00_work_out/01_complete/Phase12"
bash scripts/preflight.sh
```

모든 7개 항목이 ✅ 여야 진행. 실패 시 지시된 파일 수정 후 재실행.

---

## 🔑 1. 인증 확인 (1분)

```bash
# Firebase CLI 로그인 (브라우저 팝업)
firebase login

# 로그인된 계정이 mini12-310f5 에 대한 Editor/Owner 권한 있는지 확인
firebase projects:list | grep mini12-310f5

# gcloud 로그인 (App Hosting 은 내부적으로 gcloud 필요)
gcloud auth login
gcloud config set project mini12-310f5

# Application Default Credentials (로컬 admin SDK 테스트용 - 선택)
gcloud auth application-default login
```

---

## 🏗️ 2. App Hosting 백엔드 생성 (5분 · 1회)

> ⚠️ **macOS 외장 볼륨 사용 시** `ENOENT: uv_cwd` 에러가 간헐적으로 발생할 수 있어요. 볼륨이 언마운트/재마운트된 상태 — 아래처럼 cwd 를 강제로 갱신하세요:
> ```bash
> cd ~ && cd "/Volumes/Corsair EX300U Media/00_work_out/01_complete/Phase12"
> ```

```bash
# 대화형 모드 (권장) — CLI 가 지원되는 region 목록을 제시
firebase apphosting:backends:create --project mini12-310f5
```

대화형 프롬프트 응답:
- **Backend name**: `away-game-companion`
- **Primary region**: 제시된 목록에서 선택
  - **asia-east1** (Taiwan) 또는 **us-central1** (Iowa) 권장 — App Hosting 은 `asia-northeast3` 미지원일 수 있음
- **Web app**: `Create new` 또는 `Skip`
- **Service account**: default (Enter)
- **Root directory**: `./frontend`
- **Live branch / GitHub**: `Skip` (로컬 배포로 진행)

### 비대화형 모드 (CI/CD 용)
```bash
firebase apphosting:backends:create \
  --project mini12-310f5 \
  --backend away-game-companion \
  --primary-region asia-east1 \
  --root-dir ./frontend \
  --non-interactive
```

> ❗ **플래그 주의**: 이 CLI(15.15.0) 는 `--primary-region` 을 씁니다 (`--location` 아님).
> 최신 CLI 업데이트: `npm install -g firebase-tools@latest`

완료 후 확인:
```bash
firebase apphosting:backends:list --project mini12-310f5
```

---

## 🔐 3. Secret Manager 등록 (10분)

각 시크릿을 한 번씩 실행. 값 입력은 **프롬프트** 또는 `--data-file` 로:

```bash
# GEMINI — 필수
firebase apphosting:secrets:set GEMINI_API_KEY --project mini12-310f5
# (프롬프트에 .env 의 GEMINI_API_KEY 값 붙여넣기)

# Kakao — 지도/길찾기 (선택 · 없으면 OSRM 폴백)
firebase apphosting:secrets:set KAKAO_REST_API_KEY --project mini12-310f5
firebase apphosting:secrets:set KAKAO_MOBILITY_API_KEY --project mini12-310f5

# 기상청 / TourAPI
firebase apphosting:secrets:set WEATHER_API_KEY_ENCODED --project mini12-310f5
firebase apphosting:secrets:set TOUR_API_KEY_ENCODED --project mini12-310f5

# Firebase Web SDK 키 (Badges/Share Firestore 활성화 시)
# Firebase 콘솔 → 프로젝트 설정 → 일반 → 웹 앱 에서 복사
firebase apphosting:secrets:set NEXT_PUBLIC_FIREBASE_API_KEY --project mini12-310f5
firebase apphosting:secrets:set NEXT_PUBLIC_FIREBASE_APP_ID --project mini12-310f5
firebase apphosting:secrets:set NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID --project mini12-310f5
```

등록 확인:
```bash
firebase apphosting:secrets:list --project mini12-310f5
```

각 시크릿 등록 시 CLI 가 자동으로 App Hosting 백엔드의 Service Account 에 `roles/secretmanager.secretAccessor` 를 부여한다.

---

## 🚀 4. 초기 배포 (15분 · 빌드 소요)

```bash
cd "/Volumes/Corsair EX300U Media/00_work_out/01_complete/Phase12"

# 로컬 빌드 검증 (5분)
cd frontend && pnpm build && cd ..

# 원격 배포 — Cloud Build 에서 재빌드 (약 5~8분)
firebase deploy --only apphosting --project mini12-310f5
```

CLI 출력 끝에 URL:
```
+  apphosting: away-game-companion deployed
   URL: https://away-game-companion--mini12-310f5.us-central1.hosted.app
```

---

## 🔥 5. Firestore 보안 규칙 배포 (2분)

Badges/Share Firestore 사용 시:

```bash
firebase deploy --only firestore:rules --project mini12-310f5
firebase deploy --only firestore:indexes --project mini12-310f5
```

---

## ✅ 6. 배포 smoke test (5분)

배포 URL (편의상 `$URL` 변수로 export):
```bash
export URL="https://away-game-companion--mini12-310f5.us-central1.hosted.app"
```

### 6-1. 페이지 응답

```bash
for path in "/" "/matches" "/map" "/places" "/ai" "/badges"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$URL$path")
  echo "$path → $code"
done
```
모두 200 기대.

### 6-2. API 엔드포인트

```bash
# predict
curl -s "$URL/api/predict?team=LG&opponent=KT" | head -c 200

# route (Kakao 키 있으면 kakao, 없으면 osrm)
curl -s -X POST "$URL/api/route" \
  -H "Content-Type: application/json" \
  -d '{"origin":[37.5547,126.9707],"destination":[37.2997,127.0097]}' | head -c 300

# chat (Gemini)
curl -s -X POST "$URL/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"id":"1","role":"user","parts":[{"type":"text","text":"안녕"}]}],"filters":{"team":"LG"}}' \
  --max-time 30 | head -c 400
```

### 6-3. 브라우저 UX

1. 랜딩: 팀 카드 클릭 → URL `?team=XX` 반영 + Hero 색상 변경
2. `/matches`: Plotly 게이지 · 막대 렌더
3. `/map`: Leaflet 지도 + 4 레이어 + 경로 폴리라인 (색상으로 소스 구분 확인)
4. `/places`: 구장 선택 → 산점도 + POI 카드
5. `/ai`: "LG vs KT 승률?" 질의 → `predict_win_rate` tool 호출 + 스트리밍
6. `/badges`: 구장 토글 → 방문 수 업데이트 → 새로고침 후 유지 (localStorage / Firestore)
7. 공유 버튼 → 클립보드 URL → 타 브라우저 붙여넣기 → 필터 복원

---

## 🔄 7. 후속 배포 (반복)

코드 수정 후:
```bash
cd "/Volumes/Corsair EX300U Media/00_work_out/01_complete/Phase12"
bash scripts/preflight.sh                        # 1분
firebase deploy --only apphosting --project mini12-310f5   # 5~8분
```

시크릿 값 변경 시:
```bash
firebase apphosting:secrets:set <NAME> --project mini12-310f5
# 새 버전의 시크릿이 다음 배포부터 적용됨
firebase deploy --only apphosting --project mini12-310f5
```

---

## 🗑️ 8. 레거시 Streamlit Cloud Run 정리 (선택)

**결정 필요**: Phase 5 의 Streamlit Cloud Run 서비스 `away-game-companion` (동명 주의) 를
- **유지**: `https://away-game-companion-262552815882.asia-northeast3.run.app` 계속 접근 가능
- **삭제**: 예산 5,000원 절약 + 혼동 방지

### 유지하려면
작업 불필요. Cloud Run 서비스는 그대로 유지.

### 삭제하려면
```bash
# ⚠️ 주의: App Hosting 백엔드 이름이 같으면 안전상 실패할 수 있음 — 다른 이름일 때만 수행
gcloud run services list --project=mini12-310f5 --region=asia-northeast3
gcloud run services delete away-game-companion \
  --project=mini12-310f5 \
  --region=asia-northeast3 \
  --quiet
```

또는 Firebase Hosting 의 과거 Streamlit rewrite 만 제거 (이미 `firebase.json` 에서 제거됨).

---

## 🆘 9. 트러블슈팅

### 9-1. `firebase apphosting:backends:create` 실패
- **원인**: Blaze 플랜 미연결 → Firebase 콘솔에서 결제 계정 연결
- **원인**: API 미활성화 → Cloud Build / Cloud Run / Secret Manager / Artifact Registry API 콘솔에서 "사용" 클릭
- **원인**: `unknown option '--location'` → CLI v15.15.0 는 `--primary-region` 사용
- **원인**: `ENOENT: uv_cwd` (macOS 외장 볼륨) → `cd ~ && cd <project>` 로 cwd 갱신 후 재시도
- **원인**: `asia-northeast3` 미지원 → 대화형 모드로 실행해 지원 region 목록 확인 (보통 `asia-east1` 또는 `us-central1` 선택)

### 9-2. 빌드 실패 "Cannot find module '@ai-sdk/react'"
```bash
cd frontend && pnpm install --frozen-lockfile
```

### 9-3. 배포 후 500 error / "Google Generative AI API key is missing"
`firebase apphosting:secrets:list` 로 시크릿 확인 → 없으면 재등록 → 재배포

### 9-4. 지도 안 보임 (Leaflet CSS 미로드)
`frontend/components/map/leaflet-map.tsx` 에서 `import "leaflet/dist/leaflet.css"` 가 있는지 확인 (현재 있음 · 빌드에서 자동 CSS chunk 로 분리)

### 9-5. 속도 느림 / 첫 요청 지연
Cloud Run 콜드 스타트 — `apphosting.yaml` 의 `minInstances: 1` 로 변경 후 재배포 (요금 증가 주의).

---

## 🏁 10. 최종 체크리스트

- [ ] 배포 URL 200 OK (6 페이지 + 4 API)
- [ ] Gemini 챗봇 응답 정상 (Tool 호출 가능)
- [ ] 지도 렌더 + 폴리라인 표시
- [ ] 공유 URL round-trip 동작
- [ ] Firestore 규칙 배포됨 (Badges 쓰는 경우)
- [ ] README.md 에 배포 URL 업데이트
- [ ] CLAUDE.md Phase 6 완료 표기

---

*작성: 2026-04-17 · Session F 런북*
