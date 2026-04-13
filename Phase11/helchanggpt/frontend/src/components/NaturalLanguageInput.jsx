import { useState } from 'react'

const EXAMPLE_INPUTS = [
  "25세 남성, 178cm 82kg. 체지방 줄이고 근육 늘리고 싶어요. 주 3회 운동 가능합니다.",
  "30대 여자, 163cm 58kg이에요. 다이어트하고 싶습니다. 운동은 처음이에요.",
  "45세 남성 172cm 90kg 당뇨 전단계입니다. 무릎이 안 좋아서 달리기는 어렵습니다.",
]

export default function NaturalLanguageInput({ onSubmit, loading }) {
  const [text, setText] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (text.trim().length < 5) return
    onSubmit(text.trim())
  }

  return (
    <div className="card space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">💬</span>
        <h3 className="font-semibold text-slate-200">자연어로 입력하기</h3>
      </div>

      <p className="text-sm text-slate-400">
        나이, 성별, 키, 몸무게, 운동 목표 등을 자유롭게 입력해주세요.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="예: 25세 남성, 178cm 82kg. 체지방을 줄이고 근육을 늘리고 싶어요. 주 3회 운동 가능합니다."
          rows={4}
          className="input-field resize-none"
          disabled={loading}
        />

        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-500">
            {text.length > 0 ? `${text.length}자` : '최소 5자 이상 입력'}
          </span>
          <button
            type="submit"
            disabled={loading || text.trim().length < 5}
            className="btn-primary flex items-center gap-2"
          >
            {loading ? (
              <>
                <span className="animate-spin">⏳</span>
                분석 중...
              </>
            ) : (
              <>
                <span>🔍</span>
                프로필 분석
              </>
            )}
          </button>
        </div>
      </form>

      {/* 예시 입력 */}
      <div className="border-t border-slate-700/50 pt-4">
        <p className="text-xs text-slate-500 mb-2">예시 입력:</p>
        <div className="space-y-2">
          {EXAMPLE_INPUTS.map((example, i) => (
            <button
              key={i}
              onClick={() => setText(example)}
              className="w-full text-left text-xs text-slate-400 hover:text-orange-400
                         bg-slate-900/30 hover:bg-slate-900/60 rounded-lg px-3 py-2
                         transition-all duration-200 border border-transparent hover:border-orange-500/20"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
