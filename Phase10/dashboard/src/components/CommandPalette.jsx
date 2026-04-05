import { useRef, useEffect, useState, useMemo, memo } from "react";
import { createPortal } from "react-dom";
import { useNavigate } from "react-router-dom";
import { useSearch } from "../context/SearchContext";
import useSearchIndex from "../hooks/useSearchIndex";
import s from "./CommandPalette.module.css";

// 라우트 매핑 (App.jsx와 동일)
const ROUTE_MAP = {
  dashboard: "/", casting: "/casting", segtile: "/segmentation",
  pcb: "/pcb", nlp: "/maintenance", settings: "/settings", history: "/history",
};

// 결과 타입별 그룹 순서
const GROUP_ORDER = ["page", "metric", "model", "setting"];
const GROUP_LABELS = { page: "PAGES", metric: "METRICS", model: "MODELS", setting: "SETTINGS" };

// 하이라이트 렌더링
const HighlightText = memo(({ text, ranges }) => {
  if (!ranges?.length) return text;
  const parts = [];
  let last = 0;
  ranges.forEach(([start, end]) => {
    if (start > last) parts.push(text.slice(last, start));
    parts.push(<span key={start} className={s.highlight}>{text.slice(start, end)}</span>);
    last = end;
  });
  if (last < text.length) parts.push(text.slice(last));
  return <>{parts}</>;
});
HighlightText.displayName = "HighlightText";

const CommandPalette = () => {
  const { isOpen, query, setQuery, closeSearch } = useSearch();
  const { search } = useSearchIndex();
  const navigate = useNavigate();
  const inputRef = useRef(null);
  const [activeIdx, setActiveIdx] = useState(0);

  const results = useMemo(() => search(query), [search, query]);

  // 그룹화
  const grouped = useMemo(() => {
    const map = {};
    results.forEach(item => {
      const g = GROUP_LABELS[item.type] || "OTHER";
      if (!map[g]) map[g] = [];
      map[g].push(item);
    });
    return GROUP_ORDER
      .map(type => ({ label: GROUP_LABELS[type], items: map[GROUP_LABELS[type]] || [] }))
      .filter(g => g.items.length > 0);
  }, [results]);

  // 평탄화된 결과 (키보드 탐색용)
  const flatResults = useMemo(() => grouped.flatMap(g => g.items), [grouped]);

  // 오픈 시 포커스
  useEffect(() => {
    if (isOpen) {
      setActiveIdx(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  // 쿼리 변경 시 인덱스 리셋
  useEffect(() => { setActiveIdx(0); }, [query]);

  const executeAction = (item) => {
    closeSearch();
    const path = ROUTE_MAP[item.action.path] || "/";
    navigate(path);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Escape") { closeSearch(); return; }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIdx(prev => Math.min(prev + 1, flatResults.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIdx(prev => Math.max(prev - 1, 0));
    } else if (e.key === "Enter" && flatResults[activeIdx]) {
      e.preventDefault();
      executeAction(flatResults[activeIdx]);
    }
  };

  if (!isOpen) return null;

  return createPortal(
    <div className={s.overlay} onClick={closeSearch}>
      <div className={s.palette} onClick={e => e.stopPropagation()} role="dialog" aria-modal="true" aria-label="Command palette">
        {/* 입력 */}
        <div className={s.inputWrap}>
          <span className={s.searchIcon}>{"\u2315"}</span>
          <input
            ref={inputRef}
            className={s.input}
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search pages, models, settings..."
            spellCheck={false}
            autoComplete="off"
          />
          <span className={s.shortcut}>ESC</span>
        </div>

        {/* 결과 */}
        <div className={s.results}>
          {flatResults.length === 0 && query.trim() ? (
            <div className={s.empty}>No results for &quot;{query}&quot;</div>
          ) : (
            grouped.map(group => (
              <div key={group.label}>
                <div className={s.groupLabel}>{group.label}</div>
                {group.items.map(item => {
                  const idx = flatResults.indexOf(item);
                  return (
                    <div
                      key={item.id}
                      className={`${s.item} ${idx === activeIdx ? s.itemActive : ""}`}
                      onClick={() => executeAction(item)}
                      onMouseEnter={() => setActiveIdx(idx)}
                    >
                      <span className={s.itemIcon}>{item.icon}</span>
                      <div className={s.itemContent}>
                        <div className={s.itemLabel}>
                          <HighlightText text={item.label} ranges={item.ranges} />
                        </div>
                        <div className={s.itemDesc}>{item.description}</div>
                      </div>
                      <span className={s.itemArrow}>{"\u2192"}</span>
                    </div>
                  );
                })}
              </div>
            ))
          )}
        </div>

        {/* 푸터 */}
        <div className={s.footer}>
          <span><span className={s.footerKey}>{"\u2191\u2193"}</span> Navigate</span>
          <span><span className={s.footerKey}>{"\u21b5"}</span> Select</span>
          <span><span className={s.footerKey}>ESC</span> Close</span>
        </div>
      </div>
    </div>,
    document.body
  );
};

export default CommandPalette;
