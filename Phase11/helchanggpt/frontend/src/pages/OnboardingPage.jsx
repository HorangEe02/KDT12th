import { useState, useEffect, useRef } from 'react'
import ModelSelector from '../components/ModelSelector'

const TABS = [
  { id: 'form', label: '직접 입력하기', shortLabel: '입력', icon: 'edit_square' },
  { id: 'inbody', label: '인바디 정보 올리기', shortLabel: '인바디', icon: 'upload_file' },
  { id: 'chat', label: 'AI와 대화하기', shortLabel: 'AI', icon: 'chat' },
  { id: 'profile', label: '내 프로필 보기', shortLabel: '프로필', icon: 'person' },
]

const GOAL_OPTIONS = [
  { value: '체지방감소', label: '살 빼기 (체지방 감소)', emoji: '🔥' },
  { value: '근력증가', label: '근육 키우기 (근력 증가)', emoji: '💪' },
  { value: '체력향상', label: '체력 올리기 (스태미나)', emoji: '🏃' },
  { value: '체중관리', label: '현재 몸매 유지', emoji: '⚖️' },
  { value: '건강개선', label: '건강 관리 (질환 등)', emoji: '❤️' },
]
const CONSTRAINT_OPTIONS = ['무릎 부상', '허리 부상', '어깨 부상', '당뇨', '고혈압', '고지혈증', '심장질환']
const LEVEL_OPTIONS = ['입문 (운동 처음)', '초급 (가끔 운동)', '중급 (꾸준히 운동)', '고급 (전문가 수준)']

