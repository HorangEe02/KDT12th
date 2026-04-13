import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'

const MODE_IMAGES = {
  mammykim: '/assets/modes/mammykim.png',
  marine: '/assets/modes/marine.png',
}

const MODES = [
  { id: 'coach', emoji: '🏋️', name: '전문 코치' },
  { id: 'friend', emoji: '😄', name: '운동 친구' },
  { id: 'drill', emoji: '🫡', name: '빡센 교관' },
  { id: 'mammykim', emoji: '🥊', name: '매미킴', image: MODE_IMAGES.mammykim },
  { id: 'marine', emoji: '🫡', name: '해병문학', image: MODE_IMAGES.marine },
]

// 모드 아이콘 렌더링 (이미지가 있으면 이미지, 없으면 이모지)
function ModeIcon({ mode, size = 'sm' }) {
  const sizeClass = size === 'lg' ? 'w-8 h-8' : size === 'md' ? 'w-6 h-6' : 'w-5 h-5'
  if (mode.image) {
    return <img src={mode.image} alt={mode.name} className={`${sizeClass} rounded-full object-cover`} onError={e => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'inline' }} />
  }
  return <span className={size === 'lg' ? 'text-lg' : 'text-sm'}>{mode.emoji}</span>
}

const TABS = [
  { id: 'today', label: '오늘의 일기', icon: 'edit_note' },
  { id: 'history', label: '성장 기록', icon: 'timeline' },
  { id: 'goal', label: '목표 달성률', icon: 'flag' },
]

