import { useState, useEffect, useRef } from 'react'

const MEAL_ICONS = { breakfast: '☀️', lunch: '🍱', dinner: '🌙', snack: '🥤' }
const MEAL_NAMES = { breakfast: '아침', lunch: '점심', dinner: '저녁', snack: '간식' }
const ALLERGY_OPTIONS = ['우유/유제품', '계란', '땅콩', '견과류', '밀/글루텐', '대두/콩', '갑각류', '생선', '조개류', '복숭아']
const EXCLUDED_PRESETS = ['돼지고기', '소고기', '닭고기', '해산물', '유제품', '매운 음식']

export default function DietPage({ profile, selectedModel = 'exaone3.5:7.8b', userId: propUserId }) {
  const [activeView, setActiveView] = useState('chat') // chat | plan | history
  const [mealPlan, setMealPlan] = useState(null)
  const [activeDay, setActiveDay] = useState(0)
  const [allergies, setAllergies] = useState([])
  const [excluded, setExcluded] = useState([])
  const [loading, setLoading] = useState(false)
  const [savedHistory, setSavedHistory] = useState([])
  const [saving, setSaving] = useState(false)

  const userId = propUserId || profile?.user_id || 'default'

  // 페이지 로드 시 최근 저장된 식단 불러오기
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`/api/v1/diet/${userId}/history`)
        if (res.ok) {
          const data = await res.json()
          setSavedHistory(data.entries || [])
          // 가장 최근 저장된 식단이 있으면 자동 로드
          if (data.entries?.length > 0 && !mealPlan) {
            const latest = data.entries[data.entries.length - 1]
            setMealPlan({ meal_plan: latest.meal_plan, macro_targets: latest.macro_targets })
          }
        }
      } catch {}
    })()
  }, [userId])

  // 식단 저장 함수
  const saveMealPlan = async () => {
    if (!mealPlan?.meal_plan) return
    setSaving(true)
    try {
      const res = await fetch('/api/v1/diet/save', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, meal_plan: mealPlan.meal_plan, macro_targets: mealPlan.macro_targets, allergies, excluded_foods: excluded }),
      })
      if (res.ok) {
        const data = await res.json()
        setSavedHistory(prev => [...prev, data.entry])
      }
    } catch {}
    setSaving(false)
  }

  // 저장된 식단 불러오기
  const loadSavedPlan = (entry) => {
    setMealPlan({ meal_plan: entry.meal_plan, macro_targets: entry.macro_targets })
    setAllergies(entry.allergies || [])
    setExcluded(entry.excluded_foods || [])
    setActiveView('plan')
  }

  // 저장된 식단 삭제
  const deleteSavedPlan = async (dietId) => {
    try {
      await fetch(`/api/v1/diet/${userId}/${dietId}`, { method: 'DELETE' })
      setSavedHistory(prev => prev.filter(e => e.id !== dietId))
    } catch {}
  }

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
        <div>
          <span className="badge-neon">맞춤 식단 AI</span>
          <h2 className="font-headline font-black text-4xl tracking-tighter mt-3">
            오늘 <span className="italic text-neon">뭐 먹지?</span>
          </h2>
          <p className="section-subtitle">AI와 대화하면서 나만의 3일치 맞춤 식단을 만들어보세요</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <button onClick={() => setActiveView('chat')}
            className={`flex items-center gap-1.5 px-3 md:px-4 py-2 rounded-full text-xs font-headline font-bold transition-all whitespace-nowrap ${activeView === 'chat' ? 'bg-neon/15 text-neon border border-neon/30' : 'text-on-surface-variant border border-outline-variant/20'}`}>
            <span className="material-symbols-outlined text-[16px]">chat</span> AI 대화
          </button>
          <button onClick={() => setActiveView('plan')}
            className={`flex items-center gap-1.5 px-3 md:px-4 py-2 rounded-full text-xs font-headline font-bold transition-all whitespace-nowrap ${activeView === 'plan' ? 'bg-neon/15 text-neon border border-neon/30' : 'text-on-surface-variant border border-outline-variant/20'}`}>
            <span className="material-symbols-outlined text-[16px]">restaurant</span> 식단 보기
          </button>
          <button onClick={() => setActiveView('history')}
            className={`flex items-center gap-1.5 px-3 md:px-4 py-2 rounded-full text-xs font-headline font-bold transition-all whitespace-nowrap ${activeView === 'history' ? 'bg-neon/15 text-neon border border-neon/30' : 'text-on-surface-variant border border-outline-variant/20'}`}>
            <span className="material-symbols-outlined text-[16px]">history</span><span className="md:hidden">저장 식단</span><span className="hidden md:inline">저장된 식단</span> {savedHistory.length > 0 && <span className="bg-neon/20 text-neon text-[9px] px-1.5 rounded-full">{savedHistory.length}</span>}
          </button>
        </div>
      </div>

      {/* ═══ AI 대화 모드: 챗봇 + 사이드 설정 ═══ */}
      {activeView === 'chat' && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 md:gap-6">
          <div className="col-span-1 md:col-span-3">
            <DietChatPanel userId={userId} selectedModel={selectedModel} mealPlan={mealPlan}
              setMealPlan={setMealPlan} allergies={allergies} excluded={excluded} setActiveView={setActiveView} />
          </div>
          <div className="col-span-1 md:col-span-2">
          <div className="space-y-4">
            {/* 알레르기 / 제외 설정 */}
            <div className="card-elevated">
              <p className="metric-label mb-2">🚫 못 먹는 음식 / 알레르기</p>
              <div className="flex gap-1.5 flex-wrap mb-2">
                {ALLERGY_OPTIONS.map(a => (
                  <button key={a} onClick={() => setAllergies(prev => prev.includes(a) ? prev.filter(x => x !== a) : [...prev, a])}
                    className={`px-2.5 py-1 rounded-full text-[10px] font-bold transition-all ${allergies.includes(a) ? 'bg-error/15 text-error border border-error/30' : 'bg-surface-container text-on-surface-variant border border-transparent'}`}>
                    {a}
                  </button>
                ))}
              </div>
              <p className="metric-label mb-2 mt-3">🍽️ 추가 제외 식품</p>
              <div className="flex gap-1.5 flex-wrap">
                {EXCLUDED_PRESETS.map(e => (
                  <button key={e} onClick={() => setExcluded(prev => prev.includes(e) ? prev.filter(x => x !== e) : [...prev, e])}
                    className={`px-2.5 py-1 rounded-full text-[10px] font-bold transition-all ${excluded.includes(e) ? 'bg-error/15 text-error border border-error/30' : 'bg-surface-container text-on-surface-variant border border-transparent'}`}>
                    {e}
                  </button>
                ))}
              </div>

              {/* 3일치 식단 생성 버튼 */}
              <button
                onClick={async () => {
                  setLoading(true)
                  try {
                    const res = await fetch('/api/v1/diet/generate-multiday', {
                      method: 'POST', headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ user_id: userId, days: 3, model: selectedModel, allergies, excluded_foods: excluded }),
                    })
                    if (res.ok) { const d = await res.json(); setMealPlan(d); setActiveView('plan') }
                  } catch {}
                  setLoading(false)
                }}
                disabled={loading}
                className="btn-neon w-full mt-4 flex items-center justify-center gap-2 text-xs"
              >
                {loading ? '식단 만드는 중...' : <><span className="material-symbols-outlined text-[16px]">auto_awesome</span> 3일치 맞춤 식단 만들기</>}
              </button>
            </div>

            {/* 식단 미리보기 */}
            {mealPlan?.meal_plan?.days ? (
              <DietQuickPreview mealPlan={mealPlan} onViewDetail={() => setActiveView('plan')} onSave={saveMealPlan} saving={saving} />
            ) : (
              <div className="card-surface text-center py-8">
                <span className="text-3xl block mb-2">🍽️</span>
                <p className="text-on-surface-variant text-xs">식단을 만들면 여기에 미리보기가 표시돼요</p>
              </div>
            )}
          </div>
          </div>
        </div>
      )}

      {/* ===================== 식단 보기 모드: 풀페이지 ===================== */}
      {activeView === 'plan' && (
        <>
          {mealPlan?.meal_plan?.days && (
            <div className="flex justify-end">
              <button onClick={saveMealPlan} disabled={saving}
                className="btn-neon text-xs flex items-center gap-2">
                <span className="material-symbols-outlined text-[16px]">save</span>
                {saving ? '저장 중...' : '이 식단 저장하기'}
              </button>
            </div>
          )}
          <FullPageDietView mealPlan={mealPlan} allergies={allergies} activeDay={activeDay} setActiveDay={setActiveDay} />
        </>
      )}

      {/* ===================== 저장된 식단 이력 ===================== */}
      {activeView === 'history' && (
        <DietHistoryView history={savedHistory} onLoad={loadSavedPlan} onDelete={deleteSavedPlan} />
      )}
    </div>
  )
}


