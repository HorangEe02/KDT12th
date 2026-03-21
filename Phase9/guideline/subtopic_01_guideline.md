# 🔧 소주제 ① — 정밀 검사를 위한 이미지 정렬 및 ROI 추출

## Claude Code 실행 가이드라인

> **프로젝트**: OpenCV & ML 하이브리드 부품 결함 자동 검수 시스템  
> **연계 차시**: 1~2차시 (픽셀/채널 구조, 색공간, ROI)  
> **담당 역할**: A. 데이터 & 전처리 담당  
> **작성일**: 2026.03.19

---

## 📋 실행 전 체크리스트

### 사전 준비 사항

1. **NEU 데이터셋 다운로드 완료**
   - 출처: https://www.kaggle.com/datasets/kaustubhdikshit/neu-surface-defect-database
   - 프로젝트 루트 아래 `data/NEU-DET/` 경로에 배치
   - 폴더 구조 확인:
     ```
     data/NEU-DET/
     ├── Crazing/
     │   ├── Cr_1.bmp ~ Cr_300.bmp
     ├── Inclusion/
     │   ├── In_1.bmp ~ In_300.bmp
     ├── Patches/
     │   ├── Pa_1.bmp ~ Pa_300.bmp
     ├── Pitted_Surface/  (또는 Pitted Surface)
     │   ├── PS_1.bmp ~ PS_300.bmp
     ├── Rolled-in_Scale/  (또는 Rolled-in Scale)
     │   ├── RS_1.bmp ~ RS_300.bmp
     └── Scratches/
         ├── Sc_1.bmp ~ Sc_300.bmp
     ```
   - ⚠️ Kaggle 데이터셋에 따라 폴더명에 언더스코어(`_`) 또는 공백/하이픈이 있을 수 있음. 코드에서 `os.listdir()`로 실제 폴더명을 먼저 확인할 것

2. **Python 환경 구성 완료**
   ```bash
   pip install opencv-python numpy matplotlib seaborn scikit-learn scikit-image jupyter
   ```

3. **프로젝트 디렉토리 구조**
   ```
   project_root/
   ├── data/
   │   └── NEU-DET/          # 데이터셋
   ├── preprocessing/
   │   ├── __init__.py
   │   ├── alignment.py      # [이 가이드에서 생성] 이미지 정렬 모듈
   │   ├── roi.py            # [이 가이드에서 생성] ROI 추출 모듈
   │   └── normalization.py  # [이 가이드에서 생성] 밝기/대비 정규화 모듈
   ├── utils/
   │   ├── __init__.py
   │   └── data_loader.py    # [이 가이드에서 생성] 데이터 로드 유틸리티
   ├── notebooks/
   │   └── 01_alignment_roi.ipynb  # [이 가이드에서 생성] 분석 노트북
   ├── outputs/
   │   └── figures/           # 시각화 결과 저장
   └── README.md
   ```

---

## 🎯 소주제 ① 목표 및 범위

### 최종 목표

NEU 금속 표면 결함 이미지에 대해 **기하학적 정렬 → ROI 추출 → 밝기/대비 정규화**의 3단계 전처리 파이프라인을 구축하고, 각 단계의 효과를 시각적으로 검증한다.

### 세부 목표

| # | 목표 | 산출물 |
|---|------|--------|
| 1 | NEU 데이터셋 로드 및 EDA | `data_loader.py`, EDA 시각화 |
| 2 | 이미지 기하학적 정렬 모듈 구현 | `alignment.py` |
| 3 | ROI 추출 모듈 구현 | `roi.py` |
| 4 | 밝기/대비 정규화 모듈 구현 | `normalization.py` |
| 5 | 전처리 파이프라인 통합 및 시각화 | `01_alignment_roi.ipynb` |

---

## 🚀 Phase 1: 데이터 로더 구현 및 EDA

### 1.1 Claude Code 지시사항

