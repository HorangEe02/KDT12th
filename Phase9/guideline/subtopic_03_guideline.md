# 📐 소주제 ③ — 에지 검출 및 윤곽선 기반 특징 분석

## Claude Code 실행 가이드라인

> **프로젝트**: OpenCV & ML 하이브리드 부품 결함 자동 검수 시스템  
> **연계 차시**: 4차시 (임계값 처리, 에지 검출, 윤곽선 분석)  
> **담당 역할**: A. 데이터 & 전처리 / B. 특징 추출 & 모델링 (공동)  
> **작성일**: 2026.03.19

---

## 📋 실행 전 체크리스트

### 사전 준비 사항

1. **소주제 ①② 완료 확인**
   - `utils/data_loader.py` — NEUDataLoader 클래스 ✅
   - `preprocessing/alignment.py` — 이미지 정렬 ✅
   - `preprocessing/roi.py` — ROI 추출 ✅
   - `preprocessing/normalization.py` — 밝기/대비 정규화 ✅
   - `preprocessing/filters.py` — 블러/노이즈 제거 ✅
   - `preprocessing/sharpening.py` — 샤프닝/결함 강조 ✅
   - `preprocessing/morphology.py` — 모폴로지 연산 ✅
   - `utils/filter_utils.py` — 필터 평가 유틸리티 ✅
   - ⚠️ 최소한 `data_loader.py`, `filters.py`(bilateral_filter), `normalization.py`(clahe)가 필요

2. **소주제 ②에서 확정된 최적 전처리 파이프라인**
   ```python
   # 소주제 ②의 결론: 이 파이프라인을 에지 검출 입력으로 사용
   img = clahe_equalization(raw_img)
   img = bilateral_filter(img, d=9, sigma_color=75, sigma_space=75)
   img = adaptive_sharpen(img, blur_ksize=5, sharp_amount=1.5, noise_threshold=10)
   img = opening(img, kernel_shape="rect", kernel_size=3)
   ```

3. **프로젝트 디렉토리 구조 (소주제 ③ 추가분)**
   ```
   project_root/
   ├── data/
   │   └── NEU-DET/                          # 데이터셋
   ├── preprocessing/
   │   ├── __init__.py                       # (소주제 ②에서 v0.2.0)
   │   ├── alignment.py                      # (소주제 ①)
   │   ├── roi.py                            # (소주제 ①)
   │   ├── normalization.py                  # (소주제 ①)
   │   ├── filters.py                        # (소주제 ②)
   │   ├── sharpening.py                     # (소주제 ②)
   │   ├── morphology.py                     # (소주제 ②)
   │   ├── thresholding.py                   # [이 가이드에서 생성] 임계값 처리 모듈
   │   └── edge_detection.py                 # [이 가이드에서 생성] 에지 검출 모듈
   ├── features/
   │   ├── __init__.py                       # [이 가이드에서 생성]
   │   ├── contour_features.py              # [이 가이드에서 생성] 윤곽선 기반 특징 추출
   │   └── edge_features.py                 # [이 가이드에서 생성] 에지 기반 특징 추출
   ├── utils/
   │   ├── __init__.py
   │   ├── data_loader.py                    # (소주제 ①)
   │   └── filter_utils.py                   # (소주제 ②)
   ├── notebooks/
   │   ├── 01_alignment_roi.ipynb            # (소주제 ①)
   │   ├── 02_filtering_sharpening.ipynb     # (소주제 ②)
   │   └── 03_edge_contour_analysis.ipynb    # [이 가이드에서 생성] 분석 노트북
   ├── outputs/
   │   └── figures/
   └── README.md
   ```

---

## 🎯 소주제 ③ 목표 및 범위

### 최종 목표

NEU 금속 표면 결함 이미지에 대해 **임계값 처리 → 에지 검출 → 윤곽선 분석 → 특징 벡터 추출**의 파이프라인을 구축하고, 결함 유형별 에지/윤곽선 특성의 차이를 정량화하여 소주제 ④(ML 분류)의 특징 벡터로 활용할 기반을 마련한다.

### 핵심 질문

이 소주제가 답해야 할 핵심 질문은 다음과 같다:

1. **어떤 에지 검출 방법이 금속 결함에 최적인가?** Canny, Sobel, Laplacian, 적응형 임계값 중 결함 경계를 가장 정확하게 추출하는 방법은?
2. **전처리가 에지 검출 품질에 미치는 영향은?** 소주제 ②의 필터링 파이프라인 적용 전/후, 에지 검출 결과가 어떻게 달라지는가?
3. **윤곽선 특징으로 6종 결함을 구분할 수 있는가?** 윤곽선 수, 면적, 둘레, 복잡도 등의 수치적 특징만으로 클래스 간 분리가 가능한가?
4. **에지 밀도 분포가 결함 유형의 "지문" 역할을 할 수 있는가?** 공간적 에지 분포 패턴이 결함 유형별로 고유한 시그니처를 보이는가?

### 세부 목표

| # | 목표 | 산출물 |
|---|------|--------|
| 1 | 임계값 처리 모듈 구현 | `thresholding.py` |
| 2 | 에지 검출 모듈 구현 | `edge_detection.py` |
| 3 | 윤곽선 기반 특징 추출 모듈 구현 | `contour_features.py` |
| 4 | 에지 기반 특징 추출 모듈 구현 | `edge_features.py` |
| 5 | 결함 유형별 에지/윤곽선 특성 정량 분석 | `03_edge_contour_analysis.ipynb` |

---

## 🚀 Phase 1: 임계값 처리 모듈

### 1.1 배경 설명

임계값 처리(Thresholding)는 그레이스케일 이미지를 이진(흑/백) 이미지로 변환하는 기법이다. 에지 검출과 윤곽선 분석의 전단계로, 결함 영역과 배경을 분리하는 데 핵심적 역할을 한다. 금속 표면의 불균일한 조명과 광택 반사 때문에 단순 전역 임계값보다 **적응형 임계값**이 더 효과적인 경우가 많다.

### 1.2 Claude Code 지시사항

