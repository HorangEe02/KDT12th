"""
patient_manager.py
환자 데이터 CRUD 관리 클래스

Author: KDT12 Python Project
Date: 2026-01-09
데이터 출처: Kaggle - Healthcare Dataset
"""

import csv
import os
from datetime import datetime
from patient import Patient


class PatientManager:
    """
    환자 데이터를 관리하는 CRUD 클래스
    
    CSV 파일을 사용하여 환자 정보를 저장하고 관리
    
    Attributes:
        file_path (str): 데이터 파일 경로
        patients (list): Patient 객체 리스트
    """
    
    # CSV 헤더 정의
    CSV_HEADERS = [
        "patient_id", "name", "age", "gender", "blood_type",
        "medical_condition", "date_of_admission", "doctor", "hospital",
        "insurance_provider", "billing_amount", "room_number",
        "admission_type", "discharge_date", "medication", "test_results"
    ]
    
    def __init__(self, file_path="data/patients.csv"):
        """생성자: 파일 경로 설정 및 데이터 로드"""
        # 실행 위치 기준 경로 설정
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.file_path = os.path.join(self.base_path, file_path)
        self.patients = []
        
        # 파일 로드
        self.load_from_file()
    
    def load_from_file(self):
        """
        CSV 파일에서 환자 데이터 로드
        
        Returns:
            bool: 로드 성공 여부
        """
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
                # 파일이 없으면 빈 파일 생성
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
        """
        환자 데이터를 CSV 파일에 저장
        
        Returns:
            bool: 저장 성공 여부
        """
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
        """
        새 환자 ID 생성
        
        Returns:
            str: 새 환자 ID (예: "P031")
        """
        if not self.patients:
            return "P001"
        
        # 기존 ID에서 최대값 찾기
        max_id = 0
        for patient in self.patients:
            try:
                num = int(patient.patient_id[1:])
                if num > max_id:
                    max_id = num
            except (ValueError, IndexError):
                continue
        
        return f"P{max_id + 1:03d}"
    
    # ==================== CRUD 메서드 ====================
    
    def create(self, data):
        """
        새 환자 등록 (Create)
        
        Args:
            data (dict): 환자 정보 딕셔너리
        
        Returns:
            tuple: (성공 여부, 환자 ID 또는 오류 메시지)
        """
        # 새 ID 생성
        new_id = self.generate_id()
        data["patient_id"] = new_id
        
        # 입원일 자동 설정
        if not data.get("date_of_admission"):
            data["date_of_admission"] = datetime.now().strftime("%Y-%m-%d")
        
        # Patient 객체 생성
        patient = Patient.from_dict(data)
        
        # 유효성 검사
        is_valid, error_msg = patient.validate()
        if not is_valid:
            return (False, error_msg)
        
        # 리스트에 추가
        self.patients.append(patient)
        
        # 파일 저장
        if self.save_to_file():
            return (True, new_id)
        else:
            # 저장 실패 시 롤백
            self.patients.pop()
            return (False, "파일 저장에 실패했습니다.")
    
    def read_all(self):
        """
        모든 환자 목록 조회 (Read)
        
        Returns:
            list: Patient 객체 리스트
        """
        return self.patients
    
    def read_by_id(self, patient_id):
        """
        ID로 환자 조회 (Read)
        
        Args:
            patient_id (str): 환자 ID
        
        Returns:
            Patient or None: 환자 객체 또는 None
        """
        for patient in self.patients:
            if patient.patient_id == patient_id:
                return patient
        return None
    
    def search(self, keyword, field="all"):
        """
        환자 검색 (Read)
        
        Args:
            keyword (str): 검색어
            field (str): 검색 필드 ("all", "name", "medical_condition", "doctor", "hospital")
        
        Returns:
            list: 검색된 Patient 객체 리스트
        """
        keyword = keyword.lower().strip()
        results = []
        
        for patient in self.patients:
            if field == "all":
                # 모든 필드 검색
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
        """
        환자 정보 수정 (Update)
        
        Args:
            patient_id (str): 수정할 환자 ID
            updated_data (dict): 수정할 데이터
        
        Returns:
            tuple: (성공 여부, 메시지)
        """
        # 환자 찾기
        patient = self.read_by_id(patient_id)
        if not patient:
            return (False, f"환자 ID {patient_id}를 찾을 수 없습니다.")
        
        # 기존 데이터 백업
        backup = patient.to_dict()
        
        # 데이터 업데이트
        for key, value in updated_data.items():
            if hasattr(patient, key) and key != "patient_id":
                setattr(patient, key, value)
        
        # 유효성 검사
        is_valid, error_msg = patient.validate()
        if not is_valid:
            # 롤백
            for key, value in backup.items():
                setattr(patient, key, value)
            return (False, error_msg)
        
        # 파일 저장
        if self.save_to_file():
            return (True, "환자 정보가 수정되었습니다.")
        else:
            # 롤백
            for key, value in backup.items():
                setattr(patient, key, value)
            return (False, "파일 저장에 실패했습니다.")
    
    def delete(self, patient_id):
        """
        환자 삭제 (Delete)
        
        Args:
            patient_id (str): 삭제할 환자 ID
        
        Returns:
            tuple: (성공 여부, 메시지)
        """
        # 환자 찾기
        patient = self.read_by_id(patient_id)
        if not patient:
            return (False, f"환자 ID {patient_id}를 찾을 수 없습니다.")
        
        # 리스트에서 제거
        self.patients.remove(patient)
        
        # 파일 저장
        if self.save_to_file():
            return (True, f"환자 {patient.name}({patient_id})이(가) 삭제되었습니다.")
        else:
            # 롤백
            self.patients.append(patient)
            return (False, "파일 저장에 실패했습니다.")
    
    def discharge_patient(self, patient_id, discharge_date=None):
        """
        환자 퇴원 처리
        
        Args:
            patient_id (str): 환자 ID
            discharge_date (str): 퇴원일 (기본값: 오늘)
        
        Returns:
            tuple: (성공 여부, 메시지)
        """
        if not discharge_date:
            discharge_date = datetime.now().strftime("%Y-%m-%d")
        
        return self.update(patient_id, {"discharge_date": discharge_date})
    
    # ==================== 통계 메서드 ====================
    
    def get_statistics(self):
        """
        환자 데이터 통계 계산
        
        Returns:
            dict: 통계 데이터
        """
        if not self.patients:
            return None
        
        total = len(self.patients)
        
        # 성별 분포
        male_count = sum(1 for p in self.patients if p.gender == "Male")
        female_count = total - male_count
        
        # 연령대 분포
        age_groups = {}
        for p in self.patients:
            group = p.get_age_group()
            age_groups[group] = age_groups.get(group, 0) + 1
        
        # 진단명 분포
        conditions = {}
        for p in self.patients:
            cond = p.medical_condition
            conditions[cond] = conditions.get(cond, 0) + 1
        
        # 입원 유형 분포
        admission_types = {}
        for p in self.patients:
            atype = p.admission_type
            admission_types[atype] = admission_types.get(atype, 0) + 1
        
        # 혈액형 분포
        blood_types = {}
        for p in self.patients:
            btype = p.blood_type
            blood_types[btype] = blood_types.get(btype, 0) + 1
        
        # 검사 결과 분포
        test_results = {}
        for p in self.patients:
            result = p.test_results
            test_results[result] = test_results.get(result, 0) + 1
        
        # 입원 중인 환자 수
        hospitalized = sum(1 for p in self.patients if p.is_hospitalized())
        
        # 평균 나이
        avg_age = sum(p.age for p in self.patients) / total
        
        # 평균 청구 금액
        avg_billing = sum(p.billing_amount for p in self.patients) / total
        
        # 총 청구 금액
        total_billing = sum(p.billing_amount for p in self.patients)
        
        return {
            "total_patients": total,
            "male_count": male_count,
            "female_count": female_count,
            "male_ratio": round(male_count / total * 100, 1),
            "female_ratio": round(female_count / total * 100, 1),
            "age_groups": age_groups,
            "conditions": conditions,
            "admission_types": admission_types,
            "blood_types": blood_types,
            "test_results": test_results,
            "hospitalized_count": hospitalized,
            "discharged_count": total - hospitalized,
            "avg_age": round(avg_age, 1),
            "avg_billing": round(avg_billing, 0),
            "total_billing": round(total_billing, 0)
        }
    
    def get_today_admissions(self):
        """오늘 입원한 환자 수"""
        today = datetime.now().strftime("%Y-%m-%d")
        return sum(1 for p in self.patients if p.date_of_admission == today)
    
    def get_patients_by_condition(self, condition):
        """특정 진단명의 환자 목록"""
        return [p for p in self.patients if p.medical_condition == condition]
    
    def get_patients_by_doctor(self, doctor):
        """특정 담당의의 환자 목록"""
        return [p for p in self.patients if p.doctor == doctor]


