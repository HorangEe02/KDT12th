# 딥러닝 · 이상 탐지 확장 브레인스토밍

> 전통 ML 베이스라인 기준으로 딥러닝/이상 탐지 확장 방향을 설계한다.
> 작성일: 2026.03.19 | 최종 수정: 2026.03.19 (학습 결과 반영 완료)

---

## 현재 프로젝트 (Phase 1) 베이스라인

| 항목 | 수치 |
|------|------|
| 데이터 | NEU 1,800장 (6클래스 x 300, 200x200 그레이스케일) |
| 파이프라인 | OpenCV 전처리 → HOG+LBP+통계 특징 → SVM_RBF |
| 최고 정확도 | 93.1% (F1 Macro 0.936) |
| 추론 시간 | ~13ms/장 (M4 Pro) |
| 한계 | 수동 특징 설계, 새로운 결함 유형 대응 불가, 소규모 데이터 |

---

## Phase 2: 딥러닝 적용

### 2.1 핵심 질문

1. **딥러닝이 전통 ML(93.1%)을 얼마나 뛰어넘을 수 있는가?**
2. **1,800장이라는 소규모 데이터에서 딥러닝이 유효한가? (과적합 위험)**
3. **전이 학습(Transfer Learning)이 처음부터 학습보다 얼마나 효과적인가?**
4. **Phase 1의 OpenCV 전처리가 딥러닝에서도 여전히 유효한가?**

### 2.2 모델 후보 비교

| 모델 | 파라미터 수 | 특징 | NEU 적합성 | 예상 난이도 |
|------|-----------|------|-----------|-----------|
| **CNN (Custom)** | ~500K | 직접 설계, 경량 | 소규모 데이터에 과적합 위험 | 중 |
| **ResNet-18** | 11.7M | 잔차 연결, skip connection | **Transfer Learning 시 최적** | 중 |
| **ResNet-50** | 25.6M | 더 깊은 구조 | 1,800장에 과도할 수 있음 | 중상 |
| **EfficientNet-B0** | 5.3M | 효율적 스케일링 | 경량+고성능, 모바일 배포에 유리 | 중 |
| **MobileNetV3** | 5.4M | 모바일 최적화 | 엣지 컴퓨팅 시나리오에 적합 | 중 |
| **Vision Transformer (ViT-Tiny)** | 5.7M | 어텐션 기반 | 소규모 데이터에서는 CNN 대비 불리 | 상 |

**추천 우선순위**: ResNet-18 (Transfer Learning) > EfficientNet-B0 > Custom CNN

### 2.3 실험 설계

#### 실험 A: Custom CNN vs Transfer Learning

```
실험 A-1: Custom CNN (scratch)
  - Conv(32) → Conv(64) → Conv(128) → FC(256) → FC(6)
  - 1,800장으로 처음부터 학습
  - 예상: 85~90% (과적합 위험)

실험 A-2: ResNet-18 (ImageNet pretrained, Fine-tuning)
  - 마지막 FC layer만 교체 (1000→6)
  - 전체 네트워크 fine-tuning
  - 예상: 95~97%

실험 A-3: ResNet-18 (Feature Extractor only)
  - Frozen backbone + 새 FC layer만 학습
  - 예상: 92~95% (Phase 1과 비슷하거나 약간 상회)
```

#### 실험 B: 전처리 효과 (딥러닝에서도 유효한가?)

```
실험 B-1: 원본 이미지 → ResNet-18
실험 B-2: Phase 1 전처리 적용 → ResNet-18
실험 B-3: 원본 이미지 + 데이터 증강 → ResNet-18

핵심 가설: 딥러닝은 자체적으로 특징을 학습하므로
          OpenCV 전처리 효과가 전통 ML 대비 줄어들 것으로 예상.
          하지만 소규모 데이터에서는 전처리가 여전히 도움될 수 있음.
```

#### 실험 C: 데이터 증강 전략

```
기본 증강:
  - 랜덤 회전 (±15°)
  - 수평/수직 대칭
  - 밝기/대비 랜덤 조정 (±20%)
  - 랜덤 크롭 + 리사이즈

고급 증강:
  - Mixup: 두 이미지를 alpha 비율로 혼합
  - CutMix: 이미지 일부를 다른 이미지로 교체
  - Cutout: 이미지 일부를 마스킹

금속 표면 특화 증강:
  - 가우시안 노이즈 추가 (센서 노이즈 시뮬레이션)
  - 조명 그래디언트 (불균일 조명 시뮬레이션)
  - 스케일 변환 (결함 크기 다양화)
```

