"""
patient.py
환자 정보 모델 클래스

Author: KDT12 Python Project
Date: 2026-01-09
"""

from datetime import datetime


class Patient:
    """환자 정보를 담는 클래스"""
    
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
        """생성자"""
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
        """딕셔너리로 변환"""
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
        """딕셔너리에서 객체 생성"""
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
        """유효성 검사"""
        errors = []
        
        if not self.name or len(self.name) < 2:
            errors.append("이름은 2자 이상이어야 합니다.")
        
        if not isinstance(self.age, int) or self.age < 0 or self.age > 120:
            errors.append("나이는 0~120 사이여야 합니다.")
        
        if self.gender not in self.VALID_GENDERS:
            errors.append(f"성별은 {self.VALID_GENDERS} 중 하나여야 합니다.")
        
        if self.blood_type not in self.VALID_BLOOD_TYPES:
            errors.append(f"혈액형은 {self.VALID_BLOOD_TYPES} 중 하나여야 합니다.")
        
        if self.room_number and (self.room_number < 100 or self.room_number > 999):
            errors.append("병실번호는 100~999 사이여야 합니다.")
        
        if errors:
            return (False, "\n".join(errors))
        return (True, "")
    
    def get_gender_korean(self):
        """성별 한글 반환"""
        return "남성" if self.gender == "Male" else "여성"
    
    def get_condition_korean(self):
        """진단명 한글 반환"""
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
        """입원유형 한글 반환"""
        type_map = {"Emergency": "응급", "Elective": "선택", "Urgent": "긴급"}
        return type_map.get(self.admission_type, self.admission_type)
    
    def get_test_results_korean(self):
        """검사결과 한글 반환"""
        result_map = {"Normal": "정상", "Abnormal": "비정상", "Inconclusive": "판정불가"}
        return result_map.get(self.test_results, self.test_results)
    
    def get_billing_formatted(self):
        """청구금액 포맷"""
        return f"₩{self.billing_amount:,.0f}"
    
    def is_hospitalized(self):
        """입원 중 여부"""
        return self.discharge_date == "" or self.discharge_date is None
    
    def __str__(self):
        return f"Patient({self.patient_id}: {self.name}, {self.age}세)"
