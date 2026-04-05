import { memo } from "react";
import s from "./ReportButton.module.css";

const ReportButton = memo(({ onClick, full }) => (
  <button className={s.btn} onClick={onClick} aria-label={full ? "Generate full report" : "Generate report"}>
    {"\u2399"} {full ? "FULL REPORT" : "REPORT"}
  </button>
));

ReportButton.displayName = "ReportButton";
export default ReportButton;
