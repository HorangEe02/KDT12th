import { useEffect } from "react";
import s from "./ImgModal.module.css";

const ImgModal = ({ src, onClose }) => {
  // ESC 키로 모달 닫기
  useEffect(() => {
    if (!src) return;
    const handler = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [src, onClose]);

  if (!src) return null;

  return (
    <div className={s.overlay} onClick={onClose} role="dialog" aria-modal="true" aria-label="Image viewer">
      <img src={src} alt="Analysis output enlarged" className={s.image} />
    </div>
  );
};

export default ImgModal;
