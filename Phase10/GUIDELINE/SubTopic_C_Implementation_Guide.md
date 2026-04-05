# 🏭 소주제 C. PCB 기판 결함 자동 탐지 — 상세 구현 가이드라인

> **Claude Code에서 단계별로 실행할 수 있는 구현 명세서**
>
> 핵심 기술: YOLOv8 (Ultralytics) 객체 탐지 + 전이학습 파인튜닝 + mAP 평가

---

## 목차

1. [환경 설정](#1-환경-설정)
2. [데이터 다운로드 및 탐색](#2-데이터-다운로드-및-탐색)
3. [어노테이션 변환 — XML → YOLO 형식](#3-어노테이션-변환--xml--yolo-형식)
4. [YOLO 데이터셋 구성 (data.yaml)](#4-yolo-데이터셋-구성-datayaml)
5. [YOLOv8 모델 학습](#5-yolov8-모델-학습)
6. [성능 평가 및 분석](#6-성능-평가-및-분석)
7. [추론 및 탐지 결과 시각화](#7-추론-및-탐지-결과-시각화)
8. [모델 크기별 비교 실험](#8-모델-크기별-비교-실험)
9. [결과 저장 및 정리](#9-결과-저장-및-정리)

---

## 1. 환경 설정

### 1.1 프로젝트 디렉토리 생성

```bash
mkdir -p SubTopic_C_PCB_Detection/{data,models,results}
cd SubTopic_C_PCB_Detection
```

### 1.2 필수 패키지 설치

```bash
pip install ultralytics matplotlib seaborn pandas pillow tqdm lxml opencv-python
```

> **핵심**: Ultralytics 패키지 하나로 YOLOv8의 학습/평가/추론이 모두 가능합니다.
> PyTorch는 ultralytics 설치 시 자동으로 함께 설치됩니다.

### 1.3 requirements.txt

```text
ultralytics>=8.1.0
matplotlib>=3.7.0
seaborn>=0.12.0
pandas>=2.0.0
Pillow>=10.0.0
tqdm>=4.65.0
lxml>=4.9.0
opencv-python>=4.8.0
```

### 1.4 환경 확인

```python
import torch
from ultralytics import YOLO

print(f"PyTorch: {torch.__version__}")
print(f"CUDA: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")

# Ultralytics 정상 설치 확인
model = YOLO("yolov8n.pt")  # nano 모델 다운로드 (6MB)
print("Ultralytics YOLOv8 설치 확인 완료")
```

---

## 2. 데이터 다운로드 및 탐색

### 2.1 데이터셋 정보

| 항목        | 내용                                                 |
| ----------- | ---------------------------------------------------- |
| 데이터셋명  | PCB Defects Dataset                                  |
| 출처        | https://www.kaggle.com/datasets/akhatova/pcb-defects |
| 이미지 수   | 693장                                                |
| 결함 클래스 | 6종                                                  |
| 어노테이션  | Pascal VOC XML 형식 (바운딩 박스)                    |

### 2.2 6가지 PCB 결함 유형

```
┌─────────────────────────────────────────────────────────────┐
│  PCB 결함 6종 (인쇄회로기판에서 발생하는 대표적 결함)          │
├──────────────┬──────────────────────────────────────────────┤
│ missing_hole │ 홀 누락 — 드릴로 뚫어야 할 구멍이 없음        │
│ mouse_bite   │ 마우스 바이트 — 기판 가장자리의 불규칙한 침식  │
│ open_circuit │ 개방 회로 — 연결되어야 할 회로가 끊어짐        │
│ short        │ 단락 — 연결되면 안 되는 회로가 붙어버림        │
│ spur         │ 스퍼 — 불필요한 구리 돌출                     │
│ spurious_copper│ 불필요 구리 — 있으면 안 되는 구리 잔여물      │
└──────────────┴──────────────────────────────────────────────┘
```

### 2.3 다운로드

```bash
# Kaggle API
kaggle datasets download -d akhatova/pcb-defects
unzip pcb-defects.zip -d data/raw/
```

다운로드 후 폴더 구조:

```
data/raw/
├── images/              ← PCB 이미지 (.jpg)
│   ├── Missing_hole/
│   ├── Mouse_bite/
│   ├── Open_circuit/
│   ├── Short/
│   ├── Spur/
│   └── Spurious_copper/
└── Annotations/         ← Pascal VOC XML 어노테이션
    ├── Missing_hole/
    ├── Mouse_bite/
    ├── Open_circuit/
    ├── Short/
    ├── Spur/
    └── Spurious_copper/
```

### 2.4 데이터 탐색 (EDA)

```python
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

RAW_DIR = Path("data/raw")
IMG_BASE = RAW_DIR / "images"
ANN_BASE = RAW_DIR / "Annotations"

# === 클래스별 이미지/어노테이션 수 확인 ===
class_dirs = sorted([d for d in IMG_BASE.iterdir() if d.is_dir()])
print("=== 클래스별 데이터 수 ===")
total_images = 0
for class_dir in class_dirs:
    img_count = len(list(class_dir.glob("*.jpg")))
    total_images += img_count
    print(f"  {class_dir.name}: {img_count}장")
print(f"  총합: {total_images}장")

# === XML 어노테이션 파싱 및 바운딩 박스 통계 ===
all_classes = []
all_widths = []
all_heights = []
bbox_sizes = []

for ann_dir in sorted(ANN_BASE.iterdir()):
    if not ann_dir.is_dir():
        continue
    for xml_file in ann_dir.glob("*.xml"):
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # 이미지 크기
        size = root.find("size")
        if size is not None:
            w = int(size.find("width").text)
            h = int(size.find("height").text)
            all_widths.append(w)
            all_heights.append(h)

        # 바운딩 박스
        for obj in root.findall("object"):
            cls_name = obj.find("name").text
            all_classes.append(cls_name)

            bbox = obj.find("bndbox")
            x1 = int(bbox.find("xmin").text)
            y1 = int(bbox.find("ymin").text)
            x2 = int(bbox.find("xmax").text)
            y2 = int(bbox.find("ymax").text)
            bbox_sizes.append((x2 - x1, y2 - y1))

# 클래스 분포
class_counts = Counter(all_classes)
print(f"\n=== 바운딩 박스 클래스 분포 ===")
for cls, count in class_counts.most_common():
    print(f"  {cls}: {count}개")
print(f"  총 바운딩 박스: {sum(class_counts.values())}개")

# 이미지 크기 통계
print(f"\n=== 이미지 크기 ===")
print(f"  너비: {min(all_widths)} ~ {max(all_widths)} (평균: {np.mean(all_widths):.0f})")
print(f"  높이: {min(all_heights)} ~ {max(all_heights)} (평균: {np.mean(all_heights):.0f})")

# === 시각화: 클래스 분포 ===
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

classes = [c for c, _ in class_counts.most_common()]
counts = [n for _, n in class_counts.most_common()]
colors = ['#e74c3c', '#f39c12', '#2ecc71', '#3498db', '#9b59b6', '#1abc9c']

axes[0].barh(classes, counts, color=colors)
axes[0].set_xlabel("바운딩 박스 수")
axes[0].set_title("결함 클래스별 분포", fontweight='bold')
for i, v in enumerate(counts):
    axes[0].text(v + 5, i, str(v), va='center', fontweight='bold')

# 바운딩 박스 크기 분포
bw = [s[0] for s in bbox_sizes]
bh = [s[1] for s in bbox_sizes]
axes[1].scatter(bw, bh, alpha=0.3, s=10, c='#3498db')
axes[1].set_xlabel("박스 너비 (px)")
axes[1].set_ylabel("박스 높이 (px)")
axes[1].set_title("바운딩 박스 크기 분포", fontweight='bold')

plt.tight_layout()
plt.savefig("results/01_data_distribution.png", dpi=150, bbox_inches='tight')
plt.show()
```

### 2.5 샘플 이미지 + 바운딩 박스 시각화

```python
import cv2

def draw_bboxes_from_xml(img_path, xml_path):
    """XML 어노테이션을 읽어 이미지에 바운딩 박스를 그림"""
    img = cv2.imread(str(img_path))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    tree = ET.parse(xml_path)
    root = tree.getroot()

    color_map = {
        'missing_hole': (255, 0, 0), 'mouse_bite': (255, 165, 0),
        'open_circuit': (0, 200, 0), 'short': (0, 100, 255),
        'spur': (160, 32, 240), 'spurious_copper': (0, 200, 200)
    }

    labels = []
    for obj in root.findall("object"):
        cls = obj.find("name").text
        bbox = obj.find("bndbox")
        x1 = int(bbox.find("xmin").text)
        y1 = int(bbox.find("ymin").text)
        x2 = int(bbox.find("xmax").text)
        y2 = int(bbox.find("ymax").text)

        color = color_map.get(cls, (255, 255, 255))
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        cv2.putText(img, cls, (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, color, 1, cv2.LINE_AA)
        labels.append(cls)

    return img, labels

# 각 클래스에서 1장씩 샘플 시각화
fig, axes = plt.subplots(2, 3, figsize=(16, 10))
for idx, class_dir in enumerate(sorted(IMG_BASE.iterdir())):
    if not class_dir.is_dir():
        continue
    row, col = idx // 3, idx % 3

    img_files = list(class_dir.glob("*.jpg"))
    if img_files:
        img_path = img_files[0]
        # 대응하는 XML 파일 찾기
        xml_name = img_path.stem + ".xml"
        xml_path = ANN_BASE / class_dir.name / xml_name

        if xml_path.exists():
            img_drawn, labels = draw_bboxes_from_xml(img_path, xml_path)
            axes[row, col].imshow(img_drawn)
            axes[row, col].set_title(f'{class_dir.name}\n({", ".join(set(labels))})',
                                     fontsize=9, fontweight='bold')
        else:
            img = Image.open(img_path)
            axes[row, col].imshow(img)
            axes[row, col].set_title(class_dir.name, fontsize=9)

    axes[row, col].axis('off')

plt.suptitle('PCB 결함 유형별 샘플 (바운딩 박스 표시)', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig("results/02_sample_images.png", dpi=150, bbox_inches='tight')
plt.show()
```

---

## 3. 어노테이션 변환 — XML → YOLO 형식

### 3.1 YOLO 어노테이션 형식 설명

```
Pascal VOC XML 형식:
  <object>
    <name>short</name>
    <bndbox>
      <xmin>100</xmin>  <ymin>200</ymin>
      <xmax>300</xmax>  <ymax>400</ymax>
    </bndbox>
  </object>

YOLO TXT 형식 (한 줄에 하나의 객체):
  class_id  x_center  y_center  width  height
  3         0.3333    0.4286    0.3333  0.2857

  → 모든 좌표는 0~1로 정규화 (이미지 크기로 나눔)
  → class_id는 0부터 시작하는 정수
```

### 3.2 변환 스크립트

```python
import shutil
from sklearn.model_selection import train_test_split

# === 클래스 매핑 정의 ===
CLASS_NAMES = ['missing_hole', 'mouse_bite', 'open_circuit',
               'short', 'spur', 'spurious_copper']
CLASS_TO_ID = {name: idx for idx, name in enumerate(CLASS_NAMES)}
print("클래스 매핑:", CLASS_TO_ID)

def convert_voc_to_yolo(xml_path, img_width, img_height):
    """
    Pascal VOC XML → YOLO TXT 형식 변환

    VOC: (xmin, ymin, xmax, ymax) 절대 좌표
    YOLO: (class_id, x_center, y_center, width, height) 정규화 좌표
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    yolo_lines = []
    for obj in root.findall("object"):
        cls_name = obj.find("name").text
        if cls_name not in CLASS_TO_ID:
            continue

        cls_id = CLASS_TO_ID[cls_name]
        bbox = obj.find("bndbox")
        xmin = int(bbox.find("xmin").text)
        ymin = int(bbox.find("ymin").text)
        xmax = int(bbox.find("xmax").text)
        ymax = int(bbox.find("ymax").text)

        # YOLO 정규화 좌표 계산
        x_center = ((xmin + xmax) / 2) / img_width
        y_center = ((ymin + ymax) / 2) / img_height
        width = (xmax - xmin) / img_width
        height = (ymax - ymin) / img_height

        # 범위 클리핑 (0~1)
        x_center = max(0, min(1, x_center))
        y_center = max(0, min(1, y_center))
        width = max(0, min(1, width))
        height = max(0, min(1, height))

        yolo_lines.append(f"{cls_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

    return yolo_lines


# === 전체 데이터 변환 + Train/Val/Test 분리 ===
def prepare_yolo_dataset(raw_dir, output_dir, train_ratio=0.7, val_ratio=0.2):
    """
    XML 어노테이션을 YOLO 형식으로 변환하고
    Train/Val/Test로 분리하여 YOLO 표준 디렉토리 구조 생성
    """

    output_dir = Path(output_dir)

    # YOLO 디렉토리 구조 생성
    for split in ['train', 'val', 'test']:
        (output_dir / split / 'images').mkdir(parents=True, exist_ok=True)
        (output_dir / split / 'labels').mkdir(parents=True, exist_ok=True)

    # 모든 이미지-XML 쌍 수집
    all_pairs = []
    img_base = Path(raw_dir) / "images"
    ann_base = Path(raw_dir) / "Annotations"

    for class_dir in sorted(img_base.iterdir()):
        if not class_dir.is_dir():
            continue
        for img_path in class_dir.glob("*.jpg"):
            xml_name = img_path.stem + ".xml"
            xml_path = ann_base / class_dir.name / xml_name
            if xml_path.exists():
                all_pairs.append((img_path, xml_path))

    print(f"총 이미지-XML 쌍: {len(all_pairs)}개")

    # Train / Val / Test 분리
    train_pairs, temp_pairs = train_test_split(
        all_pairs, test_size=(1 - train_ratio), random_state=42
    )
    val_ratio_adjusted = val_ratio / (1 - train_ratio)
    val_pairs, test_pairs = train_test_split(
        temp_pairs, test_size=(1 - val_ratio_adjusted), random_state=42
    )

    print(f"Train: {len(train_pairs)} / Val: {len(val_pairs)} / Test: {len(test_pairs)}")

    # 변환 및 복사
    split_map = {'train': train_pairs, 'val': val_pairs, 'test': test_pairs}
    converted_count = 0

    for split_name, pairs in split_map.items():
        for img_path, xml_path in pairs:
            # 이미지 크기 읽기
            img = Image.open(img_path)
            img_w, img_h = img.size

            # XML → YOLO 변환
            yolo_lines = convert_voc_to_yolo(xml_path, img_w, img_h)
            if not yolo_lines:
                continue

            # 파일명 (중복 방지를 위해 클래스 접두어 추가)
            prefix = img_path.parent.name
            new_name = f"{prefix}_{img_path.stem}"

            # 이미지 복사
            dst_img = output_dir / split_name / 'images' / f"{new_name}.jpg"
            shutil.copy2(img_path, dst_img)

            # YOLO 라벨 저장
            dst_label = output_dir / split_name / 'labels' / f"{new_name}.txt"
            with open(dst_label, 'w') as f:
                f.write('\n'.join(yolo_lines))

            converted_count += 1

    print(f"\n변환 완료! 총 {converted_count}개 이미지 처리")

    # 검증: 각 split의 파일 수 확인
    for split in ['train', 'val', 'test']:
        n_imgs = len(list((output_dir / split / 'images').glob('*.jpg')))
        n_labs = len(list((output_dir / split / 'labels').glob('*.txt')))
        print(f"  {split}: {n_imgs} images, {n_labs} labels")

    return output_dir


# === 실행 ===
DATASET_DIR = prepare_yolo_dataset("data/raw", "data/pcb_yolo")
```

### 3.3 변환 결과 검증

```python
def verify_yolo_labels(dataset_dir, split='train', num_samples=3):
    """YOLO 라벨이 올바르게 변환되었는지 시각화로 검증"""

    img_dir = Path(dataset_dir) / split / 'images'
    lab_dir = Path(dataset_dir) / split / 'labels'

    img_files = sorted(img_dir.glob('*.jpg'))[:num_samples]

    fig, axes = plt.subplots(1, num_samples, figsize=(6 * num_samples, 6))
    if num_samples == 1:
        axes = [axes]

    colors = ['#e74c3c', '#f39c12', '#2ecc71', '#3498db', '#9b59b6', '#1abc9c']

    for idx, img_path in enumerate(img_files):
        img = cv2.imread(str(img_path))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = img.shape[:2]

        # YOLO 라벨 읽기
        label_path = lab_dir / f"{img_path.stem}.txt"
        if label_path.exists():
            with open(label_path) as f:
                for line in f.readlines():
                    parts = line.strip().split()
                    cls_id = int(parts[0])
                    xc, yc, bw, bh = [float(x) for x in parts[1:5]]

                    # YOLO 정규화 좌표 → 픽셀 좌표
                    x1 = int((xc - bw / 2) * w)
                    y1 = int((yc - bh / 2) * h)
                    x2 = int((xc + bw / 2) * w)
                    y2 = int((yc + bh / 2) * h)

                    color = tuple(int(c * 255) if isinstance(c, float)
                                  else int(c.lstrip('#'), 16) >> (16 - 8*i) & 0xFF
                                  for i, c in enumerate([colors[cls_id]] * 3))
                    cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    cv2.putText(img, CLASS_NAMES[cls_id], (x1, y1 - 5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

        axes[idx].imshow(img)
        axes[idx].set_title(img_path.name, fontsize=8)
        axes[idx].axis('off')

    plt.suptitle('YOLO 라벨 변환 검증', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig("results/03_label_verification.png", dpi=150, bbox_inches='tight')
    plt.show()

verify_yolo_labels("data/pcb_yolo", split='train', num_samples=4)
```

---

## 4. YOLO 데이터셋 구성 (data.yaml)

### 4.1 data.yaml 생성

```python
import yaml

data_yaml = {
    'path': str(Path("data/pcb_yolo").resolve()),  # 데이터셋 루트 (절대 경로)
    'train': 'train/images',
    'val': 'val/images',
    'test': 'test/images',
    'nc': 6,                            # 클래스 수
    'names': CLASS_NAMES,               # 클래스 이름 리스트
}

yaml_path = Path("data/pcb_yolo/data.yaml")
with open(yaml_path, 'w') as f:
    yaml.dump(data_yaml, f, default_flow_style=False, allow_unicode=True)

print(f"data.yaml 생성 완료: {yaml_path}")
print(f"\n내용:")
with open(yaml_path) as f:
    print(f.read())
```

### 4.2 최종 디렉토리 구조 확인

```
data/pcb_yolo/
├── data.yaml              ← YOLO 데이터셋 설정 파일
├── train/
│   ├── images/            ← 학습 이미지 (~485장)
│   └── labels/            ← YOLO 형식 라벨 (.txt)
├── val/
│   ├── images/            ← 검증 이미지 (~139장)
│   └── labels/
└── test/
    ├── images/            ← 테스트 이미지 (~69장)
    └── labels/
```

---

## 5. YOLOv8 모델 학습

### 5.1 Ultralytics YOLOv8 모델 크기 비교

```
┌────────────────────────────────────────────────────────┐
│  YOLOv8 모델 라인업                                      │
├──────────┬──────────┬─────────────┬────────────────────┤
│ 모델      │ 파라미터  │ 입력 크기    │ 용도               │
├──────────┼──────────┼─────────────┼────────────────────┤
│ yolov8n  │ 3.2M     │ 640×640     │ 초경량 (모바일/엣지) │
│ yolov8s  │ 11.2M    │ 640×640     │ 경량 (빠른 학습)    │
│ yolov8m  │ 25.9M    │ 640×640     │ 중간 (균형)         │
│ yolov8l  │ 43.7M    │ 640×640     │ 대형 (높은 정확도)   │
│ yolov8x  │ 68.2M    │ 640×640     │ 초대형 (최고 성능)   │
└──────────┴──────────┴─────────────┴────────────────────┘

→ 미니프로젝트 추천: yolov8s (빠르면서 적정 성능)
→ 비교 실험: yolov8n vs yolov8s vs yolov8m
```

### 5.2 학습 실행 (핵심 코드)

```python
from ultralytics import YOLO

# ========================================
# YOLOv8s 모델 학습 (COCO 사전학습 가중치)
# ========================================

model = YOLO("yolov8s.pt")  # COCO 사전학습 가중치 자동 다운로드

results = model.train(
    data="data/pcb_yolo/data.yaml",   # 데이터셋 설정
    epochs=50,                         # 학습 에폭
    imgsz=640,                         # 입력 이미지 크기
    batch=16,                          # 배치 크기 (GPU 메모리에 따라 조절)
    name="pcb_yolov8s",               # 실험 이름
    patience=10,                       # Early Stopping (10 에폭 개선 없으면 중단)
    save=True,                         # 가중치 저장
    save_period=10,                    # 10 에폭마다 체크포인트
    pretrained=True,                   # COCO 사전학습 사용
    optimizer="Adam",                  # 옵티마이저
    lr0=0.001,                         # 초기 학습률
    lrf=0.01,                          # 최종 학습률 비율 (cosine decay)
    augment=True,                      # 데이터 증강 활성화
    verbose=True,                      # 상세 로그 출력
)

# ========================================
# 학습 결과 경로 확인
# ========================================
print(f"\n학습 결과 저장 위치: runs/detect/pcb_yolov8s/")
print(f"최고 가중치: runs/detect/pcb_yolov8s/weights/best.pt")
print(f"마지막 가중치: runs/detect/pcb_yolov8s/weights/last.pt")
```

### 5.3 Ultralytics가 자동 생성하는 학습 결과물

```
runs/detect/pcb_yolov8s/
├── weights/
│   ├── best.pt           ← 최고 성능 가중치 (이것을 사용!)
│   └── last.pt           ← 마지막 에폭 가중치
├── results.csv           ← 에폭별 성능 지표 로그
├── results.png           ← 학습 곡선 그래프 (자동 생성)
├── confusion_matrix.png  ← 혼동행렬 (자동 생성)
├── F1_curve.png          ← F1 곡선 (자동 생성)
├── PR_curve.png          ← Precision-Recall 곡선 (자동 생성)
├── P_curve.png           ← Precision 곡선
├── R_curve.png           ← Recall 곡선
├── val_batch0_pred.jpg   ← 검증 배치 예측 결과 시각화
├── val_batch0_labels.jpg ← 검증 배치 정답 시각화
└── args.yaml             ← 학습 하이퍼파라미터 기록
```

> **핵심 장점**: Ultralytics는 학습 곡선, 혼동행렬, PR 곡선 등을 **자동으로 생성**합니다. 별도 시각화 코드가 필요 없습니다.

---

## 6. 성능 평가 및 분석

### 6.1 Validation 세트 평가

```python
# === Best 모델 로드 및 평가 ===
best_model = YOLO("runs/detect/pcb_yolov8s/weights/best.pt")

# Validation 평가
val_results = best_model.val(
    data="data/pcb_yolo/data.yaml",
    split='val',
    verbose=True
)

# === 주요 성능 지표 출력 ===
print(f"\n{'='*60}")
print(f"{'YOLOv8s PCB 결함 탐지 — Validation 성능':^60}")
print(f"{'='*60}")
print(f"  mAP@0.5:      {val_results.box.map50:.4f}")
print(f"  mAP@0.5:0.95: {val_results.box.map:.4f}")
print(f"  Precision:     {val_results.box.mp:.4f}")
print(f"  Recall:        {val_results.box.mr:.4f}")

# 클래스별 AP
print(f"\n  클래스별 AP@0.5:")
for i, cls_name in enumerate(CLASS_NAMES):
    ap = val_results.box.ap50[i] if i < len(val_results.box.ap50) else 0
    print(f"    {cls_name:<20s}: {ap:.4f}")
```

### 6.2 Test 세트 평가

```python
# Test 세트 평가
test_results = best_model.val(
    data="data/pcb_yolo/data.yaml",
    split='test',
    verbose=True
)

print(f"\n{'='*60}")
print(f"{'YOLOv8s PCB 결함 탐지 — Test 성능':^60}")
print(f"{'='*60}")
print(f"  mAP@0.5:      {test_results.box.map50:.4f}")
print(f"  mAP@0.5:0.95: {test_results.box.map:.4f}")
print(f"  Precision:     {test_results.box.mp:.4f}")
print(f"  Recall:        {test_results.box.mr:.4f}")
```

### 6.3 자동 생성된 그래프 복사

```python
import shutil

# Ultralytics가 자동 생성한 그래프를 results/ 폴더로 복사
train_dir = Path("runs/detect/pcb_yolov8s")
auto_files = {
    "results.png": "04_training_curves.png",
    "confusion_matrix.png": "05_confusion_matrix.png",
    "F1_curve.png": "06_f1_curve.png",
    "PR_curve.png": "07_pr_curve.png",
    "val_batch0_pred.jpg": "08_val_predictions.jpg",
}

for src_name, dst_name in auto_files.items():
    src = train_dir / src_name
    if src.exists():
        shutil.copy2(src, f"results/{dst_name}")
        print(f"복사 완료: {dst_name}")
    else:
        print(f"파일 없음: {src_name}")
```

---

## 7. 추론 및 탐지 결과 시각화

### 7.1 테스트 이미지 추론

```python
# === 테스트 이미지에서 추론 ===
test_img_dir = Path("data/pcb_yolo/test/images")
test_images = sorted(test_img_dir.glob("*.jpg"))[:12]

# 추론 실행
predictions = best_model.predict(
    source=[str(p) for p in test_images],
    conf=0.25,        # 신뢰도 임계값
    iou=0.45,         # NMS IoU 임계값
    save=True,        # 결과 이미지 저장
    save_txt=True,    # 예측 라벨 저장
    name="pcb_test_predictions"
)
```

### 7.2 커스텀 탐지 결과 시각화

```python
def visualize_detections(model, image_paths, save_path="results/09_detection_results.png"):
    """탐지 결과를 커스텀 그리드로 시각화"""

    num = min(len(image_paths), 8)
    cols = 4
    rows = (num + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 5 * rows))
    axes = axes.flatten() if rows > 1 else [axes] if rows == 1 and cols == 1 else axes.flatten()

    color_map = {
        'missing_hole': (255, 50, 50), 'mouse_bite': (255, 165, 0),
        'open_circuit': (50, 200, 50), 'short': (50, 100, 255),
        'spur': (160, 32, 240), 'spurious_copper': (0, 200, 200)
    }

    for idx in range(len(axes)):
        if idx < num:
            img_path = image_paths[idx]
            results = model.predict(str(img_path), conf=0.25, verbose=False)
            result = results[0]

            # 이미지 로드
            img = cv2.imread(str(img_path))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # 탐지 결과 그리기
            detections = []
            if result.boxes is not None and len(result.boxes) > 0:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    conf = box.conf[0].cpu().item()
                    cls_id = int(box.cls[0].cpu().item())
                    cls_name = CLASS_NAMES[cls_id]
                    color = color_map.get(cls_name, (255, 255, 255))

                    cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                    label = f"{cls_name} {conf:.2f}"
                    cv2.putText(img, label, (x1, y1 - 8),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
                    detections.append(f"{cls_name}({conf:.0%})")

            axes[idx].imshow(img)
            det_text = ', '.join(detections[:3]) if detections else 'No Detection'
            axes[idx].set_title(det_text, fontsize=7, fontweight='bold')
            axes[idx].axis('off')
        else:
            axes[idx].axis('off')

    plt.suptitle('YOLOv8 PCB 결함 탐지 결과', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

visualize_detections(best_model, test_images)
```

### 7.3 추론 속도 측정

```python
import time

def measure_inference_speed(model, test_images, num_runs=3):
    """추론 속도 측정 (FPS)"""

    # 워밍업
    model.predict(str(test_images[0]), verbose=False)

    total_time = 0
    total_images = 0

    for run in range(num_runs):
        start = time.time()
        for img_path in test_images:
            model.predict(str(img_path), verbose=False)
        elapsed = time.time() - start
        total_time += elapsed
        total_images += len(test_images)

    avg_time = total_time / total_images
    fps = 1.0 / avg_time

    print(f"\n=== 추론 속도 ===")
    print(f"  평균 추론 시간: {avg_time*1000:.1f} ms/image")
    print(f"  FPS: {fps:.1f}")
    print(f"  실시간 처리 {'가능 ✓' if fps >= 30 else '불가 ✗'} (기준: 30 FPS)")

    return avg_time, fps

avg_time, fps = measure_inference_speed(best_model, test_images)
```

---

## 8. 모델 크기별 비교 실험

### 8.1 3개 모델 순차 학습 및 비교

```python
MODEL_VARIANTS = {
    'yolov8n': 'yolov8n.pt',   # Nano (3.2M params)
    'yolov8s': 'yolov8s.pt',   # Small (11.2M params)
    'yolov8m': 'yolov8m.pt',   # Medium (25.9M params)
}

comparison = {}

for variant_name, weight_file in MODEL_VARIANTS.items():
    print(f"\n{'#'*60}")
    print(f"# 학습 시작: {variant_name}")
    print(f"{'#'*60}")

    model = YOLO(weight_file)
    model.train(
        data="data/pcb_yolo/data.yaml",
        epochs=30,              # 비교 실험은 30 에폭으로 축소
        imgsz=640,
        batch=16,
        name=f"pcb_{variant_name}",
        patience=10,
        verbose=False,
    )

    # 평가
    best = YOLO(f"runs/detect/pcb_{variant_name}/weights/best.pt")
    val_res = best.val(data="data/pcb_yolo/data.yaml", split='val', verbose=False)

    # 추론 속도
    test_imgs = sorted(Path("data/pcb_yolo/test/images").glob("*.jpg"))[:20]
    _, speed_fps = measure_inference_speed(best, test_imgs)

    # 파라미터 수
    total_params = sum(p.numel() for p in best.model.parameters())

    comparison[variant_name] = {
        'mAP50': val_res.box.map50,
        'mAP50_95': val_res.box.map,
        'precision': val_res.box.mp,
        'recall': val_res.box.mr,
        'fps': speed_fps,
        'params': total_params,
    }

    print(f"  mAP@0.5: {val_res.box.map50:.4f} | FPS: {speed_fps:.1f}")
```

### 8.2 비교 결과 시각화

```python
def plot_model_comparison(comparison, save_path="results/10_model_comparison.png"):
    """3개 YOLOv8 모델 성능 비교"""

    models = list(comparison.keys())
    metrics = {
        'mAP@0.5': [comparison[m]['mAP50'] for m in models],
        'mAP@0.5:0.95': [comparison[m]['mAP50_95'] for m in models],
        'Precision': [comparison[m]['precision'] for m in models],
        'Recall': [comparison[m]['recall'] for m in models],
    }

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    colors = ['#3498db', '#2ecc71', '#e74c3c']

    # 1) 정확도 비교
    x = np.arange(len(models))
    w = 0.2
    for i, (metric_name, values) in enumerate(metrics.items()):
        if i < 4:
            axes[0].bar(x + i * w, values, w, label=metric_name, alpha=0.85)
    axes[0].set_xticks(x + w * 1.5)
    axes[0].set_xticklabels(models)
    axes[0].set_title('정확도 비교', fontweight='bold')
    axes[0].set_ylim(0, 1)
    axes[0].legend(fontsize=7)

    # 2) 속도 비교
    fps_values = [comparison[m]['fps'] for m in models]
    axes[1].bar(models, fps_values, color=colors)
    axes[1].set_title('추론 속도 (FPS)', fontweight='bold')
    axes[1].axhline(y=30, color='red', linestyle='--', alpha=0.5, label='실시간 기준 (30 FPS)')
    axes[1].legend()
    for i, v in enumerate(fps_values):
        axes[1].text(i, v + 1, f'{v:.0f}', ha='center', fontweight='bold')

    # 3) 정확도 vs 속도 트레이드오프
    for i, m in enumerate(models):
        axes[2].scatter(comparison[m]['fps'], comparison[m]['mAP50'],
                       s=comparison[m]['params'] / 50000,  # 파라미터 수 비례 크기
                       c=colors[i], alpha=0.7, edgecolors='black')
        axes[2].annotate(m, (comparison[m]['fps'], comparison[m]['mAP50']),
                        textcoords="offset points", xytext=(10, 5), fontsize=9)
    axes[2].set_xlabel('FPS (속도)')
    axes[2].set_ylabel('mAP@0.5 (정확도)')
    axes[2].set_title('정확도 vs 속도 트레이드오프', fontweight='bold')
    axes[2].grid(True, alpha=0.3)

    plt.suptitle('YOLOv8 모델 크기별 성능 비교', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

plot_model_comparison(comparison)
```

### 8.3 비교 테이블 출력

```python
print(f"\n{'='*80}")
print(f"{'YOLOv8 모델 크기별 최종 비교':^80}")
print(f"{'='*80}")
print(f"{'모델':<12} {'파라미터':>12} {'mAP@0.5':>10} {'mAP@.5:.95':>12} {'Precision':>10} {'Recall':>10} {'FPS':>8}")
print(f"{'-'*80}")

for m in comparison:
    c = comparison[m]
    print(f"{m:<12} {c['params']/1e6:>10.1f}M {c['mAP50']:>10.4f} "
          f"{c['mAP50_95']:>12.4f} {c['precision']:>10.4f} {c['recall']:>10.4f} {c['fps']:>8.1f}")

best = max(comparison, key=lambda x: comparison[x]['mAP50'])
print(f"\n🏆 최고 mAP@0.5 모델: {best} ({comparison[best]['mAP50']:.4f})")
```

---

## 9. 결과 저장 및 정리

### 9.1 결과 JSON 저장

```python
import json

summary = {
    "project": "PCB 기판 결함 자동 탐지",
    "framework": "Ultralytics YOLOv8",
    "dataset": "PCB Defects (693 images, 6 classes)",
    "classes": CLASS_NAMES,
    "best_model": best,
    "model_comparison": {
        m: {k: round(float(v), 4) if isinstance(v, (float, np.floating)) else v
            for k, v in c.items() if k != 'params'}
        for m, c in comparison.items()
    }
}

with open("results/11_final_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
print("저장 완료: results/11_final_summary.json")
```

### 9.2 최종 출력 파일 목록

```
results/
├── 01_data_distribution.png       ← 클래스 분포 + 박스 크기 분포
├── 02_sample_images.png           ← 결함 유형별 샘플 이미지
├── 03_label_verification.png      ← YOLO 라벨 변환 검증
├── 04_training_curves.png         ← 학습 곡선 (Ultralytics 자동 생성)
├── 05_confusion_matrix.png        ← 혼동행렬 (자동 생성)
├── 06_f1_curve.png                ← F1 곡선 (자동 생성)
├── 07_pr_curve.png                ← PR 곡선 (자동 생성)
├── 08_val_predictions.jpg         ← 검증 예측 시각화 (자동 생성)
├── 09_detection_results.png       ← 커스텀 탐지 결과 그리드
├── 10_model_comparison.png        ← 3모델 성능/속도 비교
└── 11_final_summary.json          ← 성능 지표 JSON

models/ (또는 runs/detect/)
├── pcb_yolov8n/weights/best.pt
├── pcb_yolov8s/weights/best.pt
└── pcb_yolov8m/weights/best.pt
```

---

## 부록: Claude Code 실행 순서 요약

```
[Step 1] 환경 설정
  → ultralytics 설치, GPU 확인

[Step 2] 데이터 탐색
  → XML 파싱, 클래스 분포 분석, 샘플 시각화

[Step 3] 어노테이션 변환
  → XML → YOLO TXT 변환, Train/Val/Test 분리, 변환 검증

[Step 4] data.yaml 생성
  → YOLO 데이터셋 설정 파일

[Step 5] YOLOv8s 학습
  → model.train() 한 줄로 학습 실행 (50 에폭)

[Step 6] 성능 평가
  → model.val()로 mAP/Precision/Recall 확인

[Step 7] 추론 시각화
  → model.predict()로 탐지 결과 시각화 + FPS 측정

[Step 8] 모델 비교
  → yolov8n / yolov8s / yolov8m 3종 비교 (정확도 vs 속도)

[Step 9] 결과 저장
  → JSON, 자동 생성 그래프 복사
```

### 예상 소요 시간

| 단계                     | GPU (Colab T4) |    CPU Only     |
| ------------------------ | :------------: | :-------------: |
| 데이터 준비 + 변환       |      5분       |       5분       |
| YOLOv8s 학습 (50 에폭)   |    15~20분     |     2~3시간     |
| 3모델 비교 (30 에폭 × 3) |    30~40분     |     6~9시간     |
| 평가 + 시각화            |      5분       |      10분       |
| **총 소요 시간 (1모델)** | **약 25~30분** |  **약 3시간**   |
| **총 소요 시간 (3모델)** | **약 50~65분** | **약 7~10시간** |

### 목표 성능 기준

| 지표          | 최소 기준 | 우수 기준 |
| ------------- | :-------: | :-------: |
| mAP@0.5       |  ≥ 0.70   |  ≥ 0.85   |
| mAP@0.5:0.95  |  ≥ 0.45   |  ≥ 0.60   |
| Precision     |  ≥ 0.70   |  ≥ 0.85   |
| Recall        |  ≥ 0.65   |  ≥ 0.80   |
| FPS (yolov8s) |   ≥ 30    |   ≥ 60    |

### 소주제 A·B와의 핵심 차이점

| 비교 항목   |   A (분류)    | B (세그먼테이션) |         C (객체탐지)          |
| ----------- | :-----------: | :--------------: | :---------------------------: |
| 과제 유형   | 이미지 → 라벨 | 이미지 → 마스크  |     이미지 → 박스 + 라벨      |
| 출력 형태   |    (B, 2)     |   (B, 4, H, W)   |   N × (x,y,w,h, conf, cls)    |
| 프레임워크  | PyTorch 직접  |   PyTorch 직접   | **Ultralytics (고수준 API)**  |
| 손실 함수   | CrossEntropy  |    BCE + Dice    |    Box + Cls + DFL (자동)     |
| 평가 지표   | Accuracy, F1  |    Dice, IoU     |   **mAP@0.5, mAP@0.5:0.95**   |
| 데이터 포맷 |   폴더 라벨   |    RLE 마스크    | **YOLO TXT (x,y,w,h 정규화)** |
| 학습 루프   |   직접 작성   |    직접 작성     |    **model.train() 한 줄**    |
| 핵심 난이도 |   모델 비교   |  클래스 불균형   | **XML→YOLO 변환 + NMS 이해**  |
