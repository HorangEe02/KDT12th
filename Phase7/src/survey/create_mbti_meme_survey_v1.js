/**
 * ============================================================
 * MBTI 밈 예능 설문지 — "너 T야?" 에디션
 * ============================================================
 * KNU 12기 Phase7 Numpy 미니프로젝트 (예능용 버전)
 *
 * 한국 MBTI 밈 트렌드 기반 재미있는 설문
 * - T vs F 밸런스 게임
 * - E vs I 인싸/아싸 판별
 * - J vs P 계획 vs 즉흥
 * - S vs N 현실 vs 상상
 * - MBTI 상황극 & 혈액형 밈
 *
 * 사용법:
 *   1. https://script.google.com 접속
 *   2. 새 프로젝트 생성
 *   3. 이 코드를 전체 붙여넣기
 *   4. ▶ 실행 (createMBTIMemeSurvey 함수)
 *   5. Google 계정 권한 승인
 *   6. 실행 로그에서 생성된 Form URL 확인
 *
 * 총 40문항 | 예상 응답시간: 5~7분
 * ============================================================
 */

function createMBTIMemeSurvey() {
  // ── 폼 생성 ──
  const form = FormApp.create('MBTI 밈 테스트 — "너 T야?" 에디션');
  form.setDescription(
    '당신의 진짜 MBTI를 밈으로 알아보는 시간!\n\n' +
    '요즘 대세 "너 T야?" 부터 인싸/아싸 판별, J vs P 여행 계획까지...\n' +
    '한국 MBTI 밈 트렌드를 반영한 예능형 설문입니다.\n\n' +
    '⏱️ 소요시간: 약 5~7분\n' +
    '🎯 정답 없음! 직감적으로 골라주세요\n' +
    '🔒 익명 처리 | 연구 목적 사용\n\n' +
    '자, 시작합니다! 🚀'
  );
  form.setConfirmationMessage(
    '설문 완료! 🎉\n\n' +
    '당신의 답변은 MBTI & 혈액형 성격론 데이터 분석에 소중하게 활용됩니다.\n' +
    '과연 MBTI는 과학일까, 밈일까? 결과를 기대해 주세요! 📊'
  );
  form.setAllowResponseEdits(false);
  form.setLimitOneResponsePerUser(false);
  form.setProgressBar(true);


  // ============================================================
  //  섹션 1: 기본 정보 (5문항)
  // ============================================================
  form.addSectionHeaderItem()
    .setTitle('📌 일단 기본 정보!')
    .setHelpText('가볍게 시작해볼까요?');

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

  // Q5. MBTI 검사 방식
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
  //  섹션 2: 🔥 T vs F 밸런스 게임 (7문항)
  //  — "너 T야?" 밈의 핵심
  // ============================================================
  form.addSectionHeaderItem()
    .setTitle('🔥 라운드 1: "너 T야?" 밸런스 게임')
    .setHelpText(
      '친구가 다음과 같은 말을 했을 때, 당신의 첫 번째 반응은?\n' +
      '직감적으로 떠오르는 쪽을 골라주세요!'
    );

  // Q6
  form.addMultipleChoiceItem()
    .setTitle('6. 친구: "나 오늘 너무 아파..."')
    .setChoiceValues([
      'A) "어디 아파? 병원은 갔어?" (해결책 제시)',
      'B) "헐 괜찮아?? 많이 아파? ㅠㅠ" (감정 공감)'
    ])
    .setRequired(true);

  // Q7
  form.addMultipleChoiceItem()
    .setTitle('7. 친구: "남친이랑 또 싸웠어..."')
    .setChoiceValues([
      'A) "왜? 뭐 때문에? 원인이 뭔데" (원인 분석)',
      'B) "속상하겠다... 힘들었지? ㅠ" (위로 먼저)'
    ])
    .setRequired(true);

  // Q8
  form.addMultipleChoiceItem()
    .setTitle('8. 친구: "나 시험 망했어 ㅠㅠ"')
    .setChoiceValues([
      'A) "몇 점인데? 다음에 더 하면 되지" (현실 직시)',
      'B) "에이 그래도 열심히 했잖아, 괜찮아" (격려)'
    ])
    .setRequired(true);

  // Q9
  form.addMultipleChoiceItem()
    .setTitle('9. 친구: "오늘 피곤해서 드라이 샴푸 했어"')
    .setChoiceValues([
      'A) "...그냥 머리 감는 게 더 빠르지 않아?" (논리적 의문)',
      'B) "많이 피곤해? 무슨 일 있어?" (걱정 먼저)'
    ])
    .setRequired(true);

  // Q10
  form.addMultipleChoiceItem()
    .setTitle('10. 친구가 울면서 전화를 걸어왔다. 당신의 반응은?')
    .setChoiceValues([
      'A) "왜? 무슨 일이야? 일단 말해봐" (상황 파악)',
      'B) "어디야? 지금 갈게" (즉시 행동)'
    ])
    .setRequired(true);

  // Q11
  form.addMultipleChoiceItem()
    .setTitle('11. 연인이 "나 요즘 살찐 것 같아..."라고 했다.')
    .setChoiceValues([
      'A) "운동 같이 할까? 식단 짜줄까?" (솔루션)',
      'B) "무슨 소리야 예쁜데/멋진데~ 그대로가 좋아" (감정 지지)'
    ])
    .setRequired(true);

  // Q12
  form.addMultipleChoiceItem()
    .setTitle('12. 후배가 "선배, 저 일 못하는 거 같아요..." 라며 의기소침해한다.')
    .setChoiceValues([
      'A) "어떤 부분이 어려워? 구체적으로 말해봐" (문제 해결)',
      'B) "아니야, 처음엔 다 그래. 넌 잘하고 있어" (응원)'
    ])
    .setRequired(true);


  // ============================================================
  //  섹션 3: 🎭 E vs I — 인싸 아싸 판별기 (6문항)
  // ============================================================
  form.addSectionHeaderItem()
    .setTitle('🎭 라운드 2: 인싸인가 아싸인가')
    .setHelpText('당신의 에너지 충전 방식은? 솔직하게 골라주세요!');

  // Q13
  form.addMultipleChoiceItem()
    .setTitle('13. 금요일 퇴근/하교 후, 친구에게 갑자기 "오늘 술 한잔?" 연락이 왔다.')
    .setChoiceValues([
      'A) "오 좋아! 어디서 만날까?" (즉시 수락)',
      'B) "오늘은 좀... 집에서 쉬고 싶어" (정중 거절)',
      'C) "누가 오는데?" (참석자 먼저 확인)'
    ])
    .setRequired(true);

  // Q14
  form.addMultipleChoiceItem()
    .setTitle('14. 회식/MT에서 당신의 실제 모습은?')
    .setChoiceValues([
      'A) 분위기 메이커, 게임 선동자, 마이크 절대 안 놓는 사람',
      'B) 적당히 어울리다가 슬쩍 빠지는 사람',
      'C) 한쪽에서 조용히 친한 사람이랑만 이야기하는 사람',
      'D) 아예 안 가거나, 가서 빨리 끝나길 기다리는 사람'
    ])
    .setRequired(true);

  // Q15
  form.addMultipleChoiceItem()
    .setTitle('15. "한 명씩 돌아가면서 자기소개 해주세요~" 라는 말을 들었을 때?')
    .setChoiceValues([
      'A) 오 좋아, 빨리 하고 싶다 (먼저 하겠다고 손듦)',
      'B) 중간쯤 하면 되겠지... (적당한 순서 노림)',
      'C) 제발 나중에... (최대한 뒤로 미루기)',
      'D) 심장 쿵쿵, 스크립트 머릿속으로 리허설 시작'
    ])
    .setRequired(true);

  // Q16
  form.addMultipleChoiceItem()
    .setTitle('16. 카카오톡 답장 스타일은?')
    .setChoiceValues([
      'A) 오자마자 바로 답장! 이모티콘도 듬뿍',
      'B) 확인은 바로 하는데, 답장은 생각 좀 하고',
      'C) 확인했는데 나중에 답장해야지... (읽씹 가끔)',
      'D) 읽씹 장인... 읽었는데 뭐라고 답할지 모르겠어서'
    ])
    .setRequired(true);

  // Q17
  form.addMultipleChoiceItem()
    .setTitle('17. 충전 방법은?')
    .setChoiceValues([
      'A) 사람 만나기! 수다 떨면 에너지 충전됨',
      'B) 혼자만의 시간! 넷플릭스, 게임, 산책 등'
    ])
    .setRequired(true);

  // Q18
  form.addMultipleChoiceItem()
    .setTitle('18. 엘리베이터에서 아는 사람을 마주쳤다!')
    .setChoiceValues([
      'A) "안녕하세요~!" 먼저 인사하고 스몰톡 시작',
      'B) 눈 마주치면 인사는 하는데 대화는 어색...',
      'C) ...핸드폰을 꺼내 바쁜 척한다',
      'D) 다음 엘리베이터를 기다린다'
    ])
    .setRequired(true);


  // ============================================================
  //  섹션 4: 📋 J vs P — 계획충 vs 즉흥충 (6문항)
  // ============================================================
  form.addSectionHeaderItem()
    .setTitle('📋 라운드 3: 계획충인가 즉흥충인가')
    .setHelpText('당신의 라이프스타일은 어느 쪽? 정직하게!');

  // Q19
  form.addMultipleChoiceItem()
    .setTitle('19. 여행 계획 스타일은?')
    .setChoiceValues([
      'A) 엑셀 시간표 + 맛집 리스트 + 교통편 다 정리 (완벽 계획형)',
      'B) 대략적인 틀만 잡고, 현지에서 유연하게 (반반형)',
      'C) 숙소만 예약하고, 나머지는 그때 가서 결정 (즉흥형)',
      'D) 포스트잇 하나에 "즐기기" 끝 (완전 즉흥형)'
    ])
    .setRequired(true);

  // Q20
  form.addMultipleChoiceItem()
    .setTitle('20. 과제/업무 마감 3일 전, 당신의 진행률은?')
    .setChoiceValues([
      'A) 이미 끝나서 검토 중 (조기완료형)',
      'B) 70~80% 완료, 마무리 단계 (계획적)',
      'C) 절반쯤? 마감이 다가와야 엔진이 걸리는 타입',
      'D) ...아직 시작 안 했는데? (마감 전날이 리얼 시작)'
    ])
    .setRequired(true);

  // Q21
  form.addMultipleChoiceItem()
    .setTitle('21. 친구들과 약속 잡을 때...')
    .setChoiceValues([
      'A) "몇 시에 어디서 만나? 메뉴는 뭐 먹을 거야?" (확정 필요)',
      'B) "아 그날 만나! 자세한 건 그날 정하자~" (유연한 것도 OK)'
    ])
    .setRequired(true);

  // Q22
  form.addMultipleChoiceItem()
    .setTitle('22. 당신의 방/책상 상태는?')
    .setChoiceValues([
      'A) 정리정돈 완벽, 모든 물건에 자기 자리가 있음',
      'B) 겉보기엔 깔끔, 서랍 안은 카오스',
      'C) 나만의 정리 체계가 있다 (남이 보면 어지러움)',
      'D) 창의적 혼돈... 어지럽지만 필요한 건 다 찾음'
    ])
    .setRequired(true);

  // Q23
  form.addMultipleChoiceItem()
    .setTitle('23. 주말 아침, 특별한 약속이 없다면?')
    .setChoiceValues([
      'A) 이미 주말 할 일 목록(To-Do List)이 있음',
      'B) 일단 일어나서 그때 기분에 따라 결정'
    ])
    .setRequired(true);

  // Q24
  form.addMultipleChoiceItem()
    .setTitle('24. "오늘 뭐 먹지?"에 대한 반응은?')
    .setChoiceValues([
      'A) "내가 리스트 뽑아왔어! 여기 중에 골라" (준비형)',
      'B) "아무거나~ 네가 정해" (결정 위임형)',
      'C) "일단 나가서 보면서 정하자" (현장 판단형)',
      'D) 30분째 결정 못하는 중... (선택장애형)'
    ])
    .setRequired(true);


  // ============================================================
  //  섹션 5: 🔮 S vs N — 현실주의자 vs 몽상가 (5문항)
  // ============================================================
  form.addSectionHeaderItem()
    .setTitle('🔮 라운드 4: 현실주의자인가 몽상가인가')
    .setHelpText('당신의 사고방식은 어느 쪽에 가까운가요?');

  // Q25
  form.addMultipleChoiceItem()
    .setTitle('25. 친구가 갑자기 "만약에 좀비 아포칼립스가 오면 어떡할 거야?" 라고 물었다.')
    .setChoiceValues([
      'A) "갑자기 무슨 소리야 ㅋㅋ" (비현실적 질문 패스)',
      'B) "오 일단 마트부터 가서 물이랑 식량 확보하고..." (진지 분석 시작)'
    ])
    .setRequired(true);

  // Q26
  form.addMultipleChoiceItem()
    .setTitle('26. 누군가 "구름이 예쁘다~"라고 하면?')
    .setChoiceValues([
      'A) "어 진짜 예쁘네" (그냥 보이는 대로)',
      'B) "저 구름 고래처럼 생기지 않았어? 저기 꼬리 보여?" (상상력 발동)'
    ])
    .setRequired(true);

  // Q27
  form.addMultipleChoiceItem()
    .setTitle('27. 영화를 볼 때 당신은?')
    .setChoiceValues([
      'A) 스토리에 집중, 논리적 허점 찾기 (현실파)',
      'B) 감정 이입에 올인, 결말 이후 세계관까지 상상 (상상파)',
      'C) 둘 다 반반'
    ])
    .setRequired(true);

  // Q28
  form.addMultipleChoiceItem()
    .setTitle('28. 새로운 일을 시작할 때?')
    .setChoiceValues([
      'A) 매뉴얼/가이드를 먼저 읽고 검증된 방법으로 (안전 우선)',
      'B) 일단 해보면서 배우는 스타일 (체험 우선)',
      'C) "이걸 더 새로운 방식으로 할 수 없을까?" (혁신 우선)'
    ])
    .setRequired(true);

  // Q29
  form.addMultipleChoiceItem()
    .setTitle('29. 대화할 때 나는...')
    .setChoiceValues([
      'A) 구체적 사실 위주로 이야기 (어제 뭐 했는지, 뭘 먹었는지)',
      'B) 추상적 아이디어나 "만약에~" 이야기를 좋아함',
      'C) 둘 다 자연스럽게 섞어서'
    ])
    .setRequired(true);


  // ============================================================
  //  섹션 6: 🎬 MBTI 상황극 — 종합편 (6문항)
  // ============================================================
  form.addSectionHeaderItem()
    .setTitle('🎬 라운드 5: MBTI 상황극')
    .setHelpText('실제 상황에서 당신은 어떻게 행동할까요? 가장 가까운 것을 선택!');

  // Q30
  form.addMultipleChoiceItem()
    .setTitle('30. 팀 프로젝트에서 당신의 역할은?')
    .setChoiceValues([
      'A) 리더: 전체 방향 잡고 역할 분배하는 사람',
      'B) 실무자: 맡은 파트 묵묵히 해내는 사람',
      'C) 아이디어뱅크: 새로운 제안 던지는 사람',
      'D) 중재자: 팀원 갈등 조율하고 분위기 만드는 사람'
    ])
    .setRequired(true);

  // Q31
  form.addMultipleChoiceItem()
    .setTitle('31. 처음 가는 맛집에서 메뉴를 고를 때?')
    .setChoiceValues([
      'A) 리뷰 평점 1등 메뉴 주문 (검증된 것 선택)',
      'B) 이 집 시그니처 메뉴 (가장 특별한 것)',
      'C) 옆 테이블 음식 보고 "저거요!" (직감)',
      'D) 일행이 시킨 거 보고 "저도 같은 걸로요" (안전한 선택)'
    ])
    .setRequired(true);

  // Q32
  form.addMultipleChoiceItem()
    .setTitle('32. 당신이 가장 극혐하는 상황은?')
    .setChoiceValues([
      'A) "너한테 할 말 있는데 이따 말해줄게" (궁금해서 미칠 것 같음)',
      'B) "이번 수업은 전부 팀플로 진행합니다" (팀플 지옥)',
      'C) "자, 한 명씩 나와서 발표해주세요~" (발표 공포)',
      'D) "일정 변경됐어! 내일로 바뀜" (갑작스러운 변경 스트레스)'
    ])
    .setRequired(true);

  // Q33
  form.addMultipleChoiceItem()
    .setTitle('33. SNS(인스타/틱톡) 사용 스타일은?')
    .setChoiceValues([
      'A) 적극 활동! 스토리도 올리고 댓글도 잘 남김',
      'B) 올리기보단 구경하는 눈팅러',
      'C) 계정은 있는데 거의 안 함 / DM만 씀',
      'D) SNS 안 하거나 계정 없음'
    ])
    .setRequired(true);

  // Q34
  form.addMultipleChoiceItem()
    .setTitle('34. 당신의 갈등 해결 방식은?')
    .setChoiceValues([
      'A) 바로 대화! 쌓아두면 터진다 (직접 소통)',
      'B) 일단 혼자 정리하고, 시간 지나면 말함 (냉각 후 소통)',
      'C) 상대방이 먼저 말해주길 기다림 (수동적 대기)',
      'D) "뭐 그럴 수도 있지..." 넘어가는 편 (회피형)'
    ])
    .setRequired(true);

  // Q35
  form.addMultipleChoiceItem()
    .setTitle('35. 혼자 카페에 갔다. 자리를 고를 때?')
    .setChoiceValues([
      'A) 사람들이 잘 보이는 가운데 자리 (인간관찰 좋아)',
      'B) 창가 자리 (밖 구경하면서 멍때리기)',
      'C) 구석 자리 (나만의 공간 확보)',
      'D) 어디든 상관없음 (자리에 집착 없음)'
    ])
    .setRequired(true);


  // ============================================================
  //  섹션 7: 🩸 혈액형 밈 코너 (5문항)
  // ============================================================
  form.addSectionHeaderItem()
    .setTitle('🩸 보너스 라운드: 혈액형 밈 코너')
    .setHelpText(
      '한국 인터넷에서 유명한 혈액형 성격론!\n' +
      '"A형 = 소심", "B형 = 4차원" 같은 밈... 어떻게 생각하세요?'
    );

  // Q36
  form.addMultipleChoiceItem()
    .setTitle('36. 혈액형 물어보는 사람한테 솔직한 속마음은?')
    .setChoiceValues([
      'A) "아 맞혀봐~" (은근 기대됨)',
      'B) "B형이요" → 상대방 반응 관찰 (리액션 테스트)',
      'C) "그걸 왜 물어봐요?" (의미 없다고 생각)',
      'D) "혈액형으로 성격 파악하는 거 과학 아닌데..." (팩트 폭격)'
    ])
    .setRequired(true);

  // Q37
  form.addMultipleChoiceItem()
    .setTitle('37. "B형 남자는 안 된다" 같은 혈액형 차별 경험이 있나요?')
    .setChoiceValues([
      '들어본 적 있고 불쾌했음',
      '들어본 적 있는데 그냥 웃긴 밈이라고 생각',
      '직접 들어본 적은 없음',
      '솔직히 나도 은근 혈액형 보는 편...'
    ])
    .setRequired(true);

  // Q38
  form.addScaleItem()
    .setTitle('38. 혈액형으로 성격을 알 수 있다고 생각하세요?')
    .setHelpText('1 = 전혀 아니다 (그냥 밈이지) ~ 5 = 완전 맞다고 봄')
    .setBounds(1, 5)
    .setLabels('전혀 아니다', '완전 맞다고 봄')
    .setRequired(true);

  // Q39
  form.addScaleItem()
    .setTitle('39. MBTI로 성격을 정확하게 알 수 있다고 생각하세요?')
    .setHelpText('1 = 전혀 아니다 (그냥 재미) ~ 5 = 꽤 정확하다')
    .setBounds(1, 5)
    .setLabels('전혀 아니다', '꽤 정확하다')
    .setRequired(true);

  // Q40
  form.addMultipleChoiceItem()
    .setTitle('40. 최종 질문! MBTI & 혈액형, 당신의 진짜 생각은?')
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
    .setHelpText('수고하셨습니다! 마지막으로 한마디만!');

  form.addParagraphTextItem()
    .setTitle('자유 의견: MBTI나 혈액형에 대해 하고 싶은 말이 있다면? (선택)')
    .setHelpText('밈, 경험담, 불만, 웃긴 에피소드 뭐든 환영!')
    .setRequired(false);


  // ── 응답 스프레드시트 자동 연결 ──
  const ss = SpreadsheetApp.create('MBTI_밈_설문_응답_데이터');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  // ── 결과 출력 ──
  const formUrl = form.getPublishedUrl();
  const editUrl = form.getEditUrl();
  const ssUrl = ss.getUrl();

  Logger.log('============================================');
  Logger.log('🎉 MBTI 밈 예능 설문 생성 완료!');
  Logger.log('============================================');
  Logger.log('📋 설문 응답 URL: ' + formUrl);
  Logger.log('✏️ 설문 편집 URL: ' + editUrl);
  Logger.log('📊 응답 스프레드시트 URL: ' + ssUrl);
  Logger.log('============================================');
  Logger.log('총 40문항 + 자유의견 1개');
  Logger.log('  ▸ 기본 정보: 5문항');
  Logger.log('  ▸ T vs F 밸런스 게임: 7문항');
  Logger.log('  ▸ E vs I 인싸/아싸: 6문항');
  Logger.log('  ▸ J vs P 계획/즉흥: 6문항');
  Logger.log('  ▸ S vs N 현실/상상: 5문항');
  Logger.log('  ▸ MBTI 상황극: 6문항');
  Logger.log('  ▸ 혈액형 밈: 5문항');
  Logger.log('============================================');

  return {
    formUrl: formUrl,
    editUrl: editUrl,
    spreadsheetUrl: ssUrl
  };
}
