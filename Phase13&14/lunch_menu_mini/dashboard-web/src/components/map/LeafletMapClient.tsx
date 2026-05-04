"use client";

/**
 * LeafletMap SSR-safe wrapper.
 *
 * Leaflet 은 window 객체를 직접 참조하므로 Next.js 서버 렌더링 단계에서
 * ReferenceError 가 발생합니다. 이 파일은 next/dynamic 으로 클라이언트 전용
 * 렌더를 강제하고, 로딩 스켈레톤을 제공합니다.
 *
 * 사용:
 *   import LeafletMap from "@/components/map/LeafletMapClient";
 *   <LeafletMap userLat={...} userLng={...} restaurants={...} />
 */
import dynamic from "next/dynamic";

const LeafletMap = dynamic(() => import("./LeafletMap"), {
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

export default LeafletMap;
