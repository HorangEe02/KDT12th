import en from "./en.json";
import ko from "./ko.json";

const locales = { en, ko };

/**
 * 번역 함수 — 키를 현재 로케일 문자열로 변환
 * @param {string} locale - "en" | "ko"
 * @param {string} key - 점 표기법 키 (e.g., "nav.dashboard")
 * @param {object} vars - 보간 변수 (e.g., { n: "2847" })
 * @returns {string}
 */
export function translate(locale, key, vars) {
  const dict = locales[locale] || locales.en;
  let str = dict[key] ?? locales.en[key] ?? key;

  // 변수 보간: {varName} → 값
  if (vars) {
    Object.entries(vars).forEach(([k, v]) => {
      str = str.replace(new RegExp(`\\{${k}\\}`, "g"), String(v));
    });
  }

  return str;
}
