# 🤖 소주제 ④ — 하이브리드 결함 분류 모델링

## Claude Code 실행 가이드라인

> **프로젝트**: OpenCV & ML 하이브리드 부품 결함 자동 검수 시스템  
> **연계 차시**: 3~4차시 (CV기반 ML 모델 저장/로딩, 분류 모델 적용)  
> **담당 역할**: B. 특징 추출 & 모델링 / C. 평가 & 분석 (공동)  
> **작성일**: 2026.03.19

---

## 📋 실행 전 체크리스트

### 사전 준비 사항

1. **소주제 ①②③ 완료 확인**
   - `utils/data_loader.py` — NEUDataLoader 클래스 ✅
   - `preprocessing/` — alignment, roi, normalization, filters, sharpening, morphology, thresholding, edge_detection ✅
   - `features/contour_features.py` — 윤곽선 특징 추출 ✅
   - `features/edge_features.py` — 에지 특징 추출 ✅
   - `utils/filter_utils.py` — 필터 평가 유틸리티 ✅
   - `outputs/contour_edge_features.npy` — 소주제 ③에서 생성한 특징 행렬 ✅
   - `outputs/labels.npy` — 라벨 배열 ✅

2. **소주제 ②에서 확정된 최적 전처리 파이프라인**
   ```python
   def preprocess(image):
       img = clahe_equalization(image)
       img = bilateral_filter(img, d=9, sigma_color=75, sigma_space=75)
       img = adaptive_sharpen(img, blur_ksize=5, sharp_amount=1.5, noise_threshold=10)
       img = opening(img, kernel_shape="rect", kernel_size=3)
       return img
   ```

3. **Python 환경 추가 패키지 확인**
   ```bash
   pip install opencv-python scikit-learn scikit-image numpy scipy matplotlib seaborn pandas joblib jupyter
   ```

4. **프로젝트 디렉토리 구조 (소주제 ④ 추가분)**
   ```
   project_root/
   ├── data/
   │   └── NEU-DET/
   ├── preprocessing/                     # (소주제 ①②③에서 완성)
   ├── features/
   │   ├── __init__.py                    # (소주제 ③에서 생성)
   │   ├── contour_features.py            # (소주제 ③)
   │   ├── edge_features.py               # (소주제 ③)
   │   ├── hog_features.py                # [이 가이드에서 생성] HOG 특징 추출
   │   ├── lbp_features.py                # [이 가이드에서 생성] LBP 특징 추출
   │   ├── pixel_stats.py                 # [이 가이드에서 생성] 픽셀 통계 특징
   │   └── feature_pipeline.py            # [이 가이드에서 생성] 통합 특징 파이프라인
   ├── models/
   │   ├── __init__.py                    # [이 가이드에서 생성]
   │   ├── train.py                       # [이 가이드에서 생성] 모델 학습
   │   ├── evaluate.py                    # [이 가이드에서 생성] 모델 평가 및 시각화
   │   ├── inference.py                   # [이 가이드에서 생성] 추론 파이프라인
   │   └── saved/                         # 저장된 모델 (.joblib)
   ├── utils/
   │   ├── data_loader.py                 # (소주제 ①)
   │   └── filter_utils.py                # (소주제 ②)
   ├── notebooks/
   │   ├── 01_alignment_roi.ipynb         # (소주제 ①)
   │   ├── 02_filtering_sharpening.ipynb  # (소주제 ②)
   │   ├── 03_edge_contour_analysis.ipynb # (소주제 ③)
   │   └── 04_classification.ipynb        # [이 가이드에서 생성] 분류 분석 노트북
   ├── outputs/
   │   ├── figures/
   │   ├── contour_edge_features.npy      # (소주제 ③에서 생성)
   │   └── labels.npy                     # (소주제 ③에서 생성)
   └── README.md
   ```

---

## 🎯 소주제 ④ 목표 및 범위

### 최종 목표

소주제 ①②③에서 구축한 **전처리 파이프라인 + 특징 추출 모듈**의 결과를 Scikit-learn 기반 ML 모델에 입력하여 6종 금속 표면 결함을 자동 분류하고, **전처리 효과를 정량적으로 증명**하며, **제조업 맥락에서의 모델 평가**를 수행한다.

### 핵심 질문

1. **OpenCV 전처리가 ML 분류 성능을 실제로 향상시키는가?** 전처리 전/후 Accuracy, F1, Recall의 차이를 정량 비교
2. **어떤 특징 조합이 최적인가?** HOG만 vs HOG+LBP vs HOG+LBP+통계 vs HOG+LBP+통계+에지/윤곽선
3. **어떤 분류 모델이 이 데이터에 가장 적합한가?** SVM, Random Forest, KNN의 성능 비교
4. **어떤 결함이 가장 분류하기 어려운가?** 혼동행렬 기반 오분류 패턴 분석
5. **제조업 현장에서 이 모델을 신뢰할 수 있는가?** Recall 중심 평가와 FN 비용 분석

### 세부 목표

| # | 목표 | 산출물 |
|---|------|--------|
| 1 | HOG 특징 추출 모듈 구현 | `hog_features.py` |
| 2 | LBP 특징 추출 모듈 구현 | `lbp_features.py` |
| 3 | 픽셀 통계 특징 모듈 구현 | `pixel_stats.py` |
| 4 | 통합 특징 파이프라인 구현 | `feature_pipeline.py` |
| 5 | 모델 학습 모듈 구현 | `train.py` |
| 6 | 모델 평가/시각화 모듈 구현 | `evaluate.py` |
| 7 | 추론 파이프라인 구현 | `inference.py` |
| 8 | 전체 실험 및 분석 | `04_classification.ipynb` |

---

## 🚀 Phase 1: HOG 특징 추출 모듈

### 1.1 배경 설명

HOG(Histogram of Oriented Gradients)는 이미지의 국소 영역에서 그래디언트 방향의 분포를 히스토그램으로 표현하는 특징 기술자이다. 결함의 경계와 형태 패턴을 효과적으로 캡처하며, 전통적 CV 기반 분류에서 가장 널리 사용되는 특징이다.

### 1.2 Claude Code 지시사항

