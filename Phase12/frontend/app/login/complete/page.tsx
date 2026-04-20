import { Suspense } from "react";
import { KakaoComplete } from "./kakao-complete";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "로그인 처리 중 · 원정 응원 플래너",
};

export default function LoginCompletePage() {
  return (
    <Suspense fallback={null}>
      <KakaoComplete />
    </Suspense>
  );
}