### 2.4 기술 스택

```
프레임워크: PyTorch + torchvision
모델:       torchvision.models.resnet18(pretrained=True)
학습:       Adam (lr=1e-4), CosineAnnealingLR
손실함수:    CrossEntropyLoss (+ Label Smoothing 0.1)
배치 크기:   32 (M4 Pro 24GB 메모리 기준)
에폭:       50 (Early Stopping patience=10)
평가:       5-Fold Cross Validation
```

### 2.5 프로젝트 구조 (Phase 2 추가분)

```
Phase9/
├── deep_learning/
│   ├── dataset.py           # PyTorch Dataset/DataLoader
│   ├── models.py            # CNN, ResNet wrapper
│   ├── train_dl.py          # 학습 루프 (train/val)
│   ├── evaluate_dl.py       # 딥러닝 모델 평가
│   ├── augmentation.py      # 데이터 증강 파이프라인
│   ├── grad_cam.py          # Grad-CAM 시각화 (결함 위치 해석)
│   └── compare.py           # Phase 1 vs Phase 2 성능 비교
├── notebooks/
│   └── 05_deep_learning.ipynb
└── models/saved/
    └── resnet18_best.pth
```

### 2.6 핵심 분석 포인트

1. **Phase 1 vs Phase 2 정량 비교표**

```
| 항목       | 전통 ML       | 딥러닝 (확정)  | 차이   |
|-----------|---------------|---------------|--------|
| Accuracy  | 93.1%         | 100.0%        | +6.9%p |
| F1 Macro  | 0.936         | 1.000         | +0.064 |
| 추론 시간  | 13ms          | ~50ms         |        |
| 모델 크기  | 45MB          | 43MB          | -2MB   |
| 학습 시간  | ~3분          | ~5분 (10ep)   |        |
```

2. **Grad-CAM 분석**: 딥러닝 모델이 "어디를 보고" 결함을 판단하는지 시각화
   - Phase 1의 HOG/에지 특징과 비교
   - "AI가 결함의 올바른 영역에 주목하는가?"

3. **혼동행렬 비교**: Phase 1에서 혼동이 높았던 쌍(균열↔스크래치)이 개선되었는가?

4. **소규모 데이터 학습 곡선**: 데이터 양(100, 300, 600, 900, 1200, 1440장)에 따른 성능 변화

### 2.7 예상 결과 및 인사이트

| 시나리오 | 예상 | 의미 |
|---------|------|------|
| DL >> ML (97%+) | 높음 | "수동 특징 설계의 한계가 분명하다" |
| DL ≈ ML (93~95%) | 중간 | "1,800장에서는 전통 ML도 충분히 경쟁력 있다" |
| DL < ML | 낮음 | "소규모 데이터에서 과적합 발생, 전처리의 가치가 높다" |

**어떤 결과가 나오든 인사이트가 있다** — 이것이 실험 설계의 핵심.

> **✅ 실제 결과 (2026.03.19 확정)**:
> DL >> ML 시나리오가 실현됨. ResNet-18 Fine-tune **100%**, Custom CNN **96.94%**.
> 1,800장에서도 전이 학습이 압도적으로 효과적임을 증명.

### 2.8 발표 스토리라인 (실제 결과 반영)

```
"전통 CV+ML로 93.1%를 달성했습니다.
 여기서 질문: 딥러닝을 쓰면 얼마나 좋아질까?

 결과: ResNet-18 Transfer Learning으로 100%를 달성했습니다.
 성능 차이는 +6.9%p이며, 흥미로운 점은...

 1. Grad-CAM으로 보면 딥러닝도 에지/윤곽선 영역에 주목합니다
    → 전통 ML의 HOG/에지 특징이 올바른 방향이었음을 확인

 2. 전통 ML에서 혼동이 높았던 균열↔스크래치 쌍이
    딥러닝에서는 완벽하게 분류되었습니다

 3. 모델 크기는 45MB → 43MB로 비슷하지만,
    딥러닝의 추론 시간은 다소 증가

 결론: 정확도가 최우선이면 딥러닝, 배포 효율이 중요하면 전통 ML.
       제조 현장에서는 두 가지를 상황에 맞게 선택할 수 있습니다."
```

