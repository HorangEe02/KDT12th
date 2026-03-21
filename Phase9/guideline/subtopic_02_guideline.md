# 🔬 소주제 ② — 결함 특징 극대화를 위한 필터링 및 샤프닝

## Claude Code 실행 가이드라인

> **프로젝트**: OpenCV & ML 하이브리드 부품 결함 자동 검수 시스템  
> **연계 차시**: 3차시 (이미지 필터링과 변환)  
> **담당 역할**: A. 데이터 & 전처리 담당  
> **작성일**: 2026.03.19

---

## 📋 실행 전 체크리스트

### 사전 준비 사항

1. **소주제 ① 완료 확인**
   - `utils/data_loader.py` — NEUDataLoader 클래스 구현 완료
   - `preprocessing/alignment.py` — 이미지 정렬 모듈 구현 완료
   - `preprocessing/roi.py` — ROI 추출 모듈 구현 완료
   - `preprocessing/normalization.py` — 밝기/대비 정규화 모듈 구현 완료
   - `notebooks/01_alignment_roi.ipynb` — EDA 및 Phase 1 분석 완료
   - ⚠️ 소주제 ①이 미완료 시, 최소한 `data_loader.py`와 `normalization.py`는 먼저 구현할 것

2. **Python 환경 추가 패키지 확인**
   ```bash
   # 소주제 ①에서 이미 설치된 패키지 외 추가 필요 없음
   pip install opencv-python numpy matplotlib seaborn scikit-learn scikit-image jupyter
   ```

3. **프로젝트 디렉토리 구조 (소주제 ② 추가분)**
   ```
   project_root/
   ├── data/
   │   └── NEU-DET/                    # 데이터셋 (소주제 ①에서 준비 완료)
   ├── preprocessing/
   │   ├── __init__.py                 # (소주제 ①에서 생성)
   │   ├── alignment.py                # (소주제 ①에서 생성)
   │   ├── roi.py                      # (소주제 ①에서 생성)
   │   ├── normalization.py            # (소주제 ①에서 생성)
   │   ├── filters.py                  # [이 가이드에서 생성] 블러/노이즈 제거 모듈
   │   ├── sharpening.py               # [이 가이드에서 생성] 샤프닝/결함 강조 모듈
   │   └── morphology.py               # [이 가이드에서 생성] 모폴로지 연산 모듈
   ├── utils/
   │   ├── __init__.py
   │   ├── data_loader.py              # (소주제 ①에서 생성)
   │   └── filter_utils.py             # [이 가이드에서 생성] 필터 비교/평가 유틸리티
   ├── notebooks/
   │   ├── 01_alignment_roi.ipynb      # (소주제 ①에서 생성)
   │   └── 02_filtering_sharpening.ipynb  # [이 가이드에서 생성] 분석 노트북
   ├── outputs/
   │   └── figures/                    # 시각화 결과 저장
   └── README.md
   ```

---

## 🎯 소주제 ② 목표 및 범위

### 최종 목표

NEU 금속 표면 결함 이미지에 대해 **노이즈 제거(블러) → 결함 강조(샤프닝) → 미세 결함 처리(모폴로지)**의 3단계 필터링 파이프라인을 구축하고, 결함 유형별로 어떤 필터링 전략이 가장 효과적인지를 정량적·시각적으로 검증한다.

### 핵심 질문

이 소주제가 답해야 할 핵심 질문은 다음과 같다:

1. **노이즈 제거와 결함 보존의 트레이드오프**: 블러를 강하게 걸면 노이즈는 줄지만 미세한 결함 특징도 함께 사라진다. 결함 유형별 최적의 블러 강도는?
2. **샤프닝의 실질적 효과**: 샤프닝 처리가 ML 분류 성능에 실제로 기여하는가, 아니면 노이즈만 증폭하는가?
3. **결함 유형별 최적 필터 조합**: 6종 결함 각각에 대해 가장 효과적인 전처리 조합은 무엇인가?

### 세부 목표

| # | 목표 | 산출물 |
|---|------|--------|
| 1 | 블러/노이즈 제거 필터 모듈 구현 | `filters.py` |
| 2 | 샤프닝/결함 강조 모듈 구현 | `sharpening.py` |
| 3 | 모폴로지 연산 모듈 구현 | `morphology.py` |
| 4 | 필터 비교/평가 유틸리티 구현 | `filter_utils.py` |
| 5 | 통합 분석 및 결함 유형별 최적 조합 탐색 | `02_filtering_sharpening.ipynb` |

---

## 🚀 Phase 1: 블러 및 노이즈 제거 필터 모듈

### 1.1 배경 설명

금속 표면 이미지에는 촬영 환경에서 발생한 센서 노이즈, 광택 반사에 의한 고주파 성분, 표면 미세 텍스처 등 다양한 노이즈가 포함되어 있다. 블러 처리는 이러한 노이즈를 제거하되, 결함의 핵심 특징(경계선, 형태)은 최대한 보존해야 한다. 이 트레이드오프를 정량적으로 분석하는 것이 핵심이다.

### 1.2 Claude Code 지시사항

