"""
정상(결함 없는) 금속 표면 패치 생성 모듈

NEU-DET 어노테이션(XML bbox)을 활용하여 결함 영역을 제외한
깨끗한 영역을 크롭하여 정상 데이터를 생성한다.

전략:
  1. XML에서 결함 바운딩 박스 파싱
  2. 200x200 이미지에서 결함 영역을 마스킹
  3. 결함이 없는 영역에서 패치 크롭 (최소 크기 조건 충족)
  4. 크롭된 패치를 200x200으로 리사이즈
  5. 품질 필터링 (표준편차 기반: 너무 균일한 패치 제거)
"""

import os
import cv2
import numpy as np
import xml.etree.ElementTree as ET
from typing import List, Tuple, Optional
import glob


def parse_annotation(xml_path: str) -> Tuple[str, List[dict]]:
    """XML 어노테이션 파싱 → (파일명, [bbox 리스트])"""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    filename = root.find("filename").text

    bboxes = []
    for obj in root.findall("object"):
        bb = obj.find("bndbox")
        bboxes.append({
            "class": obj.find("name").text,
            "xmin": int(bb.find("xmin").text),
            "ymin": int(bb.find("ymin").text),
            "xmax": int(bb.find("xmax").text),
            "ymax": int(bb.find("ymax").text),
        })
    return filename, bboxes


def create_defect_mask(img_shape: Tuple[int, int], bboxes: List[dict],
                       margin: int = 10) -> np.ndarray:
    """결함 바운딩 박스를 마스크로 변환 (1=결함영역, 0=정상영역)"""
    h, w = img_shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    for bb in bboxes:
        x1 = max(0, bb["xmin"] - margin)
        y1 = max(0, bb["ymin"] - margin)
        x2 = min(w, bb["xmax"] + margin)
        y2 = min(h, bb["ymax"] + margin)
        mask[y1:y2, x1:x2] = 1
    return mask


def extract_clean_patches(image: np.ndarray, defect_mask: np.ndarray,
                          patch_size: int = 64, min_clean_ratio: float = 1.0,
                          stride: int = 32) -> List[np.ndarray]:
    """결함 마스크에서 깨끗한 패치를 슬라이딩 윈도우로 추출"""
    h, w = image.shape[:2]
    patches = []

    for y in range(0, h - patch_size + 1, stride):
        for x in range(0, w - patch_size + 1, stride):
            mask_patch = defect_mask[y:y+patch_size, x:x+patch_size]
            clean_ratio = 1.0 - (mask_patch.sum() / mask_patch.size)

            if clean_ratio >= min_clean_ratio:
                patch = image[y:y+patch_size, x:x+patch_size]
                # 품질 필터: 표준편차가 너무 낮으면 (균일 배경) 제외
                if patch.std() > 5.0:
                    patches.append(patch)

    return patches


