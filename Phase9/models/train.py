"""모델 학습 모듈.

SVM, Random Forest, KNN, XGBoost, LightGBM, Voting Ensemble, MLP
분류 모델의 학습, 교차 검증, 하이퍼파라미터 튜닝, 저장/로딩 기능을 제공한다.
"""

import numpy as np
import pandas as pd
import joblib
import time
from typing import Optional
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import cross_validate, GridSearchCV, learning_curve
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    from lightgbm import LGBMClassifier
    HAS_LGBM = True
except ImportError:
    HAS_LGBM = False


def get_models(include_ensemble: bool = True) -> dict:
    """실험에 사용할 분류 모델 딕셔너리.

    Parameters:
        include_ensemble: True면 Voting Ensemble 포함 (개별 모델 학습 후 사용 권장).
    """
    base = {
        "SVM_RBF": SVC(kernel="rbf", C=10, gamma="scale", probability=True, random_state=42),
        "RandomForest": RandomForestClassifier(n_estimators=200, max_depth=20, random_state=42, n_jobs=-1),
        "KNN_5": KNeighborsClassifier(n_neighbors=5, weights="distance", n_jobs=-1),
    }

    # XGBoost — Gradient Boosting 계열 SOTA
    if HAS_XGB:
        base["XGBoost"] = XGBClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8,
            use_label_encoder=False, eval_metric="mlogloss",
            random_state=42, n_jobs=-1, verbosity=0,
        )

    # LightGBM — 빠르고 메모리 효율적
    if HAS_LGBM:
        base["LightGBM"] = LGBMClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8,
            random_state=42, n_jobs=-1, verbose=-1,
        )

    # MLP — 전통 ML → 딥러닝 브릿지
    base["MLP"] = MLPClassifier(
        hidden_layer_sizes=(256, 128, 64), activation="relu",
        solver="adam", max_iter=500, early_stopping=True,
        validation_fraction=0.15, random_state=42,
    )

    # Voting Ensemble — 최강 모델 조합
    if include_ensemble:
        estimators = [
            ("svm", SVC(kernel="rbf", C=10, gamma="scale", probability=True, random_state=42)),
            ("rf", RandomForestClassifier(n_estimators=200, max_depth=20, random_state=42, n_jobs=-1)),
        ]
        if HAS_XGB:
            estimators.append(("xgb", XGBClassifier(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                use_label_encoder=False, eval_metric="mlogloss",
                random_state=42, n_jobs=-1, verbosity=0,
            )))
        base["VotingEnsemble"] = VotingClassifier(
            estimators=estimators, voting="soft", n_jobs=-1,
        )

    return base


def plot_learning_curve(
    model, X, y, cv: int = 5,
    train_sizes=None,
    title: str = "Learning Curve",
    save_path: str = None,
):
    """데이터 양에 따른 성능 변화 학습 곡선.

    Parameters:
        model: sklearn 호환 분류기.
        X, y: 전체 데이터.
        train_sizes: 학습 데이터 비율 리스트 (기본: 0.1~1.0).
        save_path: 저장 경로 (None이면 plt.show).

    Returns:
        (train_sizes_abs, train_scores, test_scores).
    """
    import matplotlib.pyplot as plt

    if train_sizes is None:
        train_sizes = np.linspace(0.1, 1.0, 10)

    train_sizes_abs, train_scores, test_scores = learning_curve(
        model, X, y, cv=cv, train_sizes=train_sizes,
        scoring="f1_macro", n_jobs=-1, random_state=42,
    )

    train_mean = train_scores.mean(axis=1)
    train_std = train_scores.std(axis=1)
    test_mean = test_scores.mean(axis=1)
    test_std = test_scores.std(axis=1)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.fill_between(train_sizes_abs, train_mean - train_std, train_mean + train_std, alpha=0.1, color="#2196F3")
    ax.fill_between(train_sizes_abs, test_mean - test_std, test_mean + test_std, alpha=0.1, color="#FF5722")
    ax.plot(train_sizes_abs, train_mean, "o-", color="#2196F3", label="Train F1")
    ax.plot(train_sizes_abs, test_mean, "o-", color="#FF5722", label="Validation F1")
    ax.set_xlabel("Training Set Size", fontsize=12)
    ax.set_ylabel("F1 Macro Score", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"  학습 곡선 저장: {save_path}")
    else:
        plt.show()

    return train_sizes_abs, train_scores, test_scores


def train_single_model(
    model, X_train, y_train, X_test, y_test, model_name: str = "model"
) -> dict:
    """단일 모델 학습 및 평가.

    Returns:
        모델명, fitted model, accuracy, classification_report, confusion_matrix,
        y_pred, y_prob, train_time, predict_time.
    """
    # 학습
    t0 = time.time()
    model.fit(X_train, y_train)
    train_time = time.time() - t0

    # 예측
    t0 = time.time()
    y_pred = model.predict(X_test)
    predict_time = time.time() - t0

    # 확률
    y_prob = None
    if hasattr(model, "predict_proba"):
        try:
            y_prob = model.predict_proba(X_test)
        except Exception:
            pass

    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_test, y_pred)

    print(f"  [{model_name}] Accuracy={acc:.4f}  F1(macro)={report['macro avg']['f1-score']:.4f}  "
          f"Train={train_time:.2f}s  Predict={predict_time:.3f}s")

    return {
        "model_name": model_name,
        "model": model,
        "accuracy": acc,
        "classification_report": report,
        "confusion_matrix": cm,
        "y_pred": y_pred,
        "y_prob": y_prob,
        "train_time": train_time,
        "predict_time": predict_time,
    }