```
다음 요구사항에 따라 preprocessing/filters.py를 구현해줘.

[파일 위치] preprocessing/filters.py

[기능 요구사항]

1. gaussian_blur(image: np.ndarray, kernel_size: int = 5, sigma: float = 0) -> np.ndarray
   - 가우시안 블러 (가장 기본적인 노이즈 제거)
   - cv2.GaussianBlur() 사용
   - kernel_size: 홀수만 허용 (짝수 입력 시 +1 보정)
   - sigma=0이면 커널 크기에서 자동 계산
   - 용도: 전반적인 고주파 노이즈 제거

2. median_blur(image: np.ndarray, kernel_size: int = 5) -> np.ndarray
   - 미디안 블러 (소금-후추 노이즈에 효과적)
   - cv2.medianBlur() 사용
   - kernel_size: 홀수만 허용
   - 용도: 점 형태의 임펄스 노이즈 제거. 에지 보존력이 가우시안보다 우수

3. bilateral_filter(image: np.ndarray, d: int = 9, sigma_color: float = 75, sigma_space: float = 75) -> np.ndarray
   - 양방향 필터 (에지를 보존하면서 노이즈 제거)
   - cv2.bilateralFilter() 사용
   - d: 필터링에 사용할 이웃 픽셀 직경
   - sigma_color: 색상 공간에서의 시그마 (값이 클수록 더 넓은 색상 범위 혼합)
   - sigma_space: 좌표 공간에서의 시그마 (값이 클수록 더 먼 픽셀에도 영향)
   - 용도: 금속 광택 반사 제거 + 결함 경계 보존. 이 프로젝트에서 가장 핵심적인 필터

4. average_blur(image: np.ndarray, kernel_size: int = 5) -> np.ndarray
   - 평균 블러 (단순 박스 필터)
   - cv2.blur() 사용
   - 가우시안보다 단순하지만, 비교 실험의 베이스라인으로 활용

5. non_local_means_denoise(image: np.ndarray, h: float = 10, template_window_size: int = 7, search_window_size: int = 21) -> np.ndarray
   - 비국소 평균 노이즈 제거 (Non-Local Means Denoising)
   - cv2.fastNlMeansDenoising() 사용 (그레이스케일 전용)
   - h: 필터 강도 (값이 클수록 더 강하게 노이즈 제거, 디테일 손실 증가)
   - template_window_size: 패치 크기 (홀수)
   - search_window_size: 검색 영역 크기 (홀수)
   - 용도: 가장 정교한 노이즈 제거. 연산 시간이 가장 김

6. apply_custom_kernel(image: np.ndarray, kernel: np.ndarray) -> np.ndarray
   - 사용자 정의 커널을 적용하는 범용 함수
   - cv2.filter2D() 사용
   - kernel: 2D numpy 배열 (예: 3×3, 5×5)
   - 용도: 실험적 커널 테스트용

7. progressive_blur(image: np.ndarray, method: str = "gaussian", kernel_sizes: list[int] = [3, 5, 7, 9, 11]) -> dict[int, np.ndarray]
   - 점진적 블러 강도 비교용 함수
   - 지정된 method로 여러 커널 사이즈를 순차 적용
   - method: "gaussian", "median", "average" 중 택 1
   - 반환: {kernel_size: blurred_image} 딕셔너리
   - 용도: 블러 강도에 따른 결함 보존도 변화를 시각적으로 비교

8. compare_blur_methods(image: np.ndarray, kernel_size: int = 5) -> dict[str, np.ndarray]
   - 동일 커널 사이즈에서 모든 블러 방법 결과를 한번에 비교
   - 반환: {"original": img, "gaussian": img, "median": img, "bilateral": img, "average": img, "nlm": img}

[코딩 규칙]
- Type hints 사용
- Docstring 작성 (Google style)
- 모든 함수는 입력 이미지를 변경하지 않음 (copy 후 처리)
- kernel_size 홀수 검증 로직: 짝수 입력 시 +1 보정 + 경고 메시지 출력
- 입력 이미지 유효성 검사: None 체크, ndim 체크 (그레이스케일 2D만 허용, 3채널 시 자동 변환+경고)
- import: cv2, numpy, typing, warnings

[테스트]
- if __name__ == "__main__": 블록에서 테스트
- NEU 데이터셋에서 Scratches, Crazing 클래스 이미지 각 1장 로드
- compare_blur_methods()로 전체 방법 비교 결과 출력
- progressive_blur()로 가우시안 블러 커널 3~11 결과 생성
- 각 결과의 mean, std 변화량 출력
```

---

## 🚀 Phase 2: 샤프닝 및 결함 강조 모듈

### 2.1 배경 설명

샤프닝은 블러와 반대로 이미지의 고주파 성분(경계, 디테일)을 강조하는 처리다. 금속 표면 결함에서 샤프닝의 역할은 **미세한 스크래치나 균열의 경계를 더 뚜렷하게 만들어** ML 모델이 이 특징을 더 잘 캡처할 수 있게 하는 것이다.

그러나 과도한 샤프닝은 노이즈까지 증폭시키므로, **블러(노이즈 제거) → 샤프닝(결함 강조)**의 순서가 중요하다. 이 모듈에서는 다양한 샤프닝 기법을 구현하고 각각의 효과를 분석한다.

### 2.2 Claude Code 지시사항

