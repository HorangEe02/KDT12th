"""딥러닝 기반 추론 파이프라인.

저장된 딥러닝 모델(.pt 체크포인트)을 로드하여
단일 이미지 또는 배치 이미지에 대한 결함 분류 추론을 수행한다.
기존 DefectClassifier와 동일한 출력 형식을 제공한다.
"""

import os
import sys
import time
import numpy as np
import torch
from typing import Optional
from PIL import Image

# 프로젝트 루트를 path에 추가
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


class DeepDefectClassifier:
    """딥러닝 기반 결함 분류 추론기.

    기존 models/inference.py의 DefectClassifier와 동일한 인터페이스를 제공한다.

    Args:
        model_path: .pt 체크포인트 파일 경로.
        model_type: 모델 유형 ("custom_cnn", "resnet18", "resnet18_fe").
        device: 추론 디바이스. None이면 자동 탐지.
    """

    # 클래스명 한글 매핑 (기존 DefectClassifier와 동일)
    CLASS_NAME_KR = {
        "crazing": "균열",
        "inclusion": "개재물",
        "patches": "패치",
        "pitted_surface": "구멍",
        "rolled-in_scale": "압연스케일",
        "scratches": "스크래치",
    }

    # 정렬된 영문 클래스명
    CLASS_NAMES = sorted(CLASS_NAME_KR.keys())

    def __init__(
        self,
        model_path: str,
        model_type: str = "resnet18",
        device: Optional[torch.device] = None,
    ):
        from deep_learning.train_dl import get_device

        self.model_path = model_path
        self.model_type = model_type

        if device is None:
            self.device = get_device()
        else:
            self.device = device

        # 모델 로드
        self.model = self._load_model()
        self.model.to(self.device)
        self.model.eval()

        # 변환 파이프라인 설정
        self._setup_transforms()

        print(f"[DeepDefectClassifier] 모델 로드 완료: {model_type}")
        print(f"[DeepDefectClassifier] 디바이스: {self.device}")

    def _load_model(self) -> torch.nn.Module:
        """체크포인트에서 모델 로드."""
        checkpoint = torch.load(self.model_path, map_location="cpu", weights_only=False)

        if self.model_type == "custom_cnn":
            from deep_learning.models.custom_cnn import CustomCNN
            model = CustomCNN(num_classes=6)
        elif self.model_type == "resnet18":
            from deep_learning.models.resnet_transfer import get_resnet18_finetune
            model = get_resnet18_finetune(num_classes=6)
        elif self.model_type == "resnet18_fe":
            from deep_learning.models.resnet_transfer import get_resnet18_feature_extractor
            model = get_resnet18_feature_extractor(num_classes=6)
        else:
            raise ValueError(f"지원하지 않는 모델 유형: {self.model_type}")

        # state_dict 로드
        if "model_state_dict" in checkpoint:
            model.load_state_dict(checkpoint["model_state_dict"])
        else:
            model.load_state_dict(checkpoint)

        return model

    def _setup_transforms(self):
        """추론용 변환 파이프라인 설정."""
        from deep_learning.augmentation import get_test_transforms

        if self.model_type == "custom_cnn":
            self.num_channels = 1
        else:
            self.num_channels = 3

        self.transform = get_test_transforms(num_channels=self.num_channels)

    def _preprocess_image(self, image: np.ndarray) -> torch.Tensor:
        """numpy 이미지를 모델 입력 텐서로 변환.

        Args:
            image: (H, W) uint8 그레이스케일 이미지.

        Returns:
            (1, C, H, W) 입력 텐서.
        """
        # 200x200으로 리사이즈
        if image.shape != (200, 200):
            import cv2
            image = cv2.resize(image, (200, 200))

        # PIL 변환
        if self.num_channels == 3:
            pil_img = Image.fromarray(
                np.stack([image, image, image], axis=-1), mode="RGB"
            )
        else:
            pil_img = Image.fromarray(image, mode="L")

        # 변환 적용
        tensor = self.transform(pil_img)
        return tensor.unsqueeze(0)  # 배치 차원 추가

    @torch.no_grad()
    def predict(self, image: np.ndarray) -> dict:
        """단일 이미지에 대한 결함 분류.

        Args:
            image: (H, W) uint8 그레이스케일 이미지.

        Returns:
            기존 DefectClassifier와 동일한 키를 가진 딕셔너리:
            - predicted_class: 예측 클래스 한글명
            - predicted_label: 예측 라벨 (정수)
            - confidence: 최대 확률 (0~1)
            - probabilities: {한글클래스명: 확률} 딕셔너리
            - feature_extraction_time_ms: 전처리 시간 (ms)
            - prediction_time_ms: 추론 시간 (ms)
            - total_time_ms: 총 처리 시간 (ms)
        """
        # 전처리
        t0 = time.time()
        input_tensor = self._preprocess_image(image)
        input_tensor = input_tensor.to(self.device)
        feat_time = (time.time() - t0) * 1000

        # 추론
        t0 = time.time()
        output = self.model(input_tensor)
        probs = torch.softmax(output, dim=1).cpu().numpy()[0]
        pred_time = (time.time() - t0) * 1000

        pred_label = int(np.argmax(probs))
        confidence = float(probs[pred_label])

        # 클래스명 매핑
        pred_class_en = self.CLASS_NAMES[pred_label]
        pred_class_kr = self.CLASS_NAME_KR.get(pred_class_en, pred_class_en)

        # 확률 딕셔너리 (한글 키)
        probabilities = {}
        for i, cn in enumerate(self.CLASS_NAMES):
            kr = self.CLASS_NAME_KR.get(cn, cn)
            probabilities[kr] = float(probs[i])

        return {
            "predicted_class": pred_class_kr,
            "predicted_label": pred_label,
            "confidence": confidence,
            "probabilities": probabilities,
            "feature_extraction_time_ms": feat_time,
            "prediction_time_ms": pred_time,
            "total_time_ms": feat_time + pred_time,
        }

    @torch.no_grad()
    def predict_batch(self, images: np.ndarray) -> list[dict]:
        """여러 이미지 일괄 추론.

        Args:
            images: (N, H, W) uint8 그레이스케일 이미지 배열
                    또는 리스트.

        Returns:
            각 이미지에 대한 결과 딕셔너리 리스트.
        """
        results = []
        for img in images:
            results.append(self.predict(img))
        return results

    def get_model_info(self) -> dict:
        """모델 정보 반환."""
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(
            p.numel() for p in self.model.parameters() if p.requires_grad
        )
        return {
            "model_type": self.model_type,
            "model_path": self.model_path,
            "device": str(self.device),
            "num_channels": self.num_channels,
            "total_params": total_params,
            "trainable_params": trainable_params,
            "class_names": self.CLASS_NAMES,
            "class_names_kr": list(self.CLASS_NAME_KR.values()),
        }


