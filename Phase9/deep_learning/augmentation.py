"""데이터 증강 및 전처리 변환 모듈.

학습/테스트용 torchvision 변환 파이프라인, OpenCV 전처리 통합,
그리고 Mixup/CutMix 배치 레벨 증강을 제공한다.
"""

import os
import sys
import numpy as np
import torch
from torchvision import transforms
from PIL import Image

# 프로젝트 루트를 path에 추가
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


class OpenCVPreprocessTransform:
    """OpenCV 기반 전처리를 torchvision 변환으로 래핑.

    기존 preprocessing 모듈의 CLAHE, bilateral filter, adaptive sharpen을
    파이프라인에 통합한다. PIL Image를 입력/출력으로 사용.
    """

    def __init__(self):
        # 지연 임포트로 순환 참조 방지
        pass

    def __call__(self, pil_img: Image.Image) -> Image.Image:
        import cv2
        from preprocessing.normalization import clahe_equalization
        from preprocessing.filters import bilateral_filter
        from preprocessing.sharpening import adaptive_sharpen

        # PIL -> numpy (그레이스케일)
        img_np = np.array(pil_img)
        if img_np.ndim == 3:
            img_np = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)

        # CLAHE 적용
        img_np = clahe_equalization(img_np)

        # Bilateral filter 적용
        img_np = bilateral_filter(img_np, d=9, sigma_color=75, sigma_space=75)

        # Adaptive sharpen 적용
        img_np = adaptive_sharpen(img_np, blur_ksize=5, sharp_amount=1.5, noise_threshold=10)

        # numpy -> PIL 복원
        if pil_img.mode == "RGB":
            img_np = np.stack([img_np, img_np, img_np], axis=-1)
            return Image.fromarray(img_np, mode="RGB")
        else:
            return Image.fromarray(img_np, mode="L")

    def __repr__(self):
        return "OpenCVPreprocessTransform(CLAHE + Bilateral + AdaptiveSharpen)"


def get_train_transforms(
    augment: bool = True,
    opencv_preprocess: bool = False,
    num_channels: int = 3,
) -> transforms.Compose:
    """학습용 변환 파이프라인 생성.

    Args:
        augment: True이면 랜덤 증강(회전, 플립, 색상 변환) 적용.
        opencv_preprocess: True이면 OpenCV 전처리(CLAHE 등) 적용.
        num_channels: 출력 채널 수 (1 또는 3).

    Returns:
        torchvision.transforms.Compose 객체.
    """
    transform_list = []

    # OpenCV 전처리 (PIL 단계에서 적용)
    if opencv_preprocess:
        transform_list.append(OpenCVPreprocessTransform())

    # 리사이즈 (ResNet은 224x224, CustomCNN은 200x200)
    if num_channels == 3:
        transform_list.append(transforms.Resize((224, 224)))
    # num_channels == 1 이면 200x200 그대로 유지

    # 데이터 증강
    if augment:
        transform_list.extend([
            transforms.RandomRotation(15),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomVerticalFlip(p=0.5),
        ])
        if num_channels == 3:
            transform_list.append(
                transforms.ColorJitter(brightness=0.2, contrast=0.2)
            )

    # 텐서 변환
    transform_list.append(transforms.ToTensor())

    # 정규화
    if num_channels == 3:
        transform_list.append(
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            )
        )
    else:
        transform_list.append(
            transforms.Normalize(mean=[0.5], std=[0.5])
        )

    return transforms.Compose(transform_list)


def get_test_transforms(num_channels: int = 3) -> transforms.Compose:
    """테스트/추론용 변환 파이프라인 생성.

    증강 없이 리사이즈 + 텐서 변환 + 정규화만 수행.

    Args:
        num_channels: 출력 채널 수 (1 또는 3).

    Returns:
        torchvision.transforms.Compose 객체.
    """
    transform_list = []

    if num_channels == 3:
        transform_list.append(transforms.Resize((224, 224)))

    transform_list.append(transforms.ToTensor())

    if num_channels == 3:
        transform_list.append(
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            )
        )
    else:
        transform_list.append(
            transforms.Normalize(mean=[0.5], std=[0.5])
        )

    return transforms.Compose(transform_list)


