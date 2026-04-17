import { Suspense } from "react";
import { TopNav } from "@/components/layout/top-nav";
import { FilterSidebar } from "@/components/sidebar/filter-sidebar";

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
        <main className="min-w-0 flex-1 px-4 py-6 md:px-8 md:py-8">
          {children}
        </main>
      </div>
    </>
  );
}