```
다음 요구사항에 따라 preprocessing/sharpening.py를 구현해줘.

[파일 위치] preprocessing/sharpening.py

[기능 요구사항]

1. unsharp_mask(image: np.ndarray, kernel_size: int = 5, sigma: float = 1.0, amount: float = 1.5, threshold: int = 0) -> np.ndarray
   - 언샤프 마스크 (가장 범용적인 샤프닝 기법)
   - 구현 방법:
     a. 가우시안 블러 적용하여 blur_img 생성
     b. sharpened = float(image) + amount * (float(image) - float(blur_img))
     c. threshold 적용: 원본과의 차이가 threshold 미만인 픽셀은 원본 유지
     d. np.clip()으로 0~255 범위 제한 후 uint8 변환
   - amount: 샤프닝 강도 (1.0=보통, 2.0=강함)
   - threshold: 노이즈 영역 보호 (0이면 모든 픽셀에 적용)
   - 용도: 결함 경계 강조의 기본 도구

2. laplacian_sharpen(image: np.ndarray, kernel_size: int = 3, scale: float = 1.0) -> np.ndarray
   - 라플라시안 기반 샤프닝
   - 구현 방법:
     a. cv2.Laplacian()으로 2차 미분 (에지) 검출
     b. sharpened = image - scale * laplacian
     c. np.clip() + uint8 변환
   - kernel_size: 라플라시안 커널 크기 (1, 3, 5, 7)
   - scale: 라플라시안 가중치 (값이 클수록 강한 샤프닝)
   - 용도: 방향성 없이 모든 에지를 균등하게 강조

3. highpass_sharpen(image: np.ndarray, kernel_size: int = 5, alpha: float = 1.5) -> np.ndarray
   - 고주파 통과 필터 기반 샤프닝
   - 구현 방법:
     a. 가우시안 블러로 저주파 성분(low_pass) 추출
     b. high_pass = float(image) - float(low_pass)
     c. sharpened = float(image) + alpha * high_pass
     d. np.clip() + uint8 변환
   - alpha: 고주파 성분 가중치
   - 용도: 블러와 샤프닝의 관계를 명시적으로 보여주는 교육적 구현

4. custom_sharpen_kernel(image: np.ndarray, strength: str = "medium") -> np.ndarray
   - 사전 정의된 샤프닝 커널 적용
   - strength 옵션:
     - "light": [[0, -1, 0], [-1, 5, -1], [0, -1, 0]]
     - "medium": [[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]]
     - "strong": [[-2, -2, -2], [-2, 17, -2], [-2, -2, -2]]
     (각각 중앙값이 다르며, 주변값의 합이 중앙값을 빼면 1이 되도록 정규화)
   - cv2.filter2D() 사용
   - 용도: 커널의 직관적 이해를 위한 시연용

5. emboss_filter(image: np.ndarray, direction: str = "top_left") -> np.ndarray
   - 엠보싱 필터 (입체감 부여로 결함의 깊이 시각화)
   - direction 옵션별 커널:
     - "top_left": [[-2, -1, 0], [-1, 1, 1], [0, 1, 2]]
     - "top_right": [[0, -1, -2], [1, 1, -1], [2, 1, 0]]
     - "bottom": [[0, 1, 2], [-1, 1, 1], [-2, -1, 0]]
   - 결과에 128 오프셋 추가 (중간 톤을 기준으로 음양 표현)
   - 용도: 결함의 물리적 깊이감 시각화 (특히 Pitted Surface에 효과적)

6. detail_enhance(image: np.ndarray, sigma_s: float = 10, sigma_r: float = 0.15) -> np.ndarray
   - 디테일 강조 (OpenCV의 detailEnhance 활용)
   - ⚠️ 그레이스케일 이미지는 3채널로 변환 후 처리 → 다시 그레이스케일 변환
   - cv2.detailEnhance() 사용
   - sigma_s: 공간적 시그마 (값이 클수록 넓은 영역 고려)
   - sigma_r: 범위 시그마 (값이 클수록 색상 차이 허용)
   - 용도: 금속 표면의 미세 텍스처 강조

7. adaptive_sharpen(image: np.ndarray, blur_ksize: int = 5, sharp_amount: float = 1.5, noise_threshold: int = 10) -> np.ndarray
   - 적응형 샤프닝 (노이즈 영역은 보호, 결함 영역만 강조)
   - 구현 방법:
     a. 가우시안 블러로 noise_map 생성
     b. diff = abs(float(image) - float(noise_map))
     c. mask = (diff > noise_threshold).astype(float)  # 결함 가능 영역
     d. 가우시안 블러로 mask를 부드럽게 처리 (hard edge 방지)
     e. unsharp_mask 결과와 원본을 mask 비율로 블렌딩
     f. result = mask * sharpened + (1 - mask) * image
   - 용도: 이 프로젝트의 핵심 기법. 노이즈 증폭 없이 결함만 선택적으로 강조

8. compare_sharpen_methods(image: np.ndarray) -> dict[str, np.ndarray]
   - 모든 샤프닝 방법의 결과를 한번에 비교
   - 반환: {"original": img, "unsharp_light": img, "unsharp_strong": img, "laplacian": img, "highpass": img, "kernel_light": img, "kernel_medium": img, "kernel_strong": img, "emboss": img, "adaptive": img}

9. blur_then_sharpen(image: np.ndarray, blur_method: str = "bilateral", blur_params: dict = None, sharpen_method: str = "unsharp", sharpen_params: dict = None) -> dict[str, np.ndarray]
   - 블러 → 샤프닝 순차 적용 파이프라인
   - blur_method: "gaussian", "median", "bilateral", "nlm" 중 택 1
   - sharpen_method: "unsharp", "laplacian", "highpass", "adaptive" 중 택 1
   - 반환: {"original": img, "blurred": img, "sharpened": img}
   - 용도: 소주제 ②의 핵심 파이프라인. "노이즈 먼저 제거 → 결함 강조"의 순서적 효과를 시연

[코딩 규칙]
- Type hints 사용
- Docstring 작성 (Google style)
- 모든 함수는 입력 이미지를 변경하지 않음 (copy 후 처리)
- float 연산 시 overflow 방지: np.float64로 변환 후 처리, 최종 np.clip(0, 255).astype(np.uint8)
- 입력 이미지 유효성 검사: None 체크, ndim 체크
- import: cv2, numpy, typing, warnings

[테스트]
- if __name__ == "__main__": 블록에서 테스트
- NEU 데이터셋에서 각 클래스 1장씩 로드
- compare_sharpen_methods()로 Scratches 이미지에 대한 전체 비교
- blur_then_sharpen()로 bilateral → unsharp 파이프라인 테스트
- 각 결과의 에지 밀도(Canny 에지 픽셀 비율) 변화 출력
```

---

## 🚀 Phase 3: 모폴로지 연산 모듈

### 3.1 배경 설명

모폴로지(형태학적) 연산은 이미지의 형태를 기반으로 노이즈를 제거하거나 결함을 강조하는 비선형 필터링 기법이다. 커널(구조 요소)의 모양과 크기에 따라 미세 결함을 확대하거나 작은 노이즈를 제거할 수 있어, 블러/샤프닝과 보완적으로 사용된다.

특히 금속 표면에서는 **Opening(침식→팽창)으로 작은 노이즈 점을 제거**하고, **Closing(팽창→침식)으로 미세 균열의 끊어진 부분을 연결**하며, **Morphological Gradient로 결함 경계를 추출**하는 것이 핵심이다.

### 3.2 Claude Code 지시사항

