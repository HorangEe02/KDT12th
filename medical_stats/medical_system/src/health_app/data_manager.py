"""
data_manager.py
건강 데이터 관리 클래스

Author: KDT12 Python Project
Date: 2026-01-09
"""

import csv
import os
from datetime import datetime


class HealthDataManager:
    """건강 데이터를 CSV 파일로 관리하는 클래스"""
    
    def __init__(self, base_path=None):
        """생성자: 파일 경로 설정"""
        if base_path is None:
            self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        else:
            self.base_path = base_path
        
        self.user_file = os.path.join(self.base_path, "data", "health_records.csv")
        self.sample_file = os.path.join(self.base_path, "data", "cardiovascular_sample.csv")
        
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """파일이 없으면 헤더와 함께 생성"""
        if not os.path.exists(self.user_file):
            os.makedirs(os.path.dirname(self.user_file), exist_ok=True)
            with open(self.user_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "date", "patient_id", "name", "age", "gender", "height", "weight",
                    "ap_hi", "ap_lo", "cholesterol", "gluc",
                    "smoke", "alco", "active", "bmi", "risk_score",
                    "doctor", "hospital", "room_number", "admission_type", "test_results", "billing_amount"
                ])
    
    def save_record(self, name, data_dict):
        """새로운 건강 기록 저장 (기존 호환)"""
        return self.save_record_with_patient_id("", name, data_dict)
    
    def save_record_with_patient_id(self, patient_id, name, data_dict):
        """환자 ID와 함께 새로운 건강 기록 저장"""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            with open(self.user_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    current_date, patient_id, name,
                    data_dict["age"], data_dict["gender"],
                    data_dict["height"], data_dict["weight"],
                    data_dict["ap_hi"], data_dict["ap_lo"],
                    data_dict["cholesterol"], data_dict["gluc"],
                    data_dict["smoke"], data_dict["alco"],
                    data_dict["active"], data_dict["bmi"],
                    data_dict["risk_score"],
                    data_dict.get("doctor", ""),
                    data_dict.get("hospital", ""),
                    data_dict.get("room_number", "0"),
                    data_dict.get("admission_type", "Elective"),
                    data_dict.get("test_results", "Normal"),
                    data_dict.get("billing_amount", "0")
                ])
            return True
        except Exception as e:
            print(f"저장 오류: {e}")
            return False
    
    def load_records(self):
        """모든 사용자 기록 불러오기"""
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
    
    def load_sample_data(self):
        """Kaggle 샘플 데이터 불러오기"""
        samples = []
        try:
            with open(self.sample_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    age_days = int(row.get("age", 0))
                    age_years = age_days // 365
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
        """샘플 데이터 기반 통계 계산 (성별 필터 지원)"""
        samples = self.load_sample_data()
        
        if not samples:
            return None
        
        if gender:
            samples = [s for s in samples if s["gender"] == gender]
        
        if not samples:
            return None
        
        total = len(samples)
        
        avg_age = sum(s["age"] for s in samples) / total
        avg_height = sum(s["height"] for s in samples) / total
        avg_weight = sum(s["weight"] for s in samples) / total
        avg_ap_hi = sum(s["ap_hi"] for s in samples) / total
        avg_ap_lo = sum(s["ap_lo"] for s in samples) / total
        
        bmi_list = []
        for s in samples:
            if s["height"] > 0:
                bmi = s["weight"] / ((s["height"] / 100) ** 2)
                bmi_list.append(bmi)
        avg_bmi = sum(bmi_list) / len(bmi_list) if bmi_list else 0
        
        cardio_count = sum(1 for s in samples if s["cardio"] == 1)
        cardio_rate = (cardio_count / total) * 100
        
        smoke_count = sum(1 for s in samples if s["smoke"] == 1)
        smoke_rate = (smoke_count / total) * 100
        
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
        """남성/여성 각각의 통계 반환"""
        return {
            "male": self.get_statistics("남성"),
            "female": self.get_statistics("여성"),
            "total": self.get_statistics(None)
        }
    
    def compare_with_gender_average(self, user_data, gender):
        """사용자 데이터를 해당 성별 평균과 비교"""
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
        
        comparison["cardio_rate"] = stats["cardio_rate"]
        
        return comparison
