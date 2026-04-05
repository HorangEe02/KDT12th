import { useState } from "react";
import s from "./SegTile.module.css";
import useTranslation from "../hooks/useTranslation";
import PAGE_CONTENT from "../data/pageContent";
import SubPage from "./SubPage";

const PageSegTile = ({ onReport }) => {
  const { t } = useTranslation();
  const [ds, setDs] = useState("mag");
  const c = ds === "mag" ? PAGE_CONTENT.segtile_mag : PAGE_CONTENT.segtile_crack;
  return (
    <SubPage id="segtile" title={c.title}
      dataset={c.datasetKeys.map(k => t(k))}
      insights={c.insightKeys.map(k => t(k))}
      models={c.models} columns={c.columns} colLabels={c.colLabels}
      images={c.images} imgBase={c.imgBase} onReport={onReport}
      extra={
        <div className={s.toggleGroup}>
          {[{ k: "mag", l: "MAGNETIC_TILE" }, { k: "crack", l: "CRACK_SEG" }].map(b => (
            <button key={b.k} onClick={() => setDs(b.k)}
              className={`${s.toggleBtn} ${ds === b.k ? s.toggleBtnActive : ""}`}>
              {b.l}
            </button>
          ))}
        </div>
      }
    />
  );
};

export default PageSegTile;
