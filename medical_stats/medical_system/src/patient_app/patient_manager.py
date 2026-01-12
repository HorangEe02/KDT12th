"""
patient_manager.py
환자 데이터 CRUD 관리 클래스

Author: KDT12 Python Project
Date: 2026-01-09
"""

import csv
import os
from datetime import datetime
from .patient import Patient


class PatientManager:
    """환자 데이터를 관리하는 CRUD 클래스"""
    
    CSV_HEADERS = [
        "patient_id", "name", "age", "gender", "blood_type",
        "medical_condition", "date_of_admission", "doctor", "hospital",
        "insurance_provider", "billing_amount", "room_number",
        "admission_type", "discharge_date", "medication", "test_results"
    ]
    
    def __init__(self, base_path=None):
        """생성자"""
        if base_path is None:
            # 현재 파일 기준으로 상위 폴더 찾기
            current_file = os.path.abspath(__file__)
            # patient_manager.py -> patient_app -> src -> medical_system
            self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        else:
            self.base_path = base_path
        
        self.file_path = os.path.join(self.base_path, "data", "patients.csv")
        self.patients = []
        
        # 디버깅용 출력 (문제 발생 시 확인용)
        print(f"[PatientManager] base_path: {self.base_path}")
        print(f"[PatientManager] file_path: {self.file_path}")
        print(f"[PatientManager] file exists: {os.path.exists(self.file_path)}")
        
        self.load_from_file()
    
    def load_from_file(self):
        """CSV 파일에서 데이터 로드"""
        self.patients = []
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        patient = Patient.from_dict(row)
                        self.patients.append(patient)
                return True
            else:
                self._create_empty_file()
                return True
        except Exception as e:
            print(f"파일 로드 오류: {e}")
            return False
    
    def _create_empty_file(self):
        """빈 CSV 파일 생성"""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.CSV_HEADERS)
    
    def save_to_file(self):
        """데이터를 CSV 파일에 저장"""
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)
                writer.writeheader()
                for patient in self.patients:
                    writer.writerow(patient.to_dict())
            return True
        except Exception as e:
            print(f"파일 저장 오류: {e}")
            return False
    
    def generate_id(self):
        """새 환자 ID 생성"""
        if not self.patients:
            return "P001"
        
        max_id = 0
        for patient in self.patients:
            try:
                num = int(patient.patient_id[1:])
                if num > max_id:
                    max_id = num
            except (ValueError, IndexError):
                continue
        
        return f"P{max_id + 1:03d}"
    
    def create(self, data):
        """새 환자 등록"""
        new_id = self.generate_id()
        data["patient_id"] = new_id
        
        if not data.get("date_of_admission"):
            data["date_of_admission"] = datetime.now().strftime("%Y-%m-%d")
        
        patient = Patient.from_dict(data)
        
        is_valid, error_msg = patient.validate()
        if not is_valid:
            return (False, error_msg)
        
        self.patients.append(patient)
        
        if self.save_to_file():
            return (True, new_id)
        else:
            self.patients.pop()
            return (False, "파일 저장에 실패했습니다.")
    
    def read_all(self):
        """모든 환자 목록 조회"""
        return self.patients
    
    def read_by_id(self, patient_id):
        """ID로 환자 조회"""
        for patient in self.patients:
            if patient.patient_id == patient_id:
                return patient
        return None
    
    def search(self, keyword, field="all"):
        """환자 검색"""
        keyword = keyword.lower().strip()
        results = []
        
        for patient in self.patients:
            if field == "all":
                searchable = f"{patient.patient_id} {patient.name} {patient.medical_condition} {patient.doctor} {patient.hospital}".lower()
                if keyword in searchable:
                    results.append(patient)
            elif field == "name":
                if keyword in patient.name.lower():
                    results.append(patient)
            elif field == "medical_condition":
                if keyword in patient.medical_condition.lower():
                    results.append(patient)
            elif field == "doctor":
                if keyword in patient.doctor.lower():
                    results.append(patient)
            elif field == "hospital":
                if keyword in patient.hospital.lower():
                    results.append(patient)
        
        return results
    
    def update(self, patient_id, updated_data):
        """환자 정보 수정"""
        patient = self.read_by_id(patient_id)
        if not patient:
            return (False, f"환자 ID {patient_id}를 찾을 수 없습니다.")
        
        backup = patient.to_dict()
        
        for key, value in updated_data.items():
            if hasattr(patient, key) and key != "patient_id":
                setattr(patient, key, value)
        
        is_valid, error_msg = patient.validate()
        if not is_valid:
            for key, value in backup.items():
                setattr(patient, key, value)
            return (False, error_msg)
        
        if self.save_to_file():
            return (True, "환자 정보가 수정되었습니다.")
        else:
            for key, value in backup.items():
                setattr(patient, key, value)
            return (False, "파일 저장에 실패했습니다.")
    
    def delete(self, patient_id):
        """환자 삭제"""
        patient = self.read_by_id(patient_id)
        if not patient:
            return (False, f"환자 ID {patient_id}를 찾을 수 없습니다.")
        
        self.patients.remove(patient)
        
        if self.save_to_file():
            return (True, f"환자 {patient.name}({patient_id})이(가) 삭제되었습니다.")
        else:
            self.patients.append(patient)
            return (False, "파일 저장에 실패했습니다.")
    
    def discharge_patient(self, patient_id, discharge_date=None):
        """환자 퇴원 처리"""
        if not discharge_date:
            discharge_date = datetime.now().strftime("%Y-%m-%d")
        return self.update(patient_id, {"discharge_date": discharge_date})
    
    def get_statistics(self):
        """통계 계산"""
        if not self.patients:
            return None
        
        total = len(self.patients)
        
        male_count = sum(1 for p in self.patients if p.gender == "Male")
        female_count = total - male_count
        
        conditions = {}
        for p in self.patients:
            cond = p.medical_condition
            conditions[cond] = conditions.get(cond, 0) + 1
        
        hospitalized = sum(1 for p in self.patients if p.is_hospitalized())
        avg_age = sum(p.age for p in self.patients) / total
        avg_billing = sum(p.billing_amount for p in self.patients) / total
        total_billing = sum(p.billing_amount for p in self.patients)
        
        return {
            "total_patients": total,
            "male_count": male_count,
            "female_count": female_count,
            "male_ratio": round(male_count / total * 100, 1),
            "female_ratio": round(female_count / total * 100, 1),
            "conditions": conditions,
            "hospitalized_count": hospitalized,
            "discharged_count": total - hospitalized,
            "avg_age": round(avg_age, 1),
            "avg_billing": round(avg_billing, 0),
            "total_billing": round(total_billing, 0)
        }
    
    def get_today_admissions(self):
        """오늘 입원 환자 수"""
        today = datetime.now().strftime("%Y-%m-%d")
        return sum(1 for p in self.patients if p.date_of_admission == today)
