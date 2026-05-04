import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Providers } from "@/lib/providers";
import { BRAND } from "@/lib/brand";
import TopNav from "@/components/layout/TopNav";
import Sidebar from "@/components/layout/Sidebar";
import BottomNav from "@/components/layout/BottomNav";
import StatusFooter from "@/components/layout/StatusFooter";
import OnboardingGate from "@/components/onboarding/OnboardingGate";

export const metadata: Metadata = {
  title: { default: BRAND.name, template: `%s · ${BRAND.name}` },
  description: BRAND.description,
  // PWA manifest — iPhone Safari "홈 화면에 추가" 시 풀스크린 + 아이콘 적용
  manifest: "/manifest.webmanifest",
  applicationName: BRAND.name,
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: BRAND.name,
    startupImage: ["/logo/mini1314-1024.png"],
  },
  icons: {
    icon: [
      { url: "/logo/mini1314-192.png", sizes: "192x192", type: "image/png" },
      { url: "/logo/mini1314-512.png", sizes: "512x512", type: "image/png" },
    ],
    apple: [
      { url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" },
      { url: "/logo/apple-touch-icon-167.png", sizes: "167x167", type: "image/png" },
      { url: "/logo/apple-touch-icon-152.png", sizes: "152x152", type: "image/png" },
    ],
    shortcut: "/logo/mini1314-192.png",
  },
  formatDetection: {
    telephone: false,
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#fdfaf6" },
    { media: "(prefers-color-scheme: dark)", color: "#000000" },
  ],
  // notch 풀스크린 — iOS safe-area 사용
  viewportFit: "cover",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko" className="h-full antialiased" suppressHydrationWarning>
      <head>
        {/* iOS Safari 홈 화면 — manifest icons 무시하므로 link 태그 명시 필수 */}
        <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
        <link rel="apple-touch-icon-precomposed" sizes="180x180" href="/apple-touch-icon-precomposed.png" />
        <link rel="apple-touch-icon" sizes="167x167" href="/logo/apple-touch-icon-167.png" />
        <link rel="apple-touch-icon" sizes="152x152" href="/logo/apple-touch-icon-152.png" />
        <link
          href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
        <link
          href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-full bg-background text-text-primary font-body">
        <Providers>
          <TopNav />
          <Sidebar />
          <main
            className="ml-0 md:ml-64 pt-16 pb-24 md:pb-10 min-h-screen"
            style={{ paddingBottom: "max(6rem, env(safe-area-inset-bottom, 0px) + 4rem)" }}
          >
            <div className="px-4 md:px-6 py-4 md:py-6">{children}</div>
          </main>
          <StatusFooter />
          <BottomNav />
          <OnboardingGate />
        </Providers>
      </body>
    </html>
  );
}
