"""전통적 머신러닝 기반 이상 탐지 모델.

HOG(Histogram of Oriented Gradients) 특징을 추출하여
Isolation Forest 및 One-Class SVM으로 이상 탐지를 수행한다.
"""

import os
import time
import pickle
from typing import Optional, Dict, Any, Union

import numpy as np
import cv2
from skimage.feature import hog
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler


def _extract_hog_features(
    image: np.ndarray,
    image_size: int = 128,
    orientations: int = 9,
    pixels_per_cell: tuple = (8, 8),
    cells_per_block: tuple = (2, 2),
) -> np.ndarray:
    """이미지에서 HOG 특징을 추출한다.

    Args:
        image: (H, W) uint8 그레이스케일 이미지 또는 (H, W, C) 컬러 이미지.
        image_size: 리사이즈 크기.
        orientations: HOG 방향 수.
        pixels_per_cell: 셀 크기.
        cells_per_block: 블록 크기.

    Returns:
        1-D HOG 특징 벡터.
    """
    # 그레이스케일 변환
    if image.ndim == 3:
        if image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            image = image[:, :, 0]

    # 리사이즈
    if image.shape[0] != image_size or image.shape[1] != image_size:
        image = cv2.resize(image, (image_size, image_size))

    # HOG 추출
    features = hog(
        image,
        orientations=orientations,
        pixels_per_cell=pixels_per_cell,
        cells_per_block=cells_per_block,
        feature_vector=True,
    )

    return features.astype(np.float32)


def _images_to_hog_features(
    images: Union[list, np.ndarray],
    image_size: int = 128,
) -> np.ndarray:
    """이미지 리스트/배열에서 HOG 특징 행렬을 추출한다.

    Args:
        images: 이미지 리스트 또는 (N, H, W) / (N, H, W, C) 배열.
        image_size: HOG 추출 전 리사이즈 크기.

    Returns:
        (N, D) HOG 특징 행렬.
    """
    features = []
    for img in images:
        if isinstance(img, np.ndarray):
            feat = _extract_hog_features(img, image_size=image_size)
        else:
            raise TypeError(f"지원하지 않는 이미지 타입: {type(img)}")
        features.append(feat)

    return np.array(features, dtype=np.float32)


class IsolationForestAD:
    """Isolation Forest 기반 이상 탐지.

    HOG 특징을 추출하여 Isolation Forest로 이상 탐지를 수행한다.

    Args:
        contamination: 이상치 비율 추정값 (기본 0.1).
        n_estimators: 트리 수 (기본 100).
        random_state: 랜덤 시드.
        image_size: HOG 추출용 리사이즈 크기.
    """

    def __init__(
        self,
        contamination: float = 0.1,
        n_estimators: int = 100,
        random_state: int = 42,
        image_size: int = 128,
    ) -> None:
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.image_size = image_size

        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=random_state,
            n_jobs=-1,
        )
        self.scaler = StandardScaler()
        self._fitted = False

    def fit(self, images_normal: Union[list, np.ndarray]) -> None:
        """정상 이미지로 모델을 학습한다.

        Args:
            images_normal: 정상 이미지 리스트 또는 (N, H, W) 배열.
        """
        print(f"[IsolationForest] HOG 특징 추출 중 ({len(images_normal)}장)...")
        t0 = time.time()

        features = _images_to_hog_features(images_normal, image_size=self.image_size)
        print(f"  특징 shape: {features.shape}")

        # 정규화
        features_scaled = self.scaler.fit_transform(features)

        # 학습
        print(f"[IsolationForest] 모델 학습 중...")
        self.model.fit(features_scaled)
        self._fitted = True

        elapsed = time.time() - t0
        print(f"[IsolationForest] 학습 완료 ({elapsed:.1f}초)")

    def predict(self, image: np.ndarray) -> Dict[str, Any]:
        """단일 이미지에 대해 이상 탐지를 수행한다.

        Args:
            image: (H, W) uint8 그레이스케일 이미지 또는 (H, W, C) 컬러 이미지.

        Returns:
            dict: is_anomaly (bool), anomaly_score (float), total_time_ms (float).
        """
        if not self._fitted:
            raise RuntimeError("모델이 학습되지 않았습니다. fit()을 먼저 호출하세요.")

        t0 = time.time()

        feat = _extract_hog_features(image, image_size=self.image_size)
        feat_scaled = self.scaler.transform(feat.reshape(1, -1))

        # sklearn IF: decision_function < 0 이면 이상
        raw_score = self.model.decision_function(feat_scaled)[0]
        prediction = self.model.predict(feat_scaled)[0]

        is_anomaly = prediction == -1
        # 점수 반전: 높을수록 이상 (기존 sklearn은 낮을수록 이상)
        anomaly_score = -float(raw_score)

        elapsed_ms = (time.time() - t0) * 1000

        return {
            "is_anomaly": bool(is_anomaly),
            "anomaly_score": anomaly_score,
            "total_time_ms": elapsed_ms,
        }

    def predict_batch(self, images: Union[list, np.ndarray]) -> Dict[str, Any]:
        """여러 이미지에 대해 배치 예측을 수행한다.

        Args:
            images: 이미지 리스트 또는 (N, H, W) 배열.

        Returns:
            dict: is_anomaly (list), anomaly_scores (np.ndarray), total_time_ms (float).
        """
        if not self._fitted:
            raise RuntimeError("모델이 학습되지 않았습니다. fit()을 먼저 호출하세요.")

        t0 = time.time()

        features = _images_to_hog_features(images, image_size=self.image_size)
        features_scaled = self.scaler.transform(features)

        raw_scores = self.model.decision_function(features_scaled)
        predictions = self.model.predict(features_scaled)

        is_anomaly = (predictions == -1).tolist()
        anomaly_scores = -raw_scores.astype(float)

        elapsed_ms = (time.time() - t0) * 1000

        return {
            "is_anomaly": is_anomaly,
            "anomaly_scores": anomaly_scores,
            "total_time_ms": elapsed_ms,
        }

    def save(self, path: str) -> None:
        """모델 저장."""
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        state = {
            "model": self.model,
            "scaler": self.scaler,
            "contamination": self.contamination,
            "n_estimators": self.n_estimators,
            "random_state": self.random_state,
            "image_size": self.image_size,
            "fitted": self._fitted,
        }
        with open(path, "wb") as f:
            pickle.dump(state, f)
        print(f"[IsolationForest] 저장 완료: {path}")

    @classmethod
    def load(cls, path: str) -> "IsolationForestAD":
        """모델 로드."""
        with open(path, "rb") as f:
            state = pickle.load(f)
        obj = cls(
            contamination=state["contamination"],
            n_estimators=state["n_estimators"],
            random_state=state["random_state"],
            image_size=state["image_size"],
        )
        obj.model = state["model"]
        obj.scaler = state["scaler"]
        obj._fitted = state["fitted"]
        print(f"[IsolationForest] 로드 완료: {path}")
        return obj


