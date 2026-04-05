import { useState, useEffect, useCallback } from "react";

/**
 * 제조 패턴을 모사하는 실시간 데이터 시뮬레이션 훅
 * @param {number} len - 데이터 포인트 수
 * @param {number} interval - 업데이트 간격(ms)
 * @returns {{ data: Array, paused: boolean, togglePause: Function, range: string, setRange: Function }}
 */
const useSimStream = (len = 30, interval = 1500) => {
  const [paused, setPaused] = useState(false);
  const [range, setRange] = useState("24H");

  const generateInitial = useCallback(() => {
    const now = new Date();
    return Array.from({ length: len }, (_, i) => {
      const t = new Date(now.getTime() - (len - 1 - i) * 60000 * (range === "1H" ? 2 : range === "6H" ? 12 : range === "7D" ? 336 : 48));
      const hour = t.getHours();
      // 교대 근무 패턴: 주간(8-16) 높은 생산성, 야간(0-6) 낮은 생산성
      const shiftFactor = (hour >= 8 && hour <= 16) ? 1.0 : (hour >= 17 || hour <= 6) ? 0.85 : 0.92;
      const yieldBase = 88 + Math.random() * 8 * shiftFactor;
      const defectBase = 2 + Math.random() * 4 * (2 - shiftFactor);
      return {
        time: t.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" }),
        yield: Math.round(yieldBase * 10) / 10,
        defect: Math.round(defectBase * 10) / 10,
      };
    });
  }, [len, range]);

  const [data, setData] = useState(generateInitial);

  useEffect(() => {
    setData(generateInitial());
  }, [range, generateInitial]);

  useEffect(() => {
    if (paused) return;
    const id = setInterval(() => {
      setData(prev => {
        const last = prev[prev.length - 1];
        const now = new Date();
        const hour = now.getHours();
        const shiftFactor = (hour >= 8 && hour <= 16) ? 1.0 : 0.88;
        const newYield = Math.max(75, Math.min(99, last.yield + (Math.random() - 0.48) * 3 * shiftFactor));
        const newDefect = Math.max(0.5, Math.min(12, last.defect + (Math.random() - 0.52) * 1.5));
        return [...prev.slice(1), {
          time: now.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" }),
          yield: Math.round(newYield * 10) / 10,
          defect: Math.round(newDefect * 10) / 10,
        }];
      });
    }, interval);
    return () => clearInterval(id);
  }, [paused, interval]);

  const togglePause = useCallback(() => setPaused(p => !p), []);

  return { data, paused, togglePause, range, setRange };
};

export default useSimStream;