```
다음 요구사항에 따라 preprocessing/thresholding.py를 구현해줘.

[파일 위치] preprocessing/thresholding.py

[기능 요구사항]

1. global_threshold(image: np.ndarray, thresh_value: int = 127, max_value: int = 255, thresh_type: int = cv2.THRESH_BINARY) -> tuple[np.ndarray, int]
   - 전역 고정 임계값 이진화
   - cv2.threshold() 사용
   - thresh_type 옵션: cv2.THRESH_BINARY, THRESH_BINARY_INV, THRESH_TRUNC, THRESH_TOZERO, THRESH_TOZERO_INV
   - 반환: (이진화 이미지, 사용된 임계값)

2. otsu_threshold(image: np.ndarray, max_value: int = 255) -> tuple[np.ndarray, int]
   - Otsu's 자동 임계값 결정
   - cv2.threshold() + cv2.THRESH_OTSU 플래그 사용
   - 이미지의 히스토그램 분포에서 최적의 임계값을 자동 계산
   - 반환: (이진화 이미지, Otsu가 결정한 임계값)
   - 용도: 단순하면서도 효과적인 자동 이진화. 배경과 결함의 밝기 차이가 뚜렷한 경우 적합

3. adaptive_threshold_mean(image: np.ndarray, max_value: int = 255, block_size: int = 11, C: int = 2) -> np.ndarray
   - 적응형 임계값 (평균 기반)
   - cv2.adaptiveThreshold() + cv2.ADAPTIVE_THRESH_MEAN_C 사용
   - block_size: 로컬 영역 크기 (홀수, 3 이상)
   - C: 계산된 평균에서 빼는 상수 (높을수록 더 많은 영역이 흰색으로)
   - 용도: 조명이 불균일한 금속 표면에서 국소적 밝기 변화에 대응

4. adaptive_threshold_gaussian(image: np.ndarray, max_value: int = 255, block_size: int = 11, C: int = 2) -> np.ndarray
   - 적응형 임계값 (가우시안 가중 기반)
   - cv2.adaptiveThreshold() + cv2.ADAPTIVE_THRESH_GAUSSIAN_C 사용
   - 평균 기반보다 중심부에 더 높은 가중치를 부여
   - 용도: 에지 근처에서 더 부드러운 이진화. Mean 방식보다 노이즈에 강건

5. multi_threshold(image: np.ndarray, thresholds: list[int] = [64, 128, 192]) -> np.ndarray
   - 다중 임계값 (이미지를 여러 단계로 분할)
   - 각 임계값 구간에 서로 다른 밝기 할당 (0, 85, 170, 255 등 균등 분배)
   - np.digitize() + 구간별 매핑으로 구현
   - 반환: 다중 레벨 이미지 (uint8)
   - 용도: 결함의 심각도(깊이)를 단계적으로 표현

6. triangle_threshold(image: np.ndarray, max_value: int = 255) -> tuple[np.ndarray, int]
   - 삼각형 알고리즘 기반 임계값
   - cv2.threshold() + cv2.THRESH_TRIANGLE 사용
   - 히스토그램이 한쪽으로 치우친 경우 효과적
   - 반환: (이진화 이미지, 결정된 임계값)
   - 용도: 결함 영역이 전체 이미지의 극소 비율인 경우 (대부분 배경, 소량 결함)

7. compare_thresholds(image: np.ndarray, block_size: int = 11) -> dict[str, np.ndarray]
   - 모든 임계값 방법의 결과를 한번에 비교
   - 반환: {
       "original": img,
       "global_127": img,
       "otsu": img,
       "triangle": img,
       "adaptive_mean": img,
       "adaptive_gaussian": img,
       "multi_3level": img
     }

8. find_optimal_threshold(image: np.ndarray) -> dict[str, any]
   - 이미지 특성에 따른 최적 임계값 방법 추천
   - 분석 기준:
     a. 히스토그램의 쌍봉(bimodal) 여부 → bimodal이면 Otsu 추천
     b. 밝기 분포의 편향도(skewness) → 편향이 크면 Triangle 추천
     c. 조명 균일도 (이미지를 4등분하여 평균 밝기 차이 계산) → 차이가 크면 Adaptive 추천
   - 반환: {"recommended_method": str, "otsu_threshold": int, "triangle_threshold": int, "illumination_uniformity": float, "histogram_bimodality": float}

[코딩 규칙]
- Type hints 사용
- Docstring 작성 (Google style)
- 모든 함수는 입력 이미지를 변경하지 않음 (copy 후 처리)
- block_size 홀수 검증 + 자동 보정 (짝수 시 +1)
- block_size 최소값 3 검증
- 입력 이미지 유효성 검사: None 체크, ndim 체크 (그레이스케일만 허용)
- import: cv2, numpy, typing, warnings, scipy.stats (skewness 계산용)

[테스트]
- if __name__ == "__main__": 블록에서 테스트
- NEU 데이터셋에서 각 클래스 1장씩 로드
- compare_thresholds()로 전체 방법 비교
- find_optimal_threshold()로 각 클래스별 추천 방법 출력
- Otsu 임계값이 클래스별로 어떻게 다른지 표로 출력
```

---

## 🚀 Phase 2: 에지 검출 모듈

### 2.1 배경 설명

에지 검출은 이미지에서 밝기가 급격히 변하는 경계를 찾아내는 기법이다. 금속 표면 결함에서 에지는 곧 **결함의 경계**를 의미하며, 결함의 형태와 크기를 파악하는 핵심 단서다. 

Canny가 가장 널리 사용되지만, 결함 유형에 따라 Sobel(방향성 에지)이나 Laplacian(2차 미분)이 더 효과적일 수 있다. 이 모듈은 다양한 에지 검출 방법을 구현하고, **소주제 ②의 전처리 적용 전/후** 에지 검출 품질 차이를 분석하는 기반을 제공한다.

### 2.2 Claude Code 지시사항

