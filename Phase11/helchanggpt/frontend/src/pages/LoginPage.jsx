import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useSettings } from '../context/SettingsContext'

export default function LoginPage() {
  const { login, signup } = useAuth()
  const { t } = useSettings()
  const [isSignup, setIsSignup] = useState(false)
  const [nickname, setNickname] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!nickname.trim() || !password.trim()) return
    setLoading(true)
    setError('')

    const result = isSignup
      ? await signup(nickname.trim(), password)
      : await login(nickname.trim(), password)

    if (!result.success) {
      setError(result.error || '오류가 발생했습니다')
    }
    setLoading(false)
  }

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-8">
        {/* 로고 */}
        <div className="text-center">
          <h1 className="text-neon font-headline font-black text-4xl tracking-tighter italic">
            {t('login.title')}
          </h1>
          <p className="text-on-surface-variant text-sm font-headline mt-2">
            {t('login.subtitle')}
          </p>
          <div className="w-16 h-0.5 bg-neon/30 mx-auto mt-4" />
        </div>

        {/* 로그인/회원가입 폼 */}
        <div className="card-elevated p-8">
          <h2 className="font-headline font-bold text-xl text-center mb-6">
            {isSignup ? t('login.tab_signup') : t('login.tab_login')}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="metric-label block mb-2">{t('login.nickname')}</label>
              <input
                type="text"
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                placeholder={t('login.nickname_placeholder')}
                className="input-dark"
                disabled={loading}
                autoFocus
              />
            </div>

            <div>
              <label className="metric-label block mb-2">{t('login.password')}</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={t('login.password_placeholder')}
                className="input-dark"
                disabled={loading}
              />
            </div>

            {error && (
              <p className="text-error text-xs bg-error/10 rounded-lg p-2 text-center">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading || !nickname.trim() || !password.trim()}
              className="btn-neon w-full flex items-center justify-center gap-2"
            >
              {loading ? t('login.processing') : isSignup ? t('login.submit_signup') : t('login.submit_login')}
            </button>
          </form>

          <div className="text-center mt-6">
            <button
              onClick={() => { setIsSignup(!isSignup); setError('') }}
              className="text-on-surface-variant text-sm hover:text-neon transition-colors"
            >
              {isSignup ? t('login.switch_to_login') : t('login.switch_to_signup')}
            </button>
          </div>
        </div>

        {/* 하단 안내 */}
        <p className="text-center text-on-surface-variant/40 text-xs">
          {t('login.footer')}
        </p>
      </div>
    </div>
  )
}