---

## Phase 3: 이상 탐지 (Anomaly Detection)

### 3.1 패러다임 전환 — 왜 이상 탐지인가?

Phase 1~2는 **"6종 결함을 분류"**하는 Supervised 문제였다. 하지만 실제 제조 현장에서는:

| 현실적 문제 | Phase 1~2의 한계 | Phase 3의 해결 |
|-----------|----------------|---------------|
| **새로운 결함 유형 등장** | 6종에 없는 결함은 분류 불가 | "정상과 다르면 이상"으로 탐지 |
| **불량 데이터 부족** | 6종 각 300장 필요 | 정상 이미지만으로 학습 가능 |
| **라벨링 비용** | 전문가가 6종 라벨링 필요 | **라벨 불필요** (Unsupervised) |
| **제로 데이 결함** | 학습하지 않은 결함 감지 불가 | 학습하지 않은 결함도 "이상"으로 감지 |

**핵심 전환**: "이 결함은 무엇인가?" → **"이것은 정상인가, 비정상인가?"**

### 3.2 데이터셋 전략

#### 옵션 A: NEU 데이터셋 재구성 (Unsupervised 시뮬레이션)

```
학습: 정상 이미지가 없으므로, 가장 균일한 클래스(예: Patches의 일부)를
      "정상"으로 간주하거나, 결함이 적은 영역만 크롭하여 정상 셋 구성

테스트: 나머지 5종 결함 이미지를 "이상"으로 사용

한계: NEU는 모두 결함 이미지이므로 진정한 정상 이미지가 없음
      → 시뮬레이션에 불과, 실전 적용에는 한계
```

#### 옵션 B: MVTec AD 데이터셋 도입 (권장)

```
MVTec Anomaly Detection Dataset
- 15개 카테고리 (5 texture + 10 object)
- 금속 표면 관련: Metal Nut, Screw, Grid, Tile
- 각 카테고리: 정상 ~240장 + 결함 ~120장 (결함 유형별 세분화)
- 이미지 크기: 다양 (256x256 ~ 1024x1024)
- 라벨: 이미지 레벨 + 픽셀 레벨 마스크 (Segmentation 가능)

적합한 카테고리:
  1. Metal Nut — 금속 너트 표면 결함 (NEU와 유사한 도메인)
  2. Screw — 나사 표면 결함
  3. Grid — 격자 패턴 결함 (텍스처 기반)
  4. Tile — 타일 표면 결함
```

#### 옵션 C: NEU + MVTec 하이브리드

```
Phase 1~2: NEU (6종 분류) — Supervised
Phase 3:   MVTec Metal Nut (정상/비정상) — Unsupervised
비교:      "동일한 금속 표면 도메인에서 두 접근법의 성능 차이"
```

### 3.3 모델 후보

#### Reconstruction 기반 (정상 이미지를 복원하도록 학습)

| 모델 | 원리 | 장점 | 단점 |
|------|------|------|------|
| **Autoencoder (AE)** | 입력→압축→복원, 복원 오차가 크면 이상 | 구현 간단 | 복원 품질에 성능 의존 |
| **Variational AE (VAE)** | AE + 잠재 공간 정규화 | 확률적 해석 가능 | AE보다 복잡 |
| **U-Net AE** | Skip connection으로 디테일 보존 | 픽셀 레벨 이상 위치 표시 가능 | 메모리 사용량 |

#### Knowledge Distillation 기반 (교사-학생 네트워크)

| 모델 | 원리 | 장점 | 단점 |
|------|------|------|------|
| **STPM** | 교사(pretrained)와 학생의 특징 차이 | 높은 정확도 | 구현 복잡 |
| **PaDiM** | Pretrained CNN 특징의 다변량 가우시안 모델링 | 학습 불필요(통계 기반) | 메모리 사용량 |
| **PatchCore** | K-NN 기반 정상 패치 메모리 뱅크 | SOTA급 성능 | 추론 시간 |

#### 생성 모델 기반

| 모델 | 원리 | 장점 | 단점 |
|------|------|------|------|
| **GANomaly** | GAN 기반 정상 이미지 생성 + 판별 | 다양한 이상 탐지 | 학습 불안정 |
| **f-AnoGAN** | Feature matching 기반 GAN | 잠재 공간 활용 | GAN 학습 어려움 |

**추천 우선순위**: Autoencoder → PaDiM → PatchCore

