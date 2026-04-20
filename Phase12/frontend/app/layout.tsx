import type { Metadata, Viewport } from "next";
import { Plus_Jakarta_Sans, Manrope, Noto_Sans_KR } from "next/font/google";
import { Toaster } from "sonner";
import { AuthProvider } from "@/components/auth/auth-provider";
import "./globals.css";

const jakarta = Plus_Jakarta_Sans({
  variable: "--font-jakarta",
  subsets: ["latin"],
  weight: ["400", "500", "700", "800"],
  display: "swap",
});

const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

const notoSansKr = Noto_Sans_KR({
  variable: "--font-noto-kr",
  subsets: ["latin"],
  weight: ["400", "500", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "원정 응원 플래너 · KBO Away Game Companion",
  description:
    "KBO 10개 구단 원정 응원러를 위한 AI 여행 플래너 — 경기·교통·맛집·숙소·관광을 한 번에.",
};

/**
 * 모바일 뷰포트 설정 (Next.js 16 `viewport` export).
 *   - viewportFit: "cover"  → iPhone notch / Dynamic Island / home indicator 영역까지 확장
 *   - themeColor: SE 프라이머리 다크네이비 (#00193c) → iOS Safari 주소창/Android 상태바 색상
 *   - maximumScale 미설정 → 사용자 핀치 줌 허용 (접근성)
 *   - initialScale 1, width device-width → 기본값 명시
 */
export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#00193c",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="ko"
      className={`${jakarta.variable} ${manrope.variable} ${notoSansKr.variable} h-full antialiased`}
    >
      <head>
        {/* Material Symbols Outlined — Google Fonts CDN */}
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap"
        />
      </head>
      <body className="min-h-full flex flex-col bg-se-surface text-se-on-surface">
        <AuthProvider>{children}</AuthProvider>
        <Toaster position="top-center" richColors closeButton />
      </body>
    </html>
  );
}
