"""딥러닝 모델 평가 및 리포트 생성 모듈.

혼동행렬, 분류 리포트, ROC 커브 등의 시각화와
Phase 1(전통적 ML) vs Phase 2(딥러닝) 성능 비교 테이블을 생성한다.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    roc_curve,
    auc,
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.preprocessing import label_binarize
from typing import Optional

# 프로젝트 루트를 path에 추가
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def _setup_plot():
    """한글 폰트 설정."""
    plt.rcParams["font.family"] = "AppleGothic"
    plt.rcParams["axes.unicode_minus"] = False


def generate_dl_report(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
    class_names: list[str],
    output_dir: str,
    experiment_name: str,
) -> dict:
    """딥러닝 모델 평가 리포트 생성 및 저장.

    혼동행렬, 분류 리포트 히트맵, ROC 커브를 생성하여 저장한다.

    Args:
        y_true: (N,) 실제 라벨 배열.
        y_pred: (N,) 예측 라벨 배열.
        y_prob: (N, num_classes) 예측 확률 배열.
        class_names: 클래스명 리스트 (영문).
        output_dir: 저장 디렉토리.
        experiment_name: 실험 이름 (파일명 접두사).

    Returns:
        평가 메트릭 딕셔너리.
    """
    _setup_plot()
    os.makedirs(output_dir, exist_ok=True)

    from utils.data_loader import NEUDataLoader
    kr_map = NEUDataLoader.CLASS_NAME_KR
    class_names_kr = [kr_map.get(cn, cn) for cn in class_names]

    # --- 1. 혼동행렬 ---
    cm = confusion_matrix(y_true, y_pred)

    # 정규화 혼동행렬
    fig, ax = plt.subplots(figsize=(10, 8))
    cm_norm = cm.astype(float) / (cm.sum(axis=1, keepdims=True) + 1e-10)
    sns.heatmap(
        cm_norm, annot=True, fmt=".2f", cmap="Blues", ax=ax,
        xticklabels=class_names_kr, yticklabels=class_names_kr,
    )
    ax.set_xlabel("예측", fontsize=12)
    ax.set_ylabel("실제", fontsize=12)
    ax.set_title(f"혼동행렬 (정규화) - {experiment_name}", fontsize=14, fontweight="bold")
    plt.tight_layout()
    cm_path = os.path.join(output_dir, f"{experiment_name}_confusion_matrix.png")
    plt.savefig(cm_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  혼동행렬 저장: {cm_path}")

    # 원본 카운트 혼동행렬
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues", ax=ax,
        xticklabels=class_names_kr, yticklabels=class_names_kr,
    )
    ax.set_xlabel("예측", fontsize=12)
    ax.set_ylabel("실제", fontsize=12)
    ax.set_title(f"혼동행렬 (카운트) - {experiment_name}", fontsize=14, fontweight="bold")
    plt.tight_layout()
    cm_count_path = os.path.join(output_dir, f"{experiment_name}_confusion_matrix_counts.png")
    plt.savefig(cm_count_path, dpi=150, bbox_inches="tight")
    plt.close()

    # --- 2. 분류 리포트 히트맵 ---
    report = classification_report(y_true, y_pred, target_names=class_names, output_dict=True)

    metrics_data = []
    for cn in class_names:
        if cn in report:
            row = report[cn]
            metrics_data.append([row["precision"], row["recall"], row["f1-score"]])
        else:
            metrics_data.append([0, 0, 0])

    report_df = pd.DataFrame(
        metrics_data,
        index=class_names_kr,
        columns=["Precision", "Recall", "F1-Score"],
    )

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(report_df, annot=True, fmt=".3f", cmap="YlOrRd", ax=ax)
    ax.set_title(f"분류 리포트 - {experiment_name}", fontsize=14, fontweight="bold")
    plt.tight_layout()
    report_path = os.path.join(output_dir, f"{experiment_name}_classification_report.png")
    plt.savefig(report_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  분류 리포트 저장: {report_path}")

    # --- 3. ROC 커브 ---
    if y_prob is not None and y_prob.ndim == 2:
        n_classes = len(class_names)
        y_bin = label_binarize(y_true, classes=list(range(n_classes)))
        colors = sns.color_palette("Set2", n_classes)

        fig, ax = plt.subplots(figsize=(10, 8))
        for i in range(n_classes):
            fpr, tpr, _ = roc_curve(y_bin[:, i], y_prob[:, i])
            roc_auc = auc(fpr, tpr)
            ax.plot(
                fpr, tpr, color=colors[i], lw=2,
                label=f"{class_names_kr[i]} (AUC={roc_auc:.3f})",
            )

        ax.plot([0, 1], [0, 1], "k--", lw=1, alpha=0.5)
        ax.set_xlabel("False Positive Rate", fontsize=12)
        ax.set_ylabel("True Positive Rate", fontsize=12)
        ax.set_title(f"ROC 커브 - {experiment_name}", fontsize=14, fontweight="bold")
        ax.legend(fontsize=9)
        plt.tight_layout()
        roc_path = os.path.join(output_dir, f"{experiment_name}_roc_curves.png")
        plt.savefig(roc_path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  ROC 커브 저장: {roc_path}")

    # --- 메트릭 요약 ---
    metrics = {
        "experiment": experiment_name,
        "accuracy": accuracy_score(y_true, y_pred),
        "f1_macro": f1_score(y_true, y_pred, average="macro"),
        "precision_macro": precision_score(y_true, y_pred, average="macro"),
        "recall_macro": recall_score(y_true, y_pred, average="macro"),
        "confusion_matrix": cm,
        "classification_report": report,
    }

    # 텍스트 리포트 저장
    text_report = classification_report(y_true, y_pred, target_names=class_names_kr)
    text_path = os.path.join(output_dir, f"{experiment_name}_report.txt")
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(f"실험: {experiment_name}\n")
        f.write(f"{'='*60}\n")
        f.write(f"Accuracy: {metrics['accuracy']:.4f}\n")
        f.write(f"F1 Macro: {metrics['f1_macro']:.4f}\n")
        f.write(f"Precision Macro: {metrics['precision_macro']:.4f}\n")
        f.write(f"Recall Macro: {metrics['recall_macro']:.4f}\n")
        f.write(f"{'='*60}\n\n")
        f.write(text_report)
    print(f"  텍스트 리포트 저장: {text_path}")

    return metrics


def phase_comparison_table(
    phase1_results: dict,
    phase2_results: dict,
) -> pd.DataFrame:
    """Phase 1 (전통적 ML) vs Phase 2 (딥러닝) 성능 비교 테이블.

    Args:
        phase1_results: Phase 1 결과 딕셔너리.
            키: 모델명, 값: {accuracy, f1_macro, precision_macro, recall_macro}.
        phase2_results: Phase 2 결과 딕셔너리.
            키: 실험명, 값: {accuracy, f1_macro, precision_macro, recall_macro}.

    Returns:
        비교 결과 DataFrame.
    """
    rows = []

    # Phase 1 결과
    for model_name, metrics in phase1_results.items():
        rows.append({
            "Phase": "Phase 1 (ML)",
            "모델": model_name,
            "Accuracy": metrics.get("accuracy", 0),
            "F1 Macro": metrics.get("f1_macro", 0),
            "Precision Macro": metrics.get("precision_macro", 0),
            "Recall Macro": metrics.get("recall_macro", 0),
        })

    # Phase 2 결과
    for exp_name, metrics in phase2_results.items():
        rows.append({
            "Phase": "Phase 2 (DL)",
            "모델": exp_name,
            "Accuracy": metrics.get("accuracy", 0),
            "F1 Macro": metrics.get("f1_macro", 0),
            "Precision Macro": metrics.get("precision_macro", 0),
            "Recall Macro": metrics.get("recall_macro", 0),
        })

    df = pd.DataFrame(rows)

    # 정렬: F1 Macro 기준 내림차순
    df = df.sort_values("F1 Macro", ascending=False).reset_index(drop=True)

    return df


def plot_training_curves(
    history: dict,
    experiment_name: str,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """학습/검증 손실 및 정확도 곡선 시각화.

    Args:
        history: {train_loss, val_loss, train_acc, val_acc} 리스트를 담은 딕셔너리.
        experiment_name: 실험 이름.
        save_path: 저장 경로.

    Returns:
        matplotlib Figure 객체.
    """
    _setup_plot()

    epochs = range(1, len(history["train_loss"]) + 1)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # 손실 곡선
    ax1.plot(epochs, history["train_loss"], "b-", label="학습 손실", linewidth=2)
    ax1.plot(epochs, history["val_loss"], "r-", label="검증 손실", linewidth=2)
    ax1.set_xlabel("에포크")
    ax1.set_ylabel("손실")
    ax1.set_title(f"손실 곡선 - {experiment_name}", fontweight="bold")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 정확도 곡선
    ax2.plot(epochs, history["train_acc"], "b-", label="학습 정확도", linewidth=2)
    ax2.plot(epochs, history["val_acc"], "r-", label="검증 정확도", linewidth=2)
    ax2.set_xlabel("에포크")
    ax2.set_ylabel("정확도")
    ax2.set_title(f"정확도 곡선 - {experiment_name}", fontweight="bold")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path is not None:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"  학습 곡선 저장: {save_path}")

    return fig


if __name__ == "__main__":
    print("=" * 60)
    print("evaluate_dl.py 스모크 테스트")
    print("=" * 60)

    # 더미 데이터
    np.random.seed(42)
    n_samples = 120
    n_classes = 6
    y_true = np.random.randint(0, n_classes, n_samples)
    y_pred = y_true.copy()
    # 약간의 오분류 추가
    noise_idx = np.random.choice(n_samples, 20, replace=False)
    y_pred[noise_idx] = np.random.randint(0, n_classes, 20)

    y_prob = np.random.dirichlet(np.ones(n_classes), n_samples)

    class_names = ["crazing", "inclusion", "patches",
                   "pitted_surface", "rolled-in_scale", "scratches"]

    # 리포트 생성 테스트 (파일 저장 없이)
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics = generate_dl_report(
            y_true, y_pred, y_prob, class_names,
            output_dir=tmpdir,
            experiment_name="test_experiment",
        )
        print(f"\n메트릭:")
        print(f"  Accuracy: {metrics['accuracy']:.4f}")
        print(f"  F1 Macro: {metrics['f1_macro']:.4f}")

        # 파일 생성 확인
        files = os.listdir(tmpdir)
        print(f"\n생성된 파일 ({len(files)}개):")
        for f in sorted(files):
            print(f"  {f}")

    # Phase 비교 테이블 테스트
    phase1 = {
        "RandomForest": {"accuracy": 0.85, "f1_macro": 0.84, "precision_macro": 0.83, "recall_macro": 0.84},
        "SVM": {"accuracy": 0.82, "f1_macro": 0.81, "precision_macro": 0.80, "recall_macro": 0.81},
    }
    phase2 = {
        "ResNet18_finetune": {"accuracy": 0.92, "f1_macro": 0.91, "precision_macro": 0.91, "recall_macro": 0.91},
        "CustomCNN": {"accuracy": 0.88, "f1_macro": 0.87, "precision_macro": 0.87, "recall_macro": 0.87},
    }
    comparison = phase_comparison_table(phase1, phase2)
    print(f"\nPhase 비교 테이블:")
    print(comparison.to_string(index=False))

    # 학습 곡선 테스트
    history = {
        "train_loss": [1.5, 1.2, 1.0, 0.8, 0.6],
        "val_loss": [1.6, 1.3, 1.1, 0.9, 0.85],
        "train_acc": [0.3, 0.5, 0.6, 0.7, 0.8],
        "val_acc": [0.25, 0.45, 0.55, 0.65, 0.72],
    }
    fig = plot_training_curves(history, "test_experiment")
    plt.close(fig)
    print("학습 곡선 생성 확인")

    print("\nevaluate_dl.py 스모크 테스트 완료")