def generate_normal_patches(data_dir: str, output_dir: str,
                            patch_size: int = 64, stride: int = 32,
                            target_size: int = 200, margin: int = 15,
                            min_std: float = 8.0,
                            max_patches_per_image: int = 3) -> dict:
    """
    NEU-DET 전체 이미지에서 정상 패치를 생성하여 저장

    Args:
        data_dir: NEU-DET 루트 경로
        output_dir: 정상 패치 저장 경로
        patch_size: 크롭 패치 크기
        stride: 슬라이딩 윈도우 간격
        target_size: 최종 리사이즈 크기
        margin: 결함 bbox 주변 마진 (픽셀)
        min_std: 최소 표준편차 (품질 필터)
        max_patches_per_image: 이미지당 최대 패치 수

    Returns:
        통계 딕셔너리
    """
    os.makedirs(output_dir, exist_ok=True)

    stats = {
        "total_images": 0,
        "images_with_clean": 0,
        "total_patches": 0,
        "per_class": {},
    }

    for split in ["train", "validation"]:
        ann_dir = os.path.join(data_dir, split, "annotations")
        img_base = os.path.join(data_dir, split, "images")

        if not os.path.isdir(ann_dir):
            continue

        xml_files = sorted(glob.glob(os.path.join(ann_dir, "*.xml")))

        for xml_path in xml_files:
            filename, bboxes = parse_annotation(xml_path)
            stats["total_images"] += 1

            # 클래스명 추출
            cls_name = bboxes[0]["class"] if bboxes else "unknown"
            if cls_name not in stats["per_class"]:
                stats["per_class"][cls_name] = 0

            # 이미지 경로 찾기
            img_path = None
            for cls_dir in os.listdir(img_base):
                candidate = os.path.join(img_base, cls_dir, filename)
                if os.path.exists(candidate):
                    img_path = candidate
                    break

            if img_path is None:
                # 확장자 변경 시도
                base = os.path.splitext(filename)[0]
                for ext in [".jpg", ".jpeg", ".bmp", ".png"]:
                    for cls_dir in os.listdir(img_base):
                        candidate = os.path.join(img_base, cls_dir, base + ext)
                        if os.path.exists(candidate):
                            img_path = candidate
                            break
                    if img_path:
                        break

            if img_path is None:
                continue

            image = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if image is None:
                continue

            # 결함 마스크 생성
            defect_mask = create_defect_mask(image.shape, bboxes, margin=margin)

            # 깨끗한 패치 추출
            patches = extract_clean_patches(
                image, defect_mask,
                patch_size=patch_size,
                min_clean_ratio=1.0,
                stride=stride,
            )

            if not patches:
                continue

            stats["images_with_clean"] += 1

            # 이미지당 최대 패치 수 제한 (다양성 확보)
            if len(patches) > max_patches_per_image:
                indices = np.random.choice(len(patches), max_patches_per_image, replace=False)
                patches = [patches[i] for i in indices]

            for i, patch in enumerate(patches):
                # 품질 필터
                if patch.std() < min_std:
                    continue

                # 200x200으로 리사이즈
                resized = cv2.resize(patch, (target_size, target_size),
                                     interpolation=cv2.INTER_CUBIC)

                # 저장
                base_name = os.path.splitext(os.path.basename(filename))[0]
                out_name = f"normal_{base_name}_p{i}.jpg"
                cv2.imwrite(os.path.join(output_dir, out_name), resized)

                stats["total_patches"] += 1
                stats["per_class"][cls_name] += 1

    return stats


def generate_synthetic_normals(data_dir: str, output_dir: str,
                               num_images: int = 100,
                               target_size: int = 200) -> int:
    """
    NEU 이미지의 텍스처 통계를 기반으로 합성 정상 이미지 생성

    실제 이미지의 주파수 스펙트럼을 분석하여
    비슷한 질감의 합성 이미지를 만든다.
    """
    os.makedirs(output_dir, exist_ok=True)

    # 모든 이미지에서 통계 수집
    all_means, all_stds = [], []
    img_dir = os.path.join(data_dir, "train", "images")

    sample_images = []
    for cls_dir in os.listdir(img_dir):
        cls_path = os.path.join(img_dir, cls_dir)
        if not os.path.isdir(cls_path):
            continue
        files = sorted(os.listdir(cls_path))[:10]
        for f in files:
            img = cv2.imread(os.path.join(cls_path, f), cv2.IMREAD_GRAYSCALE)
            if img is not None:
                all_means.append(img.mean())
                all_stds.append(img.std())
                sample_images.append(img)

    global_mean = np.mean(all_means)
    global_std = np.mean(all_stds)

    count = 0
    for i in range(num_images):
        # 랜덤 텍스처 생성 (주파수 도메인)
        base = np.random.randn(target_size, target_size).astype(np.float32)

        # 저주파 필터로 금속 질감 시뮬레이션
        ksize = np.random.choice([5, 7, 9, 11])
        blurred = cv2.GaussianBlur(base, (ksize, ksize), 0)

        # 실제 이미지와 비슷한 밝기/대비로 조정
        blurred = (blurred - blurred.mean()) / (blurred.std() + 1e-8)
        blurred = blurred * global_std + global_mean
        blurred = np.clip(blurred, 0, 255).astype(np.uint8)

        # 약간의 그래디언트 추가 (조명 불균일 시뮬레이션)
        if np.random.random() > 0.5:
            grad = np.linspace(0, np.random.uniform(-10, 10), target_size)
            grad = np.tile(grad, (target_size, 1)).astype(np.float32)
            if np.random.random() > 0.5:
                grad = grad.T
            blurred = np.clip(blurred.astype(np.float32) + grad, 0, 255).astype(np.uint8)

        cv2.imwrite(os.path.join(output_dir, f"synthetic_normal_{i:04d}.jpg"), blurred)
        count += 1

    return count