```
다음 요구사항에 따라 utils/data_loader.py를 구현해줘.

[파일 위치] utils/data_loader.py

[기능 요구사항]
1. NEUDataLoader 클래스 구현
   - __init__(self, data_dir: str): 데이터 디렉토리 경로를 받아 초기화
   - 6개 클래스명을 자동으로 탐지 (os.listdir 사용, 숨김 파일 제외)
   - 클래스명 매핑 딕셔너리: 폴더명 → 한글명 (예: "Crazing" → "균열")

2. load_all_images(self) -> tuple[np.ndarray, np.ndarray, list[str]]
   - 전체 1,800장 이미지를 numpy 배열로 로드
   - 반환: (images, labels, class_names)
   - images shape: (1800, 200, 200) — 그레이스케일
   - labels shape: (1800,) — 0~5 정수 라벨
   - OpenCV의 cv2.imread(path, cv2.IMREAD_GRAYSCALE) 사용
   - 로드 진행률 출력 (tqdm 또는 print)

3. load_class_images(self, class_name: str, n_samples: int = None) -> np.ndarray
   - 특정 클래스의 이미지만 로드
   - n_samples가 지정되면 해당 수만큼 랜덤 샘플링

4. get_sample_images(self, n_per_class: int = 5) -> dict[str, np.ndarray]
   - 각 클래스별로 n_per_class장씩 랜덤 샘플링하여 딕셔너리로 반환
   - 키: 클래스명, 값: (n_per_class, 200, 200) 배열

5. split_data(self, test_size: float = 0.2, random_state: int = 42) -> tuple
   - sklearn.model_selection.train_test_split 사용
   - stratify=labels로 클래스 비율 유지
   - 반환: (X_train, X_test, y_train, y_test)

6. get_dataset_stats(self) -> pd.DataFrame
   - 클래스별 통계: 이미지 수, 평균 밝기, 밝기 표준편차, 최소/최대 픽셀값
   - pandas DataFrame으로 반환

[코딩 규칙]
- Type hints 사용
- Docstring 작성 (Google style)
- 에러 처리: 폴더 미존재 시 FileNotFoundError 발생
- 로그 출력: print로 로딩 진행 상황 알려줄 것
- numpy, cv2, os, glob, sklearn, pandas import

[테스트]
- 파일 하단에 if __name__ == "__main__": 블록으로 테스트 코드 작성
- 데이터 로드 → 전체 이미지 수/라벨 분포 출력 → split 결과 출력
```

### 1.2 EDA 노트북 지시사항

```
다음 요구사항에 따라 notebooks/01_alignment_roi.ipynb 의 Phase 1 (EDA) 부분을 구현해줘.

[파일 위치] notebooks/01_alignment_roi.ipynb

[셀 구성]

## 셀 1: 환경 설정 및 import
- 필요한 라이브러리 import (cv2, numpy, matplotlib, seaborn, os, sys)
- 프로젝트 루트를 sys.path에 추가
- utils.data_loader에서 NEUDataLoader import
- matplotlib 한글 폰트 설정 (macOS: AppleGothic)
- %matplotlib inline 설정
- 시각화 기본 스타일: plt.style.use('seaborn-v0_8-whitegrid')

## 셀 2: 데이터 로드
- NEUDataLoader 인스턴스 생성
- load_all_images()로 전체 데이터 로드
- images.shape, labels.shape 출력
- 클래스별 이미지 수 확인 (np.unique로 카운트)

## 셀 3: 클래스별 샘플 이미지 시각화
- 6행 × 5열 격자 (6클래스 × 클래스당 5장)
- figsize=(15, 18)
- 각 행의 첫 번째 이미지에 클래스명(한글) 표시
- 각 이미지: 200×200 그레이스케일, cmap='gray'
- 제목: "NEU 금속 표면 결함 데이터셋 — 클래스별 샘플"
- outputs/figures/01_class_samples.png 로 저장

## 셀 4: 클래스별 픽셀 밝기 분포 (히스토그램)
- 6개 서브플롯 (2행 × 3열)
- figsize=(16, 10)
- 각 클래스별로 전체 300장의 평균 히스토그램 (bins=256, range=[0,256])
- 각 서브플롯에 평균±표준편차 수직선 표시
- 서브플롯 제목: 클래스명(한글) + 평균 밝기 수치
- 전체 제목: "클래스별 픽셀 밝기 분포"
- outputs/figures/01_pixel_distribution.png 로 저장

## 셀 5: 클래스별 통계 요약 테이블
- get_dataset_stats() 호출
- DataFrame 출력 (display)
- 인사이트 코멘트: 어떤 클래스가 밝기 분포에서 구별되는지 마크다운으로 정리

## 셀 6: 단일 이미지 상세 분석
- 각 클래스에서 1장씩 선택 (대표 이미지)
- 2행 × 6열 (위: 원본 이미지, 아래: 해당 이미지의 픽셀 히스토그램)
- figsize=(20, 8)
- 각 이미지 아래에 min/max/mean/std 수치 표시
- 제목: "클래스별 대표 이미지 및 픽셀 분포 상세"
- outputs/figures/01_single_image_analysis.png 로 저장

[시각화 규칙]
- 모든 figure에 plt.tight_layout() 적용
- 저장 시 dpi=150, bbox_inches='tight'
- 한글 폰트: plt.rcParams['font.family'] = 'AppleGothic'
- 마이너스 기호 깨짐 방지: plt.rcParams['axes.unicode_minus'] = False
```

