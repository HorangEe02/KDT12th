import { useMemo, useCallback } from "react";
import NAV from "../data/navigation";
import METRICS from "../data/metrics";
import MODEL_DATA from "../data/models";
import fuzzyMatch from "../utils/fuzzyMatch";

// 검색 인덱스 빌드 (정적 — 앱 로드 시 1회)
const buildIndex = () => {
  const items = [];

  // 페이지
  NAV.forEach(n => {
    items.push({
      id: `page:${n.id}`, type: "page", icon: n.icon,
      label: n.label, description: n.code,
      action: { type: "navigate", path: n.id },
      keywords: [n.label, n.code, n.id],
    });
  });

  // 메트릭 + 모델
  Object.entries(METRICS).forEach(([k, m]) => {
    items.push({
      id: `metric:${k}`, type: "metric", icon: "\u25ce",
      label: `${m.model} — ${m.value}% ${m.label}`, description: `${NAV.find(n => n.id === k)?.label || k}`,
      action: { type: "navigate", path: k },
      keywords: [m.model, m.label, k],
    });
  });

  // 개별 모델
  Object.entries(MODEL_DATA).forEach(([module, models]) => {
    models.forEach(m => {
      const metricStr = m.acc ? `ACC ${m.acc}%` : m.dice ? `Dice ${m.dice}%` : m.map50 ? `mAP ${m.map50}%` : "";
      items.push({
        id: `model:${module}:${m.name}`, type: "model", icon: "\u2b22",
        label: m.name, description: `${metricStr} — ${NAV.find(n => n.id === module)?.label || module}`,
        action: { type: "navigate", path: module },
        keywords: [m.name, module, metricStr],
      });
    });
  });

  // 설정
  [
    { label: "Dark Mode", desc: "Toggle dark/light theme" },
    { label: "Chart Animations", desc: "Enable chart transitions" },
    { label: "Language", desc: "Switch between English and Korean" },
    { label: "Live Alert Feed", desc: "Real-time alert generation" },
    { label: "Alert Threshold", desc: "Minimum confidence score" },
    { label: "Auto Refresh", desc: "Automatic data updates" },
    { label: "Refresh Interval", desc: "Data polling frequency" },
  ].forEach(s => {
    items.push({
      id: `setting:${s.label}`, type: "setting", icon: "\u2699",
      label: s.label, description: s.desc,
      action: { type: "navigate", path: "settings" },
      keywords: [s.label, s.desc, "settings"],
    });
  });

  return items;
};

export default function useSearchIndex() {
  const index = useMemo(buildIndex, []);

  const search = useCallback((query) => {
    if (!query.trim()) {
      // 빈 쿼리: 페이지 + 최근 항목
      return index.filter(i => i.type === "page").slice(0, 8);
    }
    return index
      .map(item => {
        const combined = [item.label, ...item.keywords].join(" ");
        const result = fuzzyMatch(query, combined);
        return { ...item, ...result };
      })
      .filter(i => i.match)
      .sort((a, b) => b.score - a.score)
      .slice(0, 12);
  }, [index]);

  return { index, search };
}
