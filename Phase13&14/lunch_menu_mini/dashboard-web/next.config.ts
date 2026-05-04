import type { NextConfig } from "next";
import path from "path";

// 빌드 모드 선택:
//   - NEXT_OUTPUT=standalone (기본) → Docker 배포용 .next/standalone/server.js
//   - NEXT_OUTPUT=export             → Firebase Hosting 등 정적 호스팅용 out/
//
// 사용 예:
//   npm run build              # standalone (Docker)
//   npm run build:static       # export (Firebase Hosting)
const outputMode = (process.env.NEXT_OUTPUT ?? "standalone") as
  | "standalone"
  | "export";

const nextConfig: NextConfig = {
  // 빌드 모드 — Docker 또는 정적 export 중 선택
  // https://nextjs.org/docs/app/api-reference/next-config-js/output
  output: outputMode,

  // 정적 export 시 trailingSlash가 Firebase Hosting cleanUrls와 호환되어
  // /discover/ 형태로 디렉토리 인덱스 라우팅이 자연스럽게 동작.
  trailingSlash: outputMode === "export" ? true : undefined,

  // 정적 export는 next/image 런타임 최적화를 못 쓰므로 unoptimized 명시.
  // (현재 next/image 사용처 없으므로 무영향)
  images: {
    unoptimized: outputMode === "export",
  },

  // Tree-shake large icon/chart libs so unused exports don't end up in the
  // route chunks. Next auto-rewrites bare imports into per-module paths.
  experimental: {
    optimizePackageImports: ["recharts", "lucide-react"],
  },
  // Turbopack workspace root 고정 — Mini 루트에 lock 파일이 남아있어도
  // 이 디렉토리를 기준으로 node_modules 를 찾도록 명시.
  turbopack: {
    root: path.resolve(__dirname),
  },
  // LAN 개발용 허용 origin (HMR/_next 리소스 cross-origin 차단 해제)
  // ⚠ Geolocation, Kakao Maps 는 localhost/127.0.0.1 이외에선 여전히 동작 안 함.
  allowedDevOrigins: [
    "localhost",
    "127.0.0.1",
    "172.30.1.13", // LAN IP (필요 시 본인 IP 로 수정)
    "*.local",
    // HTTPS variants for dev:https script
    "https://localhost:3000",
    "https://127.0.0.1:3000",
    "https://172.30.1.13:3000",
  ],
};

export default nextConfig;
