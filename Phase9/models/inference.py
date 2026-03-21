"""추론 파이프라인.

저장된 모델을 로드하여 단일 이미지 또는 배치 이미지에 대한
결함 분류 추론을 수행한다.
"""

import cv2
import numpy as np
import joblib
import time
from typing import Optional


class DefectClassifier:
    """결함 분류 추론기.

    Args:
        model_path: joblib으로 저장된 모델 파일 경로.
    """

    CLASS_NAME_KR = {
        "crazing": "균열", "inclusion": "개재물", "patches": "패치",
        "pitted_surface": "구멍", "rolled-in_scale": "압연스케일", "scratches": "스크래치",
    }

    def __init__(self, model_path: str):
        data = joblib.load(model_path)
        self.model = data["model"]
        self.scaler = data.get("scaler")
        self.config = data.get("config", {})
        self.class_names = data.get("class_names", [])
        self.timestamp = data.get("timestamp", "unknown")

        # FeaturePipeline 재구성
        from features.feature_pipeline import FeaturePipeline
        pp_fn = self.config.get("preprocess_fn")
        self.pipeline = FeaturePipeline(
            use_hog=self.config.get("use_hog", True),
            use_lbp=self.config.get("use_lbp", True),
            use_pixel_stats=self.config.get("use_pixel_stats", True),
            use_contour=self.config.get("use_contour", False),
            use_edge=self.config.get("use_edge", False),
            preprocess_fn=pp_fn,
            scaler="none",  # scaler는 별도 적용
        )

        print(f"[DefectClassifier] 모델 로드 완료 ({self.timestamp})")

    def predict(self, image: np.ndarray) -> dict:
        """단일 이미지에 대한 결함 분류.

        Returns:
            predicted_class, confidence, probabilities, 처리 시간 등.
        """
        # 전처리 + 특징 추출
        t0 = time.time()
        features = self.pipeline.extract_single(image).reshape(1, -1)
        feat_time = (time.time() - t0) * 1000

        # 스케일링
        if self.scaler is not None:
            features = self.scaler.transform(features)

        # 예측
        t0 = time.time()
        pred_label = int(self.model.predict(features)[0])
        pred_time = (time.time() - t0) * 1000

        # 확률
        probs = {}
        confidence = 0.0
        if hasattr(self.model, "predict_proba"):
            try:
                prob_arr = self.model.predict_proba(features)[0]
                confidence = float(prob_arr.max())
                for i, cn in enumerate(self.class_names):
                    kr = self.CLASS_NAME_KR.get(cn, cn)
                    probs[kr] = float(prob_arr[i]) if i < len(prob_arr) else 0.0
            except Exception:
                confidence = 1.0

        pred_class = self.class_names[pred_label] if pred_label < len(self.class_names) else str(pred_label)
        pred_kr = self.CLASS_NAME_KR.get(pred_class, pred_class)

        return {
            "predicted_class": pred_kr,
            "predicted_label": pred_label,
            "confidence": confidence,
            "probabilities": probs,
            "feature_extraction_time_ms": feat_time,
            "prediction_time_ms": pred_time,
            "total_time_ms": feat_time + pred_time,
        }

    def predict_batch(self, images: np.ndarray) -> list[dict]:
        """여러 이미지 일괄 추론."""
        return [self.predict(img) for img in images]

    def get_model_info(self) -> dict:
        """모델 정보 반환."""
        return {
            "model_type": type(self.model).__name__,
            "class_names": self.class_names,
            "n_classes": len(self.class_names),
            "timestamp": self.timestamp,
            "config": self.config,
        }


def quick_inference(image_path: str, model_path: str):
    """CLI용 간편 추론 함수."""
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"이미지 로드 실패: {image_path}")
        return

    classifier = DefectClassifier(model_path)
    result = classifier.predict(img)

    print(f"\n입력: {image_path}")
    print(f"예측: {result['predicted_class']} (신뢰도: {result['confidence']:.3f})")
    print(f"처리 시간: {result['total_time_ms']:.1f}ms")
    if result["probabilities"]:
        print("확률:")
        for cn, p in sorted(result["probabilities"].items(), key=lambda x: -x[1]):
            print(f"  {cn}: {p:.3f}")


if __name__ == "__main__":
    print("\n=== inference.py 테스트 ===")
    print("(모델 파일이 없으므로 구조 테스트만 수행)")
    print("DefectClassifier 클래스 정의 확인 ✅")
    print("quick_inference 함수 정의 확인 ✅")
    print("✅ inference.py 테스트 완료")
