import { memo } from "react";
import s from "./StatusDot.module.css";

const StatusDot = memo(({ status }) => {
  const cls = status === "OPTIMAL" ? s.optimal : status === "NOMINAL" ? s.nominal : s.other;
  return <span className={`${s.dot} ${cls}`} />;
});

StatusDot.displayName = "StatusDot";
export default StatusDot;
