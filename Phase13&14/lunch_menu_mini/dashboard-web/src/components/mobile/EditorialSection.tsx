"use client";

import type { ReactNode } from "react";

/**
 * App Store editorial 섹션 wrapper.
 *
 * eyebrow (작은 캡션) + 큰 타이틀 + 자식 슬롯.
 * Today 탭의 모든 섹션이 이 래퍼를 통일적으로 사용.
 */
interface EditorialSectionProps {
  eyebrow?: string;
  title: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}

export default function EditorialSection({
  eyebrow,
  title,
  action,
  children,
  className = "",
}: EditorialSectionProps) {
  return (
    <section className={`space-y-3 ${className}`}>
      <header className="flex items-end justify-between gap-3">
        <div className="min-w-0">
          {eyebrow && <p className="appstore-eyebrow">{eyebrow}</p>}
          <h2 className="appstore-title mt-0.5">{title}</h2>
        </div>
        {action && <div className="shrink-0">{action}</div>}
      </header>
      {children}
    </section>
  );
}