```
다음 요구사항에 따라 preprocessing/edge_detection.py를 구현해줘.

[파일 위치] preprocessing/edge_detection.py

[기능 요구사항]

1. canny_edge(image: np.ndarray, low_threshold: int = 50, high_threshold: int = 150, aperture_size: int = 3) -> np.ndarray
   - Canny 에지 검출 (가장 표준적인 방법)
   - cv2.Canny() 사용
   - low_threshold / high_threshold: 이중 임계값으로 강한 에지와 약한 에지를 구분
   - aperture_size: Sobel 커널 크기 (3, 5, 7)
   - 반환: 에지 이진 이미지 (0 또는 255)

2. auto_canny(image: np.ndarray, sigma: float = 0.33) -> tuple[np.ndarray, int, int]
   - 자동 임계값 Canny 에지 검출
   - 구현 방법:
     a. 이미지의 중앙값(median) 계산
     b. low = max(0, int((1.0 - sigma) * median))
     c. high = min(255, int((1.0 + sigma) * median))
     d. cv2.Canny(image, low, high) 적용
   - sigma: 임계값 범위 조절 (값이 클수록 더 넓은 범위 → 더 많은 에지)
   - 반환: (에지 이미지, low_threshold, high_threshold)
   - 용도: 이미지별로 최적의 임계값을 자동 결정. 클래스별 밝기 분포가 다른 NEU 데이터에 적합

3. sobel_edge(image: np.ndarray, dx: int = 1, dy: int = 1, ksize: int = 3, combine_method: str = "magnitude") -> np.ndarray
   - Sobel 에지 검출 (방향성 에지)
   - dx, dy: x/y 방향 미분 차수
   - combine_method:
     - "magnitude": sqrt(sobel_x² + sobel_y²)
     - "x_only": x 방향 에지만
     - "y_only": y 방향 에지만
     - "both_separate": x, y 각각 반환 (이 경우 반환 타입이 tuple)
   - cv2.Sobel() + cv2.convertScaleAbs() 사용
   - 결과를 0~255로 정규화
   - 용도: Scratches(수평/수직 방향성)의 에지 방향을 분석할 때 유용

4. laplacian_edge(image: np.ndarray, ksize: int = 3) -> np.ndarray
   - 라플라시안 에지 검출 (2차 미분, 방향성 없음)
   - cv2.Laplacian() + cv2.convertScaleAbs() 사용
   - 반환: 0~255 정규화된 에지 이미지
   - 용도: 모든 방향의 에지를 균등하게 검출. 노이즈에 민감하므로 사전 블러 필요

5. scharr_edge(image: np.ndarray, combine_method: str = "magnitude") -> np.ndarray
   - Scharr 에지 검출 (Sobel의 개선 버전, 3×3에서 더 정확)
   - cv2.Scharr() 사용 (dx=1,dy=0 과 dx=0,dy=1 각각 계산)
   - combine_method: "magnitude", "x_only", "y_only"
   - 반환: 0~255 정규화된 에지 이미지
   - 용도: Sobel보다 회전 대칭성이 좋아 미세 결함 검출에 유리

6. log_edge(image: np.ndarray, sigma: float = 1.0, threshold: int = 0) -> np.ndarray
   - Laplacian of Gaussian (LoG) 에지 검출
   - 구현 방법:
     a. 가우시안 블러(sigma) 적용으로 노이즈 제거
     b. 라플라시안 적용으로 에지 검출
     c. threshold 이상인 픽셀만 에지로 판정
   - 반환: 에지 이진 이미지
   - 용도: 노이즈에 강건한 에지 검출. sigma로 검출할 에지의 스케일 제어

7. multi_scale_edge(image: np.ndarray, method: str = "canny", scales: list[float] = [0.5, 1.0, 2.0]) -> dict[float, np.ndarray]
   - 멀티스케일 에지 검출
   - 구현 방법:
     a. 각 scale에 대해 가우시안 블러(sigma=scale) 적용
     b. 블러된 이미지에서 지정된 method로 에지 검출
     c. method가 "canny"이면 auto_canny 사용
   - 반환: {scale: edge_image} 딕셔너리
   - 용도: 미세 결함(작은 scale)과 대형 결함(큰 scale)을 동시에 탐지

8. edge_direction_map(image: np.ndarray, ksize: int = 3) -> tuple[np.ndarray, np.ndarray]
   - 에지 방향 맵 생성
   - 구현 방법:
     a. Sobel x, y 각각 계산 (float64)
     b. magnitude = sqrt(sobel_x² + sobel_y²)
     c. direction = arctan2(sobel_y, sobel_x) → 라디안 (-π ~ π)
     d. direction을 도(degree, 0~360)로 변환
   - 반환: (magnitude_map, direction_map)
   - 용도: 결함의 방향성 분석. Scratches는 특정 방향에 에지가 집중되는 특성

9. combine_edges(edge_images: list[np.ndarray], method: str = "union") -> np.ndarray
   - 여러 에지 검출 결과를 결합
   - method:
     - "union": OR 연산 (모든 에지 포함, 높은 Recall)
     - "intersection": AND 연산 (공통 에지만, 높은 Precision)
     - "weighted": 가중 평균 (각 결과를 float로 변환 후 평균, 임계값 적용)
   - 반환: 결합된 에지 이미지

10. compare_edge_methods(image: np.ndarray) -> dict[str, np.ndarray]
    - 모든 에지 검출 방법의 결과를 한번에 비교
    - 반환: {
        "original": img,
        "canny_auto": img,
        "canny_tight": img (low=100, high=200),
        "canny_wide": img (low=30, high=100),
        "sobel_magnitude": img,
        "sobel_x": img,
        "sobel_y": img,
        "laplacian": img,
        "scharr": img,
        "log_sigma1": img,
        "log_sigma2": img
      }

11. evaluate_edge_quality(original: np.ndarray, edge: np.ndarray) -> dict[str, float]
    - 에지 검출 결과의 품질 평가
    - 반환: {
        "edge_density": float,          # 에지 픽셀 비율
        "edge_continuity": float,       # 연결된 에지의 평균 길이 (윤곽선 길이 기반)
        "edge_count": int,              # 검출된 독립 에지 세그먼트 수
        "mean_edge_strength": float,    # Sobel magnitude의 평균 (에지 부분만)
        "edge_uniformity": float        # 에지 밀도의 공간적 균일도 (4분면 기준)
      }

[코딩 규칙]
- Type hints 사용
- Docstring 작성 (Google style)
- 모든 함수는 입력 이미지를 변경하지 않음
- Sobel/Laplacian 결과의 음수 처리: cv2.convertScaleAbs() 또는 np.abs() + np.clip()
- float 연산 후 반드시 uint8로 변환 전 np.clip(0, 255) 적용
- import: cv2, numpy, typing, warnings, math

[테스트]
- if __name__ == "__main__": 블록에서 테스트
- NEU 데이터셋 6클래스 각 1장 로드
- compare_edge_methods()로 Scratches 이미지 전체 비교 출력
- auto_canny()의 자동 임계값이 클래스별로 어떻게 결정되는지 출력
- edge_direction_map()으로 Scratches의 에지 방향 분포 출력 (히스토그램)
- evaluate_edge_quality()로 Canny vs Sobel 품질 비교 출력
```

---

## 🚀 Phase 3: 윤곽선 기반 특징 추출 모듈

### 3.1 배경 설명

윤곽선(Contour)은 이진화된 이미지에서 동일한 밝기/색상을 가진 연결 영역의 경계선이다. 윤곽선의 수, 면적, 둘레, 형태 복잡도, 볼록도 등의 수치적 특징은 결함 유형을 구분하는 강력한 정보가 된다.

예를 들어 Scratches는 **길고 가느다란 윤곽선**(높은 종횡비), Pitted Surface는 **작고 원형인 다수의 윤곽선**(높은 원형도), Crazing은 **복잡하게 분기하는 네트워크 윤곽선**(높은 복잡도)을 보일 것으로 예상된다. 이러한 특징을 정량화하여 소주제 ④(ML 분류)의 feature vector에 포함시킨다.

### 3.2 Claude Code 지시사항

