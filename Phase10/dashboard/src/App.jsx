import { useState, useEffect, lazy, Suspense, useCallback } from "react";
import { Routes, Route, useNavigate, useLocation, Navigate } from "react-router-dom";
import s from "./App.module.css";
import NAV from "./data/navigation";
import useTranslation from "./hooks/useTranslation";
import ErrorBoundary from "./components/ErrorBoundary";
import ToastContainer from "./components/ToastContainer";
import CommandPalette from "./components/CommandPalette";
import PrintLayout from "./components/PrintLayout";
import { useSearch } from "./context/SearchContext";
import "./styles/print.css";

// ─── 코드 스플리팅 ───
const PageDashboard = lazy(() => import("./pages/Dashboard"));
const PageCasting = lazy(() => import("./pages/Casting"));
const PageSegTile = lazy(() => import("./pages/SegTile"));
const PagePCB = lazy(() => import("./pages/PCB"));
const PageNLP = lazy(() => import("./pages/NLP"));
const PageSettings = lazy(() => import("./pages/Settings"));
const PageHistory = lazy(() => import("./pages/History"));

const NAV_ORDER = NAV.map(n => n.id);

const ROUTE_MAP = {
  dashboard: "/", casting: "/casting", segtile: "/segmentation",
  pcb: "/pcb", nlp: "/maintenance", history: "/history", settings: "/settings",
};

const PATH_TO_ID = Object.fromEntries(
  Object.entries(ROUTE_MAP).map(([id, path]) => [path, id])
);

export default function App() {
  const { t, locale } = useTranslation();
  const [time, setTime] = useState(new Date());
  const [reportModules, setReportModules] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();
  const { openSearch } = useSearch();

  const handleReport = useCallback((modules) => {
    setReportModules(modules);
    setTimeout(() => { window.print(); setReportModules(null); }, 100);
  }, []);

  useEffect(() => {
    const id = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const currentId = PATH_TO_ID[location.pathname] || "dashboard";
  const curNav = NAV.find(n => n.id === currentId);

  const handleNavigate = useCallback((id) => {
    navigate(ROUTE_MAP[id] || "/");
  }, [navigate]);

  useEffect(() => {
    const handler = (e) => {
      if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT" || e.target.tagName === "TEXTAREA") return;
      const num = parseInt(e.key);
      if (num >= 1 && num <= NAV_ORDER.length) {
        e.preventDefault();
        handleNavigate(NAV_ORDER[num - 1]);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [handleNavigate]);

  return (
    <div className={s.app}>
      <ToastContainer />
      <CommandPalette />

      {/* ── 사이드바 ── */}
      <aside className={s.sidebar}>
        <div className={s.sidebarHeader}>
          <div className={s.sidebarTitle}>{t("app.unit")}</div>
          <div className={s.sidebarSubtitle}>{t("app.shift")}</div>
        </div>

        <nav className={s.nav}>
          {NAV.filter(n => n.id !== "settings").map(n => (
            <button key={n.id} onClick={() => handleNavigate(n.id)}
              className={`${s.navBtn} ${currentId === n.id ? s.navBtnActive : ""}`}
              aria-label={t(`nav.${n.id}`)}
              aria-current={currentId === n.id ? "page" : undefined}>
              <span className={s.navIcon}>{n.icon}</span>
              {t(`nav.${n.id}`)}
            </button>
          ))}
        </nav>

        <div className={s.sidebarFooter}>
          <button onClick={() => handleNavigate("settings")}
            className={`${s.settingsBtn} ${currentId === "settings" ? s.settingsBtnActive : ""}`}
            aria-label={t("nav.settings")}>
            {"\u2699"} {t("nav.settings")}
          </button>
        </div>

        <div className={s.sysInfo}>
          <div className={s.sysInfoLabel}>{t("app.syslog")}</div>
          v2.4.1 {"\u00b7"} seed:42 {"\u00b7"} torch:2.10
        </div>
      </aside>

      {/* ── 메인 영역 ── */}
      <div className={s.main}>
        <header className={s.header}>
          <div className={s.headerLeft}>
            <span className={s.headerTitle}>{t("app.title")}</span>
            {["header.system_status", "header.notifications", "header.shift_info"].map(k => (
              <span key={k} className={s.headerTab}>{t(k)}</span>
            ))}
          </div>
          <div className={s.headerRight}>
            <button className={s.searchBadge} onClick={openSearch} aria-label="Open search">
              {"\u2315"} <span className={s.searchKey}>{"\u2318"}K</span>
            </button>
            <span className={s.clock}>{time.toLocaleTimeString(locale === "ko" ? "ko-KR" : "en-GB")}</span>
            <span className={s.statusBadge}>{t("app.status")}</span>
          </div>
        </header>

        <main className={s.content}>
          <div className={s.pageHeader}>
            <div>
              <h1 className={s.pageTitle}>{curNav?.code || currentId}</h1>
              <div className={s.pageSubtitle}>{t("app.subtitle")}</div>
            </div>
          </div>
          <ErrorBoundary>
          <Suspense fallback={<div className={s.loading}><div className={s.loadingText}>{t("app.loading")}</div></div>}>
            <Routes>
              <Route path="/" element={<PageDashboard onNavigate={handleNavigate} onReport={handleReport} />} />
              <Route path="/casting" element={<PageCasting onReport={handleReport} />} />
              <Route path="/segmentation" element={<PageSegTile onReport={handleReport} />} />
              <Route path="/pcb" element={<PagePCB onReport={handleReport} />} />
              <Route path="/maintenance" element={<PageNLP onReport={handleReport} />} />
              <Route path="/history" element={<PageHistory />} />
              <Route path="/settings" element={<PageSettings />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
          </ErrorBoundary>
        </main>
      </div>
      <PrintLayout modules={reportModules} />
    </div>
  );
}
