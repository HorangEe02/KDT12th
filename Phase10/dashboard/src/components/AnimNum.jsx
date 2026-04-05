import { useState, useEffect, memo } from "react";
import s from "./AnimNum.module.css";

const AnimNum = memo(({ value, suffix = "%", dur = 1200 }) => {
  const [cur, setCur] = useState(0);
  useEffect(() => {
    let start = 0;
    const step = value / (dur / 16);
    const id = setInterval(() => {
      start += step;
      if (start >= value) { setCur(value); clearInterval(id); }
      else setCur(start);
    }, 16);
    return () => clearInterval(id);
  }, [value, dur]);
  return <>{cur.toFixed(1)}<span className={s.suffix}>{suffix}</span></>;
});

AnimNum.displayName = "AnimNum";
export default AnimNum;
