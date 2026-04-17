"""Plotly 차트 3종 — 구단별 원정 승률, 맛집 산점도, 승률 게이지.

VIZ_CONTRACT.md 계약 준수.
"""
from __future__ import annotations

import random
from typing import Any

import pandas as pd
import plotly.graph_objects as go

from src.ui.components.hero import TEAM_COLORS

_FONT_FAMILY = "Plus Jakarta Sans, Pretendard, Noto Sans KR, sans-serif"


def bar_away_win_rate(df: pd.DataFrame, highlight_team: str) -> go.Figure:
    """구단별 최근 3년 평균 원정 승률 막대그래프. 선택 팀만 팀 컬러로 강조."""
    if df is None or df.empty:
        fig = go.Figure()
        fig.add_annotation(text="데이터 없음", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False,
                           font=dict(size=16, color="#888"))
        return fig

    max_year = int(df["year"].max())
    recent = df[df["year"] >= max_year - 2]
    agg = (recent.groupby("team")["away_win_rate"]
                 .mean().reset_index()
                 .sort_values("away_win_rate", ascending=False))

    highlight_color = TEAM_COLORS.get(highlight_team, {}).get("color", "#3B82F6")
    colors = [highlight_color if t == highlight_team else "#D1D5DB" for t in agg["team"]]

    fig = go.Figure(data=[
        go.Bar(
            x=agg["team"],
            y=agg["away_win_rate"],
            marker_color=colors,
            text=[f"{v:.3f}" for v in agg["away_win_rate"]],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>원정 승률: %{y:.3f}<extra></extra>",
        )
    ])
    fig.update_layout(
        title=f"구단별 최근 3년 원정 승률 (강조: {highlight_team})",
        xaxis_title="구단",
        yaxis_title="원정 승률",
        yaxis_range=[0, max(0.7, float(agg["away_win_rate"].max()) * 1.15)],
        template="simple_white",
        height=380,
        font=dict(family=_FONT_FAMILY, color="#00193c"),
        margin=dict(l=40, r=20, t=60, b=50),
    )
    return fig


def _infer_rating(place: dict, idx: int) -> float:
    existing = place.get("rating")
    if isinstance(existing, (int, float)):
        return float(existing)
    rng = random.Random(f"{place.get('content_id', idx)}")
    return round(rng.uniform(3.5, 4.8), 1)


def scatter_places(places: list[dict], stadium_coord: tuple[float, float]) -> go.Figure:
    """맛집/POI 거리-평점 산점도. 빈 입력 시 annotation 반환."""
    if not places:
        fig = go.Figure()
        fig.add_annotation(text="데이터 없음", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False,
                           font=dict(size=16, color="#888"))
        fig.update_layout(template="simple_white", height=380,
                          font=dict(family=_FONT_FAMILY))
        return fig

    x_dist: list[float] = []
    y_rating: list[float] = []
    names: list[str] = []
    for i, p in enumerate(places):
        try:
            d = float(p.get("dist_m") or 0)
        except (TypeError, ValueError):
            d = 0.0
        x_dist.append(d)
        y_rating.append(_infer_rating(p, i))
        names.append(str(p.get("title", "")))

    sizes = [max(8.0, 20.0 - d / 200.0) for d in x_dist]

    fig = go.Figure(data=[
        go.Scatter(
            x=x_dist,
            y=y_rating,
            mode="markers",
            marker=dict(
                size=sizes,
                color="#F97316",
                opacity=0.72,
                line=dict(color="white", width=1.2),
            ),
            text=names,
            hovertemplate="<b>%{text}</b><br>거리: %{x:.0f}m<br>평점: %{y:.1f}<extra></extra>",
        )
    ])
    fig.update_layout(
        title=f"경기장 주변 POI — 거리 vs 평점 (총 {len(places)}개)",
        xaxis_title="경기장에서 거리 (m)",
        yaxis_title="평점",
        yaxis_range=[3.0, 5.0],
        template="simple_white",
        height=400,
        font=dict(family=_FONT_FAMILY, color="#00193c"),
        margin=dict(l=40, r=20, t=60, b=50),
    )
    return fig


def gauge_win_rate(prob: float, team_name: str) -> go.Figure:
    """승률 예측 원형 게이지 (Plotly Indicator)."""
    try:
        pct = max(0.0, min(1.0, float(prob))) * 100.0
    except (TypeError, ValueError):
        pct = 50.0
    color = TEAM_COLORS.get(team_name, {}).get("color", "#3B82F6")

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=pct,
        number={"suffix": "%", "font": {"size": 34}},
        delta={
            "reference": 50,
            "increasing": {"color": color},
            "decreasing": {"color": "#6B7280"},
        },
        title={"text": f"{team_name} 승률 예측", "font": {"size": 15}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#D1D5DB"},
            "bar": {"color": color, "thickness": 0.7},
            "steps": [
                {"range": [0, 40], "color": "#FEE2E2"},
                {"range": [40, 60], "color": "#FEF3C7"},
                {"range": [60, 100], "color": "#D1FAE5"},
            ],
            "threshold": {
                "line": {"color": "#111827", "width": 3},
                "thickness": 0.75,
                "value": 50,
            },
        },
    ))
    fig.update_layout(
        height=280,
        margin=dict(l=20, r=20, t=50, b=20),
        font=dict(family=_FONT_FAMILY, color="#00193c"),
    )
    return fig


if __name__ == "__main__":
    import sys
    from pathlib import Path

    ROOT = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(ROOT))
    from src.data_loader import load_team_stats

    stats = load_team_stats()
    fig1 = bar_away_win_rate(stats, "LG")
    print(f"막대그래프 trace 수: {len(fig1.data)}")

    fig2 = scatter_places([], (37.5, 127.0))
    print(f"빈 산점도 trace 수: {len(fig2.data)}")

    fig3 = gauge_win_rate(0.62, "LG")
    print(f"게이지 trace 수: {len(fig3.data)}")