export default function OnboardingPage({ profile, setProfile, selectedModel = 'gemma4:e4b', userId = 'default' }) {
  const [activeTab, setActiveTab] = useState('form')

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div>
        <span className="badge-neon">내 몸 알기</span>
        <h2 className="font-headline font-black text-4xl tracking-tighter mt-3">
          나에 대해 <span className="italic text-neon">알려주세요</span>
        </h2>
        <p className="section-subtitle">4가지 방법으로 내 정보를 입력하고, AI 맞춤 분석을 받아보세요</p>
      </div>

      {/* 탭 선택 */}
      <div className="flex gap-2">
        {TABS.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-1.5 md:gap-2 px-3 md:px-4 py-2.5 rounded-full text-xs font-headline font-bold transition-all whitespace-nowrap ${
              activeTab === tab.id ? 'bg-neon/15 text-neon border border-neon/30' : 'text-on-surface-variant border border-outline-variant/20 hover:text-on-surface'}`}>
            <span className="material-symbols-outlined text-[16px]">{tab.icon}</span>
            <span className="md:hidden">{tab.shortLabel}</span>
            <span className="hidden md:inline">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* 탭 내용 */}
      {activeTab === 'form' && <FormInputTab userId={userId} setProfile={setProfile} />}
      {activeTab === 'inbody' && <InBodyUploadTab userId={userId} selectedModel={selectedModel} setProfile={setProfile} />}
      {activeTab === 'chat' && <ChatTab userId={userId} selectedModel={selectedModel} setProfile={setProfile} />}
      {activeTab === 'profile' && <ProfileViewTab userId={userId} profile={profile} />}
    </div>
  )
}


// ═══════════════════════════════════════
// 탭 1: 직접 입력하기 (양식 폼)
// ═══════════════════════════════════════

function FormInputTab({ userId, setProfile }) {
  const [form, setForm] = useState({ name: '', age: '', gender: '남성', height_cm: '', weight_kg: '', body_fat_percent: '', goal_type: '체지방감소', exercise_frequency: '3', experience_level: '입문 (운동 처음)', constraints: [] })
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const update = (key, val) => setForm(prev => ({ ...prev, [key]: val }))
  const toggleConstraint = (c) => setForm(prev => ({
    ...prev, constraints: prev.constraints.includes(c) ? prev.constraints.filter(x => x !== c) : [...prev.constraints, c]
  }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.age || !form.height_cm || !form.weight_kg) return
    setLoading(true)
    const payload = {
      user_id: userId, name: form.name, age: parseInt(form.age), gender: form.gender,
      height_cm: parseFloat(form.height_cm), weight_kg: parseFloat(form.weight_kg),
      body_fat_percent: form.body_fat_percent ? parseFloat(form.body_fat_percent) : null,
      goal_type: form.goal_type, exercise_frequency: parseInt(form.exercise_frequency),
      experience_level: form.experience_level.split(' (')[0],
      constraints: form.constraints,
    }

    try {
      const res = await fetch('/api/v1/profile/save', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
      if (res.ok) {
        // 계산된 지표도 가져오기
        const calcRes = await fetch('/api/v1/profile/calculate-metrics', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ weight_kg: payload.weight_kg, height_cm: payload.height_cm, age: payload.age, gender: payload.gender, exercise_frequency: payload.exercise_frequency, goal_type: payload.goal_type }),
        })
        const calc = calcRes.ok ? await calcRes.json() : {}
        setResult(calc)
        setProfile({ basic: payload, calculated: calc, nlp_analysis: { goal_type: payload.goal_type, constraints: payload.constraints, experience_level: payload.experience_level, exercise_frequency: payload.exercise_frequency }, health_risk_flags: { warnings: [] }, profile_confidence: { score: 80, level: '높음' }, meta: { input_type: 'form' } })
      }
    } catch { setResult({ bmi: Math.round(parseFloat(form.weight_kg) / (parseFloat(form.height_cm)/100)**2 * 10)/10 }) }
    setLoading(false)
  }

  return (
    <form onSubmit={handleSubmit} className="card-surface space-y-5">
      <p className="font-headline font-bold text-sm text-on-surface-variant">기본 정보를 입력하면 AI가 맞춤 분석을 해드려요</p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 md:gap-4">
        <div><label className="metric-label block mb-1">이름 (선택)</label><input value={form.name} onChange={e => update('name', e.target.value)} placeholder="홍길동" className="input-dark py-2 text-sm" /></div>
        <div><label className="metric-label block mb-1">나이 *</label><input type="number" value={form.age} onChange={e => update('age', e.target.value)} placeholder="25" className="input-dark py-2 text-sm" required /></div>
        <div><label className="metric-label block mb-1">성별 *</label>
          <div className="flex gap-2">{['남성', '여성'].map(g => (
            <button key={g} type="button" onClick={() => update('gender', g)}
              className={`flex-1 py-2 rounded-xl text-xs font-headline font-bold transition-all ${form.gender === g ? 'bg-neon/15 text-neon border border-neon/30' : 'bg-surface-container text-on-surface-variant border border-transparent'}`}>{g}</button>
          ))}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 md:gap-4">
        <div><label className="metric-label block mb-1">키 (cm) *</label><input type="number" step="0.1" value={form.height_cm} onChange={e => update('height_cm', e.target.value)} placeholder="178.0" className="input-dark py-2 text-sm" required /></div>
        <div><label className="metric-label block mb-1">몸무게 (kg) *</label><input type="number" step="0.1" value={form.weight_kg} onChange={e => update('weight_kg', e.target.value)} placeholder="82.0" className="input-dark py-2 text-sm" required /></div>
        <div><label className="metric-label block mb-1">체지방률 % (선택)</label><input type="number" step="0.1" value={form.body_fat_percent} onChange={e => update('body_fat_percent', e.target.value)} placeholder="22.0" className="input-dark py-2 text-sm" /></div>
      </div>

      {/* 운동 목표 */}
      <div>
        <label className="metric-label block mb-2">운동 목표 *</label>
        <div className="grid grid-cols-5 gap-2">{GOAL_OPTIONS.map(g => (
          <button key={g.value} type="button" onClick={() => update('goal_type', g.value)}
            className={`py-3 rounded-xl text-center transition-all ${form.goal_type === g.value ? 'bg-neon/15 border border-neon/30' : 'bg-surface-container border border-transparent hover:bg-surface-container-high'}`}>
            <span className="text-xl block">{g.emoji}</span>
            <span className={`text-[10px] font-headline font-bold ${form.goal_type === g.value ? 'text-neon' : 'text-on-surface-variant'}`}>{g.label.split(' (')[0]}</span>
          </button>
        ))}</div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
        <div><label className="metric-label block mb-1">주당 운동 가능 횟수</label>
          <select value={form.exercise_frequency} onChange={e => update('exercise_frequency', e.target.value)} className="input-dark py-2 text-sm">
            {[1,2,3,4,5,6,7].map(n => <option key={n} value={n}>주 {n}회</option>)}
          </select>
        </div>
        <div><label className="metric-label block mb-1">운동 경험</label>
          <select value={form.experience_level} onChange={e => update('experience_level', e.target.value)} className="input-dark py-2 text-sm">
            {LEVEL_OPTIONS.map(l => <option key={l} value={l}>{l}</option>)}
          </select>
        </div>
      </div>

      {/* 제약사항 */}
      <div>
        <label className="metric-label block mb-2">제약사항 / 부상 (해당 항목 선택)</label>
        <div className="flex gap-2 flex-wrap">{CONSTRAINT_OPTIONS.map(c => (
          <button key={c} type="button" onClick={() => toggleConstraint(c)}
            className={`px-3 py-1.5 rounded-full text-xs font-headline font-bold transition-all ${
              form.constraints.includes(c) ? 'bg-error/15 text-error border border-error/30' : 'bg-surface-container text-on-surface-variant border border-transparent hover:bg-surface-container-high'}`}>
            {c}
          </button>
        ))}</div>
      </div>

      <div className="flex items-center justify-between pt-2">
        <span className="text-on-surface-variant text-xs">* 필수 입력 항목</span>
        <button type="submit" disabled={loading || !form.age || !form.height_cm || !form.weight_kg} className="btn-neon flex items-center gap-2">
          {loading ? '분석 중...' : <><span className="material-symbols-outlined text-[16px]">neurology</span> 내 몸 분석하기</>}
        </button>
      </div>

      {/* 분석 결과 */}
      {result && (
        <div className="bg-neon/5 rounded-xl p-5 space-y-3">
          <p className="font-headline font-bold text-sm text-neon">✅ 분석 완료!</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
            <MetricBox label="BMI (비만도)" value={result.bmi} status={result.bmi_category} />
            <MetricBox label="기초대사량" value={result.bmr_kcal} unit="kcal" />
            <MetricBox label="하루 소모량" value={result.tdee_kcal} unit="kcal" />
            <MetricBox label="권장 섭취량" value={result.recommended_intake_kcal} unit="kcal" highlight />
          </div>
        </div>
      )}
    </form>
  )
}


// ═══════════════════════════════════════
// 탭 2: 인바디 정보 올리기
// ═══════════════════════════════════════

function InBodyUploadTab({ userId, selectedModel, setProfile }) {
  const [files, setFiles] = useState([])
  const [previews, setPreviews] = useState([])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  const handleFiles = (newFiles) => {
    const allowed = ['png','jpg','jpeg','csv','xlsx','xls','pdf','docx']
    const valid = Array.from(newFiles).filter(f => allowed.includes(f.name.split('.').pop().toLowerCase()))
    if (valid.length === 0) { setError('지원하지 않는 파일이에요 (PNG, JPG, CSV, PDF, XLSX 지원)'); return }
    setFiles(valid)
    setError('')
    // 이미지 미리보기
    const pvs = valid.map(f => f.type.startsWith('image/') ? URL.createObjectURL(f) : null)
    setPreviews(pvs)
  }

  // 이미지 파일 여부 확인
  const hasImageFile = files.some(f => f.type.startsWith('image/'))

  const handleUpload = async () => {
    if (files.length === 0) return
    setLoading(true); setError(''); setResult(null)

    // 이미지 파일이면 비전 모델(gemma4:e4b)로 자동 전환
    const uploadModel = hasImageFile ? 'gemma4:e4b' : selectedModel

    const formData = new FormData()
    formData.append('file', files[0])
    formData.append('user_id', userId)
    formData.append('model', uploadModel)

    try {
      const res = await fetch('/api/v1/inbody/upload', { method: 'POST', body: formData })
      if (res.ok) { const data = await res.json(); setResult(data); setLoading(false); return }
      const err = await res.json(); setError(err.detail || '분석 실패')
    } catch { setError('서버에 연결할 수 없어요. 백엔드가 실행 중인지 확인해주세요.') }
    setLoading(false)
  }

  return (
    <div className="card-surface space-y-4">
      <p className="font-headline font-bold text-sm text-on-surface-variant">인바디 결과지 사진이나 파일을 올리면 AI가 자동으로 읽고 분석해드려요</p>

      {/* 파일 타입별 안내 */}
      {hasImageFile && (
        <div className="flex items-start gap-2.5 bg-neon/10 rounded-xl px-4 py-3">
          <span className="material-symbols-outlined text-neon text-lg mt-0.5">auto_awesome</span>
          <div>
            <p className="text-neon font-headline font-bold text-xs">비전 모델(Gemma 4)로 자동 전환됩니다</p>
            <p className="text-on-surface-variant text-[10px] mt-0.5">이미지 파일은 비전 AI가 필요해서 분석 시 자동으로 Gemma 4 E4B 모델을 사용합니다. CSV/PDF/Excel 파일은 선택한 모델 그대로 분석돼요.</p>
          </div>
        </div>
      )}

      {/* 드래그앤드롭 */}
      <div
        onDragOver={e => { e.preventDefault(); e.currentTarget.classList.add('border-neon/60') }}
        onDragLeave={e => e.currentTarget.classList.remove('border-neon/60')}
        onDrop={e => { e.preventDefault(); e.currentTarget.classList.remove('border-neon/60'); handleFiles(e.dataTransfer.files) }}
        onClick={() => document.getElementById('inbody-input').click()}
        className="border-2 border-dashed border-outline-variant/30 hover:border-neon/40 rounded-xl p-8 text-center cursor-pointer transition-colors"
      >
        <input id="inbody-input" type="file" multiple accept=".png,.jpg,.jpeg,.csv,.xlsx,.xls,.pdf,.docx" className="hidden" onChange={e => handleFiles(e.target.files)} />

        {files.length > 0 ? (
          <div className="flex gap-3 justify-center flex-wrap">
            {files.map((f, i) => (
              <div key={i} className="text-center">
                {previews[i] ? <img src={previews[i]} alt="" className="w-32 h-32 object-cover rounded-lg shadow-neon-glow" /> :
                  <div className="w-32 h-32 bg-surface-container rounded-lg flex flex-col items-center justify-center">
                    <span className="material-symbols-outlined text-3xl text-neon">description</span>
                    <span className="text-[10px] text-on-surface-variant mt-1">{f.name.split('.').pop().toUpperCase()}</span>
                  </div>}
                <p className="text-[10px] text-on-surface-variant mt-1 truncate max-w-[8rem]">{f.name}</p>
              </div>
            ))}
          </div>
        ) : (
          <>
            <span className="material-symbols-outlined text-3xl md:text-5xl text-on-surface-variant/40">cloud_upload</span>
            <p className="text-on-surface-variant mt-2 font-headline font-bold text-sm">인바디 결과지를 끌어놓거나 클릭해서 올려주세요</p>
            <p className="text-on-surface-variant/50 text-xs mt-1">사진(PNG, JPG), PDF, 엑셀(XLSX), CSV 파일 가능</p>
          </>
        )}
      </div>

      {/* 업로드 버튼 */}
      {files.length > 0 && (
        <div className="flex items-center justify-between">
          <p className="text-xs text-on-surface-variant">분석 AI: <span className="text-neon font-bold">{selectedModel}</span> ({files.length}개 파일)</p>
          <button onClick={handleUpload} disabled={loading} className="btn-neon flex items-center gap-2">
            {loading ? <><span className="animate-spin">⏳</span> AI가 읽는 중...</> : <><span className="material-symbols-outlined text-[16px]">neurology</span> 인바디 분석 시작</>}
          </button>
        </div>
      )}

      {error && <div className="bg-error/10 text-error text-xs rounded-lg p-3 text-center">{error}</div>}

      {/* 분석 결과 + 코칭 */}
      {result && (
        <div className="space-y-4">
          <div className="bg-neon/5 rounded-xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-neon text-lg">✅</span>
              <span className="font-headline font-bold text-sm text-neon">인바디 분석 완료!</span>
              <span className="text-[10px] text-on-surface-variant">({result.parse_method}) 신뢰도 {Math.round((result.parse_confidence||0)*100)}%</span>
            </div>
            {result.analysis && (
              <>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                  <MetricBox label="체형" value={result.analysis.body_shape} />
                  <MetricBox label="종합 등급" value={result.analysis.overall_grade} highlight />
                  <MetricBox label="인바디 점수" value={result.analysis.inbody_score} unit="/100" />
                  <MetricBox label="내장지방" value={result.analysis.visceral_fat_risk} />
                </div>

                {/* 코칭 메시지 */}
                {result.analysis.praise_points?.length > 0 && (
                  <div className="mb-3">
                    <p className="metric-label text-neon mb-1">🏆 잘하고 있어요!</p>
                    {result.analysis.praise_points.map((p, i) => <p key={i} className="text-xs text-on-surface-variant">+ {p}</p>)}
                  </div>
                )}
                {result.analysis.improvement_points?.length > 0 && (
                  <div className="mb-3">
                    <p className="metric-label text-error/80 mb-1">💡 이렇게 해보면 어떨까요?</p>
                    {result.analysis.improvement_points.map((p, i) => <p key={i} className="text-xs text-on-surface-variant">→ {p}</p>)}
                  </div>
                )}
                {result.analysis.action_items?.length > 0 && (
                  <div>
                    <p className="metric-label mb-1">📋 추천 행동</p>
                    {result.analysis.action_items.map((a, i) => <p key={i} className="text-xs text-on-surface-variant">✓ {a}</p>)}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}


// ═══════════════════════════════════════
// 탭 3: AI와 대화하기
// ═══════════════════════════════════════

function ChatTab({ userId, selectedModel, setProfile }) {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: '안녕하세요! 저는 헬창지피티 AI 코치예요 🏋️\n\n편하게 대화하면서 신체 정보를 알려주시면 제가 기록하고 분석해드릴게요.\n\n예를 들어:\n• "25살 남자, 178cm 82kg이야"\n• "살 좀 빼고 싶어"\n• "무릎이 안 좋아서 달리기는 못해"' }
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
      const res = await fetch('/api/v1/chat', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, message: userMsg, model: selectedModel }),
      })
      const data = await res.json()

      let reply = data.reply || '응답을 받지 못했어요. 다시 시도해주세요.'
      if (data.profile_update) {
        const updated = Object.entries(data.profile_update).map(([k, v]) => `${k}: ${v}`).join(', ')
        reply += `\n\n📝 프로필 업데이트: ${updated}`
      }
      setMessages(prev => [...prev, { role: 'assistant', text: reply, profileUpdate: data.profile_update }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', text: '서버에 연결할 수 없어요. Ollama와 백엔드가 실행 중인지 확인해주세요.' }])
    }
    setLoading(false)
  }

  return (
    <div className="card-surface flex flex-col" style={{ height: '600px' }}>
      {/* 채팅 메시지 */}
      <div className="flex-1 overflow-y-auto space-y-3 p-2 mb-3">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[70%] rounded-2xl px-4 py-3 ${
              msg.role === 'user' ? 'bg-neon/15 text-on-surface' : 'bg-surface-container-high text-on-surface'}`}>
              {msg.role === 'assistant' && (
                <div className="flex items-center gap-1.5 mb-1">
                  <span className="text-neon text-xs">🤖</span>
                  <span className="text-[10px] font-headline font-bold text-neon">AI 코치</span>
                </div>
              )}
              <p className="text-sm whitespace-pre-wrap">{msg.text}</p>
              {msg.profileUpdate && (
                <div className="mt-2 bg-neon/10 rounded-lg px-2 py-1">
                  <span className="text-[10px] text-neon font-bold">✅ 프로필에 반영됨</span>
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-surface-container-high rounded-2xl px-4 py-3">
              <span className="text-on-surface-variant text-sm animate-pulse">AI가 생각하는 중...</span>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* 입력창 */}
      <div className="flex gap-2 border-t border-outline-variant/10 pt-3">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
          placeholder="AI 코치에게 말해보세요... (예: 25살 남자 178cm 82kg)"
          className="input-dark flex-1 py-2.5 text-sm"
          disabled={loading}
        />
        <button onClick={sendMessage} disabled={loading || !input.trim()} className="btn-neon px-4">
          <span className="material-symbols-outlined text-[18px]">send</span>
        </button>
      </div>
      <p className="text-[10px] text-on-surface-variant/40 text-center mt-1">대화 중 입력된 신체 정보는 자동으로 프로필에 반영돼요 | 모델: {selectedModel}</p>
    </div>
  )
}


