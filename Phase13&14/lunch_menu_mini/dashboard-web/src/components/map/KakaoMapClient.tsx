"use client";

/**
 * KakaoMap SSR-safe wrapper.
 *
 * Kakao Maps JS SDK 는 window 객체를 직접 참조하므로 Next.js 서버 렌더링에서
 * 에러가 납니다. 이 래퍼가 next/dynamic({ ssr: false }) 로 감싸줍니다.
 *
 * 사용:
 *   import KakaoMap from "@/components/map/KakaoMapClient";
 *   <KakaoMap userLat={...} userLng={...} restaurants={...} />
 */
import dynamic from "next/dynamic";

const KakaoMap = dynamic(() => import("./KakaoMap"), {
  ssr: false,
  loading: () => (
    <div
      className="bento-card bento-card--flat flex items-center justify-center text-text-tertiary"
      style={{ height: "400px" }}
    >
      <div className="flex flex-col items-center gap-2 text-sm">
        <span className="text-2xl">🗺</span>
        <span>지도 불러오는 중...</span>
      </div>
    </div>
  ),
});

export default KakaoMap;
