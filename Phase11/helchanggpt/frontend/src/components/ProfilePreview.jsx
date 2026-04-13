export default function ProfilePreview({ profile }) {
  if (!profile) return null

  const { basic, calculated, nlp_analysis, health_risk_flags, profile_confidence, meta } = profile

  return (
    <div className="space-y-6">
      {/* 프로필 제목 */}
      <div className="text-center">
        <h3 className="text-2xl font-bold text-slate-200 mb-1">분석 결과</h3>
        <div className="flex items-center justify-center gap-2">
          <ConfidenceBadge confidence={profile_confidence} />
          <span className="text-xs text-slate-500">
            {meta?.input_type === 'inbody_image' ? '인바디 기반' :
             meta?.input_type === 'both' ? '인바디 + 자연어' : '자연어 기반'}
          </span>
        </div>
      </div>

      {/* 기본 정보 카드 */}
      <div className="card">
        <h4 className="font-semibold text-slate-300 mb-4 flex items-center gap-2">
          <span>👤</span> 기본 정보
        </h4>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <MetricItem label="나이" value={basic?.age} unit="세" />
          <MetricItem label="성별" value={basic?.gender} />
          <MetricItem label="키" value={basic?.height_cm} unit="cm" />
          <MetricItem label="체중" value={basic?.weight_kg} unit="kg" />
        </div>
      </div>

      {/* 건강 지표 카드 */}
      {calculated && (
        <div className="card">
          <h4 className="font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <span>📊</span> 건강 지표
          </h4>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            <MetricCard
              label="BMI"
              value={calculated.bmi}
              category={calculated.bmi_category}
              color={getBMIColor(calculated.bmi_category)}
            />
            <MetricCard
              label="기초대사량 (BMR)"
              value={calculated.bmr_kcal}
              unit="kcal"
              subtitle="Mifflin-St Jeor"
            />
            <MetricCard
              label="일일 소비량 (TDEE)"
              value={calculated.tdee_kcal}
              unit="kcal"
            />
            <MetricCard
              label="권장 섭취량"
              value={calculated.recommended_intake_kcal}
              unit="kcal"
              color="text-orange-400"
            />
            <MetricCard
              label="적정 체중"
              value={calculated.ideal_weight_kg}
              unit="kg"
              subtitle={calculated.ideal_weight_range
                ? `${calculated.ideal_weight_range[0]}~${calculated.ideal_weight_range[1]}kg`
                : null}
            />
            {calculated.body_fat_category && (
              <MetricCard
                label="체지방률 판정"
                value={calculated.body_fat_category}
              />
            )}
          </div>
        </div>
      )}

      {/* 운동 목표 카드 */}
      {nlp_analysis && (
        <div className="card">
          <h4 className="font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <span>🎯</span> 운동 목표 분석
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="metric-card">
              <div className="text-sm text-slate-400 mb-1">목표 유형</div>
              <div className="text-xl font-bold text-orange-400">{nlp_analysis.goal_type}</div>
              <div className="text-xs text-slate-500 mt-1">
                신뢰도: {Math.round((nlp_analysis.goal_confidence || 0) * 100)}%
                ({nlp_analysis.goal_method})
              </div>
            </div>
            <div className="metric-card">
              <div className="text-sm text-slate-400 mb-1">운동 계획</div>
              <div className="text-lg font-semibold text-slate-200">
                주 {nlp_analysis.exercise_frequency || 3}회
              </div>
              <div className="text-xs text-slate-500 mt-1">
                경험 수준: {nlp_analysis.experience_level || '입문'}
              </div>
            </div>
          </div>

          {/* 제약사항 */}
          {nlp_analysis.constraints?.length > 0 && (
            <div className="mt-4 bg-amber-500/10 border border-amber-500/30 rounded-lg p-3">
              <span className="text-sm text-amber-400 font-medium">⚠️ 제약사항: </span>
              <span className="text-sm text-amber-300">
                {nlp_analysis.constraints.join(', ')}
              </span>
            </div>
          )}
        </div>
      )}

      {/* 건강 위험도 */}
      {health_risk_flags?.warnings?.length > 0 && (
        <div className="card border-red-500/30">
          <h4 className="font-semibold text-red-400 mb-3 flex items-center gap-2">
            <span>🚨</span> 건강 위험도 알림
          </h4>
          <div className="space-y-2">
            {health_risk_flags.warnings.map((warning, i) => (
              <div key={i} className="bg-red-500/10 rounded-lg p-3 text-sm text-red-300">
                {warning}
              </div>
            ))}
          </div>
          {health_risk_flags.recommendations?.length > 0 && (
            <div className="mt-3 space-y-1">
              {health_risk_flags.recommendations.map((rec, i) => (
                <p key={i} className="text-xs text-slate-400">💡 {rec}</p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 프로필 신뢰도 & 다음 단계 */}
      {profile_confidence && (
        <div className="card bg-gradient-to-br from-slate-800/50 to-slate-900/50">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-semibold text-slate-300 flex items-center gap-2">
              <span>📈</span> 프로필 완성도
            </h4>
            <span className="text-2xl font-bold text-orange-400">{profile_confidence.score}/100</span>
          </div>

          {/* 프로그레스 바 */}
          <div className="w-full bg-slate-700 rounded-full h-2 mb-3">
            <div
              className="bg-gradient-to-r from-orange-500 to-amber-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${profile_confidence.score}%` }}
            />
          </div>

          <p className="text-sm text-slate-400">{profile_confidence.suggestion}</p>
        </div>
      )}
    </div>
  )
}

function MetricItem({ label, value, unit }) {
  return (
    <div className="text-center">
      <div className="text-xs text-slate-500 mb-1">{label}</div>
      <div className="text-lg font-semibold text-slate-200">
        {value ?? '-'}{unit && <span className="text-sm text-slate-400 ml-1">{unit}</span>}
      </div>
    </div>
  )
}

function MetricCard({ label, value, unit, category, subtitle, color }) {
  return (
    <div className="metric-card">
      <div className="text-xs text-slate-400 mb-1">{label}</div>
      <div className={`text-xl font-bold ${color || 'text-slate-200'}`}>
        {value ?? '-'}
        {unit && <span className="text-sm text-slate-400 ml-1">{unit}</span>}
      </div>
      {category && <div className="text-xs text-slate-400 mt-1">{category}</div>}
      {subtitle && <div className="text-xs text-slate-500 mt-1">{subtitle}</div>}
    </div>
  )
}

function ConfidenceBadge({ confidence }) {
  if (!confidence) return null
  const colors = {
    '높음': 'bg-green-500/20 text-green-400 border-green-500/30',
    '보통': 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    '낮음': 'bg-red-500/20 text-red-400 border-red-500/30',
  }
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border ${colors[confidence.level] || colors['보통']}`}>
      신뢰도: {confidence.level}
    </span>
  )
}

function getBMIColor(category) {
  const map = {
    '저체중': 'text-blue-400',
    '정상': 'text-green-400',
    '과체중': 'text-amber-400',
    '1단계 비만': 'text-orange-400',
    '2단계 비만': 'text-red-400',
    '3단계 비만(고도비만)': 'text-red-500',
  }
  return map[category] || 'text-slate-200'
}
