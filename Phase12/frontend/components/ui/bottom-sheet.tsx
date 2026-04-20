"use client";

import { Drawer } from "vaul";
import { useEffect, useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * 호출부가 넘긴 snap points 를 현재 viewport 높이에 맞춰 px 로 변환·clamp.
 * - 짧은 화면(예: iPhone SE landscape, 키보드 오픈)에서 snap 이 화면을 초과하지 않도록 보장.
 * - SSR 에서는 원본 배열 그대로 반환 (hydration 후 재조정).
 * - 최소 280px (헤더 + 최소 콘텐츠 280px) ~ 최대 (vh - 24px 여백) 사이로 clamp.
 */
function useAdaptiveSnapPoints(
  snapPoints?: (string | number)[],
): (string | number)[] | undefined {
  const [vh, setVh] = useState<number | null>(null);

  useEffect(() => {
    const update = () => setVh(window.innerHeight);
    update();
    window.addEventListener("resize", update);
    window.addEventListener("orientationchange", update);
    return () => {
      window.removeEventListener("resize", update);
      window.removeEventListener("orientationchange", update);
    };
  }, []);

  if (!snapPoints || snapPoints.length === 0) return snapPoints;
  if (vh === null) return snapPoints;

  const MIN_PX = 280;
  const TOP_OFFSET = 24;
  const MAX_PX = Math.max(MIN_PX, vh - TOP_OFFSET);

  return snapPoints.map((s) => {
    let px: number;
    if (typeof s === "number") {
      px = s <= 1 ? vh * s : s;
    } else if (s.endsWith("%")) {
      const pct = Number.parseFloat(s) / 100;
      px = vh * (Number.isFinite(pct) ? pct : 0.62);
    } else if (s.endsWith("px")) {
      px = Number.parseFloat(s);
    } else {
      const n = Number.parseFloat(s);
      px = Number.isFinite(n) && n > 0 && n <= 1 ? vh * n : vh * 0.62;
    }
    return `${Math.round(Math.max(MIN_PX, Math.min(MAX_PX, px)))}px`;
  });
}

/**
 * 재사용 가능 BottomSheet — vaul 기반.
 * - drag handle (━━━) 자동
 * - snap points 지원 (예: ["50%", "92%"])
 * - body scroll lock 자동
 * - safe area inset (iPhone notch)
 * - backdrop tap dismiss
 * - ESC 키 dismiss
 *
 * 출처: vaul 공식 문서 + uiux/mobile_uiux/itinerary_route_map_mobile mockup
 */
interface BottomSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title?: string;
  description?: string;
  /**
   * snap points e.g. ["50%", "92%"] — null 이면 단일 height.
   * 내부적으로 useAdaptiveSnapPoints 가 현재 viewport 높이에 맞춰
   * px 로 변환 + 최소 280px / 최대 (vh - 24px) 로 clamp.
   * 따라서 짧은 화면(키보드 open, landscape)에서도 안전.
   */
  snapPoints?: (string | number)[];
  showCloseButton?: boolean;
  /** 추가 className for content */
  contentClassName?: string;
  children: ReactNode;
  /** 컨텐츠 하단에 sticky CTA 영역 */
  footer?: ReactNode;
}

export function BottomSheet({
  open,
  onOpenChange,
  title,
  description,
  snapPoints,
  showCloseButton = true,
  contentClassName,
  children,
  footer,
}: BottomSheetProps) {
  const adaptiveSnapPoints = useAdaptiveSnapPoints(snapPoints);
  return (
    <Drawer.Root
      open={open}
      onOpenChange={onOpenChange}
      snapPoints={adaptiveSnapPoints}
      shouldScaleBackground
    >
      <Drawer.Portal>
        <Drawer.Overlay className="fixed inset-0 z-[60] bg-black/45 backdrop-blur-sm" />
        <Drawer.Content
          className={cn(
            "fixed bottom-0 left-0 right-0 z-[60] mx-auto flex h-auto max-h-[92dvh] w-full max-w-md flex-col rounded-t-[2rem] bg-white outline-none shadow-[0_-12px_40px_rgba(0,25,60,0.18)]",
            contentClassName,
          )}
        >
          {/* Drag handle */}
          <div
            aria-hidden
            className="mx-auto mt-3 h-1.5 w-12 shrink-0 rounded-full bg-se-outline-variant/70"
          />

          {/* Header */}
          {(title || showCloseButton) && (
            <header className="flex items-center justify-between border-b border-se-outline-variant/40 px-5 pt-3 pb-3">
              {title ? (
                <Drawer.Title className="font-display text-base font-bold text-se-primary">
                  {title}
                </Drawer.Title>
              ) : (
                <span className="sr-only">설정</span>
              )}
              {description ? (
                <Drawer.Description className="sr-only">
                  {description}
                </Drawer.Description>
              ) : (
                <Drawer.Description className="sr-only">
                  사용자 설정 패널
                </Drawer.Description>
              )}
              {showCloseButton ? (
                <button
                  type="button"
                  onClick={() => onOpenChange(false)}
                  aria-label="닫기"
                  className="flex h-11 w-11 items-center justify-center rounded-full text-se-on-surface-variant transition-colors hover:bg-se-surface-container-low active:scale-90"
                >
                  <span className="material-symbols-outlined text-[20px]">
                    close
                  </span>
                </button>
              ) : null}
            </header>
          )}

          {/* Scrollable content */}
          <div
            className="flex-1 overflow-y-auto overscroll-contain px-5 py-4"
            style={{
              paddingBottom: footer
                ? "1rem"
                : "max(1.25rem, env(safe-area-inset-bottom))",
            }}
          >
            {children}
          </div>

          {/* Sticky footer (선택) */}
          {footer ? (
            <div
              className="border-t border-se-outline-variant/40 bg-white px-5 pt-3 pb-4"
              style={{
                paddingBottom: "max(1rem, env(safe-area-inset-bottom))",
              }}
            >
              {footer}
            </div>
          ) : null}
        </Drawer.Content>
      </Drawer.Portal>
    </Drawer.Root>
  );
}
