import { useAuth } from '../context/AuthContext'
import { useSettings } from '../context/SettingsContext'
import ModelSelector from '../components/ModelSelector'

const LANGUAGES = [
  { code: 'ko', name: '한국어', flag: '🇰🇷' },
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'ja', name: '日本語', flag: '🇯🇵' },
]

export default function SettingsPage() {
  const { user, logout } = useAuth()
  const { settings, updateSetting, toggleTheme, t } = useSettings()

  return (
    <div className="space-y-8 max-w-3xl">
      <div>
        <h2 className="font-headline font-black text-4xl tracking-tighter">
          <span className="text-neon">{t('settings.title')}</span>
        </h2>
        <p className="section-subtitle">{t('settings.subtitle')}</p>
      </div>

      {/* 👤 내 정보 */}
      <div className="card-elevated">
        <p className="metric-label mb-4">👤 {t('settings.profile')}</p>
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-full bg-neon/20 flex items-center justify-center">
            <span className="text-neon text-2xl font-headline font-bold">
              {user?.nickname?.charAt(0)?.toUpperCase() || 'U'}
            </span>
          </div>
          <div>
            <p className="font-headline font-bold text-lg">{user?.nickname || t('common.guest')}</p>
            <p className="text-on-surface-variant text-xs">
              {t('settings.joined')}: {user?.joined_at ? new Date(user.joined_at).toLocaleDateString(settings.language === 'ja' ? 'ja' : settings.language === 'en' ? 'en' : 'ko') : '—'}
            </p>
          </div>
          <div className="flex-1" />
          <button onClick={logout} className="btn-ghost text-xs text-error/80 hover:text-error border-error/20 hover:border-error/40">
            {t('common.logout')}
          </button>
        </div>
      </div>

      {/* 🌐 언어 선택 */}
      <div className="card-elevated">
        <p className="metric-label mb-4">🌐 {t('settings.language')}</p>
        <p className="text-on-surface-variant text-xs mb-3">{t('settings.language_desc')}</p>
        <div className="flex gap-3">
          {LANGUAGES.map(lang => (
            <button
              key={lang.code}
              onClick={() => updateSetting('language', lang.code)}
              className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl font-headline font-bold text-sm transition-all ${
                settings.language === lang.code
                  ? 'bg-neon/15 text-neon border border-neon/30'
                  : 'bg-surface-container hover:bg-surface-container-high text-on-surface-variant border border-transparent'
              }`}
            >
              <span className="text-xl">{lang.flag}</span>
              <span>{lang.name}</span>
            </button>
          ))}
        </div>
        {settings.language !== 'ko' && (
          <p className="text-on-surface-variant/50 text-[10px] mt-2">
            {t('settings.language_note')}
          </p>
        )}
      </div>

      {/* 🎨 화면 모드 */}
      <div className="card-elevated">
        <p className="metric-label mb-4">🎨 {t('settings.theme')}</p>
        <p className="text-on-surface-variant text-xs mb-3">{t('settings.theme_desc')}</p>
        <div className="flex gap-3">
          <button
            onClick={() => updateSetting('theme', 'dark')}
            className={`flex-1 flex items-center justify-center gap-3 py-4 rounded-xl font-headline font-bold text-sm transition-all ${
              settings.theme === 'dark'
                ? 'bg-neon/15 text-neon border border-neon/30'
                : 'bg-surface-container hover:bg-surface-container-high text-on-surface-variant border border-transparent'
            }`}
          >
            <span className="text-2xl">🌙</span>
            <div className="text-left">
              <p>{t('settings.dark')}</p>
              <p className="text-[10px] text-on-surface-variant font-normal">{t('settings.dark_desc')}</p>
            </div>
          </button>
          <button
            onClick={() => updateSetting('theme', 'light')}
            className={`flex-1 flex items-center justify-center gap-3 py-4 rounded-xl font-headline font-bold text-sm transition-all ${
              settings.theme === 'light'
                ? 'bg-neon/15 text-neon border border-neon/30'
                : 'bg-surface-container hover:bg-surface-container-high text-on-surface-variant border border-transparent'
            }`}
          >
            <span className="text-2xl">☀️</span>
            <div className="text-left">
              <p>{t('settings.light')}</p>
              <p className="text-[10px] text-on-surface-variant font-normal">{t('settings.light_desc')}</p>
            </div>
          </button>
        </div>
      </div>

      {/* 🤖 기본 AI 모델 */}
      <div className="card-elevated">
        <p className="metric-label mb-4">🤖 {t('settings.model')}</p>
        <p className="text-on-surface-variant text-xs mb-3">{t('settings.model_desc')}</p>
        <ModelSelector
          selectedModel={settings.defaultModel}
          onModelChange={(m) => updateSetting('defaultModel', m)}
        />
      </div>

      {/* 📊 데이터 관리 */}
      <div className="card-elevated">
        <p className="metric-label mb-4">📊 {t('settings.data')}</p>
        <p className="text-on-surface-variant text-xs mb-3">{t('settings.data_desc')}</p>
        <div className="flex gap-3">
          <button className="btn-ghost flex-1 text-xs flex items-center justify-center gap-2">
            <span className="material-symbols-outlined text-[16px]">download</span>
            {t('settings.export')}
          </button>
          <button className="btn-ghost flex-1 text-xs text-error/60 border-error/20 hover:text-error hover:border-error/40 flex items-center justify-center gap-2">
            <span className="material-symbols-outlined text-[16px]">delete</span>
            {t('settings.delete_all')}
          </button>
        </div>
      </div>

      {/* 정보 */}
      <div className="text-center space-y-1 pb-8">
        <p className="text-on-surface-variant/30 text-xs">{t('settings.version')}</p>
        <p className="text-on-surface-variant/20 text-[10px]">{t('settings.footer')}</p>
      </div>
    </div>
  )
}