```
다음 요구사항에 따라 features/contour_features.py를 구현해줘.

[파일 위치] features/contour_features.py

[기능 요구사항]

1. find_contours(image: np.ndarray, threshold_method: str = "otsu", min_area: int = 5) -> tuple[list, np.ndarray]
   - 이미지에서 윤곽선 검출
   - 구현 방법:
     a. threshold_method에 따라 이진화 ("otsu", "adaptive_mean", "adaptive_gaussian", "canny")
       - "canny"의 경우 auto_canny 사용 후 결과를 이진 이미지로 활용
     b. cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
     c. min_area 이하의 노이즈 윤곽선 필터링
   - 반환: (contours 리스트, 사용된 이진 이미지)

2. compute_contour_stats(contour: np.ndarray) -> dict[str, float]
   - 단일 윤곽선의 기하학적 특징 계산
   - 반환: {
       "area": float,                # cv2.contourArea()
       "perimeter": float,           # cv2.arcLength(contour, True)
       "circularity": float,         # 4π × area / perimeter² (1.0 = 완전한 원)
       "aspect_ratio": float,        # 바운딩 박스의 가로/세로 비율
       "extent": float,              # 윤곽선 면적 / 바운딩 박스 면적
       "solidity": float,            # 윤곽선 면적 / 볼록 껍질(convex hull) 면적
       "equiv_diameter": float,      # sqrt(4 × area / π)
       "orientation": float,         # cv2.fitEllipse()의 회전 각도 (점이 5개 이상일 때만)
       "bounding_rect": tuple,       # (x, y, w, h)
       "hu_moments": np.ndarray      # cv2.HuMoments(cv2.moments(contour)) — 7개 값
     }
   - ⚠️ 면적 0인 윤곽선, 점이 5개 미만인 윤곽선의 예외 처리 필요

3. compute_image_contour_features(image: np.ndarray, threshold_method: str = "otsu", min_area: int = 5, top_n: int = 10) -> dict[str, float]
   - 이미지 전체의 윤곽선 기반 통합 특징 벡터 추출
   - 구현 방법:
     a. find_contours()로 윤곽선 검출
     b. 면적 기준 상위 top_n개 윤곽선 선택
     c. 각 윤곽선의 compute_contour_stats() 결과를 집계
   - 반환: {
       "contour_count": int,                    # 총 윤곽선 수
       "total_contour_area": float,             # 전체 윤곽선 면적 합
       "contour_area_ratio": float,             # 전체 윤곽선 면적 / 이미지 면적
       "mean_area": float,                      # 윤곽선 평균 면적
       "std_area": float,                       # 윤곽선 면적 표준편차
       "max_area": float,                       # 최대 윤곽선 면적
       "mean_perimeter": float,                 # 평균 둘레
       "std_perimeter": float,                  # 둘레 표준편차
       "mean_circularity": float,               # 평균 원형도
       "std_circularity": float,                # 원형도 표준편차
       "mean_aspect_ratio": float,              # 평균 종횡비
       "std_aspect_ratio": float,               # 종횡비 표준편차
       "mean_solidity": float,                  # 평균 볼록도
       "std_solidity": float,                   # 볼록도 표준편차
       "mean_extent": float,                    # 평균 extent
       "contour_density": float,                # 윤곽선 수 / 이미지 면적 × 1000
       "largest_contour_hu_moments": np.ndarray # 가장 큰 윤곽선의 Hu Moments (7개)
     }
   - ⚠️ 윤곽선이 0개인 경우 모든 값을 0으로 반환

4. visualize_contours(image: np.ndarray, contours: list, top_n: int = 10) -> np.ndarray
   - 윤곽선을 원본 이미지 위에 컬러로 시각화
   - 그레이스케일 → BGR 변환
   - 상위 top_n개 윤곽선을 서로 다른 색상으로 표시
   - 각 윤곽선에 인덱스 번호 표시 (cv2.putText)
   - 가장 큰 윤곽선의 바운딩 박스를 빨간색으로 표시
   - 반환: 윤곽선이 표시된 컬러 이미지

5. contour_hierarchy_analysis(image: np.ndarray, threshold_method: str = "otsu") -> dict[str, any]
   - 윤곽선 계층 구조 분석
   - cv2.findContours()에서 cv2.RETR_TREE 모드 사용
   - 반환: {
       "total_contours": int,
       "external_contours": int,       # 최외곽 윤곽선 수
       "internal_contours": int,       # 내부(자식) 윤곽선 수
       "max_hierarchy_depth": int,     # 최대 중첩 깊이
       "hierarchy_ratio": float        # 내부 / 외부 비율
     }
   - 용도: Crazing(복잡한 중첩)과 Scratches(단순 외곽선)의 차이 분석

6. extract_contour_feature_vector(image: np.ndarray, threshold_method: str = "otsu") -> np.ndarray
   - ML 분류용 최종 윤곽선 특징 벡터 추출
   - compute_image_contour_features()와 contour_hierarchy_analysis() 결과를 합쳐서
     고정 길이의 1D numpy 배열로 반환
   - Hu Moments의 log 변환 적용: -np.sign(hu) * np.log10(np.abs(hu) + 1e-10)
   - 반환: np.ndarray (shape: (N,) — N은 전체 특징 수)
   - ⚠️ 특징 이름 리스트도 함께 반환하는 get_feature_names() 클래스 메서드 또는 별도 함수 구현

[코딩 규칙]
- Type hints 사용
- Docstring 작성 (Google style)
- 모든 함수는 입력 이미지를 변경하지 않음
- 윤곽선 0개, 면적 0, 점 부족 등 에지 케이스 처리
- division by zero 방지 (둘레 0, 면적 0 등)
- Hu Moments의 0값에 대한 log 변환 안전 처리
- import: cv2, numpy, typing, warnings, math

[테스트]
- if __name__ == "__main__": 블록에서 테스트
- NEU 데이터셋 6클래스 각 1장 로드
- 각 클래스 이미지의 compute_image_contour_features() 결과를 출력
- extract_contour_feature_vector()의 출력 shape 확인
- "Scratches는 종횡비가 높고, Pitted Surface는 원형도가 높다"는 가설 검증 출력
```

---

## 🚀 Phase 4: 에지 기반 특징 추출 모듈

### 4.1 배경 설명

윤곽선 특징이 결함의 "형태"를 캡처한다면, 에지 특징은 결함의 **"패턴과 분포"**를 캡처한다. 에지 밀도(전체/지역별), 에지 방향 분포, 에지 강도 통계 등은 결함 유형의 "지문" 역할을 할 수 있다.

이 모듈은 소주제 ④(ML 분류)에서 HOG, LBP와 함께 사용될 **에지 기반 특징 벡터**를 생성한다.

### 4.2 Claude Code 지시사항

