# ✅ Phase 5 배포 체크리스트

배포 전 이 문서를 순서대로 진행하세요. 각 단계 실패 시 해당 섹션의 트러블슈팅을 참고하세요.

---

## 1. 사전 준비 (한 번만)

### 1-1. CLI 설치
```bash
# gcloud CLI (약 3분)
brew install --cask google-cloud-sdk

# firebase-tools (이미 설치됨)
firebase --version

# Docker (이미 설치됨)
docker --version
```

### 1-2. Google/Firebase 로그인
```bash
gcloud auth login                          # 브라우저 열림
gcloud auth application-default login       # ADC 설정
firebase login                              # 브라우저 열림
```

### 1-3. Firebase 프로젝트 확인
```bash
firebase projects:list
# mini12-310f5 이 "(current)"로 표시되어야 함
firebase use mini12-310f5
```

### 1-4. 서비스 활성화 (최초 1회)
```bash
gcloud config set project mini12-310f5
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    firestore.googleapis.com \
    secretmanager.googleapis.com \
    storage.googleapis.com \
    artifactregistry.googleapis.com
```

### 1-5. Firestore 데이터베이스 생성 (최초 1회)
```bash
# 이미 Firebase Console에서 생성했다면 skip
gcloud firestore databases create \
    --location=asia-northeast3 \
    --type=firestore-native
```

### 1-6. Secret Manager에 Gemini 키 등록
```bash
bash scripts/deploy.sh secret
# 또는 수동:
# echo -n "AIza..." | gcloud secrets create gemini-api-key --data-file=- --replication-policy=automatic
```

### 1-7. 서비스 계정 키 (로컬 개발용, 선택)
1. Firebase Console → 프로젝트 설정 → 서비스 계정
2. "새 비공개 키 생성" → JSON 다운로드
3. `secrets/service-account.json` 으로 저장
4. `.env`의 `GOOGLE_APPLICATION_CREDENTIALS=./secrets/service-account.json` 확인

---

## 2. 로컬 검증 (배포 전)

### 2-1. Phase 1~5 게이트 전부 PASS 확인
```bash
python3 scripts/validate_data.py        # Phase 1
python3 scripts/validate_phase2.py      # Phase 2
python3 scripts/validate_phase3.py      # Phase 3
python3 scripts/validate_phase4.py      # Phase 4
python3 scripts/validate_phase5.py      # Phase 5
```

### 2-2. Docker 로컬 빌드 테스트 (선택)
```bash
docker build -t away-game-companion:local .
docker run -p 8080:8080 \
    -e GEMINI_API_KEY="$(grep ^GEMINI_API_KEY= .env | cut -d= -f2-)" \
    -e FIREBASE_PROJECT_ID=mini12-310f5 \
    -e K_SERVICE=local-test \
    away-game-companion:local
# http://localhost:8080 접속 → 탭 1~5 정상 확인
```

---

## 3. 배포 (원클릭)

### 3-1. 전체 자동 배포
```bash
bash scripts/deploy.sh
```

- **Cloud Build가 Dockerfile 원격 빌드** (약 3~5분)
- **Cloud Run 서비스 생성** (asia-northeast3)
- **Firebase Hosting rewrite + Firestore 규칙 배포**

### 3-2. 개별 단계 배포
```bash
bash scripts/deploy.sh init       # 1회만: 서비스 활성화
bash scripts/deploy.sh secret     # Secret Manager에 키 등록
bash scripts/deploy.sh cloudrun   # Cloud Run만 재배포
bash scripts/deploy.sh hosting    # Firebase Hosting rewrite만
bash scripts/deploy.sh rules      # Firestore 규칙만
bash scripts/deploy.sh rag        # ChromaDB → Cloud Storage 업로드
```

### 3-3. RAG 인덱스 업로드 (선택)
```bash
# 로컬에서 인덱스 재구축 후 Cloud Storage 업로드
python3 -m src.ai.rag            # ChromaDB 인덱싱
python3 -m src.db.storage_client  # GCS 업로드
```

---

## 4. 배포 후 확인

### 4-1. URL 접속
```
https://mini12-310f5.web.app
```
**Cold start 5~15초** 기다림. 그 뒤 탭 1~5 확인.

### 4-2. 로그 확인
```bash
gcloud run logs read away-game-companion --region asia-northeast3 --limit 50
```

### 4-3. Firestore 데이터 확인
- Firebase Console → Firestore Database → 데이터
- 테스트 사용자가 뱃지 저장하면 `visited_stadiums/{user_id}` 에 반영

### 4-4. Gemini 호출 확인
- 탭 4에서 "안녕하세요" 입력
- Model 배지에 `gemini-2.5-flash-lite` 표시 확인

---

## 5. 비용 모니터링

```bash
# 월간 청구서 예상
gcloud billing budgets list
```

- **무료 tier**: Cloud Run 2M 요청/월, Firestore 50K reads/일, Gemini 1,500 요청/일
- 초과 시 Firebase Console → 사용량 경고 설정 (결제 알림)

---

## 6. 롤백

### 6-1. Cloud Run 이전 리비전으로
```bash
gcloud run revisions list --service=away-game-companion --region=asia-northeast3
gcloud run services update-traffic away-game-companion \
    --region=asia-northeast3 \
    --to-revisions=away-game-companion-00001-xxx=100
```

### 6-2. 서비스 중지 (긴급)
```bash
gcloud run services update-traffic away-game-companion \
    --region=asia-northeast3 --to-revisions=LATEST=0
```

---

## 7. 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| Cold start 30초+ | `min-instances=0` 기본값 | `gcloud run services update away-game-companion --min-instances=1` (비용↑) |
| Gemini 404 error | 모델 이름 오타 / 쿼터 0 | `.env`의 `GEMINI_CHAT_MODEL=gemini-2.5-flash-lite` 확인 |
| Firestore permission denied | 서비스 계정 권한 없음 | Firebase Console → IAM → "Cloud Datastore 사용자" 역할 추가 |
| Cloud Build 실패 | `.dockerignore`에 꼭 필요한 파일 제외 | `.dockerignore` 확인 + `data/` 일부는 이미지에 필요 |
| 404 on *.web.app | rewrite 잘못됨 | `firebase.json`의 `serviceId`·`region`이 Cloud Run과 일치하는지 |
| 배포 후 "Hello World" | Cloud Run 서비스는 있으나 Streamlit 미실행 | `docker run -p 8080:8080 image` 로컬 테스트부터 |

---

## 8. 발표 직전 Warm-up

```bash
# 2분 전
open https://mini12-310f5.web.app
# 페이지 로드 완료 후 탭 4 한 번 클릭 (AI 프리페치)
```

**시연 모드** 토글도 미리 체크해두기 (사이드바).
