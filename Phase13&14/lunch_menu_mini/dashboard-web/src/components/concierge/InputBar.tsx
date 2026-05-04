"use client";

import { Send, StopCircle } from "lucide-react";
import { useRef, useEffect } from "react";

export default function InputBar({
  value,
  onChange,
  onSend,
  onStop,
  disabled,
  streaming,
}: {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  onStop?: () => void;
  disabled?: boolean;
  streaming?: boolean;
}) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize up to 5 rows
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 120)}px`;
  }, [value]);

  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!streaming && value.trim()) onSend();
    }
  };

  return (
    <div className="bg-surface-1 border-t border-outline/15 p-4">
      <div className="flex items-end gap-2 bg-surface-2 border border-outline/20 rounded-sm p-2 focus-within:border-primary/40 transition-colors">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKey}
          disabled={disabled && !streaming}
          rows={1}
          placeholder="예) 오늘 단백질 부족한데 뭐 먹지?  (Shift+Enter 줄바꿈)"
          className="flex-1 bg-transparent outline-none text-sm text-text-primary resize-none placeholder:text-text-tertiary"
          style={{ fontFamily: "var(--font-ko)", maxHeight: 120 }}
        />
        {streaming && onStop ? (
          <button
            type="button"
            onClick={onStop}
            className="flex-shrink-0 flex items-center gap-1.5 px-3 py-2 text-xs font-bold uppercase tracking-wider bg-error text-background rounded-sm hover:bg-error-dark transition-colors"
          >
            <StopCircle size={14} />
            Stop
          </button>
        ) : (
          <button
            type="button"
            onClick={onSend}
            disabled={!value.trim() || disabled}
            className="flex-shrink-0 flex items-center gap-1.5 px-4 py-2 text-xs font-bold uppercase tracking-wider bg-primary text-background rounded-sm hover:bg-primary-dark transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Send size={14} />
            Send
          </button>
        )}
      </div>
      <div
        className="text-[10px] text-text-tertiary mt-1.5 font-mono"
        style={{ fontFamily: "var(--font-ko)" }}
      >
        Enter 전송 · Shift+Enter 줄바꿈
      </div>
    </div>
  );
}
