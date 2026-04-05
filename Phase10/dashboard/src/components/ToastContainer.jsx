import { memo } from "react";
import { useToast } from "../context/ToastContext";
import s from "./ToastContainer.module.css";

const levelIcons = { crit: "\u26a0", warn: "\u26a1", ok: "\u2713", info: "\u25c9" };

const ToastContainer = memo(() => {
  const { toasts, removeToast } = useToast();

  if (toasts.length === 0) return null;

  return (
    <div className={s.container} aria-live="polite" aria-label="Notifications">
      {toasts.map(t => (
        <div key={t.id}
          className={`${s.toast} ${s[t.level] || s.info} ${t.exiting ? s.exit : ""}`}
          onClick={() => removeToast(t.id)}
          role="alert">
          <span className={s.icon}>{levelIcons[t.level] || levelIcons.info}</span>
          <span className={s.message}>{t.message}</span>
          <button className={s.close} aria-label="Dismiss">{"\u00d7"}</button>
        </div>
      ))}
    </div>
  );
});

ToastContainer.displayName = "ToastContainer";
export default ToastContainer;
