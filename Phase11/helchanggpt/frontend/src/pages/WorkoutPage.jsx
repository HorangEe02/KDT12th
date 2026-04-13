import { useState, useEffect, useRef } from 'react'

const DAYS_KR = ['월', '화', '수', '목', '금', '토', '일']
const DISCLAIMER = '⚠️ AI 추천 루틴은 참고용이며, 정답이 아닐 수 있습니다. 본인의 체력 수준과 건강 상태에 맞게 운동 방법·강도·횟수를 자유롭게 조정하세요. 통증이나 불편함이 있으면 즉시 중단하고 전문가와 상담하세요.'

export default function WorkoutPage({ profile, selectedModel = 'exaone3.5:7.8b', userId = 'default' }) {
  const [activeView, setActiveView] = useState('chat') // chat | plan | history
  const [plan, setPlan] = useState(null)
  const [activeDay, setActiveDay] = useState(0)
  const [savedHistory, setSavedHistory] = useState([])
  const [saving, setSaving] = useState(false)

  // 페이지 로드 시 최근 저장된 운동 루틴 불러오기
  // 주의: 'default' userId는 공유 데이터이므로 로드하지 않음
  useEffect(() => {
    if (!userId || userId === 'default') return
    ;(async () => {
      try {
        const res = await fetch(`/api/v1/workout/${userId}/history`)
        if (res.ok) {
          const data = await res.json()
          setSavedHistory(data.entries || [])
          if (data.entries?.length > 0 && !plan) {
            const latest = data.entries[data.entries.length - 1]
            setPlan({ workout_plan: latest.workout_plan })
          }
        }
      } catch {}
    })()
  }, [userId])

  const saveWorkoutPlan = async () => {
    if (!plan?.workout_plan) return
    setSaving(true)
    try {
      const res = await fetch('/api/v1/workout/save', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, workout_plan: plan.workout_plan }),
      })
      if (res.ok) {
        const data = await res.json()
        setSavedHistory(prev => [...prev, data.entry])
      }
    } catch {}
    setSaving(false)
  }

  const loadSavedPlan = (entry) => {
    setPlan({ workout_plan: entry.workout_plan })
    setActiveView('plan')
  }

  const deleteSavedPlan = async (workoutId) => {
    try {
      await fetch(`/api/v1/workout/${userId}/${workoutId}`, { method: 'DELETE' })
      setSavedHistory(prev => prev.filter(e => e.id !== workoutId))
    } catch {}
  }

  return (
    <div className="space-y-5">
      {/* ⚠️ 면책 문구 — 최상단 */}
      <div className="bg-surface-container-low rounded-xl px-5 py-3 flex items-start gap-3">
        <span className="material-symbols-outlined text-error text-xl mt-0.5">warning</span>
        <p className="text-on-surface-variant text-xs leading-relaxed">{DISCLAIMER}</p>
      </div>

      {/* 헤더 */}
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
        <div>
          <span className="badge-neon">맞춤 운동 AI</span>
          <h2 className="font-headline font-black text-4xl tracking-tighter mt-3">
            오늘 <span className="italic text-neon">뭐 하지?</span>
          </h2>
          <p className="section-subtitle">AI 트레이너와 대화하면서 나만의 일주일 운동 계획을 세워보세요</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <button onClick={() => setActiveView('chat')}
            className={`flex items-center gap-1.5 px-3 md:px-4 py-2 rounded-full text-xs font-headline font-bold transition-all whitespace-nowrap ${activeView === 'chat' ? 'bg-neon/15 text-neon border border-neon/30' : 'text-on-surface-variant border border-outline-variant/20'}`}>
            <span className="material-symbols-outlined text-[16px]">chat</span> AI 트레이너
          </button>
          <button onClick={() => setActiveView('plan')}
            className={`flex items-center gap-1.5 px-3 md:px-4 py-2 rounded-full text-xs font-headline font-bold transition-all whitespace-nowrap ${activeView === 'plan' ? 'bg-neon/15 text-neon border border-neon/30' : 'text-on-surface-variant border border-outline-variant/20'}`}>
            <span className="material-symbols-outlined text-[16px]">fitness_center</span><span className="md:hidden">루틴 보기</span><span className="hidden md:inline">상세 루틴 보기</span>
          </button>
          <button onClick={() => setActiveView('history')}
            className={`flex items-center gap-1.5 px-3 md:px-4 py-2 rounded-full text-xs font-headline font-bold transition-all whitespace-nowrap ${activeView === 'history' ? 'bg-neon/15 text-neon border border-neon/30' : 'text-on-surface-variant border border-outline-variant/20'}`}>
            <span className="material-symbols-outlined text-[16px]">history</span><span className="md:hidden">저장 루틴</span><span className="hidden md:inline">저장된 루틴</span> {savedHistory.length > 0 && <span className="bg-neon/20 text-neon text-[9px] px-1.5 rounded-full">{savedHistory.length}</span>}
          </button>
        </div>
      </div>

      {/* ═══ AI 트레이너 모드: 챗봇 + 사이드 루틴 ═══ */}
      {activeView === 'chat' && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 md:gap-6">
          <div className="col-span-1 md:col-span-3">
            <WorkoutChatPanel userId={userId} selectedModel={selectedModel} plan={plan} setPlan={setPlan} setActiveView={setActiveView} />
          </div>
          <div className="col-span-1 md:col-span-2">
            <WorkoutPlanView plan={plan} setPlan={setPlan} activeDay={activeDay} setActiveDay={setActiveDay}
              userId={userId} selectedModel={selectedModel} profile={profile} compact />
          </div>
        </div>
      )}

      {/* ═══ 상세 루틴 보기 모드: 풀페이지 원래 UIUX 디자인 ═══ */}
      {activeView === 'plan' && (
        <>
          {plan?.workout_plan && (
            <div className="flex justify-end">
              <button onClick={saveWorkoutPlan} disabled={saving}
                className="btn-neon text-xs flex items-center gap-2">
                <span className="material-symbols-outlined text-[16px]">save</span>
                {saving ? '저장 중...' : '이 루틴 저장하기'}
              </button>
            </div>
          )}
          <FullPageWorkoutView plan={plan} setPlan={setPlan} activeDay={activeDay} setActiveDay={setActiveDay}
            userId={userId} selectedModel={selectedModel} profile={profile} />
        </>
      )}

      {/* ═══ 저장된 운동 루틴 이력 ═══ */}
      {activeView === 'history' && (
        <WorkoutHistoryView history={savedHistory} onLoad={loadSavedPlan} onDelete={deleteSavedPlan} />
      )}
    </div>
  )
}


