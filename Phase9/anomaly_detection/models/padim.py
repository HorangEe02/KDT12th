"""PaDiM: Patch Distribution Modeling 기반 이상 탐지.

사전학습된 ResNet-18에서 다중 레이어 특징을 추출하고,
패치 위치별로 정상 이미지의 특징 분포(가우시안)를 모델링한다.
테스트 시 마할라노비스 거리를 이용하여 이상 탐지를 수행한다.

참고: Defard et al., "PaDiM: a Patch Distribution Modeling Framework
for Anomaly Detection and Localization", ICPR 2021.
"""

import os
import pickle
import random
from typing import Optional, Tuple, List

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms
from scipy.ndimage import gaussian_filter
from scipy.spatial.distance import mahalanobis


class _FeatureExtractor(nn.Module):
    """ResNet-18에서 layer1, layer2, layer3 특징을 추출하는 래퍼."""

    def __init__(self) -> None:
        super().__init__()
        resnet = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
        self.layer0 = nn.Sequential(
            resnet.conv1, resnet.bn1, resnet.relu, resnet.maxpool
        )
        self.layer1 = resnet.layer1  # 64ch
        self.layer2 = resnet.layer2  # 128ch
        self.layer3 = resnet.layer3  # 256ch

        for param in self.parameters():
            param.requires_grad = False

    def forward(self, x: torch.Tensor) -> List[torch.Tensor]:
        """다중 스케일 특징 추출.

        Args:
            x: (B, 3, H, W) 입력 텐서.

        Returns:
            [layer1_feat, layer2_feat, layer3_feat] 리스트.
        """
        h = self.layer0(x)
        feat1 = self.layer1(h)   # (B, 64, H/4, W/4)
        feat2 = self.layer2(feat1)  # (B, 128, H/8, W/8)
        feat3 = self.layer3(feat2)  # (B, 256, H/16, W/16)
        return [feat1, feat2, feat3]