// ═══════════════════════════════════════
// 탭 4: 내 프로필 보기
// ═══════════════════════════════════════

function ProfileViewTab({ userId, profile: parentProfile }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [editForm, setEditForm] = useState({})
  const [saveMsg, setSaveMsg] = useState('')

  useEffect(() => { fetchProfile() }, [userId])

  const fetchProfile = async () => {
    try {
      const res = await fetch(`/api/v1/profile/${userId}`)
      if (res.ok) { setData(await res.json()); setLoading(false); return }
    } catch {}
    if (parentProfile) {
      setData({ profile: parentProfile.basic || {}, calculated: parentProfile.calculated || {}, inbody_history: [], has_data: true, nickname: '' })
    } else {
      setData({ profile: {}, calculated: {}, inbody_history: [], has_data: false })
    }
    setLoading(false)
  }

  const startEdit = () => {
    const p = data?.profile || {}
    setEditForm({
      name: p.name || '', age: p.age || '', gender: p.gender || '남성',
      height_cm: p.height_cm || '', weight_kg: p.weight_kg || '',
      body_fat_percent: p.body_fat_percent || '',
      goal_type: p.goal_type || '체중관리',
      exercise_frequency: p.exercise_frequency || 3,
      experience_level: p.experience_level || '입문',
      constraints: p.constraints || [],
    })
    setEditing(true)
    setSaveMsg('')
  }

  const saveEdit = async () => {
    setSaveMsg('')
    const payload = {
      user_id: userId,
      name: editForm.name || null,
      age: editForm.age ? parseInt(editForm.age) : null,
      gender: editForm.gender,
      height_cm: editForm.height_cm ? parseFloat(editForm.height_cm) : null,
      weight_kg: editForm.weight_kg ? parseFloat(editForm.weight_kg) : null,
      body_fat_percent: editForm.body_fat_percent ? parseFloat(editForm.body_fat_percent) : null,
      goal_type: editForm.goal_type,
      exercise_frequency: parseInt(editForm.exercise_frequency) || 3,
      experience_level: editForm.experience_level,
      constraints: editForm.constraints,
    }
    try {
      const res = await fetch('/api/v1/profile/save', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
      if (res.ok) { setSaveMsg('✅ 저장되었습니다!'); setEditing(false); fetchProfile(); return }
    } catch {}
    setSaveMsg('저장에 실패했어요')
  }

  const toggleConstraint = (c) => setEditForm(prev => ({
    ...prev, constraints: prev.constraints.includes(c) ? prev.constraints.filter(x => x !== c) : [...prev.constraints, c]
  }))

  if (loading) return <div className="card-surface text-center py-12"><span className="animate-pulse text-on-surface-variant">불러오는 중...</span></div>

  if (!data?.has_data && !editing) {
    return (
      <div className="card-surface text-center py-16">
        <span className="text-3xl md:text-5xl block mb-4">📋</span>
        <p className="font-headline font-bold text-lg text-on-surface">아직 입력된 정보가 없어요</p>
        <p className="text-on-surface-variant text-sm mt-2 mb-4">"직접 입력하기" 또는 "AI와 대화하기"로 정보를 입력해주세요</p>
        <button onClick={startEdit} className="btn-neon text-xs mx-auto flex items-center gap-1">
          <span className="material-symbols-outlined text-[14px]">edit</span> 여기서 바로 입력하기
        </button>
      </div>
    )
  }

  const p = data?.profile || {}
  const c = data?.calculated || {}

  // ── 편집 모드 ──
  if (editing) {
    return (
      <div className="card-elevated space-y-4">
        <div className="flex items-center justify-between">
          <p className="font-headline font-bold text-lg">✏️ 내 정보 수정</p>
          <button onClick={() => setEditing(false)} className="text-on-surface-variant text-xs hover:text-error">취소</button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div><label className="metric-label block mb-1">이름</label><input value={editForm.name} onChange={e => setEditForm({...editForm, name: e.target.value})} className="input-dark py-2 text-sm" placeholder="홍길동" /></div>
          <div><label className="metric-label block mb-1">나이</label><input type="number" value={editForm.age} onChange={e => setEditForm({...editForm, age: e.target.value})} className="input-dark py-2 text-sm" /></div>
          <div><label className="metric-label block mb-1">성별</label>
            <div className="flex gap-2">{['남성','여성'].map(g => (
              <button key={g} type="button" onClick={() => setEditForm({...editForm, gender: g})}
                className={`flex-1 py-2 rounded-xl text-xs font-headline font-bold transition-all ${editForm.gender === g ? 'bg-neon/15 text-neon border border-neon/30' : 'bg-surface-container text-on-surface-variant border border-transparent'}`}>{g}</button>
            ))}</div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div><label className="metric-label block mb-1">키 (cm)</label><input type="number" step="0.1" value={editForm.height_cm} onChange={e => setEditForm({...editForm, height_cm: e.target.value})} className="input-dark py-2 text-sm" /></div>
          <div><label className="metric-label block mb-1">몸무게 (kg)</label><input type="number" step="0.1" value={editForm.weight_kg} onChange={e => setEditForm({...editForm, weight_kg: e.target.value})} className="input-dark py-2 text-sm" /></div>
          <div><label className="metric-label block mb-1">체지방률 (%)</label><input type="number" step="0.1" value={editForm.body_fat_percent} onChange={e => setEditForm({...editForm, body_fat_percent: e.target.value})} className="input-dark py-2 text-sm" /></div>
        </div>

        <div><label className="metric-label block mb-1">운동 목표</label>
          <div className="grid grid-cols-5 gap-2">{GOAL_OPTIONS.map(g => (
            <button key={g.value} type="button" onClick={() => setEditForm({...editForm, goal_type: g.value})}
              className={`py-2 rounded-xl text-center text-[10px] font-headline font-bold transition-all ${editForm.goal_type === g.value ? 'bg-neon/15 text-neon border border-neon/30' : 'bg-surface-container text-on-surface-variant border border-transparent'}`}>
              <span className="block text-lg">{g.emoji}</span>{g.label.split(' (')[0]}
            </button>
          ))}</div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div><label className="metric-label block mb-1">주당 운동 횟수</label>
            <select value={editForm.exercise_frequency} onChange={e => setEditForm({...editForm, exercise_frequency: e.target.value})} className="input-dark py-2 text-sm">
              {[1,2,3,4,5,6,7].map(n => <option key={n} value={n}>주 {n}회</option>)}
            </select>
          </div>
          <div><label className="metric-label block mb-1">운동 경험</label>
            <select value={editForm.experience_level} onChange={e => setEditForm({...editForm, experience_level: e.target.value})} className="input-dark py-2 text-sm">
              {LEVEL_OPTIONS.map(l => <option key={l} value={l.split(' (')[0]}>{l}</option>)}
            </select>
          </div>
        </div>

        <div><label className="metric-label block mb-2">제약사항 / 부상</label>
          <div className="flex gap-2 flex-wrap">{CONSTRAINT_OPTIONS.map(ct => (
            <button key={ct} type="button" onClick={() => toggleConstraint(ct)}
              className={`px-3 py-1.5 rounded-full text-xs font-headline font-bold transition-all ${editForm.constraints.includes(ct) ? 'bg-error/15 text-error border border-error/30' : 'bg-surface-container text-on-surface-variant border border-transparent'}`}>{ct}</button>
          ))}</div>
        </div>

        {saveMsg && <p className={`text-xs text-center ${saveMsg.includes('✅') ? 'text-neon' : 'text-error'}`}>{saveMsg}</p>}

        <div className="flex justify-end gap-2">
          <button onClick={() => setEditing(false)} className="btn-ghost text-xs">취소</button>
          <button onClick={saveEdit} className="btn-neon text-xs flex items-center gap-1"><span className="material-symbols-outlined text-[14px]">save</span> 저장하기</button>
        </div>
      </div>
    )
  }

  // ── 보기 모드 ──
  return (
    <div className="space-y-4">
      {/* 프로필 카드 */}
      <div className="card-elevated">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-neon/20 flex items-center justify-center">
              <span className="text-neon text-2xl font-headline font-bold">{(p.name || data.nickname || 'U').charAt(0).toUpperCase()}</span>
            </div>
            <div>
              <p className="font-headline font-bold text-xl">{p.name || data.nickname || '사용자'}</p>
              <p className="text-on-surface-variant text-sm">{p.age ? `${p.age}세` : ''} {p.gender || ''} {p.goal_type ? `· 목표: ${p.goal_type}` : ''}</p>
            </div>
          </div>
          <button onClick={startEdit} className="btn-ghost text-xs flex items-center gap-1">
            <span className="material-symbols-outlined text-[14px]">edit</span> 정보 수정
          </button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
          <MetricBox label="키" value={p.height_cm} unit="cm" />
          <MetricBox label="몸무게" value={p.weight_kg} unit="kg" />
          <MetricBox label="BMI (비만도)" value={c.bmi} status={c.bmi_category} />
          <MetricBox label="체지방률" value={p.body_fat_percent} unit="%" />
        </div>
      </div>

      {/* 건강 지표 */}
      {(c.bmr_kcal || c.tdee_kcal) && (
        <div className="card-elevated">
          <p className="metric-label mb-3">🔬 AI가 계산한 건강 지표</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 md:gap-4">
            <MetricBox label="기초대사량 (BMR)" value={c.bmr_kcal} unit="kcal" />
            <MetricBox label="하루 소모량 (TDEE)" value={c.tdee_kcal} unit="kcal" />
            <MetricBox label="권장 섭취량" value={c.recommended_intake_kcal} unit="kcal" highlight />
          </div>
          <p className="text-[10px] text-on-surface-variant/40 mt-3">* Mifflin-St Jeor 공식 기반, 한국인(KSSO) BMI 기준 적용</p>
        </div>
      )}

      {/* 운동 정보 */}
      <div className="card-elevated">
        <p className="metric-label mb-3">🏋️ 운동 정보</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 md:gap-4">
          <div><span className="text-[11px] text-on-surface-variant">운동 목표</span><p className="font-headline font-bold text-sm text-neon">{p.goal_type || '—'}</p></div>
          <div><span className="text-[11px] text-on-surface-variant">주당 운동</span><p className="font-headline font-bold text-sm">{p.exercise_frequency ? `${p.exercise_frequency}회` : '—'}</p></div>
          <div><span className="text-[11px] text-on-surface-variant">경험 수준</span><p className="font-headline font-bold text-sm">{p.experience_level || '—'}</p></div>
        </div>
        {p.constraints?.length > 0 && (
          <div className="mt-3">
            <span className="text-[11px] text-on-surface-variant">제약사항: </span>
            {p.constraints.map((ct, i) => <span key={i} className="text-[10px] bg-error/10 text-error/80 px-2 py-0.5 rounded-full mr-1">{ct}</span>)}
          </div>
        )}
      </div>

      {/* 수정 안내 */}
      <div className="card-surface bg-surface-container-low text-center py-3">
        <p className="text-on-surface-variant text-xs">💡 인바디 정보 올리기, AI와 대화하기로도 정보가 자동 업데이트됩니다</p>
      </div>

      {/* 인바디 이력 */}
      {data.inbody_history?.length > 0 && (
        <div className="card-elevated">
          <p className="metric-label mb-3">📊 인바디 측정 이력 ({data.inbody_history.length}회)</p>
          <div className="space-y-2">
            {data.inbody_history.slice(-5).reverse().map((m, i) => (
              <div key={i} className="flex items-center justify-between bg-surface-container rounded-lg px-3 py-2">
                <span className="text-xs text-on-surface-variant">{m.test_date || m.recorded_at?.split('T')[0]}</span>
                <span className="text-xs font-headline font-bold">인바디 {m.inbody_score || '—'}점</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}


// ═══════════════════════════════════════
// 공통 컴포넌트
// ═══════════════════════════════════════

function MetricBox({ label, value, unit, status, highlight }) {
  return (
    <div className="text-center">
      <p className="metric-label mb-1">{label}</p>
      <p className={`font-headline font-bold text-xl ${highlight ? 'text-neon' : 'text-on-surface'}`}>
        {value ?? '—'}{unit && <span className="text-sm text-on-surface-variant ml-0.5">{unit}</span>}
      </p>
      {status && <p className="text-[10px] text-on-surface-variant">{status}</p>}
    </div>
  )
}
