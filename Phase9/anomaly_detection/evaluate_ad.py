"""이상 탐지 평가 및 시각화 모듈.

AUROC 계산, 히스토그램, 히트맵 시각화 및 종합 보고서 생성.
한글 폰트: AppleGothic
"""

import os
from typing import Optional, Dict, Any, List, Tuple

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "AppleGothic"
plt.rcParams["axes.unicode_minus"] = False

from sklearn.metrics import roc_auc_score, roc_curve, precision_recall_curve, f1_score


# ---------------------------------------------------------------------------
# 메트릭 계산
# ---------------------------------------------------------------------------

def compute_image_auroc(y_true: np.ndarray, scores: np.ndarray) -> float:
    """이미지 레벨 AUROC를 계산한다.

    Args:
        y_true: 실제 라벨 (0=정상, 1=이상).
        scores: 이상 점수.

    Returns:
        AUROC 값 (float).
    """
    y_true = np.asarray(y_true)
    scores = np.asarray(scores)

    if len(np.unique(y_true)) < 2:
        print("[경고] 클래스가 하나뿐이어서 AUROC를 계산할 수 없습니다.")
        return 0.0

    return float(roc_auc_score(y_true, scores))


def compute_pixel_auroc(
    masks_true: np.ndarray,
    maps_pred: np.ndarray,
) -> float:
    """픽셀 레벨 AUROC를 계산한다 (마스크 필요).

    Args:
        masks_true: 실제 마스크 배열 (N, H, W) 또는 flat.
        maps_pred: 예측 이상 맵 배열 (N, H, W) 또는 flat.

    Returns:
        AUROC 값 (float).
    """
    masks_flat = np.asarray(masks_true).flatten()
    maps_flat = np.asarray(maps_pred).flatten()

    # 이진화
    masks_binary = (masks_flat > 0.5).astype(int)

    if len(np.unique(masks_binary)) < 2:
        print("[경고] 마스크에 양성 픽셀이 없어 pixel-AUROC를 계산할 수 없습니다.")
        return 0.0

    return float(roc_auc_score(masks_binary, maps_flat))


# ---------------------------------------------------------------------------
# 시각화
# ---------------------------------------------------------------------------

def plot_auroc_curve(
    y_true: np.ndarray,
    scores: np.ndarray,
    title: str = "ROC 곡선",
    save_path: Optional[str] = None,
) -> plt.Figure:
    """ROC 곡선을 그린다.

    Args:
        y_true: 실제 라벨.
        scores: 이상 점수.
        title: 그래프 제목.
        save_path: 저장 경로.

    Returns:
        matplotlib Figure.
    """
    y_true = np.asarray(y_true)
    scores = np.asarray(scores)

    auroc = compute_image_auroc(y_true, scores)
    fpr, tpr, _ = roc_curve(y_true, scores)

    fig, ax = plt.subplots(1, 1, figsize=(7, 6))
    ax.plot(fpr, tpr, "b-", linewidth=2, label=f"AUROC = {auroc:.4f}")
    ax.plot([0, 1], [0, 1], "k--", linewidth=1, alpha=0.5)
    ax.set_xlabel("False Positive Rate (위양성률)", fontsize=12)
    ax.set_ylabel("True Positive Rate (재현율)", fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.legend(fontsize=12, loc="lower right")
    ax.grid(True, alpha=0.3)
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1.05])

    plt.tight_layout()

    if save_path is not None:
        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else ".", exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[저장] {save_path}")

    return fig


