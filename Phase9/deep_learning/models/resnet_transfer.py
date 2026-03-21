"""ResNet-18 전이학습 모델.

ImageNet 사전학습된 ResNet-18을 금속 표면 결함 분류에 적용한다.
Fine-tuning(전체 레이어 학습)과 Feature Extractor(백본 동결) 두 가지 방식을 지원.
"""

import torch
import torch.nn as nn
from torchvision import models


class _ResNet18Wrapper(nn.Module):
    """ResNet-18 래퍼.

    get_gradcam_target_layer() 메서드를 추가하기 위한 래퍼 클래스.
    """

    def __init__(self, base_model: nn.Module):
        super().__init__()
        self.model = base_model

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)

    def get_gradcam_target_layer(self) -> nn.Module:
        """Grad-CAM 대상 레이어(layer4의 마지막 BasicBlock) 반환."""
        return self.model.layer4[-1]


def get_resnet18_finetune(num_classes: int = 6) -> nn.Module:
    """Fine-tuning용 ResNet-18 모델.

    ImageNet 사전학습 가중치를 로드하고, 마지막 FC 레이어를 num_classes로 교체.
    모든 레이어가 학습 가능하다.

    Args:
        num_classes: 출력 클래스 수.

    Returns:
        get_gradcam_target_layer() 메서드를 가진 ResNet-18 모델.
    """
    weights = models.ResNet18_Weights.IMAGENET1K_V1
    base_model = models.resnet18(weights=weights)

    # FC 레이어 교체
    in_features = base_model.fc.in_features
    base_model.fc = nn.Linear(in_features, num_classes)

    # 모든 파라미터 학습 가능
    for param in base_model.parameters():
        param.requires_grad = True

    model = _ResNet18Wrapper(base_model)

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[ResNet-18 Fine-tune] 총 파라미터: {total_params:,}")
    print(f"[ResNet-18 Fine-tune] 학습 가능 파라미터: {trainable_params:,}")

    return model


def get_resnet18_feature_extractor(num_classes: int = 6) -> nn.Module:
    """Feature Extractor용 ResNet-18 모델.

    ImageNet 사전학습 가중치를 로드하고, FC 레이어를 교체.
    layer4와 FC 레이어만 학습 가능하고 나머지는 동결.

    Args:
        num_classes: 출력 클래스 수.

    Returns:
        get_gradcam_target_layer() 메서드를 가진 ResNet-18 모델.
    """
    weights = models.ResNet18_Weights.IMAGENET1K_V1
    base_model = models.resnet18(weights=weights)

    # FC 레이어 교체
    in_features = base_model.fc.in_features
    base_model.fc = nn.Linear(in_features, num_classes)

    # 모든 파라미터 동결
    for param in base_model.parameters():
        param.requires_grad = False

    # layer4와 fc만 학습 가능으로 설정
    for param in base_model.layer4.parameters():
        param.requires_grad = True
    for param in base_model.fc.parameters():
        param.requires_grad = True

    model = _ResNet18Wrapper(base_model)

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[ResNet-18 Feature Extractor] 총 파라미터: {total_params:,}")
    print(f"[ResNet-18 Feature Extractor] 학습 가능 파라미터: {trainable_params:,}")

    return model


if __name__ == "__main__":
    print("=" * 60)
    print("ResNet-18 전이학습 모델 스모크 테스트")
    print("=" * 60)

    # Fine-tune 모델
    print("\n--- Fine-tune 모델 ---")
    model_ft = get_resnet18_finetune(num_classes=6)
    dummy_input = torch.randn(4, 3, 224, 224)
    output = model_ft(dummy_input)
    print(f"입력: {dummy_input.shape} -> 출력: {output.shape}")
    assert output.shape == (4, 6), f"Expected (4,6), got {output.shape}"

    # Grad-CAM 타겟 레이어
    target = model_ft.get_gradcam_target_layer()
    print(f"Grad-CAM 타겟: {type(target).__name__}")

    # Feature Extractor 모델
    print("\n--- Feature Extractor 모델 ---")
    model_fe = get_resnet18_feature_extractor(num_classes=6)
    output = model_fe(dummy_input)
    print(f"입력: {dummy_input.shape} -> 출력: {output.shape}")
    assert output.shape == (4, 6), f"Expected (4,6), got {output.shape}"

    # 동결 확인
    frozen = sum(1 for p in model_fe.parameters() if not p.requires_grad)
    trainable = sum(1 for p in model_fe.parameters() if p.requires_grad)
    print(f"동결 파라미터 그룹: {frozen}, 학습 가능 그룹: {trainable}")

    print("\nResNet-18 전이학습 모델 스모크 테스트 완료")