```
다음 요구사항에 따라 features/edge_features.py를 구현해줘.

[파일 위치] features/edge_features.py

[기능 요구사항]

1. compute_edge_density_map(image: np.ndarray, grid_size: int = 4, edge_method: str = "canny") -> np.ndarray
   - 이미지를 grid_size × grid_size로 분할하고 각 셀의 에지 밀도를 계산
   - edge_method: "canny" (auto_canny), "sobel", "laplacian"
   - 반환: (grid_size, grid_size) shape의 에지 밀도 맵 (0.0~1.0)
   - 용도: 결함의 공간적 분포 패턴 추출. Scratches는 특정 행/열에 집중, Crazing은 전체에 분산

2. compute_edge_direction_histogram(image: np.ndarray, n_bins: int = 8) -> np.ndarray
   - 에지 방향 히스토그램 계산
   - 구현 방법:
     a. edge_direction_map()으로 magnitude와 direction 계산
     b. magnitude가 threshold(자동: mean + std) 이상인 에지 픽셀만 선택
     c. 선택된 에지 픽셀의 direction을 n_bins개 구간으로 히스토그램화
     d. magnitude로 가중 (강한 에지가 더 큰 가중치)
     e. L2 정규화 (합=1)
   - 반환: (n_bins,) shape의 정규화된 방향 히스토그램
   - 용도: Scratches는 특정 방향(수평/수직)에 피크, Crazing은 균등 분포

3. compute_edge_intensity_stats(image: np.ndarray) -> dict[str, float]
   - 에지 강도(Sobel magnitude)의 통계 특징
   - 반환: {
       "edge_mean": float,       # 에지 강도 평균 (에지 픽셀만)
       "edge_std": float,        # 에지 강도 표준편차
       "edge_max": float,        # 에지 강도 최대값
       "edge_skewness": float,   # 에지 강도 분포의 왜도
       "edge_kurtosis": float,   # 에지 강도 분포의 첨도
       "edge_energy": float,     # 에지 강도 제곱합 (∑magnitude²) / 픽셀수
       "strong_edge_ratio": float # 강한 에지 비율 (magnitude > mean+2*std)
     }

4. compute_edge_texture_features(image: np.ndarray, grid_size: int = 4) -> dict[str, float]
   - 에지 밀도 맵의 텍스처 특징 (에지 분포의 패턴을 수치화)
   - 구현 방법:
     a. compute_edge_density_map()으로 밀도 맵 생성
     b. 밀도 맵에 대한 통계 계산
   - 반환: {
       "density_mean": float,          # 전체 평균 에지 밀도
       "density_std": float,           # 에지 밀도 표준편차 (불균일도)
       "density_max": float,           # 최대 에지 밀도 셀
       "density_min": float,           # 최소 에지 밀도 셀
       "density_range": float,         # max - min
       "density_concentration": float, # 상위 25% 셀의 밀도 합 / 전체 밀도 합
       "center_vs_border": float,      # 중앙 영역 밀도 / 테두리 영역 밀도
       "horizontal_symmetry": float,   # 좌/우 에지 밀도의 대칭도 (1.0 = 완전 대칭)
       "vertical_symmetry": float      # 상/하 에지 밀도의 대칭도
     }

5. compute_gradient_features(image: np.ndarray) -> dict[str, float]
   - 그래디언트 기반 특징 추출
   - 구현 방법:
     a. Sobel x, y 계산
     b. magnitude, direction 계산
   - 반환: {
       "gradient_mean_magnitude": float,
       "gradient_std_magnitude": float,
       "gradient_mean_direction": float,     # circular mean
       "gradient_std_direction": float,      # circular std
       "gradient_dominant_direction": float,  # 가장 빈도 높은 방향 (degree)
       "gradient_direction_entropy": float    # 방향 분포의 엔트로피 (균등할수록 높음)
     }

6. extract_edge_feature_vector(image: np.ndarray, grid_size: int = 4, n_direction_bins: int = 8) -> np.ndarray
   - ML 분류용 최종 에지 특징 벡터 추출
   - 구성:
     a. 에지 밀도 맵 평탄화 (grid_size × grid_size = 16개 특징)
     b. 에지 방향 히스토그램 (n_direction_bins = 8개 특징)
     c. 에지 강도 통계 (7개 특징)
     d. 에지 텍스처 특징 (9개 특징)
     e. 그래디언트 특징 (6개 특징)
   - 전체를 concatenate하여 고정 길이 벡터로 반환
   - 반환: np.ndarray (shape: (46,) 기본 설정 기준)
   - get_edge_feature_names() 함수도 함께 구현 (특징명 리스트 반환)

7. batch_extract_edge_features(images: np.ndarray, grid_size: int = 4, n_direction_bins: int = 8) -> np.ndarray
   - 여러 이미지에 대해 일괄 에지 특징 추출
   - images shape: (N, H, W)
   - 반환: (N, feature_dim) shape의 특징 행렬
   - 진행률 출력 (매 100장마다 또는 tqdm)
   - 용도: 전체 데이터셋(1,800장)의 특징 행렬을 한번에 생성

[코딩 규칙]
- Type hints 사용
- Docstring 작성 (Google style)
- 에지 픽셀 0개인 경우 안전 처리 (빈 이미지, 완전 무결점 이미지)
- 엔트로피 계산 시 0 * log(0) = 0 처리
- circular mean/std: scipy.stats.circmean, circstd 활용 가능 (또는 직접 구현)
- import: cv2, numpy, typing, warnings, math, scipy.stats

[테스트]
- if __name__ == "__main__": 블록에서 테스트
- NEU 데이터셋 6클래스 각 1장 로드
- 각 클래스의 extract_edge_feature_vector() 결과 shape 확인
- 에지 방향 히스토그램을 클래스별로 비교 출력
  (Scratches: 특정 방향 피크 vs Crazing: 균등 분포 가설 검증)
- batch_extract_edge_features()로 전체 데이터셋 특징 추출 테스트 (시간 측정)
```

---

## 🚀 Phase 5: 통합 분석 노트북

### 5.1 Claude Code 지시사항

