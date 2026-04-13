# 🏃 전(轉) — 어떻게 운동하지? | 구현 가이드라인

## 📌 개요

이 문서는 **헬창지피티(HelChangGPT)** 프로젝트의 **3단계: 맞춤 운동 루틴 생성** 구현을 위한
구현 가이드라인입니다.

1단계 프로필 + 2단계 식단 정보를 기반으로, **LLM으로 요일별 운동 루틴을 생성**하고,
**임베딩 검색(sentence-transformers) + BM25 키워드 검색**으로 운동 상세 정보를 제공합니다.

이 단계의 핵심 차별점은 **LLM 생성 결과와 검색 기반 결과를 비교·분석**하는 것입니다.

---

## 1. 이전 단계로부터 받는 입력

```python
# 1단계(기) + 2단계(승)에서 전달받는 핵심 필드

STAGE3_INPUT = {
    # ── 1단계: 프로필 ──
    "goal_type": "체지방감소",
    "experience_level": "입문",
    "exercise_frequency": 3,            # 주당 운동 가능 횟수
    "constraints": ["무릎 부상"],         # 제약사항
    "gender": "여성",
    "age": 51,
    "weight_kg": 59.1,
    "body_fat_percent": 37.5,
    "priority": "지방감량우선",
    
    # ── 2단계: 식단 ──
    "recommended_intake_kcal": 1397,
    "carb_g": 122,                       # 탄수화물 목표 (운동 에너지)
    "protein_g": 122,                    # 단백질 목표 (근회복)
}
```

---

## 2. 출력 데이터 구조

```python
WORKOUT_PLAN_SCHEMA = {
    # ── 루틴 메타 정보 ──
    "meta": {
        "goal_type": str,
        "frequency": int,               # 주 N회
        "split_type": str,               # "전신" | "상하분할" | "부위별분할" | "PPL"
        "experience_level": str,
        "constraints_applied": list,
        "model_used": str,
        "temperature": float,
        "generated_at": str,
    },
    
    # ── 요일별 운동 계획 ──
    "weekly_plan": {
        "day1": {
            "day_label": str,            # "월요일" 등
            "focus": str,                # "가슴 + 삼두" 등
            "estimated_time_min": int,
            "estimated_calories": int,
            "warmup": {
                "exercises": [
                    {
                        "name": str,
                        "duration_min": int,
                        "description": str,
                    }
                ],
            },
            "main_workout": {
                "exercises": [
                    {
                        "name": str,             # 운동명
                        "target_muscle": str,     # 주요 근육군
                        "sets": int,
                        "reps": str,              # "12" 또는 "8~12"
                        "rest_sec": int,          # 세트 간 휴식
                        "intensity": str,         # "저|중|고"
                        "description": str,       # 수행 방법
                        "alternatives": list,     # 대체 운동 목록
                        "caution": str,           # 주의사항 (제약 관련)
                    }
                ],
            },
            "cooldown": {
                "exercises": [
                    {
                        "name": str,
                        "duration_min": int,
                        "description": str,
                    }
                ],
            },
            "tip": str,                  # 오늘의 운동 팁
        },
        "day2": { ... },
        "day3": { ... },
        "rest_days": list,               # 휴식일 목록
    },
    
    # ── 검색 기반 운동 상세 정보 ──
    "exercise_details": {
        "<운동명>": {
            "description": str,          # 상세 수행 방법
            "target_muscles": list,      # 주동근 + 보조근
            "difficulty": str,           # "초급|중급|고급"
            "equipment": str,            # 필요 장비
            "common_mistakes": list,     # 흔한 실수
            "search_method": str,        # "embedding" | "bm25" | "llm"
            "search_score": float,       # 검색 유사도 점수
        }
    },
    
    # ── 주간 요약 ──
    "weekly_summary": {
        "total_sessions": int,
        "total_estimated_time_min": int,
        "total_estimated_calories": int,
        "muscle_groups_covered": list,
        "balance_score": float,          # 근육군 균형 점수 (0~100)
    },
}
```

---

## 3. 운동 정보 데이터베이스

### 3-1. 운동 DB 스키마

