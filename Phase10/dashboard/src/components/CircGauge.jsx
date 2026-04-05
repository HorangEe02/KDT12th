import { memo } from "react";
import s from "./CircGauge.module.css";

const CircGauge = memo(({ value, size = 120, stroke = 6, color = "var(--cyan)" }) => {
  const r = (size - stroke) / 2, circ = 2 * Math.PI * r, off = circ * (1 - value / 100);
  return (
    <svg width={size} height={size} className={s.gauge}>
      <circle cx={size/2} cy={size/2} r={r} className={s.track} strokeWidth={stroke} />
      <circle cx={size/2} cy={size/2} r={r} className={s.value} stroke={color} strokeWidth={stroke}
        strokeDasharray={circ} strokeDashoffset={off}
        style={{ filter: `drop-shadow(0 0 6px ${color}60)` }} />
    </svg>
  );
});

CircGauge.displayName = "CircGauge";
export default CircGauge;
