"use client";

export default function StatCard({
  icon,
  label,
  ko,
  value,
  sub,
  color,
}: {
  icon: string;
  label: string;
  ko?: string;
  value: string;
  sub?: string;
  color?: string;
}) {
  const clr = color || "var(--color-primary)";
  return (
    <div
      className="bg-surface-1 border border-outline/15 rounded-sm p-4 border-l-2 min-w-0"
      style={{ borderLeftColor: clr }}
    >
      <div className="flex items-center gap-2 mb-1">
        <span className="text-base" aria-hidden>
          {icon}
        </span>
        <span className="text-[11px] font-bold text-text-secondary uppercase tracking-[0.08em]">
          {label}
        </span>
      </div>
      {ko && (
        <div
          className="text-[10px] text-text-tertiary mb-1.5"
          style={{ fontFamily: "var(--font-ko)" }}
        >
          {ko}
        </div>
      )}
      <div className="text-xl font-heading font-bold text-text-primary leading-tight">
        {value}
      </div>
      {sub && (
        <div
          className="text-[10px] text-text-tertiary mt-1"
          style={{ fontFamily: "var(--font-ko)" }}
        >
          {sub}
        </div>
      )}
    </div>
  );
}