```python
"""
exercise_db.py
운동 정보 데이터베이스를 구축하고 관리합니다.
"""

EXERCISE_DB = [
    # ══════ 가슴 (Chest) ══════
    {
        "name": "벤치프레스",
        "name_en": "Bench Press",
        "category": "무산소",
        "target_muscle": "가슴",
        "secondary_muscles": ["삼두", "전면 어깨"],
        "equipment": "바벨, 벤치",
        "difficulty": "중급",
        "met_value": 6.0,
        "description": "벤치에 누워 바벨을 가슴까지 내렸다 올리는 운동. 견갑골을 모으고 발을 바닥에 단단히 고정한다.",
        "common_mistakes": ["팔꿈치를 과도하게 벌림", "엉덩이가 벤치에서 뜸", "바벨 경로가 일직선이 아님"],
        "contraindications": ["어깨 부상"],
        "alternatives": ["덤벨 벤치프레스", "머신 체스트프레스", "푸쉬업"],
        "sets_reps_guide": {
            "입문": {"sets": 3, "reps": "12~15", "rest_sec": 90},
            "초급": {"sets": 3, "reps": "10~12", "rest_sec": 90},
            "중급": {"sets": 4, "reps": "8~12", "rest_sec": 60},
            "고급": {"sets": 5, "reps": "6~10", "rest_sec": 60},
        },
    },
    {
        "name": "푸쉬업",
        "name_en": "Push-up",
        "category": "무산소",
        "target_muscle": "가슴",
        "secondary_muscles": ["삼두", "전면 어깨", "코어"],
        "equipment": "맨몸",
        "difficulty": "초급",
        "met_value": 3.8,
        "description": "엎드린 자세에서 팔로 몸을 밀어 올리는 운동. 몸을 일직선으로 유지하고 코어에 힘을 준다.",
        "common_mistakes": ["허리가 처짐", "엉덩이가 올라감", "팔꿈치가 과도하게 벌어짐"],
        "contraindications": [],
        "alternatives": ["무릎 푸쉬업", "인클라인 푸쉬업", "월 푸쉬업"],
        "sets_reps_guide": {
            "입문": {"sets": 3, "reps": "5~10", "rest_sec": 90},
            "초급": {"sets": 3, "reps": "10~15", "rest_sec": 60},
            "중급": {"sets": 4, "reps": "15~20", "rest_sec": 45},
            "고급": {"sets": 4, "reps": "20+", "rest_sec": 30},
        },
    },
    
    # ══════ 등 (Back) ══════
    {
        "name": "랫풀다운",
        "name_en": "Lat Pulldown",
        "category": "무산소",
        "target_muscle": "등",
        "secondary_muscles": ["이두", "후면 어깨"],
        "equipment": "케이블 머신",
        "difficulty": "초급",
        "met_value": 5.0,
        "description": "케이블 머신에 앉아 넓은 그립 바를 가슴 쪽으로 당기는 운동. 등 근육의 수축을 느끼며 천천히 수행한다.",
        "common_mistakes": ["몸을 과도하게 뒤로 젖힘", "팔로만 당김", "반동 사용"],
        "contraindications": [],
        "alternatives": ["풀업", "어시스트 풀업", "시티드 로우"],
        "sets_reps_guide": {
            "입문": {"sets": 3, "reps": "12~15", "rest_sec": 90},
            "초급": {"sets": 3, "reps": "10~12", "rest_sec": 60},
            "중급": {"sets": 4, "reps": "8~12", "rest_sec": 60},
            "고급": {"sets": 4, "reps": "8~10", "rest_sec": 45},
        },
    },
    
    # ══════ 하체 (Legs) ══════
    {
        "name": "스쿼트",
        "name_en": "Squat",
        "category": "무산소",
        "target_muscle": "하체",
        "secondary_muscles": ["둔근", "코어", "허리"],
        "equipment": "바벨 또는 맨몸",
        "difficulty": "중급",
        "met_value": 6.0,
        "description": "발을 어깨 너비로 벌리고 무릎을 구부려 앉았다 일어나는 운동. 무릎이 발끝을 넘지 않도록 주의한다.",
        "common_mistakes": ["무릎이 안쪽으로 모임", "허리가 과도하게 굽음", "발뒤꿈치가 뜸"],
        "contraindications": ["무릎 부상", "허리 부상"],
        "alternatives": ["레그프레스", "고블릿 스쿼트", "월 싯"],
        "sets_reps_guide": {
            "입문": {"sets": 3, "reps": "10~12", "rest_sec": 90},
            "초급": {"sets": 3, "reps": "10~12", "rest_sec": 90},
            "중급": {"sets": 4, "reps": "8~12", "rest_sec": 60},
            "고급": {"sets": 5, "reps": "6~10", "rest_sec": 60},
        },
    },
    {
        "name": "레그프레스",
        "name_en": "Leg Press",
        "category": "무산소",
        "target_muscle": "하체",
        "secondary_muscles": ["둔근"],
        "equipment": "레그프레스 머신",
        "difficulty": "초급",
        "met_value": 5.0,
        "description": "머신에 앉아 발판을 밀어 올리는 운동. 무릎 부담이 적어 스쿼트 대체 운동으로 적합하다.",
        "common_mistakes": ["무릎을 완전히 펴서 잠금", "엉덩이가 시트에서 뜸"],
        "contraindications": [],
        "alternatives": ["스쿼트", "고블릿 스쿼트"],
        "sets_reps_guide": {
            "입문": {"sets": 3, "reps": "12~15", "rest_sec": 90},
            "초급": {"sets": 3, "reps": "10~12", "rest_sec": 60},
            "중급": {"sets": 4, "reps": "8~12", "rest_sec": 60},
            "고급": {"sets": 4, "reps": "8~10", "rest_sec": 45},
        },
    },
    
    # ══════ 어깨 (Shoulders) ══════
    {
        "name": "오버헤드프레스",
        "name_en": "Overhead Press",
        "category": "무산소",
        "target_muscle": "어깨",
        "secondary_muscles": ["삼두", "상부 가슴"],
        "equipment": "바벨 또는 덤벨",
        "difficulty": "중급",
        "met_value": 5.0,
        "description": "서서 또는 앉아서 바벨/덤벨을 머리 위로 밀어 올리는 운동.",
        "common_mistakes": ["허리를 과도하게 젖힘", "코어에 힘을 빼기"],
        "contraindications": ["어깨 부상"],
        "alternatives": ["덤벨 숄더프레스", "머신 숄더프레스", "래터럴레이즈"],
        "sets_reps_guide": {
            "입문": {"sets": 3, "reps": "12~15", "rest_sec": 90},
            "초급": {"sets": 3, "reps": "10~12", "rest_sec": 60},
            "중급": {"sets": 4, "reps": "8~12", "rest_sec": 60},
            "고급": {"sets": 4, "reps": "6~10", "rest_sec": 60},
        },
    },
    
    # ══════ 유산소 (Cardio) ══════
    {
        "name": "트레드밀 걷기",
        "name_en": "Treadmill Walking",
        "category": "유산소",
        "target_muscle": "전신",
        "secondary_muscles": ["하체", "코어"],
        "equipment": "트레드밀",
        "difficulty": "입문",
        "met_value": 3.5,
        "description": "트레드밀에서 시속 5~6km로 걷는 유산소 운동. 경사도를 올리면 강도를 높일 수 있다.",
        "common_mistakes": ["손잡이에 의지함", "보폭이 너무 좁음"],
        "contraindications": [],
        "alternatives": ["실외 걷기", "스텝퍼", "리컴번트 바이크"],
        "sets_reps_guide": {
            "입문": {"sets": 1, "reps": "20분", "rest_sec": 0},
            "초급": {"sets": 1, "reps": "30분", "rest_sec": 0},
            "중급": {"sets": 1, "reps": "30~40분", "rest_sec": 0},
            "고급": {"sets": 1, "reps": "40~60분", "rest_sec": 0},
        },
    },
    {
        "name": "사이클",
        "name_en": "Stationary Bike",
        "category": "유산소",
        "target_muscle": "하체",
        "secondary_muscles": ["심폐"],
        "equipment": "실내 자전거",
        "difficulty": "입문",
        "met_value": 5.5,
        "description": "실내 자전거를 타는 유산소 운동. 무릎 부담이 적어 관절이 약한 사람에게 적합하다.",
        "common_mistakes": ["안장 높이가 맞지 않음", "상체를 과도하게 숙임"],
        "contraindications": [],
        "alternatives": ["리컴번트 바이크", "일립티컬", "로잉머신"],
        "sets_reps_guide": {
            "입문": {"sets": 1, "reps": "20분", "rest_sec": 0},
            "초급": {"sets": 1, "reps": "30분", "rest_sec": 0},
            "중급": {"sets": 1, "reps": "30~40분", "rest_sec": 0},
            "고급": {"sets": 1, "reps": "40~60분", "rest_sec": 0},
        },
    },
    
    # ... (전체 DB는 50~100종 목표)
]


# ── 근육군 매핑 ──
MUSCLE_GROUP_MAP = {
    "가슴": ["벤치프레스", "덤벨 벤치프레스", "머신 체스트프레스", "푸쉬업", "딥스", "케이블 크로스오버", "인클라인 벤치프레스"],
    "등": ["랫풀다운", "풀업", "바벨 로우", "덤벨 로우", "시티드 로우", "케이블 로우", "티바 로우"],
    "어깨": ["오버헤드프레스", "덤벨 숄더프레스", "래터럴레이즈", "프론트레이즈", "페이스풀", "리어델트 플라이"],
    "하체": ["스쿼트", "레그프레스", "런지", "레그익스텐션", "레그컬", "힙쓰러스트", "카프레이즈"],
    "이두": ["바벨 컬", "덤벨 컬", "해머 컬", "프리쳐 컬", "케이블 컬"],
    "삼두": ["트라이셉 푸쉬다운", "오버헤드 익스텐션", "딥스", "클로즈그립 벤치프레스"],
    "코어": ["플랭크", "크런치", "레그레이즈", "러시안 트위스트", "마운틴 클라이머"],
    "유산소": ["트레드밀 걷기", "트레드밀 달리기", "사이클", "일립티컬", "로잉머신", "줄넘기", "버피"],
}
```