// =============================================
// 운동 챗봇 패널
// =============================================

function WorkoutChatPanel({ userId, selectedModel, plan, setPlan, setActiveView }) {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: '안녕하세요! 저는 헬창지피티 AI 트레이너예요 💪\n\n이렇게 말해보세요:\n• "일주일 운동 계획 짜줘"\n• "오늘 상체 운동 추천해줘"\n• "30분밖에 시간이 없어"\n• "무릎이 아파서 하체 운동 대체해줘"\n• "오늘은 가볍게 하고 싶어"\n\n프로필에 입력한 주당 운동 횟수에 맞춰 7일 계획을 만들어드릴게요!' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const endRef = useRef(null)

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || loading) return
    const userMsg = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: userMsg }])
    setLoading(true)

    try {
      const res = await fetch('/api/v1/workout/chat', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, message: userMsg, model: selectedModel, current_plan: plan?.workout_plan || null }),
      })
      const data = await res.json()
      let reply = data.reply || '답변을 받지 못했어요.'

      if (data.workout_plan_update) {
        reply += '\n\n✅ 운동 계획이 업데이트되었어요! 옆 패널에서 바로 확인하세요.'
        setPlan(prev => {
          const prevPlan = prev?.workout_plan || {}
          const update = data.workout_plan_update
          // deep merge: weekly_plan 내부까지 병합
          const mergedWeekly = { ...prevPlan.weekly_plan }
          if (update.weekly_plan) {
            for (const [dayKey, dayData] of Object.entries(update.weekly_plan)) {
              mergedWeekly[dayKey] = { ...(mergedWeekly[dayKey] || {}), ...dayData }
            }
          }
          return {
            ...prev,
            workout_plan: {
              ...prevPlan,
              ...update,
              weekly_plan: update.weekly_plan ? mergedWeekly : (prevPlan.weekly_plan || {}),
            },
          }
        })
        // 채팅 모드 유지 — 탭 전환하지 않음 (사이드 패널에서 실시간 확인)
      }

      setMessages(prev => [...prev, { role: 'assistant', text: reply, hasPlanUpdate: !!data.workout_plan_update }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', text: 'AI 서버에 연결할 수 없어요. Ollama가 실행 중인지 확인해주세요.\n\n💡 이런 것들을 물어볼 수 있어요:\n• 일주일 운동 계획 짜줘\n• 오늘 가슴 운동\n• 20분 전신 운동' }])
    }
    setLoading(false)
  }

  return (
    <div className="card-surface flex flex-col" style={{ height: '620px' }}>
      <div className="flex items-center gap-2 pb-3 border-b border-outline-variant/10">
        <span className="text-neon text-lg">💪</span>
        <span className="font-headline font-bold text-sm">AI 트레이너</span>
        <span className="text-[10px] text-on-surface-variant">| {selectedModel}</span>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 py-3">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${msg.role === 'user' ? 'bg-neon/15 text-on-surface' : 'bg-surface-container-high text-on-surface'}`}>
              {msg.role === 'assistant' && (
                <div className="flex items-center gap-1.5 mb-1">
                  <span className="text-neon text-xs">🏋️</span>
                  <span className="text-[10px] font-headline font-bold text-neon">AI 트레이너</span>
                </div>
              )}
              <p className="text-sm whitespace-pre-wrap">{msg.text}</p>
              {msg.hasPlanUpdate && <div className="mt-2 bg-neon/10 rounded-lg px-2 py-1"><span className="text-[10px] text-neon font-bold">✅ 루틴 반영 완료</span></div>}
            </div>
          </div>
        ))}
        {loading && <div className="flex justify-start"><div className="bg-surface-container-high rounded-2xl px-4 py-3"><span className="text-on-surface-variant text-sm animate-pulse">루틴을 설계하는 중...</span></div></div>}
        <div ref={endRef} />
      </div>

      <div className="flex gap-2 border-t border-outline-variant/10 pt-3">
        <input value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
          placeholder="AI 트레이너에게 물어보세요... (예: 일주일 운동 짜줘)"
          className="input-dark flex-1 py-2.5 text-sm" disabled={loading} />
        <button onClick={sendMessage} disabled={loading || !input.trim()} className="btn-neon px-4">
          <span className="material-symbols-outlined text-[18px]">send</span>
        </button>
      </div>
    </div>
  )
}


