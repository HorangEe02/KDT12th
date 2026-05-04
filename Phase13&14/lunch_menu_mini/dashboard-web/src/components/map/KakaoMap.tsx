"use client";

/**
 * KakaoMap — Kakao Maps JavaScript SDK 래퍼.
 *
 * LeafletMap 과 동일한 Props 시그니처로 작성되어 드롭인 교체 가능합니다.
 *
 * ⚠ 요구사항:
 *   1. .env.local 에 NEXT_PUBLIC_KAKAO_MAP_KEY 설정
 *   2. Kakao Developers → 내 애플리케이션 → 플랫폼 → Web 에 사이트 도메인 등록
 *      (로컬 개발: http://localhost:3000)
 *   3. 도메인 미등록 시 401 에러로 지도 로드 실패
 *
 * SDK 로드 전략:
 *   - `autoload=false` 로 불러온 뒤 `window.kakao.maps.load(cb)` 로 lazy init
 *   - 여러 인스턴스가 있어도 SDK 는 1회만 로드 (module-level promise 캐시)
 */
import { useEffect, useRef, useState } from "react";
import type { Restaurant } from "@/lib/types";
import {
  buildGlassMarkerHTML,
  ensureGlassMarkerStylesInjected,
} from "@/components/map/markers/LiquidGlassMarker";

// ────────────────────────────────────────────────────────────
// Global SDK loader (한 페이지에서 한 번만 주입)
// ────────────────────────────────────────────────────────────
declare global {
  interface Window {
    kakao: any;
  }
}

let kakaoLoader: Promise<void> | null = null;

