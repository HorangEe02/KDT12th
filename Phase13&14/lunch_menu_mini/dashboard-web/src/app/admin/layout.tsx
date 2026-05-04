"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldAlert } from "lucide-react";
import { getRole, isTokenValid } from "@/lib/auth";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [allowed, setAllowed] = useState<"checking" | "yes" | "no">("checking");

  useEffect(() => {
    if (!isTokenValid()) {
      setAllowed("no");
      const t = setTimeout(() => router.replace("/login"), 1500);
      return () => clearTimeout(t);
    }
    if (getRole() !== "admin") {
      setAllowed("no");
      const t = setTimeout(() => router.replace("/"), 1500);
      return () => clearTimeout(t);
    }
    setAllowed("yes");
  }, [router]);

  if (allowed === "checking") {
    return (
      <div className="text-center py-20 text-text-tertiary text-sm">권한 확인 중...</div>
    );
  }

  if (allowed === "no") {
    return (
      <div className="max-w-md mx-auto bg-surface-1 border border-outline/15 rounded-sm p-8 text-center">
        <ShieldAlert size={48} className="mx-auto text-error mb-4" />
        <h2 className="text-lg font-heading font-bold text-text-primary mb-2">
          관리자 권한 필요
        </h2>
        <p className="text-xs text-text-tertiary">
          잠시 후 적절한 페이지로 이동합니다…
        </p>
      </div>
    );
  }

  return <div className="space-y-4">{children}</div>;
}
