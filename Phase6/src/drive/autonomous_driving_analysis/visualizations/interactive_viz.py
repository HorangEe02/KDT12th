"""
=============================================================
인터랙티브 시각화 모듈 (Plotly)
=============================================================
HTML 저장 가능한 인터랙티브 차트 8종 생성
=============================================================
"""

import os

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from config.settings import OUTPUTS_CHARTS_DIR


class InteractiveVisualizer:
    """Plotly 기반 인터랙티브 시각화 (8종)"""

    def __init__(self, save_dir: str = None):
        self.save_dir = save_dir or OUTPUTS_CHARTS_DIR
        os.makedirs(self.save_dir, exist_ok=True)

    def _save(self, fig, filename):
        """HTML + PNG 저장"""
        html_path = os.path.join(self.save_dir, filename.replace(".png", ".html"))
        fig.write_html(html_path)
        print(f"  📊 HTML 저장: {html_path}")

        try:
            png_path = os.path.join(self.save_dir, filename)
            fig.write_image(png_path, width=1200, height=800, scale=2)
            print(f"  📊 PNG 저장: {png_path}")
        except Exception as e:
            print(f"  ⚠️ PNG 저장 실패 (kaleido 필요): {e}")

    def plot_salary_boxplot(self, salary_data: pd.DataFrame):
        """1. 기업별 연봉 분포 인터랙티브 박스플롯"""
        if salary_data is None or salary_data.empty:
            print("  ⚠️ 연봉 데이터 없음")
            return

        company_col = [c for c in salary_data.columns if "기업" in c or "회사" in c]
        salary_col = [c for c in salary_data.columns if "연봉" in c]
        if not company_col or not salary_col:
            return

        fig = px.box(salary_data, x=company_col[0], y=salary_col[0],
                     title="자율주행/모빌리티 기업별 연봉 분포",
                     template="plotly_white", color=company_col[0])
        fig.update_layout(showlegend=False, xaxis_tickangle=-45)
        self._save(fig, "interactive_salary_boxplot.png")

    def plot_tech_stack_bar(self, tech_data: pd.DataFrame):
        """2. 기술스택 빈도 인터랙티브 막대그래프"""
        if tech_data is None or tech_data.empty:
            print("  ⚠️ 기술스택 데이터 없음")
            return

        name_col = tech_data.columns[0]
        freq_col = tech_data.columns[1]

        fig = px.bar(tech_data.head(20), x=freq_col, y=name_col, orientation="h",
                     title="자율주행/모빌리티 요구 기술스택 TOP 20",
                     template="plotly_white", color=freq_col, color_continuous_scale="Blues")
        fig.update_layout(yaxis=dict(autorange="reversed"), showlegend=False)
        self._save(fig, "interactive_tech_stack_bar.png")

    def plot_company_radar(self, company_data: pd.DataFrame):
        """3. 기업 평점 비교 인터랙티브 레이더차트"""
        if company_data is None or company_data.empty:
            print("  ⚠️ 기업 평점 데이터 없음")
            return

        company_col = [c for c in company_data.columns if "기업" in c]
        if not company_col:
            return

        rating_cols = [c for c in company_data.columns if c != company_col[0]]
        if len(rating_cols) < 3:
            return

        fig = go.Figure()
        for _, row in company_data.head(5).iterrows():
            values = [float(row.get(c, 0)) for c in rating_cols]
            values += values[:1]
            categories = rating_cols + [rating_cols[0]]
            fig.add_trace(go.Scatterpolar(r=values, theta=categories,
                                          fill="toself", name=row[company_col[0]]))

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
            title="자율주행/모빌리티 기업 평점 비교 레이더차트",
            template="plotly_white",
        )
        self._save(fig, "interactive_company_radar.png")

    def plot_trend_line(self, trend_data: pd.DataFrame):
        """4. 채용 트렌드 인터랙티브 라인차트"""
        if trend_data is None or trend_data.empty:
            print("  ⚠️ 트렌드 데이터 없음")
            return

        if isinstance(trend_data, pd.DataFrame) and len(trend_data.columns) >= 2:
            x_col, y_col = trend_data.columns[0], trend_data.columns[1]
            fig = px.line(trend_data, x=x_col, y=y_col,
                          title="자율주행/모빌리티 채용 트렌드", template="plotly_white")
            fig.update_xaxes(rangeslider_visible=True)
            self._save(fig, "interactive_trend_line.png")

    def plot_sankey(self, flow_data: pd.DataFrame):
        """5. 기업-직무-기술스택 산키 다이어그램"""
        if flow_data is None or flow_data.empty:
            print("  ⚠️ 플로우 데이터 없음")
            return

        if len(flow_data.columns) < 3:
            return

        source_col, target_col, value_col = flow_data.columns[:3]
        all_labels = list(set(flow_data[source_col].tolist() + flow_data[target_col].tolist()))
        label_map = {label: i for i, label in enumerate(all_labels)}

        fig = go.Figure(data=[go.Sankey(
            node=dict(pad=15, thickness=20, label=all_labels,
                      color=px.colors.qualitative.Set3[:len(all_labels)]),
            link=dict(
                source=[label_map[s] for s in flow_data[source_col]],
                target=[label_map[t] for t in flow_data[target_col]],
                value=flow_data[value_col],
            ),
        )])
        fig.update_layout(title="기업-직무-기술스택 산키 다이어그램", template="plotly_white")
        self._save(fig, "interactive_sankey.png")

    def plot_tech_cooccurrence_heatmap(self, cooc_data: pd.DataFrame):
        """6. 기술스택 동시 출현 인터랙티브 히트맵"""
        if cooc_data is None or cooc_data.empty:
            print("  ⚠️ 동시출현 데이터 없음")
            return

        fig = px.imshow(cooc_data, text_auto=True, color_continuous_scale="Blues",
                        title="기술스택 동시 출현 히트맵", template="plotly_white")
        self._save(fig, "interactive_cooccurrence_heatmap.png")

    def plot_company_positioning_scatter(self, company_data: pd.DataFrame):
        """7. 자율주행/모빌리티 기업 포지셔닝 맵 인터랙티브 산점도"""
        if company_data is None or company_data.empty:
            print("  ⚠️ 기업 포지셔닝 데이터 없음")
            return

        cols = company_data.columns.tolist()
        x_col = next((c for c in cols if "규모" in c or "직원" in c), cols[0] if cols else None)
        y_col = next((c for c in cols if "연봉" in c), cols[1] if len(cols) > 1 else None)
        size_col = next((c for c in cols if "공고" in c or "채용" in c), None)
        color_col = next((c for c in cols if "도메인" in c or "분야" in c), None)
        name_col = next((c for c in cols if "기업" in c or "회사" in c), None)

        if not x_col or not y_col:
            return

        fig = px.scatter(
            company_data, x=x_col, y=y_col,
            size=size_col if size_col else None,
            color=color_col if color_col else None,
            hover_name=name_col if name_col else None,
            title="자율주행/모빌리티 기업 포지셔닝 맵",
            template="plotly_white",
        )
        self._save(fig, "interactive_company_positioning.png")

    def plot_domain_sunburst(self, domain_data: pd.DataFrame):
        """8. 자율주행/모빌리티 도메인 선버스트 차트"""
        if domain_data is None or domain_data.empty:
            print("  ⚠️ 도메인 데이터 없음")
            return

        if len(domain_data.columns) >= 3:
            parent_col, child_col, value_col = domain_data.columns[:3]
            labels = ["자율주행/모빌리티"] + domain_data[parent_col].unique().tolist() + domain_data[child_col].tolist()
            parents = [""] + ["자율주행/모빌리티"] * domain_data[parent_col].nunique()
            parents += domain_data[parent_col].tolist()
            values = [0] + [domain_data[domain_data[parent_col] == p][value_col].sum()
                            for p in domain_data[parent_col].unique()]
            values += domain_data[value_col].tolist()

            fig = go.Figure(go.Sunburst(
                labels=labels, parents=parents, values=values,
                branchvalues="total",
            ))
        else:
            name_col = domain_data.columns[0]
            value_col = domain_data.columns[1]
            fig = px.sunburst(
                domain_data, path=[name_col], values=value_col,
                title="자율주행/모빌리티 도메인 선버스트 차트",
            )

        fig.update_layout(title="자율주행/모빌리티 도메인 선버스트 차트", template="plotly_white")
        self._save(fig, "interactive_domain_sunburst.png")

    def generate_all(self, data_dict: dict):
        """전체 인터랙티브 차트 생성 (8종)"""
        print("=" * 60)
        print("🎨 인터랙티브 시각화 생성 (8종)")
        print("=" * 60)

        if data_dict.get("salary") is not None:
            self.plot_salary_boxplot(data_dict["salary"])
        if data_dict.get("tech_freq") is not None:
            self.plot_tech_stack_bar(data_dict["tech_freq"])
        if data_dict.get("company_radar") is not None:
            self.plot_company_radar(data_dict["company_radar"])
        if data_dict.get("trend") is not None:
            self.plot_trend_line(data_dict["trend"])
        if data_dict.get("sankey") is not None:
            self.plot_sankey(data_dict["sankey"])
        if data_dict.get("cooccurrence") is not None:
            self.plot_tech_cooccurrence_heatmap(data_dict["cooccurrence"])
        if data_dict.get("company_positioning") is not None:
            self.plot_company_positioning_scatter(data_dict["company_positioning"])
        if data_dict.get("domain_sunburst") is not None:
            self.plot_domain_sunburst(data_dict["domain_sunburst"])

        print("\n✅ 인터랙티브 차트 생성 완료!")