class PaDiM:
    """PaDiM 이상 탐지 모델.

    사전학습 ResNet-18 backbone에서 다중 레이어 특징을 추출하고
    패치 위치별 가우시안 분포를 모델링한다.

    Args:
        n_selected_features: 랜덤 선택할 특징 차원 수 (기본 100).
        image_size: 입력 이미지 크기 (정방).
        random_seed: 랜덤 시드.
    """

    def __init__(
        self,
        n_selected_features: int = 100,
        image_size: int = 256,
        random_seed: int = 42,
    ) -> None:
        self.n_selected_features = n_selected_features
        self.image_size = image_size
        self.random_seed = random_seed

        self.feature_extractor = _FeatureExtractor()
        self.feature_extractor.eval()

        # layer1: 64, layer2: 128, layer3: 256 => 총 448 채널
        self.total_channels = 64 + 128 + 256  # 448

        # 랜덤 차원 선택
        random.seed(random_seed)
        n_sel = min(n_selected_features, self.total_channels)
        self.selected_indices = sorted(
            random.sample(range(self.total_channels), n_sel)
        )

        # 학습된 통계
        self.mean: Optional[np.ndarray] = None  # (C_sel, H_feat, W_feat)
        self.cov_inv: Optional[np.ndarray] = None  # (H_feat*W_feat, C_sel, C_sel)
        self.feat_h: int = 0
        self.feat_w: int = 0
        self._fitted = False

        # 입력 전처리 (ResNet용 ImageNet 정규화)
        self.normalize = transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        )

    def _preprocess(self, x: torch.Tensor) -> torch.Tensor:
        """이미지 전처리: 그레이스케일→RGB, 리사이즈, 정규화."""
        if x.shape[1] == 1:
            x = x.repeat(1, 3, 1, 1)

        if x.shape[-1] != self.image_size or x.shape[-2] != self.image_size:
            x = F.interpolate(x, size=(self.image_size, self.image_size),
                              mode="bilinear", align_corners=False)

        # ImageNet 정규화
        out = torch.stack([self.normalize(img) for img in x])
        return out

    def _extract_and_concat(self, x: torch.Tensor, device: torch.device) -> torch.Tensor:
        """다중 레이어 특징 추출 및 concatenation.

        Returns:
            (B, total_channels, H_feat, W_feat) 텐서.
        """
        x = self._preprocess(x).to(device)
        feats = self.feature_extractor(x)

        # layer3 해상도에 맞춰 모든 특징 리사이즈
        target_size = feats[-1].shape[-2:]

        resized = []
        for f in feats:
            if f.shape[-2:] != target_size:
                f = F.interpolate(f, size=target_size, mode="bilinear", align_corners=False)
            resized.append(f)

        # 채널 방향 concatenation
        concat = torch.cat(resized, dim=1)  # (B, 448, H, W)
        return concat

    def fit(
        self,
        train_loader,
        device: Optional[torch.device] = None,
    ) -> None:
        """정상 이미지로 패치별 가우시안 분포를 학습한다.

        Args:
            train_loader: 정상 이미지 DataLoader.
            device: 연산 디바이스.
        """
        if device is None:
            if torch.backends.mps.is_available():
                device = torch.device("mps")
            elif torch.cuda.is_available():
                device = torch.device("cuda")
            else:
                device = torch.device("cpu")

        self.feature_extractor = self.feature_extractor.to(device)
        self.feature_extractor.eval()

        print(f"[PaDiM] 정상 이미지 특징 추출 시작 (device={device})")

        all_features = []  # List of (B, C_sel, H, W)
        n_images = 0

        with torch.no_grad():
            for batch_idx, batch_data in enumerate(train_loader):
                # DataLoader 형식에 따라 이미지 추출
                if isinstance(batch_data, (list, tuple)):
                    images = batch_data[0]
                else:
                    images = batch_data

                features = self._extract_and_concat(images, device)
                # 선택된 차원만 사용
                features = features[:, self.selected_indices, :, :]
                all_features.append(features.cpu().numpy())
                n_images += images.shape[0]

                if (batch_idx + 1) % 10 == 0:
                    print(f"  배치 {batch_idx + 1} 처리 완료 ({n_images}장)")

        # (N, C_sel, H, W) 로 합치기
        all_features = np.concatenate(all_features, axis=0)
        N, C, H, W = all_features.shape
        self.feat_h = H
        self.feat_w = W

        print(f"[PaDiM] 특징 shape: ({N}, {C}, {H}, {W})")
        print(f"[PaDiM] 패치별 가우시안 분포 계산 중...")

        # (N, C, H*W)로 reshape
        features_flat = all_features.reshape(N, C, H * W)  # (N, C, H*W)

        # 패치 위치별 mean, covariance 계산
        self.mean = np.mean(features_flat, axis=0)  # (C, H*W)

        # 공분산 역행렬 계산 (위치별)
        n_positions = H * W
        self.cov_inv = np.zeros((n_positions, C, C), dtype=np.float32)

        eps = 0.01  # 정규화 상수
        for pos in range(n_positions):
            patch_features = features_flat[:, :, pos]  # (N, C)
            cov = np.cov(patch_features, rowvar=False) + eps * np.eye(C)
            try:
                self.cov_inv[pos] = np.linalg.inv(cov)
            except np.linalg.LinAlgError:
                self.cov_inv[pos] = np.linalg.pinv(cov)

            if (pos + 1) % 50 == 0:
                print(f"  위치 {pos + 1}/{n_positions} 완료")

        self._fitted = True
        print(f"[PaDiM] 학습 완료! (패치 위치 수: {n_positions})")

    def predict(
        self,
        image_tensor: torch.Tensor,
        device: Optional[torch.device] = None,
    ) -> Tuple[float, np.ndarray]:
        """이미지에 대한 이상 점수와 이상 맵을 계산한다.

        Args:
            image_tensor: (C, H, W) 또는 (1, C, H, W) 이미지 텐서.
            device: 연산 디바이스.

        Returns:
            (anomaly_score, anomaly_map) 튜플.
            - anomaly_score: float (이상 점수).
            - anomaly_map: (image_size, image_size) float numpy 배열.
        """
        if not self._fitted:
            raise RuntimeError("PaDiM이 아직 학습되지 않았습니다. fit()을 먼저 호출하세요.")

        if device is None:
            if torch.backends.mps.is_available():
                device = torch.device("mps")
            elif torch.cuda.is_available():
                device = torch.device("cuda")
            else:
                device = torch.device("cpu")

        self.feature_extractor = self.feature_extractor.to(device)

        if image_tensor.dim() == 3:
            image_tensor = image_tensor.unsqueeze(0)

        with torch.no_grad():
            features = self._extract_and_concat(image_tensor, device)
            features = features[:, self.selected_indices, :, :]

        feat = features[0].cpu().numpy()  # (C, H, W)
        C, H, W = feat.shape
        feat_flat = feat.reshape(C, H * W)  # (C, H*W)

        # 마할라노비스 거리 계산
        dist_map = np.zeros(H * W, dtype=np.float32)
        for pos in range(H * W):
            diff = feat_flat[:, pos] - self.mean[:, pos]
            dist_map[pos] = np.sqrt(
                np.clip(diff @ self.cov_inv[pos] @ diff, 0, None)
            )

        dist_map = dist_map.reshape(H, W)

        # 원본 이미지 크기로 업스케일
        dist_map_resized = torch.tensor(dist_map).unsqueeze(0).unsqueeze(0).float()
        dist_map_resized = F.interpolate(
            dist_map_resized,
            size=(self.image_size, self.image_size),
            mode="bilinear",
            align_corners=False,
        ).squeeze().numpy()

        # 가우시안 스무딩
        anomaly_map = gaussian_filter(dist_map_resized, sigma=4)

        anomaly_score = float(np.max(anomaly_map))

        return anomaly_score, anomaly_map

    def save(self, path: str) -> None:
        """모델 저장."""
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        state = {
            "n_selected_features": self.n_selected_features,
            "image_size": self.image_size,
            "random_seed": self.random_seed,
            "selected_indices": self.selected_indices,
            "mean": self.mean,
            "cov_inv": self.cov_inv,
            "feat_h": self.feat_h,
            "feat_w": self.feat_w,
            "fitted": self._fitted,
        }
        with open(path, "wb") as f:
            pickle.dump(state, f)
        print(f"[PaDiM] 저장 완료: {path}")

    @classmethod
    def load(cls, path: str) -> "PaDiM":
        """모델 로드."""
        with open(path, "rb") as f:
            state = pickle.load(f)

        model = cls(
            n_selected_features=state["n_selected_features"],
            image_size=state["image_size"],
            random_seed=state["random_seed"],
        )
        model.selected_indices = state["selected_indices"]
        model.mean = state["mean"]
        model.cov_inv = state["cov_inv"]
        model.feat_h = state["feat_h"]
        model.feat_w = state["feat_w"]
        model._fitted = state["fitted"]

        print(f"[PaDiM] 로드 완료: {path}")
        return model