---

## 🚀 Phase 2: 이미지 기하학적 정렬 모듈

### 2.1 배경 설명

NEU 데이터셋은 이미 정렬된 상태이지만, 실제 제조 현장에서는 카메라 각도, 부품 배치 오차 등으로 이미지가 틀어져 있을 수 있다. 이 모듈은 **"실환경 적용 시 필요한 전처리"**를 시연하는 목적으로 구현한다.

### 2.2 Claude Code 지시사항

```
다음 요구사항에 따라 preprocessing/alignment.py를 구현해줘.

[파일 위치] preprocessing/alignment.py

[기능 요구사항]

1. rotate_image(image: np.ndarray, angle: float, scale: float = 1.0) -> np.ndarray
   - 이미지 중심 기준으로 지정 각도만큼 회전
   - cv2.getRotationMatrix2D() + cv2.warpAffine() 사용
   - 회전 후 검은색 영역이 생기지 않도록 borderMode=cv2.BORDER_REPLICATE 적용
   - scale: 회전 시 스케일 조정 (기본 1.0)

2. auto_deskew(image: np.ndarray) -> tuple[np.ndarray, float]
   - 이미지의 기울어진 각도를 자동 감지하여 보정
   - 구현 방법:
     a. 이미지 이진화 (cv2.threshold, OTSU)
     b. cv2.findContours()로 윤곽선 검출
     c. 가장 큰 윤곽선에 대해 cv2.minAreaRect() 적용
     d. 회전 각도 추출 (minAreaRect의 angle 값)
     e. 추출된 각도로 rotate_image 호출하여 보정
   - 반환: (보정된 이미지, 감지된 기울기 각도)

3. affine_transform(image: np.ndarray, src_points: np.ndarray, dst_points: np.ndarray) -> np.ndarray
   - 3점 기반 어파인 변환
   - cv2.getAffineTransform() + cv2.warpAffine() 사용
   - src_points, dst_points: (3, 2) shape의 float32 배열

4. perspective_transform(image: np.ndarray, src_points: np.ndarray, dst_points: np.ndarray) -> np.ndarray
   - 4점 기반 원근(투시) 변환
   - cv2.getPerspectiveTransform() + cv2.warpPerspective() 사용
   - src_points, dst_points: (4, 2) shape의 float32 배열
   - 실제 부품 촬영 시 사다리꼴 형태의 왜곡 보정에 활용

5. flip_image(image: np.ndarray, flip_code: int) -> np.ndarray
   - 이미지 대칭 (좌우/상하/양방향)
   - cv2.flip() 사용
   - flip_code: 0(상하), 1(좌우), -1(양방향)

6. resize_with_aspect_ratio(image: np.ndarray, target_size: int = 200, interpolation: int = cv2.INTER_LINEAR) -> np.ndarray
   - 종횡비를 유지하면서 리사이즈
   - 긴 변을 target_size에 맞추고, 짧은 변은 비율에 맞게 조정
   - 결과 이미지를 target_size × target_size 정사각형 캔버스 중앙에 배치 (패딩은 검정)

7. demonstrate_alignment(image: np.ndarray, angles: list[float] = [-15, -10, -5, 5, 10, 15]) -> dict
   - 시연용 함수: 원본 이미지를 여러 각도로 인위적으로 회전시킨 뒤, auto_deskew로 복원
   - 각 각도별로 (회전된 이미지, 복원된 이미지, 감지된 각도, 복원 오차) 기록
   - 반환: {"angle_X": {"rotated": img, "restored": img, "detected_angle": float, "error": float}}

[코딩 규칙]
- Type hints 사용
- Docstring 작성 (Google style)
- 모든 함수는 입력 이미지를 변경하지 않음 (copy 후 처리)
- import: cv2, numpy, typing
- 각 함수에 입력 이미지 유효성 검사 (None 체크, ndim 체크)

[테스트]
- if __name__ == "__main__": 블록에서 테스트
- 200×200 합성 이미지(직사각형 포함)로 각 함수 동작 확인
- demonstrate_alignment 결과를 print로 출력
```

