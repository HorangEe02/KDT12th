"""커스텀 CNN 모델.

금속 표면 결함 분류를 위한 경량 CNN 아키텍처.
200x200 그레이스케일 이미지(1채널)를 입력으로 받아 6클래스 분류를 수행한다.
"""

import torch
import torch.nn as nn


class CustomCNN(nn.Module):
    """금속 표면 결함 분류용 커스텀 CNN.

    Architecture:
        Conv(1,32,3,pad=1) -> BN -> ReLU -> MaxPool(2)
        Conv(32,64,3,pad=1) -> BN -> ReLU -> MaxPool(2)
        Conv(64,128,3,pad=1) -> BN -> ReLU -> MaxPool(2)
        Conv(128,256,3,pad=1) -> BN -> ReLU -> AdaptiveAvgPool(4)
        Flatten -> Linear(256*4*4, 512) -> ReLU -> Dropout(0.5) -> Linear(512, 6)

    Args:
        num_classes: 출력 클래스 수 (기본값: 6).
    """

    def __init__(self, num_classes: int = 6):
        super().__init__()
        self.num_classes = num_classes

        # Block 1: (1, 200, 200) -> (32, 100, 100)
        self.block1 = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
        )

        # Block 2: (32, 100, 100) -> (64, 50, 50)
        self.block2 = nn.Sequential(
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
        )

        # Block 3: (64, 50, 50) -> (128, 25, 25)
        self.block3 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
        )

        # Block 4: (128, 25, 25) -> (256, 5, 5)
        # NOTE: AdaptiveAvgPool2d(5) — 25/5=5 (정수 분할, MPS 호환)
        self.block4 = nn.Sequential(
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d(output_size=5),
        )

        # Classifier
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(256 * 5 * 5, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.5),
            nn.Linear(512, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """순전파.

        Args:
            x: (batch, 1, 200, 200) 입력 텐서.

        Returns:
            (batch, num_classes) 로짓 텐서.
        """
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.block4(x)
        x = self.classifier(x)
        return x

    def get_gradcam_target_layer(self) -> nn.Module:
        """Grad-CAM 대상 레이어(마지막 컨볼루션 레이어) 반환."""
        # block4의 첫 번째 Conv2d 레이어
        return self.block4[0]


if __name__ == "__main__":
    print("=" * 60)
    print("CustomCNN 스모크 테스트")
    print("=" * 60)

    model = CustomCNN(num_classes=6)
    print(f"모델 구조:\n{model}")

    # 파라미터 수 계산
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"\n총 파라미터: {total_params:,}")
    print(f"학습 가능 파라미터: {trainable_params:,}")

    # 순전파 테스트
    dummy_input = torch.randn(4, 1, 200, 200)
    output = model(dummy_input)
    print(f"\n입력 shape: {dummy_input.shape}")
    print(f"출력 shape: {output.shape}")
    assert output.shape == (4, 6), f"Expected (4,6), got {output.shape}"

    # Grad-CAM 타겟 레이어 확인
    target_layer = model.get_gradcam_target_layer()
    print(f"\nGrad-CAM 타겟 레이어: {target_layer}")

    print("\nCustomCNN 스모크 테스트 완료")
