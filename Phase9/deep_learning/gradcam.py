"""Grad-CAM 시각화 모듈.

Gradient-weighted Class Activation Mapping을 사용하여
모델이 분류 결정에 사용한 이미지 영역을 시각화한다.

Reference:
    Selvaraju et al., "Grad-CAM: Visual Explanations from Deep Networks
    via Gradient-based Localization", ICCV 2017.
"""

import os
import sys
import numpy as np
import torch
import torch.nn.functional as F
import matplotlib.pyplot as plt
import cv2
from typing import Optional

# 프로젝트 루트를 path에 추가
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


class GradCAM:
    """Gradient-weighted Class Activation Mapping.

    Args:
        model: 분석할 PyTorch 모델.
        target_layer: Grad-CAM을 적용할 대상 레이어 (nn.Module).
    """

    def __init__(self, model: torch.nn.Module, target_layer: torch.nn.Module):
        self.model = model
        self.target_layer = target_layer
        self._gradients = None
        self._activations = None

        # 훅 등록
        self._forward_hook = target_layer.register_forward_hook(self._save_activation)
        self._backward_hook = target_layer.register_full_backward_hook(self._save_gradient)

    def _save_activation(self, module, input, output):
        """순전파 시 활성화 맵 저장."""
        self._activations = output.detach()

    def _save_gradient(self, module, grad_input, grad_output):
        """역전파 시 그래디언트 저장."""
        self._gradients = grad_output[0].detach()

    def __call__(
        self,
        input_tensor: torch.Tensor,
        target_class: Optional[int] = None,
    ) -> np.ndarray:
        """Grad-CAM 히트맵 생성.

        Args:
            input_tensor: (1, C, H, W) 입력 텐서.
            target_class: 타겟 클래스 인덱스. None이면 예측 클래스 사용.

        Returns:
            (H_input, W_input) 크기의 히트맵 numpy 배열 (0~1 범위).
        """
        self.model.eval()
        device = next(self.model.parameters()).device

        input_tensor = input_tensor.to(device)
        input_tensor.requires_grad_(True)

        # 순전파
        output = self.model(input_tensor)

        if target_class is None:
            target_class = output.argmax(dim=1).item()

        # 역전파
        self.model.zero_grad()
        target = output[0, target_class]
        target.backward()

        # Grad-CAM 계산
        gradients = self._gradients  # (1, C, h, w)
        activations = self._activations  # (1, C, h, w)

        # GAP over spatial dimensions -> channel weights
        weights = gradients.mean(dim=(2, 3), keepdim=True)  # (1, C, 1, 1)

        # 가중합
        cam = (weights * activations).sum(dim=1, keepdim=True)  # (1, 1, h, w)
        cam = F.relu(cam)  # ReLU

        # 입력 크기로 리사이즈
        _, _, H, W = input_tensor.shape
        cam = F.interpolate(cam, size=(H, W), mode="bilinear", align_corners=False)

        # 정규화 (0~1)
        cam = cam.squeeze().cpu().numpy()
        cam_min = cam.min()
        cam_max = cam.max()
        if cam_max - cam_min > 1e-8:
            cam = (cam - cam_min) / (cam_max - cam_min)
        else:
            cam = np.zeros_like(cam)

        return cam

    def remove_hooks(self):
        """등록된 훅 제거."""
        self._forward_hook.remove()
        self._backward_hook.remove()

    def __del__(self):
        try:
            self.remove_hooks()
        except Exception:
            pass


def overlay_gradcam(
    image_np: np.ndarray,
    heatmap: np.ndarray,
    alpha: float = 0.4,
) -> np.ndarray:
    """Grad-CAM 히트맵을 원본 이미지에 오버레이.

    Args:
        image_np: (H, W) 또는 (H, W, 3) uint8 원본 이미지.
        heatmap: (H, W) float 히트맵 (0~1).
        alpha: 오버레이 투명도 (0~1).

    Returns:
        (H, W, 3) uint8 RGB 오버레이 이미지.
    """
    # 그레이스케일 -> RGB
    if image_np.ndim == 2:
        image_rgb = np.stack([image_np, image_np, image_np], axis=-1)
    else:
        image_rgb = image_np.copy()

    if image_rgb.dtype != np.uint8:
        image_rgb = (image_rgb * 255).clip(0, 255).astype(np.uint8)

    # 히트맵 -> 컬러맵 적용
    heatmap_resized = cv2.resize(heatmap, (image_rgb.shape[1], image_rgb.shape[0]))
    heatmap_uint8 = (heatmap_resized * 255).astype(np.uint8)
    heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
    heatmap_color = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)

    # 오버레이
    overlay = (
        (1 - alpha) * image_rgb.astype(np.float32)
        + alpha * heatmap_color.astype(np.float32)
    )
    overlay = overlay.clip(0, 255).astype(np.uint8)

    return overlay