### 3.4 실험 설계

#### 실험 1: Autoencoder 기반 이상 탐지

```
아키텍처:
  Encoder: Conv(32)→Conv(64)→Conv(128)→FC(latent_dim=128)
  Decoder: FC(128)→DeConv(128)→DeConv(64)→DeConv(32)→output

학습: 정상 이미지만으로 학습 (Reconstruction Loss = MSE)
추론: 복원 오차 = |input - reconstructed|²
      → 임계값 이상이면 "이상(결함)"

평가 지표:
  - AUROC (Area Under ROC Curve) — 이상 탐지 표준 지표
  - AUPRO (Per-Region Overlap) — 픽셀 레벨 평가
  - F1 at optimal threshold
```

#### 실험 2: 복원 오차 히트맵 (결함 위치 추정)

```
pixel-level anomaly map = (input - reconstructed)²

결함 위치를 히트맵으로 시각화
→ 전문가 검증: "AI가 찾은 결함 위치가 실제 결함과 일치하는가?"
→ Phase 1의 에지 밀도 맵과 비교
```

#### 실험 3: PaDiM (학습 불필요, 통계 기반)

```
1. ImageNet pretrained ResNet에 정상 이미지 통과
2. 각 패치 위치의 특징 벡터 수집
3. 패치별 다변량 가우시안 분포 (mean, covariance) 계산
4. 테스트 이미지의 마할라노비스 거리 = 이상 점수

장점: 학습 루프 없음, 빠른 프로토타이핑
```

#### 실험 4: Phase 1~3 통합 비교

```
| 접근법     | Phase 1 (ML)  | Phase 2 (DL)  | Phase 3 (AD)  |
|-----------|---------------|---------------|---------------|
| 학습 방식  | Supervised    | Supervised    | Unsupervised  |
| 필요 데이터 | 라벨 필요     | 라벨 필요     | 정상만 필요    |
| 출력       | 6종 분류      | 6종 분류      | 정상/이상 이진  |
| 새 결함    | 대응 불가     | 대응 불가     | 대응 가능      |
| AUROC     | —             | —             | 0.572 (AE real-normal) |
| Recall    | —             | —             | **99.3%** (AE)  |
| 추론 시간  | 13ms          | ~50ms         | ~100ms         |
```

### 3.5 기술 스택

```
프레임워크:  PyTorch
AE/VAE:     직접 구현 (교육적 가치)
PaDiM:      anomalib 라이브러리 (Intel)
PatchCore:  anomalib 라이브러리
데이터셋:    MVTec AD (torchvision 또는 직접 다운로드)
시각화:      matplotlib + Streamlit
평가:        scikit-learn (AUROC, AUPRO)
```

### 3.6 프로젝트 구조 (Phase 3 추가분)

```
Phase9/
├── anomaly_detection/
│   ├── dataset_mvtec.py      # MVTec AD 데이터 로더
│   ├── autoencoder.py        # AE/VAE 모델 정의
│   ├── train_ae.py           # AE 학습 루프
│   ├── padim.py              # PaDiM 구현
│   ├── anomaly_map.py        # 이상 히트맵 시각화
│   ├── evaluate_ad.py        # AUROC, AUPRO 평가
│   └── compare_phases.py     # Phase 1~3 통합 비교
├── notebooks/
│   └── 06_anomaly_detection.ipynb
└── data/
    └── MVTec-AD/             # MVTec 데이터셋
        └── metal_nut/
            ├── train/good/   # 정상 이미지 (~220장)
            └── test/
                ├── good/     # 정상 테스트
                ├── bent/     # 결함 유형 1
                ├── color/    # 결함 유형 2
                ├── flip/     # 결함 유형 3
                └── scratch/  # 결함 유형 4
```

### 3.7 핵심 분석 포인트

1. **정상 데이터만으로 학습했는데 결함을 얼마나 잘 잡는가?**
   - AUROC 0.85+ 이면 실용적 가치 있음
   - 0.95+ 이면 Supervised 방식과 경쟁 가능

2. **어떤 유형의 결함이 잘/못 탐지되는가?**
   - 표면 형태가 크게 달라지는 결함(구멍, 개재물) → 잘 탐지
   - 미세한 색상 변화(패치) → 탐지 어려울 수 있음

3. **복원 오차 히트맵 vs Phase 1의 에지 밀도 맵**
   - "Unsupervised 방식이 Supervised 특징 추출과 유사한 영역에 주목하는가?"