```
다음 요구사항에 따라 notebooks/03_edge_contour_analysis.ipynb를 구현해줘.

[파일 위치] notebooks/03_edge_contour_analysis.ipynb

[셀 구성]

## ===== 환경 설정 =====

## 셀 1: 환경 설정 및 import
- 필요한 라이브러리 import (cv2, numpy, matplotlib, seaborn, pandas, os, sys)
- 프로젝트 루트를 sys.path에 추가
- 모듈 import:
  - utils.data_loader에서 NEUDataLoader
  - preprocessing.thresholding에서 함수들
  - preprocessing.edge_detection에서 함수들
  - preprocessing.normalization에서 clahe_equalization
  - preprocessing.filters에서 bilateral_filter
  - preprocessing.sharpening에서 adaptive_sharpen
  - preprocessing.morphology에서 opening
  - features.contour_features에서 함수들
  - features.edge_features에서 함수들
  - utils.filter_utils에서 compute_edge_density
- matplotlib 한글 폰트 설정 (macOS: AppleGothic)
- %matplotlib inline
- plt.style.use('seaborn-v0_8-whitegrid')
- outputs/figures/ 디렉토리 확인

## 셀 2: 데이터 로드 및 전처리 파이프라인 정의
- NEUDataLoader로 전체 데이터 로드
- 소주제 ②에서 확정된 최적 파이프라인 함수 정의:
  ```python
  def preprocess(image):
      img = clahe_equalization(image)
      img = bilateral_filter(img, d=9, sigma_color=75, sigma_space=75)
      img = adaptive_sharpen(img, blur_ksize=5, sharp_amount=1.5, noise_threshold=10)
      img = opening(img, kernel_shape="rect", kernel_size=3)
      return img
  ```
- 각 클래스 대표 이미지 6장 선택 + 전처리 적용 버전 준비
- 원본/전처리 이미지 쌍을 딕셔너리로 저장

## ===== Part 1: 임계값 처리 분석 =====

## 셀 3: 임계값 방법 전체 비교 (6클래스)
- 각 클래스 전처리된 대표 이미지에 compare_thresholds() 적용
- 6행(클래스) × 7열(원본 + 6가지 임계값 방법) 시각화
- 각 이미지 하단에 방법명, 사용된 임계값(해당 시) 표시
- figsize=(24, 24)
- 제목: "임계값 방법별 이진화 결과 비교 (전처리 적용 후)"
- outputs/figures/03_threshold_comparison.png 저장

## 셀 4: Otsu 임계값의 클래스별 차이 분석
- 전체 데이터셋(1,800장)에 otsu_threshold() 적용하여 클래스별 Otsu 임계값 수집
- 클래스별 Otsu 임계값 분포를 박스플롯으로 시각화
- figsize=(12, 6)
- 인사이트: "어떤 클래스의 Otsu 임계값이 가장 높고/낮은가, 그 의미는?" 마크다운 셀
- outputs/figures/03_otsu_distribution.png 저장

## 셀 5: 적응형 임계값 block_size 영향 분석
- Crazing 전처리 이미지에 adaptive_threshold_gaussian() 적용
- block_size: [3, 7, 11, 15, 21, 31, 51]
- C: 2 고정
- 1행 × 7열 시각화 + 각 결과의 흰색 픽셀 비율 표시
- figsize=(24, 4)
- outputs/figures/03_adaptive_blocksize.png 저장

## 셀 6: 최적 임계값 방법 자동 추천
- 각 클래스 대표 이미지에 find_optimal_threshold() 적용
- 결과를 DataFrame으로 정리 (행: 클래스, 열: 추천 방법, Otsu값, 균일도, 이봉성)
- display()로 출력

## ===== Part 2: 에지 검출 분석 =====

## 셀 7: 에지 검출 방법 전체 비교 (6클래스)
- 각 클래스 전처리된 대표 이미지에 compare_edge_methods() 적용
- 6행(클래스) × 11열(원본 + 10가지 에지 방법) 시각화
- figsize=(36, 24)
- ⚠️ 이미지가 많으므로 제목 fontsize=7, 각 이미지 작게
- 각 이미지 하단에 edge_density 표시 (소수점 4자리)
- 제목: "에지 검출 방법별 비교 (전처리 적용 후)"
- outputs/figures/03_edge_comparison_all.png 저장

## 셀 8: 전처리 전/후 에지 검출 품질 비교
- 핵심 분석: 소주제 ②의 전처리가 에지 검출에 미치는 영향
- 각 클래스 대표 이미지에 대해:
  - 원본 → auto_canny 
  - 전처리 → auto_canny
  - 두 결과의 차이(XOR: 전처리에서만 검출된 에지, 원본에서만 검출된 에지)
- 6행(클래스) × 4열(원본 에지, 전처리 에지, 전처리에서만 추가된 에지(녹색), 원본에서 사라진 에지(빨간))
- 추가/사라진 에지는 컬러로 표시 (원본 위에 오버레이)
- figsize=(16, 24)
- outputs/figures/03_preprocessing_effect_on_edge.png 저장

## 셀 9: 전처리 전/후 에지 품질 정량 평가
- 6클래스 × 전체 300장에 대해 evaluate_edge_quality() 적용 (전처리 전/후)
- 클래스별 평균 평가 지표를 DataFrame으로 정리
- 전처리 전/후 edge_density, edge_continuity, edge_count 변화를 grouped bar chart로
- figsize=(14, 8)
- 인사이트: "전처리 후 에지 연속성(continuity)이 향상되었는가?" 마크다운 셀
- outputs/figures/03_edge_quality_before_after.png 저장

## 셀 10: Canny 임계값 파라미터 탐색
- Scratches 전처리 이미지에 canny_edge() 적용
- low_threshold: [20, 50, 80, 100, 150]
- high_threshold: [80, 100, 150, 200, 250]
- 단, low < high 조건을 만족하는 조합만 시각화
- 유효한 조합들을 격자 시각화
- 각 조합의 edge_density 표시
- figsize=(20, 16)
- outputs/figures/03_canny_param_search.png 저장

## 셀 11: 에지 방향 분석 (결함 유형별 방향성)
- 각 클래스 대표 이미지에 edge_direction_map() 적용
- 상단: 6열 — 각 클래스의 에지 magnitude 맵
- 중단: 6열 — 각 클래스의 에지 direction 맵 (HSV 색상 매핑: 방향→색상, 강도→밝기)
  - direction을 0~180도로 매핑 → cv2.applyColorMap 또는 matplotlib colormap
- 하단: 6열 — 에지 방향 히스토그램 (극좌표 바 차트)
  - matplotlib의 projection='polar'로 방향 분포 시각화
- figsize=(24, 14)
- 인사이트: "Scratches는 특정 방향에 에지가 집중되는 반면, Crazing은 전방향에 분산" 분석
- outputs/figures/03_edge_direction_analysis.png 저장

## 셀 12: 멀티스케일 에지 검출
- Crazing 전처리 이미지에 multi_scale_edge() 적용
- scales: [0.3, 0.5, 1.0, 2.0, 3.0, 5.0]
- 1행 × 6열 (스케일별 에지 결과)
- 추가: 모든 스케일의 combine_edges(method="weighted") 결과 표시
- figsize=(24, 4)
- 인사이트: "미세 균열은 작은 스케일에서, 대형 결함은 큰 스케일에서 잘 검출됨"
- outputs/figures/03_multiscale_edge.png 저장

## ===== Part 3: 윤곽선 분석 =====

## 셀 13: 윤곽선 검출 및 시각화 (6클래스)
- 각 클래스 전처리 이미지에 find_contours() + visualize_contours() 적용
- 6행(클래스) × 3열(전처리 이미지, 이진화 결과, 윤곽선 시각화)
- 각 이미지 하단에 검출된 윤곽선 수 표시
- figsize=(15, 24)
- 제목: "클래스별 윤곽선 검출 결과"
- outputs/figures/03_contour_visualization.png 저장

## 셀 14: 윤곽선 특징 클래스별 비교 분석
- 전체 데이터셋(1,800장)에 compute_image_contour_features() 적용
  (시간 절약 위해 클래스당 100장 샘플링 가능)
- 핵심 특징 5개(contour_count, mean_area, mean_circularity, mean_aspect_ratio, mean_solidity)를 
  클래스별 박스플롯으로 시각화
- 2행 × 3열 서브플롯 (5개 특징 + 1개 비워둠 또는 contour_density)
- figsize=(18, 12)
- 인사이트: "어떤 윤곽선 특징이 클래스 간 분리력이 가장 높은가?" 마크다운 셀
- outputs/figures/03_contour_features_boxplot.png 저장

## 셀 15: 윤곽선 특징 산점도 (2D 클래스 분리 확인)
- 가장 분리력 높은 특징 2개를 선택하여 2D 산점도
  (예: mean_circularity vs mean_aspect_ratio)
- 6개 클래스를 서로 다른 색상과 마커로 표시
- figsize=(10, 8)
- 인사이트: "2개 특징만으로 어느 정도 분리가 가능한가?" 분석
- outputs/figures/03_contour_scatter.png 저장

## 셀 16: 윤곽선 계층 구조 분석
- 각 클래스 대표 이미지에 contour_hierarchy_analysis() 적용
- 결과를 DataFrame으로 정리
- Crazing(복잡 중첩)과 Scratches(단순 외곽선)의 차이가 수치로 드러나는지 확인
- grouped bar chart: 클래스별 external/internal 윤곽선 수
- figsize=(12, 6)
- outputs/figures/03_contour_hierarchy.png 저장

## ===== Part 4: 에지 기반 특징 분석 =====

## 셀 17: 에지 밀도 맵 시각화 (6클래스)
- 각 클래스 전처리 이미지에 compute_edge_density_map(grid_size=4) 적용
- 6열: 각 클래스의 에지 밀도 히트맵 (seaborn heatmap, annot=True, fmt=".3f")
- figsize=(24, 4)
- 인사이트: "Scratches는 특정 행/열에 밀도 집중, Crazing은 전반에 분산" 확인
- outputs/figures/03_edge_density_maps.png 저장

## 셀 18: 에지 특징 클래스별 비교 (박스플롯)
- 전체 데이터셋에 extract_edge_feature_vector() 적용
  (시간 절약 위해 클래스당 100장 샘플링 가능)
- 핵심 에지 특징 6개 선택하여 클래스별 박스플롯
  (density_mean, density_concentration, center_vs_border, gradient_direction_entropy, 
   strong_edge_ratio, edge_energy)
- 2행 × 3열 서브플롯
- figsize=(18, 12)
- outputs/figures/03_edge_features_boxplot.png 저장

## 셀 19: 에지 방향 엔트로피 vs 에지 밀도 산점도
- x: gradient_direction_entropy, y: density_mean
- 6클래스 색상 구분
- 예상: Scratches(저엔트로피, 중간 밀도), Crazing(고엔트로피, 고밀도), Patches(저밀도)
- figsize=(10, 8)
- outputs/figures/03_entropy_vs_density.png 저장

## ===== Part 5: 통합 특징 벡터 및 결론 =====

## 셀 20: 윤곽선 + 에지 통합 특징 벡터 생성
- 전체 데이터셋(1,800장)에 대해:
  - contour_feature = extract_contour_feature_vector(preprocess(img))
  - edge_feature = extract_edge_feature_vector(preprocess(img))
  - combined = np.concatenate([contour_feature, edge_feature])
- 전체 특징 행렬 shape 출력
- 특징명 리스트 출력
- 특징 행렬을 numpy 파일로 저장:
  np.save("outputs/contour_edge_features.npy", feature_matrix)
  np.save("outputs/labels.npy", labels)
  (소주제 ④에서 로드하여 사용)

## 셀 21: 특징 간 상관관계 분석
- 통합 특징 벡터의 상관관계 히트맵
- seaborn heatmap, figsize=(16, 14)
- 높은 상관관계(|r| > 0.8)를 가진 특징 쌍 식별 → 소주제 ④에서 제거 또는 PCA 고려
- outputs/figures/03_feature_correlation.png 저장

## 셀 22: t-SNE 시각화 (특징 벡터의 클래스 분리 확인)
- sklearn.manifold.TSNE 사용 (perplexity=30, n_iter=1000)
- 통합 특징 벡터를 2D로 축소
- 6클래스 색상/마커 구분 산점도
- figsize=(12, 10)
- 인사이트: "에지+윤곽선 특징만으로 클래스 간 분리가 가능한 정도" 분석
- outputs/figures/03_tsne_visualization.png 저장

## 셀 23: 핵심 발견사항 및 소주제 ④ 연결 (마크다운)
- 마크다운 셀로 소주제 ③의 핵심 분석 결과 정리:
  1. 최적 에지 검출: auto_canny가 클래스별 밝기 차이에 자동 대응하여 가장 안정적
  2. 전처리 효과: bilateral + sharpen 후 에지 연속성이 X% 향상, 노이즈 에지가 Y% 감소
  3. 윤곽선 특징의 분리력: mean_circularity와 mean_aspect_ratio가 클래스 분리에 효과적
  4. 에지 방향의 결함 시그니처: Scratches의 방향 엔트로피가 타 클래스 대비 유의하게 낮음
  5. 에지 밀도 맵의 공간적 패턴: 결함 유형별 고유한 공간 분포 확인
  6. 통합 특징 벡터: 윤곽선(~24차원) + 에지(~46차원) = ~70차원의 특징 벡터 생성
  7. t-SNE 결과: 6클래스의 부분적 분리 확인, 완전 분리에는 HOG/LBP 추가 필요
- "소주제 ④에서는 이 특징 벡터에 HOG, LBP, 픽셀 통계를 추가하고,
  SVM/RF/KNN으로 분류 성능을 정량 비교할 예정.
  소주제 ③에서 저장한 contour_edge_features.npy를 직접 로드하여 사용."

[시각화 규칙]
- 모든 figure에 plt.tight_layout() 적용
- 저장 시 dpi=150, bbox_inches='tight'
- 한글 폰트: plt.rcParams['font.family'] = 'AppleGothic'
- plt.rcParams['axes.unicode_minus'] = False
- 이미지 표시 시 cmap='gray' 통일 (에지 이미지 포함)
- 히트맵: seaborn의 cmap='YlOrRd' 또는 'viridis'
- 산점도: 6클래스 색상은 seaborn의 color_palette("Set2", 6) 사용
- 각 시각화 셀 끝에 print("✅ 저장 완료: {파일 경로}") 출력
- 대형 격자에서 제목 겹침 방지: fontsize 축소 + plt.subplots_adjust(hspace=0.4)
```

