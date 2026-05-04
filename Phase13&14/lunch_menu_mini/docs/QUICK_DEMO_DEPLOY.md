# 5분 임시 데모 배포 가이드 ($0)

> **목표**: 휴대폰 셀룰러 데이터 등 외부에서 접속 가능한 데모 URL 발급. 도메인 없이 무료.
>
> **결과**: `https://<your-project>.web.app` 으로 어디서나 접속.

---

## 0. 사전 준비 (한 번만)

### Mac에 도구 설치
```bash
# Cloudflare Tunnel
brew install cloudflared

# Firebase CLI
npm install -g firebase-tools
```

### Firebase 계정 + 프로젝트 (5분)
```bash
# 1. Google 계정으로 로그인
firebase login

# 2. https://console.firebase.google.com 접속
#    → "프로젝트 추가" 클릭
#    → 이름 예: "lunchmenu-demo" (전 세계 유일해야 함)
#    → 무료 Spark 플랜 선택, Google Analytics 비활성화 가능
#    → 생성된 프로젝트 ID 복사 (예: lunchmenu-demo-a1b2c3)

# 3. 본 프로젝트에 Firebase 프로젝트 ID 등록
cd ~/Downloads/lunch_menu_mini/dashboard-web
cp .firebaserc.example .firebaserc

# .firebaserc 편집 — "default": "your-firebase-project-id" 를 실제 ID로
# 예: "default": "lunchmenu-demo-a1b2c3"
```

### Kakao Maps 도메인 화이트리스트 (선택)
- https://developers.kakao.com → 내 앱 → 플랫폼 → Web
- 사이트 도메인에 `https://lunchmenu-demo-a1b2c3.web.app` 추가

---

## 1. 매 데모 시 실행 (3단계)

### 터미널 ① — Cloudflare Tunnel 시작 (이 창은 켜둔 채로)
```bash
cd ~/Downloads/lunch_menu_mini

# 백엔드는 이미 떠있어야 함 (없으면 먼저 docker compose --profile proxy up -d)

cloudflared tunnel --url https://localhost:443 --no-tls-verify
```

출력 예:
```
2026-04-29T07:30:12Z INF +--------------------------------------------------------------------------------------------+
2026-04-29T07:30:12Z INF |  Your quick Tunnel has been created! Visit it at (it may take a few seconds to be reachable):
2026-04-29T07:30:12Z INF |  https://amber-tiger-bake-flowers.trycloudflare.com                                          |
2026-04-29T07:30:12Z INF +--------------------------------------------------------------------------------------------+
```

→ 위 URL을 복사 (이 창은 닫지 않음).

### 터미널 ② — 배포 스크립트 실행
```bash
cd ~/Downloads/lunch_menu_mini

# 복사한 URL을 인자로 전달
./scripts/deploy_demo.sh https://amber-tiger-bake-flowers.trycloudflare.com
```

스크립트가 자동으로:
1. `dashboard-web/.env.production` 갱신
2. `.env` CORS_ORIGINS / NLP_API_CORS_ORIGINS / KAKAO_KA_ORIGIN 갱신
3. `lunch-api`, `nlp-api` 재기동 (force-recreate)
4. `npm run build` (정적 export)
5. `firebase deploy --only hosting`

배포 완료 출력:
```
✅ 배포 완료

  Frontend : https://lunchmenu-demo-a1b2c3.web.app
  Backend  : https://amber-tiger-bake-flowers.trycloudflare.com
```

### 단계 3 — 외부 접속 테스트
```bash
# 1. Mac 브라우저로 직접
open https://lunchmenu-demo-a1b2c3.web.app

# 2. 휴대폰 (셀룰러 데이터 권장 - LAN 우회 검증):
#    위 URL을 카카오톡 나에게 보내기 → 휴대폰에서 클릭

# 3. 백엔드 응답 확인
curl -i https://amber-tiger-bake-flowers.trycloudflare.com/api/health
curl -i https://amber-tiger-bake-flowers.trycloudflare.com/nlp/health
```

---

## 2. 데모 종료

### 터미널 ① 의 Cloudflare Tunnel 종료
- `Ctrl+C` 한 번
- 백엔드는 외부 접근 불가가 되지만 Firebase Hosting의 정적 사이트는 계속 살아있음 (단, API 호출 실패)