---

## 🚀 Phase 3: ROI 추출 모듈

### 3.1 배경 설명

ROI(Region of Interest) 추출은 이미지에서 **실제 검사가 필요한 영역만 잘라내는** 작업이다. NEU 데이터셋은 이미 200×200으로 크롭된 상태이지만, 결함이 특정 영역에 집중되는 경향이 있으므로 ROI 추출을 통해 검사 효율을 높일 수 있다.

### 3.2 Claude Code 지시사항

```
다음 요구사항에 따라 preprocessing/roi.py를 구현해줘.

[파일 위치] preprocessing/roi.py

[기능 요구사항]

1. extract_roi_manual(image: np.ndarray, x: int, y: int, w: int, h: int) -> np.ndarray
   - 수동 좌표 지정으로 ROI 추출
   - 이미지 경계 초과 시 자동 클리핑 (min/max 처리)
   - 반환: 잘라낸 ROI 이미지

2. extract_roi_center(image: np.ndarray, crop_ratio: float = 0.7) -> np.ndarray
   - 이미지 중앙 기준으로 crop_ratio 비율만큼 잘라내기
   - 200×200 이미지에서 crop_ratio=0.7이면 중앙 140×140 영역 추출
   - 추출 후 원본 크기(200×200)로 리사이즈

3. extract_roi_by_contour(image: np.ndarray, threshold_value: int = 127) -> tuple[np.ndarray, tuple]
   - 윤곽선 기반 자동 ROI 추출
   - 구현 방법:
     a. 이진화 (cv2.threshold, OTSU 또는 지정값)
     b. cv2.findContours() 실행
     c. 가장 큰 윤곽선의 바운딩 박스 계산 (cv2.boundingRect)
     d. 바운딩 박스 영역을 ROI로 추출
     e. 패딩 추가 (바운딩 박스 ±10% 확장, 이미지 경계 클리핑)
   - 반환: (ROI 이미지, (x, y, w, h) 바운딩 박스 좌표)

4. extract_roi_by_edge_density(image: np.ndarray, grid_size: int = 4) -> tuple[np.ndarray, tuple]
   - 에지 밀도 기반 관심 영역 자동 탐지
   - 구현 방법:
     a. Canny 에지 검출 적용
     b. 이미지를 grid_size × grid_size 그리드로 분할
     c. 각 그리드 셀의 에지 밀도(에지 픽셀 비율) 계산
     d. 에지 밀도가 가장 높은 셀을 포함하는 영역을 ROI로 선택
     e. 인접한 고밀도 셀들을 병합하여 최종 ROI 결정
   - 반환: (ROI 이미지, (x, y, w, h) 바운딩 박스 좌표)

5. visualize_roi(image: np.ndarray, roi_bbox: tuple, title: str = "ROI 추출 결과") -> np.ndarray
   - 원본 이미지 위에 ROI 영역을 초록색 사각형으로 표시
   - cv2.rectangle() 사용, 색상: (0, 255, 0), 두께: 2
   - 그레이스케일 → BGR 변환 후 사각형 표시
   - 반환: ROI가 표시된 컬러 이미지

6. multi_scale_roi(image: np.ndarray, scales: list[float] = [0.5, 0.7, 0.9]) -> list[np.ndarray]
   - 여러 스케일로 중앙 ROI 추출
   - 각 스케일별 추출 결과를 리스트로 반환
   - 소주제 ④(ML 분류)에서 멀티스케일 특징 추출에 활용 가능

7. create_roi_comparison(image: np.ndarray) -> dict
   - 시연용: 하나의 이미지에 대해 모든 ROI 추출 방법의 결과를 비교
   - 반환: {"manual_center": img, "center_70": img, "contour": img, "edge_density": img}
   - 각 결과에 ROI 바운딩 박스 좌표도 함께 포함

[코딩 규칙]
- Type hints 사용
- Docstring 작성 (Google style)
- 모든 함수는 입력 이미지를 변경하지 않음
- ROI 추출 실패 시 (윤곽선 미검출 등) 원본 이미지를 그대로 반환하되 경고 메시지 출력
- import: cv2, numpy, typing, warnings

[테스트]
- if __name__ == "__main__": 블록에서 테스트
- NEU 데이터셋의 각 클래스에서 1장씩 로드하여 모든 ROI 함수 테스트
- create_roi_comparison 결과를 콘솔에 출력
```