```
다음 요구사항에 따라 preprocessing/morphology.py를 구현해줘.

[파일 위치] preprocessing/morphology.py

[기능 요구사항]

1. get_kernel(shape: str = "rect", size: int = 3) -> np.ndarray
   - 모폴로지 연산용 구조 요소(커널) 생성
   - shape 옵션:
     - "rect": cv2.MORPH_RECT (직사각형)
     - "ellipse": cv2.MORPH_ELLIPSE (타원형)
     - "cross": cv2.MORPH_CROSS (십자형)
   - cv2.getStructuringElement() 사용
   - size: 홀수만 허용 (짝수 시 +1 보정)
   - 반환: (size, size) shape의 커널

2. erode(image: np.ndarray, kernel_shape: str = "rect", kernel_size: int = 3, iterations: int = 1) -> np.ndarray
   - 침식 연산 (밝은 영역 축소, 어두운 결함 강조)
   - cv2.erode() 사용
   - iterations: 반복 횟수 (값이 클수록 강한 침식)
   - 용도: Pitted Surface의 어두운 구멍 강조

3. dilate(image: np.ndarray, kernel_shape: str = "rect", kernel_size: int = 3, iterations: int = 1) -> np.ndarray
   - 팽창 연산 (밝은 영역 확장, 밝은 결함 강조)
   - cv2.dilate() 사용
   - 용도: Scratches의 밝은 선형 결함 강조

4. opening(image: np.ndarray, kernel_shape: str = "rect", kernel_size: int = 3) -> np.ndarray
   - 열기 연산 (침식 → 팽창)
   - cv2.morphologyEx(cv2.MORPH_OPEN) 사용
   - 용도: 작은 밝은 노이즈 점 제거 (전체 형태 보존)

5. closing(image: np.ndarray, kernel_shape: str = "rect", kernel_size: int = 3) -> np.ndarray
   - 닫기 연산 (팽창 → 침식)
   - cv2.morphologyEx(cv2.MORPH_CLOSE) 사용
   - 용도: 결함 내부의 작은 구멍 채우기, 끊어진 균열 연결

6. morphological_gradient(image: np.ndarray, kernel_shape: str = "rect", kernel_size: int = 3) -> np.ndarray
   - 모폴로지 그래디언트 (팽창 - 침식 = 경계 추출)
   - cv2.morphologyEx(cv2.MORPH_GRADIENT) 사용
   - 용도: 결함 경계를 추출. Canny 에지 검출의 대안으로 활용

7. tophat(image: np.ndarray, kernel_shape: str = "rect", kernel_size: int = 9) -> np.ndarray
   - 탑햇 변환 (원본 - Opening = 밝은 미세 결함 추출)
   - cv2.morphologyEx(cv2.MORPH_TOPHAT) 사용
   - 커널 사이즈를 결함보다 크게 설정해야 효과적 (기본 9)
   - 용도: 배경보다 밝은 미세 스크래치, 개재물 추출

8. blackhat(image: np.ndarray, kernel_shape: str = "rect", kernel_size: int = 9) -> np.ndarray
   - 블랙햇 변환 (Closing - 원본 = 어두운 미세 결함 추출)
   - cv2.morphologyEx(cv2.MORPH_BLACKHAT) 사용
   - 용도: 배경보다 어두운 미세 균열, 구멍 추출

9. morphology_pipeline(image: np.ndarray, operations: list[dict]) -> dict[str, np.ndarray]
   - 모폴로지 연산을 순차적으로 적용하는 파이프라인
   - operations: [{"op": "opening", "kernel_shape": "rect", "kernel_size": 3}, ...]
   - 각 단계의 중간 결과를 모두 저장하여 반환
   - 반환: {"step_0_original": img, "step_1_opening": img, "step_2_closing": img, ...}
   - 용도: 모폴로지 연산의 순서와 조합에 따른 효과 차이를 실험

10. defect_enhancement_morph(image: np.ndarray, defect_type: str = "general") -> np.ndarray
    - 결함 유형별 최적 모폴로지 전처리 적용
    - defect_type 옵션:
      - "crazing": closing(ellipse, 3) → tophat(rect, 7) — 균열 연결 후 미세 패턴 강조
      - "scratches": dilate(rect, 3, iter=1) → morphological_gradient(rect, 3) — 선형 결함 확장 후 경계 추출
      - "pitted": erode(ellipse, 3, iter=1) → blackhat(ellipse, 9) — 구멍 강조 후 어두운 결함 추출
      - "inclusion": tophat(rect, 9) — 밝은 이물질 추출
      - "patches": closing(rect, 5) → opening(rect, 3) — 패치 경계 정리
      - "rolled_in_scale": blackhat(rect, 11) → dilate(rect, 3) — 어두운 스케일 추출 후 확장
      - "general": opening(rect, 3) → closing(rect, 3) — 범용 노이즈 제거
    - 용도: 소주제 ④(ML 분류)에서 결함 유형이 알려져 있지 않으므로 "general"이 기본이지만,
      분석 단계에서 유형별 최적 전략을 탐색하는 데 활용

11. compare_morphology_methods(image: np.ndarray, kernel_size: int = 3) -> dict[str, np.ndarray]
    - 모든 모폴로지 연산 결과를 한번에 비교
    - 반환: {"original": img, "erode": img, "dilate": img, "opening": img, "closing": img, "gradient": img, "tophat": img, "blackhat": img}

[코딩 규칙]
- Type hints 사용
- Docstring 작성 (Google style)
- 모든 함수는 입력 이미지를 변경하지 않음
- 커널 사이즈 홀수 검증 + 자동 보정
- 입력 이미지 유효성 검사
- import: cv2, numpy, typing, warnings

[테스트]
- if __name__ == "__main__": 블록에서 테스트
- NEU 데이터셋에서 각 클래스 1장씩 로드
- compare_morphology_methods()로 전체 비교
- defect_enhancement_morph()로 각 클래스별 맞춤 전처리 적용
- tophat과 blackhat 결과를 원본 위에 오버레이하여 결함 위치 확인
```

---

## 🚀 Phase 4: 필터 비교 및 평가 유틸리티

### 4.1 배경 설명

다양한 필터링 방법의 효과를 정량적으로 비교하려면 공통된 평가 지표가 필요하다. 이 모듈은 필터링 전/후의 이미지 품질 변화를 측정하고, 결함 보존도를 정량화하는 유틸리티를 제공한다.

### 4.2 Claude Code 지시사항

