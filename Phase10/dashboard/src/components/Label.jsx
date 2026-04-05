import { memo } from "react";
import s from "./Label.module.css";

const Label = memo(({ children, className, variant }) => (
  <span className={`${s.label} ${variant ? s[variant] : ""} ${className || ""}`}>{children}</span>
));

Label.displayName = "Label";
export default Label;
