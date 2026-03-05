/**
 * ============================================================
 * MBTI 밈 예능 설문지 v2 — "너 T야?" 에디션
 * ============================================================
 * KNU 12기 Phase7 Numpy 미니프로젝트 (예능용 버전 v2)
 *
 * 한국 MBTI 밈 트렌드 기반 · 7점 리커트 척도
 * - E/I: 인싸/아싸 · 집순이/집돌이 밈
 * - S/N: 현실주의 vs 몽상가 · "사과 하면?" 밈
 * - T/F: "너 T야?" 밸런스 게임 · "T라 미숙해" 밈
 * - J/P: 계획충 vs 즉흥충 · 여행 엑셀 밈
 *
 * 사용법:
 *   1. https://script.google.com 접속
 *   2. 새 프로젝트 생성
 *   3. 이 코드를 전체 붙여넣기
 *   4. ▶ 실행 (createMBTIMemeSurveyV2 함수)
 *   5. Google 계정 권한 승인
 *   6. 실행 로그에서 생성된 Form URL 확인
 *
 * 총 46문항 | 예상 응답시간: 7~10분
 * ============================================================
 */

function createMBTIMemeSurveyV2() {
  // ── 폼 생성 ──
  const form = FormApp.create('MBTI 밈 테스트 v2 — "너 T야?" 에디션 🧠');
  form.setDescription(
    '🎯 당신의 진짜 MBTI를 밈으로 알아보는 시간!\n\n' +
    '"너 T야?", "사과 하면 뭐가 떠올라?", "여행 계획 엑셀로 짜는 편?"...\n' +
    '한국 MBTI 밈 트렌드를 반영한 예능형 설문입니다.\n\n' +
    '⏱️ 소요시간: 약 7~10분\n' +
    '📏 7점 척도: 자신에게 가까운 쪽으로 점수를 매겨주세요\n' +
    '🎯 정답 없음! 솔직한 첫 느낌으로 골라주세요\n' +
    '🔒 모든 응답은 익명 처리 · 연구 목적 사용\n\n' +
    '자, 시작합니다! 🚀'
  );
  form.setConfirmationMessage(
    '설문 완료! 🎉\n\n' +
    '당신의 답변은 MBTI & 혈액형 성격론 데이터 분석에 활용됩니다.\n' +
    '과연 MBTI는 과학일까, 밈일까? 결과를 기대해 주세요! 📊\n\n' +
    '"T라 미숙해~ 🎵"'
  );
  form.setAllowResponseEdits(false);
  form.setLimitOneResponsePerUser(false);
  form.setProgressBar(true);


  // ============================================================
  //  섹션 1: 기본 정보 (5문항)
  // ============================================================
  form.addSectionHeaderItem()
    .setTitle('📌 기본 정보')
    .setHelpText('가볍게 시작합니다!');

  // Q1. MBTI
  form.addListItem()
    .setTitle('1. 당신의 MBTI는? (모르면 "모름" 선택!)')
    .setChoiceValues([
      'ISTJ', 'ISFJ', 'INFJ', 'INTJ',
      'ISTP', 'ISFP', 'INFP', 'INTP',
      'ESTP', 'ESFP', 'ENFP', 'ENTP',
      'ESTJ', 'ESFJ', 'ENFJ', 'ENTJ',
      '모름/검사 안 해봄'
    ])
    .setRequired(true);

  // Q2. 혈액형
  form.addMultipleChoiceItem()
    .setTitle('2. 혈액형은?')
    .setChoiceValues(['A형', 'B형', 'O형', 'AB형', '모름'])
    .setRequired(true);

  // Q3. 성별
  form.addMultipleChoiceItem()
    .setTitle('3. 성별')
    .setChoiceValues(['남성', '여성', '기타/응답 안 함'])
    .setRequired(true);

  // Q4. 나이대
  form.addMultipleChoiceItem()
    .setTitle('4. 나이대')
    .setChoiceValues(['10대', '20대', '30대', '40대 이상'])
    .setRequired(true);

  // Q5. MBTI 검사 방법
  form.addMultipleChoiceItem()
    .setTitle('5. MBTI를 어떻게 알게 됐나요?')
    .setChoiceValues([
      '16Personalities 같은 인터넷 무료 테스트',
      '공인 기관 정식 검사',
      '친구가 "너 이거야" 해서 그냥 받아들임',
      'MBTI 밈 보고 "아 나 이거다" 하고 자가진단',
      '모름/관심 없음'
    ])
    .setRequired(true);


  // ============================================================
  //  섹션 2: E/I — 인싸인가 아싸인가 (9문항)
  //  ─ 7점 리커트: 1=전혀 아니다 / 7=매우 그렇다
  //  ─ 밈 키워드: 집순이/집돌이, 약속 취소 개꿀, 인싸/아싸
  //
  //  채점 방향:
  //    I 방향 문항(동의할수록 I): Q6, Q7, Q9, Q10, Q11, Q13, Q14
  //    E 방향 문항(동의할수록 E): Q8, Q12
  // ============================================================
  form.addSectionHeaderItem()
    .setTitle('🏠 라운드 1: 인싸인가 아싸인가 — E vs I')
    .setHelpText(
      '당신의 에너지 충전 방식은? 집순이/집돌이 감별기!\n\n' +
      '각 문항에 대해 자신에게 얼마나 해당하는지 7점 척도로 답해주세요.\n' +
      '1 = 전혀 아니다 / 4 = 보통이다 / 7 = 매우 그렇다'
    );

  // Q6 (I 방향)
  form.addScaleItem()
    .setTitle('6. 주말을 침대에서 보내고 싶다.')
    .setHelpText('집이 최고지... 🛏️')
    .setBounds(1, 7)
    .setLabels('전혀 아니다', '매우 그렇다')
    .setRequired(true);

  // Q7 (I 방향)
  form.addScaleItem()
    .setTitle('7. 외출 준비를 다 한 상황에서 약속이 취소됐다는 연락을 받으면 은근히 좋다.')
    .setHelpText('"약속 취소 = 개꿀" 밈의 주인공은 나? 😏')
    .setBounds(1, 7)
    .setLabels('전혀 아니다', '매우 그렇다')
    .setRequired(true);

  // Q8 (I 방향)
  form.addScaleItem()
    .setTitle('8. 주중에는 회사(실외)였으니 주말엔 집에 있어야 한다.')
    .setHelpText('주말엔 집에서 에너지 충전! 🏡')
    .setBounds(1, 7)
    .setLabels('전혀 아니다', '매우 그렇다')
    .setRequired(true);

  // Q9 (I 방향)
  form.addScaleItem()
    .setTitle('9. 밖에서 잘 놀고 난 다음에 "나는 이제 집에 가서 혼자 쉬면서 충전해야지" 라는 생각이 든다.')
    .setHelpText('"재밌었다! 근데 이제 집 가야지..." 🔋')
    .setBounds(1, 7)
    .setLabels('전혀 아니다', '매우 그렇다')
    .setRequired(true);

  // Q10 (I 방향)
  form.addScaleItem()
    .setTitle('10. 몇 개월 동안 집 밖에 안 나가도 잘 살 수 있다.')
    .setHelpText('궁극의 집순이/집돌이 테스트 🏡')
    .setBounds(1, 7)
    .setLabels('전혀 아니다', '매우 그렇다')
    .setRequired(true);

  // Q11 (I 방향)
  form.addScaleItem()
    .setTitle('11. 당일 갑자기 잡히는 약속이 힘들다.')
    .setHelpText('"갑자기?! 마음의 준비가..." 😰')
    .setBounds(1, 7)
    .setLabels('전혀 아니다', '매우 그렇다')
    .setRequired(true);

  // Q13 (I 방향)
  form.addScaleItem()
    .setTitle('12. 밖에서 볼일이 많으면 하루에 몰아서 끝낸다.')
    .setHelpText('효율적으로 끝내고 빨리 집에! 🏃')
    .setBounds(1, 7)
    .setLabels('전혀 아니다', '매우 그렇다')
    .setRequired(true);

  // Q14 (I 방향)
  form.addScaleItem()
    .setTitle('13. 새로운 모임에 참여하면 집에 빨리 가고 싶다.')
    .setHelpText('"언제 끝나지..." 👀')
    .setBounds(1, 7)
    .setLabels('전혀 아니다', '매우 그렇다')
    .setRequired(true);

  // Q15 (I 방향)
  form.addScaleItem()
    .setTitle('14. 빈 강의실에 앉을 때 벽 근처에 앉는다.')
    .setHelpText('구석자리 = 내 안식처 🪑')
    .setBounds(1, 7)
    .setLabels('전혀 아니다', '매우 그렇다')
    .setRequired(true);


  // ============================================================
  //  섹션 3: S/N — 현실주의자인가 몽상가인가 (9문항)
  //  ─ 7점 양극 척도: 1=S(현실적 반응) / 7=N(상상·직관적 반응)
  //  ─ 밈 키워드: "사과 하면?", 극단적 상상, 세계관 몽상
  // ============================================================
  form.addSectionHeaderItem()
    .setTitle('🔮 라운드 2: 현실주의자인가 몽상가인가 — S vs N')
    .setHelpText(
      '"사과 하면 떠오르는 것은?" — 이 질문 하나로 S/N이 갈린다는 유명한 밈!\n\n' +
      '아래 상황에서 자신의 반응이 ①번(현실적)과 ⑦번(상상·직관적) 중\n' +
      '어느 쪽에 더 가까운지 7점 척도로 답해주세요.'
    );

  // Q15 (S↔N)
  form.addScaleItem()
    .setTitle('15. 과제 있는데 깜빡했을 때, 나의 반응은?')
    .setHelpText(
      '① "너무 하기 싫다... 시간을 되돌리고 싶어.."\n' +
      '⑦ "과제 못 내고 사람들에게 망신 당하다가 자퇴하는 극단적인 상상을 함"'
    )
    .setBounds(1, 7)
    .setLabels('① 현실적 반응', '⑦ 극단적 상상')
    .setRequired(true);

  // Q16 (S↔N)
  form.addScaleItem()
    .setTitle('16. 축제를 구경할 때, 나는?')
    .setHelpText(
      '① 공연을 봄 (눈앞의 무대에 집중)\n' +
      '⑦ 내가 참가해서 노래를 너무 잘해서 사람들 다 놀라고 유튜브 난리나는 상상을 함'
    )
    .setBounds(1, 7)
    .setLabels('① 지금 이 순간', '⑦ 상상의 나라')
    .setRequired(true);

  // Q17 (S↔N)
  form.addScaleItem()
    .setTitle('17. 실제로 내가 하는 망상에 더 가까운 것은?')
    .setHelpText(
      '① 대학에 들어간 나 / 대기업에 입사한 나 / 사람들에게 인기 있는 나\n' +
      '⑦ 주먹 하나로 학교 짱 먹은 나 / 초능력을 가지게 된 나 / 내가 만든 세계관에 들어간 나'
    )
    .setBounds(1, 7)
    .setLabels('① 현실 기반 상상', '⑦ 판타지급 상상')
    .setRequired(true);

  // Q18 (S↔N)
  form.addScaleItem()
    .setTitle('18. 전공/직업 관련 드라마·영화를 보면?')
    .setHelpText(
      '① "저기 고증 좀 잘 안 되어 있는 듯?"\n' +
      '⑦ "내가 작가였다면 저기서 열 받아서 옥상 가서 울다가 떨어져서 재벌집 세 번째 아들로 환생하는 스토리로 짤 듯?"'
    )
    .setBounds(1, 7)
    .setLabels('① 고증/디테일 체크', '⑦ 2차 창작 시작')
    .setRequired(true);

  // Q19 (S↔N)
  form.addScaleItem()
    .setTitle('19. 성과가 좋지 않을 때 드는 생각은?')
    .setHelpText(
      '① "왜 성과가 안 좋지? ~한 점이 별로인가?"\n' +
      '⑦ "이대로 성과가 바닥을 치면 회의실 불려가서 욕 먹고 해고 당하고 거지가 되어 길거리에 나앉겠지?"'
    )
    .setBounds(1, 7)
    .setLabels('① 원인 분석', '⑦ 파국적 상상')
    .setRequired(true);

  // Q20 (S↔N)
  form.addScaleItem()
    .setTitle('20. 버스에 앉아 창밖을 바라보며 하는 생각은?')
    .setHelpText(
      '① "풍경 예쁘네. 근데 언제 도착하지?"\n' +
      '⑦ "매일 이 버스를 운전하는 기사님은 지루하지 않을까?"'
    )
    .setBounds(1, 7)
    .setLabels('① 현실적 관찰', '⑦ 타인/세계 상상')
    .setRequired(true);

  // Q21 (S↔N) — 유명 밈!
  form.addScaleItem()
    .setTitle('21. 🍎 "사과" 하면 떠오르는 것은?')
    .setHelpText(
      '① 빨갛다, 둥글다, 새콤달콤, 맛있다\n' +
      '⑦ 백설공주, 뉴턴, 스티브 잡스, 아이폰'
    )
    .setBounds(1, 7)
    .setLabels('① 감각적 묘사', '⑦ 연상·상징')
    .setRequired(true);

  // Q22 (S↔N)
  form.addScaleItem()
    .setTitle('22. 시험이 다가오는데 공부가 손에 안 잡힌다면?')
    .setHelpText(
      '① 벼락치기 하는 방법, 3일 만에 합격한 후기 찾아보기\n' +
      '⑦ "시험 없는 세상은 어떨까?" 상상에 빠짐'
    )
    .setBounds(1, 7)
    .setLabels('① 실전 해결책 탐색', '⑦ 이상 세계 상상')
    .setRequired(true);

  // Q23 (S↔N)
  form.addScaleItem()
    .setTitle('23. 소풍 전 날 자기 전에 드는 생각은?')
    .setHelpText(
      '① "옷 뭐 입지? 도시락 뭐 싸가지?"\n' +
      '⑦ "버스 사고나면 어쩌지?"'
    )
    .setBounds(1, 7)
    .setLabels('① 준비 체크리스트', '⑦ 만약의 시나리오')
    .setRequired(true);


  // ============================================================
  //  섹션 4: T/F — "너 T야?" 밸런스 게임 (9문항)
  //  ─ 7점 양극 척도: 1=T(논리·해결 중심) / 7=F(감정·공감 중심)
  //  ─ 밈 키워드: "너 T야?", 아이스T, T라 미숙해 🎵
  // ============================================================
  form.addSectionHeaderItem()
    .setTitle('🔥 라운드 3: "너 T야?" 밸런스 게임 — T vs F')
    .setHelpText(
      '"너 T야?" — 2023~2025 대한민국 최강 MBTI 밈!\n' +
      '밈고리즘에서 시작된 이 질문, 이제 직접 확인해봅시다.\n\n' +
      '아래 상황에서 자신의 반응이 ①번(논리·해결)과 ⑦번(감정·공감) 중\n' +
      '어느 쪽에 더 가까운지 7점 척도로 답해주세요.\n\n' +
      '🎵 "T라 미숙해~ T라 미숙해~ 티라미수 케익~"'
    );

  // Q24 (T↔F)
  form.addScaleItem()
    .setTitle('24. 친구가 고민거리를 얘기하면, 나의 반응은?')
    .setHelpText(
      '① 일단 듣고 해결 방법을 알려준다\n' +
      '⑦ 고민거리에 공감한다'
    )
    .setBounds(1, 7)
    .setLabels('① 해결책 제시', '⑦ 공감 먼저')
    .setRequired(true);

  // Q25 (T↔F)
  form.addScaleItem()
    .setTitle('25. "이러면 아무도 너 안 좋아해"라는 말을 들었을 때 반응은?')
    .setHelpText(
      '① "그래서? 어쩌라고"\n' +
      '⑦ 속상해함'
    )
    .setBounds(1, 7)
    .setLabels('① 담담한 반응', '⑦ 감정적 반응')
    .setRequired(true);

  // Q26 (T↔F)
  form.addScaleItem()
    .setTitle('26. "모르면서 아는 척 하지마"라는 말을 들었을 때 반응은?')
    .setHelpText(
      '① "아니까 말한 건데? 모르는데 어떻게 말해"\n' +
      '⑦ "말 너무 심하게 한다,,"'
    )
    .setBounds(1, 7)
    .setLabels('① 논리적 반박', '⑦ 감정적 상처')
    .setRequired(true);

  // Q27 (T↔F)
  form.addScaleItem()
    .setTitle('27. 친구가 "차 사고 났어,,"라고 연락했다. 첫 반응은?')
    .setHelpText(
      '① "보험사 불렀어? 누가 사고 낸 건데"\n' +
      '⑦ "괜찮아? 많이 다쳤어?"'
    )
    .setBounds(1, 7)
    .setLabels('① 상황 파악', '⑦ 안부 먼저')
    .setRequired(true);

  // Q28 (T↔F)
  form.addScaleItem()
    .setTitle('28. "대박 정말 좋은데? 열심히 안 했는데 이 정도면 너 재능 있다!" — 이 말을 들으면?')
    .setHelpText(
      '① 재능 있다는 말에 꽂힘 (긍정 수용)\n' +
      '⑦ 내가 열심히 안 했다고 생각하나? (숨겨진 의미에 반응)'
    )
    .setBounds(1, 7)
    .setLabels('① 팩트에 집중', '⑦ 뉘앙스에 집중')
    .setRequired(true);

  // Q29 (T↔F)
  form.addScaleItem()
    .setTitle('29. 칭찬을 할 때, 나의 스타일은?')
    .setHelpText(
      '① 구체적으로 어떻게 잘했는지 객관적인 부분을 칭찬\n' +
      '⑦ 그 사람의 상황을 공감하고 이해해주는 칭찬'
    )
    .setBounds(1, 7)
    .setLabels('① 객관적 칭찬', '⑦ 공감형 칭찬')
    .setRequired(true);

  // Q30 (T↔F)
  form.addScaleItem()
    .setTitle('30. 친구/연인이 "나 살 쪘지?"라고 물었을 때 반응은?')
    .setHelpText(
      '① "응 좀 찐 거 같다"\n' +
      '⑦ "아니 뭔 소리야 지금 너무 이쁜데"'
    )
    .setBounds(1, 7)
    .setLabels('① 솔직한 팩트', '⑦ 감성 케어')
    .setRequired(true);

  // Q31 (T↔F)
  form.addScaleItem()
    .setTitle('31. 친구가 "너를 위해 죽을 수 있어"라고 말했다.')
    .setHelpText(
      '① "그럼 죽어" (논리적으로 불가능한 말에 반응)\n' +
      '⑦ "그러지마..." (안 좋은 말 못함)'
    )
    .setBounds(1, 7)
    .setLabels('① 팩트 폭격', '⑦ 감정 보호')
    .setRequired(true);

  // Q32 (T↔F) — 메타 질문!
  form.addScaleItem()
    .setTitle('32. 이 설문을 해달라고 했을 때, 솔직한 속마음은?')
    .setHelpText(
      '① "이거 굳이 해줘야 하나?"\n' +
      '⑦ "그래도 해줘야지~"'
    )
    .setBounds(1, 7)
    .setLabels('① 귀찮음 솔직', '⑦ 의리 챙김')
    .setRequired(true);


  // ============================================================
  //  섹션 5: J/P — 계획충인가 즉흥충인가 (9문항)
  //  ─ 7점 양극 척도: 1=J(계획·체계형) / 7=P(즉흥·유연형)
  //  ─ 밈 키워드: 여행 엑셀, 벼락치기, 마감 전날 아드레날린
  // ============================================================
  form.addSectionHeaderItem()
    .setTitle('📋 라운드 4: 계획충인가 즉흥충인가 — J vs P')
    .setHelpText(
      '여행 계획을 엑셀로 짜는 J vs 포스트잇 하나로 끝내는 P!\n' +
      '"마감 전날이 진짜 리얼 시작" 인정?\n\n' +
      '아래 상황에서 자신이 ①번(계획·체계)과 ⑦번(즉흥·유연) 중\n' +
      '어느 쪽에 더 가까운지 7점 척도로 답해주세요.'
    );

  // Q33 (J↔P)
  form.addScaleItem()
    .setTitle('33. 여행 준비 스타일')
    .setHelpText(
      '① 엑셀에 분 단위 일정과 예산, 플랜 B까지 완벽히 짜야 직성이 풀린다\n' +
      '⑦ 일단 당일 아침에 기차표만 끊고 출발, 발길 닿는 대로 간다'
    )
    .setBounds(1, 7)
    .setLabels('① 엑셀 완벽 계획', '⑦ 발길 닿는 대로')
    .setRequired(true);

  // Q34 (J↔P)
  form.addScaleItem()
    .setTitle('34. 스마트폰 알림 및 바탕화면 상태')
    .setHelpText(
      '① 카톡/메일의 빨간 점을 못 견디고 다 읽음 처리, 앱은 폴더별 정리\n' +
      '⑦ 안 읽은 메시지 999+는 기본, 앱들은 다운로드한 순서대로 널브러져 있음'
    )
    .setBounds(1, 7)
    .setLabels('① 0개 알림 유지', '⑦ 999+ 기본')
    .setRequired(true);

  // Q35 (J↔P)
  form.addScaleItem()
    .setTitle('35. 꼼꼼히 알아본 식당이 하필 "임시 휴업"일 때')
    .setHelpText(
      '① 멘붕이 오지만, 이럴 줄 알고 미리 준비해 둔 플랜 B 식당으로 즉시 이동\n' +
      '⑦ 주변을 두리번거리다 간판이 맛있어 보이는 옆 식당으로 쿨하게 들어감'
    )
    .setBounds(1, 7)
    .setLabels('① 플랜 B 가동', '⑦ 즉석 발견')
    .setRequired(true);

  // Q36 (J↔P)
  form.addScaleItem()
    .setTitle('36. 일주일 뒤 마감인 중요한 과제/업무')
    .setHelpText(
      '① 마감일 역순으로 스케줄을 쪼개 하루 할당량을 정해 미리미리 완성\n' +
      '⑦ 마감 전날 새벽, 아드레날린을 폭발시키며 엄청난 집중력으로 벼락치기'
    )
    .setBounds(1, 7)
    .setLabels('① 미리미리 완성', '⑦ 전날 벼락치기')
    .setRequired(true);

  // Q37 (J↔P)
  form.addScaleItem()
    .setTitle('37. 여행 짐 싸기')
    .setHelpText(
      '① 며칠 전부터 체크리스트를 만들고 시뮬레이션을 돌리며 빠짐없이 챙겨둠\n' +
      '⑦ 출발 당일 아침이나 전날 밤, 눈에 보이는 옷들을 대충 캐리어에 쑤셔 넣음'
    )
    .setBounds(1, 7)
    .setLabels('① 체크리스트 완비', '⑦ 대충 쑤셔 넣기')
    .setRequired(true);

  // Q38 (J↔P)
  form.addScaleItem()
    .setTitle('38. 마트 장보기 스타일')
    .setHelpText(
      '① 메모장에 사야 할 물건 리스트를 미리 적어두고 딱 그것만 사서 나옴\n' +
      '⑦ 구경하다가 맛있어 보이는 신상 과자나 1+1 행사 상품을 홀린 듯 장바구니에 담음'
    )
    .setBounds(1, 7)
    .setLabels('① 리스트대로만', '⑦ 충동 장바구니')
    .setRequired(true);

  // Q39 (J↔P)
  form.addScaleItem()
    .setTitle('39. 내 방/책상의 평소 상태')
    .setHelpText(
      '① 사용한 물건은 즉시 제자리에 두며, 항상 각 잡힌 깔끔함을 유지\n' +
      '⑦ 남들이 보기엔 혼돈의 카오스지만, 그 무질서 속에서도 나만의 룰이 있어 물건을 다 찾음'
    )
    .setBounds(1, 7)
    .setLabels('① 각 잡힌 정리', '⑦ 나만의 카오스')
    .setRequired(true);

  // Q40 (J↔P)
  form.addScaleItem()
    .setTitle('40. 유튜브 레시피로 새로운 요리 도전하기')
    .setHelpText(
      '① 물 350ml, 간장 1.5스푼 등 영상에 나온 정량과 순서를 오차 없이 지킴\n' +
      '⑦ "간장은 대충 이 정도?" 눈대중과 나의 미각을 믿고 느낌대로 양념을 넣음'
    )
    .setBounds(1, 7)
    .setLabels('① 정량·정순서', '⑦ 감으로 대충')
    .setRequired(true);

  // Q41 (J↔P)
  form.addScaleItem()
    .setTitle('41. 주말을 앞둔 금요일 밤 머릿속')
    .setHelpText(
      '① 토요일 기상 시간부터 친구 만나는 시간, 쉴 시간까지 주말 타임라인이 이미 완성\n' +
      '⑦ 내일 알람을 다 끄고 늦잠을 푹 잔 뒤, 일어나서 기분 내키는 대로 할 일을 정함'
    )
    .setBounds(1, 7)
    .setLabels('① 타임라인 완성', '⑦ 알람 OFF 늦잠')
    .setRequired(true);


  // ============================================================
  //  섹션 6: 보너스 — MBTI & 혈액형 밈 인식 (5문항)
  // ============================================================
  form.addSectionHeaderItem()
    .setTitle('🎯 보너스 라운드: MBTI & 혈액형, 진짜 어떻게 생각해?')
    .setHelpText('마지막! 밈에 대한 당신의 솔직한 생각을 알려주세요.');

  // Q42
  form.addScaleItem()
    .setTitle('42. MBTI가 실제 성격을 잘 반영한다고 생각하시나요?')
    .setHelpText('1 = 전혀 아니다 (그냥 밈이지) ~ 7 = 거의 정확하다')
    .setBounds(1, 7)
    .setLabels('그냥 밈이지', '거의 정확함')
    .setRequired(true);

  // Q43
  form.addScaleItem()
    .setTitle('43. 혈액형으로 성격을 알 수 있다고 생각하시나요?')
    .setHelpText('1 = 전혀 아니다 (과학적 근거 없음) ~ 7 = 꽤 맞다고 봄')
    .setBounds(1, 7)
    .setLabels('근거 없음', '꽤 맞다고 봄')
    .setRequired(true);

  // Q44
  form.addMultipleChoiceItem()
    .setTitle('44. "너 T야?" 라는 말을 실제로 써본 적 있나요?')
    .setChoiceValues([
      '자주 쓴다 (일상 밈)',
      '가끔 쓴다',
      '들어는 봤는데 안 써봄',
      '처음 들어봄'
    ])
    .setRequired(true);

  // Q45
  form.addMultipleChoiceItem()
    .setTitle('45. 상대방의 MBTI를 알면 대하는 태도가 바뀌나요?')
    .setChoiceValues([
      '많이 바뀜 (MBTI 참고해서 대화함)',
      '약간 바뀜 (아 이래서 그랬구나~ 정도)',
      '바뀌지 않음 (참고만 하고 크게 신경 안 씀)',
      'MBTI 자체에 관심 없음'
    ])
    .setRequired(true);

  // Q46
  form.addMultipleChoiceItem()
    .setTitle('46. 최종 질문! MBTI & 혈액형 성격론, 당신의 진짜 생각은?')
    .setChoiceValues([
      '과학적 근거 있음! 진지하게 활용할 수 있다',
      '완전 과학은 아니지만 꽤 맞는 부분이 있다',
      '재미로는 좋지만 진지하게 믿진 않는다',
      '완전 미신이라고 생각한다',
      '잘 모르겠다 / 관심 없다'
    ])
    .setRequired(true);


  // ============================================================
  //  마무리
  // ============================================================
  form.addSectionHeaderItem()
    .setTitle('🎉 설문 완료!')
    .setHelpText('수고하셨습니다! 마지막으로 한마디!');

  form.addParagraphTextItem()
    .setTitle('자유 의견: MBTI나 혈액형에 대해 하고 싶은 말이 있다면? (선택)')
    .setHelpText('밈, 경험담, 불만, 웃긴 에피소드 뭐든 환영! 😄')
    .setRequired(false);


  // ── 응답 스프레드시트 자동 연결 ──
  const ss = SpreadsheetApp.create('MBTI_밈_설문v2_응답_데이터');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  // ── 결과 출력 ──
  const formUrl = form.getPublishedUrl();
  const editUrl = form.getEditUrl();
  const ssUrl = ss.getUrl();

  Logger.log('============================================');
  Logger.log('🎉 MBTI 밈 예능 설문 v2 생성 완료!');
  Logger.log('============================================');
  Logger.log('📋 설문 응답 URL: ' + formUrl);
  Logger.log('✏️ 설문 편집 URL: ' + editUrl);
  Logger.log('📊 응답 스프레드시트 URL: ' + ssUrl);
  Logger.log('============================================');
  Logger.log('총 46문항 + 자유의견 1개');
  Logger.log('');
  Logger.log('  📌 기본 정보:          5문항  (Q1-Q5)');
  Logger.log('  🏠 E/I 인싸/아싸:      9문항  (Q6-Q14)   7점 리커트');
  Logger.log('  🔮 S/N 현실/몽상:      9문항  (Q15-Q23)  7점 양극 척도');
  Logger.log('  🔥 T/F "너 T야?":      9문항  (Q24-Q32)  7점 양극 척도');
  Logger.log('  📋 J/P 계획/즉흥:      9문항  (Q33-Q41)  7점 양극 척도');
  Logger.log('  🎯 보너스 밈 인식:     5문항  (Q42-Q46)');
  Logger.log('');
  Logger.log('  채점 안내:');
  Logger.log('    E/I: 전체 I방향 문항(Q6~Q14) — 높을수록 I (전부 역채점)');
  Logger.log('    S/N: 1=S(현실적) ↔ 7=N(상상적)');
  Logger.log('    T/F: 1=T(논리적) ↔ 7=F(감정적)');
  Logger.log('    J/P: 1=J(계획형) ↔ 7=P(즉흥형)');
  Logger.log('============================================');

  return {
    formUrl: formUrl,
    editUrl: editUrl,
    spreadsheetUrl: ssUrl
  };
}
