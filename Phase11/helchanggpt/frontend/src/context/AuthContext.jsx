import { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const saved = sessionStorage.getItem('helchang_user')
    if (saved) {
      try { setUser(JSON.parse(saved)) } catch {}
    }
    setLoading(false)
  }, [])

  const login = async (nickname, password) => {
    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nickname, password }),
      })
      if (res.ok) {
        const data = await res.json()
        setUser(data.user)
        sessionStorage.setItem('helchang_user', JSON.stringify(data.user))
        return { success: true }
      }
      const err = await res.json()
      return { success: false, error: err.detail || '로그인 실패' }
    } catch {
      // 서버 미연결 시 로컬 데모 로그인
      const uid = nickname.toLowerCase().replace(/\s/g, '_')
      const demoUser = {
        nickname, user_id: uid, joined_at: new Date().toISOString(),
        role: uid === 'admin' || uid === '관리자' ? 'admin' : 'user',
        is_active: true,
      }
      setUser(demoUser)
      sessionStorage.setItem('helchang_user', JSON.stringify(demoUser))
      return { success: true, demo: true }
    }
  }

  const signup = async (nickname, password) => {
    try {
      const res = await fetch('/api/v1/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nickname, password }),
      })
      if (res.ok) {
        const data = await res.json()
        setUser(data.user)
        sessionStorage.setItem('helchang_user', JSON.stringify(data.user))
        return { success: true }
      }
      const err = await res.json()
      return { success: false, error: err.detail || '회원가입 실패' }
    } catch {
      const uid = nickname.toLowerCase().replace(/\s/g, '_')
      const demoUser = {
        nickname, user_id: uid, joined_at: new Date().toISOString(),
        role: 'user', is_active: true,
      }
      setUser(demoUser)
      sessionStorage.setItem('helchang_user', JSON.stringify(demoUser))
      return { success: true, demo: true }
    }
  }

  const logout = () => {
    setUser(null)
    sessionStorage.removeItem('helchang_user')
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