def plot_anomaly_histogram(
    normal_scores: np.ndarray,
    anomaly_scores: np.ndarray,
    title: str = "이상 점수 분포",
    save_path: Optional[str] = None,
) -> plt.Figure:
    """정상/이상 점수 분포 히스토그램.

    Args:
        normal_scores: 정상 이미지 이상 점수.
        anomaly_scores: 이상 이미지 이상 점수.
        title: 그래프 제목.
        save_path: 저장 경로.

    Returns:
        matplotlib Figure.
    """
    fig, ax = plt.subplots(1, 1, figsize=(8, 5))

    bins = 50
    ax.hist(normal_scores, bins=bins, alpha=0.6, label="정상", color="steelblue", density=True)
    ax.hist(anomaly_scores, bins=bins, alpha=0.6, label="이상", color="tomato", density=True)
    ax.set_xlabel("이상 점수", fontsize=12)
    ax.set_ylabel("밀도", fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path is not None:
        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else ".", exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[저장] {save_path}")

    return fig


def plot_anomaly_heatmap_grid(
    images: List[np.ndarray],
    maps: List[np.ndarray],
    labels: List[int],
    predictions: List[bool],
    n_samples: int = 8,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """이미지 + 이상 맵 히트맵 그리드 시각화.

    Args:
        images: 원본 이미지 리스트 (H, W) 그레이스케일.
        maps: 이상 맵 리스트 (H, W).
        labels: 실제 라벨 리스트 (0 or 1).
        predictions: 예측 결과 리스트 (True=이상).
        n_samples: 표시할 샘플 수.
        save_path: 저장 경로.

    Returns:
        matplotlib Figure.
    """
    n = min(n_samples, len(images))
    fig, axes = plt.subplots(2, n, figsize=(2.5 * n, 5))

    if n == 1:
        axes = axes.reshape(2, 1)

    for i in range(n):
        # 원본 이미지
        ax_img = axes[0, i]
        img = images[i]
        if img.ndim == 3 and img.shape[0] in (1, 3):
            img = img.transpose(1, 2, 0)
        if img.ndim == 3 and img.shape[2] == 1:
            img = img.squeeze(-1)
        ax_img.imshow(img, cmap="gray")

        gt = "이상" if labels[i] == 1 else "정상"
        pred = "이상" if predictions[i] else "정상"
        color = "red" if labels[i] != int(predictions[i]) else "green"
        ax_img.set_title(f"GT:{gt}\nPred:{pred}", fontsize=9, color=color)
        ax_img.axis("off")

        # 히트맵
        ax_map = axes[1, i]
        if img.ndim == 2:
            ax_map.imshow(img, cmap="gray", alpha=0.5)
        amap = maps[i]
        if amap.shape != img.shape[:2]:
            import cv2
            amap = cv2.resize(amap, (img.shape[1] if img.ndim >= 2 else img.shape[0],
                                      img.shape[0]))
        im = ax_map.imshow(amap, cmap="jet", alpha=0.7)
        ax_map.set_title("이상 맵", fontsize=9)
        ax_map.axis("off")

    plt.suptitle("이상 탐지 결과 시각화", fontsize=13)
    plt.tight_layout()

    if save_path is not None:
        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else ".", exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[저장] {save_path}")

    return fig


# ---------------------------------------------------------------------------
# 보고서 생성
# ---------------------------------------------------------------------------

def generate_ad_report(
    results_dict: Dict[str, Dict[str, Any]],
    output_dir: str = "outputs/phase3",
) -> None:
    """이상 탐지 실험 결과 보고서를 생성한다.

    Args:
        results_dict: {model_name: {y_true, scores, ...}} 딕셔너리.
        output_dir: 출력 디렉토리.
    """
    os.makedirs(output_dir, exist_ok=True)

    print("\n" + "=" * 60)
    print("Phase 3: 이상 탐지 결과 보고서")
    print("=" * 60)

    summary_rows = []

    for model_name, data in results_dict.items():
        y_true = np.asarray(data["y_true"])
        scores = np.asarray(data["scores"])

        # AUROC
        auroc = compute_image_auroc(y_true, scores)

        # 최적 F1 (threshold 탐색)
        if len(np.unique(y_true)) >= 2:
            fpr, tpr, thresholds = roc_curve(y_true, scores)
            # Youden's J statistic으로 최적 threshold
            j_stat = tpr - fpr
            best_idx = np.argmax(j_stat)
            best_threshold = thresholds[best_idx]

            y_pred = (scores >= best_threshold).astype(int)
            best_f1 = f1_score(y_true, y_pred)
        else:
            best_f1 = 0.0
            best_threshold = 0.0

        # 정상/이상 평균 점수
        normal_mask = y_true == 0
        anomaly_mask = y_true == 1
        mean_normal = float(scores[normal_mask].mean()) if normal_mask.sum() > 0 else 0.0
        mean_anomaly = float(scores[anomaly_mask].mean()) if anomaly_mask.sum() > 0 else 0.0

        summary_rows.append({
            "모델": model_name,
            "AUROC": round(auroc, 4),
            "최적 F1": round(best_f1, 4),
            "정상 평균 점수": round(mean_normal, 4),
            "이상 평균 점수": round(mean_anomaly, 4),
            "최적 임계값": round(float(best_threshold), 6),
        })

        # ROC 곡선 저장
        plot_auroc_curve(
            y_true, scores,
            title=f"ROC 곡선 - {model_name}",
            save_path=os.path.join(output_dir, f"roc_{model_name}.png"),
        )
        plt.close()

        # 히스토그램 저장
        if normal_mask.sum() > 0 and anomaly_mask.sum() > 0:
            plot_anomaly_histogram(
                scores[normal_mask], scores[anomaly_mask],
                title=f"점수 분포 - {model_name}",
                save_path=os.path.join(output_dir, f"hist_{model_name}.png"),
            )
            plt.close()

        print(f"  {model_name}: AUROC={auroc:.4f}, F1={best_f1:.4f}")

    # 요약 테이블
    df = pd.DataFrame(summary_rows)
    csv_path = os.path.join(output_dir, "ad_summary.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"\n[저장] 요약 테이블: {csv_path}")
    print(df.to_string(index=False))

    # 비교 바 차트
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(df))
    width = 0.35
    bars1 = ax.bar(x - width / 2, df["AUROC"], width, label="AUROC", color="steelblue")
    bars2 = ax.bar(x + width / 2, df["최적 F1"], width, label="최적 F1", color="coral")

    ax.set_xticks(x)
    ax.set_xticklabels(df["모델"], rotation=15, ha="right")
    ax.set_ylabel("점수")
    ax.set_title("모델별 성능 비교", fontsize=14)
    ax.legend()
    ax.set_ylim(0, 1.1)
    ax.grid(axis="y", alpha=0.3)

    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                f"{bar.get_height():.3f}", ha="center", fontsize=8)
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                f"{bar.get_height():.3f}", ha="center", fontsize=8)

    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, "model_comparison.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[저장] 비교 차트: {os.path.join(output_dir, 'model_comparison.png')}")


