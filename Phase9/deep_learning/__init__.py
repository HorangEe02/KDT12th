"""Phase 2 딥러닝 기반 금속 표면 결함 분류 패키지.

CNN, ResNet-18 전이학습, Grad-CAM 시각화 등을 포함한다.
"""

__version__ = "0.1.0"

__all__ = [
    "datasets",
    "augmentation",
    "train_dl",
    "gradcam",
    "evaluate_dl",
    "inference_dl",
]


if __name__ == "__main__":
    print(f"deep_learning package v{__version__}")
    print("Phase 2 딥러닝 모듈 패키지 로드 확인")
