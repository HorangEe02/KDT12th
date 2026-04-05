import { useCallback } from "react";
import { useSettings } from "../context/SettingsContext";
import { translate } from "../i18n/index";

/**
 * 번역 훅 — 현재 로케일 기반 t() 함수 반환
 * @returns {{ t: (key: string, vars?: object) => string, locale: string }}
 */
export default function useTranslation() {
  const { settings } = useSettings();
  const locale = settings.language;

  const t = useCallback(
    (key, vars) => translate(locale, key, vars),
    [locale]
  );

  return { t, locale };
}
