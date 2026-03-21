"""이상 탐지 추론(Inference) 모듈.

학습된 모델을 로드하여 단일 이미지에 대한 이상 탐지 예측을 수행한다.
지원 모델: autoencoder, padim, isolation_forest, one_class_svm
"""

import os
import sys
import time
from typing import Optional, Dict, Any

import numpy as np
import cv2
import torch
from torchvision import transforms

# 프로젝트 루트를 경로에 추가
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from anomaly_detection.models.autoencoder import (
    ConvAutoencoder,
    compute_anomaly_map,
    compute_anomaly_score,
)
from anomaly_detection.models.padim import PaDiM
from anomaly_detection.models.traditional_ad import IsolationForestAD, OneClassSVMAD


CLASS_NAME_KR = {
    "crazing": "균열", "inclusion": "개재물", "patches": "패치",
    "pitted_surface": "구멍", "rolled-in_scale": "압연스케일", "scratches": "스크래치",
}

SUPPORTED_MODELS = ("autoencoder", "padim", "isolation_forest", "one_class_svm")


class AnomalyDetector:
    """통합 이상 탐지 추론 클래스.

    다양한 이상 탐지 모델을 통일된 인터페이스로 제공한다.

    Args:
        model_path: 저장된 모델 파일 경로.
        model_type: 모델 종류 ("autoencoder", "padim", "isolation_forest", "one_class_svm").
        threshold: 이상 판정 임계값 (None이면 자동 설정).
        device: 연산 디바이스 (AE, PaDiM용).
        in_channels: 입력 채널 (AE용, 기본 1).
        image_size: 입력 이미지 크기 (AE/PaDiM용, 기본 200).
        latent_dim: 잠재 공간 차원 (AE용, 기본 128).
    """

    SUPPORTED_MODELS = list(SUPPORTED_MODELS)

    def __init__(
        self,
        model_path: str,
        model_type: str = "autoencoder",
        threshold: Optional[float] = None,
        device: Optional[torch.device] = None,
        in_channels: int = 1,
        image_size: int = 200,
        latent_dim: int = 128,
    ) -> None:
        if model_type not in SUPPORTED_MODELS:
            raise ValueError(f"지원하지 않는 모델: {model_type}. 가능: {SUPPORTED_MODELS}")

        if not os.path.isfile(model_path):
            raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {model_path}")

        self.model_path = model_path
        self.model_type = model_type
        self.threshold = threshold
        self.in_channels = in_channels
        self.image_size = image_size

        # 디바이스 설정
        if device is not None:
            self.device = device
        elif torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")

        # 모델 로드
        self.model = None
        self._load_model(in_channels, image_size, latent_dim)

        # 기본 임계값
        if self.threshold is None:
            self.threshold = self._default_threshold()

        # 이미지 전처리 (AE, PaDiM용)
        t_list = [transforms.Resize((image_size, image_size)), transforms.ToTensor()]
        self.transform = transforms.Compose(t_list)

        print(f"[AnomalyDetector] 모델 로드 완료: {model_type}")
        print(f"  경로: {model_path}")
        print(f"  디바이스: {self.device}")
        print(f"  임계값: {self.threshold}")

    def _load_model(self, in_channels: int, image_size: int, latent_dim: int) -> None:
        """모델을 로드한다."""
        if self.model_type == "autoencoder":
            self.model = ConvAutoencoder(
                in_channels=in_channels,
                image_size=image_size,
                latent_dim=latent_dim,
            )
            state_dict = torch.load(self.model_path, map_location=self.device, weights_only=True)
            self.model.load_state_dict(state_dict)
            self.model = self.model.to(self.device)
            self.model.eval()

        elif self.model_type == "padim":
            self.model = PaDiM.load(self.model_path)

        elif self.model_type == "isolation_forest":
            self.model = IsolationForestAD.load(self.model_path)

        elif self.model_type == "one_class_svm":
            self.model = OneClassSVMAD.load(self.model_path)

    def _default_threshold(self) -> float:
        """모델 유형별 기본 임계값을 반환한다."""
        defaults = {
            "autoencoder": 0.01,
            "padim": 10.0,
            "isolation_forest": 0.0,
            "one_class_svm": 0.0,
        }
        return defaults.get(self.model_type, 0.5)

    def _preprocess_image(self, image: np.ndarray) -> torch.Tensor:
        """numpy 이미지를 텐서로 변환한다.

        Args:
            image: (H, W) uint8 그레이스케일 또는 (H, W, 3) BGR 이미지.

        Returns:
            (1, C, H, W) float 텐서.
        """
        from PIL import Image as PILImage

        if image.ndim == 3 and image.shape[2] == 3:
            if self.in_channels == 1:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        pil_img = PILImage.fromarray(image)
        tensor = self.transform(pil_img)
        return tensor.unsqueeze(0)

    def predict(self, image) -> Dict[str, Any]:
        """단일 이미지에 대해 이상 탐지 예측을 수행한다.

        Args:
            image: (H, W) uint8 그레이스케일 또는 (H, W, 3) 컬러 이미지.
                   또는 파일 경로 문자열.

        Returns:
            dict:
                is_anomaly (bool): 이상 여부.
                anomaly_score (float): 이상 점수.
                anomaly_map (np.ndarray or None): 이상 맵 (AE, PaDiM만).
                confidence (float): 신뢰도 (0~1).
                total_time_ms (float): 추론 시간 (ms).
        """
        t0 = time.time()

        # 파일 경로인 경우 이미지 로드
        if isinstance(image, str):
            if not os.path.isfile(image):
                raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image}")
            image = cv2.imread(
                image,
                cv2.IMREAD_GRAYSCALE if self.in_channels == 1 else cv2.IMREAD_COLOR,
            )
            if image is None:
                raise ValueError("이미지 로드 실패")

        anomaly_map = None

        if self.model_type == "autoencoder":
            img_tensor = self._preprocess_image(image).to(self.device)
            with torch.no_grad():
                recon = self.model(img_tensor)
            anomaly_map = compute_anomaly_map(img_tensor[0].cpu(), recon[0].cpu())
            anomaly_score = compute_anomaly_score(anomaly_map)
            is_anomaly = anomaly_score > self.threshold

        elif self.model_type == "padim":
            img_tensor = self._preprocess_image(image)
            anomaly_score, anomaly_map = self.model.predict(
                img_tensor.squeeze(0), device=self.device
            )
            is_anomaly = anomaly_score > self.threshold

        elif self.model_type == "isolation_forest":
            result = self.model.predict(image)
            anomaly_score = result["anomaly_score"]
            is_anomaly = result["is_anomaly"]

        elif self.model_type == "one_class_svm":
            result = self.model.predict(image)
            anomaly_score = result["anomaly_score"]
            is_anomaly = result["is_anomaly"]

        else:
            raise ValueError(f"지원하지 않는 모델: {self.model_type}")

        # 신뢰도 계산 (시그모이드 기반)
        if self.threshold != 0:
            ratio = anomaly_score / max(abs(self.threshold), 1e-8)
        else:
            ratio = anomaly_score
        confidence = float(1.0 / (1.0 + np.exp(-2.0 * (ratio - 1.0))))

        elapsed_ms = (time.time() - t0) * 1000

        return {
            "is_anomaly": bool(is_anomaly),
            "anomaly_score": float(anomaly_score),
            "anomaly_map": anomaly_map,
            "confidence": float(confidence),
            "total_time_ms": float(elapsed_ms),
        }

    def predict_batch(self, images: list) -> list:
        """여러 이미지에 대해 배치 예측을 수행한다.

        Args:
            images: 이미지 리스트 (numpy 배열 또는 파일 경로).

        Returns:
            예측 결과 딕셔너리 리스트.
        """
        results = []
        for i, img in enumerate(images):
            try:
                result = self.predict(img)
                results.append(result)
            except Exception as e:
                print(f"[경고] 이미지 {i} 예측 실패: {e}")
                results.append({
                    "is_anomaly": None,
                    "anomaly_score": None,
                    "anomaly_map": None,
                    "confidence": None,
                    "total_time_ms": None,
                    "error": str(e),
                })

            if (i + 1) % 50 == 0:
                print(f"  예측 진행: {i + 1}/{len(images)}")

        return results

    def get_model_info(self) -> dict:
        """모델 메타데이터 반환."""
        return {
            "model_type": self.model_type,
            "model_path": self.model_path,
            "device": str(self.device),
            "threshold": self.threshold,
        }