---

## 🚀 Phase 4: 밝기/대비 정규화 모듈

### 4.1 배경 설명

금속 표면 이미지는 조명 조건, 촬영 환경에 따라 밝기와 대비가 크게 달라질 수 있다. 정규화를 통해 이미지 간 일관성을 확보하면 이후 특징 추출과 ML 분류의 안정성이 향상된다.

### 4.2 Claude Code 지시사항

```
다음 요구사항에 따라 preprocessing/normalization.py를 구현해줘.

[파일 위치] preprocessing/normalization.py

[기능 요구사항]

1. histogram_equalization(image: np.ndarray) -> np.ndarray
   - 글로벌 히스토그램 균등화
   - cv2.equalizeHist() 사용
   - 전체 이미지의 밝기 분포를 균등하게 펼침

2. clahe_equalization(image: np.ndarray, clip_limit: float = 2.0, tile_grid_size: tuple = (8, 8)) -> np.ndarray
   - 적응형 히스토그램 균등화 (CLAHE)
   - cv2.createCLAHE() 사용
   - clip_limit: 대비 증폭 제한 (기본 2.0)
   - tile_grid_size: 타일 크기 (기본 8×8)
   - 글로벌 균등화보다 국소 대비 개선에 효과적

3. min_max_normalize(image: np.ndarray, target_min: int = 0, target_max: int = 255) -> np.ndarray
   - Min-Max 정규화
   - 이미지의 최솟값→target_min, 최댓값→target_max로 선형 스케일링
   - cv2.normalize() 또는 수동 계산 사용

4. standardize(image: np.ndarray) -> np.ndarray
   - Z-score 표준화 (평균 0, 표준편차 1)
   - float64로 변환 후 (image - mean) / std 계산
   - 결과를 0~255 범위로 재매핑하여 uint8로 반환
   - ⚠️ std=0인 경우(단색 이미지) 처리 필요

5. gamma_correction(image: np.ndarray, gamma: float = 1.0) -> np.ndarray
   - 감마 보정을 통한 밝기 조정
   - gamma < 1: 어두운 영역 밝게 (밝은 이미지)
   - gamma > 1: 밝은 영역 어둡게 (어두운 이미지)
   - Look-up table 방식으로 구현 (효율적)

6. auto_brightness_contrast(image: np.ndarray, clip_hist_percent: float = 1.0) -> np.ndarray
   - 자동 밝기/대비 조정
   - 히스토그램의 상/하위 clip_hist_percent%를 클리핑하여 최적 범위 결정
   - alpha(대비) = 255 / (max_val - min_val)
   - beta(밝기) = -min_val * alpha
   - cv2.convertScaleAbs() 적용

7. normalize_pipeline(image: np.ndarray, method: str = "clahe", **kwargs) -> np.ndarray
   - 정규화 방법을 문자열로 선택하여 적용하는 통합 함수
   - method 옵션: "histogram", "clahe", "minmax", "standardize", "gamma", "auto"
   - **kwargs: 각 방법의 파라미터를 전달
   - 잘못된 method 입력 시 ValueError 발생

8. compare_normalizations(image: np.ndarray) -> dict[str, np.ndarray]
   - 모든 정규화 방법의 결과를 한번에 비교
   - 반환: {"original": img, "histogram_eq": img, "clahe": img, "minmax": img, "standardize": img, "gamma_0.5": img, "gamma_1.5": img, "auto": img}

[코딩 규칙]
- Type hints 사용
- Docstring 작성 (Google style)
- 모든 함수는 입력 이미지를 변경하지 않음 (copy 후 처리)
- 입력 이미지가 컬러(3채널)인 경우 그레이스케일로 변환 후 처리하되, 경고 메시지 출력
- import: cv2, numpy, typing, warnings

[테스트]
- if __name__ == "__main__": 블록에서 테스트
- NEU 데이터셋에서 밝기가 다른 이미지 3장 선택하여 모든 정규화 결과 비교
- 각 결과의 평균/표준편차 출력
```

