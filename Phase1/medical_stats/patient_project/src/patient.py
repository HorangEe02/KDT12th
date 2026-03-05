"""
patient.py
환자 정보 모델 클래스

Author: KDT12 Python Project
Date: 2026-01-09
데이터 출처: Kaggle - Healthcare Dataset
"""

from datetime import datetime


class Patient:
    """
    환자 정보를 담는 클래스
    
    Kaggle Healthcare Dataset 구조를 기반으로 설계
    
    Attributes:
        patient_id (str): 환자 고유 ID (예: "P001")
        name (str): 환자 이름
        age (int): 나이
        gender (str): 성별 ("Male" / "Female")
        blood_type (str): 혈액형 ("A+", "B-", "O+", "AB-" 등)
        medical_condition (str): 진단명
        date_of_admission (str): 입원일 (YYYY-MM-DD)
        doctor (str): 담당 의사
        hospital (str): 병원명
        insurance_provider (str): 보험사
        billing_amount (float): 청구 금액
        room_number (int): 병실 번호
        admission_type (str): 입원 유형
        discharge_date (str): 퇴원일
        medication (str): 처방약
        test_results (str): 검사 결과
    """
    
    # 유효한 값 목록 (클래스 변수)
    VALID_GENDERS = ["Male", "Female"]
    VALID_BLOOD_TYPES = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]
    VALID_ADMISSION_TYPES = ["Emergency", "Elective", "Urgent"]
    VALID_TEST_RESULTS = ["Normal", "Abnormal", "Inconclusive"]
    VALID_CONDITIONS = ["Diabetes", "Hypertension", "Asthma", "Obesity", "Arthritis", "Cancer"]
    
    def __init__(self, patient_id="", name="", age=0, gender="Male", blood_type="A+",
                 medical_condition="", date_of_admission="", doctor="", hospital="",
                 insurance_provider="", billing_amount=0.0, room_number=0,
                 admission_type="Elective", discharge_date="", medication="",
                 test_results="Normal"):
        """생성자: 환자 정보 초기화"""
        self.patient_id = patient_id
        self.name = name
        self.age = age
        self.gender = gender
        self.blood_type = blood_type
        self.medical_condition = medical_condition
        self.date_of_admission = date_of_admission if date_of_admission else datetime.now().strftime("%Y-%m-%d")
        self.doctor = doctor
        self.hospital = hospital
        self.insurance_provider = insurance_provider
        self.billing_amount = billing_amount
        self.room_number = room_number
        self.admission_type = admission_type
        self.discharge_date = discharge_date
        self.medication = medication
        self.test_results = test_results
    
    def to_dict(self):
        """
        객체를 딕셔너리로 변환
        
        Returns:
            dict: 환자 정보 딕셔너리
        """
        return {
            "patient_id": self.patient_id,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "blood_type": self.blood_type,
            "medical_condition": self.medical_condition,
            "date_of_admission": self.date_of_admission,
            "doctor": self.doctor,
            "hospital": self.hospital,
            "insurance_provider": self.insurance_provider,
            "billing_amount": self.billing_amount,
            "room_number": self.room_number,
            "admission_type": self.admission_type,
            "discharge_date": self.discharge_date,
            "medication": self.medication,
            "test_results": self.test_results
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        딕셔너리에서 Patient 객체 생성 (클래스 메서드)
        
        Args:
            data (dict): 환자 정보 딕셔너리
        
        Returns:
            Patient: 새 Patient 객체
        """
        return cls(
            patient_id=data.get("patient_id", ""),
            name=data.get("name", ""),
            age=int(data.get("age", 0)),
            gender=data.get("gender", "Male"),
            blood_type=data.get("blood_type", "A+"),
            medical_condition=data.get("medical_condition", ""),
            date_of_admission=data.get("date_of_admission", ""),
            doctor=data.get("doctor", ""),
            hospital=data.get("hospital", ""),
            insurance_provider=data.get("insurance_provider", ""),
            billing_amount=float(data.get("billing_amount", 0)),
            room_number=int(data.get("room_number", 0)) if data.get("room_number") else 0,
            admission_type=data.get("admission_type", "Elective"),
            discharge_date=data.get("discharge_date", ""),
            medication=data.get("medication", ""),
            test_results=data.get("test_results", "Normal")
        )
    
    def validate(self):
        """
        데이터 유효성 검사
        
        Returns:
            tuple: (성공 여부, 오류 메시지)
        """
        errors = []
        
        # 필수 필드 검사
        if not self.name or len(self.name) < 2:
            errors.append("이름은 2자 이상이어야 합니다.")
        
        if not isinstance(self.age, int) or self.age < 0 or self.age > 120:
            errors.append("나이는 0~120 사이여야 합니다.")
        
        if self.gender not in self.VALID_GENDERS:
            errors.append(f"성별은 {self.VALID_GENDERS} 중 하나여야 합니다.")
        
        if self.blood_type not in self.VALID_BLOOD_TYPES:
            errors.append(f"혈액형은 {self.VALID_BLOOD_TYPES} 중 하나여야 합니다.")
        
        if self.admission_type and self.admission_type not in self.VALID_ADMISSION_TYPES:
            errors.append(f"입원유형은 {self.VALID_ADMISSION_TYPES} 중 하나여야 합니다.")
        
        if self.test_results and self.test_results not in self.VALID_TEST_RESULTS:
            errors.append(f"검사결과는 {self.VALID_TEST_RESULTS} 중 하나여야 합니다.")
        
        if self.room_number and (self.room_number < 100 or self.room_number > 999):
            errors.append("병실번호는 100~999 사이여야 합니다.")
        
        if errors:
            return (False, "\n".join(errors))
        return (True, "")
    
    def get_gender_korean(self):
        """성별을 한글로 반환"""
        return "남성" if self.gender == "Male" else "여성"
    
    def get_condition_korean(self):
        """진단명을 한글로 반환"""
        condition_map = {
            "Diabetes": "당뇨병",
            "Hypertension": "고혈압",
            "Asthma": "천식",
            "Obesity": "비만",
            "Arthritis": "관절염",
            "Cancer": "암"
        }
        return condition_map.get(self.medical_condition, self.medical_condition)
    
    def get_admission_type_korean(self):
        """입원유형을 한글로 반환"""
        type_map = {
            "Emergency": "응급",
            "Elective": "선택",
            "Urgent": "긴급"
        }
        return type_map.get(self.admission_type, self.admission_type)
    
    def get_test_results_korean(self):
        """검사결과를 한글로 반환"""
        result_map = {
            "Normal": "정상",
            "Abnormal": "비정상",
            "Inconclusive": "판정불가"
        }
        return result_map.get(self.test_results, self.test_results)
    
    def get_billing_formatted(self):
        """청구금액을 포맷팅하여 반환"""
        return f"₩{self.billing_amount:,.0f}"
    
    def get_age_group(self):
        """연령대 반환"""
        if self.age < 20:
            return "10대 이하"
        elif self.age < 30:
            return "20대"
        elif self.age < 40:
            return "30대"
        elif self.age < 50:
            return "40대"
        elif self.age < 60:
            return "50대"
        elif self.age < 70:
            return "60대"
        else:
            return "70대 이상"
    
    def is_hospitalized(self):
        """현재 입원 중인지 확인"""
        return self.discharge_date == "" or self.discharge_date is None
    
    def get_display_info(self):
        """
        표시용 정보 문자열 반환
        
        Returns:
            str: 환자 정보 요약
        """
        status = "🏥 입원중" if self.is_hospitalized() else "✅ 퇴원"
        return f"""
{'='*50}
환자 ID: {self.patient_id}
{'='*50}
👤 기본 정보
   이름: {self.name}
   나이: {self.age}세 ({self.get_age_group()})
   성별: {self.get_gender_korean()}
   혈액형: {self.blood_type}

🩺 의료 정보
   진단명: {self.get_condition_korean()} ({self.medical_condition})
   담당의: {self.doctor}
   병원: {self.hospital}
   처방약: {self.medication}
   검사결과: {self.get_test_results_korean()}

📅 입원 정보
   입원일: {self.date_of_admission}
   퇴원일: {self.discharge_date if self.discharge_date else "-"}
   입원유형: {self.get_admission_type_korean()}
   병실: {self.room_number}호
   상태: {status}

💰 비용 정보
   보험사: {self.insurance_provider}
   청구금액: {self.get_billing_formatted()}
{'='*50}
"""
    
    def __str__(self):
        """문자열 표현"""
        return f"Patient({self.patient_id}: {self.name}, {self.age}세, {self.medical_condition})"
    
    def __repr__(self):
        """개발자용 문자열 표현"""
        return f"Patient(id={self.patient_id}, name={self.name})"


# 테스트 코드
if __name__ == "__main__":
    # 테스트용 환자 생성
    patient = Patient(
        patient_id="P001",
        name="홍길동",
        age=45,
        gender="Male",
        blood_type="A+",
        medical_condition="Diabetes",
        date_of_admission="2026-01-05",
        doctor="Dr. 김철수",
        hospital="서울대병원",
        insurance_provider="국민건강보험",
        billing_amount=1500000,
        room_number=302,
        admission_type="Emergency",
        medication="Metformin",
        test_results="Normal"
    )
    
    # 정보 출력
    print(patient.get_display_info())
    
    # 유효성 검사
    is_valid, error_msg = patient.validate()
    print(f"유효성 검사: {'통과' if is_valid else '실패'}")
    if not is_valid:
        print(f"오류: {error_msg}")
    
    # 딕셔너리 변환 테스트
    print("\n📋 딕셔너리 변환:")
    patient_dict = patient.to_dict()
    for key, value in patient_dict.items():
        print(f"   {key}: {value}")
    
    # from_dict 테스트
    new_patient = Patient.from_dict(patient_dict)
    print(f"\n📋 from_dict 테스트: {new_patient}")
