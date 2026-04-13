"""
build_exercise_db.py
운동 정보 데이터베이스를 구축합니다.

50+ 운동 데이터를 JSON으로 생성하고, MET 계수 데이터와 병합합니다.
Stage 3 (운동 루틴 생성) + BM25/FAISS 검색에 사용됩니다.

사용법:
    python scripts/build_exercise_db.py
    python scripts/build_exercise_db.py --validate

출력:
    data/exercises/exercise_db.json — 운동 정보 DB
    data/exercises/exercise_met.json — MET 계수 데이터
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import OUTPUT_FILES, ensure_dirs


# ═══════════════════════════════════════
# 운동 데이터베이스 (한국어)
# ═══════════════════════════════════════

EXERCISE_DB = [
    # ══════ 가슴 (Chest) ══════
    {"name": "벤치프레스", "name_en": "Bench Press", "category": "무산소", "target_muscle": "가슴",
     "secondary_muscles": ["삼두", "전면 어깨"], "equipment": "바벨, 벤치", "difficulty": "중급",
     "met_value": 6.0,
     "description": "벤치에 누워 바벨을 가슴까지 내렸다 올리는 운동. 견갑골을 모으고 발을 바닥에 단단히 고정한다.",
     "common_mistakes": ["팔꿈치를 과도하게 벌림", "엉덩이가 벤치에서 뜸", "바벨 경로가 일직선이 아님"],
     "contraindications": ["어깨 부상"],
     "alternatives": ["덤벨 벤치프레스", "머신 체스트프레스", "푸쉬업"],
     "sets_reps_guide": {"입문": {"sets": 3, "reps": "12~15", "rest_sec": 90}, "초급": {"sets": 3, "reps": "10~12", "rest_sec": 90},
                         "중급": {"sets": 4, "reps": "8~12", "rest_sec": 60}, "고급": {"sets": 5, "reps": "6~10", "rest_sec": 60}}},
    {"name": "푸쉬업", "name_en": "Push-up", "category": "무산소", "target_muscle": "가슴",
     "secondary_muscles": ["삼두", "전면 어깨", "코어"], "equipment": "맨몸", "difficulty": "초급", "met_value": 3.8,
     "description": "엎드린 자세에서 팔로 몸을 밀어 올리는 운동. 몸을 일직선으로 유지하고 코어에 힘을 준다.",
     "common_mistakes": ["허리가 처짐", "엉덩이가 올라감"], "contraindications": [],
     "alternatives": ["무릎 푸쉬업", "인클라인 푸쉬업", "월 푸쉬업"],
     "sets_reps_guide": {"입문": {"sets": 3, "reps": "5~10", "rest_sec": 90}, "초급": {"sets": 3, "reps": "10~15", "rest_sec": 60},
                         "중급": {"sets": 4, "reps": "15~20", "rest_sec": 45}, "고급": {"sets": 4, "reps": "20+", "rest_sec": 30}}},
    {"name": "덤벨 플라이", "name_en": "Dumbbell Fly", "category": "무산소", "target_muscle": "가슴",
     "secondary_muscles": ["전면 어깨"], "equipment": "덤벨, 벤치", "difficulty": "중급", "met_value": 5.0,
     "description": "벤치에 누워 양손에 덤벨을 들고 팔을 벌렸다 모으는 운동. 팔꿈치를 살짝 구부린 채 유지한다.",
     "common_mistakes": ["팔꿈치를 너무 펴서 관절에 부담"], "contraindications": ["어깨 부상"],
     "alternatives": ["케이블 플라이", "펙덱 머신"], "sets_reps_guide": {"입문": {"sets": 3, "reps": "12~15", "rest_sec": 60},
      "초급": {"sets": 3, "reps": "10~12", "rest_sec": 60}, "중급": {"sets": 4, "reps": "10~12", "rest_sec": 45}, "고급": {"sets": 4, "reps": "8~12", "rest_sec": 45}}},

    # ══════ 등 (Back) ══════
    {"name": "랫풀다운", "name_en": "Lat Pulldown", "category": "무산소", "target_muscle": "등",
     "secondary_muscles": ["이두", "후면 어깨"], "equipment": "케이블 머신", "difficulty": "초급", "met_value": 5.0,
     "description": "케이블 머신에 앉아 넓은 그립 바를 가슴 쪽으로 당기는 운동.",
     "common_mistakes": ["몸을 과도하게 뒤로 젖힘", "팔로만 당김"], "contraindications": [],
     "alternatives": ["풀업", "어시스트 풀업", "시티드 로우"],
     "sets_reps_guide": {"입문": {"sets": 3, "reps": "12~15", "rest_sec": 90}, "초급": {"sets": 3, "reps": "10~12", "rest_sec": 60},
                         "중급": {"sets": 4, "reps": "8~12", "rest_sec": 60}, "고급": {"sets": 4, "reps": "8~10", "rest_sec": 45}}},
    {"name": "바벨 로우", "name_en": "Barbell Row", "category": "무산소", "target_muscle": "등",
     "secondary_muscles": ["이두", "후면 어깨", "코어"], "equipment": "바벨", "difficulty": "중급", "met_value": 6.0,
     "description": "상체를 45도 각도로 숙인 채 바벨을 배꼽 쪽으로 당기는 운동.",
     "common_mistakes": ["허리가 둥글게 말림", "반동 사용"], "contraindications": ["허리 부상"],
     "alternatives": ["덤벨 로우", "시티드 케이블 로우", "머신 로우"],
     "sets_reps_guide": {"입문": {"sets": 3, "reps": "10~12", "rest_sec": 90}, "초급": {"sets": 3, "reps": "10~12", "rest_sec": 60},
                         "중급": {"sets": 4, "reps": "8~12", "rest_sec": 60}, "고급": {"sets": 4, "reps": "6~10", "rest_sec": 60}}},
    {"name": "풀업", "name_en": "Pull-up", "category": "무산소", "target_muscle": "등",
     "secondary_muscles": ["이두", "코어"], "equipment": "철봉", "difficulty": "고급", "met_value": 8.0,
     "description": "철봉에 매달려 몸을 끌어올리는 운동. 등 근육 발달에 가장 효과적.",
     "common_mistakes": ["턱만 올리고 등 수축 부족", "반동 사용"], "contraindications": ["어깨 부상"],
     "alternatives": ["어시스트 풀업 머신", "랫풀다운", "밴드 풀업"],
     "sets_reps_guide": {"입문": {"sets": 3, "reps": "1~3", "rest_sec": 120}, "초급": {"sets": 3, "reps": "3~5", "rest_sec": 90},
                         "중급": {"sets": 4, "reps": "6~10", "rest_sec": 60}, "고급": {"sets": 4, "reps": "10~15", "rest_sec": 60}}},

    # ══════ 하체 (Legs) ══════
    {"name": "스쿼트", "name_en": "Squat", "category": "무산소", "target_muscle": "하체",
     "secondary_muscles": ["둔근", "코어", "허리"], "equipment": "바벨 또는 맨몸", "difficulty": "중급", "met_value": 6.0,
     "description": "발을 어깨 너비로 벌리고 무릎을 구부려 앉았다 일어나는 운동.",
     "common_mistakes": ["무릎이 안쪽으로 모임", "허리가 과도하게 굽음"], "contraindications": ["무릎 부상", "허리 부상"],
     "alternatives": ["레그프레스", "고블릿 스쿼트", "월 싯"],
     "sets_reps_guide": {"입문": {"sets": 3, "reps": "10~12", "rest_sec": 90}, "초급": {"sets": 3, "reps": "10~12", "rest_sec": 90},
                         "중급": {"sets": 4, "reps": "8~12", "rest_sec": 60}, "고급": {"sets": 5, "reps": "6~10", "rest_sec": 60}}},
    {"name": "레그프레스", "name_en": "Leg Press", "category": "무산소", "target_muscle": "하체",
     "secondary_muscles": ["둔근"], "equipment": "레그프레스 머신", "difficulty": "초급", "met_value": 5.0,
     "description": "머신에 앉아 발판을 밀어내는 운동. 무릎 부상자도 비교적 안전하게 수행 가능.",
     "common_mistakes": ["무릎을 완전히 펴서 잠금", "엉덩이가 뜸"], "contraindications": [],
     "alternatives": ["스쿼트", "고블릿 스쿼트"],
     "sets_reps_guide": {"입문": {"sets": 3, "reps": "12~15", "rest_sec": 60}, "초급": {"sets": 3, "reps": "10~12", "rest_sec": 60},
                         "중급": {"sets": 4, "reps": "10~12", "rest_sec": 60}, "고급": {"sets": 4, "reps": "8~10", "rest_sec": 45}}},
    {"name": "레그 익스텐션", "name_en": "Leg Extension", "category": "무산소", "target_muscle": "하체(전면)",
     "secondary_muscles": [], "equipment": "레그 익스텐션 머신", "difficulty": "초급", "met_value": 4.0,
     "description": "머신에 앉아 다리를 펴서 대퇴사두근을 수축하는 운동.",
     "common_mistakes": ["반동 사용", "너무 무거운 중량"], "contraindications": ["무릎 부상"],
     "alternatives": ["월 싯", "시시 스쿼트"],
     "sets_reps_guide": {"입문": {"sets": 3, "reps": "12~15", "rest_sec": 60}, "초급": {"sets": 3, "reps": "10~12", "rest_sec": 60},
                         "중급": {"sets": 4, "reps": "10~12", "rest_sec": 45}, "고급": {"sets": 4, "reps": "8~12", "rest_sec": 45}}},
    {"name": "런지", "name_en": "Lunge", "category": "무산소", "target_muscle": "하체",
     "secondary_muscles": ["둔근", "코어"], "equipment": "맨몸 또는 덤벨", "difficulty": "초급", "met_value": 5.0,
     "description": "한 발을 앞으로 내딛고 무릎을 구부려 내려갔다 올라오는 운동.",
     "common_mistakes": ["앞무릎이 발끝을 넘김", "상체가 앞으로 기울어짐"], "contraindications": ["무릎 부상"],
     "alternatives": ["스플릿 스쿼트", "불가리안 스플릿 스쿼트"],
     "sets_reps_guide": {"입문": {"sets": 3, "reps": "8~10(각)", "rest_sec": 60}, "초급": {"sets": 3, "reps": "10~12(각)", "rest_sec": 60},
                         "중급": {"sets": 4, "reps": "10~12(각)", "rest_sec": 45}, "고급": {"sets": 4, "reps": "12~15(각)", "rest_sec": 45}}},

    # ══════ 어깨 (Shoulders) ══════
    {"name": "오버헤드 프레스", "name_en": "Overhead Press", "category": "무산소", "target_muscle": "어깨",
     "secondary_muscles": ["삼두", "코어"], "equipment": "바벨 또는 덤벨", "difficulty": "중급", "met_value": 5.0,
     "description": "바벨이나 덤벨을 머리 위로 밀어 올리는 운동.",
     "common_mistakes": ["허리를 과도하게 젖힘", "팔꿈치가 뒤로 빠짐"], "contraindications": ["어깨 부상", "허리 부상"],
     "alternatives": ["덤벨 숄더프레스", "머신 숄더프레스"],
     "sets_reps_guide": {"입문": {"sets": 3, "reps": "10~12", "rest_sec": 90}, "초급": {"sets": 3, "reps": "8~12", "rest_sec": 60},
                         "중급": {"sets": 4, "reps": "8~10", "rest_sec": 60}, "고급": {"sets": 4, "reps": "6~8", "rest_sec": 60}}},
    {"name": "사이드 레터럴 레이즈", "name_en": "Side Lateral Raise", "category": "무산소", "target_muscle": "어깨(측면)",
     "secondary_muscles": [], "equipment": "덤벨", "difficulty": "초급", "met_value": 3.5,
     "description": "양손에 덤벨을 들고 팔을 옆으로 들어올리는 운동.",
     "common_mistakes": ["반동 사용", "어깨를 으쓱함"], "contraindications": ["어깨 부상"],
     "alternatives": ["케이블 레터럴 레이즈"],
     "sets_reps_guide": {"입문": {"sets": 3, "reps": "12~15", "rest_sec": 45}, "초급": {"sets": 3, "reps": "12~15", "rest_sec": 45},
                         "중급": {"sets": 4, "reps": "12~15", "rest_sec": 30}, "고급": {"sets": 4, "reps": "15~20", "rest_sec": 30}}},

    # ══════ 팔 (Arms) ══════
    {"name": "바이셉 컬", "name_en": "Bicep Curl", "category": "무산소", "target_muscle": "이두",
     "secondary_muscles": ["전완"], "equipment": "덤벨 또는 바벨", "difficulty": "초급", "met_value": 3.5,
     "description": "덤벨이나 바벨을 들고 팔꿈치를 구부려 올리는 운동.",
     "common_mistakes": ["팔꿈치가 앞뒤로 흔들림", "반동 사용"], "contraindications": [],
     "alternatives": ["해머 컬", "케이블 컬", "프리처 컬"],
     "sets_reps_guide": {"입문": {"sets": 3, "reps": "12~15", "rest_sec": 45}, "초급": {"sets": 3, "reps": "10~12", "rest_sec": 45},
                         "중급": {"sets": 4, "reps": "10~12", "rest_sec": 30}, "고급": {"sets": 4, "reps": "8~12", "rest_sec": 30}}},
    {"name": "트라이셉 푸쉬다운", "name_en": "Tricep Pushdown", "category": "무산소", "target_muscle": "삼두",
     "secondary_muscles": [], "equipment": "케이블 머신", "difficulty": "초급", "met_value": 3.5,
     "description": "케이블 머신 바를 아래로 밀어내며 삼두를 수축하는 운동.",
     "common_mistakes": ["팔꿈치가 몸에서 벌어짐", "상체를 숙여서 밀어냄"], "contraindications": [],
     "alternatives": ["덤벨 킥백", "스컬크러셔"],
     "sets_reps_guide": {"입문": {"sets": 3, "reps": "12~15", "rest_sec": 45}, "초급": {"sets": 3, "reps": "10~12", "rest_sec": 45},
                         "중급": {"sets": 4, "reps": "10~12", "rest_sec": 30}, "고급": {"sets": 4, "reps": "8~12", "rest_sec": 30}}},

    # ══════ 코어 (Core) ══════
    {"name": "플랭크", "name_en": "Plank", "category": "무산소", "target_muscle": "코어",
     "secondary_muscles": ["어깨", "둔근"], "equipment": "맨몸", "difficulty": "초급", "met_value": 3.0,
     "description": "엎드린 자세에서 팔꿈치와 발끝으로 몸을 지탱하며 일직선을 유지하는 운동.",
     "common_mistakes": ["엉덩이가 올라감", "허리가 처짐"], "contraindications": [],
     "alternatives": ["사이드 플랭크", "무릎 플랭크"],
     "sets_reps_guide": {"입문": {"sets": 3, "reps": "15~20초", "rest_sec": 60}, "초급": {"sets": 3, "reps": "30초", "rest_sec": 60},
                         "중급": {"sets": 4, "reps": "45~60초", "rest_sec": 45}, "고급": {"sets": 4, "reps": "60초+", "rest_sec": 30}}},
    {"name": "크런치", "name_en": "Crunch", "category": "무산소", "target_muscle": "복근",
     "secondary_muscles": [], "equipment": "맨몸", "difficulty": "초급", "met_value": 3.5,
     "description": "누운 자세에서 상체를 살짝 들어올려 복근을 수축하는 운동.",
     "common_mistakes": ["목을 당김", "반동 사용"], "contraindications": ["허리 부상"],
     "alternatives": ["시티드 크런치 머신", "바이시클 크런치"],
     "sets_reps_guide": {"입문": {"sets": 3, "reps": "10~15", "rest_sec": 45}, "초급": {"sets": 3, "reps": "15~20", "rest_sec": 45},
                         "중급": {"sets": 4, "reps": "20~25", "rest_sec": 30}, "고급": {"sets": 4, "reps": "25+", "rest_sec": 30}}},
    {"name": "데드버그", "name_en": "Dead Bug", "category": "무산소", "target_muscle": "코어",
     "secondary_muscles": ["허리"], "equipment": "맨몸", "difficulty": "초급", "met_value": 3.0,
     "description": "누운 상태에서 반대쪽 팔과 다리를 교차로 뻗는 운동. 허리가 바닥에서 뜨지 않도록 한다.",
     "common_mistakes": ["허리가 바닥에서 뜸"], "contraindications": [],
     "alternatives": ["플랭크", "버드독"],
     "sets_reps_guide": {"입문": {"sets": 3, "reps": "8~10(각)", "rest_sec": 45}, "초급": {"sets": 3, "reps": "10~12(각)", "rest_sec": 45},
                         "중급": {"sets": 4, "reps": "12~15(각)", "rest_sec": 30}, "고급": {"sets": 4, "reps": "15~20(각)", "rest_sec": 30}}},

    # ══════ 유산소 (Cardio) ══════
    {"name": "트레드밀 걷기", "name_en": "Treadmill Walking", "category": "유산소", "target_muscle": "전신",
     "secondary_muscles": ["하체", "코어"], "equipment": "트레드밀", "difficulty": "입문", "met_value": 3.5,
     "description": "트레드밀에서 빠르게 걷는 운동. 경사도를 높이면 강도 증가.",
     "common_mistakes": ["손잡이에 체중을 실음"], "contraindications": [],
     "alternatives": ["야외 걷기", "실내 자전거"],
     "sets_reps_guide": {"입문": {"sets": 1, "reps": "15~20분", "rest_sec": 0}, "초급": {"sets": 1, "reps": "20~30분", "rest_sec": 0},
                         "중급": {"sets": 1, "reps": "30~40분", "rest_sec": 0}, "고급": {"sets": 1, "reps": "40~60분", "rest_sec": 0}}},
    {"name": "러닝", "name_en": "Running", "category": "유산소", "target_muscle": "전신",
     "secondary_muscles": ["하체", "코어"], "equipment": "트레드밀 또는 야외", "difficulty": "초급", "met_value": 8.0,
     "description": "중간 속도로 달리는 운동. 심폐 기능 향상에 효과적.",
     "common_mistakes": ["과도한 보폭", "착지 시 발뒤꿈치만 사용"], "contraindications": ["무릎 부상", "발목 부상"],
     "alternatives": ["사이클", "수영", "로잉 머신"],
     "sets_reps_guide": {"입문": {"sets": 1, "reps": "10~15분", "rest_sec": 0}, "초급": {"sets": 1, "reps": "15~25분", "rest_sec": 0},
                         "중급": {"sets": 1, "reps": "25~40분", "rest_sec": 0}, "고급": {"sets": 1, "reps": "40~60분", "rest_sec": 0}}},
    {"name": "사이클", "name_en": "Cycling", "category": "유산소", "target_muscle": "하체",
     "secondary_muscles": ["코어"], "equipment": "실내 자전거", "difficulty": "입문", "met_value": 6.0,
     "description": "실내 자전거를 타는 운동. 관절 부담이 적어 재활에도 적합.",
     "common_mistakes": ["안장 높이 부적절"], "contraindications": [],
     "alternatives": ["트레드밀 걷기", "일립티컬"],
     "sets_reps_guide": {"입문": {"sets": 1, "reps": "15~20분", "rest_sec": 0}, "초급": {"sets": 1, "reps": "20~30분", "rest_sec": 0},
                         "중급": {"sets": 1, "reps": "30~45분", "rest_sec": 0}, "고급": {"sets": 1, "reps": "45~60분", "rest_sec": 0}}},
    {"name": "줄넘기", "name_en": "Jump Rope", "category": "유산소", "target_muscle": "전신",
     "secondary_muscles": ["종아리", "어깨", "코어"], "equipment": "줄넘기", "difficulty": "초급", "met_value": 10.0,
     "description": "줄넘기를 넘는 고강도 유산소 운동. 짧은 시간에 높은 칼로리 소모.",
     "common_mistakes": ["팔 전체를 크게 돌림"], "contraindications": ["무릎 부상", "발목 부상"],
     "alternatives": ["버피", "점핑잭"],
     "sets_reps_guide": {"입문": {"sets": 3, "reps": "30초", "rest_sec": 60}, "초급": {"sets": 5, "reps": "1분", "rest_sec": 30},
                         "중급": {"sets": 5, "reps": "2분", "rest_sec": 30}, "고급": {"sets": 5, "reps": "3분", "rest_sec": 15}}},

    # ══════ 전신 복합 (Compound) ══════
    {"name": "데드리프트", "name_en": "Deadlift", "category": "무산소", "target_muscle": "전신",
     "secondary_muscles": ["등", "둔근", "하체", "코어"], "equipment": "바벨", "difficulty": "고급", "met_value": 6.0,
     "description": "바닥에 놓인 바벨을 잡고 일어서는 운동. 전신 근력 발달에 가장 효과적.",
     "common_mistakes": ["등이 둥글게 말림", "바가 몸에서 멀어짐"], "contraindications": ["허리 부상"],
     "alternatives": ["루마니안 데드리프트", "트랩바 데드리프트"],
     "sets_reps_guide": {"입문": {"sets": 3, "reps": "8~10", "rest_sec": 120}, "초급": {"sets": 3, "reps": "8~10", "rest_sec": 90},
                         "중급": {"sets": 4, "reps": "6~8", "rest_sec": 90}, "고급": {"sets": 5, "reps": "3~6", "rest_sec": 120}}},
    {"name": "버피", "name_en": "Burpee", "category": "유산소", "target_muscle": "전신",
     "secondary_muscles": ["가슴", "삼두", "코어", "하체"], "equipment": "맨몸", "difficulty": "중급", "met_value": 10.0,
     "description": "스쿼트-플랭크-푸쉬업-점프를 연속으로 수행하는 고강도 전신 운동.",
     "common_mistakes": ["허리가 처짐", "점프 시 무릎이 안쪽으로 모임"], "contraindications": ["무릎 부상", "허리 부상", "손목 부상"],
     "alternatives": ["하프 버피", "스쿼트 점프"],
     "sets_reps_guide": {"입문": {"sets": 3, "reps": "3~5", "rest_sec": 90}, "초급": {"sets": 3, "reps": "5~8", "rest_sec": 60},
                         "중급": {"sets": 4, "reps": "8~12", "rest_sec": 45}, "고급": {"sets": 5, "reps": "12~15", "rest_sec": 30}}},

    # ══════ 스트레칭/유연성 ══════
    {"name": "폼롤러 스트레칭", "name_en": "Foam Rolling", "category": "스트레칭", "target_muscle": "전신",
     "secondary_muscles": [], "equipment": "폼롤러", "difficulty": "입문", "met_value": 2.0,
     "description": "폼롤러 위에 근육을 올리고 천천히 굴려 근막을 이완하는 운동.",
     "common_mistakes": ["너무 빠르게 굴림"], "contraindications": [],
     "alternatives": ["마사지볼", "라크로스볼"],
     "sets_reps_guide": {"입문": {"sets": 1, "reps": "부위당 30초", "rest_sec": 0}, "초급": {"sets": 1, "reps": "부위당 1분", "rest_sec": 0},
                         "중급": {"sets": 1, "reps": "부위당 1~2분", "rest_sec": 0}, "고급": {"sets": 1, "reps": "부위당 2분", "rest_sec": 0}}},
]


# ── MET 계수 참조 테이블 (Compendium of Physical Activities 기반) ──
MET_REFERENCE = {
    "걷기(보통 속도)": 3.5, "걷기(빠른 속도)": 4.5, "조깅": 7.0, "러닝(일반)": 8.0,
    "러닝(빠른 속도)": 11.0, "사이클(보통)": 6.0, "사이클(고강도)": 10.0,
    "수영(자유형)": 8.0, "수영(접영)": 11.0, "줄넘기(보통)": 10.0,
    "웨이트트레이닝(보통)": 5.0, "웨이트트레이닝(고강도)": 6.0,
    "요가(하타)": 2.5, "요가(파워)": 4.0, "필라테스": 3.0,
    "에어로빅(보통)": 6.5, "에어로빅(고강도)": 7.5,
    "등산": 6.0, "등산(가파른 길)": 8.0,
    "농구": 6.5, "축구": 7.0, "테니스": 7.3, "배드민턴": 5.5,
    "스트레칭": 2.3, "복싱(샌드백)": 5.5,
    "일립티컬": 5.0, "로잉머신": 7.0, "계단 오르기": 9.0,
    "HIIT(인터벌)": 9.0, "크로스핏": 8.0,
}


def validate_exercise_db(exercises: list[dict]) -> dict:
    """운동 DB 데이터 무결성을 검증합니다."""
    issues = []
    muscles = set()
    names = set()

    for i, ex in enumerate(exercises):
        name = ex.get("name", f"index_{i}")

        # 중복 이름
        if name in names:
            issues.append(f"중복 운동명: {name}")
        names.add(name)

        # 필수 필드
        for field in ["name", "category", "target_muscle", "difficulty", "met_value", "description"]:
            if not ex.get(field):
                issues.append(f"{name}: '{field}' 누락")

        # MET 범위
        met = ex.get("met_value", 0)
        if met < 1 or met > 20:
            issues.append(f"{name}: MET 값 이상 ({met})")

        muscles.add(ex.get("target_muscle"))

    return {
        "total_exercises": len(exercises),
        "unique_muscles": sorted(muscles - {None}),
        "issues": issues,
        "is_valid": len(issues) == 0,
    }


def main():
    parser = argparse.ArgumentParser(description="운동 DB 구축")
    parser.add_argument("--validate", action="store_true", help="데이터 검증만 실행")
    args = parser.parse_args()

    ensure_dirs()

    print("=" * 60)
    print("🏋️ 운동 정보 데이터베이스 구축")
    print("=" * 60)

    # 검증
    validation = validate_exercise_db(EXERCISE_DB)
    print(f"\n📋 총 {validation['total_exercises']}개 운동")
    print(f"   근육군: {', '.join(validation['unique_muscles'])}")

    if validation["issues"]:
        print(f"\n⚠️ 검증 이슈 {len(validation['issues'])}건:")
        for issue in validation["issues"]:
            print(f"   - {issue}")
    else:
        print("   ✅ 데이터 검증 통과")

    if args.validate:
        return

    # 운동 DB 저장
    db_output = {
        "exercises": EXERCISE_DB,
        "total_count": len(EXERCISE_DB),
        "muscle_groups": validation["unique_muscles"],
        "generated_at": datetime.now().isoformat(),
        "version": "1.0.0",
    }

    with open(OUTPUT_FILES["exercise_db"], "w", encoding="utf-8") as f:
        json.dump(db_output, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 운동 DB 저장: {OUTPUT_FILES['exercise_db']}")

    # MET 참조 테이블 저장
    met_output = {
        "met_reference": MET_REFERENCE,
        "source": "Compendium of Physical Activities (Ainsworth et al.)",
        "note": "MET = 안정 시 대비 에너지 소비 배수. 칼로리 = MET × 체중(kg) × 시간(h)",
        "generated_at": datetime.now().isoformat(),
    }

    with open(OUTPUT_FILES["exercise_met"], "w", encoding="utf-8") as f:
        json.dump(met_output, f, ensure_ascii=False, indent=2)
    print(f"✅ MET 참조 저장: {OUTPUT_FILES['exercise_met']}")

    print("\n✨ 운동 DB 구축 완료!")


if __name__ == "__main__":
    main()