# ---------------------------------------------------------------------------
# 스모크 테스트
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("PaDiM 스모크 테스트")
    print("=" * 60)

    device = "cpu"
    if torch.backends.mps.is_available():
        device = "mps"
    elif torch.cuda.is_available():
        device = "cuda"
    print(f"[INFO] Device: {device}")

    # 더미 DataLoader 생성
    from torch.utils.data import TensorDataset, DataLoader

    # 3ch 256x256 (MVTec 스타일)
    print("\n--- 3ch 256x256 테스트 ---")
    dummy_images = torch.randn(20, 3, 256, 256) * 0.5 + 0.5
    dummy_labels = torch.zeros(20, dtype=torch.long)
    dummy_ds = TensorDataset(dummy_images, dummy_labels)
    dummy_loader = DataLoader(dummy_ds, batch_size=8, shuffle=False)

    padim = PaDiM(n_selected_features=50, image_size=256)
    padim.fit(dummy_loader, device=torch.device(device))

    # 예측 테스트
    test_img = torch.randn(3, 256, 256) * 0.5 + 0.5
    score, amap = padim.predict(test_img, device=torch.device(device))
    print(f"Anomaly score: {score:.4f}, map shape: {amap.shape}")

    # 1ch 200x200 (NEU 스타일)
    print("\n--- 1ch 200x200 테스트 ---")
    dummy_gray = torch.randn(15, 1, 200, 200) * 0.5 + 0.5
    dummy_ds_gray = TensorDataset(dummy_gray, torch.zeros(15, dtype=torch.long))
    dummy_loader_gray = DataLoader(dummy_ds_gray, batch_size=8, shuffle=False)

    padim_gray = PaDiM(n_selected_features=50, image_size=200)
    padim_gray.fit(dummy_loader_gray, device=torch.device(device))

    test_gray = torch.randn(1, 200, 200) * 0.5 + 0.5
    score_g, amap_g = padim_gray.predict(test_gray, device=torch.device(device))
    print(f"Anomaly score: {score_g:.4f}, map shape: {amap_g.shape}")

    # 저장/로드 테스트
    print("\n--- 저장/로드 테스트 ---")
    save_path = "/tmp/padim_test.pkl"
    padim.save(save_path)
    padim_loaded = PaDiM.load(save_path)
    score2, amap2 = padim_loaded.predict(test_img, device=torch.device(device))
    print(f"로드 후 score: {score2:.4f}")
    assert abs(score - score2) < 1e-4, "저장/로드 후 결과가 다릅니다!"

    # 정리
    os.remove(save_path)

    print("\n[PASS] PaDiM 스모크 테스트 완료")