```
다음 요구사항에 따라 features/hog_features.py를 구현해줘.

[파일 위치] features/hog_features.py

[기능 요구사항]

1. extract_hog(image: np.ndarray, orientations: int = 9, pixels_per_cell: tuple = (8, 8), cells_per_block: tuple = (2, 2), visualize: bool = False) -> Union[np.ndarray, tuple[np.ndarray, np.ndarray]]
   - HOG 특징 벡터 추출
   - skimage.feature.hog() 사용
   - orientations: 방향 빈 수 (기본 9 → 20° 간격)
   - pixels_per_cell: 셀당 픽셀 수 (기본 8×8)
   - cells_per_block: 블록당 셀 수 (기본 2×2, L2-norm 정규화)
   - visualize=True이면 HOG 시각화 이미지도 함께 반환
   - 입력 이미지를 0~1 float로 정규화 후 전달
   - 반환: feature_vector (visualize=False) 또는 (feature_vector, hog_image) (visualize=True)
   - 200×200 이미지, 기본 파라미터 시: (200/8 - 2 + 1)² × 2 × 2 × 9 = 24² × 36 = 20,736차원
     ⚠️ 실제 차원은 skimage 내부 계산에 따라 다를 수 있으므로 출력 shape 확인 필수

2. extract_hog_multiscale(image: np.ndarray, cell_sizes: list[tuple] = [(4,4), (8,8), (16,16)]) -> np.ndarray
   - 멀티스케일 HOG: 여러 셀 크기에서 HOG를 추출하고 concatenate
   - 작은 셀(4×4): 미세 결함 패턴 캡처
   - 큰 셀(16×16): 전체적 형태 캡처
   - 반환: concatenated feature vector

3. extract_hog_compact(image: np.ndarray, target_dim: int = 512) -> np.ndarray
   - 차원 축소된 HOG 특징 추출
   - 구현 방법:
     a. 기본 HOG 추출
     b. 차원이 target_dim보다 크면 PCA로 축소
     c. sklearn.decomposition.PCA(n_components=target_dim)
     d. PCA 모델도 반환 (또는 클래스 속성으로 저장)하여 추론 시 동일 변환 적용
   - 반환: (target_dim,) shape의 특징 벡터
   - 용도: 고차원 HOG를 합리적 크기로 축소하여 학습 속도 개선

4. batch_extract_hog(images: np.ndarray, orientations: int = 9, pixels_per_cell: tuple = (8, 8), cells_per_block: tuple = (2, 2)) -> np.ndarray
   - 여러 이미지에 대해 일괄 HOG 추출
   - images shape: (N, 200, 200)
   - 반환: (N, feature_dim) shape의 특징 행렬
   - 진행률 출력 (매 100장 또는 10%마다)
   - 용도: 전체 데이터셋 특징 행렬 생성

5. get_hog_feature_dim(image_shape: tuple = (200, 200), orientations: int = 9, pixels_per_cell: tuple = (8, 8), cells_per_block: tuple = (2, 2)) -> int
   - 파라미터에 따른 HOG 특징 차원 계산 (실제 추출 없이)
   - 더미 이미지로 한번 추출하여 차원 확인하는 방식도 가능
   - 반환: 특징 벡터 차원(int)

[코딩 규칙]
- Type hints 사용, Docstring (Google style)
- skimage.feature.hog import 필요
- 입력 이미지: uint8(0~255) → float64(0~1)로 자동 변환
- 그레이스케일 2D만 허용
- import: numpy, cv2, skimage.feature, sklearn.decomposition, typing, warnings

[테스트]
- if __name__ == "__main__": 블록
- NEU 데이터셋 6클래스 각 1장에 extract_hog() 적용, 출력 shape 확인
- HOG 시각화 이미지 1장 저장 (visualize=True)
- batch_extract_hog()로 30장(5/class) 추출, shape 확인
- 기본 파라미터와 compact(512d) 결과 비교 출력
```

---

## 🚀 Phase 2: LBP 특징 추출 모듈

### 2.1 배경 설명

LBP(Local Binary Pattern)는 각 픽셀 주변의 밝기 패턴을 이진 코드로 인코딩하는 텍스처 기술자이다. HOG가 결함의 "형태"를 캡처한다면, LBP는 결함 표면의 **"텍스처 패턴"**을 캡처한다. 금속 표면의 결함 유형별 미세 텍스처 차이(균열의 거친 질감 vs 패치의 매끈한 질감)를 구분하는 데 효과적이다.

### 2.2 Claude Code 지시사항

```
다음 요구사항에 따라 features/lbp_features.py를 구현해줘.

[파일 위치] features/lbp_features.py

[기능 요구사항]

1. extract_lbp(image: np.ndarray, n_points: int = 24, radius: int = 3, method: str = "uniform") -> np.ndarray
   - LBP 패턴 맵 생성
   - skimage.feature.local_binary_pattern() 사용
   - n_points: 주변 샘플링 포인트 수 (기본 24)
   - radius: 샘플링 반경 (기본 3)
   - method: "uniform" (Uniform LBP, 회전 불변 + 축소된 빈 수)
   - 반환: LBP 패턴 맵 (image와 동일한 shape, 각 픽셀의 LBP 코드값)

2. extract_lbp_histogram(image: np.ndarray, n_points: int = 24, radius: int = 3, method: str = "uniform") -> np.ndarray
   - LBP 히스토그램 (특징 벡터)
   - 구현 방법:
     a. extract_lbp()로 LBP 패턴 맵 생성
     b. Uniform LBP의 빈 수: n_points + 2 (uniform 패턴 n_points개 + non-uniform 1개 + 추가)
     c. np.histogram()으로 히스토그램 계산 (bins=n_points+2, range=(0, n_points+2))
     d. L2 정규화 (합의 제곱근으로 나눔)
   - 반환: (n_points+2,) shape의 정규화된 히스토그램
   - 용도: ML 분류의 특징 벡터로 직접 사용

3. extract_lbp_spatial(image: np.ndarray, grid_size: int = 4, n_points: int = 24, radius: int = 3) -> np.ndarray
   - 공간 분할 LBP 히스토그램 (Spatial LBP)
   - 구현 방법:
     a. 이미지를 grid_size × grid_size 블록으로 분할
     b. 각 블록에서 LBP 히스토그램 추출
     c. 모든 블록의 히스토그램을 concatenate
   - 반환: (grid_size² × (n_points+2),) shape의 벡터
   - 용도: 결함의 공간적 텍스처 분포를 캡처. 전체 히스토그램보다 정보량 풍부

4. extract_lbp_multiscale(image: np.ndarray, radii: list[int] = [1, 3, 5], n_points_list: list[int] = [8, 24, 40]) -> np.ndarray
   - 멀티스케일 LBP
   - 각 (radius, n_points) 쌍에서 LBP 히스토그램 추출 후 concatenate
   - radii와 n_points_list는 같은 길이여야 함
   - 반환: concatenated feature vector
   - 용도: 미세 텍스처(작은 radius)와 거시 텍스처(큰 radius) 동시 캡처

5. batch_extract_lbp(images: np.ndarray, mode: str = "histogram", **kwargs) -> np.ndarray
   - 여러 이미지에 대해 일괄 LBP 특징 추출
   - mode: "histogram", "spatial", "multiscale"
   - 반환: (N, feature_dim) 특징 행렬
   - 진행률 출력

6. visualize_lbp_pattern(image: np.ndarray, n_points: int = 24, radius: int = 3) -> np.ndarray
   - LBP 패턴 맵을 시각화용으로 0~255 정규화
   - 반환: uint8 이미지 (matplotlib 표시용)

[코딩 규칙]
- Type hints 사용, Docstring (Google style)
- skimage.feature.local_binary_pattern import 필요
- 히스토그램 정규화 시 L2 norm (분모 0 방지: + 1e-7)
- 그레이스케일 2D만 허용
- radii와 n_points_list 길이 불일치 시 ValueError
- import: numpy, cv2, skimage.feature, typing, warnings

[테스트]
- if __name__ == "__main__": 블록
- NEU 6클래스 각 1장에 LBP 히스토그램 추출, shape 확인
- 클래스별 LBP 히스토그램을 오버레이하여 분포 차이 확인 (print로 피크 위치 출력)
- spatial LBP(grid=4)와 multiscale LBP 차원 비교
- batch_extract_lbp()로 30장 추출 테스트
```

