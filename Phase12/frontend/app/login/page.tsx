import { redirect } from "next/navigation";
import { LoginShell } from "@/components/auth/login-shell";
import { getOptionalUser } from "@/lib/firebase/server-session";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "로그인 · 원정 응원 플래너",
  description: "이메일 또는 Google 계정으로 로그인하세요.",
};

interface LoginPageProps {
  searchParams: Promise<{ next?: string }>;
}

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const sp = await searchParams;
  const user = await getOptionalUser();
  if (user) redirect(sanitizeNext(sp.next));
  return <LoginShell mode="login" next={sanitizeNext(sp.next)} />;
}

function sanitizeNext(next?: string): string {
  if (!next) return "/";
  // 외부 도메인 / 프로토콜 차단
  if (!next.startsWith("/") || next.startsWith("//")) return "/";
  return next;
}