// =============================================
// 상세 루틴 보기
// =============================================

function WorkoutPlanView({ plan, setPlan, activeDay, setActiveDay, userId, selectedModel, profile }) {
  const [loading, setLoading] = useState(false)

  const generatePlan = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/v1/workout/demo', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          frequency: profile?.nlp_analysis?.exercise_frequency || 3,
          goal_type: profile?.nlp_analysis?.goal_type || '체지방감소',
          experience: profile?.nlp_analysis?.experience_level || '입문',
          constraints: profile?.nlp_analysis?.constraints || [],
        }),
      })
      if (res.ok) setPlan(await res.json())
    } catch { setPlan(DEMO_WORKOUT) }
    setLoading(false)
  }

  const wp = plan?.workout_plan?.weekly_plan || {}
  const days = Object.entries(wp).filter(([k]) => k.startsWith('day'))
  const restDays = plan?.workout_plan?.rest_days || []
  const currentDay = days[activeDay]?.[1]
  const analysis = plan?.analysis || {}

  if (!plan) {
    return (
      <div className="space-y-4">
        <div className="card-surface text-center py-12">
          <span className="text-4xl block mb-3">🏋️</span>
          <p className="font-headline font-bold text-sm">아직 운동 계획이 없어요</p>
          <p className="text-on-surface-variant text-xs mt-1 mb-4">AI 트레이너와 대화하거나 아래 버튼으로 만들어보세요</p>
          <button onClick={generatePlan} disabled={loading} className="btn-neon text-xs flex items-center gap-2 mx-auto">
            {loading ? '만드는 중...' : <><span className="material-symbols-outlined text-[16px]">auto_awesome</span> 일주일 운동 계획 만들기</>}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* 7일 캘린더 */}
      <div className="grid grid-cols-7 gap-1.5">
        {DAYS_KR.map((day, i) => {
          const workoutDayIndex = days.findIndex(([_, d]) => d.day_label === day || d.day_label === day + '요일')
          const isWorkout = workoutDayIndex >= 0
          const isRest = restDays.includes(day) || restDays.includes(day + '요일')
          const isActive = isWorkout && workoutDayIndex === activeDay

          return (
            <button key={day} onClick={() => isWorkout && setActiveDay(workoutDayIndex)}
              className={`py-2.5 rounded-xl text-center transition-all ${
                isActive ? 'bg-neon text-on-primary-fixed shadow-neon-glow' :
                isWorkout ? 'bg-surface-container-high text-on-surface hover:bg-surface-container-highest cursor-pointer' :
                'bg-surface-container-low text-on-surface-variant/30'}`}>
              <p className="font-headline font-bold text-[10px] tracking-widest">{day}</p>
              {isWorkout ? (
                <>
                  <p className="font-headline font-black text-lg mt-0.5">
                    {days[workoutDayIndex]?.[1]?.focus?.substring(0, 2) || '운동'}
                  </p>
                  <div className="w-1 h-1 rounded-full bg-current mx-auto mt-0.5" />
                </>
              ) : (
                <p className="text-[10px] mt-1 text-on-surface-variant/40">휴식</p>
              )}
            </button>
          )
        })}
      </div>

      {/* 오늘의 운동 상세 — 원래 양식 (대형 메인 카드 + AI 패널 + 2열 그리드) */}
      {currentDay && (
        <div className="space-y-3">
          {/* 헤더 */}
          <div className="flex items-start justify-between">
            <div>
              <h3 className="font-headline font-black text-2xl tracking-tighter">
                {currentDay.focus?.toUpperCase()} <span className="italic text-neon">정밀 루틴</span>
              </h3>
              <p className="section-subtitle flex items-center gap-2">
                <span className="material-symbols-outlined text-[14px]">schedule</span>
                예상 {currentDay.estimated_time_min}분 · 약 {currentDay.estimated_calories}kcal 소모
              </p>
            </div>
            <button className="btn-neon text-xs flex items-center gap-2">
              <span className="material-symbols-outlined text-[16px]">play_arrow</span> 세션 시작하기
            </button>
          </div>

          {/* 메인 운동 (첫 번째) — 대형 5:2 레이아웃 */}
          {currentDay.main_workout?.exercises?.slice(0, 1).map((ex, i) => (
            <div key={i} className="card-elevated grid grid-cols-1 md:grid-cols-5 gap-4 md:gap-6">
              <div className="col-span-1 md:col-span-3 space-y-3">
                <span className="badge-neon">오늘의 메인 운동</span>
                <h3 className="font-headline font-black text-3xl tracking-tighter uppercase">{ex.name}</h3>
                <p className="text-on-surface-variant text-sm">{ex.description}</p>
                <div className="flex gap-8 mt-4">
                  <div><p className="metric-label">세트 수</p><p className="font-headline font-black text-3xl">{ex.sets}</p></div>
                  <div><p className="metric-label">반복 횟수</p><p className="font-headline font-black text-3xl">{ex.reps}</p></div>
                  <div><p className="metric-label">쉬는 시간</p><p className="font-headline font-black text-3xl">{ex.rest_sec}<span className="text-sm text-on-surface-variant">초</span></p></div>
                </div>
              </div>
              <div className="col-span-2 bg-surface-container rounded-xl p-5">
                <p className="metric-label">AI가 분석한 이 운동 정보</p>
                <p className="font-headline font-bold text-sm mt-2">운동 강도: <span className="text-neon uppercase">{ex.intensity === '중' ? '보통' : ex.intensity === '고' ? '높음' : ex.intensity === '저' ? '낮음' : ex.intensity}</span></p>
                <p className="text-on-surface-variant text-xs mt-3">타겟 부위: {ex.target_muscle}</p>
                {ex.caution && <p className="text-error text-xs mt-2">⚠ {ex.caution}</p>}
                {ex.alternatives?.length > 0 && (
                  <div className="mt-3">
                    <p className="metric-label">이 운동 대신 할 수 있는 운동</p>
                    {ex.alternatives.map((alt, j) => <span key={j} className="inline-block text-[10px] text-on-surface-variant bg-surface-container-low rounded-full px-2 py-0.5 mr-1 mt-1">{alt}</span>)}
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* 나머지 운동 — 2열 그리드 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {currentDay.main_workout?.exercises?.slice(1).map((ex, i) => (
              <div key={i} className="card-elevated hover:shadow-neon-glow transition-shadow">
                <div className="flex items-center justify-between mb-2">
                  <span className="metric-label">{ex.target_muscle}</span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    ex.intensity === '고' || ex.intensity === '높음' ? 'bg-error/15 text-error' :
                    ex.intensity === '중' || ex.intensity === '보통' ? 'bg-neon/15 text-neon' :
                    'bg-surface-container-high text-on-surface-variant'}`}>
                    강도: {ex.intensity === '중' ? '보통' : ex.intensity === '고' ? '높음' : ex.intensity === '저' ? '낮음' : ex.intensity}
                  </span>
              </div>

              <h4 className="font-headline font-black text-lg tracking-tight uppercase">{ex.name}</h4>
              <p className="text-on-surface-variant text-xs mt-1">{ex.description}</p>

              <div className="flex gap-6 mt-3">
                <div><p className="metric-label">세트</p><p className="font-headline font-bold text-xl">{ex.sets}</p></div>
                <div><p className="metric-label">반복</p><p className="font-headline font-bold text-xl">{ex.reps}</p></div>
                <div><p className="metric-label">쉬는 시간</p><p className="font-headline font-bold text-xl">{ex.rest_sec}<span className="text-xs text-on-surface-variant">초</span></p></div>
              </div>

              {ex.caution && <p className="text-error/80 text-[10px] mt-2 flex items-center gap-1"><span className="material-symbols-outlined text-[12px]">warning</span>{ex.caution}</p>}

              {ex.alternatives?.length > 0 && (
                <div className="mt-2 pt-2 border-t border-outline-variant/5">
                  <span className="text-[10px] text-on-surface-variant/50">대체 운동: </span>
                  {ex.alternatives.map((alt, j) => <span key={j} className="text-[10px] text-neon/50 bg-neon/5 px-1.5 py-0.5 rounded mr-1">{alt}</span>)}
                </div>
              )}
            </div>
          ))}
          </div>

          {/* 팁 */}
          {currentDay.tip && (
            <div className="bg-surface-container-low rounded-xl px-4 py-2.5 flex items-center gap-2">
              <span className="text-neon text-sm">💡</span>
              <p className="text-xs text-on-surface-variant">{currentDay.tip}</p>
            </div>
          )}
        </div>
      )}

      {/* 분석 */}
      {analysis.grade && (
        <div className="card-surface flex items-center gap-4">
          <div className="text-center">
            <p className="metric-label">균형 점수</p>
            <p className="font-headline font-black text-xl text-neon">{analysis.grade}</p>
            <p className="text-[10px] text-on-surface-variant">{analysis.overall_score}/100</p>
          </div>
          <div className="flex-1 space-y-1">
            {analysis.improvements?.map((imp, i) => <p key={i} className="text-[10px] text-on-surface-variant">→ {imp}</p>)}
          </div>
        </div>
      )}
    </div>
  )
}


// =============================================
// 풀페이지 상세 루틴 보기 (원래 UIUX 디자인)
// =============================================

function FullPageWorkoutView({ plan, setPlan, activeDay, setActiveDay, userId, selectedModel, profile }) {
  const [loading, setLoading] = useState(false)
  const wp = plan?.workout_plan?.weekly_plan || {}
  const days = Object.entries(wp).filter(([k]) => k.startsWith('day'))
  const restDays = plan?.workout_plan?.rest_days || []
  const currentDay = days[activeDay]?.[1]
  const analysis = plan?.analysis || {}

  const generatePlan = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/v1/workout/demo', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ frequency: profile?.nlp_analysis?.exercise_frequency || 3, goal_type: profile?.nlp_analysis?.goal_type || '체지방감소', experience: profile?.nlp_analysis?.experience_level || '입문', constraints: profile?.nlp_analysis?.constraints || [] }),
      })
      if (res.ok) setPlan(await res.json())
    } catch { setPlan(DEMO_WORKOUT) }
    setLoading(false)
  }

  if (!plan) {
    return (
      <div className="card-surface text-center py-20">
        <span className="text-3xl md:text-5xl block mb-4">🏋️</span>
        <p className="font-headline font-bold text-lg">아직 운동 계획이 없어요</p>
        <p className="text-on-surface-variant text-sm mt-2 mb-6">"AI 트레이너" 탭에서 대화하거나 아래 버튼으로 만들어보세요</p>
        <button onClick={generatePlan} disabled={loading} className="btn-neon text-xs flex items-center gap-2 mx-auto">
          {loading ? '만드는 중...' : <><span className="material-symbols-outlined text-[16px]">auto_awesome</span> 일주일 운동 계획 만들기</>}
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 헤더 — 원래 UIUX: 대형 제목 + START SESSION */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-headline font-black text-4xl tracking-tighter">
            {currentDay?.focus?.toUpperCase() || 'WORKOUT'} <span className="italic text-neon">PRECISION</span>
          </h3>
          <p className="section-subtitle flex items-center gap-2 mt-1">
            <span className="material-symbols-outlined text-[14px]">schedule</span>
            예상 {currentDay?.estimated_time_min || '—'}분 | 집중 부위: {currentDay?.focus || '—'}
          </p>
        </div>
        <button className="btn-neon flex items-center gap-2">
          <span className="material-symbols-outlined text-[18px]">play_arrow</span>
          세션 시작하기
        </button>
      </div>

      {/* 주간 캘린더 — 원래 UIUX: 7열 날짜 블록 */}
      <div className="grid grid-cols-7 gap-2">
        {DAYS_KR.map((day, i) => {
          const wdi = days.findIndex(([_, d]) => d.day_label === day || d.day_label === day + '요일')
          const isWorkout = wdi >= 0
          const isActive = isWorkout && wdi === activeDay
          return (
            <button key={day} onClick={() => isWorkout && setActiveDay(wdi)}
              className={`py-3 rounded-xl text-center transition-all ${
                isActive ? 'bg-neon text-on-primary-fixed shadow-neon-glow' :
                isWorkout ? 'bg-surface-container-high text-on-surface hover:bg-surface-container-highest cursor-pointer' :
                'bg-surface-container-low text-on-surface-variant/30'}`}>
              <p className="font-headline font-bold text-[10px] uppercase tracking-widest">{day}</p>
              <p className="font-headline font-black text-2xl mt-1">{isWorkout ? (10 + i) : '—'}</p>
              {isWorkout && <div className="w-1 h-1 rounded-full bg-current mx-auto mt-1" />}
            </button>
          )
        })}
      </div>

      {/* 메인 운동 — 원래 UIUX: 대형 3:2 카드 (운동 상세 + AI 분석) */}
      {currentDay?.main_workout?.exercises?.slice(0, 1).map((ex, i) => (
        <div key={i} className="card-elevated grid grid-cols-1 md:grid-cols-5 gap-4 md:gap-6">
          <div className="col-span-1 md:col-span-3 space-y-4">
            <span className="badge-neon">오늘의 메인 운동 (PRIMARY LIFT)</span>
            <h3 className="font-headline font-black text-4xl tracking-tighter uppercase">{ex.name}</h3>
            <p className="text-on-surface-variant text-sm leading-relaxed">{ex.description}</p>
            <div className="flex gap-10 mt-4">
              <div><p className="metric-label">세트 수 (SETS)</p><p className="font-headline font-black text-4xl">{ex.sets}</p></div>
              <div><p className="metric-label">반복 횟수 (REPS)</p><p className="font-headline font-black text-4xl">{ex.reps}</p></div>
              <div><p className="metric-label">쉬는 시간 (REST)</p><p className="font-headline font-black text-4xl">{ex.rest_sec}<span className="text-lg text-on-surface-variant">s</span></p></div>
            </div>
          </div>
          <div className="col-span-2 bg-surface-container rounded-xl p-6 space-y-4">
            <p className="font-headline font-bold text-sm uppercase tracking-tight">AI 퍼포먼스 분석</p>
            <div>
              <p className="metric-label">운동 강도</p>
              <p className="font-headline font-bold text-lg text-neon mt-1">{ex.intensity === '중' ? '보통 (MODERATE)' : ex.intensity === '고' ? '높음 (HIGH)' : '낮음 (LOW)'}</p>
            </div>
            <div>
              <p className="metric-label">타겟 부위</p>
              <p className="text-on-surface text-sm mt-1">{ex.target_muscle}</p>
            </div>
            {ex.caution && <p className="text-error text-xs mt-2">⚠ {ex.caution}</p>}
            {ex.alternatives?.length > 0 && (
              <div>
                <p className="metric-label">대체 운동</p>
                <div className="flex gap-2 mt-1 flex-wrap">
                  {ex.alternatives.map((alt, j) => <span key={j} className="text-xs text-on-surface-variant bg-surface-container-low rounded-full px-3 py-1">{alt}</span>)}
                </div>
              </div>
            )}
          </div>
        </div>
      ))}

      {/* 나머지 운동 — 원래 UIUX: 2열 그리드 카드 */}
      {currentDay?.main_workout?.exercises?.length > 1 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
          {currentDay.main_workout.exercises.slice(1).map((ex, i) => (
            <div key={i} className="card-elevated hover:shadow-neon-glow transition-shadow">
              <div className="flex items-center justify-between mb-2">
                <span className="metric-label">{ex.target_muscle}</span>
                <span className="text-[10px] text-on-surface-variant">쉬는 시간: {ex.rest_sec}초</span>
              </div>
              <h4 className="font-headline font-black text-xl tracking-tight uppercase">{ex.name}</h4>
              <p className="text-on-surface-variant text-xs mt-1">{ex.description}</p>
              <div className="flex gap-8 mt-3">
                <div><p className="metric-label">세트</p><p className="font-headline font-bold text-2xl">{ex.sets}</p></div>
                <div><p className="metric-label">반복</p><p className="font-headline font-bold text-2xl">{ex.reps}</p></div>
              </div>
              {ex.caution && <p className="text-error/80 text-[10px] mt-2">⚠ {ex.caution}</p>}
              {ex.alternatives?.length > 0 && (
                <div className="mt-2 pt-2 border-t border-outline-variant/5">
                  <span className="text-[10px] text-on-surface-variant/50">대체: </span>
                  {ex.alternatives.map((alt, j) => <span key={j} className="text-[10px] text-neon/50 bg-neon/5 px-1.5 py-0.5 rounded mr-1">{alt}</span>)}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 오늘의 팁 */}
      {currentDay?.tip && (
        <div className="bg-surface-container-low rounded-xl px-5 py-3 flex items-center gap-3">
          <span className="text-neon text-lg">💡</span>
          <p className="text-sm text-on-surface-variant">{currentDay.tip}</p>
        </div>
      )}

      {/* 루틴 분석 */}
      {analysis.grade && (
        <div className="card-surface flex items-center gap-6">
          <div className="text-center px-4">
            <p className="metric-label">균형 점수</p>
            <p className="font-headline font-black text-3xl text-neon">{analysis.grade}</p>
            <p className="text-[10px] text-on-surface-variant">{analysis.overall_score}/100</p>
          </div>
          <div className="flex-1 space-y-1">
            {analysis.improvements?.map((imp, i) => <p key={i} className="text-xs text-on-surface-variant">→ {imp}</p>)}
          </div>
        </div>
      )}
    </div>
  )
}


// =============================================
// 저장된 운동 루틴 이력 보기
// =============================================

function WorkoutHistoryView({ history, onLoad, onDelete }) {
  if (history.length === 0) {
    return (
      <div className="card-surface text-center py-16">
        <span className="text-3xl md:text-5xl block mb-4">💪</span>
        <p className="font-headline font-bold text-lg">저장된 운동 루틴이 없어요</p>
        <p className="text-on-surface-variant text-sm mt-2">AI 트레이너와 대화해서 루틴을 만들고 "이 루틴 저장하기" 버튼을 눌러보세요!</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="card-elevated flex items-center justify-between">
        <div>
          <p className="font-headline font-bold text-lg">💪 저장된 운동 루틴</p>
          <p className="text-on-surface-variant text-xs">지금까지 {history.length}개의 루틴을 저장했어요</p>
        </div>
        <div className="text-right">
          <p className="font-headline font-black text-3xl text-neon">{history.length}</p>
          <p className="metric-label">총 루틴</p>
        </div>
      </div>

      <div className="space-y-3">
        {[...history].reverse().map((entry) => {
          const days = entry.days_count || 0
          const savedDate = entry.saved_at ? new Date(entry.saved_at).toLocaleDateString('ko', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : ''
          const weeklyPlan = entry.workout_plan?.weekly_plan || {}
          const focuses = Object.values(weeklyPlan).map(d => d.focus).filter(Boolean).slice(0, 3)

          return (
            <div key={entry.id} className="card-elevated hover:shadow-neon-glow transition-shadow">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-neon/10 flex items-center justify-center">
                    <span className="text-neon text-lg">🏋️</span>
                  </div>
                  <div>
                    <p className="font-headline font-bold text-sm">{entry.title}</p>
                    <div className="flex items-center gap-3 text-[10px] text-on-surface-variant mt-0.5">
                      <span>📅 {savedDate}</span>
                      <span>🗓️ {days}일</span>
                    </div>
                    {focuses.length > 0 && (
                      <div className="flex gap-1 mt-1">
                        {focuses.map((f, i) => <span key={i} className="text-[9px] bg-neon/10 text-neon px-1.5 py-0.5 rounded">{f}</span>)}
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => onLoad(entry)}
                    className="btn-neon text-[10px] py-1.5 px-3 flex items-center gap-1">
                    <span className="material-symbols-outlined text-[14px]">visibility</span> 불러오기
                  </button>
                  <button onClick={() => onDelete(entry.id)}
                    className="btn-ghost text-[10px] py-1.5 px-3 text-error/60 border-error/20 hover:text-error hover:border-error/40">
                    <span className="material-symbols-outlined text-[14px]">delete</span>
                  </button>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}


const DEMO_WORKOUT = {
  workout_plan: {
    weekly_plan: {
      day1: { day_label: "월", focus: "상체 + 코어", estimated_time_min: 50, estimated_calories: 250,
        main_workout: { exercises: [
          { name: "푸쉬업", target_muscle: "가슴", sets: 3, reps: "8~12", rest_sec: 60, intensity: "보통", description: "팔꿈치를 45도로 유지하며 가슴까지 내려갔다 올라옵니다", alternatives: ["머신 체스트프레스", "덤벨 플라이"], caution: "" },
          { name: "랫풀다운", target_muscle: "등", sets: 3, reps: "10~12", rest_sec: 60, intensity: "보통", description: "견갑골을 모으며 바를 쇄골 쪽으로 당깁니다", alternatives: ["시티드 로우"], caution: "" },
          { name: "덤벨 숄더프레스", target_muscle: "어깨", sets: 3, reps: "10~12", rest_sec: 60, intensity: "보통", description: "덤벨을 귀 옆에서 머리 위로 밀어 올립니다", alternatives: ["머신 숄더프레스"], caution: "" },
          { name: "플랭크", target_muscle: "코어", sets: 3, reps: "30초", rest_sec: 45, intensity: "보통", description: "팔꿈치와 발끝으로 몸을 지탱, 일직선 유지", alternatives: ["데드버그"], caution: "" },
        ]}, tip: "운동 전 물 한 잔, 운동 중 수시로 수분 보충하세요" },
      day2: { day_label: "수", focus: "하체 + 유산소", estimated_time_min: 60, estimated_calories: 300,
        main_workout: { exercises: [
          { name: "레그프레스", target_muscle: "하체", sets: 3, reps: "10~12", rest_sec: 90, intensity: "보통", description: "머신에서 발판을 밀어냅니다 (무릎 부담 적음)", alternatives: ["고블릿 스쿼트"], caution: "" },
          { name: "힙 브릿지", target_muscle: "둔근", sets: 3, reps: "15", rest_sec: 60, intensity: "보통", description: "누워서 엉덩이를 들어올립니다", alternatives: ["힙쓰러스트"], caution: "" },
          { name: "사이클", target_muscle: "유산소", sets: 1, reps: "20분", rest_sec: 0, intensity: "보통", description: "실내 자전거 중간 강도로 타기", alternatives: ["일립티컬"], caution: "" },
        ]}, tip: "호흡을 멈추지 마세요! 힘 쓸 때 내쉬고, 돌아올 때 들이쉽니다" },
      day3: { day_label: "금", focus: "전신 + 유산소", estimated_time_min: 50, estimated_calories: 280,
        main_workout: { exercises: [
          { name: "스쿼트", target_muscle: "하체", sets: 3, reps: "10~12", rest_sec: 90, intensity: "보통", description: "전신 운동의 기본, 하체 전체 자극", alternatives: ["레그프레스"], caution: "" },
          { name: "푸쉬업", target_muscle: "가슴", sets: 3, reps: "8~12", rest_sec: 60, intensity: "보통", description: "상체 밀기 동작의 기본", alternatives: ["인클라인 푸쉬업"], caution: "" },
          { name: "트레드밀 경사걷기", target_muscle: "유산소", sets: 1, reps: "15분", rest_sec: 0, intensity: "보통", description: "경사도 5~8%에서 시속 5km 걷기", alternatives: ["사이클"], caution: "" },
        ]}, tip: "무게보다 자세가 먼저입니다. 올바른 자세를 유지하세요" },
    },
    rest_days: ["화", "목", "토", "일"],
    disclaimer_short: "⚠️ AI 추천 루틴은 참고용입니다. 본인 체력에 맞게 자유롭게 조정하세요. 통증 시 즉시 중단!",
  },
  analysis: { balance_score: 74, overall_score: 81, grade: "B", improvements: ["유산소 운동 추가 권장", "이두/삼두 부위 운동 추가 권장"] },
}