### 3-2. 데이터 출처

```python
"""
exercise_data_sources.py
운동 정보 수집에 활용할 수 있는 데이터 출처입니다.
"""

DATA_SOURCES = {
    "공공데이터": {
        "국민체력측정 운동처방 데이터": {
            "url": "https://www.data.go.kr/data/7844714/linkedData.do",
            "format": "CSV",
            "content": "체력측정별 운동처방 결과, 연령/BMI별 추천 운동 5종",
        },
        "모바일 헬스케어 운동 목록": {
            "url": "https://www.data.go.kr/data/15068730/fileData.do",
            "format": "CSV",
            "content": "운동명, MET 계수 (칼로리 소모량 계산용)",
        },
        "근력운동 처방 AI 학습 데이터": {
            "url": "https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=71331",
            "format": "JSON",
            "content": "질환별 근력운동 처방 데이터, PHR 연동",
        },
    },
    "외부 참고": {
        "ExRx.net": {
            "url": "https://exrx.net/Lists/ExList/HomeWt",
            "content": "부위별/장비별 운동 목록, 수행 방법, 근육 해부도",
        },
        "Muscle Wiki": {
            "url": "https://musclewiki.com",
            "content": "인터랙티브 근육 맵, 운동 영상/설명",
        },
    },
}
```