def gradcam_grid(
    model: torch.nn.Module,
    images: np.ndarray,
    labels: np.ndarray,
    class_names: list[str],
    device: torch.device,
    n_per_class: int = 2,
    save_path: Optional[str] = None,
    num_channels: int = 3,
) -> plt.Figure:
    """클래스별 Grad-CAM 시각화 그리드 생성.

    Args:
        model: 분석할 모델 (get_gradcam_target_layer 메서드 필요).
        images: (N, 200, 200) uint8 원본 이미지.
        labels: (N,) int 라벨 배열.
        class_names: 클래스명 리스트.
        device: 디바이스.
        n_per_class: 클래스당 표시할 샘플 수.
        save_path: 저장 경로 (None이면 저장하지 않음).
        num_channels: 모델 입력 채널 수 (1 또는 3).

    Returns:
        matplotlib Figure 객체.
    """
    from deep_learning.augmentation import get_test_transforms

    plt.rcParams["font.family"] = "AppleGothic"
    plt.rcParams["axes.unicode_minus"] = False

    target_layer = model.get_gradcam_target_layer()
    gradcam = GradCAM(model, target_layer)

    transform = get_test_transforms(num_channels=num_channels)

    n_classes = len(class_names)
    fig, axes = plt.subplots(
        n_classes, n_per_class * 2,
        figsize=(4 * n_per_class * 2, 4 * n_classes),
    )

    from utils.data_loader import NEUDataLoader
    kr_map = NEUDataLoader.CLASS_NAME_KR

    for cls_idx in range(n_classes):
        cls_mask = labels == cls_idx
        cls_images = images[cls_mask]

        if len(cls_images) == 0:
            continue

        # 랜덤 샘플링
        rng = np.random.default_rng(42)
        sample_indices = rng.choice(
            len(cls_images), size=min(n_per_class, len(cls_images)), replace=False
        )

        for j, idx in enumerate(sample_indices):
            img = cls_images[idx]  # (200, 200) uint8

            # 변환 적용
            from PIL import Image as PILImage
            if num_channels == 3:
                pil_img = PILImage.fromarray(
                    np.stack([img, img, img], axis=-1), mode="RGB"
                )
            else:
                pil_img = PILImage.fromarray(img, mode="L")

            input_tensor = transform(pil_img).unsqueeze(0)

            # Grad-CAM 생성
            heatmap = gradcam(input_tensor, target_class=cls_idx)
            overlay = overlay_gradcam(img, heatmap, alpha=0.4)

            # 원본 이미지 표시
            col_orig = j * 2
            col_cam = j * 2 + 1

            axes[cls_idx, col_orig].imshow(img, cmap="gray")
            kr_name = kr_map.get(class_names[cls_idx], class_names[cls_idx])
            axes[cls_idx, col_orig].set_title(f"{kr_name} (원본)", fontsize=10)
            axes[cls_idx, col_orig].axis("off")

            # Grad-CAM 오버레이 표시
            axes[cls_idx, col_cam].imshow(overlay)
            axes[cls_idx, col_cam].set_title(f"{kr_name} (Grad-CAM)", fontsize=10)
            axes[cls_idx, col_cam].axis("off")

    plt.suptitle("Grad-CAM 시각화 (클래스별)", fontsize=16, fontweight="bold")
    plt.tight_layout()

    if save_path is not None:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Grad-CAM 그리드 저장: {save_path}")

    gradcam.remove_hooks()
    return fig


if __name__ == "__main__":
    print("=" * 60)
    print("gradcam.py 스모크 테스트")
    print("=" * 60)

    from deep_learning.models.custom_cnn import CustomCNN

    # 더미 모델 및 입력
    model = CustomCNN(num_classes=6)
    model.eval()

    target_layer = model.get_gradcam_target_layer()
    gradcam = GradCAM(model, target_layer)

    dummy_input = torch.randn(1, 1, 200, 200)
    heatmap = gradcam(dummy_input, target_class=0)
    print(f"히트맵 shape: {heatmap.shape}")
    print(f"히트맵 범위: [{heatmap.min():.4f}, {heatmap.max():.4f}]")
    assert heatmap.shape == (200, 200), f"Expected (200,200), got {heatmap.shape}"

    # 오버레이 테스트
    dummy_image = np.random.randint(0, 255, (200, 200), dtype=np.uint8)
    overlay = overlay_gradcam(dummy_image, heatmap, alpha=0.4)
    print(f"오버레이 shape: {overlay.shape}, dtype: {overlay.dtype}")
    assert overlay.shape == (200, 200, 3)
    assert overlay.dtype == np.uint8

    gradcam.remove_hooks()
    print("\ngradcam.py 스모크 테스트 완료")
