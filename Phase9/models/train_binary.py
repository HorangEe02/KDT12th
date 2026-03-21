"""
Stage 1: 정상 vs 비정상 이진 분류 — ML 파이프라인

Severstal 패치(256×256)에서 OpenCV 특징 추출 후
7종 ML 모델로 이진 분류(정상=0, 비정상=1).
"""

import os
import sys
import time
import numpy as np
import joblib
from typing import Dict, List, Optional, Tuple

from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.preprocessing import StandardScaler, label_binarize

# ──────────────────────────────────────────────
# 모델 정의
# ──────────────────────────────────────────────
def get_binary_models() -> Dict:
    """이진 분류용 7종 ML 모델."""
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

    # XGBoost
    try:
        from xgboost import XGBClassifier
        models["XGBoost"] = XGBClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            use_label_encoder=False, eval_metric="logloss", random_state=42, n_jobs=-1,
        )
    except ImportError:
        print("[경고] XGBoost 미설치 — 건너뜀")

    # LightGBM
    try:
        from lightgbm import LGBMClassifier
        models["LightGBM"] = LGBMClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            random_state=42, n_jobs=-1, verbose=-1,
        )
    except ImportError:
        print("[경고] LightGBM 미설치 — 건너뜀")

    # Voting Ensemble (사용 가능한 모델로 구성)
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
def train_single_binary_model(
    model,
    model_name: str,
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_train: np.ndarray,
    y_test: np.ndarray,
) -> Dict:
    """단일 모델 학습 및 평가."""
    print(f"\n{'='*50}")
    print(f"[{model_name}] 학습 시작...")

    # 학습
    t0 = time.time()
    model.fit(X_train, y_train)
    train_time = time.time() - t0

    # 예측
    t0 = time.time()
    y_pred = model.predict(X_test)
    pred_time = time.time() - t0

    # 확률 예측 (가능한 경우)
    y_prob = None
    if hasattr(model, "predict_proba"):
        y_prob = model.predict_proba(X_test)[:, 1]
    elif hasattr(model, "decision_function"):
        y_prob = model.decision_function(X_test)

    # 메트릭
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="binary")
    prec = precision_score(y_test, y_pred, average="binary")
    rec = recall_score(y_test, y_pred, average="binary")
    auc = roc_auc_score(y_test, y_prob) if y_prob is not None else 0.0
    cm = confusion_matrix(y_test, y_pred)

    print(f"  Accuracy: {acc:.4f}")
    print(f"  F1 Score: {f1:.4f}")
    print(f"  Precision: {prec:.4f}")
    print(f"  Recall: {rec:.4f}")
    print(f"  AUC-ROC: {auc:.4f}")
    print(f"  학습 시간: {train_time:.2f}s")
    print(f"  추론 시간: {pred_time:.4f}s ({pred_time/len(y_test)*1000:.2f}ms/장)")
    print(f"\n  Confusion Matrix:")
    print(f"    TN={cm[0][0]:,}  FP={cm[0][1]:,}")
    print(f"    FN={cm[1][0]:,}  TP={cm[1][1]:,}")

    return {
        "model_name": model_name,
        "model": model,
        "accuracy": acc,
        "f1_score": f1,
        "precision": prec,
        "recall": rec,
        "auc_roc": auc,
        "confusion_matrix": cm,
        "y_pred": y_pred,
        "y_prob": y_prob,
        "train_time": train_time,
        "pred_time": pred_time,
        "classification_report": classification_report(
            y_test, y_pred, target_names=["정상", "비정상"]
        ),
    }


def run_binary_experiment(
    X: np.ndarray,
    y: np.ndarray,
    test_size: float = 0.2,
    seed: int = 42,
    save_dir: Optional[str] = None,
) -> Tuple[Dict[str, Dict], np.ndarray, np.ndarray]:
    """전체 이진 분류 실험 실행.

    Returns
    -------
    results : {model_name: result_dict}
    X_test, y_test : 테스트 세트
    """
    # 스케일링
    scaler = StandardScaler()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=seed
    )

    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print(f"\n{'#'*60}")
    print(f"Stage 1: 정상 vs 비정상 이진 분류 ML 실험")
    print(f"{'#'*60}")
    print(f"학습 세트: {len(X_train):,}장 (정상 {(y_train==0).sum():,} / 비정상 {(y_train==1).sum():,})")
    print(f"테스트 세트: {len(X_test):,}장 (정상 {(y_test==0).sum():,} / 비정상 {(y_test==1).sum():,})")
    print(f"특징 차원: {X.shape[1]}D")

    models = get_binary_models()
    results = {}

    for name, model in models.items():
        result = train_single_binary_model(
            model, name, X_train_scaled, X_test_scaled, y_train, y_test
        )
        results[name] = result

        # 모델 저장
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            joblib.dump(model, os.path.join(save_dir, f"binary_{name}.joblib"))
            joblib.dump(scaler, os.path.join(save_dir, "binary_scaler.joblib"))

    # 결과 요약
    print(f"\n{'='*60}")
    print(f"{'모델':>20s} | {'Acc':>7s} | {'F1':>7s} | {'AUC':>7s} | {'Recall':>7s}")
    print(f"{'-'*60}")
    for name, r in sorted(results.items(), key=lambda x: x[1]["accuracy"], reverse=True):
        print(f"{name:>20s} | {r['accuracy']:>7.4f} | {r['f1_score']:>7.4f} | {r['auc_roc']:>7.4f} | {r['recall']:>7.4f}")
    print(f"{'='*60}")

    return results, X_test_scaled, y_test


# ──────────────────────────────────────────────
if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, base)

    from utils.severstal_preprocessor import PatchDataLoader
    from features.feature_pipeline import FeaturePipeline

    patch_dir = os.path.join(base, "data", "severstal_patches")
    save_dir = os.path.join(base, "outputs", "models_severstal", "binary_ml")

    # 패치 로드 (균형 맞춤)
    patch_loader = PatchDataLoader(patch_dir)
    patch_loader.print_stats()

    print("\n[데이터 로드 중... (max 5,000/class)]")
    images, labels = patch_loader.load_binary(
        max_per_class=5000, resize=(200, 200), grayscale=True
    )
    print(f"  로드 완료: {len(images)}장 (정상 {(labels==0).sum()} / 비정상 {(labels==1).sum()})")

    # 특징 추출
    print("\n[특징 추출 중...]")
    pipeline = FeaturePipeline()
    X, _ = pipeline.extract_batch(images)
    print(f"  특징 벡터: {X.shape}")

    # 실험 실행
    results, X_test, y_test = run_binary_experiment(X, labels, save_dir=save_dir)
