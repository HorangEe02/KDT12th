"""합성곱 오토인코더(Convolutional Autoencoder) 기반 이상 탐지 모델.

정상 이미지만으로 학습한 오토인코더가 비정상 이미지를 복원하지 못하는
원리를 이용하여, 복원 오류(reconstruction error)로 이상을 탐지한다.
NEU (1ch, 200x200) 및 MVTec (3ch, 256x256) 모두 지원.
"""

import math
from typing import Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from scipy.ndimage import gaussian_filter


class ConvAutoencoder(nn.Module):
    """합성곱 오토인코더.

    Encoder: 4-layer CNN (stride=2 다운샘플링)
    Bottleneck: FC → latent → FC
    Decoder: 4-layer transposed CNN (stride=2 업샘플링)

    Args:
        in_channels: 입력 채널 수 (1=그레이스케일, 3=RGB).
        image_size: 입력 이미지 크기 (정방).
        latent_dim: 잠재 공간 차원.
    """

    def __init__(
        self,
        in_channels: int = 1,
        image_size: int = 200,
        latent_dim: int = 128,
    ) -> None:
        super().__init__()
        self.in_channels = in_channels
        self.image_size = image_size
        self.latent_dim = latent_dim

        # 인코더 출력 공간 크기 계산 (Conv2d(k=4,s=2,p=1) 4번)
        # out = floor((in - 4 + 2*1) / 2) + 1 = floor(in/2)
        self.feat_size = image_size
        for _ in range(4):
            self.feat_size = self.feat_size // 2
        self.flat_dim = 256 * self.feat_size * self.feat_size

        # --- Encoder ---
        self.encoder = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),

            nn.Conv2d(32, 64, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),

            nn.Conv2d(64, 128, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),

            nn.Conv2d(128, 256, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
        )

        # --- Bottleneck ---
        self.fc_encode = nn.Linear(self.flat_dim, latent_dim)
        self.fc_decode = nn.Linear(latent_dim, self.flat_dim)

        # --- Decoder ---
        # 디코더 출력 패딩 보정을 위해 각 단계의 기대 크기 계산
        sizes = [image_size]
        for _ in range(4):
            sizes.append(math.ceil(sizes[-1] / 2))
        sizes.reverse()  # [feat_size, ..., image_size]

        # output_padding 계산: ConvTranspose2d(s=2)의 출력은 (input-1)*2 - 2*p + k + op
        # k=4, p=1 -> out = (in-1)*2 + 2 + op = in*2 + op
        ops = []
        for i in range(4):
            expected_out = sizes[i + 1]
            base_out = sizes[i] * 2
            op = expected_out - base_out
            ops.append(max(0, min(op, 1)))

        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(256, 128, kernel_size=4, stride=2, padding=1, output_padding=ops[0]),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),

            nn.ConvTranspose2d(128, 64, kernel_size=4, stride=2, padding=1, output_padding=ops[1]),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),

            nn.ConvTranspose2d(64, 32, kernel_size=4, stride=2, padding=1, output_padding=ops[2]),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),

            nn.ConvTranspose2d(32, in_channels, kernel_size=4, stride=2, padding=1, output_padding=ops[3]),
            nn.Sigmoid(),
        )

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """인코더: 입력 → 잠재 벡터."""
        h = self.encoder(x)
        h = h.view(h.size(0), -1)
        z = self.fc_encode(h)
        return z

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        """디코더: 잠재 벡터 → 복원 이미지."""
        h = self.fc_decode(z)
        h = h.view(h.size(0), 256, self.feat_size, self.feat_size)
        out = self.decoder(h)
        # 정확한 크기로 맞추기
        if out.shape[-1] != self.image_size or out.shape[-2] != self.image_size:
            out = torch.nn.functional.interpolate(
                out, size=(self.image_size, self.image_size),
                mode="bilinear", align_corners=False,
            )
        return out

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """순전파: 입력 → 복원."""
        z = self.encode(x)
        recon = self.decode(z)
        return recon

    def get_latent(self, x: torch.Tensor) -> torch.Tensor:
        """잠재 벡터 추출 (추론용)."""
        with torch.no_grad():
            return self.encode(x)