---

## 4. 검색 엔진 구현

### 4-1. 임베딩 검색 (Semantic Search)

```python
"""
exercise_search_embedding.py
sentence-transformers + FAISS로 운동 정보를 의미 기반 검색합니다.
"""

import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer


class ExerciseEmbeddingSearch:
    """
    운동 정보를 임베딩하여 의미 기반 검색을 수행합니다.
    
    사용 예시:
        searcher = ExerciseEmbeddingSearch(EXERCISE_DB)
        results = searcher.search("무릎에 부담 적은 하체 운동", top_k=5)
        # → [레그프레스, 힙쓰러스트, 사이클, ...]
    """
    
    def __init__(
        self,
        exercises: list[dict],
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
    ):
        self.exercises = exercises
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.embeddings = None
        self._build_index()
    
    def _build_index(self):
        """운동 정보를 임베딩하고 FAISS 인덱스를 생성합니다."""
        # 각 운동의 검색용 텍스트 생성
        texts = []
        for ex in self.exercises:
            search_text = (
                f"{ex['name']} {ex.get('name_en', '')} "
                f"{ex['target_muscle']} {' '.join(ex.get('secondary_muscles', []))} "
                f"{ex['category']} {ex['difficulty']} "
                f"{ex.get('equipment', '')} "
                f"{ex.get('description', '')}"
            )
            texts.append(search_text)
        
        # 임베딩 생성
        self.embeddings = self.model.encode(texts, show_progress_bar=False)
        
        # FAISS 인덱스 생성
        dim = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)  # Inner Product (코사인 유사도용)
        
        # L2 정규화 (코사인 유사도 사용)
        faiss.normalize_L2(self.embeddings)
        self.index.add(self.embeddings)
    
    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        자연어 쿼리로 운동을 검색합니다.
        
        Args:
            query: 검색 쿼리 (예: "초보자 가슴 운동 맨몸")
            top_k: 반환할 결과 수
        
        Returns:
            [{"exercise": {...}, "score": 0.85, "method": "embedding"}, ...]
        """
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        scores, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            results.append({
                "exercise": self.exercises[idx],
                "score": float(score),
                "method": "embedding",
            })
        
        return results
    
    def search_by_conditions(
        self,
        target_muscle: str = None,
        difficulty: str = None,
        equipment: str = None,
        exclude_contraindications: list = None,
        top_k: int = 5,
    ) -> list[dict]:
        """
        조건 기반 필터링 + 임베딩 검색을 조합합니다.
        """
        # 조건 기반 필터링
        filtered = self.exercises
        
        if target_muscle:
            filtered = [e for e in filtered if e["target_muscle"] == target_muscle]
        
        if difficulty:
            level_order = ["입문", "초급", "중급", "고급"]
            max_idx = level_order.index(difficulty)
            filtered = [e for e in filtered 
                       if level_order.index(e["difficulty"]) <= max_idx]
        
        if equipment:
            filtered = [e for e in filtered if equipment in e.get("equipment", "")]
        
        if exclude_contraindications:
            filtered = [
                e for e in filtered
                if not any(c in e.get("contraindications", [])
                          for c in exclude_contraindications)
            ]
        
        return [{"exercise": e, "score": 1.0, "method": "filter"} for e in filtered[:top_k]]
```

### 4-2. BM25 키워드 검색

```python
"""
exercise_search_bm25.py
BM25 알고리즘으로 운동 정보를 키워드 기반 검색합니다.
"""

from rank_bm25 import BM25Okapi
from konlpy.tag import Okt


class ExerciseBM25Search:
    """
    BM25로 운동 정보를 키워드 기반 검색합니다.
    임베딩 검색과 비교하기 위한 baseline 검색 엔진입니다.
    
    사용 예시:
        searcher = ExerciseBM25Search(EXERCISE_DB)
        results = searcher.search("가슴 운동 초보자", top_k=5)
    """
    
    def __init__(self, exercises: list[dict]):
        self.exercises = exercises
        self.okt = Okt()
        self.bm25 = None
        self.tokenized_docs = []
        self._build_index()
    
    def _build_index(self):
        """운동 정보를 토크나이즈하고 BM25 인덱스를 생성합니다."""
        for ex in self.exercises:
            doc_text = (
                f"{ex['name']} {ex.get('name_en', '')} "
                f"{ex['target_muscle']} {' '.join(ex.get('secondary_muscles', []))} "
                f"{ex['category']} {ex['difficulty']} "
                f"{ex.get('equipment', '')} "
                f"{ex.get('description', '')}"
            )
            tokens = self.okt.morphs(doc_text, stem=True)
            self.tokenized_docs.append(tokens)
        
        self.bm25 = BM25Okapi(self.tokenized_docs)
    
    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """BM25로 운동을 검색합니다."""
        query_tokens = self.okt.morphs(query, stem=True)
        scores = self.bm25.get_scores(query_tokens)
        
        top_indices = scores.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append({
                    "exercise": self.exercises[idx],
                    "score": float(scores[idx]),
                    "method": "bm25",
                })
        
        return results
```