```
다음 요구사항에 따라 utils/filter_utils.py를 구현해줘.

[파일 위치] utils/filter_utils.py

[기능 요구사항]

1. compute_edge_density(image: np.ndarray, low_threshold: int = 50, high_threshold: int = 150) -> float
   - Canny 에지 검출 후 에지 픽셀 비율 계산
   - 반환: 0.0 ~ 1.0 (에지 픽셀 수 / 전체 픽셀 수)
   - 용도: 필터링 후 결함 경계가 얼마나 보존되었는지 측정

2. compute_psnr(original: np.ndarray, processed: np.ndarray) -> float
   - Peak Signal-to-Noise Ratio (PSNR) 계산
   - cv2.PSNR() 또는 수동 계산: 20 * log10(255 / sqrt(MSE))
   - 높을수록 원본과 유사 (노이즈 제거가 적음)
   - 반환: float (dB 단위). 동일 이미지면 float('inf')

3. compute_ssim(original: np.ndarray, processed: np.ndarray) -> float
   - Structural Similarity Index (SSIM) 계산
   - skimage.metrics.structural_similarity 사용
   - 1.0에 가까울수록 구조적으로 유사 (결함 형태 보존)
   - 반환: -1.0 ~ 1.0

4. compute_variance_of_laplacian(image: np.ndarray) -> float
   - 라플라시안 분산 (이미지 선명도 지표)
   - cv2.Laplacian() 후 분산 계산
   - 높을수록 선명한 이미지 (에지가 많음)
   - 블러 강도가 증가하면 이 값이 감소 → 결함 특징 손실의 간접 지표

5. compute_noise_level(image: np.ndarray) -> float
   - 이미지의 노이즈 수준 추정
   - 구현: 가우시안 블러(sigma=5)와의 차이 이미지의 표준편차
   - 높을수록 노이즈가 많음
   - 필터링 전/후 비교하여 노이즈 제거 효과 정량화

6. evaluate_filter(original: np.ndarray, filtered: np.ndarray) -> dict[str, float]
   - 단일 필터의 종합 평가
   - 반환: {
       "psnr": float,
       "ssim": float,
       "edge_density_original": float,
       "edge_density_filtered": float,
       "edge_density_change": float,  # (filtered - original) / original * 100
       "laplacian_var_original": float,
       "laplacian_var_filtered": float,
       "sharpness_change": float,  # (filtered - original) / original * 100
       "noise_original": float,
       "noise_filtered": float,
       "noise_reduction": float  # (original - filtered) / original * 100
     }

7. batch_evaluate_filters(image: np.ndarray, filtered_images: dict[str, np.ndarray]) -> pd.DataFrame
   - 여러 필터를 한번에 비교 평가
   - filtered_images: {"method_name": filtered_image, ...}
   - 각 방법에 대해 evaluate_filter() 호출
   - 결과를 pandas DataFrame으로 반환 (행: 필터명, 열: 평가 지표)
   - DataFrame을 SSIM 기준 내림차순 정렬

8. find_optimal_filter(image: np.ndarray, filtered_images: dict[str, np.ndarray], priority: str = "edge_preservation") -> str
   - 최적 필터 자동 선택
   - priority 옵션:
     - "edge_preservation": SSIM이 높으면서 edge_density_change가 가장 적은 필터
     - "noise_reduction": noise_reduction이 가장 큰 필터
     - "balanced": (SSIM * 0.4 + edge_preservation_score * 0.3 + noise_reduction_score * 0.3)의 종합 점수
   - 반환: 최적 필터 이름 (문자열)

[코딩 규칙]
- Type hints 사용
- Docstring 작성 (Google style)
- import: cv2, numpy, pandas, typing, skimage.metrics (SSIM용)
- 동일 이미지 비교 시 division by zero 방지
- 모든 비율 계산에서 분모 0 방지

[테스트]
- if __name__ == "__main__": 블록에서 테스트
- NEU 데이터셋에서 Scratches 이미지 1장 로드
- 5가지 블러 방법 적용 후 batch_evaluate_filters() 실행
- DataFrame 출력
- find_optimal_filter()로 최적 필터 출력
```

---

## 🚀 Phase 5: 통합 분석 노트북

### 5.1 Claude Code 지시사항

