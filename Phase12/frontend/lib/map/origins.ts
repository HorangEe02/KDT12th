/**
 * 출발지 프리셋 — server/client 양쪽에서 임포트 가능해야 하므로 "use client" 없이 순수 모듈.
 * 포팅 원본: src/ui/tabs/tab2_map.py _ORIGIN_PRESETS
 */
export const ORIGIN_PRESETS: Record<string, [number, number]> = {
  seoul: [37.5547, 126.9707],
  gangnam: [37.4979, 127.0276],
  suwon: [37.2657, 127.0009],
  daejeon: [36.3322, 127.4342],
};

export const ORIGIN_LABEL: Record<string, string> = {
  seoul: "서울역",
  gangnam: "강남역",
  suwon: "수원역",
  daejeon: "대전역",
};
