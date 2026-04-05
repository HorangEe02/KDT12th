import s from "./Settings.module.css";
import useTranslation from "../hooks/useTranslation";
import Label from "../components/Label";
import Panel from "../components/Panel";
import { useSettings } from "../context/SettingsContext";

const PageSettings = () => {
  const { t } = useTranslation();
  const { settings, update, reset } = useSettings();

  return (
    <div className={s.container}>
      <Panel>
        <div className={s.sectionTitle}>{t("settings.display")}</div>
        <div className={s.settingRow}>
          <div className={s.settingInfo}>
            <div className={s.settingLabel}>{t("settings.dark_mode")}</div>
            <div className={s.settingDesc}>{t("settings.dark_mode_desc")}</div>
          </div>
          <button className={`${s.toggle} ${settings.darkMode ? s.toggleOn : ""}`}
            onClick={() => update("darkMode", !settings.darkMode)} aria-label={t("settings.dark_mode")} />
        </div>
        <div className={s.settingRow}>
          <div className={s.settingInfo}>
            <div className={s.settingLabel}>{t("settings.chart_anim")}</div>
            <div className={s.settingDesc}>{t("settings.chart_anim_desc")}</div>
          </div>
          <button className={`${s.toggle} ${settings.chartAnimation ? s.toggleOn : ""}`}
            onClick={() => update("chartAnimation", !settings.chartAnimation)} aria-label={t("settings.chart_anim")} />
        </div>
        <div className={s.settingRow}>
          <div className={s.settingInfo}>
            <div className={s.settingLabel}>{t("settings.language")}</div>
            <div className={s.settingDesc}>{t("settings.language_desc")}</div>
          </div>
          <select className={s.select} value={settings.language} onChange={e => update("language", e.target.value)}>
            <option value="en">English</option>
            <option value="ko">{"\ud55c\uad6d\uc5b4"}</option>
          </select>
        </div>
      </Panel>

      <Panel>
        <div className={s.sectionTitle}>{t("settings.alert_config")}</div>
        <div className={s.settingRow}>
          <div className={s.settingInfo}>
            <div className={s.settingLabel}>{t("settings.live_alert")}</div>
            <div className={s.settingDesc}>{t("settings.live_alert_desc")}</div>
          </div>
          <button className={`${s.toggle} ${settings.liveAlerts ? s.toggleOn : ""}`}
            onClick={() => update("liveAlerts", !settings.liveAlerts)} aria-label={t("settings.live_alert")} />
        </div>
        <div className={s.settingRow}>
          <div className={s.settingInfo}>
            <div className={s.settingLabel}>{t("settings.threshold")}</div>
            <div className={s.settingDesc}>{t("settings.threshold_desc")}</div>
          </div>
          <div className={s.sliderWrap}>
            <input type="range" min={50} max={99} value={settings.alertThreshold}
              onChange={e => update("alertThreshold", Number(e.target.value))} className={s.slider} />
            <span className={s.sliderValue}>{settings.alertThreshold}%</span>
          </div>
        </div>
      </Panel>

      <Panel>
        <div className={s.sectionTitle}>{t("settings.data_config")}</div>
        <div className={s.settingRow}>
          <div className={s.settingInfo}>
            <div className={s.settingLabel}>{t("settings.auto_refresh")}</div>
            <div className={s.settingDesc}>{t("settings.auto_refresh_desc")}</div>
          </div>
          <button className={`${s.toggle} ${settings.autoRefresh ? s.toggleOn : ""}`}
            onClick={() => update("autoRefresh", !settings.autoRefresh)} aria-label={t("settings.auto_refresh")} />
        </div>
        <div className={s.settingRow}>
          <div className={s.settingInfo}>
            <div className={s.settingLabel}>{t("settings.interval")}</div>
            <div className={s.settingDesc}>{t("settings.interval_desc")}</div>
          </div>
          <div className={s.sliderWrap}>
            <input type="range" min={1} max={30} value={settings.refreshInterval}
              onChange={e => update("refreshInterval", Number(e.target.value))} className={s.slider} />
            <span className={s.sliderValue}>{settings.refreshInterval}s</span>
          </div>
        </div>
      </Panel>

      <Panel>
        <div className={s.sectionTitle}>{t("settings.system_info")}</div>
        <div className={s.sysGrid}>
          {[["settings.sys.version","v2.4.1"],["settings.sys.react","v19.2.4"],["settings.sys.build","Vite 8.0"],["settings.sys.models","4 / 4"],["settings.sys.seed","42"],["settings.sys.pytorch","2.10"],["settings.sys.cuda","12.1"],["settings.sys.uptime","48h 23m"]].map(([k,v]) => (
            <div key={k} className={s.sysItem}>
              <span className={s.sysKey}>{t(k)}</span>
              <span className={s.sysVal}>{v}</span>
            </div>
          ))}
        </div>
        <button className={s.resetBtn} onClick={reset}>{"\u21bb"} {t("settings.reset")}</button>
      </Panel>
    </div>
  );
};

export default PageSettings;
