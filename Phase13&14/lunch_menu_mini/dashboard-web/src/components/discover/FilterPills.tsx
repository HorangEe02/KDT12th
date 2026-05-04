"use client";

export default function FilterPills({
  categories,
  active,
  onChange,
}: {
  categories: string[];
  active: string;
  onChange: (c: string) => void;
}) {
  return (
    <div className="flex gap-1.5 flex-wrap">
      {categories.map((c) => {
        const isActive = c === active;
        return (
          <button
            key={c}
            onClick={() => onChange(c)}
            className={`px-3 py-1.5 text-[11px] font-bold uppercase tracking-[0.04em] border rounded-sm transition-colors ${
              isActive
                ? "bg-primary/10 border-primary/40 text-primary"
                : "bg-surface-1 border-outline/15 text-text-tertiary hover:text-text-secondary hover:border-outline/30"
            }`}
          >
            {c}
          </button>
        );
      })}
    </div>
  );
}
