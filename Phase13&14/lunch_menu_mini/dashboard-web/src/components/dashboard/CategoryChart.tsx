"use client";

export interface CategoryCount {
  name: string;
  count: number;
  color?: string;
}

export default function CategoryChart({
  categories,
}: {
  categories: CategoryCount[];
}) {
  if (!categories.length) return null;
  const maxCount = Math.max(...categories.map((c) => c.count));

  return (
    <div className="bento-card">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-heading font-bold text-text-primary uppercase tracking-[0.04em]">
            Category Distribution
          </h3>
          <p className="text-[11px] text-text-tertiary uppercase tracking-[0.1em] mt-0.5">
            Registered Restaurants by Cuisine
          </p>
          <p
            className="text-[10px] text-text-tertiary mt-0.5"
            style={{ fontFamily: "var(--font-ko)" }}
          >
            카테고리별 음식점 분포
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {categories.map((cat) => {
          const pct = maxCount > 0 ? (cat.count / maxCount) * 100 : 0;
          return (
            <div key={cat.name}>
              <div className="flex items-baseline justify-between mb-1">
                <span className="text-xs font-bold text-text-primary uppercase tracking-[0.04em]">
                  {cat.name}
                </span>
                <span className="text-xs font-mono font-semibold text-primary">
                  {cat.count.toLocaleString()} 곳
                </span>
              </div>
              <div className="h-[6px] bg-surface-3 overflow-hidden">
                <div
                  className="h-full transition-all duration-700 ease-out"
                  style={{
                    width: `${pct}%`,
                    background: cat.color || "var(--color-primary)",
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
