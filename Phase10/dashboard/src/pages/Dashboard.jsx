import { useState, useEffect, useMemo, memo } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from "recharts";
import s from "./Dashboard.module.css";
import METRICS from "../data/metrics";
import NAV from "../data/navigation";
import ALERTS from "../data/alerts";
import useSimStream from "../hooks/useSimStream";
import useTranslation from "../hooks/useTranslation";
import { useSettings } from "../context/SettingsContext";
import { useToast } from "../context/ToastContext";
import { useChartColors } from "../utils/cssVar";
import AnimNum from "../components/AnimNum";
import CircGauge from "../components/CircGauge";
import StatusDot from "../components/StatusDot";
import Label from "../components/Label";
import Panel from "../components/Panel";

// ─── 커스텀 툴팁 ───
const ChartTooltip = memo(({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className={s.tooltip}>
      <div className={s.tooltipLabel}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} className={s.tooltipRow}>
          <span className={`${s.tooltipDot} ${p.dataKey === "yield" ? s.dotCyan : s.dotOrange}`} />
          <span>{p.name}: <strong>{p.value}%</strong></span>
        </div>
      ))}
    </div>
  );
});
ChartTooltip.displayName = "ChartTooltip";

const radarData = [
  { metric: "Casting", value: 96.5 },
  { metric: "SegTile", value: 80.0 },
  { metric: "PCB", value: 95.0 },
  { metric: "NLP", value: 97.4 },
];

const MONO = "'JetBrains Mono', monospace";

