import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { translations } from '../i18n/translations'

const SettingsContext = createContext(null)

const DEFAULTS = {
  theme: 'dark',       // 'dark' | 'light'
  language: 'ko',      // 'ko' | 'en' | 'ja'
  defaultModel: 'exaone3.5:7.8b',
}

export function SettingsProvider({ children }) {
  const [settings, setSettings] = useState(() => {
    const saved = localStorage.getItem('helchang_settings')
    return saved ? { ...DEFAULTS, ...JSON.parse(saved) } : DEFAULTS
  })

  useEffect(() => {
    localStorage.setItem('helchang_settings', JSON.stringify(settings))
    // 테마 적용
    if (settings.theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [settings])

  const updateSetting = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }

  const toggleTheme = () => {
    updateSetting('theme', settings.theme === 'dark' ? 'light' : 'dark')
  }

  // 번역 함수: 현재 언어 → 한국어 폴백 → 키 원문
  const t = useCallback((key) => {
    return translations[settings.language]?.[key]
      || translations['ko'][key]
      || key
  }, [settings.language])

  return (
    <SettingsContext.Provider value={{ settings, updateSetting, toggleTheme, t }}>
      {children}
    </SettingsContext.Provider>
  )
}

export function useSettings() {
  const ctx = useContext(SettingsContext)
  if (!ctx) throw new Error('useSettings must be used within SettingsProvider')
  return ctx
}
