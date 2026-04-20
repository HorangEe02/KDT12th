"use client";

import { useState, useTransition } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { cn } from "@/lib/utils";

interface UserFiltersProps {
  currentRole?: "user" | "admin";
  currentStatus?: "active" | "disabled";
  currentSearch: string;
}

export function UserFilters({
  currentRole,
  currentStatus,
  currentSearch,
}: UserFiltersProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [, startTransition] = useTransition();
  const [searchInput, setSearchInput] = useState(currentSearch);

  function pushQuery(patch: Record<string, string | null>) {
    const p = new URLSearchParams(searchParams.toString());
    p.delete("cursor"); // 필터 변경 시 1페이지로
    for (const [k, v] of Object.entries(patch)) {
      if (v === null || v === "") p.delete(k);
      else p.set(k, v);
    }
    startTransition(() => {
      router.replace(`${pathname}?${p.toString()}`, { scroll: false });
    });
  }

  return (
    <div className="flex flex-col gap-3 rounded-2xl bg-se-surface-container-lowest p-4 shadow-[0_2px_10px_rgba(0,0,0,0.02)] md:flex-row md:items-center">
      {/* Search */}
      <form
        className="flex flex-1 items-center gap-2 rounded-xl bg-se-surface-container-low px-3 py-1.5"
        onSubmit={(e) => {
          e.preventDefault();
          pushQuery({ q: searchInput.trim() || null });
        }}
      >
        <span className="material-symbols-outlined text-[20px] text-se-outline">
          search
        </span>
        <input
          type="text"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          placeholder="이메일 또는 닉네임 검색"
          className="w-full bg-transparent py-1.5 text-sm outline-none placeholder:text-se-outline"
        />
        {searchInput ? (
          <button
            type="button"
            onClick={() => {
              setSearchInput("");
              pushQuery({ q: null });
            }}
            className="text-se-outline hover:text-se-primary"
          >
            <span className="material-symbols-outlined text-[18px]">close</span>
          </button>
        ) : null}
      </form>

      {/* Role filter */}
      <div className="flex gap-1.5">
        <FilterChip
          active={!currentRole}
          label="전체"
          onClick={() => pushQuery({ role: null })}
        />
        <FilterChip
          active={currentRole === "user"}
          label="회원"
          onClick={() => pushQuery({ role: "user" })}
        />
        <FilterChip
          active={currentRole === "admin"}
          label="관리자"
          onClick={() => pushQuery({ role: "admin" })}
        />
      </div>

      {/* Status filter */}
      <div className="flex gap-1.5">
        <FilterChip
          active={currentStatus === "active"}
          label="활성"
          onClick={() =>
            pushQuery({ status: currentStatus === "active" ? null : "active" })
          }
        />
        <FilterChip
          active={currentStatus === "disabled"}
          label="비활성"
          onClick={() =>
            pushQuery({
              status: currentStatus === "disabled" ? null : "disabled",
            })
          }
        />
      </div>
    </div>
  );
}

function FilterChip({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-full border px-3 py-1.5 text-xs font-bold transition-colors",
        active
          ? "border-se-primary bg-se-primary text-white"
          : "border-se-outline-variant bg-white text-se-on-surface hover:border-se-primary",
      )}
    >
      {label}
    </button>
  );
}