def train_with_cross_validation(
    model, X, y, cv: int = 5, model_name: str = "model"
) -> dict:
    """교차 검증 학습."""
    scoring = ["accuracy", "f1_macro", "recall_macro", "precision_macro"]
    results = cross_validate(model, X, y, cv=cv, scoring=scoring, n_jobs=-1)

    return {
        "model_name": model_name,
        "cv_accuracy_mean": float(results["test_accuracy"].mean()),
        "cv_accuracy_std": float(results["test_accuracy"].std()),
        "cv_f1_mean": float(results["test_f1_macro"].mean()),
        "cv_f1_std": float(results["test_f1_macro"].std()),
        "cv_recall_mean": float(results["test_recall_macro"].mean()),
        "cv_recall_std": float(results["test_recall_macro"].std()),
        "cv_scores": results,
    }


def hyperparameter_tuning(
    model_name: str, X_train, y_train, param_grid: dict = None
) -> tuple:
    """GridSearchCV 기반 하이퍼파라미터 튜닝.

    Returns:
        (best_model, best_params, cv_results_df).
    """
    default_grids = {
        "SVM_RBF": {"C": [1, 10, 100], "gamma": ["scale", "auto", 0.01]},
        "RandomForest": {"n_estimators": [100, 200], "max_depth": [10, 20, None]},
        "KNN": {"n_neighbors": [3, 5, 7, 10], "weights": ["uniform", "distance"]},
        "XGBoost": {"n_estimators": [100, 200], "max_depth": [4, 6, 8], "learning_rate": [0.05, 0.1]},
        "LightGBM": {"n_estimators": [100, 200], "max_depth": [4, 6, 8], "learning_rate": [0.05, 0.1]},
        "MLP": {"hidden_layer_sizes": [(128, 64), (256, 128, 64)], "alpha": [0.0001, 0.001]},
    }

    if param_grid is None:
        param_grid = default_grids.get(model_name, {})

    models = get_models()
    if model_name in models:
        base = models[model_name]
    elif "SVM" in model_name:
        base = SVC(kernel="rbf", probability=True, random_state=42)
    elif "Forest" in model_name or "RF" in model_name:
        base = RandomForestClassifier(random_state=42, n_jobs=-1)
    else:
        base = KNeighborsClassifier(n_jobs=-1)

    gs = GridSearchCV(base, param_grid, cv=3, scoring="f1_macro", n_jobs=-1, verbose=0)
    gs.fit(X_train, y_train)

    return gs.best_estimator_, gs.best_params_, pd.DataFrame(gs.cv_results_)


def run_full_experiment(
    X_train, y_train, X_test, y_test,
    class_names: list[str], experiment_name: str = "experiment"
) -> tuple[pd.DataFrame, dict]:
    """모든 모델에 대한 전체 실험 실행.

    Returns:
        (summary_df, detailed_results_dict).
    """
    print(f"\n=== 실험: {experiment_name} ===")
    models = get_models()
    detailed = {}
    rows = []

    for mname, model in models.items():
        result = train_single_model(model, X_train, y_train, X_test, y_test, mname)
        detailed[mname] = result
        report = result["classification_report"]
        rows.append({
            "model": mname,
            "accuracy": result["accuracy"],
            "f1_macro": report["macro avg"]["f1-score"],
            "recall_macro": report["macro avg"]["recall"],
            "precision_macro": report["macro avg"]["precision"],
            "train_time": result["train_time"],
        })

    summary = pd.DataFrame(rows).set_index("model")
    print(f"\n[{experiment_name}] 요약:")
    print(summary.round(4).to_string())
    return summary, detailed


def save_model(model, scaler, feature_pipeline_config: dict, filepath: str, class_names: list[str] = None):
    """모델과 관련 정보를 joblib으로 저장."""
    from datetime import datetime
    data = {
        "model": model,
        "scaler": scaler,
        "config": feature_pipeline_config,
        "class_names": class_names,
        "timestamp": datetime.now().isoformat(),
    }
    joblib.dump(data, filepath)
    print(f"모델 저장 완료: {filepath}")


def load_model(filepath: str) -> dict:
    """저장된 모델 로드."""
    return joblib.load(filepath)


if __name__ == "__main__":
    print("\n=== train.py 테스트 ===")
    # 더미 데이터
    np.random.seed(42)
    X = np.random.randn(60, 20)
    y = np.repeat(np.arange(6), 10)
    from sklearn.model_selection import train_test_split
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.3, stratify=y, random_state=42)

    summary, detailed = run_full_experiment(X_tr, y_tr, X_te, y_te, [str(i) for i in range(6)], "dummy")
    print(f"\n요약 shape: {summary.shape}")
    print("✅ train.py 테스트 완료")
