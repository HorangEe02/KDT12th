import { memo } from "react";
import s from "./MiniChart.module.css";

const MiniChart = memo(({ data, color = "var(--cyan)", w = 200, h = 50 }) => {
  const max = Math.max(...data), min = Math.min(...data);
  const pts = data.map((v, i) => `${(i / (data.length - 1)) * w},${h - ((v - min) / (max - min || 1)) * h}`).join(" ");
  return (
    <svg width={w} height={h} className={s.chart}>
      <polyline points={pts} className={s.line} stroke={color} style={{ filter: `drop-shadow(0 0 3px ${color}40)` }} />
    </svg>
  );
});

MiniChart.displayName = "MiniChart";
export default MiniChart;