class OneClassSVMAD:
    """One-Class SVM 기반 이상 탐지.

    HOG 특징을 추출하여 One-Class SVM으로 이상 탐지를 수행한다.

    Args:
        kernel: SVM 커널 (기본 "rbf").
        nu: 이상치 비율 상한 (기본 0.1).
        gamma: RBF 커널 감마 (기본 "scale").
        image_size: HOG 추출용 리사이즈 크기.
    """

    def __init__(
        self,
        kernel: str = "rbf",
        nu: float = 0.1,
        gamma: str = "scale",
        image_size: int = 128,
    ) -> None:
        self.kernel = kernel
        self.nu = nu
        self.gamma = gamma
        self.image_size = image_size

        self.model = OneClassSVM(
            kernel=kernel,
            nu=nu,
            gamma=gamma,
        )
        self.scaler = StandardScaler()
        self._fitted = False

    def fit(self, images_normal: Union[list, np.ndarray]) -> None:
        """정상 이미지로 모델을 학습한다.

        Args:
            images_normal: 정상 이미지 리스트 또는 (N, H, W) 배열.
        """
        print(f"[OneClassSVM] HOG 특징 추출 중 ({len(images_normal)}장)...")
        t0 = time.time()

        features = _images_to_hog_features(images_normal, image_size=self.image_size)
        print(f"  특징 shape: {features.shape}")

        # 정규화
        features_scaled = self.scaler.fit_transform(features)

        # 학습
        print(f"[OneClassSVM] 모델 학습 중...")
        self.model.fit(features_scaled)
        self._fitted = True

        elapsed = time.time() - t0
        print(f"[OneClassSVM] 학습 완료 ({elapsed:.1f}초)")

    def predict(self, image: np.ndarray) -> Dict[str, Any]:
        """단일 이미지에 대해 이상 탐지를 수행한다.

        Args:
            image: (H, W) uint8 그레이스케일 이미지 또는 (H, W, C) 컬러 이미지.

        Returns:
            dict: is_anomaly (bool), anomaly_score (float), total_time_ms (float).
        """
        if not self._fitted:
            raise RuntimeError("모델이 학습되지 않았습니다. fit()을 먼저 호출하세요.")

        t0 = time.time()

        feat = _extract_hog_features(image, image_size=self.image_size)
        feat_scaled = self.scaler.transform(feat.reshape(1, -1))

        raw_score = self.model.decision_function(feat_scaled)[0]
        prediction = self.model.predict(feat_scaled)[0]

        is_anomaly = prediction == -1
        anomaly_score = -float(raw_score)

        elapsed_ms = (time.time() - t0) * 1000

        return {
            "is_anomaly": bool(is_anomaly),
            "anomaly_score": anomaly_score,
            "total_time_ms": elapsed_ms,
        }

    def predict_batch(self, images: Union[list, np.ndarray]) -> Dict[str, Any]:
        """여러 이미지에 대해 배치 예측을 수행한다.

        Args:
            images: 이미지 리스트 또는 (N, H, W) 배열.

        Returns:
            dict: is_anomaly (list), anomaly_scores (np.ndarray), total_time_ms (float).
        """
        if not self._fitted:
            raise RuntimeError("모델이 학습되지 않았습니다. fit()을 먼저 호출하세요.")

        t0 = time.time()

        features = _images_to_hog_features(images, image_size=self.image_size)
        features_scaled = self.scaler.transform(features)

        raw_scores = self.model.decision_function(features_scaled)
        predictions = self.model.predict(features_scaled)

        is_anomaly = (predictions == -1).tolist()
        anomaly_scores = -raw_scores.astype(float)

        elapsed_ms = (time.time() - t0) * 1000

        return {
            "is_anomaly": is_anomaly,
            "anomaly_scores": anomaly_scores,
            "total_time_ms": elapsed_ms,
        }

    def save(self, path: str) -> None:
        """모델 저장."""
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        state = {
            "model": self.model,
            "scaler": self.scaler,
            "kernel": self.kernel,
            "nu": self.nu,
            "gamma": self.gamma,
            "image_size": self.image_size,
            "fitted": self._fitted,
        }
        with open(path, "wb") as f:
            pickle.dump(state, f)
        print(f"[OneClassSVM] 저장 완료: {path}")

    @classmethod
    def load(cls, path: str) -> "OneClassSVMAD":
        """모델 로드."""
        with open(path, "rb") as f:
            state = pickle.load(f)
        obj = cls(
            kernel=state["kernel"],
            nu=state["nu"],
            gamma=state["gamma"],
            image_size=state["image_size"],
        )
        obj.model = state["model"]
        obj.scaler = state["scaler"]
        obj._fitted = state["fitted"]
        print(f"[OneClassSVM] 로드 완료: {path}")
        return obj