class Mixup:
    """Mixup 배치 레벨 데이터 증강.

    두 샘플을 선형 보간하여 새로운 학습 샘플을 생성한다.

    Args:
        alpha: Beta 분포 파라미터. 작을수록 원본에 가깝다.

    Reference:
        Zhang et al., "mixup: Beyond Empirical Risk Minimization", ICLR 2018.
    """

    def __init__(self, alpha: float = 0.2):
        self.alpha = alpha

    def __call__(
        self, images: torch.Tensor, labels: torch.Tensor, num_classes: int = 6
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """배치에 Mixup 적용.

        Args:
            images: (B, C, H, W) 텐서.
            labels: (B,) 정수 라벨 텐서.
            num_classes: 클래스 수.

        Returns:
            (mixed_images, mixed_labels) 튜플.
            mixed_labels는 (B, num_classes) one-hot 소프트 라벨.
        """
        if self.alpha > 0:
            lam = np.random.beta(self.alpha, self.alpha)
        else:
            lam = 1.0

        batch_size = images.size(0)
        index = torch.randperm(batch_size, device=images.device)

        mixed_images = lam * images + (1 - lam) * images[index]

        # 소프트 라벨 생성
        labels_onehot = torch.zeros(batch_size, num_classes, device=images.device)
        labels_onehot.scatter_(1, labels.unsqueeze(1), 1.0)
        labels_onehot_shuffled = labels_onehot[index]
        mixed_labels = lam * labels_onehot + (1 - lam) * labels_onehot_shuffled

        return mixed_images, mixed_labels

    def __repr__(self):
        return f"Mixup(alpha={self.alpha})"


class CutMix:
    """CutMix 배치 레벨 데이터 증강.

    이미지의 일부 영역을 다른 이미지로 대체한다.

    Args:
        alpha: Beta 분포 파라미터.

    Reference:
        Yun et al., "CutMix: Regularization Strategy to Train Strong Classifiers
        with Localizable Features", ICCV 2019.
    """

    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha

    @staticmethod
    def _rand_bbox(
        size: tuple, lam: float
    ) -> tuple[int, int, int, int]:
        """랜덤 bounding box 생성."""
        _, _, H, W = size
        cut_ratio = np.sqrt(1.0 - lam)
        cut_h = int(H * cut_ratio)
        cut_w = int(W * cut_ratio)

        # 중심점 랜덤 선택
        cy = np.random.randint(H)
        cx = np.random.randint(W)

        y1 = np.clip(cy - cut_h // 2, 0, H)
        y2 = np.clip(cy + cut_h // 2, 0, H)
        x1 = np.clip(cx - cut_w // 2, 0, W)
        x2 = np.clip(cx + cut_w // 2, 0, W)

        return y1, y2, x1, x2

    def __call__(
        self, images: torch.Tensor, labels: torch.Tensor, num_classes: int = 6
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """배치에 CutMix 적용.

        Args:
            images: (B, C, H, W) 텐서.
            labels: (B,) 정수 라벨 텐서.
            num_classes: 클래스 수.

        Returns:
            (mixed_images, mixed_labels) 튜플.
            mixed_labels는 (B, num_classes) one-hot 소프트 라벨.
        """
        if self.alpha > 0:
            lam = np.random.beta(self.alpha, self.alpha)
        else:
            lam = 1.0

        batch_size = images.size(0)
        index = torch.randperm(batch_size, device=images.device)

        mixed_images = images.clone()
        y1, y2, x1, x2 = self._rand_bbox(images.size(), lam)
        mixed_images[:, :, y1:y2, x1:x2] = images[index, :, y1:y2, x1:x2]

        # 실제 비율 재계산
        _, _, H, W = images.size()
        lam_actual = 1.0 - (y2 - y1) * (x2 - x1) / (H * W)

        # 소프트 라벨 생성
        labels_onehot = torch.zeros(batch_size, num_classes, device=images.device)
        labels_onehot.scatter_(1, labels.unsqueeze(1), 1.0)
        labels_onehot_shuffled = labels_onehot[index]
        mixed_labels = lam_actual * labels_onehot + (1 - lam_actual) * labels_onehot_shuffled

        return mixed_images, mixed_labels

    def __repr__(self):
        return f"CutMix(alpha={self.alpha})"


if __name__ == "__main__":
    print("=" * 60)
    print("augmentation.py 스모크 테스트")
    print("=" * 60)

    # 변환 파이프라인 생성 테스트
    tf_train_3ch = get_train_transforms(augment=True, num_channels=3)
    tf_test_3ch = get_test_transforms(num_channels=3)
    tf_train_1ch = get_train_transforms(augment=True, num_channels=1)
    tf_test_1ch = get_test_transforms(num_channels=1)
    print(f"학습 변환 (3ch): {tf_train_3ch}")
    print(f"테스트 변환 (3ch): {tf_test_3ch}")
    print(f"학습 변환 (1ch): {tf_train_1ch}")

    # PIL 이미지로 변환 테스트
    dummy = Image.fromarray(np.random.randint(0, 255, (200, 200), dtype=np.uint8), mode="L")
    dummy_rgb = Image.fromarray(
        np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8), mode="RGB"
    )

    out_1ch = tf_train_1ch(dummy)
    print(f"1ch 변환 결과: {out_1ch.shape}")
    assert out_1ch.shape == (1, 200, 200)

    out_3ch = tf_train_3ch(dummy_rgb)
    print(f"3ch 변환 결과: {out_3ch.shape}")
    assert out_3ch.shape == (3, 224, 224)

    # Mixup 테스트
    mixup = Mixup(alpha=0.2)
    batch_imgs = torch.randn(8, 3, 224, 224)
    batch_lbls = torch.randint(0, 6, (8,))
    mixed_imgs, mixed_lbls = mixup(batch_imgs, batch_lbls, num_classes=6)
    print(f"Mixup: images={mixed_imgs.shape}, labels={mixed_lbls.shape}")
    assert mixed_lbls.shape == (8, 6)

    # CutMix 테스트
    cutmix = CutMix(alpha=1.0)
    mixed_imgs, mixed_lbls = cutmix(batch_imgs, batch_lbls, num_classes=6)
    print(f"CutMix: images={mixed_imgs.shape}, labels={mixed_lbls.shape}")
    assert mixed_lbls.shape == (8, 6)

    print("\naugmentation.py 스모크 테스트 완료")