### 데모만 잠시 중지하고 싶을 때
```bash
# Tunnel 종료 후 다시 시작 — URL이 변경되므로 deploy_demo.sh 재실행 필요
```

### Firebase Hosting 사이트를 비공개화
```bash
# 옵션 A: 사이트 비활성화
firebase hosting:disable

# 옵션 B: 다른 콘텐츠로 덮어쓰기 (예: 단순 "데모 종료" 페이지)
```

---

## 3. 자주 발생하는 문제

| 증상 | 원인 | 해결 |
|---|---|---|
| `cloudflared: command not found` | brew 설치 안됨 | `brew install cloudflared` |
| `Error: HTTP Error: 403 Forbidden` (firebase) | Firebase 프로젝트 ID 오타 또는 권한 없음 | `.firebaserc` 확인, `firebase projects:list` |
| `502 Bad Gateway` (Tunnel URL 호출 시) | 백엔드 컨테이너 죽음 | `docker compose ps`, `docker logs mini-lunch-api` |
| 페이지 로딩되지만 데이터 없음 | CORS 불일치 또는 API URL 오타 | `.env.production` 확인, 브라우저 콘솔 Network 탭 |
| Mixed content 차단 | HTTPS 페이지에서 HTTP API 호출 | `NEXT_PUBLIC_*_API` 가 https:// 인지 확인 |
| Mac 절전 → Tunnel 끊김 | 절전 모드 진입 | `caffeinate -dimsu` 또는 시스템 설정에서 절전 비활성화 |
| **Tunnel URL DNS NXDOMAIN (수 시간/일 후 갑자기 끊김)** | trycloudflare 익명 quick tunnel은 24~72시간 후 호스트네임이 만료됨. cloudflared 프로세스 자체는 살아있어도 Cloudflare 엣지에서 재등록 실패 무한 루프 | (1) 죽은 프로세스 `kill <PID>` (2) 새 tunnel 시작 `cloudflared tunnel --url https://localhost:443 --no-tls-verify` (3) 새 URL로 `./scripts/deploy_demo.sh "<NEW_URL>"` 재실행. 영구 해결은 named tunnel(`docs/CLOUDFLARE_TUNNEL.md`) |
| **`mini-nlp-api`만 시작 실패 (`mkdir /host_mnt/Volumes/...: file exists`)** | 외장 SSD 위 bind mount(`./NLP/nlp_research/checkpoints`)에 대한 Docker Desktop VM stale. force-recreate 시 발생 | Docker Desktop UI → `Quit` → 재시작 후 `docker compose --profile proxy up -d`. 재발 시 프로젝트를 내장 SSD(`~/Downloads/lunch_menu_mini` 등)로 이동 — named volume(`mini-data` 등)은 자동 보존되어 데이터 손실 없음 |
| Kakao Maps 안 뜸 | Kakao 콘솔 도메인 미등록 | https://developers.kakao.com 에서 .web.app 도메인 추가 |
| 빌드 시 `Module not found` | npm install 안 됨 또는 lockfile/package.json 불일치 | `cd dashboard-web && npm install` (CI 모드 `npm ci` 실패 시 lockfile 재생성용으로 `npm install` 사용) |

---

## 4. 비용·한도 체크

| 항목 | 사용량 | 한도 | 여유 |
|---|---|---|---|
| Firebase Hosting 저장 | ~3.6MB | 10GB | 99.96% |
| Firebase Hosting 전송/일 | 변동 | 360MB | 데모 수준 충분 |
| Cloudflare Tunnel 트래픽 | 변동 | 무제한 | ∞ |
| `*.trycloudflare.com` URL | 임시 | 즉시 | 매 시작 시 변경 |

---

## 5. 영구 URL로 업그레이드 (나중에)

도메인 보유 후 (Cloudflare Registrar 권장, 원가 ~$11/년):

```bash
# 1. Tunnel 영구 등록
cloudflared tunnel create lunchmenu
cloudflared tunnel route dns lunchmenu lunchmenu.your-domain.com

# 2. 설정 파일 ~/.cloudflared/config.yml 생성 (CLOUDFLARE_TUNNEL.md §2-A 참조)

# 3. 서비스로 등록 (Mac 부팅 시 자동 시작)
sudo cloudflared service install

# 4. .env.production 갱신 후 재배포
./scripts/deploy_demo.sh https://lunchmenu.your-domain.com
```