# ---------------------------------------------------------------------------
# 스모크 테스트
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Traditional AD 스모크 테스트")
    print("=" * 60)

    # 더미 이미지 생성
    np.random.seed(42)
    normal_images = [
        np.random.randint(100, 200, (200, 200), dtype=np.uint8)
        for _ in range(30)
    ]
    anomaly_images = [
        np.random.randint(0, 100, (200, 200), dtype=np.uint8)
        for _ in range(10)
    ]

    # --- Isolation Forest ---
    print("\n--- Isolation Forest ---")
    iforest = IsolationForestAD(contamination=0.1, image_size=128)
    iforest.fit(normal_images)

    result_normal = iforest.predict(normal_images[0])
    print(f"정상 이미지: {result_normal}")

    result_anomaly = iforest.predict(anomaly_images[0])
    print(f"이상 이미지: {result_anomaly}")

    batch_result = iforest.predict_batch(anomaly_images[:5])
    print(f"배치 예측: is_anomaly={batch_result['is_anomaly']}, "
          f"time={batch_result['total_time_ms']:.1f}ms")

    # 저장/로드
    iforest.save("/tmp/iforest_test.pkl")
    iforest_loaded = IsolationForestAD.load("/tmp/iforest_test.pkl")
    r2 = iforest_loaded.predict(normal_images[0])
    print(f"로드 후 예측: {r2}")
    os.remove("/tmp/iforest_test.pkl")

    # --- One-Class SVM ---
    print("\n--- One-Class SVM ---")
    ocsvm = OneClassSVMAD(nu=0.1, image_size=128)
    ocsvm.fit(normal_images)

    result_normal = ocsvm.predict(normal_images[0])
    print(f"정상 이미지: {result_normal}")

    result_anomaly = ocsvm.predict(anomaly_images[0])
    print(f"이상 이미지: {result_anomaly}")

    batch_result = ocsvm.predict_batch(anomaly_images[:5])
    print(f"배치 예측: is_anomaly={batch_result['is_anomaly']}, "
          f"time={batch_result['total_time_ms']:.1f}ms")

    # 저장/로드
    ocsvm.save("/tmp/ocsvm_test.pkl")
    ocsvm_loaded = OneClassSVMAD.load("/tmp/ocsvm_test.pkl")
    r2 = ocsvm_loaded.predict(normal_images[0])
    print(f"로드 후 예측: {r2}")
    os.remove("/tmp/ocsvm_test.pkl")

    print("\n[PASS] Traditional AD 스모크 테스트 완료")
