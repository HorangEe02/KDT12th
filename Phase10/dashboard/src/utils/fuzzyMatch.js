/**
 * 커스텀 퍼지 매칭 알고리즘
 * @param {string} query - 검색어
 * @param {string} text - 대상 텍스트
 * @returns {{ match: boolean, score: number, ranges: number[][] }}
 */
export default function fuzzyMatch(query, text) {
  if (!query) return { match: true, score: 0, ranges: [] };

  const q = query.toLowerCase();
  const t = text.toLowerCase();
  const ranges = [];
  let qi = 0, score = 0, consecutive = 0, lastMatchIdx = -2;

  for (let ti = 0; ti < t.length && qi < q.length; ti++) {
    if (t[ti] === q[qi]) {
      // 연속 매치 보너스
      consecutive = (ti === lastMatchIdx + 1) ? consecutive + 1 : 1;
      score += consecutive * 2;
      // 단어 경계 보너스 (_, 공백, 대소문자 변화 후)
      if (ti === 0 || t[ti - 1] === "_" || t[ti - 1] === " " || t[ti - 1] === "-") score += 5;
      // 매치 범위 기록
      if (ranges.length && ranges[ranges.length - 1][1] === ti) {
        ranges[ranges.length - 1][1] = ti + 1;
      } else {
        ranges.push([ti, ti + 1]);
      }
      lastMatchIdx = ti;
      qi++;
    }
  }

  const match = qi === q.length;
  // 정확 매치 보너스
  if (match && q === t) score += 100;
  // 접두사 매치 보너스
  if (match && t.startsWith(q)) score += 50;

  return { match, score: match ? score : 0, ranges };
}