### 4-3. 하이브리드 검색 + 비교

```python
"""
exercise_search_hybrid.py
임베딩 검색과 BM25 검색 결과를 통합하고 비교합니다.
"""


class HybridExerciseSearch:
    """
    임베딩 + BM25 결과를 조합하여 최적의 검색 결과를 제공합니다.
    두 방식의 결과를 비교 분석하는 기능도 포함합니다.
    """
    
    def __init__(self, exercises: list[dict]):
        self.embedding_search = ExerciseEmbeddingSearch(exercises)
        self.bm25_search = ExerciseBM25Search(exercises)
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        embedding_weight: float = 0.6,
        bm25_weight: float = 0.4,
    ) -> list[dict]:
        """
        하이브리드 검색을 수행합니다. (가중 평균)
        """
        emb_results = self.embedding_search.search(query, top_k=top_k * 2)
        bm25_results = self.bm25_search.search(query, top_k=top_k * 2)
        
        # 점수 정규화 및 통합
        score_map = {}
        
        for r in emb_results:
            name = r["exercise"]["name"]
            score_map[name] = score_map.get(name, {"exercise": r["exercise"], "scores": {}})
            score_map[name]["scores"]["embedding"] = r["score"]
        
        for r in bm25_results:
            name = r["exercise"]["name"]
            score_map[name] = score_map.get(name, {"exercise": r["exercise"], "scores": {}})
            score_map[name]["scores"]["bm25"] = r["score"]
        
        # 가중 합산
        results = []
        for name, data in score_map.items():
            emb_score = data["scores"].get("embedding", 0)
            bm25_score = data["scores"].get("bm25", 0)
            
            # BM25 점수 정규화 (0~1 범위)
            bm25_norm = min(bm25_score / 10.0, 1.0) if bm25_score > 0 else 0
            
            combined = (emb_score * embedding_weight) + (bm25_norm * bm25_weight)
            
            results.append({
                "exercise": data["exercise"],
                "combined_score": round(combined, 4),
                "embedding_score": round(emb_score, 4),
                "bm25_score": round(bm25_score, 4),
                "method": "hybrid",
            })
        
        results.sort(key=lambda x: x["combined_score"], reverse=True)
        return results[:top_k]
    
    def compare_methods(self, query: str, top_k: int = 5) -> dict:
        """
        같은 쿼리에 대해 3가지 검색 방식의 결과를 비교합니다.
        
        반환값 예시:
        {
            "query": "무릎에 부담 적은 하체 운동",
            "embedding_results": [...],
            "bm25_results": [...],
            "hybrid_results": [...],
            "overlap": {"emb_bm25": 3, "emb_hybrid": 4, "bm25_hybrid": 3},
        }
        """
        emb = self.embedding_search.search(query, top_k)
        bm25 = self.bm25_search.search(query, top_k)
        hybrid = self.search(query, top_k)
        
        emb_names = {r["exercise"]["name"] for r in emb}
        bm25_names = {r["exercise"]["name"] for r in bm25}
        hybrid_names = {r["exercise"]["name"] for r in hybrid}
        
        return {
            "query": query,
            "embedding_results": emb,
            "bm25_results": bm25,
            "hybrid_results": hybrid,
            "overlap": {
                "emb_bm25": len(emb_names & bm25_names),
                "emb_hybrid": len(emb_names & hybrid_names),
                "bm25_hybrid": len(bm25_names & hybrid_names),
            },
        }
```

---

## 5. LLM 기반 운동 루틴 생성

### 5-1. 분할법 결정 로직

```python
"""
split_selector.py
사용자 조건에 따라 최적의 운동 분할법을 결정합니다.
"""


def select_split_type(frequency: int, experience: str, goal: str) -> dict:
    """
    주당 운동 횟수, 경험 수준, 목표에 따라 분할법을 결정합니다.
    
    분할법 종류:
    - 전신 (Full Body): 주 2~3회, 입문~초급
    - 상하 분할 (Upper/Lower): 주 4회, 초급~중급
    - PPL (Push/Pull/Legs): 주 3~6회, 중급~고급
    - 부위별 분할 (Bro Split): 주 5회, 중급~고급
    """
    if frequency <= 2 or experience == "입문":
        return {
            "split_type": "전신",
            "description": "전신 운동을 매 세션마다 수행합니다",
            "sessions": [
                {"day": f"Day {i+1}", "focus": "전신"} for i in range(frequency)
            ],
        }
    
    elif frequency == 3:
        if experience in ["입문", "초급"]:
            return {
                "split_type": "전신",
                "description": "전신 운동을 주 3회 수행합니다",
                "sessions": [
                    {"day": "Day 1", "focus": "전신 A"},
                    {"day": "Day 2", "focus": "전신 B"},
                    {"day": "Day 3", "focus": "전신 C"},
                ],
            }
        else:
            return {
                "split_type": "PPL",
                "description": "Push/Pull/Legs로 분할합니다",
                "sessions": [
                    {"day": "Day 1", "focus": "Push (가슴+어깨+삼두)"},
                    {"day": "Day 2", "focus": "Pull (등+이두)"},
                    {"day": "Day 3", "focus": "Legs (하체+코어)"},
                ],
            }
    
    elif frequency == 4:
        return {
            "split_type": "상하분할",
            "description": "상체와 하체를 번갈아 수행합니다",
            "sessions": [
                {"day": "Day 1", "focus": "상체 A (가슴+삼두)"},
                {"day": "Day 2", "focus": "하체 A (스쿼트 중심)"},
                {"day": "Day 3", "focus": "상체 B (등+이두)"},
                {"day": "Day 4", "focus": "하체 B (힙힌지 중심)"},
            ],
        }
    
    else:  # 5회 이상
        return {
            "split_type": "부위별분할",
            "description": "매일 다른 근육군을 집중 훈련합니다",
            "sessions": [
                {"day": "Day 1", "focus": "가슴"},
                {"day": "Day 2", "focus": "등"},
                {"day": "Day 3", "focus": "어깨"},
                {"day": "Day 4", "focus": "하체"},
                {"day": "Day 5", "focus": "팔 + 코어"},
            ],
        }
```

