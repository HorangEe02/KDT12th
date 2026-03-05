"""
data_manager.py
데이터 저장 및 관리 클래스

Author: KDT12 Python Project
Date: 2026-01-08
"""

import csv
import os
from datetime import datetime


class DataManager:
    """
    건강 데이터를 CSV 파일로 관리하는 클래스
    
    Attributes:
        user_file (str): 사용자 기록 파일 경로
        sample_file (str): 샘플 데이터 파일 경로
    """
    
    def __init__(self, user_file="data/user_records.csv", sample_file="data/sample_data.csv"):
        """생성자: 파일 경로 설정"""
        # 실행 위치 기준 경로 설정
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.user_file = os.path.join(self.base_path, user_file)
        self.sample_file = os.path.join(self.base_path, sample_file)
        
        # 파일이 없으면 생성
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """파일이 없으면 헤더와 함께 생성"""
        if not os.path.exists(self.user_file):
            # 디렉토리 생성
            os.makedirs(os.path.dirname(self.user_file), exist_ok=True)
            
            # 헤더 작성
            with open(self.user_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "date", "name", "age", "gender", "height", "weight",
                    "ap_hi", "ap_lo", "cholesterol", "gluc",
                    "smoke", "alco", "active", "bmi", "risk_score"
                ])
    
    def save_record(self, name, data_dict):
        """
        새로운 건강 기록 저장
        
        Args:
            name (str): 사용자 이름
            data_dict (dict): 건강 데이터 딕셔너리
        
        Returns:
            bool: 저장 성공 여부
        """
        try:
            # 현재 날짜 추가
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            with open(self.user_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    current_date,
                    name,
                    data_dict["age"],
                    data_dict["gender"],
                    data_dict["height"],
                    data_dict["weight"],
                    data_dict["ap_hi"],
                    data_dict["ap_lo"],
                    data_dict["cholesterol"],
                    data_dict["gluc"],
                    data_dict["smoke"],
                    data_dict["alco"],
                    data_dict["active"],
                    data_dict["bmi"],
                    data_dict["risk_score"]
                ])
            return True
        except Exception as e:
            print(f"저장 오류: {e}")
            return False
    
    def load_records(self):
        """
        모든 사용자 기록 불러오기
        
        Returns:
            list: 기록 딕셔너리 리스트
        """
        records = []
        try:
            with open(self.user_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    records.append(row)
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"불러오기 오류: {e}")
        
        return records
    
    def delete_record(self, index):
        """
        특정 기록 삭제
        
        Args:
            index (int): 삭제할 레코드 인덱스 (0부터 시작)
        
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            records = self.load_records()
            
            if 0 <= index < len(records):
                del records[index]
                
                # 파일 다시 쓰기
                with open(self.user_file, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    # 헤더 작성
                    writer.writerow([
                        "date", "name", "age", "gender", "height", "weight",
                        "ap_hi", "ap_lo", "cholesterol", "gluc",
                        "smoke", "alco", "active", "bmi", "risk_score"
                    ])
                    # 데이터 작성
                    for record in records:
                        writer.writerow(list(record.values()))
                
                return True
            return False
        except Exception as e:
            print(f"삭제 오류: {e}")
            return False
    
    def load_sample_data(self):
        """
        Kaggle 샘플 데이터 불러오기
        
        Returns:
            list: 샘플 데이터 딕셔너리 리스트
        """
        samples = []
        try:
            with open(self.sample_file, "r", encoding="utf-8") as f:
                # 세미콜론 구분자 사용 (Kaggle 원본 형식)
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    # 나이를 일(days)에서 년(years)으로 변환
                    age_days = int(row.get("age", 0))
                    age_years = age_days // 365
                    
                    # 성별 변환 (1: 여성, 2: 남성)
                    gender = "여성" if row.get("gender") == "1" else "남성"
                    
                    samples.append({
                        "id": row.get("id"),
                        "age": age_years,
                        "gender": gender,
                        "height": int(row.get("height", 0)),
                        "weight": float(row.get("weight", 0)),
                        "ap_hi": int(row.get("ap_hi", 0)),
                        "ap_lo": int(row.get("ap_lo", 0)),
                        "cholesterol": int(row.get("cholesterol", 1)),
                        "gluc": int(row.get("gluc", 1)),
                        "smoke": int(row.get("smoke", 0)),
                        "alco": int(row.get("alco", 0)),
                        "active": int(row.get("active", 0)),
                        "cardio": int(row.get("cardio", 0))
                    })
        except FileNotFoundError:
            print("샘플 데이터 파일을 찾을 수 없습니다.")
        except Exception as e:
            print(f"샘플 데이터 로드 오류: {e}")
        
        return samples
    
    def get_statistics(self, gender=None):
        """
        샘플 데이터 기반 통계 계산 (성별 필터 지원)
        
        Args:
            gender (str, optional): "남성" 또는 "여성". None이면 전체 통계
        
        Returns:
            dict: 통계 데이터
        """
        samples = self.load_sample_data()
        
        if not samples:
            return None
        
        # 성별 필터링
        if gender:
            samples = [s for s in samples if s["gender"] == gender]
        
        if not samples:
            return None
        
        total = len(samples)
        
        # 평균 계산
        avg_age = sum(s["age"] for s in samples) / total
        avg_height = sum(s["height"] for s in samples) / total
        avg_weight = sum(s["weight"] for s in samples) / total
        avg_ap_hi = sum(s["ap_hi"] for s in samples) / total
        avg_ap_lo = sum(s["ap_lo"] for s in samples) / total
        
        # BMI 계산
        bmi_list = []
        for s in samples:
            if s["height"] > 0:
                bmi = s["weight"] / ((s["height"] / 100) ** 2)
                bmi_list.append(bmi)
        avg_bmi = sum(bmi_list) / len(bmi_list) if bmi_list else 0
        
        # 심혈관 질환 비율
        cardio_count = sum(1 for s in samples if s["cardio"] == 1)
        cardio_rate = (cardio_count / total) * 100
        
        # 흡연자 비율
        smoke_count = sum(1 for s in samples if s["smoke"] == 1)
        smoke_rate = (smoke_count / total) * 100
        
        # 고콜레스테롤 비율
        high_chol_count = sum(1 for s in samples if s["cholesterol"] >= 2)
        high_chol_rate = (high_chol_count / total) * 100
        
        return {
            "gender": gender if gender else "전체",
            "total_samples": total,
            "avg_age": round(avg_age, 1),
            "avg_height": round(avg_height, 1),
            "avg_weight": round(avg_weight, 1),
            "avg_bmi": round(avg_bmi, 1),
            "avg_ap_hi": round(avg_ap_hi, 1),
            "avg_ap_lo": round(avg_ap_lo, 1),
            "cardio_rate": round(cardio_rate, 1),
            "smoke_rate": round(smoke_rate, 1),
            "high_chol_rate": round(high_chol_rate, 1)
        }
    
    def get_gender_statistics(self):
        """
        남성/여성 각각의 통계 반환
        
        Returns:
            dict: {"male": {...}, "female": {...}, "total": {...}}
        """
        return {
            "male": self.get_statistics("남성"),
            "female": self.get_statistics("여성"),
            "total": self.get_statistics(None)
        }
    
    def compare_with_sample(self, user_data):
        """
        사용자 데이터를 샘플 평균과 비교
        
        Args:
            user_data (dict): 사용자 건강 데이터
        
        Returns:
            dict: 비교 결과
        """
        stats = self.get_statistics()
        
        if not stats:
            return None
        
        comparison = {}
        
        # BMI 비교
        user_bmi = user_data.get("bmi", 0)
        if user_bmi > stats["avg_bmi"]:
            comparison["bmi"] = f"평균보다 {round(user_bmi - stats['avg_bmi'], 1)} 높음"
        else:
            comparison["bmi"] = f"평균보다 {round(stats['avg_bmi'] - user_bmi, 1)} 낮음"
        
        # 혈압 비교
        user_ap = user_data.get("ap_hi", 0)
        if user_ap > stats["avg_ap_hi"]:
            comparison["bp"] = f"수축기 혈압이 평균보다 {round(user_ap - stats['avg_ap_hi'], 1)} 높음"
        else:
            comparison["bp"] = f"수축기 혈압이 평균보다 {round(stats['avg_ap_hi'] - user_ap, 1)} 낮음"
        
        return comparison
    
    def compare_with_gender_average(self, user_data, gender):
        """
        사용자 데이터를 해당 성별 평균과 비교
        
        Args:
            user_data (dict): 사용자 건강 데이터
            gender (str): "남성" 또는 "여성"
        
        Returns:
            dict: 비교 결과
        """
        stats = self.get_statistics(gender)
        
        if not stats:
            return None
        
        comparison = {
            "gender": gender,
            "sample_count": stats["total_samples"]
        }
        
        # BMI 비교
        user_bmi = user_data.get("bmi", 0)
        diff_bmi = user_bmi - stats["avg_bmi"]
        if diff_bmi > 0:
            comparison["bmi"] = {"diff": round(diff_bmi, 1), "status": "higher", "text": f"평균보다 {abs(round(diff_bmi, 1))} 높음 ▲"}
        elif diff_bmi < 0:
            comparison["bmi"] = {"diff": round(diff_bmi, 1), "status": "lower", "text": f"평균보다 {abs(round(diff_bmi, 1))} 낮음 ▼"}
        else:
            comparison["bmi"] = {"diff": 0, "status": "same", "text": "평균과 동일"}
        comparison["bmi"]["avg"] = stats["avg_bmi"]
        comparison["bmi"]["user"] = round(user_bmi, 1)
        
        # 키 비교
        user_height = user_data.get("height", 0)
        diff_height = user_height - stats["avg_height"]
        if diff_height > 0:
            comparison["height"] = {"diff": round(diff_height, 1), "status": "higher", "text": f"평균보다 {abs(round(diff_height, 1))}cm 큼 ▲"}
        elif diff_height < 0:
            comparison["height"] = {"diff": round(diff_height, 1), "status": "lower", "text": f"평균보다 {abs(round(diff_height, 1))}cm 작음 ▼"}
        else:
            comparison["height"] = {"diff": 0, "status": "same", "text": "평균과 동일"}
        comparison["height"]["avg"] = stats["avg_height"]
        comparison["height"]["user"] = user_height
        
        # 몸무게 비교
        user_weight = user_data.get("weight", 0)
        diff_weight = user_weight - stats["avg_weight"]
        if diff_weight > 0:
            comparison["weight"] = {"diff": round(diff_weight, 1), "status": "higher", "text": f"평균보다 {abs(round(diff_weight, 1))}kg 많음 ▲"}
        elif diff_weight < 0:
            comparison["weight"] = {"diff": round(diff_weight, 1), "status": "lower", "text": f"평균보다 {abs(round(diff_weight, 1))}kg 적음 ▼"}
        else:
            comparison["weight"] = {"diff": 0, "status": "same", "text": "평균과 동일"}
        comparison["weight"]["avg"] = stats["avg_weight"]
        comparison["weight"]["user"] = user_weight
        
        # 수축기 혈압 비교
        user_ap_hi = user_data.get("ap_hi", 0)
        diff_ap_hi = user_ap_hi - stats["avg_ap_hi"]
        if diff_ap_hi > 0:
            comparison["ap_hi"] = {"diff": round(diff_ap_hi, 1), "status": "higher", "text": f"평균보다 {abs(round(diff_ap_hi, 1))}mmHg 높음 ▲"}
        elif diff_ap_hi < 0:
            comparison["ap_hi"] = {"diff": round(diff_ap_hi, 1), "status": "lower", "text": f"평균보다 {abs(round(diff_ap_hi, 1))}mmHg 낮음 ▼"}
        else:
            comparison["ap_hi"] = {"diff": 0, "status": "same", "text": "평균과 동일"}
        comparison["ap_hi"]["avg"] = stats["avg_ap_hi"]
        comparison["ap_hi"]["user"] = user_ap_hi
        
        # 이완기 혈압 비교
        user_ap_lo = user_data.get("ap_lo", 0)
        diff_ap_lo = user_ap_lo - stats["avg_ap_lo"]
        if diff_ap_lo > 0:
            comparison["ap_lo"] = {"diff": round(diff_ap_lo, 1), "status": "higher", "text": f"평균보다 {abs(round(diff_ap_lo, 1))}mmHg 높음 ▲"}
        elif diff_ap_lo < 0:
            comparison["ap_lo"] = {"diff": round(diff_ap_lo, 1), "status": "lower", "text": f"평균보다 {abs(round(diff_ap_lo, 1))}mmHg 낮음 ▼"}
        else:
            comparison["ap_lo"] = {"diff": 0, "status": "same", "text": "평균과 동일"}
        comparison["ap_lo"]["avg"] = stats["avg_ap_lo"]
        comparison["ap_lo"]["user"] = user_ap_lo
        
        # 심혈관 질환 비율 정보
        comparison["cardio_rate"] = stats["cardio_rate"]
        
        return comparison


# 테스트 코드
if __name__ == "__main__":
    # 테스트용 데이터 매니저 생성
    dm = DataManager()
    
    print("=" * 50)
    print("데이터 매니저 테스트")
    print("=" * 50)
    
    # 샘플 데이터 통계
    stats = dm.get_statistics()
    if stats:
        print(f"\n📊 샘플 데이터 통계 (총 {stats['total_samples']}명)")
        print(f"   평균 나이: {stats['avg_age']}세")
        print(f"   평균 키: {stats['avg_height']}cm")
        print(f"   평균 몸무게: {stats['avg_weight']}kg")
        print(f"   평균 BMI: {stats['avg_bmi']}")
        print(f"   평균 수축기 혈압: {stats['avg_ap_hi']}mmHg")
        print(f"   심혈관 질환 비율: {stats['cardio_rate']}%")
        print(f"   흡연자 비율: {stats['smoke_rate']}%")
    
    # 기록 저장 테스트
    test_data = {
        "age": 35,
        "gender": "남성",
        "height": 175,
        "weight": 70,
        "ap_hi": 120,
        "ap_lo": 80,
        "cholesterol": 1,
        "gluc": 1,
        "smoke": 0,
        "alco": 0,
        "active": 1,
        "bmi": 22.9,
        "risk_score": 15
    }
    
    print(f"\n📝 테스트 기록 저장...")
    if dm.save_record("테스트", test_data):
        print("   저장 성공!")
    
    # 기록 불러오기
    records = dm.load_records()
    print(f"\n📋 저장된 기록: {len(records)}건")
    for i, record in enumerate(records):
        print(f"   [{i}] {record.get('date')} - {record.get('name')}")