---

## 🚀 Phase 5: 통합 파이프라인 및 시각화

### 5.1 Claude Code 지시사항 — 노트북 Phase 2~4 추가

```
notebooks/01_alignment_roi.ipynb에 Phase 2~4 셀을 추가해줘.
(Phase 1의 EDA 셀 이후에 이어서 작성)

## ===== Phase 2: 이미지 정렬 시연 =====

## 셀 7: 정렬 모듈 import 및 시연 데이터 준비
- preprocessing.alignment에서 함수들 import
- NEU 데이터셋에서 Scratches 클래스 이미지 1장 선택 (선형 패턴이라 기울기가 잘 보임)
- 원본 이미지 표시

## 셀 8: 인위적 회전 및 자동 복원 시연
- demonstrate_alignment() 함수 호출 (angles=[-15, -10, -5, 5, 10, 15])
- 3행 × 6열 시각화:
  - 1행: 인위적으로 회전된 이미지들
  - 2행: auto_deskew로 복원된 이미지들
  - 3행: 원본과 복원 이미지의 차이(절대값)
- 각 열 제목: "회전 {angle}° → 감지: {detected}° (오차: {error}°)"
- figsize=(24, 12)
- outputs/figures/01_alignment_demo.png 저장

## 셀 9: 대칭 변환 시연
- 각 클래스 대표 이미지 1장씩, 좌우/상하/양방향 대칭
- 4행 × 6열 (원본, 좌우, 상하, 양방향) × 6클래스
- figsize=(20, 14)
- outputs/figures/01_flip_demo.png 저장

## 셀 10: 어파인/투시 변환 시연
- 1장의 이미지에 대해 어파인 변환, 투시 변환 시연
- 변환 전/후를 나란히 표시
- 변환 포인트를 이미지 위에 원으로 표시 (cv2.circle)
- figsize=(16, 6)
- outputs/figures/01_transform_demo.png 저장

## ===== Phase 3: ROI 추출 =====

## 셀 11: ROI 모듈 import 및 전체 방법 비교
- preprocessing.roi에서 함수들 import
- 각 클래스에서 1장씩 선택하여 4가지 ROI 방법 적용
- 6행(클래스) × 5열(원본 + 4가지 ROI 방법) 시각화
- 각 이미지에 ROI 바운딩 박스를 초록색으로 표시
- figsize=(20, 24)
- outputs/figures/01_roi_comparison.png 저장

## 셀 12: 에지 밀도 기반 ROI 상세 분석
- Scratches 이미지 1장에 대해:
  - 원본 이미지
  - Canny 에지 맵
  - grid_size=4 에지 밀도 히트맵 (seaborn heatmap)
  - 최종 ROI 추출 결과
- 1행 × 4열 시각화
- figsize=(20, 5)
- outputs/figures/01_edge_density_roi.png 저장

## 셀 13: 멀티스케일 ROI 시연
- 1장의 이미지에 대해 scales=[0.5, 0.6, 0.7, 0.8, 0.9] 멀티스케일 ROI
- 1행 × 5열로 각 스케일 결과 표시
- 각 이미지 아래에 추출 크기 표시
- figsize=(18, 4)
- outputs/figures/01_multiscale_roi.png 저장

## ===== Phase 4: 밝기/대비 정규화 =====

## 셀 14: 정규화 모듈 import 및 전체 방법 비교
- preprocessing.normalization에서 함수들 import
- 각 클래스에서 1장씩 선택하여 모든 정규화 방법 적용
- 6행(클래스) × 8열(원본 + 7가지 정규화) 시각화
- 각 이미지 아래에 mean±std 수치 표시
- figsize=(28, 22)
- outputs/figures/01_normalization_comparison.png 저장

## 셀 15: 히스토그램 균등화 vs CLAHE 상세 비교
- 6클래스 대표 이미지에 대해:
  - 상단 3행: 원본/HistEq/CLAHE 이미지
  - 하단 3행: 각각의 픽셀 히스토그램
- figsize=(20, 18)
- 인사이트: "CLAHE가 금속 표면 결함에서 더 효과적인 이유" 마크다운 셀 추가
- outputs/figures/01_histeq_vs_clahe.png 저장

## 셀 16: 감마 보정 파라미터 탐색
- 1장의 이미지에 대해 gamma=[0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0] 적용
- 1행 × 7열로 감마값별 결과 표시
- 각 이미지 아래에 gamma값과 mean 밝기 표시
- figsize=(24, 4)
- outputs/figures/01_gamma_exploration.png 저장

## ===== Phase 5: 통합 파이프라인 =====

## 셀 17: 전처리 파이프라인 통합 함수 정의
- preprocess_pipeline(image, align=False, roi_method="center", normalize_method="clahe") 함수 정의
- 3단계 순차 적용: 정렬 → ROI 추출 → 정규화
- 각 단계 적용 전/후 이미지를 딕셔너리로 반환
  {"original": img, "aligned": img, "roi": img, "normalized": img}

## 셀 18: 파이프라인 적용 결과 시각화
- 각 클래스 대표 이미지에 대해 파이프라인 적용
- 6행(클래스) × 4열(원본 → 정렬 → ROI → 정규화)
- 각 열 위에 단계명 표시
- figsize=(16, 24)
- outputs/figures/01_pipeline_result.png 저장

## 셀 19: 전처리 전/후 통계 비교
- 전체 데이터셋(1,800장)에 파이프라인 적용 (ROI=center_0.7, Normalize=CLAHE)
- 전처리 전/후의 클래스별 평균 밝기, 표준편차를 DataFrame으로 비교
- 전처리 후 클래스 간 밝기 분포가 더 균등해졌는지 확인
- seaborn boxplot으로 전/후 비교 시각화
- figsize=(14, 6)
- outputs/figures/01_before_after_stats.png 저장

## 셀 20: Phase 1 결론 및 다음 단계
- 마크다운 셀로 소주제 ①의 핵심 발견사항 정리:
  1. NEU 데이터셋의 클래스별 밝기 분포 차이 확인
  2. auto_deskew의 정렬 복원 성능 (평균 오차 X°)
  3. 에지 밀도 기반 ROI 추출의 유효성
  4. CLAHE가 금속 표면 결함에 가장 적합한 정규화 방법인 이유
  5. 통합 파이프라인 적용 후 데이터 일관성 향상 수치
- "소주제 ②(필터링 및 샤프닝)에서 이 결과를 바탕으로 결함 특징을 강조하는 추가 전처리를 적용할 예정" 명시

[시각화 규칙]
- 모든 figure에 plt.tight_layout() 적용
- 저장 시 dpi=150, bbox_inches='tight'
- 한글 폰트: plt.rcParams['font.family'] = 'AppleGothic'
- plt.rcParams['axes.unicode_minus'] = False
- 이미지 표시 시 cmap='gray' 통일
- 각 시각화 셀 끝에 print("✅ 저장 완료: {파일 경로}") 출력
```

