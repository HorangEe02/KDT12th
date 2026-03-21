"""
Stage 2: 비정상 이미지 → 4종 결함 세부 분류 — ML 파이프라인

Severstal 결함 패치만 사용하여 4종 분류:
  ClassId 1: 점상 결함 (Pitting Spot, PS)
  ClassId 2: 선형 긁힘 (Linear Scratch, LS)
  ClassId 3: 표면 변색 (Surface Stain, SS)
  ClassId 4: 압연 압흔 (Rolling Dent, RD)
"""

import os
import sys
import time
import numpy as np
import joblib
from typing import Dict, Optional, Tuple

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix,
)
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.severstal_loader import CLASS_NAMES_KR, CLASS_ABBR


# ──────────────────────────────────────────────
# 모델 정의 (train_binary.py와 동일 구조)
# ──────────────────────────────────────────────
def get_defect4_models() -> Dict:
    """4종 분류용 ML 모델."""
    from sklearn.svm import SVC
    from sklearn.ensemble import RandomForestClassifier, VotingClassifier
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.neural_network import MLPClassifier

    models = {
        "SVM_RBF": SVC(kernel="rbf", C=10, gamma="scale", probability=True, random_state=42),
        "RandomForest": RandomForestClassifier(n_estimators=200, max_depth=20, random_state=42, n_jobs=-1),
        "KNN": KNeighborsClassifier(n_neighbors=5, n_jobs=-1),
        "MLP": MLPClassifier(hidden_layer_sizes=(256, 128), max_iter=500, random_state=42, early_stopping=True),
    }

    try:
        from xgboost import XGBClassifier
        models["XGBoost"] = XGBClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            use_label_encoder=False, eval_metric="mlogloss", random_state=42, n_jobs=-1,
        )
    except ImportError:
        pass

    try:
        from lightgbm import LGBMClassifier
        models["LightGBM"] = LGBMClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            random_state=42, n_jobs=-1, verbose=-1,
        )
    except ImportError:
        pass

    estimators = []
    if "SVM_RBF" in models:
        estimators.append(("svm", models["SVM_RBF"]))
    if "RandomForest" in models:
        estimators.append(("rf", models["RandomForest"]))
    if "XGBoost" in models:
        estimators.append(("xgb", models["XGBoost"]))
    if len(estimators) >= 2:
        models["VotingEnsemble"] = VotingClassifier(
            estimators=estimators, voting="soft", n_jobs=-1
        )

    return models


# ──────────────────────────────────────────────
# 학습 및 평가
# ──────────────────────────────────────────────
def train_single_defect4_model(
    model, model_name: str,
    X_train: np.ndarray, X_test: np.ndarray,
    y_train: np.ndarray, y_test: np.ndarray,
) -> Dict:
    """단일 모델 학습 및 평가 (4종 분류)."""
    target_names = [f"{CLASS_ABBR[i]} ({CLASS_NAMES_KR[i]})" for i in [1, 2, 3, 4]]
    labels_list = [0, 1, 2, 3]  # 0-indexed (mapped from ClassId 1~4)

    print(f"\n{'='*50}")
    print(f"[{model_name}] 학습 시작...")

    t0 = time.time()
    model.fit(X_train, y_train)
    train_time = time.time() - t0

    t0 = time.time()
    y_pred = model.predict(X_test)
    pred_time = time.time() - t0

    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="macro")
    cm = confusion_matrix(y_test, y_pred, labels=labels_list)

    report = classification_report(
        y_test, y_pred, labels=labels_list, target_names=target_names
    )

    print(f"  Accuracy: {acc:.4f}")
    print(f"  F1 (macro): {f1:.4f}")
    print(f"  학습 시간: {train_time:.2f}s")
    print(f"  추론 시간: {pred_time:.4f}s")
    print(f"\n{report}")

    return {
        "model_name": model_name,
        "model": model,
        "accuracy": acc,
        "f1_score": f1,
        "confusion_matrix": cm,
        "y_pred": y_pred,
        "train_time": train_time,
        "pred_time": pred_time,
        "classification_report": report,
    }


def run_defect4_experiment(
    X: np.ndarray,
    y: np.ndarray,
    test_size: float = 0.2,
    seed: int = 42,
    save_dir: Optional[str] = None,
) -> Tuple[Dict[str, Dict], np.ndarray, np.ndarray]:
    """4종 결함 분류 실험."""
    scaler = StandardScaler()

    # ClassId 1~4 → 0~3 변환 (XGBoost 호환)
    label_map = {1: 0, 2: 1, 3: 2, 4: 3}
    inv_label_map = {0: 1, 1: 2, 2: 3, 3: 4}
    y_mapped = np.array([label_map[v] for v in y])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_mapped, test_size=test_size, stratify=y_mapped, random_state=seed
    )

    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print(f"\n{'#'*60}")
    print(f"Stage 2: 비정상 → 4종 결함 세부 분류 ML 실험")
    print(f"{'#'*60}")
    print(f"학습 세트: {len(X_train):,}장")
    for cid in [1, 2, 3, 4]:
        cnt = (y_train == label_map[cid]).sum()
        print(f"  ClassId {cid} ({CLASS_ABBR[cid]}): {cnt:,}장")
    print(f"테스트 세트: {len(X_test):,}장")
    print(f"특징 차원: {X.shape[1]}D")

    models = get_defect4_models()
    results = {}

    for name, model in models.items():
        result = train_single_defect4_model(
            model, name, X_train_scaled, X_test_scaled, y_train, y_test
        )
        results[name] = result

        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            joblib.dump(model, os.path.join(save_dir, f"defect4_{name}.joblib"))
            joblib.dump(scaler, os.path.join(save_dir, "defect4_scaler.joblib"))

    # 결과 요약
    print(f"\n{'='*60}")
    print(f"{'모델':>20s} | {'Acc':>7s} | {'F1(macro)':>9s}")
    print(f"{'-'*60}")
    for name, r in sorted(results.items(), key=lambda x: x[1]["accuracy"], reverse=True):
        print(f"{name:>20s} | {r['accuracy']:>7.4f} | {r['f1_score']:>9.4f}")
    print(f"{'='*60}")

    return results, X_test_scaled, y_test


# ──────────────────────────────────────────────
if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    from utils.severstal_preprocessor import PatchDataLoader
    from features.feature_pipeline import FeaturePipeline

    patch_dir = os.path.join(base, "data", "severstal_patches")
    save_dir = os.path.join(base, "outputs", "models_severstal", "defect4_ml")

    patch_loader = PatchDataLoader(patch_dir)

    print("\n[결함 패치 로드 중...]")
    images, labels = patch_loader.load_defect4(
        max_per_class=None, resize=(200, 200), grayscale=True
    )
    print(f"  로드 완료: {len(images)}장")
    for cid in [1, 2, 3, 4]:
        print(f"    ClassId {cid} ({CLASS_ABBR[cid]}): {(labels==cid).sum()}장")

    print("\n[특징 추출 중...]")
    pipeline = FeaturePipeline()
    X, _ = pipeline.extract_batch(images)
    print(f"  특징 벡터: {X.shape}")

    results, X_test, y_test = run_defect4_experiment(X, labels, save_dir=save_dir)
