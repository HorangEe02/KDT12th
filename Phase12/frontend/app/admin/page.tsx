import { fetchAdminMetrics, fetchLiveFeed } from "@/lib/firebase/admin-metrics";
import { KpiHeroCard, KpiSmallCard } from "@/components/admin/kpi-card";
import { EngagementChart } from "@/components/admin/engagement-chart";
import { LiveFeed } from "@/components/admin/live-feed";

export const dynamic = "force-dynamic";

export default async function AdminDashboardPage() {
  const [metrics, feed] = await Promise.all([
    fetchAdminMetrics(),
    fetchLiveFeed(12),
  ]);

  if (!metrics) {
    return (
      <div className="rounded-2xl border border-dashed border-se-outline-variant bg-white p-8 text-center">
        <p className="font-display text-lg font-bold text-se-primary">
          Firestore Admin SDK 미구성
        </p>
        <p className="mt-2 text-sm text-se-on-surface-variant">
          서비스 계정 키 또는 Cloud Run ADC 가 필요합니다. <br />
          (로컬: <code className="rounded bg-se-surface-container px-1 py-0.5 text-xs">gcloud auth application-default login</code>)
        </p>
      </div>
    );
  }

  const sparkline =
    metrics.engagement.length > 0
      ? metrics.engagement.map((d) => d.activeUsers)
      : Array(12).fill(0);

  return (
    <section className="flex flex-col gap-8">
      {/* Header */}
      <header className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="font-display text-3xl font-extrabold tracking-tight text-se-on-surface">
            대시보드
          </h1>
          <p className="mt-1 font-medium text-se-on-surface-variant">
            플랫폼 운영 현황과 실시간 활동을 한눈에.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-full bg-se-surface-container-lowest px-3 py-1.5 text-xs text-se-on-surface-variant shadow-[0_2px_10px_rgba(0,0,0,0.04)]">
          <span className="h-2 w-2 animate-pulse rounded-full bg-se-secondary" />
          마지막 업데이트:{" "}
          {new Date(metrics.generatedAt).toLocaleString("ko-KR")}
        </div>
      </header>

      {/* KPI grid */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        <KpiHeroCard
          icon="group"
          label="전체 회원"
          value={metrics.totalUsers}
          delta={
            metrics.newUsers7d > 0
              ? { sign: "up", text: `+${metrics.newUsers7d}명 (7일)` }
              : { sign: "flat", text: "변동 없음" }
          }
          sparkline={sparkline}
        />
        <KpiSmallCard
          icon="confirmation_number"
          label="누적 코스"
          value={metrics.totalPlans}
          hint={`AI 챗 ${metrics.totalChatSessions.toLocaleString("ko-KR")}회 생성`}
          accent="secondary"
        />
        <KpiSmallCard
          icon="admin_panel_settings"
          label="관리자"
          value={metrics.totalAdmins}
          hint={`비활성 ${metrics.disabledUsers}명`}
          accent="tertiary"
        />
      </div>

      {/* Chart + Feed */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="rounded-[1.5rem] bg-se-surface-container-lowest p-6 shadow-[0_4px_24px_rgba(0,0,0,0.02)] lg:col-span-2 lg:p-8">
          <div className="mb-6 flex items-start justify-between">
            <div>
              <h3 className="font-display text-xl font-bold text-se-on-surface">
                일일 활성 사용자 (14일)
              </h3>
              <p className="text-sm font-medium text-se-on-surface-variant">
                Daily Active Users — 마지막 로그인 기준
              </p>
            </div>
          </div>
          <EngagementChart data={metrics.engagement} />
        </div>
        <div className="rounded-[1.5rem] bg-se-surface-container-lowest p-6 shadow-[0_4px_24px_rgba(0,0,0,0.02)] lg:p-8">
          <div className="mb-6 flex items-center justify-between">
            <h3 className="font-display text-xl font-bold text-se-on-surface">
              Live Feed
            </h3>
            <span className="flex items-center gap-1 font-display text-xs font-bold uppercase tracking-wider text-se-secondary">
              <span className="h-2 w-2 animate-pulse rounded-full bg-se-secondary" />
              실시간
            </span>
          </div>
          <LiveFeed items={feed} />
        </div>
      </div>

      {/* By team */}
      {metrics.byTeam.length > 0 ? (
        <div className="rounded-[1.5rem] bg-se-surface-container-lowest p-6 shadow-[0_4px_24px_rgba(0,0,0,0.02)] md:p-8">
          <h3 className="mb-4 font-display text-xl font-bold text-se-on-surface">
            응원팀 분포
          </h3>
          <div className="flex flex-wrap gap-2">
            {metrics.byTeam.map((t) => (
              <div
                key={t.team}
                className="flex items-center gap-2 rounded-xl bg-se-surface-container-low px-3 py-2"
              >
                <span className="font-display text-sm font-bold text-se-primary">
                  {t.team}
                </span>
                <span className="text-xs font-semibold text-se-on-surface-variant">
                  {t.count.toLocaleString("ko-KR")}명
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
