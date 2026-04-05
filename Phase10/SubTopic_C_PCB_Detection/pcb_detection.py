#!/usr/bin/env python3
"""
소주제 C. PCB 기판 결함 자동 탐지
==================================
AI 기반 스마트 팩토리 품질관리 시스템 — YOLOv8 객체 탐지

파이프라인:
  1. 환경 설정
  2. 데이터 탐색 (EDA)
  3. XML → YOLO 형식 변환
  4. YOLOv8s 학습 (50 epochs)
  5. 평가 및 자동 생성 그래프 수집
  6. 탐지 결과 시각화
  7. 모델 크기별 비교 (n/s/m, 각 30 epochs)
  8. 최종 결과 저장

실행:
  python pcb_detection.py
"""

import os
import json
import random
import shutil
import time
import warnings
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import cv2
import yaml
from PIL import Image
from sklearn.model_selection import train_test_split
from ultralytics import YOLO

import torch

warnings.filterwarnings("ignore")
matplotlib.rc("font", family="AppleGothic")
matplotlib.rcParams["axes.unicode_minus"] = False

# ============================================================
# 설정
# ============================================================
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

MAIN_EPOCHS = 50
COMPARE_EPOCHS = 30

CLASS_NAMES = ["missing_hole", "mouse_bite", "open_circuit", "short", "spur", "spurious_copper"]
CLASS_TO_ID = {name: idx for idx, name in enumerate(CLASS_NAMES)}
NUM_CLASSES = len(CLASS_NAMES)

CLASS_COLORS = {
    "missing_hole": (255, 50, 50), "mouse_bite": (255, 165, 0),
    "open_circuit": (50, 200, 50), "short": (50, 100, 255),
    "spur": (160, 32, 240), "spurious_copper": (0, 200, 200),
}

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR.parent / "data" / "PCB_DATASET"
IMG_BASE = RAW_DIR / "images"
ANN_BASE = RAW_DIR / "Annotations"
YOLO_DIR = BASE_DIR / "data" / "pcb_yolo"
MODEL_DIR = BASE_DIR / "models"
RESULT_DIR = BASE_DIR / "results"


# ============================================================
# 1. 환경 설정
# ============================================================
def setup_environment():
    print(f"  PyTorch: {torch.__version__}")
    if torch.cuda.is_available():
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        print("  MPS 사용 가능")
    else:
        print("  CPU 사용")
    _ = YOLO("yolov8n.pt")
    print("  Ultralytics YOLOv8 OK")