def compute_anomaly_map(
    original: torch.Tensor,
    reconstructed: torch.Tensor,
    sigma: float = 4.0,
) -> np.ndarray:
    """픽셀별 복원 오류 기반 이상 맵 계산.

    Args:
        original: 원본 이미지 텐서 (C, H, W) 또는 (1, C, H, W).
        reconstructed: 복원 이미지 텐서 (동일 shape).
        sigma: 가우시안 스무딩 시그마.

    Returns:
        (H, W) float numpy 배열 (이상 맵).
    """
    # numpy 또는 tensor 모두 지원
    if isinstance(original, np.ndarray):
        original = torch.from_numpy(original).float()
    if isinstance(reconstructed, np.ndarray):
        reconstructed = torch.from_numpy(reconstructed).float()

    if original.dim() == 4:
        original = original.squeeze(0)
    if reconstructed.dim() == 4:
        reconstructed = reconstructed.squeeze(0)
    # (H, W) → (1, H, W) 보정
    if original.dim() == 2:
        original = original.unsqueeze(0)
    if reconstructed.dim() == 2:
        reconstructed = reconstructed.unsqueeze(0)

    # 채널 평균 MSE
    with torch.no_grad():
        diff = (original - reconstructed) ** 2
        if diff.shape[0] > 1:
            anomaly_map = diff.mean(dim=0).cpu().numpy()
        else:
            anomaly_map = diff.squeeze(0).cpu().numpy()

    # 가우시안 스무딩
    anomaly_map = gaussian_filter(anomaly_map, sigma=sigma)

    return anomaly_map.astype(np.float32)


def compute_anomaly_score(anomaly_map: np.ndarray) -> float:
    """이상 맵에서 이상 점수를 계산한다.

    Args:
        anomaly_map: (H, W) float 이상 맵.

    Returns:
        이상 점수 (이상 맵의 최댓값).
    """
    return float(np.max(anomaly_map))


# ---------------------------------------------------------------------------
# 스모크 테스트
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("ConvAutoencoder 스모크 테스트")
    print("=" * 60)

    device = "cpu"
    if torch.backends.mps.is_available():
        device = "mps"
        print("[INFO] MPS 가속 사용")
    elif torch.cuda.is_available():
        device = "cuda"
        print("[INFO] CUDA 가속 사용")
    else:
        print("[INFO] CPU 사용")

    # 1ch 200x200 테스트 (NEU)
    print("\n--- 1ch 200x200 (NEU) ---")
    model_neu = ConvAutoencoder(in_channels=1, image_size=200, latent_dim=128).to(device)
    dummy_neu = torch.randn(4, 1, 200, 200).to(device)
    recon_neu = model_neu(dummy_neu)
    print(f"Input: {dummy_neu.shape} -> Output: {recon_neu.shape}")
    assert recon_neu.shape == dummy_neu.shape, f"Shape mismatch: {recon_neu.shape}"

    z_neu = model_neu.get_latent(dummy_neu)
    print(f"Latent: {z_neu.shape}")

    # 3ch 256x256 테스트 (MVTec)
    print("\n--- 3ch 256x256 (MVTec) ---")
    model_mvtec = ConvAutoencoder(in_channels=3, image_size=256, latent_dim=256).to(device)
    dummy_mvtec = torch.randn(4, 3, 256, 256).to(device)
    recon_mvtec = model_mvtec(dummy_mvtec)
    print(f"Input: {dummy_mvtec.shape} -> Output: {recon_mvtec.shape}")
    assert recon_mvtec.shape == dummy_mvtec.shape, f"Shape mismatch: {recon_mvtec.shape}"

    # Anomaly map 테스트
    print("\n--- Anomaly Map ---")
    amap = compute_anomaly_map(dummy_neu[0].cpu(), recon_neu[0].cpu())
    score = compute_anomaly_score(amap)
    print(f"Anomaly map shape: {amap.shape}, score: {score:.6f}")

    # 파라미터 수
    n_params_neu = sum(p.numel() for p in model_neu.parameters())
    n_params_mvtec = sum(p.numel() for p in model_mvtec.parameters())
    print(f"\n파라미터 수 - NEU: {n_params_neu:,}, MVTec: {n_params_mvtec:,}")

    print("\n[PASS] ConvAutoencoder 스모크 테스트 완료")