const PageDashboard = ({ onNavigate, onReport }) => {
  const { t, locale } = useTranslation();
  const { data: streamData, paused, togglePause, range, setRange } = useSimStream();
  const { settings } = useSettings();
  const { addToast } = useToast();
  const cc = useChartColors();
  const entries = Object.entries(METRICS);

  // 차트 틱 스타일 (테마 연동)
  const tickStyle = useMemo(() => ({ fill: cc.tick, fontSize: 9, fontFamily: MONO }), [cc.tick]);
  const labelTickStyle = useMemo(() => ({ fill: cc.label, fontSize: 10, fontFamily: MONO }), [cc.label]);

  // 실시간 알림 시뮬레이션
  const [alerts, setAlerts] = useState(ALERTS);
  useEffect(() => {
    if (!settings.liveAlerts) return;
    const templates = [
      { key: "alert.tpl.0", lvl: "ok" },
      { key: "alert.tpl.1", lvl: "crit" },
      { key: "alert.tpl.2", lvl: "warn" },
      { key: "alert.tpl.3", lvl: "ok" },
      { key: "alert.tpl.4", lvl: "warn" },
      { key: "alert.tpl.5", lvl: "crit" },
    ];
    const id = setInterval(() => {
      const tpl = templates[Math.floor(Math.random() * templates.length)];
      const now = new Date();
      const vars = {
        n: String(Math.floor(2000 + Math.random() * 8000)),
        u: String(Math.floor(1 + Math.random() * 9)),
        c: String(Math.floor(80 + Math.random() * 19)),
        l: ["A", "B", "C"][Math.floor(Math.random() * 3)],
      };
      const newAlert = {
        t: now.toLocaleTimeString(locale === "ko" ? "ko-KR" : "en-GB"),
        msg: t(tpl.key, vars),
        lvl: tpl.lvl,
        isNew: true,
      };
      setAlerts(prev => [newAlert, ...prev.slice(0, 7)]);
      if (newAlert.lvl === "crit") addToast(newAlert.msg, "crit", 5000);
    }, 5000);
    return () => clearInterval(id);
  }, [settings.liveAlerts, addToast]);

  return (
    <div className={s.container}>
      {/* 메트릭 카드 */}
      <div className={s.metricsGrid}>
        {entries.map(([k, m]) => (
          <Panel key={k} glow={m.status === "OPTIMAL"} className={s.metricCard}
            onClick={() => onNavigate && onNavigate(k)}>
            <div className={s.gaugeWrap}>
              <CircGauge value={m.value} size={100} color={m.status === "OPTIMAL" ? "var(--cyan)" : "var(--orange)"} />
              <div className={s.gaugeValue}><AnimNum value={m.value} /></div>
            </div>
            <Label>{m.label}</Label>
            <div className={s.modelName}>{m.model}</div>
            <div className={s.statusRow}><StatusDot status={m.status} /><Label variant="sm">{m.status}</Label></div>
          </Panel>
        ))}
      </div>

      <div className={s.midGrid}>
        {/* 레이더 차트 */}
        <Panel>
          <Label>{t("dashboard.radar_title")}</Label>
          <div className={s.radarWrap}>
            <ResponsiveContainer width="100%" height={200}>
              <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="70%">
                <PolarGrid stroke={cc.grid} />
                <PolarAngleAxis dataKey="metric" tick={labelTickStyle} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: cc.tick, fontSize: 9 }} axisLine={false} />
                <Radar name="Performance" dataKey="value" stroke={cc.cyan} fill={cc.cyan} fillOpacity={0.15} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
          <div className={s.healthList}>
            {entries.map(([k, m]) => (
              <div key={k} className={s.healthRow}>
                <div className={s.healthLabel}>
                  <StatusDot status={m.status} />
                  <span className={s.healthCode}>{NAV.find(n => n.id === k)?.code || k}</span>
                </div>
                <span className={s.healthValue}>{m.value}%</span>
              </div>
            ))}
          </div>
        </Panel>

        {/* 생산 트렌드 */}
        <Panel>
          <div className={s.chartHeader}>
            <Label>{t("dashboard.trend_title")}</Label>
            <div className={s.chartControls}>
              {["1H", "6H", "24H", "7D"].map(r => (
                <button key={r} onClick={() => setRange(r)}
                  className={`${s.rangeBtn} ${range === r ? s.rangeBtnActive : ""}`}>{r}</button>
              ))}
              <button onClick={togglePause} className={`${s.rangeBtn} ${paused ? s.rangeBtnPaused : ""}`}
                aria-label={paused ? "Resume" : "Pause"}>
                {paused ? "\u25b6" : "\u275a\u275a"}
              </button>
            </div>
          </div>
          <div className={s.chartWrap}>
            <ResponsiveContainer width="100%" height={160}>
              <AreaChart data={streamData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="gradYield" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={cc.cyan} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={cc.cyan} stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gradDefect" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={cc.orange} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={cc.orange} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={cc.grid} />
                <XAxis dataKey="time" tick={tickStyle} axisLine={{ stroke: cc.grid }} tickLine={false} interval="preserveStartEnd" />
                <YAxis tick={tickStyle} axisLine={false} tickLine={false} />
                <Tooltip content={<ChartTooltip />} />
                <Area type="monotone" dataKey="yield" name="Yield" stroke={cc.cyan} fill="url(#gradYield)" strokeWidth={2} dot={false} activeDot={{ r: 4, fill: cc.cyan }} />
                <Area type="monotone" dataKey="defect" name="Defect" stroke={cc.orange} fill="url(#gradDefect)" strokeWidth={2} dot={false} activeDot={{ r: 4, fill: cc.orange }} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className={s.legend}>
            <Label variant="cyan">{"\u25cf"} {t("dashboard.yield")}</Label>
            <Label variant="orange">{"\u25cf"} {t("dashboard.defect")}</Label>
            {paused && <Label variant="red">{"\u25cf"} {t("dashboard.paused")}</Label>}
          </div>
        </Panel>
      </div>

      {/* 알림 피드 */}
      <Panel>
        <div className={s.alertHeader}>
          <Label>{t("dashboard.alert_title")}</Label>
          <span className={s.alertLive}>{"\u25cf"} {t("dashboard.live")}</span>
        </div>
        <div className={s.alertList}>
          {alerts.map((a, i) => (
            <div key={`${a.t}-${i}`} className={`${s.alertRow} ${a.isNew && i === 0 ? s.alertNew : ""}`}>
              <span className={s.alertTime}>{a.t}</span>
              <span className={`${s.alertDot} ${a.lvl === "crit" ? s.alertDotCrit : a.lvl === "warn" ? s.alertDotWarn : s.alertDotOk}`} />
              <span className={a.lvl === "crit" ? s.alertMsgCrit : s.alertMsg}>{a.msg}</span>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
};

export default PageDashboard;
