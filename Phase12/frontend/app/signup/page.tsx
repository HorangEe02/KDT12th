import { redirect } from "next/navigation";
import { LoginShell } from "@/components/auth/login-shell";
import { getOptionalUser } from "@/lib/firebase/server-session";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "회원가입 · 원정 응원 플래너",
  description: "이메일 또는 Google 계정으로 30초만에 가입하세요.",
};

interface SignupPageProps {
  searchParams: Promise<{ next?: string }>;
}

export default async function SignupPage({ searchParams }: SignupPageProps) {
  const sp = await searchParams;
  const user = await getOptionalUser();
  if (user) redirect(sanitizeNext(sp.next));
  return <LoginShell mode="signup" next={sanitizeNext(sp.next)} />;
}

function sanitizeNext(next?: string): string {
  if (!next) return "/";
  if (!next.startsWith("/") || next.startsWith("//")) return "/";
  return next;
}
