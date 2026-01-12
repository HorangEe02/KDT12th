"""
integration_manager.py
건강 체크 시스템과 환자 관리 시스템을 연동하는 브릿지 클래스

Author: KDT12 Python Project
Date: 2026-01-09
"""

import os
import sys

# 상위 모듈 import를 위한 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from health_app.health_checker import HealthChecker
from health_app.data_manager import HealthDataManager
from patient_app.patient import Patient
from patient_app.patient_manager import PatientManager


class IntegrationManager:
    """
    건강 체크 시스템과 환자 관리 시스템을 연동하는 브릿지 클래스
    
    주요 기능:
    - 환자 ID로 건강 기록 조회
    - 건강 위험도 → 진단명 변환
    - 건강 체크 결과로 환자 등록
    - 통합 통계
    """
    
    # 위험도 → 진단명 매핑 규칙
    CONDITION_MAPPING = {
        "obesity": "Obesity",
        "hypertension": "Hypertension", 
        "diabetes": "Diabetes",
        "high_risk": "Cancer",
        "default": "Asthma"
    }
    
    def __init__(self, base_path=None):
        """생성자"""
        if base_path is None:
            self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        else:
            self.base_path = base_path
        
        self.health_manager = HealthDataManager(self.base_path)
        self.patient_manager = PatientManager(self.base_path)
    
    def get_patient_list(self):
        """
        환자 목록 조회 (건강 체크 시 선택용)
        
        Returns:
            list: [(patient_id, name, age, gender), ...]
        """
        patients = self.patient_manager.read_all()
        return [
            (p.patient_id, p.name, p.age, p.gender)
            for p in patients
        ]
    
    def get_patient_by_id(self, patient_id):
        """
        환자 ID로 환자 정보 조회
        
        Args:
            patient_id: 환자 ID
            
        Returns:
            Patient or None
        """
        return self.patient_manager.read_by_id(patient_id)
    
    def get_health_records_by_patient(self, patient_id):
        """
        환자 ID로 건강 기록 조회
        
        Args:
            patient_id: 환자 ID
            
        Returns:
            list: 해당 환자의 건강 기록 리스트
        """
        all_records = self.health_manager.load_records()
        return [
            record for record in all_records
            if record.get("patient_id") == patient_id
        ]
    
    def get_health_records_by_name(self, name):
        """
        이름으로 건강 기록 조회 (patient_id 없는 기존 기록 호환)
        
        Args:
            name: 환자 이름
            
        Returns:
            list: 해당 이름의 건강 기록 리스트
        """
        all_records = self.health_manager.load_records()
        return [
            record for record in all_records
            if record.get("name") == name
        ]
    
    def suggest_condition(self, health_data):
        """
        건강 데이터를 분석하여 진단명 추천
        
        Args:
            health_data: dict with bmi, ap_hi, ap_lo, gluc, risk_score
            
        Returns:
            tuple: (추천 진단명, 근거 설명)
        """
        suggestions = []
        
        bmi = float(health_data.get("bmi", 0))
        ap_hi = int(health_data.get("ap_hi", 0))
        ap_lo = int(health_data.get("ap_lo", 0))
        gluc = int(health_data.get("gluc", 1))
        risk_score = int(health_data.get("risk_score", 0))
        
        # 비만 체크 (BMI >= 25)
        if bmi >= 25:
            suggestions.append(("Obesity", f"BMI {bmi} (비만 기준 초과)"))
        
        # 고혈압 체크 (수축기 >= 140 or 이완기 >= 90)
        if ap_hi >= 140 or ap_lo >= 90:
            suggestions.append(("Hypertension", f"혈압 {ap_hi}/{ap_lo} (고혈압 기준 초과)"))
        
        # 당뇨 체크 (혈당 레벨 3)
        if gluc >= 3:
            suggestions.append(("Diabetes", f"혈당 레벨 {gluc} (고혈당)"))
        
        # 고위험군 (위험점수 >= 60)
        if risk_score >= 60:
            suggestions.append(("Cancer", f"위험점수 {risk_score}점 (정밀검사 권고)"))
        
        # 추천이 없으면 기본값
        if not suggestions:
            return ("Asthma", "특이 소견 없음 (기본 진단)")
        
        # 가장 심각한 것 반환 (위험점수 기준)
        priority = ["Cancer", "Hypertension", "Diabetes", "Obesity"]
        for condition in priority:
            for sug in suggestions:
                if sug[0] == condition:
                    return sug
        
        return suggestions[0]
    
    def save_health_record_with_patient(self, patient_id, name, health_data):
        """
        환자 ID와 함께 건강 기록 저장
        
        Args:
            patient_id: 환자 ID (없으면 빈 문자열)
            name: 이름
            health_data: 건강 데이터 딕셔너리
            
        Returns:
            bool: 성공 여부
        """
        # patient_id를 데이터에 추가
        health_data["patient_id"] = patient_id if patient_id else ""
        return self.health_manager.save_record_with_patient_id(patient_id, name, health_data)
    
    def register_patient_from_health(self, health_data, extra_info):
        """
        건강 체크 결과로 새 환자 등록
        
        Args:
            health_data: 건강 체크 데이터
            extra_info: 추가 정보 (doctor, hospital, blood_type 등)
            
        Returns:
            tuple: (성공 여부, 환자 ID 또는 오류 메시지)
        """
        # 진단명 추천
        condition, reason = self.suggest_condition(health_data)
        
        # 환자 데이터 구성
        patient_data = {
            "name": health_data.get("name", ""),
            "age": health_data.get("age", 0),
            "gender": "Male" if health_data.get("gender") == "남성" else "Female",
            "blood_type": extra_info.get("blood_type", "A+"),
            "medical_condition": extra_info.get("medical_condition", condition),
            "doctor": extra_info.get("doctor", ""),
            "hospital": extra_info.get("hospital", ""),
            "insurance_provider": extra_info.get("insurance_provider", ""),
            "billing_amount": extra_info.get("billing_amount", 0),
            "room_number": extra_info.get("room_number", 0),
            "admission_type": extra_info.get("admission_type", "Elective"),
            "medication": extra_info.get("medication", ""),
            "test_results": extra_info.get("test_results", "Normal")
        }
        
        return self.patient_manager.create(patient_data)
    
    def get_health_trend(self, patient_id):
        """
        환자의 건강 추이 분석
        
        Args:
            patient_id: 환자 ID
            
        Returns:
            dict: 추이 정보 (bmi_trend, bp_trend, risk_trend)
        """
        records = self.get_health_records_by_patient(patient_id)
        
        if len(records) < 2:
            return None
        
        # 날짜순 정렬 (최신이 마지막)
        records_sorted = sorted(records, key=lambda x: x.get("date", ""))
        
        latest = records_sorted[-1]
        previous = records_sorted[-2]
        
        def get_trend(current, prev):
            if current < prev:
                return "↓ 개선"
            elif current > prev:
                return "↑ 악화"
            else:
                return "→ 유지"
        
        try:
            bmi_trend = get_trend(
                float(latest.get("bmi", 0)),
                float(previous.get("bmi", 0))
            )
            bp_trend = get_trend(
                int(latest.get("ap_hi", 0)),
                int(previous.get("ap_hi", 0))
            )
            risk_trend = get_trend(
                int(latest.get("risk_score", 0)),
                int(previous.get("risk_score", 0))
            )
            
            return {
                "bmi_trend": bmi_trend,
                "bp_trend": bp_trend,
                "risk_trend": risk_trend,
                "record_count": len(records)
            }
        except (ValueError, TypeError):
            return None
    
    def get_integrated_statistics(self):
        """
        통합 통계 조회
        
        Returns:
            dict: 통합 통계 정보
        """
        patient_stats = self.patient_manager.get_statistics()
        health_records = self.health_manager.load_records()
        
        # 건강 기록 통계
        total_health_records = len(health_records)
        linked_records = sum(1 for r in health_records if r.get("patient_id"))
        
        # 평균 BMI, 위험도
        if health_records:
            avg_bmi = sum(float(r.get("bmi", 0)) for r in health_records) / len(health_records)
            avg_risk = sum(int(r.get("risk_score", 0)) for r in health_records) / len(health_records)
        else:
            avg_bmi = 0
            avg_risk = 0
        
        return {
            "patient_stats": patient_stats,
            "total_health_records": total_health_records,
            "linked_records": linked_records,
            "unlinked_records": total_health_records - linked_records,
            "avg_bmi": round(avg_bmi, 1),
            "avg_risk_score": round(avg_risk, 1)
        }
    
    def find_matching_patient(self, name, age, gender):
        """
        이름, 나이, 성별로 매칭되는 환자 찾기
        
        Args:
            name: 이름
            age: 나이
            gender: 성별 (남성/여성 또는 Male/Female)
            
        Returns:
            Patient or None
        """
        # 성별 정규화
        if gender in ["남성", "Male"]:
            gender_norm = "Male"
        else:
            gender_norm = "Female"
        
        for patient in self.patient_manager.patients:
            if (patient.name == name and 
                patient.age == int(age) and 
                patient.gender == gender_norm):
                return patient
        
        return None