class NormalDataManager:
    """정상 데이터 통합 관리 클래스"""

    def __init__(self, data_dir: str, normal_dir: str = None):
        self.data_dir = data_dir
        self.normal_dir = normal_dir or os.path.join(
            os.path.dirname(data_dir), "normal_patches"
        )

    def prepare(self, force: bool = False) -> dict:
        """정상 데이터 준비 (크롭 + 합성)"""
        crop_dir = os.path.join(self.normal_dir, "cropped")
        synth_dir = os.path.join(self.normal_dir, "synthetic")

        if not force and os.path.isdir(crop_dir) and len(os.listdir(crop_dir)) > 50:
            n_crop = len([f for f in os.listdir(crop_dir) if f.endswith(".jpg")])
            n_synth = len([f for f in os.listdir(synth_dir) if f.endswith(".jpg")]) if os.path.isdir(synth_dir) else 0
            return {"cropped": n_crop, "synthetic": n_synth, "total": n_crop + n_synth, "cached": True}

        print("정상 패치 크롭 중...")
        crop_stats = generate_normal_patches(
            self.data_dir, crop_dir,
            patch_size=64, stride=32,
            target_size=200, margin=15,
            min_std=8.0, max_patches_per_image=3,
        )
        n_crop = crop_stats["total_patches"]
        print(f"  크롭 패치: {n_crop}장 (원본 {crop_stats['total_images']}장에서)")

        # 크롭이 부족하면 합성 보충
        target_total = 300
        n_synth = 0
        if n_crop < target_total:
            n_need = target_total - n_crop
            print(f"합성 정상 이미지 {n_need}장 생성 중...")
            n_synth = generate_synthetic_normals(
                self.data_dir, synth_dir,
                num_images=n_need, target_size=200,
            )
            print(f"  합성: {n_synth}장")

        return {
            "cropped": n_crop,
            "synthetic": n_synth,
            "total": n_crop + n_synth,
            "crop_stats": crop_stats,
            "cached": False,
        }

    def load_normal_images(self, max_images: int = 300) -> List[np.ndarray]:
        """정상 이미지 로드"""
        images = []

        # 크롭된 패치 우선 로드
        crop_dir = os.path.join(self.normal_dir, "cropped")
        if os.path.isdir(crop_dir):
            files = sorted([f for f in os.listdir(crop_dir) if f.endswith(".jpg")])
            for f in files[:max_images]:
                img = cv2.imread(os.path.join(crop_dir, f), cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    images.append(img)

        # 부족하면 합성 추가
        if len(images) < max_images:
            synth_dir = os.path.join(self.normal_dir, "synthetic")
            if os.path.isdir(synth_dir):
                files = sorted([f for f in os.listdir(synth_dir) if f.endswith(".jpg")])
                remain = max_images - len(images)
                for f in files[:remain]:
                    img = cv2.imread(os.path.join(synth_dir, f), cv2.IMREAD_GRAYSCALE)
                    if img is not None:
                        images.append(img)

        return images

    def get_stats(self) -> dict:
        """현재 정상 데이터 통계"""
        stats = {"cropped": 0, "synthetic": 0}
        crop_dir = os.path.join(self.normal_dir, "cropped")
        synth_dir = os.path.join(self.normal_dir, "synthetic")
        if os.path.isdir(crop_dir):
            stats["cropped"] = len([f for f in os.listdir(crop_dir) if f.endswith(".jpg")])
        if os.path.isdir(synth_dir):
            stats["synthetic"] = len([f for f in os.listdir(synth_dir) if f.endswith(".jpg")])
        stats["total"] = stats["cropped"] + stats["synthetic"]
        return stats


if __name__ == "__main__":
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "NEU-DET")
    NORMAL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "normal_patches")

    mgr = NormalDataManager(DATA_DIR, NORMAL_DIR)
    result = mgr.prepare(force=True)
    print(f"\n=== 결과 ===")
    print(f"크롭 패치: {result['cropped']}장")
    print(f"합성 이미지: {result['synthetic']}장")
    print(f"총 정상 이미지: {result['total']}장")

    if "crop_stats" in result:
        print(f"\n클래스별 크롭:")
        for cls, cnt in result["crop_stats"]["per_class"].items():
            print(f"  {cls}: {cnt}장")

    # 샘플 시각화
    normals = mgr.load_normal_images(10)
    print(f"\n로드된 샘플: {len(normals)}장, 크기: {normals[0].shape}")
