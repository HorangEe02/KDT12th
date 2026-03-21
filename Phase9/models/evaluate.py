"""모델 평가 및 시각화 모듈.

혼동행렬, Classification Report, ROC 커브, 모델 비교,
특징 중요도, 오분류 분석 등의 시각화 기능을 제공한다.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional
from sklearn.metrics import roc_curve, auc
from sklearn.preprocessing import label_binarize
import math


def _setup_plot():
    """한글 폰트 설정."""
    plt.rcParams["font.family"] = "AppleGothic"
    plt.rcParams["axes.unicode_minus"] = False


def plot_confusion_matrix(
    cm: np.ndarray, class_names: list[str],
    title: str = "혼동행렬", save_path: str = None, normalize: bool = True
):
    """혼동행렬 히트맵."""
    _setup_plot()
    fig, ax = plt.subplots(figsize=(10, 8))
    if normalize:
        cm_plot = cm.astype(float) / (cm.sum(axis=1, keepdims=True) + 1e-10)
        fmt = ".2f"
    else:
        cm_plot = cm
        fmt = "d"

    sns.heatmap(cm_plot, annot=True, fmt=fmt, cmap="Blues", ax=ax,
                xticklabels=class_names, yticklabels=class_names)
    ax.set_xlabel("예측", fontsize=12)
    ax.set_ylabel("실제", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"✅ 저장 완료: {save_path}")
    plt.show()


def plot_classification_report(
    report_dict: dict, class_names: list[str],
    title: str = "분류 리포트", save_path: str = None
):
    """classification_report를 히트맵으로 시각화."""
    _setup_plot()
    metrics = ["precision", "recall", "f1-score"]
    data = []
    for cn in class_names:
        key = cn
        if key not in report_dict:
            # 라벨 인덱스로 시도
            for k in report_dict:
                if str(k) in cn or cn in str(k):
                    key = k
                    break
        row = report_dict.get(key, report_dict.get(str(class_names.index(cn)), {}))
        data.append([row.get(m, 0) for m in metrics])

    df = pd.DataFrame(data, index=class_names, columns=["Precision", "Recall", "F1-Score"])

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(df, annot=True, fmt=".3f", cmap="YlOrRd", ax=ax)
    ax.set_title(title, fontsize=14, fontweight="bold")
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"✅ 저장 완료: {save_path}")
    plt.show()


def plot_roc_curves(
    y_test, y_prob, class_names: list[str],
    title: str = "ROC 커브", save_path: str = None
):
    """One-vs-Rest ROC 커브."""
    _setup_plot()
    if y_prob is None:
        print("⚠️ y_prob가 없어 ROC 커브를 그릴 수 없습니다.")
        return

    n_classes = len(class_names)
    y_bin = label_binarize(y_test, classes=list(range(n_classes)))
    colors = sns.color_palette("Set2", n_classes)

    fig, ax = plt.subplots(figsize=(10, 8))
    for i in range(n_classes):
        fpr, tpr, _ = roc_curve(y_bin[:, i], y_prob[:, i])
        roc_auc = auc(fpr, tpr)
        ax.plot(fpr, tpr, color=colors[i], lw=2,
                label=f"{class_names[i]} (AUC={roc_auc:.3f})")

    ax.plot([0, 1], [0, 1], "k--", lw=1, alpha=0.5)
    ax.set_xlabel("False Positive Rate", fontsize=12)
    ax.set_ylabel("True Positive Rate", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.legend(fontsize=9)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"✅ 저장 완료: {save_path}")
    plt.show()


def plot_model_comparison(
    summary_df: pd.DataFrame,
    metrics: list[str] = None,
    title: str = "모델 성능 비교", save_path: str = None
):
    """여러 모델의 성능을 grouped bar chart로 비교."""
    if metrics is None:
        metrics = ["accuracy", "f1_macro", "recall_macro"]
    _setup_plot()

    x = np.arange(len(summary_df))
    width = 0.8 / len(metrics)
    fig, ax = plt.subplots(figsize=(14, 6))

    for i, m in enumerate(metrics):
        vals = summary_df[m].values
        bars = ax.bar(x + i * width, vals, width, label=m, alpha=0.8)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                    f"{v:.3f}", ha="center", va="bottom", fontsize=7)

    ax.set_xticks(x + width * (len(metrics) - 1) / 2)
    ax.set_xticklabels(summary_df.index, rotation=15)
    ax.set_ylabel("성능")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.legend()
    ax.set_ylim(0, 1.05)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"✅ 저장 완료: {save_path}")
    plt.show()


def plot_experiment_comparison(
    experiment_results: dict[str, pd.DataFrame],
    metric: str = "f1_macro", save_path: str = None
):
    """여러 실험 조건의 성능을 히트맵으로 비교."""
    _setup_plot()
    rows = []
    for exp_name, df in experiment_results.items():
        row = {"experiment": exp_name}
        for model_name in df.index:
            row[model_name] = df.loc[model_name, metric]
        rows.append(row)

    heatmap_df = pd.DataFrame(rows).set_index("experiment")

    fig, ax = plt.subplots(figsize=(12, max(4, len(heatmap_df) + 1)))
    sns.heatmap(heatmap_df, annot=True, fmt=".3f", cmap="YlGnBu", ax=ax)
    ax.set_title(f"실험 조건별 {metric} 비교", fontsize=14, fontweight="bold")
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"✅ 저장 완료: {save_path}")
    plt.show()


def plot_feature_importance(
    model, feature_names: list[str], top_n: int = 20,
    title: str = "특징 중요도", save_path: str = None
):
    """RandomForest feature_importance 또는 permutation importance 시각화."""
    _setup_plot()
    if hasattr(model, "feature_importances_"):
        importance = model.feature_importances_
    else:
        print("⚠️ feature_importances_ 없음. permutation_importance를 사용하세요.")
        return

    n = min(top_n, len(importance))
    indices = np.argsort(importance)[-n:]
    names = [feature_names[i] if i < len(feature_names) else f"feat_{i}" for i in indices]
    vals = importance[indices]

    fig, ax = plt.subplots(figsize=(12, max(6, n * 0.3)))
    ax.barh(range(n), vals, color="steelblue", alpha=0.8)
    ax.set_yticks(range(n))
    ax.set_yticklabels(names, fontsize=8)
    ax.set_xlabel("중요도")
    ax.set_title(title, fontsize=14, fontweight="bold")
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"✅ 저장 완료: {save_path}")
    plt.show()


def plot_misclassified_samples(
    X_test_images: np.ndarray, y_test, y_pred, class_names: list[str],
    n_samples: int = 12, save_path: str = None
):
    """오분류된 이미지 샘플 시각화."""
    _setup_plot()
    wrong_idx = np.where(y_test != y_pred)[0]
    if len(wrong_idx) == 0:
        print("오분류 없음!")
        return
    n_show = min(n_samples, len(wrong_idx))
    sel = np.random.choice(wrong_idx, n_show, replace=False)

    cols = 4
    rows = math.ceil(n_show / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(20, rows * 5))
    axes = axes.flatten() if rows > 1 else [axes] if cols == 1 else axes.flatten()

    for i, idx in enumerate(sel):
        axes[i].imshow(X_test_images[idx], cmap="gray")
        actual = class_names[y_test[idx]] if y_test[idx] < len(class_names) else str(y_test[idx])
        predicted = class_names[y_pred[idx]] if y_pred[idx] < len(class_names) else str(y_pred[idx])
        axes[i].set_title(f"실제: {actual}\n예측: {predicted}", fontsize=9, color="red")
        axes[i].axis("off")

    for i in range(n_show, len(axes)):
        axes[i].axis("off")

    plt.suptitle("오분류 사례", fontsize=14, fontweight="bold")
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"✅ 저장 완료: {save_path}")
    plt.show()


def print_recall_analysis(cm: np.ndarray, class_names: list[str]):
    """제조업 맥락 Recall 분석 출력."""
    print("\n" + "=" * 60)
    print("제조업 맥락 Recall 분석")
    print("=" * 60)
    print(f"{'클래스':12s} {'Recall':>8s} {'FN(놓친불량)':>12s} {'주요 혼동 대상':>15s}")
    print("-" * 60)

    worst_recall = 1.0
    worst_class = ""

    for i, cn in enumerate(class_names):
        total = cm[i].sum()
        tp = cm[i, i]
        fn = total - tp
        recall = tp / total if total > 0 else 0
        if recall < worst_recall:
            worst_recall = recall
            worst_class = cn

        # 주요 혼동 대상
        off_diag = cm[i].copy()
        off_diag[i] = 0
        if off_diag.max() > 0:
            confused_with = class_names[np.argmax(off_diag)]
        else:
            confused_with = "-"

        print(f"{cn:12s} {recall:8.3f} {fn:12d} {confused_with:>15s}")

    print("-" * 60)
    print(f"⚠️ 가장 위험한 결함: {worst_class} (Recall={worst_recall:.3f})")
    print(f"   → 100개 중 {int((1-worst_recall)*100)}개의 불량이 출하될 수 있음")
    print("=" * 60)


def generate_full_report(
    result: dict, class_names: list[str],
    experiment_name: str, output_dir: str = "outputs/figures"
):
    """단일 모델 결과에 대한 전체 리포트 자동 생성."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    mn = result["model_name"]
    prefix = f"{output_dir}/{experiment_name}_{mn}"

    plot_confusion_matrix(result["confusion_matrix"], class_names,
                          f"혼동행렬 — {mn}", f"{prefix}_confusion_matrix.png")
    plot_confusion_matrix(result["confusion_matrix"], class_names,
                          f"혼동행렬(원본) — {mn}", f"{prefix}_confusion_matrix_counts.png", normalize=False)

    # classification report에서 클래스별 키 매핑
    report = result["classification_report"]
    # 키가 숫자 문자열인 경우 클래스명으로 매핑
    mapped_report = {}
    for i, cn in enumerate(class_names):
        if cn in report:
            mapped_report[cn] = report[cn]
        elif str(i) in report:
            mapped_report[cn] = report[str(i)]

    plot_classification_report(mapped_report, class_names,
                               f"분류 리포트 — {mn}", f"{prefix}_classification_report.png")

    if result["y_prob"] is not None:
        plot_roc_curves(result.get("y_test", None), result["y_prob"], class_names,
                        f"ROC 커브 — {mn}", f"{prefix}_roc_curves.png")


if __name__ == "__main__":
    print("\n=== evaluate.py 테스트 ===")
    cm = np.array([[50, 5, 2, 0, 1, 2], [3, 48, 4, 1, 2, 2],
                    [1, 3, 52, 2, 1, 1], [0, 1, 2, 55, 1, 1],
                    [2, 2, 1, 1, 50, 4], [1, 3, 1, 1, 3, 51]])
    cn = ["균열", "개재물", "패치", "구멍", "압연스케일", "스크래치"]
    print_recall_analysis(cm, cn)
    print("✅ evaluate.py 테스트 완료")
