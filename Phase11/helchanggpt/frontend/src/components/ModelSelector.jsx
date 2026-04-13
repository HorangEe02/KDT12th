import { useState, useEffect } from 'react'

const DEFAULT_MODELS = [
  { name: 'exaone3.5:7.8b', display: 'EXAONE 3.5 7.8B', desc: '한국어 최강 — LG AI ✅', korean: 3, vision: false, size: '4.8GB', emoji: '🇰🇷' },
  { name: 'exaone3.5:2.4b', display: 'EXAONE 3.5 2.4B', desc: '한국어 경량·빠른 응답', korean: 3, vision: false, size: '1.6GB', emoji: '🇰🇷' },
  { name: 'qwen3.5:9b', display: 'Qwen 3.5 9B', desc: '다국어 — Alibaba', korean: 2, vision: false, size: '6.1GB', emoji: '🌏' },
  { name: 'qwen3.5:4b', display: 'Qwen 3.5 4B', desc: '경량·빠른 응답 ⚡', korean: 2, vision: false, size: '3.2GB', emoji: '⚡' },
  { name: 'gemma4:e4b', display: 'Gemma 4', desc: '이미지 분석 가능 — Google', korean: 2, vision: true, size: '8.9GB', emoji: '👁️' },
  { name: 'exaone-deep', display: 'EXAONE Deep', desc: '추론 특화 — LG AI', korean: 3, vision: false, size: '4.8GB', emoji: '🧠' },
]

export default function ModelSelector({ selectedModel, onModelChange, visionOnly = false, compact = false }) {
  const [open, setOpen] = useState(false)

  const models = visionOnly ? DEFAULT_MODELS.filter(m => m.vision) : DEFAULT_MODELS
  const current = models.find(m => m.name === selectedModel) || models[0]

  if (compact) {
    return (
      <div className="relative">
        <button
          onClick={() => setOpen(!open)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-container-high hover:bg-surface-container-highest text-xs font-headline font-bold transition-all"
        >
          <span>{current.emoji}</span>
          <span className="text-on-surface-variant">{current.display}</span>
          <span className="material-symbols-outlined text-[14px] text-on-surface-variant">expand_more</span>
        </button>

        {open && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
            <div className="absolute top-full mt-1 right-0 z-50 bg-surface-container-highest rounded-xl shadow-neon-glow p-2 min-w-[250px]">
              <p className="metric-label px-3 py-1 mb-1">AI 모델 선택</p>
              {models.map(m => (
                <button
                  key={m.name}
                  onClick={() => { onModelChange(m.name); setOpen(false) }}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-all ${
                    m.name === selectedModel ? 'bg-neon/10 text-neon' : 'hover:bg-surface-container-high text-on-surface-variant'
                  }`}
                >
                  <span className="text-lg">{m.emoji}</span>
                  <div className="flex-1 min-w-0">
                    <p className="font-headline font-bold text-xs">{m.display}</p>
                    <p className="text-[10px] text-on-surface-variant/60 truncate">{m.desc}</p>
                  </div>
                  {m.name === selectedModel && <span className="text-neon text-xs">✓</span>}
                </button>
              ))}
            </div>
          </>
        )}
      </div>
    )
  }

  return (
    <div className="card-elevated">
      <p className="metric-label mb-3">🤖 AI 모델 선택</p>
      <div className="grid grid-cols-2 gap-2">
        {models.map(m => (
          <button
            key={m.name}
            onClick={() => onModelChange(m.name)}
            className={`flex items-center gap-2 p-3 rounded-xl text-left transition-all ${
              m.name === selectedModel
                ? 'bg-neon/10 border border-neon/30 shadow-neon-glow'
                : 'bg-surface-container hover:bg-surface-container-high border border-transparent'
            }`}
          >
            <span className="text-xl">{m.emoji}</span>
            <div className="min-w-0">
              <p className={`font-headline font-bold text-xs ${m.name === selectedModel ? 'text-neon' : 'text-on-surface'}`}>
                {m.display}
              </p>
              <p className="text-[10px] text-on-surface-variant truncate">{m.desc}</p>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-[9px] text-on-surface-variant/50">{m.size}</span>
                {m.vision && <span className="text-[9px] text-tertiary">👁 비전</span>}
                {'🇰🇷'.repeat(m.korean > 2 ? 1 : 0) && m.korean >= 3 && <span className="text-[9px]">🇰🇷</span>}
              </div>
            </div>
          </button>
        ))}
      </div>
      <p className="text-[10px] text-on-surface-variant/40 mt-2 text-center">
        선택한 모델이 Ollama에서 실행됩니다 (로컬 GPU)
      </p>
    </div>
  )
}
