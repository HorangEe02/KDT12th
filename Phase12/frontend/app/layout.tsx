import type { Metadata } from "next";
import { Plus_Jakarta_Sans, Manrope, Noto_Sans_KR } from "next/font/google";
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
        {children}
      </body>
    </html>
  );
}