---

## 🚀 Phase 3: 픽셀 통계 특징 모듈

### 3.1 배경 설명

픽셀 통계 특징은 이미지의 전역적 밝기 분포를 수치화한 것이다. 평균, 분산, 왜도, 첨도 등의 통계값은 단순하지만 결함 유형 간 밝기 특성 차이를 캡처한다. GLCM(Gray-Level Co-occurrence Matrix) 기반 텍스처 특징도 포함하여 2차 통계 정보까지 추출한다.

### 3.2 Claude Code 지시사항

```
다음 요구사항에 따라 features/pixel_stats.py를 구현해줘.

[파일 위치] features/pixel_stats.py

[기능 요구사항]

1. extract_basic_stats(image: np.ndarray) -> dict[str, float]
   - 기본 픽셀 통계
   - 반환: {
       "mean": float,          # 평균 밝기
       "std": float,           # 표준편차
       "median": float,        # 중앙값
       "min": float,           # 최솟값
       "max": float,           # 최댓값
       "range": float,         # max - min
       "skewness": float,      # 왜도 (scipy.stats.skew)
       "kurtosis": float,      # 첨도 (scipy.stats.kurtosis)
       "energy": float,        # 에너지 (sum(pixel²) / N)
       "entropy": float        # 엔트로피 (-sum(p * log2(p)), 히스토그램 기반)
     }

2. extract_histogram_features(image: np.ndarray, n_bins: int = 32) -> np.ndarray
   - 밝기 히스토그램을 특징 벡터로 사용
   - n_bins개 구간으로 히스토그램 계산
   - L1 정규화 (합=1)
   - 반환: (n_bins,) shape의 정규화된 히스토그램

3. extract_glcm_features(image: np.ndarray, distances: list[int] = [1, 3], angles: list[float] = [0, np.pi/4, np.pi/2, 3*np.pi/4]) -> dict[str, float]
   - GLCM(Gray-Level Co-occurrence Matrix) 기반 텍스처 특징
   - skimage.feature.graycomatrix() + graycoprops() 사용
   - ⚠️ 입력 이미지를 levels 파라미터에 맞게 양자화 (예: 256→64 레벨로 축소)
   - 추출할 속성: contrast, dissimilarity, homogeneity, energy, correlation, ASM
   - 각 (distance, angle) 조합별 속성값 계산 → 전체 평균으로 집약
   - 반환: {
       "glcm_contrast": float,
       "glcm_dissimilarity": float,
       "glcm_homogeneity": float,
       "glcm_energy": float,
       "glcm_correlation": float,
       "glcm_ASM": float
     }

4. extract_spatial_stats(image: np.ndarray, grid_size: int = 4) -> np.ndarray
   - 공간 분할 통계 특징
   - 이미지를 grid_size×grid_size로 분할, 각 블록의 mean과 std 추출
   - 반환: (grid_size² × 2,) shape의 벡터 (mean + std 교차 배치)

5. extract_pixel_feature_vector(image: np.ndarray) -> np.ndarray
   - ML 분류용 최종 픽셀 통계 특징 벡터
   - 구성:
     a. basic_stats (10개)
     b. histogram_features (32개)
     c. glcm_features (6개)
     d. spatial_stats (32개, grid=4)
   - 전체를 concatenate하여 고정 길이 벡터 반환
   - 반환: np.ndarray (shape: (80,))

6. get_pixel_feature_names() -> list[str]
   - 특징명 리스트 반환 (80개)

7. batch_extract_pixel_features(images: np.ndarray) -> np.ndarray
   - 여러 이미지에 대해 일괄 픽셀 통계 추출
   - 반환: (N, 80) 특징 행렬
   - 진행률 출력

[코딩 규칙]
- Type hints 사용, Docstring (Google style)
- scipy.stats.skew, kurtosis import
- skimage.feature.graycomatrix, graycoprops import
- GLCM 양자화: (image / (256 / n_levels)).astype(np.uint8)
- 엔트로피 계산 시 p=0에 대한 0*log(0)=0 처리
- import: numpy, cv2, scipy.stats, skimage.feature, typing, warnings

[테스트]
- if __name__ == "__main__": 블록
- NEU 6클래스 각 1장에 extract_pixel_feature_vector() 적용
- 클래스별 basic_stats 비교 출력 (특히 mean, skewness, entropy 차이)
- GLCM 특징의 클래스별 차이 출력
```

---

## 🚀 Phase 4: 통합 특징 파이프라인

### 4.1 배경 설명

소주제 ③의 에지/윤곽선 특징, 소주제 ④의 HOG/LBP/픽셀 통계를 하나의 통합 파이프라인으로 묶어 **최종 특징 행렬**을 생성한다. 이 파이프라인이 전처리 적용 여부, 특징 조합 변경을 쉽게 실험할 수 있는 유연한 구조여야 한다.

### 4.2 Claude Code 지시사항