def full_phase_comparison(
    phase1_dict: Optional[Dict[str, Any]] = None,
    phase2_dict: Optional[Dict[str, Any]] = None,
    phase3_dict: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """Phase 1, 2, 3 결과를 종합 비교한다.

    각 dict는 {model_name: {accuracy, f1, auroc, ...}} 형태.

    Args:
        phase1_dict: Phase 1 (전통적 CV) 결과.
        phase2_dict: Phase 2 (딥러닝) 결과.
        phase3_dict: Phase 3 (이상 탐지) 결과.

    Returns:
        종합 비교 DataFrame.
    """
    rows = []

    if phase1_dict:
        for name, metrics in phase1_dict.items():
            rows.append({
                "Phase": "Phase 1 (전통적 CV)",
                "모델": name,
                "Accuracy": metrics.get("accuracy", None),
                "F1": metrics.get("f1", None),
                "AUROC": metrics.get("auroc", None),
            })

    if phase2_dict:
        for name, metrics in phase2_dict.items():
            rows.append({
                "Phase": "Phase 2 (딥러닝)",
                "모델": name,
                "Accuracy": metrics.get("accuracy", None),
                "F1": metrics.get("f1", None),
                "AUROC": metrics.get("auroc", None),
            })

    if phase3_dict:
        for name, metrics in phase3_dict.items():
            rows.append({
                "Phase": "Phase 3 (이상 탐지)",
                "모델": name,
                "Accuracy": metrics.get("accuracy", None),
                "F1": metrics.get("f1", None),
                "AUROC": metrics.get("auroc", None),
            })

    df = pd.DataFrame(rows)
    return df


# ---------------------------------------------------------------------------
# 스모크 테스트
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("evaluate_ad.py 스모크 테스트")
    print("=" * 60)

    np.random.seed(42)

    # 더미 데이터
    n_normal = 50
    n_anomaly = 30
    y_true = np.concatenate([np.zeros(n_normal), np.ones(n_anomaly)])
    scores_good = np.concatenate([
        np.random.normal(0.2, 0.1, n_normal),
        np.random.normal(0.7, 0.15, n_anomaly),
    ])
    scores_bad = np.concatenate([
        np.random.normal(0.4, 0.2, n_normal),
        np.random.normal(0.5, 0.2, n_anomaly),
    ])

    # AUROC
    auroc_good = compute_image_auroc(y_true, scores_good)
    auroc_bad = compute_image_auroc(y_true, scores_bad)
    print(f"\n좋은 모델 AUROC: {auroc_good:.4f}")
    print(f"나쁜 모델 AUROC: {auroc_bad:.4f}")

    # ROC 곡선
    fig = plot_auroc_curve(y_true, scores_good, title="테스트 ROC",
                          save_path="/tmp/test_roc.png")
    plt.close()
    print("ROC 곡선 저장 완료")

    # 히스토그램
    fig = plot_anomaly_histogram(
        scores_good[:n_normal], scores_good[n_normal:],
        title="테스트 히스토그램",
        save_path="/tmp/test_hist.png",
    )
    plt.close()
    print("히스토그램 저장 완료")

    # 보고서
    results = {
        "model_good": {"y_true": y_true, "scores": scores_good},
        "model_bad": {"y_true": y_true, "scores": scores_bad},
    }
    generate_ad_report(results, output_dir="/tmp/ad_report")

    # Phase 비교
    df = full_phase_comparison(
        phase1_dict={"SVM": {"accuracy": 0.85, "f1": 0.84}},
        phase2_dict={"ResNet": {"accuracy": 0.95, "f1": 0.94, "auroc": 0.98}},
        phase3_dict={"AE": {"auroc": 0.88, "f1": 0.80}},
    )
    print("\nPhase 비교:")
    print(df.to_string(index=False))

    # 정리
    import shutil
    for p in ["/tmp/test_roc.png", "/tmp/test_hist.png"]:
        if os.path.isfile(p):
            os.remove(p)
    shutil.rmtree("/tmp/ad_report", ignore_errors=True)

    print("\n[PASS] evaluate_ad.py 스모크 테스트 완료")