---

## 🚀 Phase 6: preprocessing/__init__.py 통합

### 6.1 Claude Code 지시사항

```
preprocessing/__init__.py를 작성하여 모듈을 통합 export해줘.

[파일 위치] preprocessing/__init__.py

[내용]
- alignment, roi, normalization 모듈의 주요 함수들을 한 번에 import할 수 있도록 구성
- from preprocessing import * 시 주요 함수들이 노출되도록 __all__ 정의
- 버전 정보: __version__ = "0.1.0"
- 모듈 설명 docstring 작성

[예시 사용법 — docstring에 포함]
```python
from preprocessing import rotate_image, extract_roi_center, clahe_equalization
from preprocessing.alignment import demonstrate_alignment
from preprocessing.normalization import compare_normalizations
```
```

---

## 📊 산출물 체크리스트

### 코드 파일

| 파일 | 상태 | 설명 |
|------|------|------|
| `utils/__init__.py` | ⬜ | 빈 init |
| `utils/data_loader.py` | ⬜ | NEU 데이터 로더 |
| `preprocessing/__init__.py` | ⬜ | 모듈 통합 |
| `preprocessing/alignment.py` | ⬜ | 이미지 정렬 (7개 함수) |
| `preprocessing/roi.py` | ⬜ | ROI 추출 (7개 함수) |
| `preprocessing/normalization.py` | ⬜ | 밝기/대비 정규화 (8개 함수) |
| `notebooks/01_alignment_roi.ipynb` | ⬜ | 분석 노트북 (20개 셀) |

### 시각화 산출물

