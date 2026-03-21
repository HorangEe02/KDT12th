"""딥러닝 모델 서브패키지.

CustomCNN 및 ResNet-18 전이학습 모델을 제공한다.
"""

from deep_learning.models.custom_cnn import CustomCNN
from deep_learning.models.resnet_transfer import (
    get_resnet18_finetune,
    get_resnet18_feature_extractor,
)

__all__ = [
    "CustomCNN",
    "get_resnet18_finetune",
    "get_resnet18_feature_extractor",
]


if __name__ == "__main__":
    print("deep_learning.models 패키지 로드 확인")
    print(f"  CustomCNN: {CustomCNN}")
    print(f"  get_resnet18_finetune: {get_resnet18_finetune}")
    print(f"  get_resnet18_feature_extractor: {get_resnet18_feature_extractor}")