```
다음 요구사항에 따라 features/feature_pipeline.py를 구현해줘.

[파일 위치] features/feature_pipeline.py

[기능 요구사항]

1. FeaturePipeline 클래스 구현

class FeaturePipeline:
    def __init__(self, 
                 use_hog: bool = True,
                 use_lbp: bool = True,
                 use_pixel_stats: bool = True,
                 use_contour: bool = True,
                 use_edge: bool = True,
                 hog_params: dict = None,
                 lbp_params: dict = None,
                 preprocess_fn: callable = None,
                 scaler: str = "standard"):
        """
        통합 특징 추출 파이프라인.
        
        Args:
            use_hog: HOG 특징 사용 여부
            use_lbp: LBP 특징 사용 여부
            use_pixel_stats: 픽셀 통계 특징 사용 여부
            use_contour: 윤곽선 특징 사용 여부 (소주제 ③)
            use_edge: 에지 특징 사용 여부 (소주제 ③)
            hog_params: HOG 파라미터 딕셔너리 (기본: orientations=9, pixels_per_cell=(8,8))
            lbp_params: LBP 파라미터 딕셔너리 (기본: n_points=24, radius=3, mode="histogram")
            preprocess_fn: 전처리 함수 (None이면 전처리 없이 원본 사용)
            scaler: 스케일링 방법 ("standard", "minmax", "none")
        """
    
    def extract_single(self, image: np.ndarray) -> np.ndarray:
        """단일 이미지에서 특징 벡터 추출"""
        # 1. 전처리 적용 (preprocess_fn이 있으면)
        # 2. 각 특징 추출기 호출
        # 3. concatenate하여 1D 벡터 반환
    
    def extract_batch(self, images: np.ndarray, labels: np.ndarray = None) -> tuple[np.ndarray, np.ndarray]:
        """배치 이미지에서 특징 행렬 추출 + 스케일링 fit"""
        # 1. 각 이미지에 extract_single() 적용
        # 2. (N, feature_dim) 행렬 생성
        # 3. scaler fit_transform 적용
        # 4. 진행률 출력
        # 반환: (특징 행렬, 라벨)
    
    def transform(self, images: np.ndarray) -> np.ndarray:
        """학습 시 fit된 scaler로 transform만 (테스트 데이터용)"""
    
    def get_feature_names(self) -> list[str]:
        """전체 특징 이름 리스트 반환 (선택된 특징만)"""
    
    def get_feature_dim(self) -> int:
        """전체 특징 벡터 차원 반환"""
    
    def get_feature_group_indices(self) -> dict[str, tuple[int, int]]:
        """각 특징 그룹의 시작/끝 인덱스 반환
        예: {"hog": (0, 512), "lbp": (512, 538), ...}
        """

2. create_experiment_configs() -> list[dict]
   - README에 정의된 실험 조건 목록을 딕셔너리 리스트로 반환
   - 반환:
     [
       {"name": "Baseline_HOG_only_raw", "use_hog": True, "use_lbp": False, "use_pixel_stats": False, "use_contour": False, "use_edge": False, "preprocess": False},
       {"name": "HOG_only_preprocessed", "use_hog": True, "use_lbp": False, "use_pixel_stats": False, "use_contour": False, "use_edge": False, "preprocess": True},
       {"name": "HOG_LBP_preprocessed", "use_hog": True, "use_lbp": True, "use_pixel_stats": False, "use_contour": False, "use_edge": False, "preprocess": True},
       {"name": "HOG_LBP_Stats_preprocessed", "use_hog": True, "use_lbp": True, "use_pixel_stats": True, "use_contour": False, "use_edge": False, "preprocess": True},
       {"name": "All_features_preprocessed", "use_hog": True, "use_lbp": True, "use_pixel_stats": True, "use_contour": True, "use_edge": True, "preprocess": True},
     ]

[코딩 규칙]
- sklearn.preprocessing.StandardScaler, MinMaxScaler 사용
- scaler는 fit 후 객체를 self._scaler에 저장 (joblib 직렬화 시 함께 저장)
- preprocess_fn은 인자로 받되, 기본값은 None (전처리 없음)
- 각 특징의 NaN/Inf 체크: np.isnan, np.isinf → 0으로 대체 + 경고
- import: numpy, sklearn.preprocessing, joblib, typing, warnings + 모든 features 모듈

[테스트]
- if __name__ == "__main__": 블록
- 실험 설정 5개에 대해 각각 FeaturePipeline 생성
- 30장(5/class)에 대해 extract_batch() 실행
- 각 설정의 feature_dim 출력
- get_feature_names() 일부 출력
```

---

## 🚀 Phase 5: 모델 학습 모듈

### 5.1 Claude Code 지시사항

```
다음 요구사항에 따라 models/train.py를 구현해줘.

[파일 위치] models/train.py

[기능 요구사항]

1. get_models() -> dict[str, sklearn.base.BaseEstimator]
   - 실험에 사용할 분류 모델 딕셔너리 반환
   - 반환: {
       "SVM_RBF": SVC(kernel='rbf', C=10, gamma='scale', probability=True, random_state=42),
       "SVM_Linear": SVC(kernel='linear', C=1, probability=True, random_state=42),
       "RandomForest": RandomForestClassifier(n_estimators=200, max_depth=20, random_state=42, n_jobs=-1),
       "KNN_5": KNeighborsClassifier(n_neighbors=5, weights='distance', n_jobs=-1),
       "KNN_10": KNeighborsClassifier(n_neighbors=10, weights='distance', n_jobs=-1)
     }

2. train_single_model(model, X_train, y_train, X_test, y_test, model_name: str = "model") -> dict
   - 단일 모델 학습 및 평가
   - 구현 방법:
     a. model.fit(X_train, y_train) — 학습 시간 측정
     b. y_pred = model.predict(X_test)
     c. y_prob = model.predict_proba(X_test) (가능한 경우)
     d. classification_report 계산
     e. confusion_matrix 계산
   - 반환: {
       "model_name": str,
       "model": fitted_model,
       "accuracy": float,
       "classification_report": dict,  # sklearn의 classification_report(output_dict=True)
       "confusion_matrix": np.ndarray,
       "y_pred": np.ndarray,
       "y_prob": np.ndarray or None,
       "train_time": float (초),
       "predict_time": float (초)
     }

3. train_with_cross_validation(model, X, y, cv: int = 5, model_name: str = "model") -> dict
   - 교차 검증 학습
   - sklearn.model_selection.cross_validate() 사용
   - scoring: ['accuracy', 'f1_macro', 'recall_macro', 'precision_macro']
   - 반환: {
       "model_name": str,
       "cv_accuracy_mean": float,
       "cv_accuracy_std": float,
       "cv_f1_mean": float,
       "cv_f1_std": float,
       "cv_recall_mean": float,
       "cv_recall_std": float,
       "cv_scores": dict  # cross_validate 전체 결과
     }

4. hyperparameter_tuning(model_name: str, X_train, y_train, param_grid: dict = None) -> tuple
   - GridSearchCV 기반 하이퍼파라미터 튜닝
   - model_name별 기본 param_grid:
     - "SVM_RBF": {"C": [0.1, 1, 10, 100], "gamma": ["scale", "auto", 0.01, 0.001]}
     - "RandomForest": {"n_estimators": [100, 200, 300], "max_depth": [10, 20, 30, None], "min_samples_split": [2, 5]}
     - "KNN": {"n_neighbors": [3, 5, 7, 10, 15], "weights": ["uniform", "distance"]}
   - GridSearchCV(cv=3, scoring='f1_macro', n_jobs=-1, verbose=1)
   - 반환: (best_model, best_params, cv_results_df)

5. run_full_experiment(X_train, y_train, X_test, y_test, class_names: list[str], experiment_name: str = "experiment") -> pd.DataFrame
   - 모든 모델에 대한 전체 실험 실행
   - get_models()의 5개 모델 순차 학습+평가
   - 결과를 DataFrame으로 집약 (행: 모델, 열: accuracy, f1_macro, recall_macro, precision_macro, train_time)
   - 각 모델의 상세 결과를 딕셔너리로도 반환
   - 반환: (summary_df, detailed_results_dict)

6. save_model(model, scaler, feature_pipeline_config: dict, filepath: str)
   - 모델과 관련 정보를 joblib으로 저장
   - 저장 내용: {"model": model, "scaler": scaler, "config": feature_pipeline_config, "class_names": list, "timestamp": str}
   - joblib.dump() 사용

7. load_model(filepath: str) -> dict
   - 저장된 모델 로드
   - joblib.load() 사용
   - 반환: 저장 시의 딕셔너리

[코딩 규칙]
- sklearn: SVC, RandomForestClassifier, KNeighborsClassifier, GridSearchCV, cross_validate
- sklearn.metrics: classification_report, confusion_matrix, accuracy_score
- 학습/예측 시간: time.time() 으로 측정
- probability=True (SVC) 필수 — ROC 커브에 필요
- n_jobs=-1 — M4 Pro 12코어 활용
- import: sklearn, numpy, pandas, joblib, time, typing

[테스트]
- if __name__ == "__main__": 블록
- 30장(5/class) 소규모 데이터로 train_single_model() 테스트
- 모델 저장/로딩 테스트
```