### 5-2. LLM 프롬프트

```python
"""
workout_prompts.py
운동 루틴 생성을 위한 LLM 프롬프트입니다.
"""

WORKOUT_GENERATION_PROMPT = """
당신은 공인 피트니스 트레이너(CSCS)입니다.

아래 사용자 정보와 분할법을 바탕으로 주간 운동 루틴을 생성해주세요.

[사용자 정보]
- 성별: {gender}, 나이: {age}세, 체중: {weight_kg}kg
- 체지방률: {body_fat_percent}%
- 운동 목표: {goal_type}
- 운동 경험: {experience_level}
- 주당 운동 횟수: {frequency}회
- 제약사항: {constraints}
- 일일 섭취 칼로리: {intake_kcal}kcal
- 탄수화물: {carb_g}g (운동 에너지)

[분할법]
- 방식: {split_type}
- 세션 구성: {sessions}

[생성 규칙]
1. 각 세션마다 워밍업(5~10분), 메인 운동(4~6종), 쿨다운(5~10분)을 포함하세요.
2. 제약사항에 해당하는 운동은 반드시 제외하고 대체 운동을 넣으세요.
   - 예: "무릎 부상" → 스쿼트 대신 레그프레스/힙쓰러스트
3. 경험 수준에 맞는 세트수/횟수/휴식시간을 설정하세요.
4. 각 운동마다 수행 방법을 한 줄로 설명하세요.
5. 목표에 따라 유산소 운동 비율을 조정하세요.
   - 체지방감소: 무산소 60% + 유산소 40%
   - 근력증가: 무산소 85% + 유산소 15%
   - 체력향상: 무산소 40% + 유산소 60%
6. 예상 운동 시간(분)과 소모 칼로리를 각 세션에 표기하세요.

아래 JSON 형식으로만 응답하세요:
{{
  "weekly_plan": {{
    "day1": {{
      "day_label": "<요일>",
      "focus": "<운동 부위>",
      "estimated_time_min": <숫자>,
      "estimated_calories": <숫자>,
      "warmup": {{
        "exercises": [{{"name": "<이름>", "duration_min": <숫자>, "description": "<설명>"}}]
      }},
      "main_workout": {{
        "exercises": [
          {{
            "name": "<운동명>",
            "target_muscle": "<주요 근육>",
            "sets": <숫자>,
            "reps": "<횟수>",
            "rest_sec": <숫자>,
            "intensity": "<저|중|고>",
            "description": "<수행 방법>",
            "alternatives": ["<대체 운동1>", "<대체 운동2>"],
            "caution": "<주의사항 또는 null>"
          }}
        ]
      }},
      "cooldown": {{
        "exercises": [{{"name": "<이름>", "duration_min": <숫자>, "description": "<설명>"}}]
      }},
      "tip": "<오늘의 운동 팁>"
    }},
    ...
  }},
  "rest_days": ["<휴식 요일1>", "<휴식 요일2>"]
}}
"""
```

### 5-3. 제약사항 기반 운동 필터링