# ---------------------------------------------------------------------------
# 스모크 테스트
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import tempfile
    import shutil

    print("=" * 60)
    print("inference_ad.py 스모크 테스트")
    print("=" * 60)

    device_str = "cpu"
    if torch.backends.mps.is_available():
        device_str = "mps"
    elif torch.cuda.is_available():
        device_str = "cuda"
    device = torch.device(device_str)
    print(f"Device: {device}")

    tmpdir = tempfile.mkdtemp()

    try:
        # 1. Autoencoder 테스트
        print("\n--- Autoencoder 추론 테스트 ---")
        ae = ConvAutoencoder(in_channels=1, image_size=200, latent_dim=64)
        ae_path = os.path.join(tmpdir, "ae.pth")
        torch.save(ae.state_dict(), ae_path)

        detector_ae = AnomalyDetector(
            ae_path, model_type="autoencoder",
            device=device, in_channels=1, image_size=200, latent_dim=64,
        )

        dummy_img = np.random.randint(0, 255, (200, 200), dtype=np.uint8)
        result = detector_ae.predict(dummy_img)
        print(f"  is_anomaly={result['is_anomaly']}, score={result['anomaly_score']:.6f}, "
              f"confidence={result['confidence']:.4f}, time={result['total_time_ms']:.1f}ms")
        print(f"  anomaly_map shape={result['anomaly_map'].shape}")

        # 2. PaDiM 테스트
        print("\n--- PaDiM 추론 테스트 ---")
        from torch.utils.data import TensorDataset, DataLoader
        dummy_data = torch.randn(10, 1, 200, 200).clamp(0, 1)
        dummy_ds = TensorDataset(dummy_data, torch.zeros(10))
        dummy_loader = DataLoader(dummy_ds, batch_size=5)

        padim = PaDiM(n_selected_features=30, image_size=200)
        padim.fit(dummy_loader, device=device)
        padim_path = os.path.join(tmpdir, "padim.pkl")
        padim.save(padim_path)

        detector_padim = AnomalyDetector(
            padim_path, model_type="padim",
            device=device, image_size=200,
        )
        result = detector_padim.predict(dummy_img)
        print(f"  is_anomaly={result['is_anomaly']}, score={result['anomaly_score']:.4f}, "
              f"confidence={result['confidence']:.4f}, time={result['total_time_ms']:.1f}ms")

        # 3. Isolation Forest 테스트
        print("\n--- Isolation Forest 추론 테스트 ---")
        normal_imgs = [np.random.randint(100, 200, (200, 200), dtype=np.uint8) for _ in range(20)]
        iforest = IsolationForestAD(image_size=128)
        iforest.fit(normal_imgs)
        if_path = os.path.join(tmpdir, "iforest.pkl")
        iforest.save(if_path)

        detector_if = AnomalyDetector(if_path, model_type="isolation_forest")
        result = detector_if.predict(dummy_img)
        print(f"  is_anomaly={result['is_anomaly']}, score={result['anomaly_score']:.4f}, "
              f"confidence={result['confidence']:.4f}, time={result['total_time_ms']:.1f}ms")

        # 4. One-Class SVM 테스트
        print("\n--- One-Class SVM 추론 테스트 ---")
        ocsvm = OneClassSVMAD(image_size=128)
        ocsvm.fit(normal_imgs)
        svm_path = os.path.join(tmpdir, "ocsvm.pkl")
        ocsvm.save(svm_path)

        detector_svm = AnomalyDetector(svm_path, model_type="one_class_svm")
        result = detector_svm.predict(dummy_img)
        print(f"  is_anomaly={result['is_anomaly']}, score={result['anomaly_score']:.4f}, "
              f"confidence={result['confidence']:.4f}, time={result['total_time_ms']:.1f}ms")

        # 5. 배치 예측 테스트
        print("\n--- 배치 예측 테스트 ---")
        batch_imgs = [np.random.randint(0, 255, (200, 200), dtype=np.uint8) for _ in range(5)]
        batch_results = detector_if.predict_batch(batch_imgs)
        print(f"  배치 결과 수: {len(batch_results)}")
        for i, r in enumerate(batch_results):
            print(f"    [{i}] anomaly={r['is_anomaly']}, score={r['anomaly_score']:.4f}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print("\n[PASS] inference_ad.py 스모크 테스트 완료")