if __name__ == "__main__":
    print("=" * 60)
    print("inference_dl.py 스모크 테스트")
    print("=" * 60)

    # 체크포인트 없이 구조 테스트
    # 더미 모델 저장 후 로드 테스트
    import tempfile
    from deep_learning.models.custom_cnn import CustomCNN

    model = CustomCNN(num_classes=6)

    with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
        tmp_path = f.name
        checkpoint = {
            "model_state_dict": model.state_dict(),
            "model_name": "CustomCNN_test",
            "best_accuracy": 0.5,
        }
        torch.save(checkpoint, tmp_path)

    try:
        classifier = DeepDefectClassifier(
            model_path=tmp_path,
            model_type="custom_cnn",
            device=torch.device("cpu"),
        )

        # 단일 이미지 추론
        dummy_image = np.random.randint(0, 255, (200, 200), dtype=np.uint8)
        result = classifier.predict(dummy_image)

        print(f"\n추론 결과:")
        print(f"  predicted_class: {result['predicted_class']}")
        print(f"  predicted_label: {result['predicted_label']}")
        print(f"  confidence: {result['confidence']:.4f}")
        print(f"  total_time_ms: {result['total_time_ms']:.1f}")
        print(f"  확률:")
        for cn, p in sorted(result["probabilities"].items(), key=lambda x: -x[1]):
            print(f"    {cn}: {p:.4f}")

        # 키 일치 확인
        expected_keys = {
            "predicted_class", "predicted_label", "confidence",
            "probabilities", "feature_extraction_time_ms",
            "prediction_time_ms", "total_time_ms",
        }
        assert set(result.keys()) == expected_keys, (
            f"키 불일치: {set(result.keys())} != {expected_keys}"
        )

        # 배치 추론 테스트
        batch_images = np.random.randint(0, 255, (5, 200, 200), dtype=np.uint8)
        batch_results = classifier.predict_batch(batch_images)
        print(f"\n배치 추론 결과: {len(batch_results)}개")

        # 모델 정보
        info = classifier.get_model_info()
        print(f"\n모델 정보:")
        for k, v in info.items():
            print(f"  {k}: {v}")

    finally:
        os.unlink(tmp_path)

    print("\ninference_dl.py 스모크 테스트 완료")
