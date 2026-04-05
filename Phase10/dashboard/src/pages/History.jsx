import { useState, useMemo, memo } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import s from "./History.module.css";
import HISTORY from "../data/modelHistory";
import useTranslation from "../hooks/useTranslation";
import { useChartColors } from "../utils/cssVar";
import Label from "../components/Label";
import Panel from "../components/Panel";

const MODULES = [
  { id: "casting", label: "CASTING" },
  { id: "segtile", label: "SEGTILE" },
  { id: "pcb", label: "PCB" },
  { id: "nlp", label: "NLP" },
];

const RANGES = [
  { id: "ALL", label: "ALL", filter: () => true },
  { id: "LAST10", label: "LAST 10", filter: (_, i, arr) => i >= arr.length - 10 },
  { id: "LAST5", label: "LAST 5", filter: (_, i, arr) => i >= arr.length - 5 },
];

const MONO = "'JetBrains Mono', monospace";

// 차트 툴팁
const ChartTooltip = memo(({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className={s.tooltip}>
      <div className={s.tooltipEpoch}>EPOCH {label}</div>
      {payload.map((p, i) => (
        <div key={i} className={s.tooltipRow}>
          <span className={s.tooltipDot} style={{ background: p.color }} />
          <span>{p.name}: <strong>{p.value}%</strong></span>
        </div>
      ))}
    </div>
  );
});
ChartTooltip.displayName = "ChartTooltip";

const PageHistory = () => {
  const { t } = useTranslation();
  const cc = useChartColors();
  const [module, setModule] = useState("casting");
  const [range, setRange] = useState("ALL");
  const [selected, setSelected] = useState(new Set());

  // 모델 색상 배열을 CSS 변수에서 생성
  const modelColors = useMemo(() => [cc.cyan, cc.orange, cc.yellow, cc.textDim, cc.red], [cc]);

  const hist = HISTORY[module];

  const toggleModule = (id) => {
    setModule(id);
    setSelected(new Set(HISTORY[id].models));
  };

  useMemo(() => { setSelected(new Set(hist.models)); }, [module]);

  const toggleModel = (name) => {
    setSelected(prev => {
      const next = new Set(prev);
      next.has(name) ? next.delete(name) : next.add(name);
      return next;
    });
  };

  const filteredData = useMemo(() => {
    const rangeFilter = RANGES.find(r => r.id === range)?.filter || (() => true);
    return hist.data.filter(rangeFilter);
  }, [hist.data, range]);

  const tickStyle = useMemo(() => ({ fill: cc.tick, fontSize: 10, fontFamily: MONO }), [cc.tick]);
  const yTickStyle = useMemo(() => ({ fill: cc.tick, fontSize: 9, fontFamily: MONO }), [cc.tick]);

  return (
    <div className={s.container}>
      {/* 모듈 선택 */}
      <Panel>
        <Label>{t("history.select_module")}</Label>
        <div className={s.moduleSelector}>
          {MODULES.map(m => (
            <button key={m.id} onClick={() => toggleModule(m.id)}
              className={`${s.moduleBtn} ${module === m.id ? s.moduleBtnActive : ""}`}>
              {m.label}
            </button>
          ))}
        </div>
      </Panel>

      {/* 학습 곡선 차트 */}
      <Panel>
        <div className={s.chartHeader}>
          <Label>{t("history.training")} — {hist.metricLabel}</Label>
          <div className={s.rangeSelector}>
            {RANGES.map(r => (
              <button key={r.id} onClick={() => setRange(r.id)}
                className={`${s.rangeBtn} ${range === r.id ? s.rangeBtnActive : ""}`}>
                {r.label}
              </button>
            ))}
          </div>
        </div>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={filteredData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={cc.grid} />
            <XAxis dataKey="epoch" tick={tickStyle} axisLine={{ stroke: cc.grid }} tickLine={false}
              label={{ value: "Epoch", position: "insideBottomRight", offset: -5, fill: cc.tick, fontSize: 9 }} />
            <YAxis tick={yTickStyle} axisLine={false} tickLine={false} />
            <Tooltip content={<ChartTooltip />} />
            {hist.models.map((name, i) => (
              selected.has(name) && (
                <Line key={name} type="monotone" dataKey={name} name={name}
                  stroke={modelColors[i]} strokeWidth={name === hist.best ? 2.5 : 1.5}
                  dot={false} activeDot={{ r: 4, fill: modelColors[i] }}
                  strokeDasharray={name === hist.best ? undefined : "5 3"} />
              )
            ))}
          </LineChart>
        </ResponsiveContainer>

        {/* 모델 토글 */}
        <div className={s.modelToggles}>
          {hist.models.map((name, i) => (
            <button key={name} onClick={() => toggleModel(name)}
              className={`${s.modelToggle} ${!selected.has(name) ? s.modelToggleOff : ""}`}
              style={{ color: selected.has(name) ? modelColors[i] : "var(--text-muted)", borderColor: selected.has(name) ? modelColors[i] : "var(--border)" }}>
              <span className={s.modelDot} style={{ background: modelColors[i] }} />
              {name} {name === hist.best ? "\u2605" : ""}
            </button>
          ))}
        </div>
      </Panel>

      {/* 최종 에폭 요약 */}
      <Panel>
        <Label>{t("history.summary")}</Label>
        <table className={s.summaryTable}>
          <thead>
            <tr>
              <th>{t("history.col.model")}</th>
              <th>{t("history.col.epoch1")}</th>
              <th>{t("history.col.epoch10")}</th>
              <th>{t("history.col.final", { n: hist.data.length })}</th>
              <th>{t("history.col.improvement")}</th>
            </tr>
          </thead>
          <tbody>
            {hist.models.map((name, i) => {
              const first = hist.data[0]?.[name] || 0;
              const mid = hist.data[Math.min(9, hist.data.length - 1)]?.[name] || 0;
              const last = hist.data[hist.data.length - 1]?.[name] || 0;
              const isBest = name === hist.best;
              return (
                <tr key={name}>
                  <td style={{ color: modelColors[i] }}>{isBest ? "\u2605 " : ""}{name}</td>
                  <td>{first.toFixed(2)}%</td>
                  <td>{mid.toFixed(2)}%</td>
                  <td className={isBest ? s.bestCell : ""}>{last.toFixed(2)}%</td>
                  <td className={isBest ? s.bestCell : ""}>+{(last - first).toFixed(2)}%p</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Panel>
    </div>
  );
};

export default PageHistory;
