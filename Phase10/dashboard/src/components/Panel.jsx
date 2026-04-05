import { memo } from "react";
import s from "./Panel.module.css";

const Panel = memo(({ children, style, glow, className, onClick, onMouseEnter, onMouseLeave }) => (
  <div
    className={`${s.panel} ${glow ? s.glow : ""} ${className || ""}`}
    style={style}
    onClick={onClick}
    onMouseEnter={onMouseEnter}
    onMouseLeave={onMouseLeave}
  >
    {children}
  </div>
));

Panel.displayName = "Panel";
export default Panel;