---

## 🚀 Phase 6: 모델 평가 및 시각화 모듈

### 6.1 Claude Code 지시사항

```
다음 요구사항에 따라 models/evaluate.py를 구현해줘.

[파일 위치] models/evaluate.py

[기능 요구사항]

1. plot_confusion_matrix(cm: np.ndarray, class_names: list[str], title: str = "혼동행렬", save_path: str = None, normalize: bool = True) -> None
   - seaborn heatmap으로 혼동행렬 시각화
   - normalize=True: 행 기준 정규화 (각 실제 클래스별 비율)
   - annot=True, fmt=".2f" (정규화) 또는 "d" (원본)
   - cmap: "Blues"
   - figsize=(10, 8)
   - x/y 라벨에 한글 클래스명 사용
   - save_path 지정 시 파일 저장

2. plot_classification_report(report_dict: dict, class_names: list[str], title: str = "분류 리포트", save_path: str = None) -> None
   - classification_report를 히트맵으로 시각화
   - 행: 클래스명, 열: precision, recall, f1-score
   - seaborn heatmap, annot=True, fmt=".3f", cmap="YlOrRd"
   - figsize=(10, 8)

3. plot_roc_curves(y_test, y_prob, class_names: list[str], title: str = "ROC 커브", save_path: str = None) -> None
   - One-vs-Rest ROC 커브
   - sklearn.preprocessing.label_binarize()로 라벨 이진화
   - sklearn.metrics.roc_curve, auc 사용
   - 각 클래스별 ROC 커브 + micro/macro 평균 ROC
   - 범례에 AUC 값 표시
   - figsize=(10, 8)
   - 대각선(random classifier) 점선 표시

4. plot_model_comparison(summary_df: pd.DataFrame, metrics: list[str] = ["accuracy", "f1_macro", "recall_macro"], title: str = "모델 성능 비교", save_path: str = None) -> None
   - 여러 모델의 성능을 grouped bar chart로 비교
   - x축: 모델명, y축: 성능 수치, 색상: 메트릭 종류
   - 바 위에 수치 표시 (소수점 3자리)
   - figsize=(14, 6)

5. plot_experiment_comparison(experiment_results: dict[str, pd.DataFrame], metric: str = "f1_macro", save_path: str = None) -> None
   - 여러 실험 조건(전처리/특징 조합)의 성능을 비교
   - experiment_results: {"실험명": summary_df, ...}
   - 히트맵: 행=실험 조건, 열=모델명, 값=metric
   - figsize=(12, 8)

6. plot_feature_importance(model, feature_names: list[str], top_n: int = 20, title: str = "특징 중요도", save_path: str = None) -> None
   - RandomForest의 feature_importance 시각화
   - 상위 top_n개 특징을 수평 바 차트로
   - 특징 이름에 소속 그룹(HOG, LBP, Stats, Contour, Edge) 색상 구분
   - figsize=(12, 8)
   - ⚠️ SVM/KNN은 feature_importance가 없으므로 permutation_importance 사용
   - sklearn.inspection.permutation_importance 활용

7. plot_misclassified_samples(X_test_images: np.ndarray, y_test, y_pred, class_names: list[str], n_samples: int = 12, save_path: str = None) -> None
   - 오분류된 이미지 샘플 시각화
   - 오분류 인덱스에서 n_samples개 랜덤 선택
   - 각 이미지 위에 "실제: {actual} → 예측: {predicted}" 표시
   - 맞은 예측은 녹색 테두리, 틀린 예측은 빨간 테두리
   - figsize=(20, ceil(n_samples/4)*5)

8. plot_learning_curve(model, X, y, cv: int = 5, train_sizes: np.ndarray = np.linspace(0.1, 1.0, 10), title: str = "학습 곡선", save_path: str = None) -> None
   - sklearn.model_selection.learning_curve() 사용
   - 학습 데이터 크기에 따른 train/validation 성능 변화
   - 평균 ± 표준편차 영역(fill_between) 표시
   - figsize=(10, 6)

9. generate_full_report(result: dict, class_names: list[str], experiment_name: str, output_dir: str = "outputs/figures") -> None
   - 단일 모델 결과에 대한 전체 리포트 자동 생성
   - 생성 파일:
     - {experiment_name}_{model_name}_confusion_matrix.png
     - {experiment_name}_{model_name}_classification_report.png
     - {experiment_name}_{model_name}_roc_curves.png
   - 모든 시각화를 자동 저장

10. print_recall_analysis(cm: np.ndarray, class_names: list[str]) -> None
    - 제조업 맥락 Recall 분석 출력
    - 각 클래스별 Recall과 "놓친 불량 수(FN)" 출력
    - "가장 위험한 결함(Recall이 가장 낮은 클래스)" 강조
    - "가장 혼동되는 쌍(off-diagonal 최대값)" 식별
    - 포맷: 표 형태로 깔끔하게 print

[코딩 규칙]
- 모든 plot 함수에 plt.tight_layout(), 한글 폰트 설정 포함
- save_path가 None이면 plt.show()만, 아니면 저장 후 plt.close()
- dpi=150, bbox_inches='tight'
- 색상 팔레트 통일: Set2 또는 tab10
- import: matplotlib, seaborn, sklearn.metrics, sklearn.inspection, numpy, pandas

[테스트]
- if __name__ == "__main__": 블록
- 더미 confusion matrix로 plot_confusion_matrix() 테스트
- 더미 y_prob로 plot_roc_curves() 테스트
```

---

## 🚀 Phase 7: 추론 파이프라인

### 7.1 Claude Code 지시사항