// =============================================
// 사이드 패널: 3일치 식단 요약 미리보기
// =============================================

function DietQuickPreview({ mealPlan, onViewDetail, onSave, saving }) {
  const [previewDay, setPreviewDay] = useState(0)
  const days = mealPlan?.meal_plan?.days
  const macro = mealPlan?.macro_targets || {}

  if (!days) return null

  const dayEntries = Object.entries(days)
  const currentDay = dayEntries[previewDay]?.[1]

  return (
    <div className="space-y-3">
      {/* 칼로리 요약 */}
      <div className="card-elevated bg-neon/5">
        <div className="flex items-center justify-between mb-2">
          <p className="text-neon font-headline font-bold text-sm">✅ {dayEntries.length}일치 식단 완성!</p>
          <span className="text-on-surface-variant text-[10px]">목표 {macro.total_kcal || '—'}kcal</span>
        </div>
        <div className="flex gap-3 text-center text-[10px]">
          <div className="flex-1 bg-surface-container rounded-lg py-1.5">
            <p className="text-on-surface-variant">탄수화물</p>
            <p className="font-headline font-bold text-sm" style={{ color: 'rgb(var(--color-tertiary-container))' }}>{macro.carb_g || '—'}g</p>
          </div>
          <div className="flex-1 bg-surface-container rounded-lg py-1.5">
            <p className="text-on-surface-variant">단백질</p>
            <p className="font-headline font-bold text-sm text-neon">{macro.protein_g || '—'}g</p>
          </div>
          <div className="flex-1 bg-surface-container rounded-lg py-1.5">
            <p className="text-on-surface-variant">지방</p>
            <p className="font-headline font-bold text-sm" style={{ color: 'rgb(var(--color-primary))' }}>{macro.fat_g || '—'}g</p>
          </div>
        </div>
      </div>

      {/* 날짜 탭 */}
      <div className="flex gap-1.5">
        {dayEntries.map(([key, day], i) => (
          <button key={key} onClick={() => setPreviewDay(i)}
            className={`flex-1 py-2 rounded-lg text-center text-[10px] font-headline font-bold transition-all ${
              previewDay === i ? 'bg-neon text-on-primary-fixed' : 'bg-surface-container text-on-surface-variant hover:bg-surface-container-high'}`}>
            {day.date_label || `${i + 1}일차`}
          </button>
        ))}
      </div>

      {/* 선택된 날짜의 끼니 요약 */}
      {currentDay?.meals && (
        <div className="space-y-2">
          {Object.entries(currentDay.meals).map(([key, meal]) => {
            const icon = MEAL_ICONS[key] || '🍽️'
            const name = MEAL_NAMES[key] || key
            const totalCal = (meal.foods || []).reduce((s, f) => s + (f.calories_kcal || 0), 0)
            return (
              <div key={key} className="card-elevated py-3 px-4">
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-1.5">
                    <span className="text-sm">{icon}</span>
                    <span className="font-headline font-bold text-[11px] text-on-surface-variant uppercase">{name}</span>
                    {meal.recommended_time && <span className="text-[9px] text-neon/60 bg-neon/10 px-1.5 rounded">{meal.recommended_time}</span>}
                  </div>
                  <span className="font-headline font-bold text-xs">{totalCal}<span className="text-[9px] text-on-surface-variant">kcal</span></span>
                </div>
                <p className="font-headline font-bold text-xs text-neon truncate">{meal.menu_name}</p>
                <div className="flex gap-1 mt-1 flex-wrap">
                  {(meal.foods || []).map((food, i) => (
                    <span key={i} className="text-[9px] text-on-surface-variant bg-surface-container px-1.5 py-0.5 rounded truncate max-w-[120px]">{food.name}</span>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* 버튼 */}
      <div className="flex gap-2">
        <button onClick={onViewDetail} className="btn-neon flex-1 text-[10px] flex items-center justify-center gap-1 py-2">
          <span className="material-symbols-outlined text-[14px]">fullscreen</span> 상세 보기
        </button>
        <button onClick={onSave} disabled={saving} className="btn-ghost flex-1 text-[10px] flex items-center justify-center gap-1 py-2">
          <span className="material-symbols-outlined text-[14px]">save</span> {saving ? '저장 중...' : '저장'}
        </button>
      </div>
    </div>
  )
}


// =============================================
// 풀페이지 식단 보기 (원래 UIUX 디자인)
// =============================================

function FullPageDietView({ mealPlan, allergies, activeDay, setActiveDay }) {
  const macro = mealPlan?.macro_targets || {}
  const days = mealPlan?.meal_plan?.days
  const currentDayData = days ? Object.values(days)[activeDay] : null

  if (!days) {
    return (
      <div className="card-surface text-center py-20">
        <span className="text-3xl md:text-5xl block mb-4">🍽️</span>
        <p className="font-headline font-bold text-lg">아직 식단이 없어요</p>
        <p className="text-on-surface-variant text-sm mt-2">"AI 대화" 탭에서 식단을 먼저 만들어주세요</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 날짜 탭 */}
      <div className="flex gap-2">
        {Object.entries(days).map(([key, day], i) => (
          <button key={key} onClick={() => setActiveDay(i)}
            className={`flex-1 py-3 rounded-xl text-center font-headline font-bold text-sm transition-all ${
              activeDay === i ? 'bg-neon text-on-primary-fixed shadow-neon-glow' : 'bg-surface-container-high text-on-surface-variant hover:bg-surface-container-highest'}`}>
            {day.date_label || `${i + 1}일차`}
          </button>
        ))}
      </div>

      {/* 칼로리 대시보드 — 원래 UIUX 디자인 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
        {/* 대형 칼로리 카드 */}
        <div className="card-elevated col-span-1 md:col-span-2">
          <p className="metric-label">오늘 먹어야 할 칼로리 (DAILY TARGET)</p>
          <div className="flex items-baseline mt-2">
            <span className="font-headline font-black text-4xl md:text-7xl tracking-tighter">{macro.total_kcal || '—'}</span>
            <span className="font-headline font-light text-2xl text-on-surface-variant ml-2">KCAL</span>
          </div>
          <p className="text-on-surface-variant text-xs mt-3">당신의 목표와 신체 조건에 맞게 AI가 계산한 권장 칼로리</p>
          <div className="flex items-center gap-4 mt-4">
            <span className="font-headline font-bold text-sm text-on-surface-variant">탄:단:지 비율</span>
            <span className="font-headline font-black text-xl">{macro.carb_ratio || 40}:{macro.protein_ratio || 35}:{macro.fat_ratio || 25}</span>
          </div>
        </div>

        {/* 매크로 영양소 */}
        <div className="card-elevated flex flex-col justify-center space-y-4">
          <div className="flex items-center justify-between">
            <span className="font-headline font-bold text-xs text-on-surface-variant">단백질 (PROTEIN)</span>
            <span className="font-headline font-bold text-lg text-neon">{macro.protein_g || '—'}g</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="font-headline font-bold text-xs text-on-surface-variant">탄수화물 (CARBS)</span>
            <span className="font-headline font-bold text-lg" style={{ color: '#3afea0' }}>{macro.carb_g || '—'}g</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="font-headline font-bold text-xs text-on-surface-variant">지방 (FATS)</span>
            <span className="font-headline font-bold text-lg" style={{ color: '#ddffaf' }}>{macro.fat_g || '—'}g</span>
          </div>
        </div>

        {/* 대사 타이밍 */}
        <div className="card-elevated flex flex-col justify-between">
          <div>
            <p className="metric-label">지금 뭘 먹으면 좋을까?</p>
            <p className="text-neon font-headline font-bold text-sm mt-2">운동 후 → 단백질 섭취!</p>
            <p className="text-on-surface-variant text-xs mt-1">단백질 40g 정도 섭취하면 근육 회복에 좋아요</p>
          </div>
          <button className="btn-ghost w-full text-xs mt-3">식단 바꾸기</button>
        </div>
      </div>

      {/* 식단 제목 */}
      <div>
        <h3 className="font-headline font-black text-2xl tracking-tighter italic">오늘의 식단 추천</h3>
        <p className="section-subtitle">시간대별로 무엇을 먹으면 좋은지 AI가 추천해드려요. 취향에 맞게 바꿔도 돼요!</p>
      </div>

      {/* 끼니 카드 — 4열 그리드 (원래 UIUX) */}
      {currentDayData?.meals && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
          {Object.entries(currentDayData.meals).map(([key, meal]) => (
            <MealCardFull key={key} mealKey={key} meal={meal} allergies={allergies} />
          ))}
        </div>
      )}

      {/* AI 영양 분석 */}
      {mealPlan?.analysis && (
        <div className="card-surface">
          <p className="metric-label mb-2">AI 영양 분석 결과</p>
          <div className="flex items-center gap-6">
            <div>
              <span className="font-headline font-bold text-lg text-neon">{mealPlan.analysis.grade}</span>
              <span className="text-on-surface-variant text-xs ml-2">점수: {mealPlan.analysis.overall_score}/100</span>
            </div>
            <div className="flex-1"><p className="text-xs text-on-surface-variant">{mealPlan.analysis.summary}</p></div>
          </div>
          {mealPlan.analysis.keywords?.length > 0 && (
            <div className="flex gap-2 mt-3 flex-wrap">
              {mealPlan.analysis.keywords.map((kw, i) => <span key={i} className="badge-neon">{kw}</span>)}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function MealCardFull({ mealKey, meal, allergies }) {
  const icon = MEAL_ICONS[mealKey] || '🍽️'
  const name = MEAL_NAMES[mealKey] || mealKey
  const totalCal = (meal.foods || []).reduce((s, f) => s + (f.calories_kcal || 0), 0)

  return (
    <div className="card-elevated hover:shadow-neon-glow transition-shadow duration-300 group">
      {/* 시간 뱃지 */}
      {meal.recommended_time && (
        <span className="inline-block bg-neon text-on-primary-fixed text-[10px] font-headline font-bold px-2 py-0.5 rounded-full mb-2">{meal.recommended_time}</span>
      )}

      <div className="flex items-center gap-2">
        <span className="text-xl">{icon}</span>
        <span className="font-headline font-bold text-xs uppercase tracking-tight text-on-surface-variant">{name}</span>
      </div>

      <p className="font-headline font-black text-base mt-2 group-hover:text-neon transition-colors">{meal.menu_name}</p>

      {/* 음식 목록 */}
      <div className="mt-3 space-y-1.5">
        {(meal.foods || []).map((food, i) => (
          <div key={i}>
            <div className="flex items-center justify-between">
              <span className="text-[11px] text-on-surface">{food.name}</span>
              <span className="text-[10px] text-on-surface-variant">{food.amount}</span>
            </div>
            <div className="flex gap-2 text-[9px] text-on-surface-variant/60">
              <span>탄{food.carb_g}g</span><span>단{food.protein_g}g</span><span>지{food.fat_g}g</span>
            </div>
            {food.alternatives?.length > 0 && (
              <div className="flex gap-1 mt-0.5">
                {food.alternatives.map((alt, j) => <span key={j} className="text-[9px] text-neon/40 bg-neon/5 px-1 rounded">{alt}</span>)}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* 칼로리 합계 */}
      <div className="flex items-baseline mt-3 pt-2 border-t border-outline-variant/10">
        <span className="font-headline font-bold text-2xl">{totalCal}</span>
        <span className="text-on-surface-variant text-xs ml-1">KCAL</span>
      </div>

      {meal.tip && <p className="text-[10px] text-neon/50 mt-2 italic">💡 {meal.tip}</p>}
    </div>
  )
}


// =============================================
// 식단 챗봇 패널
// =============================================

function DietChatPanel({ userId, selectedModel, mealPlan, setMealPlan, allergies, excluded, setActiveView }) {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: '안녕하세요! 저는 헬창지피티 AI 영양사예요 🍱\n\n이렇게 말해보세요:\n• "3일치 식단 짜줘"\n• "점심 메뉴 바꿔줘"\n• "오늘 회식이야, 식단 조정해줘"\n• "견과류 알레르기가 있어"\n• "닭가슴살 말고 다른 단백질로"\n\n프로필 정보를 바탕으로 맞춤 식단을 만들어드릴게요!' }
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
      const res = await fetch('/api/v1/diet/chat', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId, message: userMsg, model: selectedModel,
          current_meal_plan: mealPlan?.meal_plan || null,
        }),
      })
      const data = await res.json()

      let reply = data.reply || '답변을 받지 못했어요.'

      // 식단 업데이트 감지
      if (data.meal_plan_update) {
        reply += '\n\n✅ 식단이 업데이트되었어요! "식단 보기"에서 확인하세요.'
        setMealPlan(prev => ({ ...prev, meal_plan: { ...prev?.meal_plan, ...data.meal_plan_update } }))
        setActiveView('plan')
      }

      // 일정 변동 감지
      if (data.schedule_change) {
        reply += `\n\n📅 일정 변동 감지: ${data.schedule_change.type}`
      }

      setMessages(prev => [...prev, { role: 'assistant', text: reply, hasMealUpdate: !!data.meal_plan_update, scheduleChange: data.schedule_change }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', text: 'AI 서버에 연결할 수 없어요. Ollama가 실행 중인지 확인해주세요.\n\n💡 이런 것들을 물어볼 수 있어요:\n• 식단 짜줘\n• 회식 때문에 저녁 변경\n• 알레르기 음식 제외' }])
    }
    setLoading(false)
  }

  return (
    <div className="card-surface flex flex-col" style={{ height: '650px' }}>
      <div className="flex items-center gap-2 pb-3 border-b border-outline-variant/10">
        <span className="text-neon text-lg">🤖</span>
        <span className="font-headline font-bold text-sm">AI 영양사</span>
        <span className="text-[10px] text-on-surface-variant">| {selectedModel}</span>
        {(allergies.length > 0 || excluded.length > 0) && (
          <span className="text-[10px] text-error/60 ml-auto">🚫 제외 {allergies.length + excluded.length}개</span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 py-3">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
              msg.role === 'user' ? 'bg-neon/15 text-on-surface' : 'bg-surface-container-high text-on-surface'}`}>
              {msg.role === 'assistant' && (
                <div className="flex items-center gap-1.5 mb-1">
                  <span className="text-neon text-xs">🍱</span>
                  <span className="text-[10px] font-headline font-bold text-neon">AI 영양사</span>
                </div>
              )}
              <p className="text-sm whitespace-pre-wrap">{msg.text}</p>
              {msg.hasMealUpdate && (
                <div className="mt-2 bg-neon/10 rounded-lg px-2 py-1">
                  <span className="text-[10px] text-neon font-bold">✅ 식단 반영 완료</span>
                </div>
              )}
              {msg.scheduleChange && (
                <div className="mt-2 bg-tertiary/10 rounded-lg px-2 py-1">
                  <span className="text-[10px] text-tertiary font-bold">📅 {msg.scheduleChange.type} 감지 → 식단 조정</span>
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-surface-container-high rounded-2xl px-4 py-3">
              <span className="text-on-surface-variant text-sm animate-pulse">식단을 고민하는 중...</span>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div className="flex gap-2 border-t border-outline-variant/10 pt-3">
        <input value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
          placeholder="AI 영양사에게 물어보세요... (예: 3일치 식단 짜줘)"
          className="input-dark flex-1 py-2.5 text-sm" disabled={loading} />
        <button onClick={sendMessage} disabled={loading || !input.trim()} className="btn-neon px-4">
          <span className="material-symbols-outlined text-[18px]">send</span>
        </button>
      </div>
    </div>
  )
}


// =============================================
// 저장된 식단 이력 보기
// =============================================

function DietHistoryView({ history, onLoad, onDelete }) {
  if (history.length === 0) {
    return (
      <div className="card-surface text-center py-16">
        <span className="text-3xl md:text-5xl block mb-4">📋</span>
        <p className="font-headline font-bold text-lg">저장된 식단이 없어요</p>
        <p className="text-on-surface-variant text-sm mt-2">AI와 대화해서 식단을 만들고 "이 식단 저장하기" 버튼을 눌러보세요!</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="card-elevated flex items-center justify-between">
        <div>
          <p className="font-headline font-bold text-lg">📋 저장된 식단 목록</p>
          <p className="text-on-surface-variant text-xs">지금까지 {history.length}개의 식단을 저장했어요</p>
        </div>
        <div className="text-right">
          <p className="font-headline font-black text-3xl text-neon">{history.length}</p>
          <p className="metric-label">총 식단</p>
        </div>
      </div>

      <div className="space-y-3">
        {[...history].reverse().map((entry) => {
          const days = entry.meal_plan?.days ? Object.keys(entry.meal_plan.days).length : 0
          const kcal = entry.macro_targets?.total_kcal || '—'
          const savedDate = entry.saved_at ? new Date(entry.saved_at).toLocaleDateString('ko', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : ''

          return (
            <div key={entry.id} className="card-elevated hover:shadow-neon-glow transition-shadow">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-neon/10 flex items-center justify-center">
                    <span className="text-neon text-lg">🍱</span>
                  </div>
                  <div>
                    <p className="font-headline font-bold text-sm">{entry.title}</p>
                    <div className="flex items-center gap-3 text-[10px] text-on-surface-variant mt-0.5">
                      <span>📅 {savedDate}</span>
                      <span>📊 {kcal}kcal</span>
                      <span>🗓️ {days}일치</span>
                      {entry.allergies?.length > 0 && <span className="text-error/60">🚫 제외 {entry.allergies.length}</span>}
                    </div>
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


// =============================================
// 끼니 카드 (대체 음식 포함)
// =============================================

function DayMealCards({ dayData, allergies }) {
  if (!dayData?.meals) return null

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {Object.entries(dayData.meals).map(([key, meal]) => (
        <MealCard key={key} mealKey={key} meal={meal} allergies={allergies} />
      ))}
    </div>
  )
}

function MealCard({ mealKey, meal, allergies }) {
  const [showAlts, setShowAlts] = useState(false)
  const icon = MEAL_ICONS[mealKey] || '🍽️'
  const name = MEAL_NAMES[mealKey] || mealKey

  // 끼니 칼로리 계산
  const totalCal = (meal.foods || []).reduce((s, f) => s + (f.calories_kcal || 0), 0)

  return (
    <div className="card-elevated hover:shadow-neon-glow transition-shadow duration-300 group">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">{icon}</span>
        <span className="font-headline font-bold text-xs uppercase tracking-tight text-on-surface-variant">{name}</span>
        <span className="ml-auto font-headline font-bold text-sm">{totalCal}<span className="text-xs text-on-surface-variant ml-0.5">kcal</span></span>
      </div>

      <p className="font-headline font-black text-sm text-neon mb-2">{meal.menu_name}</p>

      <div className="space-y-1.5">
        {(meal.foods || []).map((food, i) => {
          const isExcluded = allergies.some(a => food.name?.includes(a))
          return (
            <div key={i} className={`${isExcluded ? 'line-through opacity-40' : ''}`}>
              <div className="flex items-center justify-between">
                <span className="text-[11px] text-on-surface">{food.name}</span>
                <span className="text-[10px] text-on-surface-variant">{food.amount}</span>
              </div>
              <div className="flex gap-3 text-[9px] text-on-surface-variant/60">
                <span>탄{food.carb_g}g</span>
                <span>단{food.protein_g}g</span>
                <span>지{food.fat_g}g</span>
                <span>{food.calories_kcal}kcal</span>
              </div>
              {/* 대체 음식 */}
              {food.alternatives?.length > 0 && (
                <div className="flex items-center gap-1 mt-0.5">
                  <span className="text-[9px] text-on-surface-variant/40">대체:</span>
                  {food.alternatives.map((alt, j) => (
                    <span key={j} className="text-[9px] text-neon/50 bg-neon/5 px-1.5 py-0.5 rounded">{alt}</span>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {meal.tip && <p className="text-[10px] text-neon/50 mt-2 italic border-t border-outline-variant/5 pt-1.5">💡 {meal.tip}</p>}
    </div>
  )
}