---

## 🚀 Phase 6: 모듈 통합 업데이트

### 6.1 Claude Code 지시사항

```
preprocessing/__init__.py와 features/__init__.py를 업데이트해줘.

[파일 1] preprocessing/__init__.py

- 기존 모듈 (alignment, roi, normalization, filters, sharpening, morphology) 유지
- 소주제 ③ 모듈 추가: thresholding, edge_detection
- __all__ 업데이트
- 버전: __version__ = "0.3.0"

[파일 2] features/__init__.py (신규 생성)

- contour_features, edge_features 모듈 export
- __all__ 정의
- 버전: __version__ = "0.1.0"

[예시 사용법 — docstring에 포함]
```python
# 소주제 ③ 에지 검출 및 특징 추출
from preprocessing.thresholding import otsu_threshold, adaptive_threshold_gaussian
from preprocessing.edge_detection import auto_canny, sobel_edge, edge_direction_map
from features.contour_features import extract_contour_feature_vector
from features.edge_features import extract_edge_feature_vector

# 통합 특징 벡터 추출
contour_feat = extract_contour_feature_vector(preprocessed_img)
edge_feat = extract_edge_feature_vector(preprocessed_img)
combined_feat = np.concatenate([contour_feat, edge_feat])
```
```

---

## 📊 산출물 체크리스트

### 코드 파일

| 파일 | 상태 | 함수 수 | 설명 |
|------|------|---------|------|
| `preprocessing/thresholding.py` | ⬜ | 8개 | 임계값 처리 |
| `preprocessing/edge_detection.py` | ⬜ | 11개 | 에지 검출 |
| `features/contour_features.py` | ⬜ | 6개 | 윤곽선 기반 특징 추출 |
| `features/edge_features.py` | ⬜ | 7개 | 에지 기반 특징 추출 |
| `features/__init__.py` | ⬜ | — | 특징 추출 모듈 통합 |
| `preprocessing/__init__.py` | ⬜ | — | 업데이트 (v0.3.0) |
| `notebooks/03_edge_contour_analysis.ipynb` | ⬜ | 23셀 | 분석 노트북 |

