import { cn } from "@/lib/utils";

interface KpiHeroProps {
  icon: string;
  label: string;
  value: number;
  delta?: { sign: "up" | "down" | "flat"; text: string };
  sparkline?: number[];
  accent?: "primary" | "secondary" | "tertiary";
}

export function KpiHeroCard({
  icon,
  label,
  value,
  delta,
  sparkline,
  accent = "primary",
}: KpiHeroProps) {
  return (
    <div className="relative col-span-1 flex flex-col justify-between overflow-hidden rounded-[1.5rem] bg-se-surface-container-lowest p-6 md:col-span-2 md:p-8 lg:col-span-2">
      <div className="absolute -right-10 -top-10 h-48 w-48 rounded-full bg-se-primary-fixed/30 blur-3xl" />
      <div className="relative z-10 mb-8 flex items-start justify-between">
        <div>
          <div className="mb-1 flex items-center gap-2">
            <span className="material-symbols-outlined text-[20px] text-se-primary">
              {icon}
            </span>
            <h2 className="font-display text-sm font-bold uppercase tracking-wider text-se-on-surface-variant">
              {label}
            </h2>
          </div>
          <div className="font-display text-5xl font-black tracking-tighter text-se-on-surface">
            {value.toLocaleString("ko-KR")}
          </div>
        </div>
        {delta ? <DeltaBadge {...delta} /> : null}
      </div>
      {sparkline && sparkline.length > 0 ? (
        <div className="relative z-10 mt-auto flex h-16 items-end gap-1 opacity-80">
          {sparkline.slice(-12).map((v, i, arr) => {
            const max = Math.max(...arr, 1);
            const h = Math.max(8, (v / max) * 100);
            const isLast = i === arr.length - 1;
            return (
              <div
                key={i}
                className={cn(
                  "w-full rounded-t-sm",
                  isLast ? "bg-se-primary" : "bg-se-primary-fixed",
                )}
                style={{ height: `${h}%` }}
              />
            );
          })}
        </div>
      ) : null}
    </div>
  );
}

interface KpiSmallProps {
  icon: string;
  label: string;
  value: string | number;
  hint?: string;
  accent?: "primary" | "secondary" | "tertiary";
}

export function KpiSmallCard({
  icon,
  label,
  value,
  hint,
  accent = "primary",
}: KpiSmallProps) {
  const borderClass =
    accent === "secondary"
      ? "border-se-secondary-fixed"
      : accent === "tertiary"
        ? "border-se-tertiary-container"
        : "border-se-primary-fixed-dim";
  return (
    <div
      className={cn(
        "relative flex flex-col justify-between rounded-[1.5rem] border-l-4 bg-se-surface-container-lowest p-6",
        borderClass,
      )}
    >
      <div>
        <div className="mb-2 flex items-center gap-2">
          <span className="material-symbols-outlined text-[20px] text-se-primary">
            {icon}
          </span>
          <h2 className="font-display text-sm font-bold uppercase tracking-wider text-se-on-surface-variant">
            {label}
          </h2>
        </div>
        <div className="font-display text-4xl font-extrabold tracking-tight text-se-on-surface">
          {typeof value === "number" ? value.toLocaleString("ko-KR") : value}
        </div>
      </div>
      {hint ? (
        <div className="mt-4 text-sm font-medium text-se-on-surface-variant">
          {hint}
        </div>
      ) : null}
    </div>
  );
}

function DeltaBadge({
  sign,
  text,
}: {
  sign: "up" | "down" | "flat";
  text: string;
}) {
  const tone =
    sign === "up"
      ? "bg-se-secondary-container text-se-on-secondary-container"
      : sign === "down"
        ? "bg-red-100 text-red-900"
        : "bg-se-surface-container text-se-on-surface-variant";
  const icon = sign === "up" ? "trending_up" : sign === "down" ? "trending_down" : "trending_flat";
  return (
    <div
      className={cn(
        "flex items-center gap-1 rounded-full px-3 py-1 text-sm font-bold",
        tone,
      )}
    >
      <span className="material-symbols-outlined text-[16px]">{icon}</span>
      {text}
    </div>
  );
}
