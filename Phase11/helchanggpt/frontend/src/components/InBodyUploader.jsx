import { useState, useRef } from 'react'

export default function InBodyUploader({ onUpload, loading }) {
  const [dragActive, setDragActive] = useState(false)
  const [preview, setPreview] = useState(null)
  const [fileName, setFileName] = useState('')
  const inputRef = useRef(null)

  const handleFile = (file) => {
    if (!file || !file.type.startsWith('image/')) {
      alert('이미지 파일만 업로드 가능합니다.')
      return
    }
    setFileName(file.name)
    const reader = new FileReader()
    reader.onload = (e) => setPreview(e.target.result)
    reader.readAsDataURL(file)
  }

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files?.[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleChange = (e) => {
    if (e.target.files?.[0]) {
      handleFile(e.target.files[0])
    }
  }

  const handleSubmit = () => {
    if (inputRef.current?.files?.[0]) {
      onUpload(inputRef.current.files[0])
    }
  }

  return (
    <div className="card space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">📋</span>
        <h3 className="font-semibold text-slate-200">인바디 결과지 업로드</h3>
      </div>

      <p className="text-sm text-slate-400">
        인바디 측정 결과지 이미지를 업로드하면 AI가 자동으로 데이터를 추출합니다.
      </p>

      {/* 드래그앤드롭 영역 */}
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer
                    transition-all duration-200
                    ${dragActive
                      ? 'border-orange-500 bg-orange-500/10'
                      : 'border-slate-600 hover:border-slate-500 hover:bg-slate-800/30'
                    }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          onChange={handleChange}
          className="hidden"
        />

        {preview ? (
          <div className="space-y-3">
            <img
              src={preview}
              alt="인바디 미리보기"
              className="max-h-48 mx-auto rounded-lg shadow-lg"
            />
            <p className="text-sm text-slate-300">{fileName}</p>
            <p className="text-xs text-slate-500">다른 이미지를 올리려면 클릭하세요</p>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="text-4xl">📤</div>
            <p className="text-slate-300 font-medium">
              인바디 결과지를 드래그하거나 클릭하여 업로드
            </p>
            <p className="text-xs text-slate-500">
              PNG, JPG, JPEG 형식 지원
            </p>
          </div>
        )}
      </div>

      {/* 업로드 버튼 */}
      {preview && (
        <button
          onClick={handleSubmit}
          disabled={loading}
          className="btn-primary w-full flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <span className="animate-spin">⏳</span>
              AI가 인바디를 분석 중...
            </>
          ) : (
            <>
              <span>🔍</span>
              인바디 분석 시작
            </>
          )}
        </button>
      )}

      {/* 안내 */}
      <div className="bg-slate-900/50 rounded-lg p-3">
        <p className="text-xs text-slate-500">
          💡 GPT-4o Vision이 인바디 결과지의 수치를 자동으로 읽어냅니다.
          최적의 결과를 위해 깨끗하고 선명한 이미지를 업로드해주세요.
        </p>
      </div>
    </div>
  )
}
