"""Tab 1 — 원정 경기 리스트 + 승률 게이지 + 구단별 원정 승률 막대그래프."""
from __future__ import annotations

import hashlib
import logging
import random

import pandas as pd
import streamlit as st

from src.data_loader import load_schedule, load_team_stats
from src.viz.plotly_charts import bar_away_win_rate, gauge_win_rate

log = logging.getLogger(__name__)


@st.cache_resource(show_spinner=False)
def _load_win_rate_model():
    """Phase 4 승률 모델을 한 번만 로드. 실패 시 None."""
    try:
        from src.ai.predict import load_model
        return load_model()
    except FileNotFoundError:
        log.warning("승률 모델 없음 — 더미값 사용")
        return None


def _dummy_win_prob(game_id: str) -> float:
    """모델 없을 때 폴백: game_id 기반 재현 가능 더미값."""
    h = int(hashlib.md5(str(game_id).encode()).hexdigest(), 16) % 10_000
    rng = random.Random(h)
    return round(rng.uniform(0.35, 0.65), 2)


def _real_or_dummy_win_prob(team: str, opponent: str, stats_df: pd.DataFrame, game_id: str) -> tuple[float, str]:
    """학습된 모델 예측 시도 → 실패 시 더미. (prob, source) 반환."""
    model = _load_win_rate_model()
    if model is None:
        return _dummy_win_prob(game_id), "더미 (모델 없음)"
    try:
        from src.ai.predict import predict_win_rate
        prob = predict_win_rate(team, opponent, stats_df, model)
        return prob, "로지스틱 회귀 모델"
    except Exception as exc:
        log.warning("예측 실패: %s → 더미 사용", exc)
        return _dummy_win_prob(game_id), "더미 (예측 오류)"


def render(filters: dict) -> None:
    st.subheader("⚾ 원정 경기 & 승률 예측")

    df = load_schedule()
    team = filters.get("team", "LG")
    away_games = df[df["away_team"] == team]

    date_range = filters.get("date_range")
    if not date_range or len(date_range) != 2:
        st.info("사이드바에서 원정 기간을 선택해주세요.")
        return
    start, end = date_range
    mask = (away_games["date"] >= pd.Timestamp(start)) & (
        away_games["date"] <= pd.Timestamp(end)
    )
    filtered = away_games.loc[mask].sort_values("date").reset_index(drop=True)

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("응원팀", team)
    col_b.metric("원정 경기", f"{len(filtered)}건")
    col_c.metric("기간", f"{start} ~ {end}")

    if len(filtered) == 0:
        st.info("선택한 기간에 원정 경기가 없습니다. 사이드바에서 기간을 넓혀보세요.")
        st.divider()
    else:
        # 선택 가능한 경기 (승률 게이지용)
        filtered["_label"] = filtered.apply(
            lambda r: f"{r['date'].strftime('%Y-%m-%d')} ({r['day_of_week']}) @ {r['stadium']} vs {r['home_team']}",
            axis=1,
        )
        picked_label = st.selectbox(
            "🎯 집중할 경기",
            options=filtered["_label"].tolist(),
            index=0,
            key="tab1_selected_game",
        )
        selected_game = filtered[filtered["_label"] == picked_label].iloc[0]

        col_info, col_gauge = st.columns([3, 2])
        with col_info:
            st.markdown(
                f"### 🆚 vs {selected_game['home_team']} @ {selected_game['stadium']}"
            )
            st.markdown(f"📅 **{selected_game['date'].strftime('%Y-%m-%d')}** ({selected_game['day_of_week']})")
            st.markdown(f"🕐 경기 시작: **{selected_game['start_time']}**")
            broadcast = selected_game.get("broadcast", "")
            if broadcast:
                st.markdown(f"📺 중계: {broadcast}")
        with col_gauge:
            stats_for_pred = load_team_stats()
            win_prob, source = _real_or_dummy_win_prob(
                team=team,
                opponent=str(selected_game["home_team"]),
                stats_df=stats_for_pred,
                game_id=str(selected_game["game_id"]),
            )
            fig_gauge = gauge_win_rate(win_prob, team)
            st.plotly_chart(fig_gauge, use_container_width=True)
            st.caption(f"🔮 예측 소스: **{source}**")
        with col_info:
            st.caption(
                "💡 로지스틱 회귀 모델은 더미 데이터(연도별 팀 순위·승률)로 학습되어 "
                "실제 경기 결과 대비 극단적인 확률을 출력할 수 있습니다. "
                "실제 KBO 기록 연동 시 더 현실적인 예측이 가능해집니다."
            )

        st.markdown("#### 📋 기간 내 원정 경기 리스트")
        display = filtered[
            ["date", "day_of_week", "home_team", "stadium", "start_time", "broadcast"]
        ].copy()
        display["date"] = display["date"].dt.strftime("%Y-%m-%d")
        display.columns = ["날짜", "요일", "홈팀", "구장", "경기시간", "중계"]
        st.dataframe(display, use_container_width=True, hide_index=True)

    st.divider()

    # 구단별 원정 승률 막대그래프 (필터 없이 항상 표시)
    stats = load_team_stats()
    st.markdown("#### 📊 구단별 최근 3년 원정 승률")
    fig_bar = bar_away_win_rate(stats, team)
    st.plotly_chart(fig_bar, use_container_width=True)

    max_year = int(stats["year"].max())
    recent = stats[stats["year"] >= max_year - 2]
    top_team = recent.groupby("team")["away_win_rate"].mean().idxmax()
    top_rate = recent.groupby("team")["away_win_rate"].mean().max()
    highlighted = recent[recent["team"] == team]["away_win_rate"].mean()
    st.caption(
        f"💡 최근 3년 원정 승률 1위는 **{top_team}** (`{top_rate:.3f}`). "
        f"{team}의 평균 원정 승률: `{highlighted:.3f}`. "
        "그래프에서 회색은 비교군, 컬러는 선택 팀입니다."
    )