```
다음 요구사항에 따라 models/inference.py를 구현해줘.

[파일 위치] models/inference.py

[기능 요구사항]

1. DefectClassifier 클래스 구현

class DefectClassifier:
    def __init__(self, model_path: str):
        """
        저장된 모델을 로드하여 추론 파이프라인 구성.
        
        model_path: joblib으로 저장된 모델 파일 경로
        로드 시 model, scaler, config, class_names를 복원
        config 기반으로 FeaturePipeline 재구성
        """
    
    def predict(self, image: np.ndarray) -> dict:
        """
        단일 이미지에 대한 결함 분류.
        
        반환: {
            "predicted_class": str,       # 예측된 결함 유형 (한글)
            "predicted_label": int,       # 예측된 라벨 (0~5)
            "confidence": float,          # 예측 확률의 최대값
            "probabilities": dict,        # {클래스명: 확률} 딕셔너리
            "preprocessing_time_ms": float,
            "feature_extraction_time_ms": float,
            "prediction_time_ms": float,
            "total_time_ms": float
        }
        """
    
    def predict_batch(self, images: np.ndarray) -> list[dict]:
        """여러 이미지 일괄 추론"""
    
    def predict_with_visualization(self, image: np.ndarray) -> dict:
        """
        추론 + 시각화 정보 반환 (Streamlit 대시보드용).
        
        반환: predict() 결과 + {
            "preprocessed_image": np.ndarray,    # 전처리된 이미지
            "hog_visualization": np.ndarray,     # HOG 시각화 이미지
            "edge_map": np.ndarray,              # 에지 검출 결과
            "contour_image": np.ndarray,         # 윤곽선 시각화
            "edge_density_map": np.ndarray       # 에지 밀도 히트맵
        }
        """
    
    def get_model_info(self) -> dict:
        """모델 정보 반환 (모델명, 특징 차원, 클래스 수 등)"""

2. quick_inference(image_path: str, model_path: str) -> None
   - CLI용 간편 추론 함수
   - 이미지 로드 → 추론 → 결과 출력
   - 용도: 커맨드라인에서 빠른 테스트

[코딩 규칙]
- 시간 측정: time.time() (ms 단위로 변환)
- 모델 파일 미존재 시 FileNotFoundError
- 이미지 로드 실패 시 적절한 에러 메시지
- import: cv2, numpy, joblib, time, typing

[테스트]
- if __name__ == "__main__": 블록
- 저장된 모델로 NEU 이미지 6장 추론 테스트
- 각 추론 결과의 confidence, 처리 시간 출력
- predict_with_visualization()으로 시각화 정보 포함 추론 테스트
```

---

## 🚀 Phase 8: 통합 분석 노트북

### 8.1 Claude Code 지시사항

