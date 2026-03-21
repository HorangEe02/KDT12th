"""
2단계 검수 파이프라인

Stage 1: 이상 탐지 (Gate) — 정상/비정상 판단
Stage 2: 결함 분류 (Type) — 비정상이면 6종 결함 유형 특정

파이프라인 흐름:
  입력 이미지
    → Stage 1: Autoencoder/PaDiM으로 이상 점수 계산
       ├── 정상 (점수 < 임계값) → "통과" 출력
       └── 비정상 (점수 ≥ 임계값) → Stage 2로 전달
    → Stage 2: ResNet-18 / SVM으로 6종 결함 분류
       → 결함 유형 + 신뢰도 출력
"""

import os
import sys
import time
import cv2
import numpy as np
import torch
from typing import Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TwoStagePipeline:
    """2단계 검수 파이프라인"""

    KR_MAP = {
        "crazing": "균열", "inclusion": "개재물", "patches": "패치",
        "pitted_surface": "구멍", "rolled-in_scale": "압연스케일",
        "scratches": "스크래치",
    }

    def __init__(self,
                 anomaly_model_path: str = None,
                 anomaly_model_type: str = "autoencoder",
                 classifier_model_path: str = None,
                 classifier_type: str = "resnet18",
                 anomaly_threshold: float = None,
                 device: str = None):
        """
        Args:
            anomaly_model_path: Stage 1 모델 경로
            anomaly_model_type: "autoencoder" | "padim" | "isolation_forest"
            classifier_model_path: Stage 2 모델 경로
            classifier_type: "resnet18" | "svm" | "custom_cnn"
            anomaly_threshold: 이상 판정 임계값 (None이면 자동 설정)
            device: "mps" | "cuda" | "cpu"
        """
        if device is None:
            if torch.backends.mps.is_available():
                self.device = torch.device("mps")
            elif torch.cuda.is_available():
                self.device = torch.device("cuda")
            else:
                self.device = torch.device("cpu")
        else:
            self.device = torch.device(device)

        self.anomaly_model_type = anomaly_model_type
        self.classifier_type = classifier_type
        self.anomaly_threshold = anomaly_threshold
        self.stage1_model = None
        self.stage2_model = None

        # 모델 로드
        if anomaly_model_path and os.path.exists(anomaly_model_path):
            self._load_anomaly_model(anomaly_model_path)
        if classifier_model_path and os.path.exists(classifier_model_path):
            self._load_classifier(classifier_model_path)

    def _load_anomaly_model(self, path: str):
        """Stage 1 이상 탐지 모델 로드"""
        if self.anomaly_model_type == "autoencoder":
            from anomaly_detection.models.autoencoder import ConvAutoencoder
            ckpt = torch.load(path, map_location="cpu", weights_only=False)
            model = ConvAutoencoder(
                in_channels=ckpt.get("in_channels", 1),
                image_size=ckpt.get("image_size", 200),
                latent_dim=ckpt.get("latent_dim", 128),
            )
            model.load_state_dict(ckpt["model_state_dict"])
            model.to(self.device)
            model.eval()
            self.stage1_model = model

        elif self.anomaly_model_type == "padim":
            from anomaly_detection.models.padim import PaDiM
            model = PaDiM()
            model.load(path)
            self.stage1_model = model

        elif self.anomaly_model_type == "isolation_forest":
            from anomaly_detection.models.traditional_ad import IsolationForestAD
            model = IsolationForestAD()
            model.load(path)
            self.stage1_model = model

    def _load_classifier(self, path: str):
        """Stage 2 결함 분류 모델 로드"""
        if self.classifier_type == "resnet18":
            from deep_learning.models.resnet_transfer import get_resnet18_finetune
            ckpt = torch.load(path, map_location="cpu", weights_only=False)
            model = get_resnet18_finetune(num_classes=6)
            model.load_state_dict(ckpt["model_state_dict"])
            model.to(self.device)
            model.eval()
            self.stage2_model = model

        elif self.classifier_type == "svm":
            import joblib
            self.stage2_model = joblib.load(path)

    def predict_anomaly(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Stage 1: 이상 탐지

        Returns:
            {
                "anomaly_score": float,
                "is_anomaly": bool,
                "anomaly_map": np.ndarray (있으면),
                "stage1_time_ms": float,
            }
        """
        t0 = time.time()

        if self.stage1_model is None:
            return {"anomaly_score": 0.0, "is_anomaly": False, "stage1_time_ms": 0}

        if self.anomaly_model_type == "autoencoder":
            from anomaly_detection.models.autoencoder import compute_anomaly_map, compute_anomaly_score

            if image.shape[:2] != (200, 200):
                image = cv2.resize(image, (200, 200))

            img_tensor = torch.FloatTensor(image).unsqueeze(0).unsqueeze(0) / 255.0
            img_tensor = img_tensor.to(self.device)

            with torch.no_grad():
                recon = self.stage1_model(img_tensor)

            orig_np = img_tensor[0][0].cpu().numpy()
            recon_np = recon[0][0].cpu().numpy()
            amap = compute_anomaly_map(orig_np, recon_np)
            score = compute_anomaly_score(amap)

            threshold = self.anomaly_threshold or 0.015
            result = {
                "anomaly_score": float(score),
                "is_anomaly": score >= threshold,
                "anomaly_map": amap,
                "threshold": threshold,
                "stage1_time_ms": (time.time() - t0) * 1000,
            }

        elif self.anomaly_model_type == "padim":
            img_tensor = torch.FloatTensor(image).unsqueeze(0).unsqueeze(0) / 255.0
            score, amap = self.stage1_model.predict(img_tensor, device=self.device)
            threshold = self.anomaly_threshold or 5.0
            result = {
                "anomaly_score": float(score),
                "is_anomaly": score >= threshold,
                "anomaly_map": amap,
                "threshold": threshold,
                "stage1_time_ms": (time.time() - t0) * 1000,
            }

        elif self.anomaly_model_type == "isolation_forest":
            r = self.stage1_model.predict(image)
            threshold = self.anomaly_threshold or 0.0
            result = {
                "anomaly_score": float(r["anomaly_score"]),
                "is_anomaly": r["anomaly_score"] >= threshold,
                "anomaly_map": None,
                "threshold": threshold,
                "stage1_time_ms": (time.time() - t0) * 1000,
            }

        return result

    def predict_defect_type(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Stage 2: 결함 유형 분류

        Returns:
            {
                "predicted_class": str (영문),
                "predicted_kr": str (한글),
                "confidence": float,
                "probabilities": dict,
                "stage2_time_ms": float,
            }
        """
        t0 = time.time()
        class_names = ["crazing", "inclusion", "patches",
                       "pitted_surface", "rolled-in_scale", "scratches"]

        if self.stage2_model is None:
            return {"predicted_class": "unknown", "predicted_kr": "알 수 없음",
                    "confidence": 0.0, "stage2_time_ms": 0}

        if self.classifier_type == "resnet18":
            if image.shape[:2] != (224, 224):
                img_resized = cv2.resize(image, (224, 224))
            else:
                img_resized = image

            # 3채널로 변환
            img_3ch = np.stack([img_resized] * 3, axis=0).astype(np.float32) / 255.0
            img_tensor = torch.FloatTensor(img_3ch).unsqueeze(0).to(self.device)

            with torch.no_grad():
                output = self.stage2_model(img_tensor)
                probs = torch.softmax(output.cpu(), dim=1)[0].numpy()

            pred_idx = int(probs.argmax())
            pred_class = class_names[pred_idx]

            result = {
                "predicted_class": pred_class,
                "predicted_kr": self.KR_MAP.get(pred_class, pred_class),
                "confidence": float(probs[pred_idx]),
                "probabilities": {self.KR_MAP.get(c, c): float(probs[i])
                                  for i, c in enumerate(class_names)},
                "stage2_time_ms": (time.time() - t0) * 1000,
            }

        elif self.classifier_type == "svm":
            from features.hog_features import extract_hog
            from features.lbp_features import extract_lbp_histogram

            if image.shape[:2] != (200, 200):
                image = cv2.resize(image, (200, 200))

            hog_feat = extract_hog(image)
            lbp_feat = extract_lbp_histogram(image)
            feat = np.concatenate([hog_feat, lbp_feat]).reshape(1, -1)

            pred_idx = int(self.stage2_model.predict(feat)[0])
            pred_class = class_names[pred_idx]

            probs_arr = self.stage2_model.predict_proba(feat)[0] \
                if hasattr(self.stage2_model, "predict_proba") else np.zeros(6)

            result = {
                "predicted_class": pred_class,
                "predicted_kr": self.KR_MAP.get(pred_class, pred_class),
                "confidence": float(max(probs_arr)) if probs_arr.sum() > 0 else 0.0,
                "probabilities": {self.KR_MAP.get(c, c): float(probs_arr[i])
                                  for i, c in enumerate(class_names)},
                "stage2_time_ms": (time.time() - t0) * 1000,
            }

        return result

    def predict(self, image: np.ndarray) -> Dict[str, Any]:
        """
        전체 2단계 파이프라인 실행

        Returns:
            {
                "verdict": "정상" | "결함 감지",
                "stage1": {...},  # 이상 탐지 결과
                "stage2": {...},  # 결함 분류 결과 (이상일 때만)
                "total_time_ms": float,
            }
        """
        t0 = time.time()

        # Stage 1: 이상 탐지
        stage1 = self.predict_anomaly(image)

        result = {
            "stage1": stage1,
            "stage2": None,
        }

        if stage1["is_anomaly"]:
            # Stage 2: 결함 분류
            stage2 = self.predict_defect_type(image)
            result["stage2"] = stage2
            result["verdict"] = "결함 감지"
            result["defect_type"] = stage2["predicted_kr"]
            result["confidence"] = stage2["confidence"]
        else:
            result["verdict"] = "정상"
            result["defect_type"] = None
            result["confidence"] = 1.0 - stage1["anomaly_score"]

        result["total_time_ms"] = (time.time() - t0) * 1000
        return result

    def evaluate_on_dataset(self, test_loader, verbose: bool = True) -> Dict[str, Any]:
        """테스트 데이터셋으로 전체 파이프라인 평가"""
        from sklearn.metrics import roc_auc_score, accuracy_score, f1_score

        all_scores = []
        all_labels = []
        all_verdicts = []
        stage2_preds = []
        stage2_true_types = []

        for imgs, labels in test_loader:
            for i in range(len(labels)):
                img_np = (imgs[i][0].numpy() * 255).astype(np.uint8)
                label = labels[i].item()

                result = self.predict(img_np)
                all_scores.append(result["stage1"]["anomaly_score"])
                all_labels.append(label)
                all_verdicts.append(1 if result["verdict"] == "결함 감지" else 0)

                if label == 1 and result["stage2"] is not None:
                    stage2_preds.append(result["stage2"]["predicted_class"])
                    defect_type = test_loader.dataset.get_defect_type(
                        sum(len(b[1]) for b in list(zip(range(len(all_labels)-1), [None]*len(all_labels)))[:0]) + i
                    ) if hasattr(test_loader.dataset, "get_defect_type") else "unknown"

        all_scores = np.array(all_scores)
        all_labels = np.array(all_labels)

        # AUROC
        try:
            auroc = roc_auc_score(all_labels, all_scores)
        except ValueError:
            auroc = 0.0

        # 이진 정확도
        all_verdicts = np.array(all_verdicts)
        binary_acc = accuracy_score(all_labels, all_verdicts)
        binary_f1 = f1_score(all_labels, all_verdicts, zero_division=0)

        result = {
            "auroc": auroc,
            "binary_accuracy": binary_acc,
            "binary_f1": binary_f1,
            "n_total": len(all_labels),
            "n_normal": int((all_labels == 0).sum()),
            "n_anomaly": int((all_labels == 1).sum()),
            "scores": all_scores,
            "labels": all_labels,
        }

        if verbose:
            print(f"=== 2단계 파이프라인 평가 ===")
            print(f"AUROC: {auroc:.4f}")
            print(f"이진 Accuracy: {binary_acc:.4f}")
            print(f"이진 F1: {binary_f1:.4f}")
            print(f"테스트: 정상 {result['n_normal']}장 + 결함 {result['n_anomaly']}장")

        return result


def build_default_pipeline(project_root: str) -> TwoStagePipeline:
    """기본 설정으로 2단계 파이프라인 생성"""
    return TwoStagePipeline(
        anomaly_model_path=os.path.join(project_root, "outputs", "models_ad", "autoencoder.pt"),
        anomaly_model_type="autoencoder",
        classifier_model_path=os.path.join(project_root, "outputs", "models_dl", "resnet18_finetune.pt"),
        classifier_type="resnet18",
    )


if __name__ == "__main__":
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    pipeline = build_default_pipeline(PROJECT_ROOT)
    print(f"Stage 1: {pipeline.anomaly_model_type}")
    print(f"Stage 2: {pipeline.classifier_type}")
    print(f"Device: {pipeline.device}")

    # 테스트: 결함 이미지
    test_img_dir = os.path.join(PROJECT_ROOT, "data", "NEU-DET", "train", "images", "scratches")
    test_files = sorted(os.listdir(test_img_dir))[:1]
    if test_files:
        img = cv2.imread(os.path.join(test_img_dir, test_files[0]), cv2.IMREAD_GRAYSCALE)
        result = pipeline.predict(img)
        print(f"\n결함 이미지 테스트:")
        print(f"  판정: {result['verdict']}")
        print(f"  이상 점수: {result['stage1']['anomaly_score']:.6f}")
        if result["stage2"]:
            print(f"  결함 유형: {result['defect_type']} (신뢰도 {result['confidence']:.1%})")
        print(f"  총 시간: {result['total_time_ms']:.1f}ms")
