import { redirect } from "next/navigation";
import type { ReactNode } from "react";
import { getOptionalUser } from "@/lib/firebase/server-session";
import { AdminShell } from "@/components/admin/admin-shell";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "관리자 콘솔 · 원정 응원 플래너",
  robots: { index: false, follow: false },
};

export default async function AdminLayout({
  children,
}: {
  children: ReactNode;
}) {
  const user = await getOptionalUser({ checkRevoked: true });
  if (!user) redirect("/login?next=/admin");
  if (!user.isAdmin) redirect("/?error=forbidden");
  return <AdminShell user={user}>{children}</AdminShell>;
}
