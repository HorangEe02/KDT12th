import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'

export default function AdminPage() {
  const { user } = useAuth()
  const [users, setUsers] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [actionMsg, setActionMsg] = useState('')
  const [selectedUser, setSelectedUser] = useState(null)

  useEffect(() => { fetchData() }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [usersRes, statsRes] = await Promise.all([
        fetch(`/api/v1/admin/users?admin_id=${user.user_id}`),
        fetch(`/api/v1/admin/stats?admin_id=${user.user_id}`),
      ])
      if (usersRes.ok) setUsers((await usersRes.json()).users || [])
      if (statsRes.ok) setStats(await statsRes.json())
    } catch {
      // 서버 미연결 시 데모 데이터
      setUsers([
        { user_id: 'admin', nickname: '관리자', role: 'admin', is_active: true, joined_at: '2026-04-10', last_active_at: '2026-04-10', measurement_count: 0 },
        { user_id: 'demo_user', nickname: '데모사용자', role: 'user', is_active: true, joined_at: '2026-04-10', last_active_at: '2026-04-10', measurement_count: 2 },
      ])
      setStats({ users: { total: 2, admins: 1, active_today: 1 }, data: { nutrition_items: 1146, exercises: 24, inbody_measurements: 2 } })
    }
    setLoading(false)
  }

  const handleAction = async (action, targetId) => {
    setActionMsg('')
    try {
      let res
      if (action === 'toggle-active') {
        res = await fetch(`/api/v1/admin/users/${targetId}/toggle-active?admin_id=${user.user_id}`, { method: 'PUT' })
      } else if (action === 'reset-password') {
        res = await fetch(`/api/v1/admin/users/${targetId}/reset-password?admin_id=${user.user_id}`, { method: 'PUT' })
      } else if (action === 'make-admin') {
        res = await fetch(`/api/v1/admin/users/${targetId}/role?admin_id=${user.user_id}`, {
          method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ role: 'admin' }),
        })
      } else if (action === 'make-user') {
        res = await fetch(`/api/v1/admin/users/${targetId}/role?admin_id=${user.user_id}`, {
          method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ role: 'user' }),
        })
      } else if (action === 'delete') {
        if (!confirm(`정말 '${targetId}' 계정을 삭제할까요? 이 작업은 되돌릴 수 없습니다.`)) return
        res = await fetch(`/api/v1/admin/users/${targetId}?admin_id=${user.user_id}`, { method: 'DELETE' })
      }
      if (res?.ok) {
        const data = await res.json()
        setActionMsg(data.message || '완료')
        fetchData()
      } else {
        const err = await res?.json()
        setActionMsg(err?.detail || '오류 발생')
      }
    } catch {
      setActionMsg('서버에 연결할 수 없어요')
    }
  }

  if (user?.role !== 'admin') {
    return (
      <div className="card-surface text-center py-24">
        <span className="text-3xl md:text-5xl">🔒</span>
        <h2 className="section-title mt-4">접근 권한이 없습니다</h2>
        <p className="section-subtitle mt-2">관리자 계정으로 로그인해주세요</p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* 헤더 */}
      <div>
        <span className="badge-neon">관리자 전용</span>
        <h2 className="font-headline font-black text-4xl tracking-tighter mt-3">
          🔐 <span className="text-neon">관리자</span> 대시보드
        </h2>
        <p className="section-subtitle">사용자 계정과 시스템 현황을 관리합니다</p>
      </div>

      {/* 시스템 현황 카드 */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
          <StatCard icon="group" label="전체 회원" value={stats.users.total} unit="명" />
          <StatCard icon="shield_person" label="관리자" value={stats.users.admins} unit="명" color="text-tertiary" />
          <StatCard icon="local_fire_department" label="오늘 활성" value={stats.users.active_today} unit="명" color="text-neon" />
          <StatCard icon="monitoring" label="인바디 측정" value={stats.data.inbody_measurements} unit="건" />
        </div>
      )}

      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 md:gap-4">
          <div className="card-surface text-center">
            <p className="metric-label">식품 영양성분 DB</p>
            <p className="font-headline font-bold text-2xl mt-1">{stats.data.nutrition_items.toLocaleString()}<span className="text-sm text-on-surface-variant ml-1">건</span></p>
          </div>
          <div className="card-surface text-center">
            <p className="metric-label">운동 DB</p>
            <p className="font-headline font-bold text-2xl mt-1">{stats.data.exercises}<span className="text-sm text-on-surface-variant ml-1">개</span></p>
          </div>
          <div className="card-surface text-center">
            <p className="metric-label">총 인바디 분석</p>
            <p className="font-headline font-bold text-2xl mt-1">{stats.data.inbody_measurements}<span className="text-sm text-on-surface-variant ml-1">건</span></p>
          </div>
        </div>
      )}

      {/* 알림 메시지 */}
      {actionMsg && (
        <div className="bg-neon/10 text-neon text-sm rounded-xl p-3 text-center font-headline font-bold">
          {actionMsg}
        </div>
      )}

      {/* 사용자 목록 */}
      <div className="card-elevated">
        <div className="flex items-center justify-between mb-4">
          <p className="font-headline font-bold text-lg">👤 사용자 관리</p>
          <p className="text-on-surface-variant text-xs">{users.length}명</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-outline-variant/10">
                <th className="text-left py-3 px-3 metric-label">닉네임</th>
                <th className="text-left py-3 px-3 metric-label">역할</th>
                <th className="text-left py-3 px-3 metric-label">가입일</th>
                <th className="text-left py-3 px-3 metric-label">최근 활동</th>
                <th className="text-left py-3 px-3 metric-label">측정</th>
                <th className="text-left py-3 px-3 metric-label">상태</th>
                <th className="text-right py-3 px-3 metric-label">관리</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.user_id} className={`border-b border-outline-variant/5 hover:bg-surface-container transition-colors ${!u.is_active ? 'opacity-50' : ''}`}>
                  <td className="py-3 px-3">
                    <div className="flex items-center gap-2">
                      <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${u.role === 'admin' ? 'bg-neon/20 text-neon' : 'bg-surface-container-high text-on-surface-variant'}`}>
                        {u.nickname?.charAt(0)?.toUpperCase()}
                      </div>
                      <span className="font-headline font-bold">{u.nickname}</span>
                    </div>
                  </td>
                  <td className="py-3 px-3">
                    <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${u.role === 'admin' ? 'bg-neon/15 text-neon' : 'bg-surface-container-high text-on-surface-variant'}`}>
                      {u.role === 'admin' ? '관리자' : '일반'}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-on-surface-variant text-xs">{u.joined_at?.split('T')[0]}</td>
                  <td className="py-3 px-3 text-on-surface-variant text-xs">{u.last_active_at?.split('T')[0] || '—'}</td>
                  <td className="py-3 px-3 text-on-surface-variant text-xs">{u.measurement_count || 0}회</td>
                  <td className="py-3 px-3">
                    <span className={`text-[10px] font-bold ${u.is_active ? 'text-neon' : 'text-error'}`}>
                      {u.is_active ? '● 활성' : '○ 비활성'}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-right">
                    {u.user_id !== 'admin' && (
                      <div className="flex items-center justify-end gap-1">
                        <ActionBtn icon="swap_horiz" title={u.role === 'admin' ? '일반으로 변경' : '관리자로 승격'}
                          onClick={() => handleAction(u.role === 'admin' ? 'make-user' : 'make-admin', u.user_id)} />
                        <ActionBtn icon={u.is_active ? 'block' : 'check_circle'} title={u.is_active ? '비활성화' : '활성화'}
                          onClick={() => handleAction('toggle-active', u.user_id)} />
                        <ActionBtn icon="lock_reset" title="비밀번호 초기화"
                          onClick={() => handleAction('reset-password', u.user_id)} />
                        <ActionBtn icon="delete" title="계정 삭제" danger
                          onClick={() => handleAction('delete', u.user_id)} />
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 초기 비밀번호 안내 */}
      <div className="card-surface bg-surface-container-low">
        <p className="metric-label mb-2">💡 관리자 참고사항</p>
        <ul className="text-xs text-on-surface-variant space-y-1">
          <li>• 초기 관리자 비밀번호: <code className="text-neon bg-neon/10 px-1 rounded">helchang2026!</code> (첫 로그인 후 변경 권장)</li>
          <li>• 비밀번호 초기화 시 임시 비밀번호: <code className="text-neon bg-neon/10 px-1 rounded">reset1234</code></li>
          <li>• 관리자 계정(admin)은 비활성화/삭제할 수 없습니다</li>
          <li>• 계정 삭제는 되돌릴 수 없으니 신중히 진행하세요</li>
        </ul>
      </div>
    </div>
  )
}

function StatCard({ icon, label, value, unit, color = 'text-on-surface' }) {
  return (
    <div className="card-elevated text-center">
      <span className={`material-symbols-outlined text-2xl ${color}`}>{icon}</span>
      <p className={`font-headline font-black text-3xl mt-1 ${color}`}>{value}<span className="text-sm text-on-surface-variant ml-1">{unit}</span></p>
      <p className="metric-label mt-1">{label}</p>
    </div>
  )
}

function ActionBtn({ icon, title, onClick, danger = false }) {
  return (
    <button
      onClick={onClick}
      title={title}
      className={`w-7 h-7 rounded-lg flex items-center justify-center transition-all ${
        danger
          ? 'hover:bg-error/20 text-on-surface-variant hover:text-error'
          : 'hover:bg-surface-container-high text-on-surface-variant hover:text-neon'
      }`}
    >
      <span className="material-symbols-outlined text-[16px]">{icon}</span>
    </button>
  )
}
