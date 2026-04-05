import s from "./PrintLayout.module.css";
import METRICS from "../data/metrics";
import PAGE_CONTENT from "../data/pageContent";
import useTranslation from "../hooks/useTranslation";

const PrintLayout = ({ modules }) => {
  const { t, locale } = useTranslation();

  if (!modules || modules.length === 0) return null;

  const now = new Date().toLocaleDateString(locale === "ko" ? "ko-KR" : "en-GB", {
    year: "numeric", month: "long", day: "numeric", hour: "2-digit", minute: "2-digit",
  });

  return (
    <div className={`${s.layout} printLayout`}>
      {/* 표지 */}
      <div className={s.header}>
        <div className={s.headerTitle}>{t("report.title")}</div>
        <div className={s.headerSub}>{t("report.subtitle")}</div>
        <div className={s.headerDate}>Generated: {now}</div>
      </div>

      {/* 모듈별 섹션 */}
      {modules.map((modId, idx) => {
        const contentKey = modId === "segtile" ? "segtile_mag" : modId;
        const content = PAGE_CONTENT[contentKey];
        const metric = METRICS[modId];
        if (!content || !metric) return null;

        return (
          <div key={modId} className={`${s.section} ${idx > 0 ? "printSection" : ""}`}>
            <div className={s.sectionTitle}>{content.title}</div>

            <div className={s.metricRow}>
              <span className={s.metricValue}>{metric.value}%</span>
              <span className={s.metricLabel}>{metric.label} — {metric.model}</span>
            </div>

            <div className={s.datasetList}>
              {content.datasetKeys.map((k, i) => <div key={i}>{t(k)}</div>)}
            </div>

            <table className={s.table}>
              <thead>
                <tr>{content.columns.map(c => <th key={c}>{content.colLabels[c]}</th>)}</tr>
              </thead>
              <tbody>
                {content.models.map((row, i) => (
                  <tr key={i} className={row.best ? s.bestRow : ""}>
                    {content.columns.map(c => (
                      <td key={c}>
                        {c === "name" ? `${row.best ? "\u2605 " : ""}${row[c]}` :
                          row[c] !== undefined ? (typeof row[c] === "number" ? row[c].toFixed(2) : row[c]) : "\u2014"}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>

            {content.insightKeys && (
              <div className={s.insightList}>
                {content.insightKeys.map((k, i) => (
                  <div key={i} className={s.insight}>
                    <span className={s.insightIcon}>{"\u25b8"}</span>{t(k)}
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}

      <div className={s.footer}>{t("report.footer")}</div>
    </div>
  );
};

export default PrintLayout;