### 시각화 산출물

| 파일명 | 상태 | 내용 |
|--------|------|------|
| `03_threshold_comparison.png` | ⬜ | 6클래스 × 7임계값 방법 비교 |
| `03_otsu_distribution.png` | ⬜ | 클래스별 Otsu 임계값 박스플롯 |
| `03_adaptive_blocksize.png` | ⬜ | Adaptive block_size 영향 |
| `03_edge_comparison_all.png` | ⬜ | 6클래스 × 11에지 방법 비교 |
| `03_preprocessing_effect_on_edge.png` | ⬜ | 전처리 전/후 에지 차이 |
| `03_edge_quality_before_after.png` | ⬜ | 에지 품질 정량 비교 |
| `03_canny_param_search.png` | ⬜ | Canny 임계값 파라미터 탐색 |
| `03_edge_direction_analysis.png` | ⬜ | 에지 방향 분석 (극좌표) |
| `03_multiscale_edge.png` | ⬜ | 멀티스케일 에지 |
| `03_contour_visualization.png` | ⬜ | 6클래스 윤곽선 시각화 |
| `03_contour_features_boxplot.png` | ⬜ | 윤곽선 특징 박스플롯 |
| `03_contour_scatter.png` | ⬜ | 윤곽선 특징 2D 산점도 |
| `03_contour_hierarchy.png` | ⬜ | 윤곽선 계층 구조 분석 |
| `03_edge_density_maps.png` | ⬜ | 6클래스 에지 밀도 히트맵 |
| `03_edge_features_boxplot.png` | ⬜ | 에지 특징 박스플롯 |
| `03_entropy_vs_density.png` | ⬜ | 방향 엔트로피 vs 밀도 산점도 |
| `03_feature_correlation.png` | ⬜ | 특징 상관관계 히트맵 |
| `03_tsne_visualization.png` | ⬜ | t-SNE 클래스 분리 시각화 |

### 데이터 파일

| 파일명 | 상태 | 설명 |
|--------|------|------|
| `outputs/contour_edge_features.npy` | ⬜ | 통합 특징 행렬 (1800, ~70) |
| `outputs/labels.npy` | ⬜ | 라벨 배열 (1800,) |

---

## ⚠️ Claude Code 실행 시 주의사항

### 연산 시간 관련

1. **전체 데이터셋 특징 추출**: 1,800장 × (윤곽선 + 에지) 특징 추출은 M4 Pro에서 약 3~10분 소요 예상. 노트북 셀 20에서 진행률 표시 필수.

2. **t-SNE**: sklearn TSNE의 기본 설정(n_iter=1000)으로 1,800개 샘플은 1~2분 소요. 시간이 길면 n_iter=500으로 줄여도 시각화 품질에 큰 차이 없음.

3. **에지 방향 히스토그램**: scipy.stats.circmean/circstd가 없으면 직접 구현. `np.arctan2`의 결과는 라디안이므로 degree 변환 시 `np.degrees()` 사용.

### 코딩 관련

1. **윤곽선 검출 0개 문제**: 일부 이미지에서 적절한 임계값을 찾지 못하면 윤곽선이 0개일 수 있음. 모든 윤곽선 관련 함수에서 `if len(contours) == 0:` 처리 필수.

2. **Hu Moments log 변환**: `cv2.HuMoments()`는 매우 작은 값(1e-20 수준)을 반환할 수 있음. `np.log10(np.abs(hu) + 1e-10)` 형태로 안전하게 변환.

3. **cv2.fitEllipse() 최소 점 수**: 5개 이상의 점이 필요. 작은 윤곽선에서는 에러 발생. `if len(contour) >= 5:` 조건 확인.

4. **에지 밀도 맵 grid 분할**: 이미지 크기(200)가 grid_size로 정확히 나누어지지 않을 수 있음. `np.array_split()` 사용 또는 마지막 셀 크기 조정.

5. **극좌표 차트**: matplotlib의 `projection='polar'`에서 `theta`는 라디안. 에지 방향(degree)을 `np.radians()`로 변환 필요.

### 소주제 간 연결

1. **소주제 ①에서 받는 것**: `clahe_equalization()` → 밝기 정규화된 이미지를 에지 검출의 입력으로 사용.

2. **소주제 ②에서 받는 것**: `bilateral_filter()` + `adaptive_sharpen()` + `opening()` → 노이즈 제거 + 결함 강조된 이미지를 에지 검출의 입력으로 사용. `filter_utils.py`의 `compute_edge_density()` 재활용.

3. **소주제 ④에 넘기는 것**:
   - `outputs/contour_edge_features.npy` → 소주제 ④에서 HOG/LBP와 concatenate하여 최종 특징 벡터 구성
   - `outputs/labels.npy` → 라벨 배열
   - `extract_contour_feature_vector()`, `extract_edge_feature_vector()` → 소주제 ④에서 개별 이미지 추론 시 호출
   - `get_feature_names()` 계열 함수 → 소주제 ④에서 특징 중요도 분석 시 활용

4. **Streamlit 대시보드 연결**:
   - `compare_edge_methods()` → Page 2(전처리 실험실) 에지 검출 탭
   - `visualize_contours()` → Page 3(결함 분류기) 분류 결과 위에 윤곽선 오버레이
   - `compute_edge_density_map()` → Page 4(성능 분석) 에지 밀도 히트맵 시각화

---

## 📝 Claude Code 실행 순서 요약

```
1단계: preprocessing/thresholding.py 구현 → 테스트
2단계: preprocessing/edge_detection.py 구현 → 테스트
3단계: features/contour_features.py 구현 → 테스트
4단계: features/edge_features.py 구현 → 테스트
5단계: preprocessing/__init__.py 업데이트 + features/__init__.py 생성
6단계: notebooks/03_edge_contour_analysis.ipynb 전체 실행 → 시각화 + 특징 저장
7단계: 산출물 체크리스트 확인
```

각 단계별로 Claude Code에 해당 Phase의 지시사항을 복사하여 실행하면 됩니다.

---

## 🔗 소주제 ③의 핵심 산출물이 이후에 쓰이는 곳 요약

| 산출물 | 소주제 ④ | Streamlit |
|--------|----------|-----------|
| `contour_edge_features.npy` | HOG/LBP와 concatenate → 최종 특징 행렬 | — |
| `labels.npy` | train/test split용 라벨 | — |
| `extract_contour_feature_vector()` | 개별 이미지 추론 파이프라인 | Page 3 분류기 내부 |
| `extract_edge_feature_vector()` | 개별 이미지 추론 파이프라인 | Page 3 분류기 내부 |
| `auto_canny()` | 전처리 파이프라인 구성 요소 | Page 2 에지 탭 |
| `compare_edge_methods()` | — | Page 2 에지 비교 시각화 |
| `visualize_contours()` | — | Page 3 결과 오버레이 |
| `compute_edge_density_map()` | 특징 벡터 구성 요소 | Page 4 밀도 맵 |
| t-SNE 결과 | 특징 품질 검증 참고 | Page 4 분석 차트 |
