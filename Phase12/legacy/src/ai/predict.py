"""원정 경기 승률 예측 — scikit-learn 로지스틱 회귀.

학습 데이터: data/team_stats_10yr.csv
- 각 샘플: (team, opponent, year) 3-tuple, 피처 5종
- 타깃: 해당 연도 team의 away_win_rate > 0.5 여부 (이진)
모델 저장: models/win_rate_model.pkl
"""
from __future__ import annotations

import logging
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src import config

log = logging.getLogger(__name__)

_FEATURE_NAMES = [
    "team_away_win_rate",
    "opponent_home_win_rate",
    "team_rank",
    "opponent_rank",
    "rank_diff",
]


def _build_samples(stats_df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """연도별 × 팀쌍 조합으로 이진 분류 학습 샘플 생성.

    피처: 팀의 원정/홈 승률 + 순위 비교 (종합 win_rate는 타깃과 직결되므로 제외)
    타깃: 해당 연도 팀이 상대보다 전반적으로 강한가 (`team.win_rate > opp.win_rate`) → 50/50 균형
    """
    rows = []
    for year, year_df in stats_df.groupby("year"):
        lookup = {r["team"]: r for _, r in year_df.iterrows()}
        teams = list(lookup.keys())
        for team in teams:
            for opponent in teams:
                if team == opponent:
                    continue
                a = lookup[team]
                b = lookup[opponent]
                x = [
                    float(a["away_win_rate"]),
                    float(b["home_win_rate"]),
                    float(a["final_rank"]),
                    float(b["final_rank"]),
                    float(b["final_rank"] - a["final_rank"]),
                ]
                y = 1 if float(a["win_rate"]) > float(b["win_rate"]) else 0
                rows.append((x, y))
    X = np.array([r[0] for r in rows], dtype=np.float32)
    y = np.array([r[1] for r in rows], dtype=np.int32)
    return X, y


def train_model(save_path: str | Path | None = None) -> dict:
    """모델 학습 → pkl 저장 → 요약 dict 반환."""
    from src.data_loader import load_team_stats

    save_path = Path(save_path) if save_path else config.WIN_RATE_MODEL_PATH

    stats = load_team_stats()
    X, y = _build_samples(stats)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=500, C=1.0, random_state=42)),
    ])
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    acc = float(accuracy_score(y_test, y_pred))

    save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "wb") as f:
        pickle.dump(
            {"pipeline": pipeline, "feature_names": _FEATURE_NAMES},
            f,
        )

    return {
        "accuracy": acc,
        "n_samples": int(X.shape[0]),
        "n_train": int(X_train.shape[0]),
        "n_test": int(X_test.shape[0]),
        "feature_names": _FEATURE_NAMES,
        "save_path": str(save_path),
    }


def load_model(path: str | Path | None = None):
    """pkl 로드, 없으면 FileNotFoundError."""
    path = Path(path) if path else config.WIN_RATE_MODEL_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"승률 모델이 없습니다: {path}\n"
            "먼저 `python -m src.ai.predict` 실행으로 학습해 주세요."
        )
    with open(path, "rb") as f:
        return pickle.load(f)


def predict_win_rate(
    team: str,
    opponent: str,
    team_stats_df: pd.DataFrame,
    model: dict | None = None,
) -> float:
    """team의 원정 경기 승률 예측. 기록 없으면 0.45 반환."""
    if model is None:
        try:
            model = load_model()
        except FileNotFoundError:
            log.warning("승률 모델 없음 → 중립값 0.45 반환")
            return 0.45

    try:
        max_year = int(team_stats_df["year"].max())
        latest = team_stats_df[team_stats_df["year"] == max_year]
        a = latest[latest["team"] == team]
        b = latest[latest["team"] == opponent]
        if a.empty or b.empty:
            log.warning("팀 기록 없음 (%s vs %s) → 0.45", team, opponent)
            return 0.45
        a = a.iloc[0]
        b = b.iloc[0]
        x = np.array([[
            float(a["away_win_rate"]),
            float(b["home_win_rate"]),
            float(a["final_rank"]),
            float(b["final_rank"]),
            float(b["final_rank"] - a["final_rank"]),
        ]], dtype=np.float32)
        pipeline = model["pipeline"]
        prob = float(pipeline.predict_proba(x)[0, 1])
        return round(prob, 4)
    except Exception as exc:
        log.warning("예측 실패 (%s vs %s): %s → 0.45", team, opponent, exc)
        return 0.45


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    summary = train_model()
    print(f"✅ 학습 완료: acc={summary['accuracy']:.3f} "
          f"(train={summary['n_train']}, test={summary['n_test']})")
    print(f"저장: {summary['save_path']}")

    import sys
    from pathlib import Path
    ROOT = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(ROOT))
    from src.data_loader import load_team_stats

    stats = load_team_stats()
    for team, opp in [("LG", "KT"), ("KIA", "삼성"), ("두산", "한화"), ("키움", "SSG")]:
        prob = predict_win_rate(team, opp, stats)
        print(f"  {team:4s} vs {opp:4s} 원정 승률: {prob:.2%}")