```python
"""
constraint_filter.py
제약사항에 따라 위험한 운동을 자동 필터링하고 대체 운동을 추천합니다.
"""

CONSTRAINT_EXERCISE_RULES = {
    "무릎 부상": {
        "forbidden": ["스쿼트", "런지", "점프 스쿼트", "박스 점프", "트레드밀 달리기"],
        "alternatives": {
            "스쿼트": "레그프레스 (가동범위 제한)",
            "런지": "힙쓰러스트",
            "트레드밀 달리기": "사이클 또는 일립티컬",
        },
        "general_advice": "무릎 굴곡 90도 이상 피하기, 충격이 적은 운동 선택",
    },
    "허리 부상": {
        "forbidden": ["데드리프트", "굿모닝", "바벨 로우", "싯업", "레그레이즈"],
        "alternatives": {
            "데드리프트": "힙쓰러스트",
            "바벨 로우": "머신 시티드 로우 (등받이 지지)",
            "싯업": "데드버그 또는 버드독",
        },
        "general_advice": "척추 중립 유지, 과도한 전방 굴곡 피하기",
    },
    "어깨 부상": {
        "forbidden": ["오버헤드프레스", "비하인드넥 프레스", "업라이트 로우", "딥스"],
        "alternatives": {
            "오버헤드프레스": "래터럴레이즈 (가벼운 무게)",
            "딥스": "머신 체스트프레스",
        },
        "general_advice": "오버헤드 동작 최소화, 외회전 강화 운동 추가",
    },
    "고혈압": {
        "forbidden": [],
        "alternatives": {},
        "general_advice": "발살바 호흡법 피하기, 고중량 피하기, 유산소 비율 높이기",
    },
    "당뇨": {
        "forbidden": [],
        "alternatives": {},
        "general_advice": "운동 전 혈당 확인, 저혈당 대비 간식 준비, 공복 운동 피하기",
    },
}


def filter_exercises(
    exercises: list[dict],
    constraints: list[str],
) -> list[dict]:
    """제약사항에 따라 운동을 필터링하고 대체 운동을 적용합니다."""
    forbidden_set = set()
    for constraint in constraints:
        rules = CONSTRAINT_EXERCISE_RULES.get(constraint, {})
        forbidden_set.update(rules.get("forbidden", []))
    
    filtered = []
    for ex in exercises:
        if ex["name"] not in forbidden_set:
            filtered.append(ex)
    
    return filtered


def get_exercise_warnings(constraints: list[str]) -> list[str]:
    """제약사항에 따른 운동 시 주의사항을 반환합니다."""
    warnings = []
    for constraint in constraints:
        rules = CONSTRAINT_EXERCISE_RULES.get(constraint, {})
        advice = rules.get("general_advice")
        if advice:
            warnings.append(f"[{constraint}] {advice}")
    return warnings
```

---

## 6. 칼로리 소모량 계산

```python
"""
calorie_calculator.py
운동별 칼로리 소모량을 MET 값 기반으로 계산합니다.

MET(Metabolic Equivalent of Task):
  1 MET = 1 kcal/kg/hour (안정 시 대사율)
  칼로리 소모 = MET × 체중(kg) × 시간(hour)
"""


def calculate_exercise_calories(
    met_value: float,
    weight_kg: float,
    duration_min: int,
) -> int:
    """
    운동별 칼로리 소모량을 계산합니다.
    
    Args:
        met_value: 운동의 MET 값
        weight_kg: 사용자 체중 (kg)
        duration_min: 운동 시간 (분)
    
    Returns:
        예상 칼로리 소모량 (kcal)
    
    사용 예시:
        # 59.1kg 사용자가 30분 사이클 (MET 5.5)
        cal = calculate_exercise_calories(5.5, 59.1, 30)
        # → 163 kcal
    """
    duration_hour = duration_min / 60
    calories = met_value * weight_kg * duration_hour
    return round(calories)


def calculate_session_calories(
    exercises: list[dict],
    weight_kg: float,
) -> int:
    """한 세션의 총 칼로리 소모량을 계산합니다."""
    total = 0
    for ex in exercises:
        # 무산소 운동: 세트수 × 횟수 기반 시간 추정
        if ex.get("category") == "무산소":
            sets = ex.get("sets", 3)
            rest_sec = ex.get("rest_sec", 60)
            estimated_min = (sets * 0.5) + (sets * rest_sec / 60)
        else:
            estimated_min = int(ex.get("reps", "30").replace("분", "").split("~")[0])
        
        met = ex.get("met_value", 4.0)
        total += calculate_exercise_calories(met, weight_kg, estimated_min)
    
    return total
```

---

## 7. React 프론트엔드 가이드

### 7-1. 운동 루틴 페이지 컴포넌트 구조

```
WorkoutPage/
├── WeeklyOverview             ← 주간 요약 카드 (총 세션/시간/칼로리)
│   └── MuscleBalanceChart     ← 근육군 균형 레이더 차트
├── DayCard (×N)               ← 요일별 운동 카드
│   ├── DayHeader              ← 요일 + 부위 + 예상 시간/칼로리
│   ├── WarmupSection          ← 워밍업 운동 리스트
│   ├── MainWorkoutList        ← 메인 운동 리스트
│   │   └── ExerciseRow        ← 운동명, 세트/횟수, 강도 표시
│   │       ├── ExerciseDetail ← 접기/펼치기 상세 정보 (검색 결과)
│   │       └── AlternativeBtn ← 대체 운동 보기 버튼
│   ├── CooldownSection        ← 쿨다운 운동 리스트
│   └── DayTip                 ← 오늘의 운동 팁
├── ConstraintWarnings         ← 제약사항 경고 배너
├── ExerciseSearchPanel        ← 운동 정보 검색 패널
│   ├── SearchInput            ← 자연어 검색 입력
│   ├── SearchMethodToggle     ← 임베딩/BM25/하이브리드 전환
│   └── SearchResults          ← 검색 결과 리스트 + 점수 비교
└── ModelComparisonPanel       ← LLM 생성 vs 검색 기반 비교
```

### 7-2. API 엔드포인트