| 파일명 | 상태 | 내용 |
|--------|------|------|
| `01_class_samples.png` | ⬜ | 6클래스 × 5장 샘플 격자 |
| `01_pixel_distribution.png` | ⬜ | 클래스별 픽셀 밝기 분포 |
| `01_single_image_analysis.png` | ⬜ | 대표 이미지 상세 분석 |
| `01_alignment_demo.png` | ⬜ | 자동 정렬 시연 결과 |
| `01_flip_demo.png` | ⬜ | 대칭 변환 시연 |
| `01_transform_demo.png` | ⬜ | 어파인/투시 변환 시연 |
| `01_roi_comparison.png` | ⬜ | 4가지 ROI 방법 비교 |
| `01_edge_density_roi.png` | ⬜ | 에지 밀도 ROI 상세 |
| `01_multiscale_roi.png` | ⬜ | 멀티스케일 ROI |
| `01_normalization_comparison.png` | ⬜ | 정규화 방법 전체 비교 |
| `01_histeq_vs_clahe.png` | ⬜ | HistEq vs CLAHE 상세 |
| `01_gamma_exploration.png` | ⬜ | 감마 보정 파라미터 탐색 |
| `01_pipeline_result.png` | ⬜ | 통합 파이프라인 결과 |
| `01_before_after_stats.png` | ⬜ | 전처리 전/후 통계 비교 |

---

## ⚠️ Claude Code 실행 시 주의사항

### 환경 관련

1. **macOS + M4 Pro 환경**: OpenCV는 `opencv-python`으로 설치하면 arm64 네이티브로 동작함. `opencv-python-headless`는 GUI 기능이 없으므로 cv2.imshow()를 사용하려면 `opencv-python` 필요. 단, Jupyter Notebook에서는 matplotlib으로 표시하므로 headless도 무방.

2. **한글 폰트**: macOS에서 matplotlib 한글 표시를 위해 반드시 아래 코드를 실행:
   ```python
   import matplotlib.pyplot as plt
   plt.rcParams['font.family'] = 'AppleGothic'
   plt.rcParams['axes.unicode_minus'] = False
   ```

3. **메모리**: 1,800장 × 200×200 = 약 72MB. M4 Pro 24GB 메모리에서 전혀 문제없음.

### 코딩 관련

1. **이미지 경로**: NEU 데이터셋의 폴더명은 Kaggle 버전에 따라 다를 수 있음. `data_loader.py`에서 `os.listdir()`로 실제 폴더명을 먼저 확인하는 로직 포함.

2. **OpenCV 이미지 포맷**: `cv2.imread()`로 읽은 이미지는 BGR 순서. 그레이스케일 로드 시 `cv2.IMREAD_GRAYSCALE` 플래그 사용. matplotlib 표시 시 `cmap='gray'` 지정.

3. **BMP 파일**: NEU 데이터셋은 BMP 포맷. OpenCV는 BMP를 기본 지원하므로 별도 처리 불필요.

4. **함수 독립성**: 각 전처리 함수는 독립적으로 동작해야 함. 다른 전처리 함수에 의존하지 않도록 설계. 파이프라인 조합은 노트북에서 처리.

### 소주제 간 연결

1. **소주제 ②로의 연결**: 이 모듈에서 구현한 `normalize_pipeline()` 함수의 결과를 소주제 ②의 필터링/샤프닝 입력으로 활용.

2. **소주제 ④로의 연결**: `extract_roi_center()`와 `clahe_equalization()`은 소주제 ④(ML 분류)의 전처리 파이프라인에서 기본 전처리로 사용될 예정.

3. **Streamlit 대시보드 연결**: `compare_normalizations()`과 `create_roi_comparison()` 함수는 Streamlit Page 2(전처리 실험실)에서 직접 호출하여 인터랙티브 비교 제공.

---

## 📝 Claude Code 실행 순서 요약

```
1단계: utils/data_loader.py 구현 → 테스트
2단계: preprocessing/alignment.py 구현 → 테스트
3단계: preprocessing/roi.py 구현 → 테스트
4단계: preprocessing/normalization.py 구현 → 테스트
5단계: preprocessing/__init__.py 통합
6단계: notebooks/01_alignment_roi.ipynb 전체 실행 → 시각화 저장
7단계: 산출물 체크리스트 확인
```

각 단계별로 Claude Code에 해당 Phase의 지시사항을 복사하여 실행하면 됩니다.
