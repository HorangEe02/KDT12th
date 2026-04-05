import { useState, useMemo } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import s from "./SubPage.module.css";
import METRICS from "../data/metrics";
import AnimNum from "../components/AnimNum";
import CircGauge from "../components/CircGauge";
import StatusDot from "../components/StatusDot";
import Label from "../components/Label";
import Panel from "../components/Panel";
import ImgModal from "../components/ImgModal";
import ReportButton from "../components/ReportButton";
import useTranslation from "../hooks/useTranslation";
import { useChartColors } from "../utils/cssVar";

// ─── CSV 내보내기 유틸 ───
const exportCSV = (models, columns, colLabels) => {
  const header = columns.map(c => colLabels[c]).join(",");
  const rows = models.map(row =>
    columns.map(c => row[c] !== undefined ? row[c] : "").join(",")
  );
  const csv = [header, ...rows].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "model_benchmark.csv";
  a.click();
  URL.revokeObjectURL(url);
};

// ─── 차트 툴팁 ───
const ChartTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className={s.chartTooltip}>
      <div className={s.chartTooltipLabel}>{d.name}</div>
      {payload.map((p, i) => (
        <div key={i} className={s.chartTooltipRow}>
          {p.name}: <strong>{p.value}</strong>
        </div>
      ))}
    </div>
  );
};

const SubPage = ({ id, title, dataset, models, columns, colLabels, images, imgBase, insights, extra, onReport }) => {
  const { t } = useTranslation();
  const cc = useChartColors();
  const [modal, setModal] = useState(null);
  const [viewMode, setViewMode] = useState("table"); // table | chart
  const m = METRICS[id];

  // 차트용 수치 컬럼만 필터
  const numericCols = useMemo(() =>
    columns.filter(c => c !== "name" && c !== "ds" && c !== "params" && models.some(r => typeof r[c] === "number")),
    [columns, models]
  );
  const [chartMetric, setChartMetric] = useState(numericCols[0] || "");

  return (
    <div className={s.container}>
      <ImgModal src={modal} onClose={() => setModal(null)} />

      {/* 상단: 핵심 메트릭 + 데이터셋 */}
      <div className={s.topGrid}>
        <Panel glow className={s.metricPanel}>
          <div className={s.gaugeWrap}>
            <CircGauge value={m.value} size={140} stroke={7} />
            <div className={s.gaugeValue}>
              <AnimNum value={m.value} />
            </div>
          </div>
          <Label>{m.label}</Label>
          <div className={s.modelBadge}>{m.model}</div>
          <div className={s.statusRow}><StatusDot status={m.status} /><Label variant="sm">{m.status}</Label></div>
        </Panel>

        <Panel>
          <Label>{t("subpage.dataset")}</Label>
          <div className={s.datasetInfo}>
            {dataset.map((d, i) => <div key={i} className={s.datasetRow}>{d}</div>)}
          </div>
          {extra}
        </Panel>
      </div>

      {/* 모델 비교 — 테이블/차트 토글 */}
      <Panel>
        <div className={s.benchmarkHeader}>
          <Label>{t("subpage.benchmark")}</Label>
          <div className={s.benchmarkControls}>
            <button className={`${s.viewBtn} ${viewMode === "table" ? s.viewBtnActive : ""}`} onClick={() => setViewMode("table")} aria-label="Table view">
              {"\u2630"}
            </button>
            <button className={`${s.viewBtn} ${viewMode === "chart" ? s.viewBtnActive : ""}`} onClick={() => setViewMode("chart")} aria-label="Chart view">
              {"\u2593"}
            </button>
            <button className={s.exportBtn} onClick={() => exportCSV(models, columns, colLabels)} aria-label="Export CSV">
              {"\u2913"} CSV
            </button>
            {onReport && <ReportButton onClick={() => onReport([id])} />}
          </div>
        </div>

        {viewMode === "table" ? (
          <div className={s.tableWrap}>
            <table className={s.table}>
              <thead>
                <tr>{columns.map(c => (
                  <th key={c} className={`${s.th} ${c === "name" ? s.thLeft : s.thCenter}`}>{colLabels[c]}</th>
                ))}</tr>
              </thead>
              <tbody>
                {models.map((row, i) => (
                  <tr key={i} className={`${s.tr} ${row.best ? s.trBest : ""}`}>
                    {columns.map(c => (
                      <td key={c} className={`${s.td} ${c === "name" || c === "ds" ? s.tdLeft : s.tdCenter} ${row.best && c !== "name" && c !== "ds" ? s.tdBest : ""}`}>
                        {c === "name" ? <>{row.best && <span className={s.bestStar}>{"\u2605"} </span>}{row[c]}</> : (row[c] !== undefined ? (typeof row[c] === "number" ? row[c].toFixed(2) : row[c]) : "\u2014")}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className={s.chartArea}>
            {/* 메트릭 선택 */}
            <div className={s.metricSelector}>
              {numericCols.map(c => (
                <button key={c} onClick={() => setChartMetric(c)}
                  className={`${s.metricBtn} ${chartMetric === c ? s.metricBtnActive : ""}`}>
                  {colLabels[c]}
                </button>
              ))}
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={models} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={cc.grid} />
                <XAxis dataKey="name" tick={{ fill: cc.label, fontSize: 10, fontFamily: "'JetBrains Mono'" }} axisLine={{ stroke: cc.grid }} tickLine={false} />
                <YAxis tick={{ fill: cc.tick, fontSize: 9, fontFamily: "'JetBrains Mono'" }} axisLine={false} tickLine={false} />
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey={chartMetric} name={colLabels[chartMetric]} radius={[4, 4, 0, 0]} maxBarSize={50}>
                  {models.map((entry, i) => (
                    <Cell key={i} fill={entry.best ? cc.cyan : cc.grid} stroke={entry.best ? cc.cyan : cc.textMuted} strokeWidth={1} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </Panel>

      {/* 시각화 */}
      <Panel>
        <Label>{t("subpage.output")}</Label>
        <div className={s.gallery}>
          {images.map(img => {
            const src = `/images/${imgBase}/${img.f}`;
            return (
              <div key={img.f} className={s.imgCard} onClick={() => setModal(src)}>
                <img src={src} alt={img.l} loading="lazy" />
                <div className={s.imgLabel}>{img.l}</div>
              </div>
            );
          })}
        </div>
      </Panel>

      {/* 인사이트 */}
      {insights && (
        <Panel>
          <Label>{t("subpage.insights")}</Label>
          <div className={s.insightList}>
            {insights.map((ins, i) => (
              <div key={i} className={s.insightRow}>
                <span className={s.insightIcon}>{"\u25b8"}</span>
                <span className={s.insightText}>{ins}</span>
              </div>
            ))}
          </div>
        </Panel>
      )}
    </div>
  );
};

export default SubPage;