export default function DiaryPage({ profile, selectedModel = 'exaone3.5:7.8b', userId: propUserId }) {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('today')
  const userId = propUserId || user?.user_id || 'default'

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div>
        <span className="badge-neon">운동 일기</span>
        <h2 className="font-headline font-black text-4xl tracking-tighter mt-3">
          오늘의 <span className="italic text-neon">운동 일기</span>
        </h2>
        <p className="section-subtitle">운동 후 느낀 점을 적으면, AI가 감정을 읽고 맞춤 피드백을 해줘요</p>
      </div>

      {/* 탭 */}
      <div className="flex gap-2">
        {TABS.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-full text-xs font-headline font-bold transition-all ${
              activeTab === tab.id ? 'bg-neon/15 text-neon border border-neon/30' : 'text-on-surface-variant border border-outline-variant/20 hover:text-on-surface'}`}>
            <span className="material-symbols-outlined text-[16px]">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'today' && <TodayDiaryTab userId={userId} selectedModel={selectedModel} profile={profile} />}
      {activeTab === 'history' && <GrowthHistoryTab userId={userId} />}
      {activeTab === 'goal' && <GoalProgressTab userId={userId} />}
    </div>
  )
}


// ═══════════════════════════════════════
// 탭 1: 오늘의 일기
// ═══════════════════════════════════════

function TodayDiaryTab({ userId, selectedModel, profile }) {
  const [diaryText, setDiaryText] = useState('')
  const [activeMode, setActiveMode] = useState('coach')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [saved, setSaved] = useState(false)

  const handleAnalyze = async () => {
    if (!diaryText.trim()) return
    setLoading(true); setSaved(false)

    const entry = { date: new Date().toISOString().split('T')[0], text: diaryText, exercises_done: [], duration_min: 50 }

    // 일기 저장
    try {
      await fetch('/api/v1/diary/save', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, text: diaryText, exercises_done: [], duration_min: 50 }),
      })
      setSaved(true)
    } catch {}

    // 감성 분석 + 피드백
    const freq = profile?.nlp_analysis?.exercise_frequency || profile?.exercise_frequency || 3
    try {
      const res = await fetch('/api/v1/feedback/analyze', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ diary_entries: [entry], planned_frequency: freq, mode: activeMode, use_llm: true, model: selectedModel }),
      })
      if (res.ok) { setResult(await res.json()); setLoading(false); return }
    } catch {}
    setResult(generateDemoResult(diaryText, activeMode))
    setLoading(false)
  }

  const sentiment = result?.sentiment_analysis?.entries?.[0]
  const feedback = result?.feedback

  return (
    <div className="grid grid-cols-1 md:grid-cols-5 gap-4 md:gap-6">
      {/* 왼쪽: 일지 입력 */}
      <div className="col-span-1 md:col-span-3 space-y-4">
        <div className="card-elevated">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-neon text-[18px]">edit_note</span>
              <span className="font-headline font-bold text-sm">오늘 운동은 어땠나요?</span>
            </div>
            <span className="text-on-surface-variant text-[10px]">{new Date().toLocaleDateString('ko')}</span>
          </div>
          <textarea value={diaryText} onChange={e => setDiaryText(e.target.value)}
            placeholder="오늘 운동하면서 느낀 점을 편하게 적어주세요. 예: 레그프레스 무게 올렸는데 잘 됐다! / 오늘은 좀 힘들었다..."
            rows={5} className="input-dark resize-none text-sm" />
          <div className="flex items-center justify-between mt-3">
            <span className="text-on-surface-variant text-xs">{saved ? '✅ 일기가 저장되었어요' : ''}</span>
            <button onClick={handleAnalyze} disabled={loading || !diaryText.trim()} className="btn-neon text-xs flex items-center gap-2">
              {loading ? '분석하는 중...' : 'AI한테 피드백 받기'}
            </button>
          </div>
        </div>

        {/* 감성 분석 결과 */}
        {sentiment && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
            <div className="card-elevated text-center">
              <p className="metric-label mb-3">오늘의 기분</p>
              <p className={`font-headline font-black text-3xl ${sentiment.sentiment === '긍정' ? 'text-neon' : sentiment.sentiment === '부정' ? 'text-error' : 'text-on-surface-variant'}`}>
                {sentiment.sentiment === '긍정' ? '기분 좋음 😊' : sentiment.sentiment === '부정' ? '좀 힘들었음 😮‍💨' : '보통이었음 😐'}
              </p>
              <div className="relative w-20 h-20 mx-auto mt-3">
                <svg className="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
                  <circle cx="40" cy="40" r="35" fill="none" stroke="#201f1f" strokeWidth="6" />
                  <circle cx="40" cy="40" r="35" fill="none" stroke={sentiment.sentiment === '긍정' ? '#a2fe00' : sentiment.sentiment === '부정' ? '#ff7351' : '#adaaaa'}
                    strokeWidth="6" strokeDasharray={`${sentiment.confidence * 220} 220`} strokeLinecap="round" />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center font-headline font-bold text-sm">{Math.round(sentiment.confidence * 100)}%</span>
              </div>
              <p className="text-on-surface-variant text-xs mt-2">세부 감정: {sentiment.emotion_detail}</p>
            </div>
            <div className="card-elevated text-center">
              <p className="metric-label mb-3">운동 집중도</p>
              <p className="font-headline font-black text-3xl text-neon">{sentiment.confidence > 0.8 ? '최고 🔥' : sentiment.confidence > 0.5 ? '높음 💪' : '보통 👌'}</p>
              <div className="relative w-20 h-20 mx-auto mt-3">
                <svg className="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
                  <circle cx="40" cy="40" r="35" fill="none" stroke="#201f1f" strokeWidth="6" />
                  <circle cx="40" cy="40" r="35" fill="none" stroke="#3afea0" strokeWidth="6" strokeDasharray={`${(sentiment.confidence > 0.8 ? 94 : 75) / 100 * 220} 220`} strokeLinecap="round" />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center font-headline font-bold text-sm">{sentiment.confidence > 0.8 ? '94' : '75'}%</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 오른쪽: 피드백 모드 + AI */}
      <div className="col-span-2 space-y-4">
        <div className="card-elevated">
          <p className="metric-label mb-3">어떤 스타일로 피드백 받을까요?</p>
          <div className="grid grid-cols-5 gap-1">
            {MODES.map(m => (
              <button key={m.id} onClick={() => setActiveMode(m.id)}
                className={`py-2 rounded-lg text-center transition-all flex flex-col items-center gap-1 ${activeMode === m.id ? 'bg-neon/15 border border-neon/30' : 'hover:bg-surface-container-high'}`}>
                <ModeIcon mode={m} size="lg" />
                <span className="hidden" />
                <span className={`text-[8px] font-headline font-bold ${activeMode === m.id ? 'text-neon' : 'text-on-surface-variant'}`}>{m.name}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="card-elevated bg-surface-container-highest animate-neon-pulse">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded-full bg-neon/20 flex items-center justify-center overflow-hidden">
              <ModeIcon mode={MODES.find(m => m.id === activeMode) || MODES[0]} size="md" />
              <span className="hidden" />
            </div>
            <div>
              <p className="font-headline font-bold text-xs">AI {MODES.find(m => m.id === activeMode)?.name}의 한마디</p>
              <p className="text-[9px] text-on-surface-variant">당신의 일지를 읽고 AI가 작성한 피드백</p>
            </div>
          </div>

          {feedback ? (
            <div className="space-y-3">
              <p className="text-sm text-on-surface leading-relaxed italic">"{feedback.main_message}"</p>
              {feedback.praise_points?.length > 0 && (
                <div><p className="metric-label text-neon mb-1">잘한 점</p>{feedback.praise_points.map((p, i) => <p key={i} className="text-xs text-on-surface-variant">+ {p}</p>)}</div>
              )}
              {feedback.improvement_suggestions?.length > 0 && (
                <div><p className="metric-label text-error/80 mb-1">이렇게 해보면?</p>{feedback.improvement_suggestions.map((s, i) => <p key={i} className="text-xs text-on-surface-variant">→ {s}</p>)}</div>
              )}
              {feedback.encouragement_quote && <p className="text-[11px] text-neon/70 italic border-t border-outline-variant/10 pt-2 mt-2">{feedback.encouragement_quote}</p>}
            </div>
          ) : (
            <p className="text-on-surface-variant text-sm italic">위에 오늘 운동 이야기를 적고 "AI한테 피드백 받기"를 눌러주세요!</p>
          )}
        </div>
      </div>
    </div>
  )
}


// ═══════════════════════════════════════
// 탭 2: 성장 기록
// ═══════════════════════════════════════

function GrowthHistoryTab({ userId }) {
  const [diaries, setDiaries] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`/api/v1/diary/${userId}/history`)
        if (res.ok) { const d = await res.json(); setDiaries(d.entries || []) }
      } catch {}
      setLoading(false)
    })()
  }, [userId])

  if (loading) return <div className="card-surface text-center py-12"><span className="animate-pulse text-on-surface-variant">불러오는 중...</span></div>

  if (diaries.length === 0) {
    return (
      <div className="card-surface text-center py-16">
        <span className="text-3xl md:text-5xl block mb-4">📝</span>
        <p className="font-headline font-bold text-lg">아직 운동 일기가 없어요</p>
        <p className="text-on-surface-variant text-sm mt-2">"오늘의 일기" 탭에서 첫 일기를 작성해보세요!</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="card-elevated flex items-center justify-between">
        <div>
          <p className="font-headline font-bold text-lg">📚 나의 성장 일지</p>
          <p className="text-on-surface-variant text-xs">지금까지 {diaries.length}개의 운동 일기를 작성했어요</p>
        </div>
        <div className="text-right">
          <p className="font-headline font-black text-3xl text-neon">{diaries.length}</p>
          <p className="metric-label">총 기록</p>
        </div>
      </div>

      {/* 일기 목록 (최신순) */}
      <div className="space-y-2">
        {[...diaries].reverse().map((entry, i) => (
          <div key={i} className="card-elevated">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-neon text-sm">📝</span>
                <span className="font-headline font-bold text-xs">{entry.date}</span>
              </div>
              <div className="flex items-center gap-3 text-[10px] text-on-surface-variant">
                {entry.duration_min > 0 && <span>⏱ {entry.duration_min}분</span>}
                {entry.exercises_done?.length > 0 && <span>🏋️ {entry.exercises_done.length}종목</span>}
              </div>
            </div>
            <p className="text-sm text-on-surface">{entry.text}</p>
            {entry.exercises_done?.length > 0 && (
              <div className="flex gap-1.5 mt-2 flex-wrap">
                {entry.exercises_done.map((ex, j) => <span key={j} className="badge-neon text-[9px]">{ex}</span>)}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}


// ═══════════════════════════════════════
// 탭 3: 목표 달성률
// ═══════════════════════════════════════

function GoalProgressTab({ userId }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`/api/v1/diary/${userId}/growth`)
        if (res.ok) setData(await res.json())
      } catch {}
      setLoading(false)
    })()
  }, [userId])

  if (loading) return <div className="card-surface text-center py-12"><span className="animate-pulse text-on-surface-variant">분석하는 중...</span></div>

  if (!data || data.total_sessions === 0) {
    return (
      <div className="card-surface text-center py-16">
        <span className="text-3xl md:text-5xl block mb-4">🎯</span>
        <p className="font-headline font-bold text-lg">아직 데이터가 부족해요</p>
        <p className="text-on-surface-variant text-sm mt-2">운동 일기를 작성하면 목표 달성률을 분석해드려요!</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* 목표 메시지 */}
      <div className="card-elevated bg-neon/5">
        <p className="font-headline font-bold text-lg text-neon">{data.goal_message}</p>
        <p className="text-on-surface-variant text-xs mt-1">목표: {data.goal_type} | 주 {data.target_frequency}회 운동</p>
      </div>

      {/* 요약 카드 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="card-elevated text-center">
          <p className="metric-label">총 운동 횟수</p>
          <p className="font-headline font-black text-3xl text-neon">{data.total_sessions}</p>
          <p className="text-[10px] text-on-surface-variant">회</p>
        </div>
        <div className="card-elevated text-center">
          <p className="metric-label">총 운동 시간</p>
          <p className="font-headline font-black text-3xl">{data.total_minutes}</p>
          <p className="text-[10px] text-on-surface-variant">분</p>
        </div>
        <div className="card-elevated text-center">
          <p className="metric-label">평균 달성률</p>
          <p className={`font-headline font-black text-3xl ${data.avg_weekly_completion_rate >= 80 ? 'text-neon' : data.avg_weekly_completion_rate >= 50 ? 'text-tertiary' : 'text-error'}`}>
            {data.avg_weekly_completion_rate}%
          </p>
        </div>
        <div className="card-elevated text-center">
          <p className="metric-label">연속 운동</p>
          <p className="font-headline font-black text-3xl text-neon">{data.streak?.current || 0}</p>
          <p className="text-[10px] text-on-surface-variant">일 (최고 {data.streak?.best || 0}일)</p>
        </div>
      </div>

      {/* 주별 달성률 */}
      {data.weekly_stats?.length > 0 && (
        <div className="card-elevated">
          <p className="metric-label mb-3">📊 주별 달성률</p>
          <div className="space-y-2">
            {data.weekly_stats.slice(-8).map((w, i) => (
              <div key={i} className="flex items-center gap-3">
                <span className="text-[10px] text-on-surface-variant w-16">{w.week}</span>
                <div className="flex-1 progress-track">
                  <div className="progress-fill" style={{ width: `${w.completion_rate}%` }} />
                </div>
                <span className={`text-xs font-headline font-bold w-12 text-right ${w.completion_rate >= 80 ? 'text-neon' : w.completion_rate >= 50 ? 'text-on-surface' : 'text-error'}`}>
                  {w.sessions}/{w.target}
                </span>
                <span className="text-[10px] text-on-surface-variant w-10 text-right">{w.completion_rate}%</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 인바디 기록 */}
      {data.inbody_count > 0 && (
        <div className="card-surface">
          <p className="text-xs text-on-surface-variant">{"📊 인바디 측정: " + data.inbody_count + "회 — '내 몸 알기 → 내 프로필 보기'에서 변화를 확인하세요"}</p>
        </div>
      )}
    </div>
  )
}


function generateDemoResult(text, mode) {
  const isPositive = /잘 됐|성공|올렸|재밌|좋|뿌듯|대단|개운|상쾌|오운완|해냈|신기록/.test(text)
  const isNegative = /피곤|힘들|못|아프|의욕|포기|실패|지쳤|귀찮|통증|스트레스/.test(text)
  const sentiment = isPositive ? '긍정' : isNegative ? '부정' : '중립'
  const emotion = isPositive ? '성취감' : isNegative ? '피로' : '일상'

  // 감성별 × 모드별 메시지 (긍정/부정/중립 각각 다르게)
  const messageMap = {
    coach: {
      positive: '이번 운동 수행이 우수했습니다. 점진적 과부하 원칙에 따라 다음에 강도를 올려보세요.',
      negative: '컨디션이 좋지 않았군요. 수면과 영양을 점검하고, 다음에는 강도를 낮춰 진행하세요.',
      neutral: '오늘도 꾸준히 기록하고 있습니다. 매일의 기록이 쌓여 큰 변화를 만듭니다.',
    },
    friend: {
      positive: '야 오늘 진짜 잘했다ㅋㅋ 대박!! 💪🔥',
      negative: '에이 괜찮아~ 그런 날도 있는 거야! 다음에 같이 가자! 😊',
      neutral: '오 꾸준히 하고 있네~ 이 페이스 좋은데? ㅎㅎ',
    },
    drill: {
      positive: '좋았다! 그 투지를 잃지 마라! 방심은 금물이다!',
      negative: '이게 최선이냐?! ...그래도 포기 안 한 건 인정한다. 내일 다시 온다!',
      neutral: '절반은 했다. 나쁘지 않다. 하지만 넌 더 할 수 있다!',
    },
    mammykim: {
      positive: '오 운동 많이 된다. 굿 파트너. 진짜 도움 많이 되고 있어. 대화가 된다.',
      negative: '괜찮아. 스트레스 받은 것도 운동이야. 자기 전에 생각 많이 날 거야. 내일 와. 운동 많이 될 거야.',
      neutral: '왔으면 운동 된다. 꾸준히 하고 있네. 대화가 된다.',
    },
    marine: {
      positive: '필승! 이 잔망스러운 근성장을 보십시오! 귀신잡는 해병대 정신! 아쎄이!',
      negative: '필승! 이 달콤쌉싸름한 피로감... 하지만 해병에게 포기란 없습니다! 앙증맞은 운동화를 다시 신으십시오!',
      neutral: '필승! 이 앙증맞은 출석을 보고합니다. 귀신잡는 해병대는 매일 전진합니다!',
    },
  }

  const sentimentKey = isPositive ? 'positive' : isNegative ? 'negative' : 'neutral'
  const modeMessages = messageMap[mode] || messageMap.coach
  const mainMessage = modeMessages[sentimentKey]

  const quotes = {
    coach: '꾸준함은 재능을 이긴다.', friend: '같이 가면 멀리 간다! 💪', drill: '고통은 일시적. 포기는 영원!',
    mammykim: '운동 많이 된다. 굿 파트너. 🥊', marine: '필승! 해병은 포기하지 않는다! 🫡',
  }
  return {
    sentiment_analysis: { entries: [{ date: new Date().toISOString().split('T')[0], text, sentiment, confidence: isPositive ? 0.85 : isNegative ? 0.92 : 0.6, emotion_detail: emotion }], weekly_sentiment: { positive_count: isPositive ? 1 : 0, negative_count: isNegative ? 1 : 0, neutral_count: sentiment === '중립' ? 1 : 0, trend: '유지', dominant_sentiment: sentiment } },
    weekly_summary: { text: `이번 주 1회 운동.`, total_sessions: 1, planned_sessions: 3, highlights: isPositive ? ['기록 갱신'] : [] },
    feedback: { main_message: mainMessage, praise_points: isPositive ? ['운동 수행 완료'] : ['운동에 참여한 의지 확인'], improvement_suggestions: isNegative ? ['수면과 영양 섭취를 점검해보세요'] : [], encouragement_quote: quotes[mode] || quotes.coach, mode, mode_name: MODES.find(m => m.id === mode)?.name || mode, mode_emoji: MODES.find(m => m.id === mode)?.emoji || '🏋️' },
  }
}