function loadKakaoSdk(appkey: string): Promise<void> {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("SSR context"));
  }
  if (window.kakao && window.kakao.maps) {
    // 이미 로드됨 → maps.load 만 호출해서 초기화 보장
    return new Promise((resolve) => {
      window.kakao.maps.load(() => resolve());
    });
  }
  if (kakaoLoader) return kakaoLoader;

  kakaoLoader = new Promise<void>((resolve, reject) => {
    const existing = document.getElementById("kakao-maps-sdk");
    if (existing) {
      // 다른 인스턴스가 주입 중 — 이벤트 대기
      existing.addEventListener("load", () => {
        window.kakao.maps.load(() => resolve());
      });
      existing.addEventListener("error", () => reject(new Error("SDK load failed")));
      return;
    }

    const script = document.createElement("script");
    script.id = "kakao-maps-sdk";
    script.async = true;
    // ⚠ crossOrigin="anonymous" 제거 — 카카오 SDK 서버가 CORS 헤더를
    //   반환하지 않는 케이스가 있어 스크립트 로드가 차단될 수 있음.
    // autoload=false: window.kakao.maps 를 수동 init 하기 위함
    // libraries 파라미터는 제거 — services/clusterer 등은 앱에 별도 권한 필요
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${appkey}&autoload=false`;
    script.onload = () => {
      if (!window.kakao || !window.kakao.maps) {
        reject(new Error("Kakao Maps SDK loaded but window.kakao is missing"));
        return;
      }
      window.kakao.maps.load(() => resolve());
    };
    script.onerror = () => {
      // 실패한 script 태그 제거 — 재시도 시 새 태그를 주입할 수 있도록
      script.remove();
      reject(new Error("Kakao Maps SDK script failed to load"));
    };
    document.head.appendChild(script);
  }).catch((e) => {
    // 실패 시 캐시 초기화 → 다음 마운트에서 재시도 가능
    kakaoLoader = null;
    throw e;
  });

  return kakaoLoader;
}

// ────────────────────────────────────────────────────────────
// Props (LeafletMap 호환)
// ────────────────────────────────────────────────────────────
interface KakaoMapProps {
  userLat: number;
  userLng: number;
  restaurants: Restaurant[];
  selectedId?: string | null;
  onSelect?: (id: string) => void;
  height?: string;
  zoom?: number;
  /** 사용자 위치 기준 반경 원 (미터). 없으면 미표시 */
  showRadius?: number;
  /** 지도 중심 모드 */
  centerOn?: "user" | "selected";
}

// ────────────────────────────────────────────────────────────
// Component
// ────────────────────────────────────────────────────────────
export default function KakaoMap({
  userLat,
  userLng,
  restaurants,
  selectedId = null,
  onSelect,
  height = "400px",
  zoom = 4, // Kakao zoom: 1(가까움) ~ 14(멀리), 15 기본 ≈ Leaflet 15 → 4
  showRadius,
  centerOn = "user",
}: KakaoMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const userMarkerRef = useRef<any>(null);
  const circleRef = useRef<any>(null);
  const infoRef = useRef<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  const appkey = process.env.NEXT_PUBLIC_KAKAO_MAP_KEY || "";

  // SDK 로드 + 지도 초기화 (1회, retryCount 변경 시 재시도)
  useEffect(() => {
    if (!appkey) {
      setError("NEXT_PUBLIC_KAKAO_MAP_KEY 가 설정되지 않았습니다.");
      return;
    }

    let cancelled = false;
    setError(null);
    ensureGlassMarkerStylesInjected();

    loadKakaoSdk(appkey)
      .then(() => {
        if (cancelled || !containerRef.current) return;
        const { kakao } = window;
        const center = new kakao.maps.LatLng(userLat, userLng);
        const map = new kakao.maps.Map(containerRef.current, {
          center,
          level: zoom,
        });
        mapRef.current = map;
        setReady(true);
      })
      .catch((e) => {
        if (cancelled) return;
        setError(e.message || "Kakao Maps SDK 로드 실패");
      });

    return () => {
      cancelled = true;
      // clean up markers/map references
      markersRef.current.forEach((m) => m.setMap(null));
      markersRef.current = [];
      userMarkerRef.current?.setMap(null);
      circleRef.current?.setMap(null);
      infoRef.current?.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [appkey, retryCount]);

  // ResizeObserver — 모바일 LIST↔MAP 토글이 display:none 으로만 가시성을 바꿔
  // 0×0 컨테이너에서 init된 SDK 캔버스가 그대로 멈추는 문제 대응.
  // iOS 주소창 토글로 인한 vh 변화, 회전, split view 진입 등도 함께 처리.
  useEffect(() => {
    if (!ready || !containerRef.current || !mapRef.current) return;
    const el = containerRef.current;

    const doRelayout = () => {
      if (!mapRef.current) return;
      const center = mapRef.current.getCenter();
      mapRef.current.relayout();
      mapRef.current.setCenter(center);
    };

    const raf = requestAnimationFrame(doRelayout);
    const ro = new ResizeObserver(doRelayout);
    ro.observe(el);

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
    };
  }, [ready]);

  // 사용자 위치 마커 + 반경 원 + 중심 동기화
  useEffect(() => {
    if (!ready || !mapRef.current) return;
    const { kakao } = window;
    const map = mapRef.current;
    const userPos = new kakao.maps.LatLng(userLat, userLng);

    // 중심 이동 (centerOn=user 인 경우)
    if (centerOn === "user") {
      map.setCenter(userPos);
    }

    // 사용자 마커 (Liquid Glass 컴퍼스-도트)
    if (userMarkerRef.current) {
      userMarkerRef.current.setMap(null);
    }
    const userOverlay = new kakao.maps.CustomOverlay({
      position: userPos,
      content: buildGlassMarkerHTML({ kind: "user" }),
      yAnchor: 0.5,
      xAnchor: 0.5,
    });
    userOverlay.setMap(map);
    userMarkerRef.current = userOverlay;

    // 반경 원
    if (circleRef.current) {
      circleRef.current.setMap(null);
    }
    if (showRadius) {
      const circle = new kakao.maps.Circle({
        center: userPos,
        radius: showRadius,
        strokeWeight: 1.5,
        strokeColor: "#e8593c",
        strokeOpacity: 0.8,
        fillColor: "#e8593c",
        fillOpacity: 0.06,
      });
      circle.setMap(map);
      circleRef.current = circle;

      // 반경에 맞게 줌 자동 조절
      // Kakao zoom level: 1=가까움 ~ 14=멀리
      const level =
        showRadius <= 300
          ? 3
          : showRadius <= 500
          ? 4
          : showRadius <= 1000
          ? 5
          : showRadius <= 2000
          ? 6
          : showRadius <= 3000
          ? 7
          : 8;
      map.setLevel(level);
    }
  }, [ready, userLat, userLng, showRadius, centerOn]);

  // 음식점 마커
  useEffect(() => {
    if (!ready || !mapRef.current) return;
    const { kakao } = window;
    const map = mapRef.current;

    // 기존 마커 제거
    markersRef.current.forEach((m) => m.setMap(null));
    markersRef.current = [];
    infoRef.current?.close();

    const withCoords = restaurants.filter(
      (r): r is Restaurant & { lat: number; lng: number } =>
        typeof r.lat === "number" && typeof r.lng === "number"
    );

    withCoords.forEach((r) => {
      const pos = new kakao.maps.LatLng(r.lat, r.lng);
      const isSelected = String(r.id) === String(selectedId);

      const overlay = new kakao.maps.CustomOverlay({
        position: pos,
        yAnchor: 1,
        xAnchor: 0.5,
        content: buildGlassMarkerHTML({
          kind: isSelected ? "restaurantSelected" : "restaurant",
          rid: r.id,
        }),
      });
      overlay.setMap(map);
      markersRef.current.push(overlay);

      // 클릭 이벤트: CustomOverlay 는 기본 click 없어서 DOM 이벤트로 처리
      setTimeout(() => {
        const el = document.querySelector<HTMLElement>(`[data-rid="${r.id}"]`);
        if (el) {
          el.onclick = () => {
            onSelect?.(String(r.id));
            // 인포윈도우 표시
            infoRef.current?.close();
            const info = new kakao.maps.InfoWindow({
              position: pos,
              content:
                `<div style="padding:8px 12px;font-size:12px;line-height:1.5;min-width:140px;">` +
                `<div style="font-weight:700;margin-bottom:2px;">${escapeHtml(r.name)}</div>` +
                `<div style="font-size:11px;opacity:0.75;">${escapeHtml(r.category ?? "기타")} · ${r.distance_m ?? "?"}m</div>` +
                (r.address
                  ? `<div style="font-size:10px;opacity:0.6;margin-top:4px;">${escapeHtml(r.address)}</div>`
                  : "") +
                `</div>`,
              removable: true,
            });
            info.open(map, new kakao.maps.Marker({ position: pos }));
            infoRef.current = info;
          };
        }
      }, 0);
    });

    // centerOn=selected 모드: 선택된 음식점으로 중심 이동
    if (centerOn === "selected" && selectedId) {
      const sel = withCoords.find((r) => String(r.id) === String(selectedId));
      if (sel) {
        map.setCenter(new kakao.maps.LatLng(sel.lat, sel.lng));
      }
    }
  }, [ready, restaurants, selectedId, onSelect, centerOn]);

  if (error) {
    return (
      <div
        className="bg-surface-1 border border-outline/15 rounded-sm flex items-center justify-center text-center text-text-tertiary text-sm"
        style={{ height }}
      >
        <div className="max-w-xs px-4">
          <div className="text-2xl mb-2">🗺</div>
          <div className="font-semibold text-error text-sm">{error}</div>
          <div
            className="text-[10px] mt-2 opacity-70 leading-relaxed"
            style={{ fontFamily: "var(--font-ko)" }}
          >
            확인 사항:
            <br />1. Kakao Developers → Web 플랫폼에 <b>http://localhost:3000</b> 등록
            <br />2. 앱 키가 <b>JavaScript 키</b>인지 확인 (REST API 키 아님)
            <br />3. 브라우저 콘솔에서 401/CORS 에러 확인
          </div>
          <button
            onClick={() => setRetryCount((c) => c + 1)}
            className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-bold uppercase border border-primary/40 text-primary rounded-sm hover:bg-primary/10 transition-colors"
          >
            🔄 재시도
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      style={{
        width: "100%",
        height,
        borderRadius: "1.25rem",
        overflow: "hidden",
        border: "1px solid color-mix(in srgb, var(--outline) 40%, transparent)",
      }}
    />
  );
}

// Small HTML escaper for InfoWindow content
function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
