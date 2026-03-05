"""
인터랙티브 시각화 모듈 (Plotly 기반)
6종 인터랙티브 차트 - HTML + PNG 저장
"""

import logging
import numpy as np
import pandas as pd

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config.settings import OUTPUT_CHARTS_DIR

logger = logging.getLogger(__name__)

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.warning("Plotly가 설치되지 않았습니다. pip install plotly kaleido")


class InteractiveVisualizer:
    """Plotly 기반 인터랙티브 시각화 (6종)"""

    def __init__(self):
        self.output_dir = OUTPUT_CHARTS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.template = "plotly_white"

    def _save_interactive(self, fig, filename: str):
        """HTML + PNG 저장"""
        # HTML 저장
        html_path = self.output_dir / f"{filename}.html"
        fig.write_html(str(html_path))
        logger.info(f"HTML 저장: {html_path}")

        # PNG 저장 (kaleido 필요)
        try:
            png_path = self.output_dir / f"{filename}.png"
            fig.write_image(str(png_path), width=1200, height=800, scale=2)
            logger.info(f"PNG 저장: {png_path}")
        except Exception as e:
            logger.warning(f"PNG 저장 실패 (kaleido 필요): {e}")

    # ── 1. 기업별 연봉 분포 인터랙티브 박스플롯 ──
    def plot_salary_boxplot(self, data: pd.DataFrame):
        """인터랙티브 연봉 박스플롯"""
        if not PLOTLY_AVAILABLE:
            return

        company_col = "기업명" if "기업명" in data.columns else "회사명"

        fig = px.box(data, x=company_col, y="연봉_만원",
                     color=company_col, template=self.template,
                     title="기업별 연봉 분포 (인터랙티브)")

        fig.update_layout(
            xaxis_title="기업명",
            yaxis_title="연봉 (만원)",
            showlegend=False,
            font=dict(size=12),
        )
        fig.update_traces(hovertemplate="기업: %{x}<br>연봉: %{y}만원<extra></extra>")

        self._save_interactive(fig, "interactive_salary_boxplot")

    # ── 2. 기술스택 빈도 인터랙티브 막대그래프 ──
    def plot_tech_stack_bar(self, data: pd.DataFrame):
        """기술스택 빈도 인터랙티브 막대그래프"""
        if not PLOTLY_AVAILABLE:
            return

        df = data.sort_values("빈도", ascending=True)

        fig = go.Figure(go.Bar(
            x=df["빈도"],
            y=df["기술스택"],
            orientation="h",
            marker=dict(
                color=df["빈도"],
                colorscale="Blues",
                showscale=True,
                colorbar=dict(title="빈도"),
            ),
            hovertemplate="기술: %{y}<br>빈도: %{x}회<extra></extra>",
        ))

        fig.update_layout(
            title="자율주행 분야 기술스택 빈도 (인터랙티브)",
            xaxis_title="빈도수",
            yaxis_title="기술스택",
            template=self.template,
            font=dict(size=12),
        )

        self._save_interactive(fig, "interactive_tech_bar")

    # ── 3. 기업 평점 비교 인터랙티브 레이더차트 ──
    def plot_company_radar(self, ratings: dict):
        """인터랙티브 레이더차트"""
        if not PLOTLY_AVAILABLE:
            return

        categories = ["연봉", "워라밸", "성장성", "사내문화", "복지", "기술력"]
        fig = go.Figure()

        colors = px.colors.qualitative.Set2

        for idx, (company, values) in enumerate(ratings.items()):
            vals = list(values.values())[:len(categories)]
            while len(vals) < len(categories):
                vals.append(0)
            vals_closed = vals + [vals[0]]

            fig.add_trace(go.Scatterpolar(
                r=vals_closed,
                theta=categories + [categories[0]],
                fill="toself",
                name=company,
                opacity=0.6,
                line=dict(color=colors[idx % len(colors)]),
            ))

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
            title="기업 평점 비교 레이더차트 (인터랙티브)",
            template=self.template,
            font=dict(size=12),
        )

        self._save_interactive(fig, "interactive_company_radar")

    # ── 4. 채용 트렌드 인터랙티브 라인차트 ──
    def plot_hiring_trend(self, data: pd.DataFrame):
        """범위 슬라이더 포함 채용 트렌드"""
        if not PLOTLY_AVAILABLE:
            return

        fig = go.Figure()

        if isinstance(data, pd.DataFrame) and data.ndim == 2 and len(data.columns) > 1:
            # 멀티 키워드 트렌드
            for col in data.columns:
                fig.add_trace(go.Scatter(
                    x=data.index, y=data[col],
                    mode="lines+markers", name=col,
                    hovertemplate="%{x}<br>%{y}건<extra></extra>"
                ))
        else:
            fig.add_trace(go.Scatter(
                x=data.index, y=data.values if hasattr(data, "values") else data.iloc[:, 0],
                mode="lines+markers", name="채용공고",
                fill="tozeroy", fillcolor="rgba(33,150,243,0.1)",
                line=dict(color="#2196F3"),
            ))

        fig.update_layout(
            title="채용 트렌드 (인터랙티브)",
            xaxis_title="시기",
            yaxis_title="공고 수",
            template=self.template,
            font=dict(size=12),
            xaxis=dict(
                rangeslider=dict(visible=True),
                type="category",
            ),
        )

        self._save_interactive(fig, "interactive_hiring_trend")

    # ── 5. 기업-기술스택 산키 다이어그램 ──
    def plot_sankey_diagram(self, data: pd.DataFrame):
        """기업 → 직무분류 → 기술스택 산키 다이어그램"""
        if not PLOTLY_AVAILABLE:
            return

        # data에 필요한 컬럼: source, target, value
        if not all(col in data.columns for col in ["source", "target", "value"]):
            logger.warning("산키 다이어그램 데이터에 source, target, value 컬럼이 필요합니다.")
            return

        # 노드 목록 생성
        all_nodes = list(set(data["source"].tolist() + data["target"].tolist()))
        node_indices = {node: idx for idx, node in enumerate(all_nodes)}

        # 노드 색상 (3그룹: 기업, 직무, 기술)
        node_colors = []
        for node in all_nodes:
            if node in ["인지", "판단", "제어", "인프라", "데이터"]:
                node_colors.append("rgba(255,152,0,0.8)")
            elif any(c in node for c in ["Python", "C++", "ROS", "PyTorch", "Linux", "Docker"]):
                node_colors.append("rgba(76,175,80,0.8)")
            else:
                node_colors.append("rgba(33,150,243,0.8)")

        fig = go.Figure(go.Sankey(
            node=dict(
                pad=15, thickness=20,
                label=all_nodes,
                color=node_colors,
            ),
            link=dict(
                source=[node_indices[s] for s in data["source"]],
                target=[node_indices[t] for t in data["target"]],
                value=data["value"],
                color="rgba(200,200,200,0.4)",
            ),
        ))

        fig.update_layout(
            title="기업-직무-기술스택 흐름 (산키 다이어그램)",
            template=self.template,
            font=dict(size=12),
        )

        self._save_interactive(fig, "interactive_sankey")

    # ── 6. 기술스택 동시 출현 인터랙티브 히트맵 ──
    def plot_tech_cooccurrence_heatmap(self, data: pd.DataFrame):
        """기술스택 동시 출현 히트맵"""
        if not PLOTLY_AVAILABLE:
            return

        fig = go.Figure(go.Heatmap(
            z=data.values,
            x=data.columns.tolist(),
            y=data.index.tolist(),
            colorscale="Blues",
            hovertemplate="%{y} × %{x}<br>동시출현: %{z}회<extra></extra>",
        ))

        fig.update_layout(
            title="기술스택 동시 출현 히트맵 (인터랙티브)",
            xaxis_title="기술스택",
            yaxis_title="기술스택",
            template=self.template,
            font=dict(size=11),
            width=1000, height=900,
        )

        self._save_interactive(fig, "interactive_tech_cooccurrence")

    def create_all(self, data: dict):
        """전체 인터랙티브 차트 생성 (6종)"""
        if not PLOTLY_AVAILABLE:
            logger.error("Plotly가 설치되지 않아 인터랙티브 차트를 생성할 수 없습니다.")
            return

        logger.info("=" * 40)
        logger.info("인터랙티브 차트 생성 시작 (총 6개)")
        logger.info("=" * 40)

        chart_map = {
            "salary_data": self.plot_salary_boxplot,
            "tech_freq_df": self.plot_tech_stack_bar,
            "radar_data": self.plot_company_radar,
            "trend_data": self.plot_hiring_trend,
            "sankey_data": self.plot_sankey_diagram,
            "cooccurrence_data": self.plot_tech_cooccurrence_heatmap,
        }

        for key, func in chart_map.items():
            if data.get(key) is not None:
                try:
                    func(data[key])
                except Exception as e:
                    logger.error(f"인터랙티브 차트 생성 실패 ({key}): {e}")
            else:
                logger.warning(f"데이터 없음: {key}")

        logger.info("인터랙티브 차트 생성 완료")
