import { Suspense } from "react";
import { TopNav } from "@/components/layout/top-nav";
import { FilterSidebar } from "@/components/sidebar/filter-sidebar";
import { MobileFilterSheet } from "@/components/sidebar/mobile-filter-sheet";
import { MobileBottomNav } from "@/components/nav/mobile-bottom-nav";

export default function ShellLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <Suspense fallback={null}>
        <TopNav />
      </Suspense>
      <div className="mx-auto flex w-full max-w-[1240px] flex-1">
        <Suspense fallback={null}>
          <FilterSidebar />
        </Suspense>
        <main className="min-w-0 flex-1 px-4 py-6 pb-28 md:px-8 md:py-8 md:pb-8">
          {children}
        </main>
      </div>
      <Suspense fallback={null}>
        <MobileFilterSheet />
      </Suspense>
      <Suspense fallback={null}>
        <MobileBottomNav />
      </Suspense>
    </>
  );
}
