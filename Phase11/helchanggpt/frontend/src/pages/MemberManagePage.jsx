import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'

const GOAL_OPTIONS = ['체지방감소', '근력증가', '체력향상', '체중관리', '건강개선']
const LEVEL_OPTIONS = ['입문', '초급', '중급', '고급']

export default function MemberManagePage() {
  const { user } = useAuth()
  const [members, setMembers] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('')
  const [activeFilter, setActiveFilter] = useState('')
  const [sortBy, setSortBy] = useState('joined_at')
  const [selectedMember, setSelectedMember] = useState(null)
  const [detailData, setDetailData] = useState(null)
  const [editing, setEditing] = useState(false)
  const [editForm, setEditForm] = useState({})
  const [msg, setMsg] = useState('')

  useEffect(() => { fetchMembers() }, [search, roleFilter, activeFilter, sortBy])

  const fetchMembers = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ admin_id: user.user_id, search, role_filter: roleFilter, active_filter: activeFilter, sort_by: sortBy, sort_order: 'desc' })
      const res = await fetch(`/api/v1/admin/members?${params}`)
      if (res.ok) { const d = await res.json(); setMembers(d.members || []); setLoading(false); return }
    } catch {}
    // 데모 데이터
    setMembers([
      { user_id: 'admin', nickname: '관리자', role: 'admin', is_active: true, joined_at: '2026-04-10T00:00', last_active_at: '2026-04-10T12:00', measurement_count: 0, profile: {}, admin_memo: '' },
      { user_id: 'hong', nickname: '홍길동', role: 'user', is_active: true, joined_at: '2026-04-10T09:00', last_active_at: '2026-04-10T18:00', measurement_count: 3, profile: { age: 25, gender: '남성', height_cm: 178, weight_kg: 82, goal_type: '체지방감소', constraints: ['무릎 부상'], experience_level: '초급', exercise_frequency: 3 }, admin_memo: '무릎 재활 중' },
      { user_id: 'kim', nickname: '김영희', role: 'user', is_active: true, joined_at: '2026-04-11T10:00', last_active_at: '2026-04-11T15:00', measurement_count: 1, profile: { age: 30, gender: '여성', height_cm: 163, weight_kg: 58, goal_type: '건강개선', constraints: ['당뇨'], experience_level: '입문', exercise_frequency: 2 }, admin_memo: '' },
      { user_id: 'park', nickname: '박철수', role: 'user', is_active: false, joined_at: '2026-04-12T08:00', last_active_at: '2026-04-12T08:00', measurement_count: 0, profile: {}, admin_memo: '' },
    ])
    setLoading(false)
  }

  const openDetail = async (member) => {
    setSelectedMember(member)
    setEditing(false)
    try {
      const res = await fetch(`/api/v1/admin/members/${member.user_id}/detail?admin_id=${user.user_id}`)
      if (res.ok) { setDetailData(await res.json()); return }
    } catch {}
    setDetailData({ ...member, inbody_history: [], diet_history: [], workout_history: [], diary_history: [], activity_log: [] })
  }

  const startEdit = () => {
    setEditing(true)
    setEditForm({ ...selectedMember.profile, admin_memo: selectedMember.admin_memo || '' })
  }

  const saveProfile = async () => {
    setMsg('')
    try {
      const res = await fetch(`/api/v1/admin/members/${selectedMember.user_id}/profile?admin_id=${user.user_id}`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editForm),
      })
      if (res.ok) {
        const d = await res.json()
        setMsg(d.message)
        setEditing(false)
        fetchMembers()
        openDetail({ ...selectedMember, profile: d.profile, admin_memo: editForm.admin_memo })
        return
      }
    } catch {}
    setMsg('저장에 실패했어요 (데모 모드에서는 서버 연결 필요)')
  }

  const handleAction = async (action, targetId) => {
    setMsg('')
    try {
      let res
      if (action === 'toggle-active') res = await fetch(`/api/v1/admin/users/${targetId}/toggle-active?admin_id=${user.user_id}`, { method: 'PUT' })
      else if (action === 'reset-password') res = await fetch(`/api/v1/admin/users/${targetId}/reset-password?admin_id=${user.user_id}`, { method: 'PUT' })
      else if (action === 'delete') {
        if (!confirm(`정말 이 회원을 탈퇴 처리할까요? 되돌릴 수 없습니다.`)) return
        res = await fetch(`/api/v1/admin/users/${targetId}?admin_id=${user.user_id}`, { method: 'DELETE' })
      }
      if (res?.ok) { const d = await res.json(); setMsg(d.message); setSelectedMember(null); fetchMembers() }
      else { const err = await res?.json(); setMsg(err?.detail || '오류') }
    } catch { setMsg('서버 연결 실패') }
  }

  if (user?.role !== 'admin') return <div className="card-surface text-center py-24"><span className="text-3xl md:text-5xl">🔒</span><h2 className="section-title mt-4">관리자 전용 페이지입니다</h2></div>

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div>
        <span className="badge-neon">관리자 전용</span>
        <h2 className="font-headline font-black text-4xl tracking-tighter mt-3">👥 <span className="text-neon">회원</span> 관리</h2>
        <p className="section-subtitle">가입한 회원들의 프로필을 열람하고, 정보를 수정하거나 관리할 수 있어요</p>
      </div>

      {/* 알림 */}
      {msg && <div className="bg-neon/10 text-neon text-sm rounded-xl p-3 text-center font-headline font-bold">{msg}</div>}

      <div className="flex gap-6">
        {/* 왼쪽: 회원 목록 */}
        <div className={`${selectedMember ? 'w-1/2' : 'w-full'} space-y-4 transition-all`}>
          {/* 검색/필터 */}
          <div className="flex gap-2 flex-wrap">
            <div className="flex items-center gap-2 flex-1">
              <span className="material-symbols-outlined text-on-surface-variant text-[18px]">search</span>
              <input value={search} onChange={e => setSearch(e.target.value)} placeholder="닉네임으로 검색..." className="input-dark flex-1 py-2 text-sm" />
            </div>
            <select value={roleFilter} onChange={e => setRoleFilter(e.target.value)} className="input-dark py-2 text-xs w-24">
              <option value="">전체 역할</option>
              <option value="admin">관리자</option>
              <option value="user">일반</option>
            </select>
            <select value={activeFilter} onChange={e => setActiveFilter(e.target.value)} className="input-dark py-2 text-xs w-24">
              <option value="">전체 상태</option>
              <option value="active">활성</option>
              <option value="inactive">비활성</option>
            </select>
            <select value={sortBy} onChange={e => setSortBy(e.target.value)} className="input-dark py-2 text-xs w-28">
              <option value="joined_at">가입일순</option>
              <option value="last_active_at">최근활동순</option>
              <option value="nickname">이름순</option>
              <option value="measurement_count">측정횟수순</option>
            </select>
          </div>

          {/* 회원 카드 목록 */}
          <div className="space-y-2">
            {members.map(m => (
              <button
                key={m.user_id}
                onClick={() => openDetail(m)}
                className={`w-full card-elevated flex items-center gap-4 text-left transition-all hover:shadow-neon-glow ${
                  selectedMember?.user_id === m.user_id ? 'border border-neon/30 bg-neon/5' : ''
                } ${!m.is_active ? 'opacity-50' : ''}`}
              >
                <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold ${
                  m.role === 'admin' ? 'bg-neon/20 text-neon' : 'bg-surface-container-high text-on-surface-variant'}`}>
                  {m.nickname?.charAt(0)?.toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-headline font-bold text-sm">{m.nickname}</span>
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${m.role === 'admin' ? 'bg-neon/15 text-neon' : 'bg-surface-container-high text-on-surface-variant'}`}>
                      {m.role === 'admin' ? '관리자' : '일반'}
                    </span>
                    {!m.is_active && <span className="text-[9px] text-error">비활성</span>}
                  </div>
                  <div className="flex items-center gap-3 mt-0.5">
                    {m.profile?.goal_type && <span className="text-[10px] text-neon">{m.profile.goal_type}</span>}
                    {m.profile?.age && <span className="text-[10px] text-on-surface-variant">{m.profile.age}세 {m.profile.gender}</span>}
                    <span className="text-[10px] text-on-surface-variant">인바디 {m.measurement_count}회</span>
                  </div>
                </div>
                <span className="material-symbols-outlined text-on-surface-variant/30 text-[18px]">chevron_right</span>
              </button>
            ))}
            {members.length === 0 && !loading && (
              <p className="text-center text-on-surface-variant text-sm py-8">검색 결과가 없어요</p>
            )}
          </div>
          <p className="text-on-surface-variant/40 text-xs text-center">총 {members.length}명</p>
        </div>

        {/* 오른쪽: 회원 상세 */}
        {selectedMember && (
          <div className="w-1/2 space-y-4">
            {/* 상세 헤더 */}
            <div className="card-elevated flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold ${
                  selectedMember.role === 'admin' ? 'bg-neon/20 text-neon' : 'bg-surface-container-high text-on-surface-variant'}`}>
                  {selectedMember.nickname?.charAt(0)?.toUpperCase()}
                </div>
                <div>
                  <p className="font-headline font-bold text-lg">{selectedMember.nickname}</p>
                  <p className="text-on-surface-variant text-xs">가입: {selectedMember.joined_at?.split('T')[0]} · 마지막 활동: {selectedMember.last_active_at?.split('T')[0]}</p>
                </div>
              </div>
              <button onClick={() => setSelectedMember(null)} className="material-symbols-outlined text-on-surface-variant hover:text-neon text-xl">close</button>
            </div>

            {/* 프로필 정보 (편집 모드/보기 모드) */}
            <div className="card-elevated">
              <div className="flex items-center justify-between mb-3">
                <p className="metric-label">📋 기본 정보</p>
                {!editing && selectedMember.user_id !== 'admin' && (
                  <button onClick={startEdit} className="text-neon text-xs font-headline font-bold hover:underline flex items-center gap-1">
                    <span className="material-symbols-outlined text-[14px]">edit</span> 수정
                  </button>
                )}
              </div>

              {editing ? (
                <div className="space-y-3">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <label className="metric-label mb-1 block">나이</label>
                      <input type="number" value={editForm.age || ''} onChange={e => setEditForm({ ...editForm, age: parseInt(e.target.value) || null })} className="input-dark py-2 text-sm" />
                    </div>
                    <div>
                      <label className="metric-label mb-1 block">성별</label>
                      <select value={editForm.gender || ''} onChange={e => setEditForm({ ...editForm, gender: e.target.value })} className="input-dark py-2 text-sm">
                        <option value="">선택</option><option value="남성">남성</option><option value="여성">여성</option>
                      </select>
                    </div>
                    <div>
                      <label className="metric-label mb-1 block">키 (cm)</label>
                      <input type="number" value={editForm.height_cm || ''} onChange={e => setEditForm({ ...editForm, height_cm: parseFloat(e.target.value) || null })} className="input-dark py-2 text-sm" />
                    </div>
                    <div>
                      <label className="metric-label mb-1 block">체중 (kg)</label>
                      <input type="number" value={editForm.weight_kg || ''} onChange={e => setEditForm({ ...editForm, weight_kg: parseFloat(e.target.value) || null })} className="input-dark py-2 text-sm" />
                    </div>
                    <div>
                      <label className="metric-label mb-1 block">운동 목표</label>
                      <select value={editForm.goal_type || ''} onChange={e => setEditForm({ ...editForm, goal_type: e.target.value })} className="input-dark py-2 text-sm">
                        <option value="">선택</option>
                        {GOAL_OPTIONS.map(g => <option key={g} value={g}>{g}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="metric-label mb-1 block">경험 수준</label>
                      <select value={editForm.experience_level || ''} onChange={e => setEditForm({ ...editForm, experience_level: e.target.value })} className="input-dark py-2 text-sm">
                        <option value="">선택</option>
                        {LEVEL_OPTIONS.map(l => <option key={l} value={l}>{l}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="metric-label mb-1 block">주당 운동 횟수</label>
                      <input type="number" min="0" max="7" value={editForm.exercise_frequency || ''} onChange={e => setEditForm({ ...editForm, exercise_frequency: parseInt(e.target.value) || null })} className="input-dark py-2 text-sm" />
                    </div>
                    <div>
                      <label className="metric-label mb-1 block">제약사항</label>
                      <input value={(editForm.constraints || []).join(', ')} onChange={e => setEditForm({ ...editForm, constraints: e.target.value.split(',').map(s => s.trim()).filter(Boolean) })} placeholder="쉼표로 구분" className="input-dark py-2 text-sm" />
                    </div>
                  </div>
                  <div>
                    <label className="metric-label mb-1 block">📝 관리자 메모</label>
                    <textarea value={editForm.admin_memo || ''} onChange={e => setEditForm({ ...editForm, admin_memo: e.target.value })} rows={2} className="input-dark text-sm resize-none" placeholder="이 회원에 대한 메모 (회원에게 보이지 않음)" />
                  </div>
                  <div className="flex gap-2 justify-end">
                    <button onClick={() => setEditing(false)} className="btn-ghost text-xs">취소</button>
                    <button onClick={saveProfile} className="btn-neon text-xs">저장하기</button>
                  </div>
                </div>
              ) : (
                <ProfileView profile={selectedMember.profile} memo={selectedMember.admin_memo} />
              )}
            </div>

            {/* 인바디 이력 */}
            <div className="card-elevated">
              <p className="metric-label mb-3">📊 인바디 측정 이력 ({detailData?.inbody_history?.length || selectedMember.measurement_count || 0}회)</p>
              {(detailData?.inbody_history || []).length > 0 ? (
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {detailData.inbody_history.map((m, i) => (
                    <div key={i} className="flex items-center justify-between bg-surface-container rounded-lg px-3 py-2">
                      <span className="text-xs text-on-surface-variant">{m.test_date || m.recorded_at?.split('T')[0]}</span>
                      <span className="text-xs font-headline font-bold">점수: {m.inbody_score || '—'}</span>
                      <span className="text-[10px] text-on-surface-variant">{m.parse_method}</span>
                    </div>
                  ))}
                </div>
              ) : <p className="text-on-surface-variant text-xs">아직 측정 기록이 없어요</p>}
            </div>

            {/* 최근 활동 */}
            {detailData?.activity_log?.length > 0 && (
              <div className="card-elevated">
                <p className="metric-label mb-3">🕐 최근 활동 (최신 5건)</p>
                <div className="space-y-1">
                  {detailData.activity_log.slice(-5).reverse().map((log, i) => (
                    <div key={i} className="flex items-center gap-2 text-xs text-on-surface-variant">
                      <span className="text-[10px] text-on-surface-variant/50 w-28">{log.timestamp?.split('T')[1]?.substring(0, 5)}</span>
                      <span>{log.action}</span>
                      {log.detail && <span className="text-on-surface-variant/40">— {log.detail}</span>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 계정 관리 버튼 */}
            {selectedMember.user_id !== 'admin' && (
              <div className="card-elevated">
                <p className="metric-label mb-3">⚙️ 계정 관리</p>
                <div className="flex gap-2 flex-wrap">
                  <button onClick={() => handleAction('toggle-active', selectedMember.user_id)}
                    className={`btn-ghost text-xs flex items-center gap-1 ${selectedMember.is_active ? '' : 'text-neon border-neon/30'}`}>
                    <span className="material-symbols-outlined text-[14px]">{selectedMember.is_active ? 'block' : 'check_circle'}</span>
                    {selectedMember.is_active ? '계정 비활성화' : '계정 활성화'}
                  </button>
                  <button onClick={() => handleAction('reset-password', selectedMember.user_id)} className="btn-ghost text-xs flex items-center gap-1">
                    <span className="material-symbols-outlined text-[14px]">lock_reset</span>
                    비밀번호 초기화
                  </button>
                  <button onClick={() => handleAction('delete', selectedMember.user_id)} className="btn-ghost text-xs text-error/60 border-error/20 hover:text-error hover:border-error/40 flex items-center gap-1">
                    <span className="material-symbols-outlined text-[14px]">person_remove</span>
                    회원 탈퇴 처리
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function ProfileView({ profile, memo }) {
  if (!profile || Object.keys(profile).length === 0) {
    return <p className="text-on-surface-variant text-xs">프로필 정보가 아직 없어요 (편집 버튼으로 추가할 수 있습니다)</p>
  }

  return (
    <div className="space-y-2">
      <div className="grid grid-cols-2 gap-x-6 gap-y-1">
        {profile.age && <InfoRow label="나이" value={`${profile.age}세`} />}
        {profile.gender && <InfoRow label="성별" value={profile.gender} />}
        {profile.height_cm && <InfoRow label="키" value={`${profile.height_cm}cm`} />}
        {profile.weight_kg && <InfoRow label="체중" value={`${profile.weight_kg}kg`} />}
        {profile.goal_type && <InfoRow label="목표" value={profile.goal_type} highlight />}
        {profile.experience_level && <InfoRow label="경험" value={profile.experience_level} />}
        {profile.exercise_frequency && <InfoRow label="주당 운동" value={`${profile.exercise_frequency}회`} />}
      </div>
      {profile.constraints?.length > 0 && (
        <div className="flex items-center gap-2 mt-1">
          <span className="metric-label">제약사항:</span>
          {profile.constraints.map((c, i) => (
            <span key={i} className="text-[10px] bg-error/10 text-error/80 px-2 py-0.5 rounded-full">{c}</span>
          ))}
        </div>
      )}
      {memo && (
        <div className="mt-2 bg-surface-container-low rounded-lg p-2">
          <span className="metric-label">📝 관리자 메모: </span>
          <span className="text-xs text-on-surface-variant">{memo}</span>
        </div>
      )}
    </div>
  )
}

function InfoRow({ label, value, highlight = false }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-[11px] text-on-surface-variant">{label}</span>
      <span className={`text-xs font-headline font-bold ${highlight ? 'text-neon' : 'text-on-surface'}`}>{value}</span>
    </div>
  )
}