```
다음 요구사항에 따라 notebooks/02_filtering_sharpening.ipynb를 구현해줘.

[파일 위치] notebooks/02_filtering_sharpening.ipynb

[셀 구성]

## ===== 환경 설정 =====

## 셀 1: 환경 설정 및 import
- 필요한 라이브러리 import (cv2, numpy, matplotlib, seaborn, pandas, os, sys)
- 프로젝트 루트를 sys.path에 추가
- 모듈 import:
  - utils.data_loader에서 NEUDataLoader
  - preprocessing.filters에서 함수들
  - preprocessing.sharpening에서 함수들
  - preprocessing.morphology에서 함수들
  - preprocessing.normalization에서 clahe_equalization (소주제 ①에서 구현)
  - utils.filter_utils에서 함수들
- matplotlib 한글 폰트 설정 (macOS: AppleGothic)
- %matplotlib inline
- plt.style.use('seaborn-v0_8-whitegrid')
- outputs/figures/ 디렉토리 생성 확인 (os.makedirs)

## 셀 2: 데이터 로드 및 클래스별 대표 이미지 선택
- NEUDataLoader로 전체 데이터 로드
- 각 클래스에서 결함이 잘 보이는 대표 이미지 1장씩 선택 (인덱스 고정)
- 대표 이미지 6장을 딕셔너리에 저장: {"Crazing": img, "Inclusion": img, ...}
- 간단한 1행 × 6열 시각화로 선택된 이미지 확인
- figsize=(20, 4)

## ===== Part 1: 블러/노이즈 제거 분석 =====

## 셀 3: 블러 방법 전체 비교 (6클래스 × 6방법)
- 각 클래스 대표 이미지에 compare_blur_methods() 적용
- 6행(클래스) × 6열(원본 + 5가지 블러) 시각화
- 각 이미지 하단에 edge_density 수치 표시 (소수점 4자리)
- 각 이미지 하단에 laplacian_var 수치 표시
- figsize=(24, 24)
- 제목: "블러 방법별 결과 비교 (6클래스)"
- outputs/figures/02_blur_comparison_all.png 저장

## 셀 4: 점진적 블러 강도 분석 (Gaussian)
- Scratches 대표 이미지에 progressive_blur() 적용 (kernel_sizes=[3,5,7,9,11,15,21])
- 상단 행: 커널 사이즈별 블러 결과 이미지
- 하단 행: 각 결과의 Canny 에지 맵
- 1행 × 7열 (이미지) + 1행 × 7열 (에지) = 2행 × 7열
- figsize=(24, 8)
- 추가: edge_density vs kernel_size 선 그래프 별도 셀로
- 제목: "가우시안 블러 강도에 따른 에지 보존도 변화 (Scratches)"
- outputs/figures/02_progressive_blur.png 저장

## 셀 5: 블러 강도 vs 에지 보존도 정량 분석
- 6클래스 각각에 대해 gaussian_blur를 kernel_size [3,5,7,9,11,15,21]로 적용
- 각 경우의 edge_density 계산
- 6개 선(클래스)이 있는 선 그래프 (x: kernel_size, y: edge_density)
- 범례에 클래스명(한글) 표시
- figsize=(12, 7)
- 인사이트: "어떤 클래스가 블러에 가장 민감한가?" 마크다운 셀 추가
- outputs/figures/02_blur_vs_edge_density.png 저장

## 셀 6: Bilateral Filter 파라미터 탐색
- Scratches 이미지에 bilateral_filter를 다양한 파라미터로 적용
- sigma_color: [25, 50, 75, 100, 150]
- sigma_space: [25, 50, 75, 100, 150]
- 5×5 격자 시각화 (행: sigma_color, 열: sigma_space)
- 각 이미지에 SSIM과 edge_density 표시
- figsize=(20, 20)
- 제목: "Bilateral Filter 파라미터 탐색 (Scratches)"
- outputs/figures/02_bilateral_param_search.png 저장

## 셀 7: 블러 방법 정량 평가 DataFrame
- 6클래스 각각에 대해 batch_evaluate_filters() 실행
- 클래스별로 별도 DataFrame 출력 (총 6개 테이블)
- 각 테이블에서 최적 필터를 find_optimal_filter(priority="balanced")로 선택
- 최종 요약: 클래스별 최적 블러 방법 테이블 (1개 DataFrame)
- display()로 각 DataFrame 출력

## ===== Part 2: 샤프닝/결함 강조 분석 =====

## 셀 8: 샤프닝 방법 전체 비교 (6클래스)
- 각 클래스 대표 이미지에 compare_sharpen_methods() 적용
- 6행(클래스) × 10열(원본 + 9가지 샤프닝) 시각화
- figsize=(32, 24)
- ⚠️ 이미지가 많으므로 각 이미지 크기는 작게. 제목 폰트 축소 (fontsize=8)
- 각 이미지 하단에 laplacian_var 수치 표시
- 제목: "샤프닝 방법별 결과 비교 (6클래스)"
- outputs/figures/02_sharpen_comparison_all.png 저장

## 셀 9: Unsharp Mask 파라미터 탐색
- Crazing 대표 이미지 (미세 균열은 샤프닝 효과가 잘 보임)
- amount: [0.5, 1.0, 1.5, 2.0, 3.0]
- sigma: [0.5, 1.0, 2.0, 3.0, 5.0]
- 5×5 격자 시각화 (행: amount, 열: sigma)
- 각 이미지에 laplacian_var 표시
- figsize=(20, 20)
- 제목: "Unsharp Mask 파라미터 탐색 (Crazing)"
- outputs/figures/02_unsharp_param_search.png 저장

## 셀 10: 적응형 샤프닝 vs 일반 샤프닝 비교
- 각 클래스 대표 이미지에 대해:
  - 일반 unsharp_mask (amount=1.5)
  - adaptive_sharpen (amount=1.5, noise_threshold=10)
  - 두 결과의 차이 이미지 (abs(unsharp - adaptive))
- 6행(클래스) × 4열(원본, 일반 샤프닝, 적응형 샤프닝, 차이) 시각화
- figsize=(16, 24)
- 인사이트: "적응형 샤프닝이 노이즈 영역에서 어떻게 다르게 동작하는가" 마크다운 셀
- outputs/figures/02_adaptive_vs_normal_sharpen.png 저장

## 셀 11: 엠보싱 필터 결함 깊이 시각화
- 각 클래스 대표 이미지에 3방향 엠보싱 적용
- 6행(클래스) × 4열(원본, top_left, top_right, bottom) 시각화
- 특히 Pitted Surface에서 구멍의 깊이감이 잘 나타나는지 주목
- figsize=(16, 24)
- outputs/figures/02_emboss_depth.png 저장

## ===== Part 3: 모폴로지 연산 분석 =====

## 셀 12: 모폴로지 연산 전체 비교 (6클래스)
- 각 클래스 대표 이미지에 compare_morphology_methods() 적용
- 6행(클래스) × 8열(원본 + 7가지 모폴로지) 시각화
- figsize=(28, 24)
- 제목: "모폴로지 연산 비교 (6클래스)"
- outputs/figures/02_morphology_comparison_all.png 저장

## 셀 13: TopHat/BlackHat 결함 추출 분석
- 각 클래스 대표 이미지에 tophat(kernel_size=9)과 blackhat(kernel_size=9) 적용
- 6행(클래스) × 4열(원본, TopHat, BlackHat, TopHat+BlackHat 합성)
- TopHat+BlackHat 합성: 두 결과를 더한 뒤 정규화 → 전체 결함 맵
- 각 이미지에 결함 영역 비율(%) 표시 (임계값 30 이상인 픽셀 비율)
- figsize=(16, 24)
- 인사이트: "TopHat은 밝은 결함, BlackHat은 어두운 결함에 특화" 마크다운 셀
- outputs/figures/02_tophat_blackhat_analysis.png 저장

## 셀 14: 결함 유형별 맞춤 모폴로지 전처리
- 각 클래스 대표 이미지에 defect_enhancement_morph(defect_type=해당 클래스) 적용
- 6행(클래스) × 3열(원본, General 전처리, 맞춤 전처리) 비교
- 각 이미지에 edge_density 표시
- figsize=(12, 24)
- 인사이트: "맞춤 전처리가 범용 전처리 대비 어떤 장점이 있는가" 마크다운 셀
- outputs/figures/02_defect_specific_morph.png 저장

## 셀 15: 모폴로지 커널 형태/크기 영향 분석
- Scratches 이미지에 대해:
  - 커널 형태: rect, ellipse, cross
  - 커널 크기: 3, 5, 7, 9
  - 연산: morphological_gradient (가장 시각적 차이가 큰 연산)
- 3행(형태) × 4열(크기) 시각화
- figsize=(16, 12)
- outputs/figures/02_kernel_shape_size_impact.png 저장

## ===== Part 4: 통합 파이프라인 =====

## 셀 16: 블러 → 샤프닝 순차 파이프라인 비교
- 각 클래스 대표 이미지에 blur_then_sharpen() 적용
- 4가지 조합 비교:
  - gaussian → unsharp
  - bilateral → unsharp
  - bilateral → adaptive_sharpen
  - median → laplacian
- 6행(클래스) × 5열(원본 + 4가지 조합) 시각화
- 각 이미지에 edge_density + SSIM 표시
- figsize=(20, 24)
- 제목: "블러→샤프닝 파이프라인 조합별 비교"
- outputs/figures/02_blur_sharpen_pipeline.png 저장

## 셀 17: 풀 파이프라인 (정규화 → 블러 → 샤프닝 → 모폴로지)
- 소주제 ①의 정규화와 소주제 ②의 필터링을 합친 전체 파이프라인 시연
- 파이프라인:
  1. CLAHE 정규화 (소주제 ①)
  2. Bilateral 블러 (노이즈 제거)
  3. Adaptive Sharpen (결함 강조)
  4. Opening (잔여 노이즈 제거)
- 각 클래스 대표 이미지에 4단계 순차 적용
- 6행(클래스) × 5열(원본, CLAHE, +블러, +샤프닝, +모폴로지) 시각화
- 각 단계별 edge_density 변화를 선 그래프로 추가 시각화
- figsize=(20, 24) + 추가 차트 figsize=(12, 6)
- 제목: "소주제 ①+② 통합 전처리 파이프라인"
- outputs/figures/02_full_pipeline.png 저장
- outputs/figures/02_pipeline_edge_density_flow.png 저장

## 셀 18: 전처리 전/후 정량 평가 종합
- 전체 데이터셋 1,800장에 대해 풀 파이프라인 적용
  (시간 절약을 위해 클래스당 50장 샘플링도 가능)
- 전처리 전/후의 클래스별 평균 평가 지표 (edge_density, laplacian_var, noise_level) 계산
- 결과를 pandas DataFrame으로 정리
- seaborn의 grouped bar chart로 시각화 (전/후 비교)
- figsize=(14, 6)
- outputs/figures/02_full_evaluation.png 저장

## ===== Part 5: 결론 =====

## 셀 19: 핵심 발견사항 정리 (마크다운)
- 마크다운 셀로 소주제 ②의 핵심 분석 결과를 정리:
  1. 블러 방법 비교: 각 클래스별 최적 블러 방법과 그 이유
  2. Bilateral Filter의 우위: 에지 보존과 노이즈 제거의 균형
  3. 적응형 샤프닝의 효과: 일반 샤프닝 대비 노이즈 증폭 억제
  4. 모폴로지 연산의 역할: TopHat/BlackHat의 결함 유형별 효과
  5. 최적 파이프라인 제안: CLAHE → Bilateral → Adaptive Sharpen → Opening
  6. 결함 유형별 맞춤 전처리의 가능성과 한계
  7. "이 전처리 파이프라인이 소주제 ④(ML 분류)에서 얼마나 성능 향상을 가져오는지는
     소주제 ④에서 정량적으로 검증할 예정"

## 셀 20: 소주제 ③ 연결 포인트 (마크다운)
- "소주제 ③에서는 이 전처리 결과를 기반으로 에지 검출 및 윤곽선 분석을 수행한다.
  특히 소주제 ②에서 발견한 '블러 강도 vs 에지 보존도 트레이드오프'가
  소주제 ③의 Canny 에지 검출 성능에 어떤 영향을 미치는지를 분석할 것이다."

[시각화 규칙]
- 모든 figure에 plt.tight_layout() 적용
- 저장 시 dpi=150, bbox_inches='tight'
- 한글 폰트: plt.rcParams['font.family'] = 'AppleGothic'
- plt.rcParams['axes.unicode_minus'] = False
- 이미지 표시 시 cmap='gray' 통일
- 각 시각화 셀 끝에 print("✅ 저장 완료: {파일 경로}") 출력
- 대형 격자 시각화에서 제목 폰트: fontsize=8~10 (겹침 방지)
```

