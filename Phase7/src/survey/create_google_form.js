/**
 * ============================================================
 * MBTI & 혈액형: 과학인가 미신인가 — 설문 자동 생성 스크립트
 * ============================================================
 * KNU 12기 Phase7 Numpy 미니프로젝트
 *
 * 사용법:
 *   1. https://script.google.com 접속
 *   2. 새 프로젝트 생성
 *   3. 이 코드를 전체 붙여넣기
 *   4. ▶ 실행 (createMBTIBloodTypeSurvey 함수)
 *   5. Google 계정 권한 승인
 *   6. 실행 로그에서 생성된 Form URL 확인
 *
 * 총 48문항 | 예상 응답시간: 8~12분
 * ============================================================
 */

function createMBTIBloodTypeSurvey() {
  // ── 폼 생성 ──
  const form = FormApp.create('MBTI & 혈액형: 과학인가 미신인가 — 성격 유형 설문조사');
  form.setDescription(
    '안녕하세요! 이 설문은 KNU 12기 데이터 분석 프로젝트의 일환으로,\n' +
    'MBTI 성격 유형과 혈액형 성격론에 대한 여러분의 생각과 성격 특성을 조사합니다.\n\n' +
    '📋 소요시간: 약 8~12분\n' +
    '🔒 개인정보: 모든 응답은 익명으로 처리되며 연구 목적으로만 사용됩니다.\n' +
    '📊 결과 활용: 통계 분석을 통해 성격 유형론의 과학적 근거를 검증합니다.\n\n' +
    '정답이 없는 설문이므로, 편안하게 평소 자신의 모습에 가장 가까운 답을 선택해 주세요.\n' +
    '감사합니다! 🙏'
  );
  form.setConfirmationMessage(
    '설문에 참여해 주셔서 감사합니다! 🎉\n' +
    '응답은 익명으로 처리되며, 분석 결과는 추후 공유될 예정입니다.'
  );
  form.setAllowResponseEdits(false);
  form.setLimitOneResponsePerUser(false);
  form.setProgressBar(true);

  // ============================================================
  //  섹션 1: 기본 정보 (6문항)
  // ============================================================
  form.addSectionHeaderItem()
    .setTitle('📌 섹션 1: 기본 정보')
    .setHelpText('먼저 간단한 기본 정보를 입력해 주세요.');

  // Q1. 성별
  form.addMultipleChoiceItem()
    .setTitle('1. 귀하의 성별은 무엇입니까?')
    .setChoiceValues(['남성', '여성', '기타', '응답하고 싶지 않음'])
    .setRequired(true);

  // Q2. 나이대
  form.addMultipleChoiceItem()
    .setTitle('2. 귀하의 나이대는 어떻게 되십니까?')
    .setChoiceValues(['10대 (15-19세)', '20대 (20-29세)', '30대 (30-39세)', '40대 (40-49세)', '50대 이상'])
    .setRequired(true);

  // Q3. 교육수준
  form.addMultipleChoiceItem()
    .setTitle('3. 귀하의 최종 학력은 무엇입니까?')
    .setChoiceValues(['고등학교 졸업 이하', '대학교 재학 중', '대학교 졸업', '대학원 재학/졸업 이상'])
    .setRequired(true);

  // Q4. 혈액형
  form.addMultipleChoiceItem()
    .setTitle('4. 귀하의 혈액형은 무엇입니까?')
    .setChoiceValues(['A형', 'B형', 'O형', 'AB형', '모름'])
    .setRequired(true);

  // Q5. MBTI 유형
  form.addListItem()
    .setTitle('5. 귀하가 알고 있는 자신의 MBTI 유형은 무엇입니까?')
    .setHelpText('MBTI 검사를 받아본 적이 없다면 "모름/검사 안 해봄"을 선택해 주세요.')
    .setChoiceValues([
      'ISTJ', 'ISFJ', 'INFJ', 'INTJ',
      'ISTP', 'ISFP', 'INFP', 'INTP',
      'ESTP', 'ESFP', 'ENFP', 'ENTP',
      'ESTJ', 'ESFJ', 'ENFJ', 'ENTJ',
      '모름/검사 안 해봄'
    ])
    .setRequired(true);

  // Q6. MBTI 검사 경험
  form.addMultipleChoiceItem()
    .setTitle('6. MBTI 성격 검사를 어떤 방식으로 해보셨나요?')
    .setChoiceValues([
      '공인 기관/전문가를 통한 공식 검사 (MBTI Form M/Q 등)',
      '인터넷 무료 검사 (16Personalities, 다른 온라인 테스트 등)',
      '둘 다 해봄',
      '검사한 적 없음'
    ])
    .setRequired(true);


  // ============================================================
  //  섹션 2: 성격 측정 — 외향(E) / 내향(I) 차원 (8문항)
  // ============================================================
  form.addSectionHeaderItem()
    .setTitle('🧠 섹션 2: 성격 측정 — 에너지 방향')
    .setHelpText(
      '각 문항을 읽고, 평소 자신의 모습에 얼마나 해당하는지 7점 척도로 답해 주세요.\n' +
      '1 = 전혀 아니다 / 4 = 보통이다 / 7 = 매우 그렇다'
    );

  const likert7 = ['1 (전혀 아니다)', '2', '3', '4 (보통이다)', '5', '6', '7 (매우 그렇다)'];

  const eiQuestions = [
    '7. 새로운 사람들을 만나면 에너지가 충전되는 느낌이다.',
    '8. 혼자만의 시간을 보내는 것이 휴식이 된다.',
    '9. 모임이나 파티에서 먼저 다가가서 대화를 시작하는 편이다.',
    '10. 여러 명과 함께하는 것보다 소수의 친한 친구와 있는 것이 편하다.',
    '11. 생각을 말로 표현하면서 정리하는 편이다.',
    '12. 중요한 결정을 내리기 전에 혼자 깊이 생각하는 시간이 필요하다.',
    '13. 조용한 환경보다 사람이 많은 활기찬 환경에서 더 잘 집중된다.',
    '14. 처음 보는 사람에게 자신의 이야기를 쉽게 하는 편이다.'
  ];

  eiQuestions.forEach(q => {
    form.addScaleItem()
      .setTitle(q)
      .setBounds(1, 7)
      .setLabels('전혀 아니다', '매우 그렇다')
      .setRequired(true);
  });


  // ============================================================
  //  섹션 3: 성격 측정 — 감각(S) / 직관(N) 차원 (8문항)
  // ============================================================
  form.addSectionHeaderItem()
    .setTitle('🧠 섹션 3: 성격 측정 — 인식 방식')
    .setHelpText(
      '평소 자신의 모습에 얼마나 해당하는지 7점 척도로 답해 주세요.\n' +
      '1 = 전혀 아니다 / 4 = 보통이다 / 7 = 매우 그렇다'
    );

  const snQuestions = [
    '15. 현실적이고 실용적인 정보에 더 관심이 있다.',
    '16. 미래의 가능성과 상상의 세계에 대해 자주 생각한다.',
    '17. 세부 사항과 구체적인 사실에 주의를 기울이는 편이다.',
    '18. 전체적인 큰 그림이나 패턴을 먼저 파악하려 한다.',
    '19. 경험해보지 않은 새로운 방법보다는 검증된 방법을 선호한다.',
    '20. 비유나 은유적 표현을 자주 사용하거나 이해하는 것이 쉽다.',
    '21. "지금 여기"에 집중하는 편이다.',
    '22. 앞으로 일어날 일에 대한 예감이나 직감이 잘 맞는 편이다.'
  ];

  snQuestions.forEach(q => {
    form.addScaleItem()
      .setTitle(q)
      .setBounds(1, 7)
      .setLabels('전혀 아니다', '매우 그렇다')
      .setRequired(true);
  });


  // ============================================================
  //  섹션 4: 성격 측정 — 사고(T) / 감정(F) 차원 (8문항)
  // ============================================================
  form.addSectionHeaderItem()
    .setTitle('🧠 섹션 4: 성격 측정 — 판단 기준')
    .setHelpText(
      '평소 자신의 모습에 얼마나 해당하는지 7점 척도로 답해 주세요.\n' +
      '1 = 전혀 아니다 / 4 = 보통이다 / 7 = 매우 그렇다'
    );

  const tfQuestions = [
    '23. 결정을 내릴 때 논리와 객관적 사실을 가장 중요하게 생각한다.',
    '24. 다른 사람의 감정이나 상황을 고려해서 결정하는 편이다.',
    '25. 공정함과 일관성이 배려보다 더 중요하다고 생각한다.',
    '26. 주변 사람의 기분을 잘 알아차리고 공감하는 편이다.',
    '27. 비판적 피드백을 솔직하게 전달하는 것이 도움이 된다고 생각한다.',
    '28. 갈등 상황에서 상대방의 입장을 먼저 이해하려고 노력한다.',
    '29. 감정보다는 이성적 분석을 통해 문제를 해결하는 편이다.',
    '30. 다른 사람을 돕거나 화합을 이루는 것에서 보람을 느낀다.'
  ];

  tfQuestions.forEach(q => {
    form.addScaleItem()
      .setTitle(q)
      .setBounds(1, 7)
      .setLabels('전혀 아니다', '매우 그렇다')
      .setRequired(true);
  });


  // ============================================================
  //  섹션 5: 성격 측정 — 판단(J) / 인식(P) 차원 (8문항)
  // ============================================================
  form.addSectionHeaderItem()
    .setTitle('🧠 섹션 5: 성격 측정 — 생활 방식')
    .setHelpText(
      '평소 자신의 모습에 얼마나 해당하는지 7점 척도로 답해 주세요.\n' +
      '1 = 전혀 아니다 / 4 = 보통이다 / 7 = 매우 그렇다'
    );

  const jpQuestions = [
    '31. 미리 계획을 세우고 그에 따라 행동하는 것을 좋아한다.',
    '32. 상황에 따라 유연하게 대처하는 것을 선호한다.',
    '33. 마감 기한은 반드시 지켜야 한다고 생각한다.',
    '34. 여행할 때 즉흥적으로 일정을 정하는 것이 더 재미있다.',
    '35. 할 일 목록(To-Do List)을 작성하고 체크하는 습관이 있다.',
    '36. 여러 가지 선택지를 열어두고 마지막까지 결정을 미루는 편이다.',
    '37. 정리정돈이 잘 된 깔끔한 환경에서 효율이 높아진다.',
    '38. 규칙이나 절차보다는 상황에 맞게 유연하게 행동하는 것이 낫다.'
  ];

  jpQuestions.forEach(q => {
    form.addScaleItem()
      .setTitle(q)
      .setBounds(1, 7)
      .setLabels('전혀 아니다', '매우 그렇다')
      .setRequired(true);
  });


  // ============================================================
  //  섹션 6: 혈액형 성격론 인식 (10문항)
  // ============================================================
  form.addSectionHeaderItem()
    .setTitle('🩸 섹션 6: 혈액형과 성격에 대한 인식')
    .setHelpText('혈액형과 성격의 관계에 대한 여러분의 생각을 알고 싶습니다.');

  // Q39. 혈액형-성격 관련성 믿음
  form.addScaleItem()
    .setTitle('39. 혈액형과 성격 사이에 관련이 있다고 생각하십니까?')
    .setBounds(1, 5)
    .setLabels('전혀 관련 없다', '매우 관련 있다')
    .setRequired(true);

  // Q40. 혈액형 궁합 믿음
  form.addScaleItem()
    .setTitle('40. 혈액형에 따른 궁합(연애/우정)이 실제로 존재한다고 생각하십니까?')
    .setBounds(1, 5)
    .setLabels('전혀 그렇지 않다', '매우 그렇다')
    .setRequired(true);

  // Q41-44. 혈액형별 성격 고정관념
  form.addMultipleChoiceItem()
    .setTitle('41. "A형은 꼼꼼하고 소심하다"는 말에 동의하십니까?')
    .setChoiceValues(['매우 동의', '약간 동의', '보통', '별로 동의하지 않음', '전혀 동의하지 않음'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('42. "B형은 자유분방하고 자기중심적이다"는 말에 동의하십니까?')
    .setChoiceValues(['매우 동의', '약간 동의', '보통', '별로 동의하지 않음', '전혀 동의하지 않음'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('43. "O형은 활발하고 리더십이 있다"는 말에 동의하십니까?')
    .setChoiceValues(['매우 동의', '약간 동의', '보통', '별로 동의하지 않음', '전혀 동의하지 않음'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('44. "AB형은 독특하고 이중적이다"는 말에 동의하십니까?')
    .setChoiceValues(['매우 동의', '약간 동의', '보통', '별로 동의하지 않음', '전혀 동의하지 않음'])
    .setRequired(true);

  // Q45. 혈액형으로 판단 경험
  form.addMultipleChoiceItem()
    .setTitle('45. 혈액형을 알게 된 후 그 사람의 성격을 추측한 적이 있습니까?')
    .setChoiceValues(['자주 있다', '가끔 있다', '거의 없다', '전혀 없다'])
    .setRequired(true);

  // Q46. 혈액형 차별 경험
  form.addMultipleChoiceItem()
    .setTitle('46. 혈액형 때문에 부정적인 말이나 편견을 경험한 적이 있습니까? (예: "B형이라서...")')
    .setChoiceValues(['자주 경험함', '가끔 경험함', '한두 번 정도', '경험 없음'])
    .setRequired(true);

  // Q47. 정보 습득 경로
  form.addCheckboxItem()
    .setTitle('47. 혈액형 성격론에 대한 정보를 주로 어디서 접하셨나요? (복수 선택)')
    .setChoiceValues([
      'TV 예능/드라마',
      'SNS (인스타그램, 틱톡 등)',
      '인터넷 커뮤니티/블로그',
      '주변 지인/친구',
      '책/잡지',
      '특별히 접한 적 없음'
    ])
    .setRequired(true);

  // Q48. 과학적 근거 의견
  form.addMultipleChoiceItem()
    .setTitle('48. 혈액형 성격론에 과학적 근거가 있다고 생각하십니까?')
    .setChoiceValues([
      '확실히 과학적 근거가 있다',
      '어느 정도 관련이 있을 수 있다',
      '잘 모르겠다',
      '과학적 근거가 부족하다고 생각한다',
      '전혀 과학적 근거가 없다'
    ])
    .setRequired(true);


  // ============================================================
  //  섹션 7: 관심사 & 라이프스타일 (4문항 → Q49-Q52 추가)
  // ============================================================
  form.addSectionHeaderItem()
    .setTitle('🎯 섹션 7: 관심사 & 라이프스타일')
    .setHelpText('마지막으로 관심사와 생활 방식에 대해 알려주세요.');

  // (설문 번호를 공식적으로는 48까지로 카운트하되, 추가 문항으로 처리)
  form.addCheckboxItem()
    .setTitle('49. 귀하의 주요 관심사 분야를 모두 선택해 주세요. (복수 선택)')
    .setChoiceValues([
      '기술/IT/프로그래밍',
      '예술/음악/디자인',
      '스포츠/운동/건강',
      '독서/글쓰기',
      '여행/문화 탐방',
      '요리/음식',
      '게임/엔터테인먼트',
      '과학/자연',
      '경영/경제/투자',
      '사회활동/봉사'
    ])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('50. 주말에 여가 시간이 생기면 주로 어떻게 보내시나요?')
    .setChoiceValues([
      '집에서 혼자 쉬기 (영화, 독서, 게임 등)',
      '친구/지인과 만나서 활동하기',
      '야외 활동 (운동, 산책, 여행 등)',
      '자기계발 (공부, 온라인 강의 등)',
      '그때그때 다름'
    ])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('51. 중요한 결정을 내릴 때 주로 어떤 방식을 사용하시나요?')
    .setChoiceValues([
      '데이터와 정보를 충분히 수집한 후 논리적으로 판단',
      '직감과 느낌을 주로 따름',
      '주변 사람들의 의견을 듣고 종합적으로 판단',
      '장단점 목록을 만들어서 비교',
      '특별한 방법 없이 상황에 따라 다름'
    ])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('52. 새로운 사람들과의 관계에서 귀하의 스타일은?')
    .setChoiceValues([
      '적극적으로 다가가서 친해지려 한다',
      '상대방이 먼저 다가오면 친하게 지낸다',
      '천천히 시간을 두고 관계를 쌓아간다',
      '소수의 사람과만 깊은 관계를 맺는다',
      '상황에 따라 다르다'
    ])
    .setRequired(true);


  // ============================================================
  //  섹션 8: 마무리
  // ============================================================
  form.addSectionHeaderItem()
    .setTitle('✅ 마무리')
    .setHelpText('설문에 참여해 주셔서 감사합니다!');

  form.addParagraphTextItem()
    .setTitle('추가로 하고 싶은 말씀이 있다면 자유롭게 적어주세요. (선택 사항)')
    .setRequired(false);


  // ── 응답 스프레드시트 자동 연결 ──
  const ss = SpreadsheetApp.create('MBTI_혈액형_설문_응답_데이터');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  // ── 결과 출력 ──
  const formUrl = form.getPublishedUrl();
  const editUrl = form.getEditUrl();
  const ssUrl = ss.getUrl();

  Logger.log('========================================');
  Logger.log('✅ 설문 폼 생성 완료!');
  Logger.log('========================================');
  Logger.log('📋 설문 응답 URL: ' + formUrl);
  Logger.log('✏️ 설문 편집 URL: ' + editUrl);
  Logger.log('📊 응답 스프레드시트 URL: ' + ssUrl);
  Logger.log('========================================');
  Logger.log('총 문항 수: 52문항 (기본정보 6 + 성격측정 32 + 혈액형인식 10 + 관심사 4)');
  Logger.log('========================================');

  return {
    formUrl: formUrl,
    editUrl: editUrl,
    spreadsheetUrl: ssUrl
  };
}
