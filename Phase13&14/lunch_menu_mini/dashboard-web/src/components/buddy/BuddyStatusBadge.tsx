"use client";

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  open: { label: "모집중", color: "bg-success/20 text-success" },
  full: { label: "모집완료", color: "bg-warning/20 text-warning" },
  closed: { label: "마감", color: "bg-text-tertiary/20 text-text-tertiary" },
  cancelled: { label: "취소됨", color: "bg-text-tertiary/20 text-text-tertiary" },
  expired: { label: "시간경과", color: "bg-text-tertiary/20 text-text-tertiary" },
};

export default function BuddyStatusBadge({ status }: { status: string }) {
  const info = STATUS_MAP[status] ?? STATUS_MAP.closed;
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${info.color}`}
    >
      {info.label}
    </span>
  );
}