---

## 🚀 Phase 6: preprocessing/__init__.py 업데이트

### 6.1 Claude Code 지시사항

```
preprocessing/__init__.py를 업데이트하여 소주제 ② 모듈을 추가 export해줘.

[파일 위치] preprocessing/__init__.py

[추가 내용]
- 기존 소주제 ① 모듈 (alignment, roi, normalization) 유지
- 소주제 ② 모듈 추가: filters, sharpening, morphology
- __all__ 업데이트
- 버전: __version__ = "0.2.0"

[예시 사용법 — docstring에 추가]
```python
# 소주제 ② 필터링 및 샤프닝
from preprocessing.filters import gaussian_blur, bilateral_filter, compare_blur_methods
from preprocessing.sharpening import unsharp_mask, adaptive_sharpen, blur_then_sharpen
from preprocessing.morphology import tophat, blackhat, defect_enhancement_morph

# 통합 파이프라인 예시
from preprocessing.normalization import clahe_equalization
from preprocessing.filters import bilateral_filter
from preprocessing.sharpening import adaptive_sharpen
from preprocessing.morphology import opening

img = clahe_equalization(raw_img)
img = bilateral_filter(img, d=9, sigma_color=75, sigma_space=75)
img = adaptive_sharpen(img, blur_ksize=5, sharp_amount=1.5, noise_threshold=10)
img = opening(img, kernel_shape="rect", kernel_size=3)
```
```

---

## 📊 산출물 체크리스트

### 코드 파일

| 파일 | 상태 | 함수 수 | 설명 |
|------|------|---------|------|
| `preprocessing/filters.py` | ⬜ | 8개 | 블러/노이즈 제거 |
| `preprocessing/sharpening.py` | ⬜ | 9개 | 샤프닝/결함 강조 |
| `preprocessing/morphology.py` | ⬜ | 11개 | 모폴로지 연산 |
| `utils/filter_utils.py` | ⬜ | 8개 | 필터 비교/평가 유틸리티 |
| `preprocessing/__init__.py` | ⬜ | — | 업데이트 (v0.2.0) |
| `notebooks/02_filtering_sharpening.ipynb` | ⬜ | 20셀 | 분석 노트북 |

### 시각화 산출물

