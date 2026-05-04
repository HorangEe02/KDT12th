"use client";

import { useState, useMemo } from "react";
import { X, Search, Clock, Users, MessageSquareText } from "lucide-react";
import type { Restaurant } from "@/lib/types";

interface Props {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: {
    restaurant_id?: string | null;
    restaurant_name: string;
    meal_time: string;
    max_buddies: number;
    message?: string;
  }) => void;
  restaurants: Restaurant[];
}

export default function CreateBuddyModal({
  open,
  onClose,
  onSubmit,
  restaurants,
}: Props) {
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [customName, setCustomName] = useState("");
  const [mealTime, setMealTime] = useState("12:00");
  const [maxBuddies, setMaxBuddies] = useState(3);
  const [message, setMessage] = useState("");

  const filtered = useMemo(() => {
    if (!search.trim()) return restaurants.slice(0, 8);
    const q = search.toLowerCase();
    return restaurants
      .filter(
        (r) =>
          r.name.toLowerCase().includes(q) ||
          (r.category ?? "").toLowerCase().includes(q)
      )
      .slice(0, 8);
  }, [search, restaurants]);

  const selectedRestaurant = restaurants.find(
    (r) => String(r.id) === selectedId
  );
  const displayName =
    selectedRestaurant?.name ?? customName.trim() ?? "";

  const canSubmit = displayName.length > 0 && mealTime;

  const handleSubmit = () => {
    if (!canSubmit) return;
    onSubmit({
      restaurant_id: selectedId,
      restaurant_name: displayName,
      meal_time: mealTime,
      max_buddies: maxBuddies,
      message: message.trim() || undefined,
    });
    // reset
    setSearch("");
    setSelectedId(null);
    setCustomName("");
    setMealTime("12:00");
    setMaxBuddies(3);
    setMessage("");
    onClose();
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      {/* backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* modal */}
      <div className="relative glass-panel w-full max-w-md mx-4 rounded-2xl border border-outline/15 p-5 animate-[slide-up_0.2s_ease-out]">
        {/* header */}
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-heading font-bold text-text-primary uppercase tracking-tight">
            New Buddy Post
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-surface-2 text-text-tertiary"
          >
            <X size={18} />
          </button>
        </div>

        {/* 식당 선택 */}
        <div className="mb-4">
          <label className="text-[10px] text-text-tertiary uppercase tracking-wider font-bold mb-1.5 block">
            Restaurant
          </label>
          <div className="relative mb-2">
            <Search
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary"
            />
            <input
              type="text"
              placeholder="식당 검색 또는 직접 입력..."
              value={selectedRestaurant ? selectedRestaurant.name : search}
              onChange={(e) => {
                setSearch(e.target.value);
                setSelectedId(null);
                setCustomName(e.target.value);
              }}
              className="w-full pl-9 pr-3 py-2 rounded-lg bg-surface-1 border border-outline/15 text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none focus:ring-1 focus:ring-primary/50"
            />
          </div>
          {/* 자동완성 결과 */}
          {!selectedId && search.trim() && filtered.length > 0 && (
            <div className="max-h-32 overflow-y-auto rounded-lg border border-outline/10 bg-surface-1">
              {filtered.map((r) => (
                <button
                  key={r.id}
                  onClick={() => {
                    setSelectedId(String(r.id));
                    setSearch(r.name);
                  }}
                  className="w-full text-left px-3 py-1.5 text-xs text-text-secondary hover:bg-surface-2 transition-colors"
                >
                  <span className="font-medium text-text-primary">
                    {r.name}
                  </span>
                  {r.category && (
                    <span className="text-text-tertiary ml-1.5">
                      {r.category}
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* 시간 + 인원 */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div>
            <label className="text-[10px] text-text-tertiary uppercase tracking-wider font-bold mb-1.5 flex items-center gap-1">
              <Clock size={11} /> Time
            </label>
            <input
              type="time"
              value={mealTime}
              onChange={(e) => setMealTime(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-surface-1 border border-outline/15 text-sm text-text-primary focus:outline-none focus:ring-1 focus:ring-primary/50"
            />
          </div>
          <div>
            <label className="text-[10px] text-text-tertiary uppercase tracking-wider font-bold mb-1.5 flex items-center gap-1">
              <Users size={11} /> Max Buddies
            </label>
            <select
              value={maxBuddies}
              onChange={(e) => setMaxBuddies(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-lg bg-surface-1 border border-outline/15 text-sm text-text-primary focus:outline-none focus:ring-1 focus:ring-primary/50"
            >
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
                <option key={n} value={n}>
                  {n}명
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* 메시지 */}
        <div className="mb-5">
          <label className="text-[10px] text-text-tertiary uppercase tracking-wider font-bold mb-1.5 flex items-center gap-1">
            <MessageSquareText size={11} /> Message (optional)
          </label>
          <input
            type="text"
            placeholder="짬뽕 드시러 가실 분!"
            maxLength={200}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            className="w-full px-3 py-2 rounded-lg bg-surface-1 border border-outline/15 text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none focus:ring-1 focus:ring-primary/50"
          />
        </div>

        {/* 제출 */}
        <button
          onClick={handleSubmit}
          disabled={!canSubmit}
          className="w-full py-2.5 rounded-lg bg-primary hover:bg-primary-dark disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs font-bold uppercase tracking-wider transition-colors"
        >
          모집글 올리기
        </button>
      </div>
    </div>
  );
}