```
POST /api/v1/workout/generate
  - Body: { "user_profile": {...}, "meal_plan": {...},
            "model": "gpt-4o", "temperature": 0.7 }
  - Response: WorkoutPlan JSON

GET  /api/v1/workout/search?q=가슴+운동+초보자&method=hybrid
  - Response: [SearchResult, ...]

GET  /api/v1/workout/search/compare?q=무릎+부담+적은+하체+운동
  - Response: { "embedding": [...], "bm25": [...], "hybrid": [...] }

GET  /api/v1/workout/exercise/{name}
  - Response: ExerciseDetail JSON

POST /api/v1/workout/validate
  - Body: { "workout_plan": {...}, "constraints": [...] }
  - Response: ValidationResult JSON
```

---

## 8. 비교 실험 설계

| 실험 축 | 비교 대상 | 평가 지표 |
|---------|---------|---------|
| **루틴 생성** | OpenAI vs EXAONE | 제약 준수율, 분할법 적절성, 운동 다양성 |
| **검색 엔진** | 임베딩 vs BM25 vs 하이브리드 | nDCG, 적합성 점수, 응답 속도 |
| **LLM vs 검색** | LLM이 선택한 운동 vs 검색 결과 top-K | 일치율, 전문가 평가 |
| **temperature** | 0.3 vs 0.7 vs 1.0 | 운동 다양성, 제약 준수율 |

```python
# ── 검색 비교 테스트 쿼리 세트 ──
SEARCH_TEST_QUERIES = [
    {"query": "초보자 가슴 운동 맨몸", "expected": ["푸쉬업", "인클라인 푸쉬업"]},
    {"query": "무릎에 부담 적은 하체 운동", "expected": ["레그프레스", "힙쓰러스트", "사이클"]},
    {"query": "어깨 넓어지는 운동 덤벨", "expected": ["래터럴레이즈", "덤벨 숄더프레스"]},
    {"query": "뱃살 빼는 유산소 운동", "expected": ["사이클", "트레드밀 걷기", "일립티컬"]},
    {"query": "허리 안 아픈 등 운동", "expected": ["랫풀다운", "머신 시티드 로우"]},
]
```

---

## 9. 4단계(피드백)로의 연결

```
전(轉) 운동 루틴 출력
    │
    └──▶ 결(結) 피드백
         ├─ 운동 계획 vs 실제 수행 비교
         ├─ 근육군 균형 추적
         └─ 운동 일지 작성 시 계획 참조
```

---

## 10. 체크리스트 (v1.1 현황)

### 필수 구현

- [x] 운동 정보 DB 구축 ✅ `exercise_db.json` (24종, 11개 근육군) + MET 테이블 (30종)
- [x] 분할법 자동 선택 로직 ✅ `workout_prompts.py` (전신/상하/부위별/PPL)
- [x] LLM 운동 루틴 생성 (EXAONE 3.5) ✅ `workout_generator.py`
- [x] 제약사항 기반 운동 필터링 + 대체 운동 ✅ `exercise_search.py`
- [x] 임베딩 검색 (sentence-transformers) ✅ `exercise_search.py`
- [x] BM25 키워드 검색 (rank_bm25) ✅ `exercise_search.py`
- [x] 하이브리드 검색 통합 (BM25 + 필터 + 임베딩) ✅
- [x] MET 기반 칼로리 소모량 계산 ✅ `exercise_met.json` (30종)
- [x] React 운동 루틴 페이지 UI ✅ 3탭 (AI트레이너 + 상세루틴 + 저장이력)
- [x] AI 트레이너 챗봇 ✅ `WorkoutChatPanel` — 대화하며 루틴 생성/수정
- [x] 면책 문구 상단 표시 ✅ DISCLAIMER 상수
- [x] 7일 캘린더 UI (요일별 운동/휴식 표시) ✅
- [x] 루틴 균형 분석 (근육군 커버리지, 유산소 비율) ✅ `workout_analyzer.py`
- [x] 루틴 저장/조회/삭제 API ✅ `/api/v1/workout/save`, `history`, `delete`
- [x] 페이지 새로고침 시 최근 루틴 자동 복원 ✅

### 비교 분석

- [x] BM25 vs 필터 vs 임베딩 검색 비교 ✅ 하이브리드(BM25+필터) 채택
- [x] 루틴 균형 점수 평가 ✅ 73.9/100 (체지방감소 데모 기준)
- [ ] EXAONE vs Qwen 루틴 생성 비교
- [ ] temperature별 운동 다양성 비교

### 고도화 (선택)

- [x] 데모 루틴 (LLM 없이 즉시 생성) ✅ `/api/v1/workout/demo`
- [ ] 운동 DB 확장 (24종 → 50~100종)
- [ ] 운동 영상 링크 연결 (YouTube API)
- [ ] 점진적 과부하 (Progressive Overload) 추적
- [ ] 운동 부위별 근육 해부도 시각화

---

> **💡 핵심 원칙**: 3단계의 차별점은 **LLM 생성과 검색 기반 추천의 비교**입니다.
> LLM은 사용자 맥락을 이해한 창의적 루틴을 제공하고,
> 검색 엔진은 데이터 기반의 정확한 운동 정보를 제공합니다.
> 두 접근법의 결과를 비교·분석하여 **어떤 방식이 더 효과적인지 인사이트를 도출**하는 것이 핵심입니다.