| 파일명 | 상태 | 내용 |
|--------|------|------|
| `02_blur_comparison_all.png` | ⬜ | 6클래스 × 6블러 방법 비교 |
| `02_progressive_blur.png` | ⬜ | 가우시안 블러 강도별 에지 변화 |
| `02_blur_vs_edge_density.png` | ⬜ | 블러 강도 vs 에지 밀도 선 그래프 (6클래스) |
| `02_bilateral_param_search.png` | ⬜ | Bilateral Filter 5×5 파라미터 격자 |
| `02_sharpen_comparison_all.png` | ⬜ | 6클래스 × 10샤프닝 방법 비교 |
| `02_unsharp_param_search.png` | ⬜ | Unsharp Mask 5×5 파라미터 격자 |
| `02_adaptive_vs_normal_sharpen.png` | ⬜ | 적응형 vs 일반 샤프닝 비교 |
| `02_emboss_depth.png` | ⬜ | 엠보싱 결함 깊이 시각화 |
| `02_morphology_comparison_all.png` | ⬜ | 6클래스 × 8모폴로지 연산 비교 |
| `02_tophat_blackhat_analysis.png` | ⬜ | TopHat/BlackHat 결함 추출 분석 |
| `02_defect_specific_morph.png` | ⬜ | 결함 유형별 맞춤 모폴로지 비교 |
| `02_kernel_shape_size_impact.png` | ⬜ | 커널 형태/크기 영향 분석 |
| `02_blur_sharpen_pipeline.png` | ⬜ | 블러→샤프닝 4가지 조합 비교 |
| `02_full_pipeline.png` | ⬜ | 소주제 ①+② 통합 4단계 파이프라인 |
| `02_pipeline_edge_density_flow.png` | ⬜ | 파이프라인 단계별 에지 밀도 변화 |
| `02_full_evaluation.png` | ⬜ | 전처리 전/후 정량 평가 종합 |

---

## ⚠️ Claude Code 실행 시 주의사항

### 연산 시간 관련

1. **Non-Local Means Denoising**: `cv2.fastNlMeansDenoising()`은 다른 블러 방법 대비 10~50배 느림. 전체 데이터셋(1,800장) 적용 시 시간이 오래 걸릴 수 있으므로, 배치 평가(셀 18)에서는 NLM을 제외하거나 샘플링하는 것을 권장.

2. **Bilateral Filter**: 커널이 클수록(d 값) 연산 시간이 급증. d=9 이상은 200×200 이미지에서도 체감될 수 있음. 파라미터 탐색(셀 6)에서 d=9로 고정하고 sigma만 변경하는 것을 권장.

3. **대형 격자 시각화**: 셀 8(6×10 격자)은 60개 이미지를 동시에 표시. 메모리 사용량이 높을 수 있으므로 figsize를 적절히 조절하고, 저장 후 `plt.close()`로 메모리 해제할 것.

### 코딩 관련

1. **Float Overflow**: 샤프닝 연산에서 `float(image) + amount * diff`가 255를 초과하거나 0 미만이 될 수 있음. **반드시** `np.clip(0, 255).astype(np.uint8)` 적용.

2. **Emboss 오프셋**: 엠보싱 결과는 -255~255 범위. +128 오프셋으로 중간 톤 기준 표현. `np.clip(0, 255)` 적용 필수.

3. **SSIM 의존성**: `skimage.metrics.structural_similarity` 사용. `scikit-image`가 설치되어 있는지 확인. `from skimage.metrics import structural_similarity as ssim` 형태로 import.

4. **모폴로지 커널과 결함 크기의 관계**: TopHat/BlackHat에서 커널 크기가 결함보다 작으면 결함이 추출되지 않음. NEU 데이터(200×200)에서 결함 크기를 고려하면 커널 7~11 정도가 적절. 너무 크면(21 이상) 배경 텍스처까지 결함으로 추출.

### 소주제 간 연결

1. **소주제 ①에서 받는 것**: `clahe_equalization()` 함수를 정규화 단계로 활용. 소주제 ①의 EDA에서 확인한 클래스별 밝기 분포 특성을 필터 파라미터 선정에 참고.

2. **소주제 ③에 넘기는 것**: 이 모듈에서 구현한 `blur_then_sharpen()` 결과를 소주제 ③의 에지 검출 입력으로 활용. 특히 "블러 강도에 따른 Canny 에지 품질 변화"를 소주제 ③에서 정량 분석.

3. **소주제 ④에 넘기는 것**: 셀 17에서 확정한 최적 파이프라인(CLAHE → Bilateral → Adaptive Sharpen → Opening)을 소주제 ④의 전처리로 사용. `filter_utils.py`의 `evaluate_filter()` 함수는 소주제 ④에서 "전처리 적용 시 ML 성능 변화"를 분석할 때 재활용.

4. **Streamlit 대시보드 연결**: `compare_blur_methods()`, `compare_sharpen_methods()`, `compare_morphology_methods()` 함수를 Streamlit Page 2(전처리 실험실)에서 직접 호출하여 인터랙티브 비교 제공. `progressive_blur()`는 슬라이더 연동에 적합.

---

## 📝 Claude Code 실행 순서 요약

```
1단계: preprocessing/filters.py 구현 → 테스트
2단계: preprocessing/sharpening.py 구현 → 테스트
3단계: preprocessing/morphology.py 구현 → 테스트
4단계: utils/filter_utils.py 구현 → 테스트
5단계: preprocessing/__init__.py 업데이트
6단계: notebooks/02_filtering_sharpening.ipynb 전체 실행 → 시각화 저장
7단계: 산출물 체크리스트 확인
```

각 단계별로 Claude Code에 해당 Phase의 지시사항을 복사하여 실행하면 됩니다.

---

## 🔗 소주제 ②의 핵심 산출물이 이후에 쓰이는 곳 요약

| 산출물 | 소주제 ③ | 소주제 ④ | Streamlit |
|--------|----------|----------|-----------|
| `bilateral_filter()` | Canny 에지 입력 전처리 | 전처리 파이프라인 구성 | Page 2 슬라이더 연동 |
| `adaptive_sharpen()` | — | 전처리 파이프라인 구성 | Page 2 체크박스 연동 |
| `tophat()` / `blackhat()` | 윤곽선 분석 보조 | 특징 벡터 보강 가능 | Page 2 시각화 |
| `defect_enhancement_morph()` | — | 클래스별 맞춤 전처리 실험 | — |
| `evaluate_filter()` | 에지 검출 품질 측정 | 전처리 전/후 성능 비교 | Page 4 평가 지표 |
| 최적 파이프라인 조합 | 에지 검출 입력 결정 | ML 학습 데이터 전처리 | Page 3 기본 전처리 |