# 테스트 코드
if __name__ == "__main__":
    # 테스트용 매니저 생성
    manager = PatientManager()
    
    print("=" * 60)
    print("환자 관리 시스템 테스트")
    print("=" * 60)
    
    # 전체 환자 수
    patients = manager.read_all()
    print(f"\n📋 전체 환자 수: {len(patients)}명")
    
    # 처음 5명 출력
    print("\n📋 환자 목록 (상위 5명):")
    for p in patients[:5]:
        print(f"   {p.patient_id}: {p.name} ({p.age}세, {p.get_gender_korean()}) - {p.get_condition_korean()}")
    
    # 검색 테스트
    print("\n🔍 검색 테스트 (키워드: 'Diabetes'):")
    results = manager.search("Diabetes", "medical_condition")
    for p in results[:3]:
        print(f"   {p.patient_id}: {p.name} - {p.medical_condition}")
    
    # 통계
    print("\n📊 통계:")
    stats = manager.get_statistics()
    if stats:
        print(f"   총 환자 수: {stats['total_patients']}명")
        print(f"   남성: {stats['male_count']}명 ({stats['male_ratio']}%)")
        print(f"   여성: {stats['female_count']}명 ({stats['female_ratio']}%)")
        print(f"   평균 나이: {stats['avg_age']}세")
        print(f"   입원 중: {stats['hospitalized_count']}명")
        print(f"   평균 청구금액: ₩{stats['avg_billing']:,.0f}")
        
        print("\n   진단명별 분포:")
        for cond, count in stats['conditions'].items():
            print(f"     - {cond}: {count}명")
    
    # Create 테스트
    print("\n➕ 새 환자 등록 테스트:")
    new_patient_data = {
        "name": "테스트환자",
        "age": 30,
        "gender": "Male",
        "blood_type": "O+",
        "medical_condition": "Diabetes",
        "doctor": "Dr. 테스트",
        "hospital": "테스트병원",
        "insurance_provider": "테스트보험",
        "billing_amount": 500000,
        "room_number": 101,
        "admission_type": "Elective",
        "medication": "Test Med",
        "test_results": "Normal"
    }
    success, result = manager.create(new_patient_data)
    print(f"   등록 {'성공' if success else '실패'}: {result}")
    
    # Delete 테스트 (방금 등록한 환자)
    if success:
        print(f"\n🗑️ 환자 삭제 테스트 ({result}):")
        del_success, del_msg = manager.delete(result)
        print(f"   삭제 {'성공' if del_success else '실패'}: {del_msg}")
