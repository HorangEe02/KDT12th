import React, { useState, useEffect } from 'react'
import { AuthProvider, useAuth } from './context/AuthContext'
import { SettingsProvider, useSettings } from './context/SettingsContext'
import ModelSelector from './components/ModelSelector'
import LoginPage from './pages/LoginPage'
import OnboardingPage from './pages/OnboardingPage'
import DietPage from './pages/DietPage'
import WorkoutPage from './pages/WorkoutPage'
import DiaryPage from './pages/DiaryPage'
import SettingsPage from './pages/SettingsPage'
import AdminPage from './pages/AdminPage'
import MemberManagePage from './pages/MemberManagePage'

// ── 에러 경계: 렌더링 크래시 시 검은 화면 방지 ──
class ErrorBoundary extends React.Component {
  constructor(props) { super(props); this.state = { hasError: false, error: null } }
  static getDerivedStateFromError(error) { return { hasError: true, error } }
  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-surface flex items-center justify-center p-4">
          <div className="card-elevated p-8 max-w-md text-center space-y-4">
            <span className="text-4xl">⚠️</span>
            <h2 className="font-headline font-bold text-lg text-on-surface">오류가 발생했어요</h2>
            <p className="text-on-surface-variant text-sm">{this.state.error?.message || '알 수 없는 오류'}</p>
            <button onClick={() => { this.setState({ hasError: false, error: null }); sessionStorage.removeItem('helchang_user'); window.location.reload() }}
              className="btn-neon text-xs mx-auto">로그인 화면으로 돌아가기</button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

function AppContent() {
  const { user, loading, logout } = useAuth()
  const { settings, t } = useSettings()
  const [activePage, setActivePage] = useState('onboarding')
  const [profile, setProfile] = useState(null)
  const [selectedModel, setSelectedModel] = useState(settings.defaultModel || 'exaone3.5:7.8b')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  // 로그인 후 서버에서 프로필 자동 로드
  useEffect(() => {
    if (!user) return
    const userId = user.user_id || user.nickname
    if (!userId || userId === 'default') return
    ;(async () => {
      try {
        const res = await fetch(`/api/v1/profile/${userId}`)
        if (res.ok) {
          const data = await res.json()
          if (data.has_data && data.profile) {
            // 서버 프로필을 프론트 profile 구조에 맞게 변환
            const p = data.profile
            setProfile({
              basic: { age: p.age, gender: p.gender, height_cm: p.height_cm, weight_kg: p.weight_kg },
              calculated: data.calculated || {},
              nlp_analysis: {
                goal_type: p.goal_type,
                constraints: p.constraints || [],
                experience_level: p.experience_level,
                exercise_frequency: p.exercise_frequency,
              },
              health_risk_flags: { warnings: [] },
              profile_confidence: { score: 80, level: '높음' },
              meta: { input_type: 'server_loaded' },
            })
          }
        }
      } catch {}
    })()
  }, [user])

  // 로딩 중 표시 (sessionStorage 읽는 동안)
  if (loading) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center">
        <div className="text-center space-y-3">
          <span className="text-4xl animate-pulse">💪</span>
          <p className="text-neon font-headline font-bold text-sm animate-pulse">로딩 중...</p>
        </div>
      </div>
    )
  }

  if (!user) return <LoginPage />

  const navItems = [
    { id: 'onboarding', label: t('nav.body'), icon: 'sprint', short: t('nav.body.short') },
    { id: 'diet', label: t('nav.diet'), icon: 'restaurant', short: t('nav.diet.short') },
    { id: 'workout', label: t('nav.workout'), icon: 'fitness_center', short: t('nav.workout.short') },
    { id: 'diary', label: t('nav.diary'), icon: 'edit_note', short: t('nav.diary.short') },
    { id: 'settings', label: t('nav.settings'), icon: 'settings', short: t('nav.settings') },
  ]

  return (
    <div className={`${settings.theme === 'dark' ? 'dark' : ''} flex min-h-screen`}>
      <div className="flex min-h-screen w-full bg-surface text-on-surface">

        {/* ══ 데스크톱 사이드바 (md 이상에서만 표시) ══ */}
        <aside className="hidden md:flex fixed left-0 top-0 h-screen w-60 bg-surface flex-col z-40 border-r border-outline-variant/10">
          <div className="p-6 pb-2">
            <h1 className="text-neon font-headline font-black text-xl tracking-tighter italic">{t('common.app_name')}</h1>
            <p className="text-on-surface-variant text-[9px] font-headline font-bold tracking-[0.2em] uppercase mt-0.5">{t('common.app_subtitle')}</p>
          </div>
          <nav className="flex-1 mt-6 space-y-1">
            {navItems.map((item) => (
              <button key={item.id} onClick={() => setActivePage(item.id)}
                className={`nav-item w-full text-left ${activePage === item.id ? 'nav-item-active' : ''}`}>
                <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
                <span className="text-xs">{item.label}</span>
              </button>
            ))}
            {/* 모델 비교 */}
            <button onClick={() => setActivePage('comparison')}
              className={`nav-item w-full text-left ${activePage === 'comparison' ? 'nav-item-active' : ''}`}>
              <span className="material-symbols-outlined text-[20px]">compare_arrows</span>
              <span className="text-xs">{t('nav.comparison')}</span>
            </button>
            {/* 어드민 전용 */}
            {user?.role === 'admin' && (
              <>
                <button onClick={() => setActivePage('members')}
                  className={`nav-item w-full text-left mt-1 ${activePage === 'members' ? 'nav-item-active' : ''}`}>
                  <span className="material-symbols-outlined text-[20px]">group</span>
                  <span className="text-xs">{t('nav.members')}</span>
                </button>
                <button onClick={() => setActivePage('admin')}
                  className={`nav-item w-full text-left ${activePage === 'admin' ? 'nav-item-active' : ''}`}>
                  <span className="material-symbols-outlined text-[20px]">admin_panel_settings</span>
                  <span className="text-xs">{t('nav.admin')}</span>
                </button>
              </>
            )}
          </nav>
          <div className="p-4 border-t border-outline-variant/10">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-neon/20 flex items-center justify-center">
                <span className="text-neon text-xs font-headline font-bold">{user.nickname?.charAt(0)?.toUpperCase() || 'U'}</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-headline font-bold text-on-surface truncate">{user.nickname}</p>
                <button onClick={logout} className="text-[10px] text-on-surface-variant hover:text-error transition-colors">{t('common.logout')}</button>
              </div>
            </div>
          </div>
        </aside>

        {/* ══ 메인 콘텐츠 ══ */}
        <main className="md:ml-60 flex-1 min-h-screen pb-20 md:pb-0">
          {/* 상단 바 */}
          <header className="sticky top-0 z-30 glass px-4 md:px-8 py-3 md:py-4 flex items-center justify-between">
            {/* 모바일: 로고 + 햄버거 */}
            <div className="flex items-center gap-3">
              <button className="md:hidden text-on-surface-variant" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
                <span className="material-symbols-outlined">{mobileMenuOpen ? 'close' : 'menu'}</span>
              </button>
              <h1 className="md:hidden text-neon font-headline font-black text-lg tracking-tighter italic">{t('common.app_name')}</h1>
              {/* 데스크톱: 검색 */}
              <div className="hidden md:flex items-center gap-3">
                <span className="material-symbols-outlined text-on-surface-variant text-xl">search</span>
                <input type="text" placeholder={t('common.search_placeholder')} className="bg-transparent text-sm text-on-surface placeholder-on-surface-variant/40 focus:outline-none w-64 font-body" />
              </div>
            </div>
            <div className="flex items-center gap-2 md:gap-4">
              <div className="hidden md:block"><ModelSelector selectedModel={selectedModel} onModelChange={setSelectedModel} compact /></div>
              <button onClick={() => setActivePage('settings')} className="material-symbols-outlined text-on-surface-variant hover:text-neon cursor-pointer transition-colors text-xl">settings</button>
              <span className="hidden md:inline text-neon font-headline font-bold text-xs tracking-tight">{t('common.app_short')}</span>
            </div>
          </header>

          {/* 모바일 메뉴 드롭다운 */}
          {mobileMenuOpen && (
            <div className="md:hidden fixed inset-0 top-14 z-40 bg-surface/95 backdrop-blur-sm p-4 space-y-2">
              {navItems.map(item => (
                <button key={item.id} onClick={() => { setActivePage(item.id); setMobileMenuOpen(false) }}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-headline font-bold transition-all ${
                    activePage === item.id ? 'bg-neon/15 text-neon' : 'text-on-surface-variant'}`}>
                  <span className="material-symbols-outlined">{item.icon}</span>{item.label}
                </button>
              ))}
              {user?.role === 'admin' && (
                <>
                  <div className="border-t border-outline-variant/10 pt-2 mt-2">
                    <button onClick={() => { setActivePage('members'); setMobileMenuOpen(false) }}
                      className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-headline font-bold text-on-surface-variant">
                      <span className="material-symbols-outlined">group</span>{t('nav.members')}
                    </button>
                    <button onClick={() => { setActivePage('admin'); setMobileMenuOpen(false) }}
                      className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-headline font-bold text-on-surface-variant">
                      <span className="material-symbols-outlined">admin_panel_settings</span>{t('nav.admin')}
                    </button>
                  </div>
                </>
              )}
              {/* 모델 선택 */}
              <div className="border-t border-outline-variant/10 pt-3 mt-2">
                <ModelSelector selectedModel={selectedModel} onModelChange={setSelectedModel} />
              </div>
              <button onClick={logout} className="w-full text-center text-xs text-on-surface-variant hover:text-error py-2">{t('common.logout')}</button>
            </div>
          )}

          {/* 페이지 */}
          <div className="p-4 md:p-8">
            {activePage === 'onboarding' && <OnboardingPage profile={profile} setProfile={setProfile} selectedModel={selectedModel} userId={user.user_id || user.nickname} />}
            {activePage === 'diet' && <DietPage profile={profile} selectedModel={selectedModel} userId={user.user_id || user.nickname} />}
            {activePage === 'workout' && <WorkoutPage profile={profile} selectedModel={selectedModel} userId={user.user_id || user.nickname} />}
            {activePage === 'diary' && <DiaryPage profile={profile} selectedModel={selectedModel} userId={user.user_id || user.nickname} />}
            {activePage === 'comparison' && <ComingSoon />}
            {activePage === 'settings' && <SettingsPage />}
            {activePage === 'members' && <MemberManagePage />}
            {activePage === 'admin' && <AdminPage />}
          </div>
        </main>

        {/* ══ 모바일 하단 네비게이션 바 (md 미만에서만 표시) ══ */}
        <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 glass border-t border-outline-variant/10">
          <div className="flex items-center justify-around py-2">
            {navItems.slice(0, 4).map(item => (
              <button key={item.id} onClick={() => setActivePage(item.id)}
                className={`flex flex-col items-center gap-0.5 py-1 px-3 rounded-xl transition-all ${
                  activePage === item.id ? 'text-neon' : 'text-on-surface-variant'}`}>
                <span className="material-symbols-outlined text-[22px]">{item.icon}</span>
                <span className="text-[9px] font-headline font-bold">{item.short}</span>
              </button>
            ))}
            {/* 더보기 (프로필 아이콘) */}
            <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className={`flex flex-col items-center gap-0.5 py-1 px-3 rounded-xl transition-all ${
                mobileMenuOpen || ['settings','comparison','members','admin'].includes(activePage) ? 'text-neon' : 'text-on-surface-variant'}`}>
              <span className="material-symbols-outlined text-[22px]">more_horiz</span>
              <span className="text-[9px] font-headline font-bold">{t('nav.more')}</span>
            </button>
          </div>
        </nav>
      </div>

      <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
    </div>
  )
}

export default function App() {
  return (
    <ErrorBoundary>
      <SettingsProvider>
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </SettingsProvider>
    </ErrorBoundary>
  )
}

function ComingSoon() {
  const { t } = useSettings()
  return (
    <div className="card-surface text-center py-16 md:py-24">
      <div className="text-4xl md:text-5xl mb-4 md:mb-6">🔬</div>
      <h2 className="section-title text-on-surface text-lg md:text-2xl">{t('page.comparison.title')}</h2>
      <p className="section-subtitle mt-2 text-xs md:text-sm">{t('page.comparison.desc')}</p>
    </div>
  )
}