```
다음 요구사항에 따라 notebooks/04_classification.ipynb를 구현해줘.

[파일 위치] notebooks/04_classification.ipynb

[셀 구성]

## ===== 환경 설정 =====

## 셀 1: 환경 설정 및 import
- 전체 라이브러리 import
- 모든 모듈 import (preprocessing, features, models, utils)
- 전처리 파이프라인 함수 정의 (소주제 ②의 최적 파이프라인)
- matplotlib 한글 폰트, 시각화 스타일 설정
- 랜덤 시드 고정: np.random.seed(42)
- outputs/figures/, models/saved/ 디렉토리 확인/생성

## 셀 2: 데이터 로드 및 분할
- NEUDataLoader로 전체 데이터 로드
- 클래스명 한글 매핑: ["균열", "개재물", "패치", "구멍", "압연스케일", "스크래치"]
- train/test 분할 (test_size=0.2, stratify=True, random_state=42)
- 분할 결과 출력: 클래스별 train/test 이미지 수
- X_train_images, X_test_images, y_train, y_test 변수 저장
  (images는 원본 이미지 배열, 전처리는 FeaturePipeline 내부에서 처리)

## ===== Part 1: 특징 추출 (5가지 실험 조건) =====

## 셀 3: 실험 조건 정의
- create_experiment_configs()로 5가지 실험 설정 생성
- 각 실험 조건을 표로 출력:
  | 실험명 | 전처리 | HOG | LBP | Stats | Contour | Edge | 예상 차원 |
- 전처리 함수: 소주제 ②의 최적 파이프라인

## 셀 4: Exp-1 (Baseline) 특징 추출
- FeaturePipeline(use_hog=True, 나머지 False, preprocess_fn=None)
- extract_batch() 실행 (train + test)
- 특징 행렬 shape 출력, 추출 시간 출력
- 결과 저장: exp1_X_train, exp1_X_test

## 셀 5: Exp-2~5 특징 추출 (반복)
- 나머지 4가지 실험 조건에 대해 동일 프로세스
- 각 실험의 특징 행렬을 딕셔너리에 저장
- 전체 추출 시간 요약 표 출력
- ⚠️ 전체 데이터셋 처리에 시간이 걸리므로 진행률 표시 중요
  (시간이 너무 길면 클래스당 200장으로 샘플링하는 옵션 제공)

## ===== Part 2: 모델 학습 및 비교 =====

## 셀 6: Exp-1 (Baseline: HOG만, 전처리 없음) 전체 모델 학습
- run_full_experiment(exp1_X_train, y_train, exp1_X_test, y_test, class_names, "Baseline")
- summary_df 출력
- 최고 성능 모델 하이라이트

## 셀 7: Exp-2 (HOG만, 전처리 적용) 전체 모델 학습
- 동일 프로세스
- "전처리 효과": Exp-1 vs Exp-2 Accuracy/F1 차이 계산 및 출력

## 셀 8: Exp-3~5 학습 (반복)
- 나머지 실험 조건에 대해 동일 프로세스

## 셀 9: 전체 실험 결과 종합 비교
- 5개 실험 × 5개 모델 = 25개 결과를 하나의 히트맵으로
- plot_experiment_comparison() 호출
- figsize=(14, 8)
- 행: 실험 조건, 열: 모델, 값: F1 Macro
- 최고 성능 조합 강조 (빨간 테두리)
- outputs/figures/04_experiment_comparison_heatmap.png 저장

## 셀 10: 전처리 효과 정량 분석
- Exp-1(전처리 없음) vs Exp-2(전처리 적용) 비교에 집중
- 모델별 Accuracy, F1, Recall 변화량을 바 차트로
- "전처리로 인한 성능 향상: +X.X%" 형태로 출력
- figsize=(12, 6)
- outputs/figures/04_preprocessing_effect.png 저장

## 셀 11: 특징 조합 효과 분석
- Exp-2(HOG만) → Exp-3(+LBP) → Exp-4(+Stats) → Exp-5(+에지/윤곽선)
- 특징 추가에 따른 점진적 성능 변화 선 그래프
- 최적 모델(SVM 또는 RF)을 고정하고 특징 조합만 변경
- x축: 특징 조합, y축: F1/Accuracy
- figsize=(12, 6)
- outputs/figures/04_feature_ablation.png 저장

## ===== Part 3: 최적 모델 심층 분석 =====

## 셀 12: 최적 모델 선정
- 전체 25개 결과에서 F1 Macro 최고 조합 선택
- 해당 조합의 모델 정보, 특징 조건, 성능 수치 출력
- 마크다운 셀: "최적 모델: {모델명}, 특징: {조건명}, F1: {값}"

## 셀 13: 최적 모델 혼동행렬
- plot_confusion_matrix() (정규화 + 원본 둘 다)
- figsize=(10, 8)
- outputs/figures/04_best_confusion_matrix.png 저장
- outputs/figures/04_best_confusion_matrix_counts.png 저장

## 셀 14: 최적 모델 Classification Report
- plot_classification_report() 히트맵
- 별도로 클래스별 Precision/Recall/F1을 바 차트로도 시각화
- figsize=(12, 6)
- outputs/figures/04_best_classification_report.png 저장

## 셀 15: 최적 모델 ROC 커브
- plot_roc_curves()
- 6클래스 OvR ROC + micro/macro 평균
- figsize=(10, 8)
- outputs/figures/04_best_roc_curves.png 저장

## 셀 16: 제조업 맥락 Recall 분석
- print_recall_analysis() 호출
- "가장 위험한 결함(Recall 최저)" 식별
- "가장 혼동되는 쌍" 식별 및 해당 이미지 비교
- 마크다운 셀로 제조업 관점 해석:
  - FN 비용: "Recall 0.85는 100개 중 15개의 불량이 출하됨을 의미"
  - 개선 방향: "해당 클래스에 특화된 전처리 또는 추가 데이터 필요"

## 셀 17: 오분류 사례 시각화
- plot_misclassified_samples() — 12개 오분류 이미지
- 각 이미지에 실제 클래스 vs 예측 클래스 표시
- outputs/figures/04_misclassified_samples.png 저장

## 셀 18: 오분류 패턴 심층 분석
- 혼동행렬에서 가장 혼동이 큰 2개 클래스 쌍 선택
- 해당 쌍에 속하는 오분류 이미지 6장 + 정분류 이미지 6장을 나란히 비교
- 오분류/정분류 이미지의 HOG 시각화 비교
- figsize=(20, 10)
- 인사이트: "왜 이 두 클래스가 혼동되는가?" 마크다운 분석
- outputs/figures/04_confusion_pair_analysis.png 저장

## ===== Part 4: 추가 분석 =====

## 셀 19: 특징 중요도 분석
- 최적 모델이 RF인 경우: feature_importance 직접 사용
- 최적 모델이 SVM/KNN인 경우: permutation_importance 사용
- plot_feature_importance() — 상위 20개 특징
- 특징 그룹별(HOG, LBP, Stats, Contour, Edge) 중요도 합산 파이 차트 추가
- figsize=(12, 8) + figsize=(8, 8)
- outputs/figures/04_feature_importance.png 저장
- outputs/figures/04_feature_group_importance.png 저장

## 셀 20: 학습 곡선 분석
- 최적 모델에 대해 plot_learning_curve() 
- 데이터 크기 10%~100%에서의 성능 변화
- "데이터가 더 있으면 성능이 향상될 여지가 있는가?" 분석
- figsize=(10, 6)
- outputs/figures/04_learning_curve.png 저장

## 셀 21: 하이퍼파라미터 튜닝
- 최적 모델에 대해 hyperparameter_tuning() 실행
- 튜닝 전/후 성능 비교 표
- 최적 하이퍼파라미터 출력
- 튜닝 후 모델로 다시 전체 평가 실행

## 셀 22: 최종 모델 저장
- 최적 모델(튜닝 후) + scaler + config를 joblib으로 저장
- save_model() 호출
- 저장 경로: models/saved/best_model.joblib
- 저장 성공 메시지 + 파일 크기 출력

## 셀 23: 추론 데모
- DefectClassifier 인스턴스 생성 (저장된 모델 로드)
- 테스트셋에서 각 클래스 1장씩 추론
- predict_with_visualization() 결과를 시각화:
  6행(클래스) × 5열(원본, 전처리, HOG맵, 에지맵, 윤곽선) + 예측 결과 텍스트
- figsize=(20, 24)
- outputs/figures/04_inference_demo.png 저장

## ===== Part 5: 결론 =====

## 셀 24: 전체 프로젝트 결론 (마크다운)
- 마크다운 셀로 전체 프로젝트의 핵심 결론 정리:

### 주요 발견사항
1. **전처리 효과**: 소주제 ②의 전처리 파이프라인(CLAHE→Bilateral→Adaptive Sharpen→Opening) 적용으로 
   분류 성능이 Accuracy 기준 +X.X%, F1 기준 +X.X% 향상
2. **최적 특징 조합**: {조합명}이 최적이며, 특히 {특징 그룹}의 기여가 가장 큼
3. **최적 분류 모델**: {모델명}이 F1 Macro {값}으로 최고 성능
4. **가장 분류 어려운 결함**: {클래스명} (Recall {값}), {혼동 쌍} 간 혼동이 주요 원인
5. **제조업 적용 시사점**: Recall {값}은 {비율}의 불량 출하를 의미, 개선을 위해 {방안} 필요

### 프로젝트 기여도 (소주제별)
- 소주제 ① (정렬/ROI): 밝기 정규화로 일관된 입력 데이터 확보
- 소주제 ② (필터링/샤프닝): 노이즈 제거 + 결함 강조로 특징 추출 품질 향상
- 소주제 ③ (에지/윤곽선): 결함의 형태적·방향적 특징 정량화
- 소주제 ④ (ML 분류): 전처리 효과 증명 + 최적 모델 도출 + 제조업 맥락 분석

### 향후 확장 계획
- Phase 2: PyTorch CNN 적용으로 전통 ML 대비 성능 향상 검증
- Phase 3: MVTec AD 데이터셋 확장 + Unsupervised Anomaly Detection
- Phase 4: Streamlit 대시보드 고도화 + 실시간 추론
- Phase 5: React + FastAPI 웹 서비스 전환

[시각화 규칙]
- 모든 figure에 plt.tight_layout(), 한글 폰트 설정
- 저장 시 dpi=150, bbox_inches='tight'
- 한글 폰트: plt.rcParams['font.family'] = 'AppleGothic'
- plt.rcParams['axes.unicode_minus'] = False
- 색상 팔레트: seaborn color_palette("Set2", 6) 통일
- 각 시각화 셀 끝에 print("✅ 저장 완료: {파일 경로}") 출력
```

---

## 📊 산출물 체크리스트

### 코드 파일