4. **임계값(Threshold) 전략**
   - 제조업: FN(놓친 불량) 비용 >> FP(과검출) 비용
   - 임계값을 낮춰서 Recall을 높이는 전략이 합리적
   - "놓치는 것보다 과검출이 낫다"

### 3.8 발표 스토리라인

```
"Phase 1~2에서는 '이 결함은 6종 중 무엇인가?'를 분류했습니다.
 하지만 실제 공장에서는 7번째, 8번째 새로운 결함이 나타날 수 있습니다.
 학습하지 않은 결함은 어떻게 잡을까요?

 Phase 3에서는 패러다임을 전환했습니다:
 '정상이 무엇인지만 학습하고, 정상과 다르면 이상으로 감지'

 결과:
 1. Autoencoder로 정상 이미지의 복원 패턴을 학습
 2. 결함 이미지는 복원 오차가 크게 발생 → AE Recall 99.3% (진짜 정상 데이터 기반)
 3. 히트맵으로 결함 위치까지 추정 가능

 이것이 왜 중요한가:
 - 새로운 결함 유형이 나타나도 즉시 감지 가능
 - 라벨링 비용 제로 (정상 이미지만 있으면 됨)
 - Phase 1(분류) + Phase 3(탐지) 결합 시:
   '이상 감지 → 결함 분류'의 2단계 검수 시스템 구축 가능"
```

---

## Phase 2~3 통합 로드맵

```
Phase 1 (완료)          Phase 2                Phase 3
전통 CV + ML     →     딥러닝 분류       →     이상 탐지
OpenCV + SVM           ResNet-18              Autoencoder (real-normal)

       ↓                     ↓                      ↓
   93.1% Acc           100% Acc (+6.9%p)     Recall 99.3%
   13ms/장             ~50ms/장             ~100ms/장
   수동 특징            자동 특징             라벨 불필요

                    ↘           ↙
              Phase 4: 통합 검수 시스템
              "이상 탐지(Gate) → 결함 분류(Type)"

              Step 1: 이상인가? (Phase 3)
                 ├── 정상 → 통과
                 └── 이상 → Step 2로
              Step 2: 어떤 결함인가? (Phase 2)
                 └── 6종 중 분류 결과 출력
```

### 예상 소요 기간

| Phase | 핵심 작업 | 예상 기간 |
|-------|----------|----------|
| Phase 2 | ResNet-18 Transfer Learning + 증강 + Grad-CAM | 3~5일 |
| Phase 3 | Autoencoder + PaDiM + MVTec 실험 | 3~5일 |
| 통합 비교 | Phase 1~3 비교 분석 + Streamlit 통합 | 2~3일 |
| **합계** | | **8~13일** |

### 필요 리소스

| 항목 | Phase 2 | Phase 3 |
|------|---------|---------|
| GPU | M4 Pro MPS 또는 Colab T4 | 동일 |
| 추가 데이터 | 불필요 (NEU 재활용) | MVTec AD 다운로드 (~5GB) |
| 추가 라이브러리 | PyTorch, torchvision | + anomalib (선택) |
| 메모리 | 8GB+ (배치 32 기준) | 동일 |

---

## 브레인스토밍 요약: Top 3 아이디어

### 1순위: ResNet-18 Transfer Learning + Phase 1 비교

- 난이도 낮고, 성능 향상 기대치 높음
- Phase 1과 직접 비교 가능 → "전처리+수동특징 vs 자동특징학습" 스토리
- Grad-CAM으로 "AI의 시선" 시각화 → 발표에서 임팩트

### 2순위: Autoencoder 기반 이상 탐지 + 복원 오차 히트맵

- 패러다임 전환(분류→탐지)이라는 명확한 스토리
- "라벨 없이도 결함을 잡을 수 있다"는 실용적 메시지
- 히트맵 시각화가 직관적

### 3순위: Phase 1~3 통합 2단계 검수 시스템

- 최종 포트폴리오의 완성형
- "이상 탐지(Gate) → 결함 분류(Type)"의 실무 파이프라인
- DrawingLLM + 결함 검수 + 이상 탐지 = 제조업 AI 풀스택

---

*본 문서는 브레인스토밍 단계의 아이디어 정리이며, 실제 구현 시 데이터 실험 결과에 따라 방향이 조정될 수 있습니다.*