# ============================================================
# 2. 데이터 탐색 (EDA)
# ============================================================
def explore_data():
    class_counts = {}
    bbox_sizes = []
    all_pairs = []

    for cls_dir in sorted(IMG_BASE.iterdir()):
        if not cls_dir.is_dir():
            continue
        cls_name = cls_dir.name
        imgs = list(cls_dir.glob("*.jpg"))
        class_counts[cls_name] = len(imgs)
        for img_path in imgs:
            xml_path = ANN_BASE / cls_name / (img_path.stem + ".xml")
            if xml_path.exists():
                all_pairs.append((img_path, xml_path))
                tree = ET.parse(xml_path)
                for obj in tree.findall(".//object"):
                    bb = obj.find("bndbox")
                    w = int(bb.find("xmax").text) - int(bb.find("xmin").text)
                    h = int(bb.find("ymax").text) - int(bb.find("ymin").text)
                    bbox_sizes.append({"class": obj.find("name").text, "width": w, "height": h})

    print("  클래스별 이미지 수:")
    for cls, cnt in class_counts.items():
        print(f"    {cls:<20s}: {cnt}장")
    print(f"    합계: {sum(class_counts.values())}장, 바운딩 박스: {len(bbox_sizes)}개")

    # --- 분포 시각화 ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    names = list(class_counts.keys())
    counts = list(class_counts.values())
    bars = axes[0].bar(range(len(names)), counts, color=[plt.cm.Set2(i) for i in range(len(names))])
    axes[0].set_xticks(range(len(names)))
    axes[0].set_xticklabels(names, rotation=30, ha="right", fontsize=9)
    axes[0].set_ylabel("이미지 수")
    axes[0].set_title("결함 유형별 이미지 수")
    axes[0].bar_label(bars, padding=2)

    bw = [b["width"] for b in bbox_sizes]
    bh = [b["height"] for b in bbox_sizes]
    axes[1].scatter(bw, bh, alpha=0.3, s=10, c="#3498DB")
    axes[1].set_xlabel("BBox Width (px)")
    axes[1].set_ylabel("BBox Height (px)")
    axes[1].set_title(f"바운딩 박스 크기 분포 ({len(bbox_sizes)}개)")
    axes[1].grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(RESULT_DIR / "01_data_distribution.png", dpi=150, bbox_inches="tight")
    plt.close()

    # --- 샘플 이미지 ---
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    for idx, cls_name in enumerate(CLASS_NAMES):
        ax = axes[idx // 3, idx % 3]
        cls_dir = None
        for d in IMG_BASE.iterdir():
            if d.name.lower().replace(" ", "_") == cls_name or d.name.lower() == cls_name:
                cls_dir = d
                break
        if cls_dir is None:
            continue
        img_path = sorted(cls_dir.glob("*.jpg"))[0]
        xml_path = ANN_BASE / cls_dir.name / (img_path.stem + ".xml")
        img = cv2.imread(str(img_path))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        tree = ET.parse(xml_path)
        for obj in tree.findall(".//object"):
            bb = obj.find("bndbox")
            x1, y1 = int(bb.find("xmin").text), int(bb.find("ymin").text)
            x2, y2 = int(bb.find("xmax").text), int(bb.find("ymax").text)
            name = obj.find("name").text
            color = CLASS_COLORS.get(name, (255, 255, 255))
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
            cv2.putText(img, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        ax.imshow(img)
        ax.set_title(cls_name, fontsize=11, fontweight="bold")
        ax.axis("off")
    plt.suptitle("PCB 결함 유형별 샘플 (GT BBox)", fontsize=14, y=1.01)
    plt.tight_layout()
    plt.savefig(RESULT_DIR / "02_sample_images.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  저장: 01_data_distribution.png, 02_sample_images.png")
    return all_pairs


# ============================================================
# 3. XML → YOLO 변환
# ============================================================
def convert_voc_to_yolo(xml_path, img_w, img_h):
    tree = ET.parse(xml_path)
    lines = []
    for obj in tree.findall(".//object"):
        cls_name = obj.find("name").text
        if cls_name not in CLASS_TO_ID:
            continue
        cls_id = CLASS_TO_ID[cls_name]
        bb = obj.find("bndbox")
        xmin, ymin = int(bb.find("xmin").text), int(bb.find("ymin").text)
        xmax, ymax = int(bb.find("xmax").text), int(bb.find("ymax").text)
        x_center = max(0, min(1, ((xmin + xmax) / 2) / img_w))
        y_center = max(0, min(1, ((ymin + ymax) / 2) / img_h))
        width = max(0, min(1, (xmax - xmin) / img_w))
        height = max(0, min(1, (ymax - ymin) / img_h))
        lines.append(f"{cls_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")
    return lines


def prepare_yolo_dataset(pairs, output_dir, train_ratio=0.7, val_ratio=0.2):
    output_dir = Path(output_dir)
    for split in ["train", "val", "test"]:
        (output_dir / split / "images").mkdir(parents=True, exist_ok=True)
        (output_dir / split / "labels").mkdir(parents=True, exist_ok=True)

    train_pairs, temp = train_test_split(pairs, test_size=1 - train_ratio, random_state=SEED)
    val_adj = val_ratio / (1 - train_ratio)
    val_pairs, test_pairs = train_test_split(temp, test_size=1 - val_adj, random_state=SEED)

    split_map = {"train": train_pairs, "val": val_pairs, "test": test_pairs}
    converted = 0

    for split_name, split_pairs in split_map.items():
        for img_path, xml_path in split_pairs:
            img = Image.open(img_path)
            img_w, img_h = img.size
            yolo_lines = convert_voc_to_yolo(xml_path, img_w, img_h)
            if not yolo_lines:
                continue
            prefix = img_path.parent.name
            new_name = f"{prefix}_{img_path.stem}"
            shutil.copy2(img_path, output_dir / split_name / "images" / f"{new_name}.jpg")
            with open(output_dir / split_name / "labels" / f"{new_name}.txt", "w") as f:
                f.write("\n".join(yolo_lines))
            converted += 1

    data_yaml = {
        "path": str(output_dir.resolve()),
        "train": "train/images", "val": "val/images", "test": "test/images",
        "nc": NUM_CLASSES, "names": CLASS_NAMES,
    }
    with open(output_dir / "data.yaml", "w") as f:
        yaml.dump(data_yaml, f, default_flow_style=False, allow_unicode=True)

    print(f"  YOLO 데이터셋 생성: {converted}장")
    for s, p in split_map.items():
        print(f"    {s}: {len(p)}장")
    return split_map


def verify_labels():
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    train_imgs = sorted((YOLO_DIR / "train" / "images").glob("*.jpg"))[:6]
    for idx, img_path in enumerate(train_imgs):
        ax = axes[idx // 3, idx % 3]
        img = cv2.imread(str(img_path))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = img.shape[:2]
        label_path = YOLO_DIR / "train" / "labels" / (img_path.stem + ".txt")
        if label_path.exists():
            with open(label_path) as f:
                for line in f:
                    parts = line.strip().split()
                    cls_id = int(parts[0])
                    xc, yc, bw, bh = [float(v) for v in parts[1:]]
                    x1 = int((xc - bw / 2) * w)
                    y1 = int((yc - bh / 2) * h)
                    x2 = int((xc + bw / 2) * w)
                    y2 = int((yc + bh / 2) * h)
                    color = list(CLASS_COLORS.values())[cls_id]
                    cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
                    cv2.putText(img, CLASS_NAMES[cls_id], (x1, y1 - 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        ax.imshow(img)
        ax.set_title(img_path.stem[:25], fontsize=8)
        ax.axis("off")
    plt.suptitle("YOLO 라벨 변환 검증", fontsize=14, y=1.01)
    plt.tight_layout()
    plt.savefig(RESULT_DIR / "03_label_verification.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  저장: 03_label_verification.png")


# ============================================================
# 4-5. 학습 및 평가
# ============================================================
def train_main_model():
    yaml_path = str((YOLO_DIR / "data.yaml").resolve())
    project_dir = str((BASE_DIR / "runs" / "detect").resolve())

    model = YOLO("yolov8s.pt")
    model.train(
        data=yaml_path, epochs=MAIN_EPOCHS, imgsz=640, batch=16,
        project=project_dir, name="pcb_yolov8s", patience=10,
        optimizer="Adam", lr0=0.001, lrf=0.01, augment=True,
        pretrained=True, verbose=True, seed=SEED,
    )

    # 결과 디렉토리 찾기
    detect_dir = Path(project_dir)
    run_dir = sorted(detect_dir.glob("pcb_yolov8s*"))[-1]

    # 자동 생성 그래프 복사
    auto_files = {
        "results.png": "04_training_curves.png",
        "confusion_matrix.png": "05_confusion_matrix.png",
        "F1_curve.png": "06_f1_curve.png",
        "PR_curve.png": "07_pr_curve.png",
    }
    for src_name, dst_name in auto_files.items():
        src = run_dir / src_name
        if src.exists():
            shutil.copy2(src, RESULT_DIR / dst_name)

    # Test 평가
    best_pt = run_dir / "weights" / "best.pt"
    best_model = YOLO(str(best_pt))
    test_results = best_model.val(
        data=str((YOLO_DIR / "data.yaml").resolve()), split="test", verbose=True,
    )

    print(f"\n  === Test 성능 ===")
    print(f"  mAP@0.5:      {test_results.box.map50:.4f}")
    print(f"  mAP@0.5:0.95: {test_results.box.map:.4f}")
    print(f"  Precision:     {test_results.box.mp:.4f}")
    print(f"  Recall:        {test_results.box.mr:.4f}")

    shutil.copy2(best_pt, MODEL_DIR / "best_yolov8s.pt")
    return best_model, test_results


# ============================================================
# 6. 탐지 결과 시각화
# ============================================================
def visualize_detections(best_model):
    test_images = sorted((YOLO_DIR / "test" / "images").glob("*.jpg"))[:8]
    fig, axes = plt.subplots(2, 4, figsize=(20, 10))
    axes = axes.flatten()

    for idx, img_path in enumerate(test_images):
        preds = best_model.predict(str(img_path), conf=0.25, iou=0.45, verbose=False)
        result = preds[0]
        img = cv2.imread(str(img_path))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        det_texts = []
        if result.boxes is not None and len(result.boxes) > 0:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                conf = box.conf[0].cpu().item()
                cls_id = int(box.cls[0].cpu().item())
                cls_name = CLASS_NAMES[cls_id]
                color = CLASS_COLORS.get(cls_name, (255, 255, 255))
                cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                cv2.putText(img, f"{cls_name} {conf:.2f}", (x1, y1 - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
                det_texts.append(f"{cls_name}({conf:.0%})")
        axes[idx].imshow(img)
        axes[idx].set_title(", ".join(det_texts[:3]) if det_texts else "No Detection",
                            fontsize=7, fontweight="bold")
        axes[idx].axis("off")

    plt.suptitle("YOLOv8s PCB 결함 탐지 결과", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(RESULT_DIR / "08_detection_results.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  저장: 08_detection_results.png")


# ============================================================
# 7. 모델 크기별 비교
# ============================================================
def compare_models():
    yaml_path = str((YOLO_DIR / "data.yaml").resolve())
    variants = {"yolov8n": "yolov8n.pt", "yolov8s": "yolov8s.pt", "yolov8m": "yolov8m.pt"}
    comparison = {}

    project_dir = str((BASE_DIR / "runs" / "detect").resolve())

    for variant, weight in variants.items():
        print(f"\n  학습: {variant}")
        m = YOLO(weight)
        m.train(data=yaml_path, epochs=COMPARE_EPOCHS, imgsz=640, batch=16,
                project=project_dir, name=f"pcb_{variant}", patience=10,
                verbose=False, seed=SEED)

        detect_dir = Path(project_dir)
        best_path = sorted(detect_dir.glob(f"pcb_{variant}*"))[-1] / "weights" / "best.pt"
        best = YOLO(str(best_path))
        val_res = best.val(data=yaml_path, split="val", verbose=False)

        # FPS
        t_imgs = sorted((YOLO_DIR / "test" / "images").glob("*.jpg"))[:20]
        _ = best.predict(str(t_imgs[0]), verbose=False)
        start = time.time()
        for p in t_imgs:
            best.predict(str(p), verbose=False)
        fps = len(t_imgs) / (time.time() - start)

        total_params = sum(p.numel() for p in best.model.parameters())
        comparison[variant] = {
            "mAP50": float(val_res.box.map50), "mAP50_95": float(val_res.box.map),
            "precision": float(val_res.box.mp), "recall": float(val_res.box.mr),
            "fps": fps, "params": total_params,
        }
        print(f"    mAP@0.5: {val_res.box.map50:.4f} | FPS: {fps:.1f}")

    # --- 비교 시각화 ---
    models_list = list(comparison.keys())
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    colors = ["#3498DB", "#2ECC71", "#E74C3C"]

    x = np.arange(len(models_list))
    w = 0.2
    for i, (metric, label) in enumerate([("mAP50", "mAP@0.5"), ("mAP50_95", "mAP@.5:.95"),
                                          ("precision", "Precision"), ("recall", "Recall")]):
        vals = [comparison[m][metric] for m in models_list]
        axes[0].bar(x + i * w, vals, w, label=label, alpha=0.85)
    axes[0].set_xticks(x + w * 1.5)
    axes[0].set_xticklabels(models_list)
    axes[0].set_title("정확도 비교", fontweight="bold")
    axes[0].set_ylim(0, 1)
    axes[0].legend(fontsize=7)

    fps_vals = [comparison[m]["fps"] for m in models_list]
    bars = axes[1].bar(models_list, fps_vals, color=colors)
    axes[1].axhline(y=30, color="red", linestyle="--", alpha=0.5, label="30 FPS")
    axes[1].set_title("추론 속도 (FPS)", fontweight="bold")
    axes[1].legend()
    axes[1].bar_label(bars, fmt="%.0f", padding=2)

    for i, m in enumerate(models_list):
        c = comparison[m]
        axes[2].scatter(c["fps"], c["mAP50"], s=c["params"] / 50000,
                        c=colors[i], alpha=0.7, edgecolors="black")
        axes[2].annotate(m, (c["fps"], c["mAP50"]), textcoords="offset points",
                         xytext=(10, 5), fontsize=9)
    axes[2].set_xlabel("FPS")
    axes[2].set_ylabel("mAP@0.5")
    axes[2].set_title("정확도 vs 속도", fontweight="bold")
    axes[2].grid(True, alpha=0.3)

    plt.suptitle("YOLOv8 모델 크기별 비교", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(RESULT_DIR / "09_model_comparison.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  저장: 09_model_comparison.png")
    return comparison


# ============================================================
# 8. 최종 결과 저장
# ============================================================
def save_final_summary(all_pairs, split_map, test_results, comparison):
    best_variant = max(comparison, key=lambda m: comparison[m]["mAP50"])

    summary = {
        "project": "소주제 C — PCB 기판 결함 자동 탐지",
        "framework": "Ultralytics YOLOv8",
        "dataset": f"PCB Defects ({len(all_pairs)}장, {NUM_CLASSES}클래스)",
        "classes": CLASS_NAMES,
        "data_split": {s: len(p) for s, p in split_map.items()},
        "main_model": {
            "name": "yolov8s", "epochs": MAIN_EPOCHS,
            "test_mAP50": round(float(test_results.box.map50), 4),
            "test_mAP50_95": round(float(test_results.box.map), 4),
            "test_precision": round(float(test_results.box.mp), 4),
            "test_recall": round(float(test_results.box.mr), 4),
        },
        "model_comparison": {
            m: {k: round(float(v), 4) if isinstance(v, (float, np.floating)) else v
                for k, v in c.items()}
            for m, c in comparison.items()
        },
        "best_variant": best_variant, "seed": SEED,
    }

    with open(RESULT_DIR / "10_final_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n  {'=' * 78}")
    print("   소주제 C — PCB 기판 결함 자동 탐지 | 최종 결과")
    print(f"  {'=' * 78}")
    print(f'\n  {"Model":<12} {"Params":>10} {"mAP@0.5":>10} {"mAP@.5:.95":>12} '
          f'{"Precision":>10} {"Recall":>10} {"FPS":>8}')
    print("  " + "-" * 78)
    for m in comparison:
        c = comparison[m]
        marker = " ★" if m == best_variant else ""
        print(f'  {m:<12} {c["params"]/1e6:>8.1f}M {c["mAP50"]:>10.4f} '
              f'{c["mAP50_95"]:>12.4f} {c["precision"]:>10.4f} {c["recall"]:>10.4f} '
              f'{c["fps"]:>8.1f}{marker}')

    print(f"\n  ★ Best: {best_variant}")
    print(f"\n  저장된 파일:")
    for f in sorted(RESULT_DIR.glob("*")):
        print(f"    → results/{f.name}")
    for f in sorted(MODEL_DIR.glob("*.pt")):
        print(f"    → models/{f.name}")


# ============================================================
# main
# ============================================================
def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print(" 소주제 C. PCB 기판 결함 자동 탐지")
    print(" YOLOv8 (yolov8n / yolov8s / yolov8m) 비교 실험")
    print("=" * 65)

    print("\n[1/8] 환경 설정")
    setup_environment()

    print("\n[2/8] 데이터 탐색 (EDA)")
    all_pairs = explore_data()

    print("\n[3/8] XML → YOLO 변환")
    # 재실행 시 기존 데이터셋 정리 (중복 방지)
    if YOLO_DIR.exists():
        shutil.rmtree(YOLO_DIR)
        print("  기존 YOLO 데이터셋 삭제")
    split_map = prepare_yolo_dataset(all_pairs, YOLO_DIR)
    verify_labels()

    print("\n[4/8] YOLOv8s 학습")
    best_model, test_results = train_main_model()

    print("\n[5/8] 자동 생성 그래프 수집 완료")

    print("\n[6/8] 탐지 결과 시각화")
    visualize_detections(best_model)

    print("\n[7/8] 모델 크기별 비교")
    comparison = compare_models()

    print("\n[8/8] 최종 결과 저장")
    save_final_summary(all_pairs, split_map, test_results, comparison)

    print(f"\n{'=' * 65}")
    print(" 전체 파이프라인 완료!")
    print(f"{'=' * 65}")


if __name__ == "__main__":
    main()