| 파일 | 상태 | 함수/클래스 수 | 설명 |
|------|------|----------------|------|
| `features/hog_features.py` | ⬜ | 5개 | HOG 특징 추출 |
| `features/lbp_features.py` | ⬜ | 6개 | LBP 특징 추출 |
| `features/pixel_stats.py` | ⬜ | 7개 | 픽셀 통계 특징 |
| `features/feature_pipeline.py` | ⬜ | 1클래스+1함수 | 통합 특징 파이프라인 |
| `models/__init__.py` | ⬜ | — | 모델 모듈 init |
| `models/train.py` | ⬜ | 7개 | 모델 학습/저장/로딩 |
| `models/evaluate.py` | ⬜ | 10개 | 평가/시각화 |
| `models/inference.py` | ⬜ | 1클래스+1함수 | 추론 파이프라인 |
| `features/__init__.py` | ⬜ | — | 업데이트 (v0.2.0) |
| `notebooks/04_classification.ipynb` | ⬜ | 24셀 | 분류 분석 노트북 |

### 시각화 산출물

| 파일명 | 상태 | 내용 |
|--------|------|------|
| `04_experiment_comparison_heatmap.png` | ⬜ | 5실험 × 5모델 F1 히트맵 |
| `04_preprocessing_effect.png` | ⬜ | 전처리 전/후 성능 변화 |
| `04_feature_ablation.png` | ⬜ | 특징 추가에 따른 점진적 성능 변화 |
| `04_best_confusion_matrix.png` | ⬜ | 최적 모델 혼동행렬 (정규화) |
| `04_best_confusion_matrix_counts.png` | ⬜ | 최적 모델 혼동행렬 (원본) |
| `04_best_classification_report.png` | ⬜ | 클래스별 P/R/F1 히트맵 |
| `04_best_roc_curves.png` | ⬜ | 6클래스 OvR ROC 커브 |
| `04_misclassified_samples.png` | ⬜ | 오분류 이미지 12개 |
| `04_confusion_pair_analysis.png` | ⬜ | 혼동 쌍 심층 비교 |
| `04_feature_importance.png` | ⬜ | 특징 중요도 Top 20 |
| `04_feature_group_importance.png` | ⬜ | 특징 그룹별 중요도 파이 차트 |
| `04_learning_curve.png` | ⬜ | 학습 곡선 |
| `04_inference_demo.png` | ⬜ | 추론 데모 시각화 |

### 모델 파일

| 파일명 | 상태 | 설명 |
|--------|------|------|
| `models/saved/best_model.joblib` | ⬜ | 최적 모델 + scaler + config |

---

## ⚠️ Claude Code 실행 시 주의사항

### 연산 시간 관련

1. **HOG 특징 추출**: 1,800장 × HOG(기본 파라미터)는 약 2~5분 소요. compact(PCA 512d) 적용 시 PCA fit에 추가 시간.

2. **5가지 실험 × 5가지 모델 = 25회 학습**: SVM(RBF)의 GridSearchCV가 가장 오래 걸림 (클래스당 300장 기준 5~15분). 시간이 부족하면 GridSearchCV를 생략하고 기본 파라미터로 실행.

3. **Permutation Importance**: SVM/KNN의 특징 중요도 계산에 수 분 소요. n_repeats=5로 축소 가능.

4. **전략적 시간 관리**: 전체 파이프라인의 핵심은 "전처리 전/후 비교(Exp-1 vs Exp-2)"와 "최적 모델 분석"이야. 시간이 부족하면 Exp-3~5와 하이퍼파라미터 튜닝을 스킵하고 이 두 가지에 집중.

### 코딩 관련

1. **HOG 차원 불일치**: skimage.feature.hog()의 출력 차원은 파라미터에 따라 달라짐. batch 추출 시 첫 번째 이미지로 차원을 확인한 뒤 배열을 미리 할당.

2. **SVC probability=True**: predict_proba()를 쓰려면 SVC 생성 시 probability=True 필수. 이것이 빠지면 ROC 커브 생성 불가.

3. **StandardScaler 누수 방지**: scaler는 반드시 train 데이터에만 fit하고, test 데이터에는 transform만. FeaturePipeline의 extract_batch()에서 fit_transform, transform()에서 transform만 호출되도록 설계.

4. **NaN/Inf 처리**: 일부 이미지에서 특징 추출이 실패하면 NaN이 들어갈 수 있음. Scikit-learn 모델은 NaN 입력 시 에러 발생. FeaturePipeline에서 np.nan_to_num() 적용.

5. **클래스 라벨 순서**: NEUDataLoader의 라벨 순서와 class_names 리스트 순서가 일치하는지 반드시 확인. 혼동행렬의 행/열 해석에 직접 영향.

### Streamlit 대시보드 연결

| 산출물 | Streamlit Page | 활용 |
|--------|---------------|------|
| `best_model.joblib` | Page 3 (결함 분류기) | 모델 로드 → 업로드 이미지 추론 |
| `DefectClassifier` | Page 3 | predict_with_visualization()으로 결과+시각화 동시 제공 |
| `plot_confusion_matrix()` | Page 4 (성능 분석) | 혼동행렬 인터랙티브 표시 |
| `plot_roc_curves()` | Page 4 | ROC 커브 표시 |
| `plot_feature_importance()` | Page 4 | 특징 중요도 표시 |
| 실험 비교 히트맵 | Page 4 | 전처리 효과 증명 차트 |

---

## 📝 Claude Code 실행 순서 요약

```
1단계: features/hog_features.py 구현 → 테스트
2단계: features/lbp_features.py 구현 → 테스트
3단계: features/pixel_stats.py 구현 → 테스트
4단계: features/feature_pipeline.py 구현 → 테스트
5단계: models/train.py 구현 → 테스트
6단계: models/evaluate.py 구현 → 테스트
7단계: models/inference.py 구현 → 테스트
8단계: features/__init__.py 업데이트 + models/__init__.py 생성
9단계: notebooks/04_classification.ipynb 전체 실행 → 시각화 + 모델 저장
10단계: 산출물 체크리스트 확인
```

각 단계별로 Claude Code에 해당 Phase의 지시사항을 복사하여 실행하면 됩니다.

---

## 🔗 전체 프로젝트 파이프라인 최종 요약

```
[소주제 ①]                [소주제 ②]              [소주제 ③]              [소주제 ④]
정렬/ROI/정규화    →    필터링/샤프닝/모폴로지  →  에지/윤곽선/특징추출  →  ML 분류/평가
                                                                            │
alignment.py            filters.py               thresholding.py          hog_features.py
roi.py                  sharpening.py            edge_detection.py        lbp_features.py
normalization.py        morphology.py            contour_features.py      pixel_stats.py
data_loader.py          filter_utils.py          edge_features.py         feature_pipeline.py
                                                                          train.py
                                                                          evaluate.py
                                                                          inference.py
                                                          │
                                                          ▼
                                                  [Streamlit 대시보드]
                                                  Page 1: EDA
                                                  Page 2: 전처리 실험실
                                                  Page 3: 결함 분류기
                                                  Page 4: 성능 분석
```
