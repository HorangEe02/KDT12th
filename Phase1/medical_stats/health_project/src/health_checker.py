"""
health_checker.py
건강 상태 분석 클래스

Author: KDT12 Python Project
Date: 2026-01-08
"""


class HealthChecker:
    """
    건강 상태를 분석하는 클래스
    
    Attributes:
        age (int): 나이 (년)
        gender (str): 성별 ("남성" 또는 "여성")
        height (int): 키 (cm)
        weight (float): 몸무게 (kg)
        ap_hi (int): 수축기 혈압 (mmHg)
        ap_lo (int): 이완기 혈압 (mmHg)
        cholesterol (int): 콜레스테롤 수치 (1: 정상, 2: 높음, 3: 매우높음)
        gluc (int): 혈당 수치 (1: 정상, 2: 높음, 3: 매우높음)
        smoke (int): 흡연 여부 (0: 비흡연, 1: 흡연)
        alco (int): 음주 여부 (0: 비음주, 1: 음주)
        active (int): 신체활동 여부 (0: 비활동, 1: 활동)
    """
    
    def __init__(self, age=30, gender="남성", height=170, weight=65,
                 ap_hi=120, ap_lo=80, cholesterol=1, gluc=1,
                 smoke=0, alco=0, active=1):
        """생성자: 초기값 설정"""
        self.age = age
        self.gender = gender
        self.height = height
        self.weight = weight
        self.ap_hi = ap_hi
        self.ap_lo = ap_lo
        self.cholesterol = cholesterol
        self.gluc = gluc
        self.smoke = smoke
        self.alco = alco
        self.active = active
    
    def calculate_bmi(self):
        """
        BMI 계산 및 판정
        
        Returns:
            tuple: (BMI 값, 판정 결과, 색상 코드)
        """
        if self.height <= 0 or self.weight <= 0:
            return (0, "측정 불가", "#95a5a6")
        
        height_m = self.height / 100
        bmi = self.weight / (height_m ** 2)
        
        # WHO 아시아-태평양 기준
        if bmi < 18.5:
            return (round(bmi, 1), "저체중", "#3498db")
        elif bmi < 23:
            return (round(bmi, 1), "정상", "#2ecc71")
        elif bmi < 25:
            return (round(bmi, 1), "과체중", "#f39c12")
        elif bmi < 30:
            return (round(bmi, 1), "비만", "#e74c3c")
        else:
            return (round(bmi, 1), "고도비만", "#8e44ad")
    
    def analyze_blood_pressure(self):
        """
        혈압 분석
        
        Returns:
            tuple: (분류, 설명, 색상 코드)
        """
        systolic = self.ap_hi
        diastolic = self.ap_lo
        
        if systolic < 90 or diastolic < 60:
            return ("저혈압", "혈압이 낮습니다. 어지러움에 주의하세요.", "#3498db")
        elif systolic < 120 and diastolic < 80:
            return ("정상", "정상 혈압입니다. 현재 상태를 유지하세요.", "#2ecc71")
        elif systolic < 130 and diastolic < 80:
            return ("주의", "혈압이 약간 높습니다. 생활습관 개선이 필요합니다.", "#f1c40f")
        elif systolic < 140 or diastolic < 90:
            return ("고혈압 전단계", "고혈압 위험이 있습니다. 관리가 필요합니다.", "#f39c12")
        elif systolic < 160 or diastolic < 100:
            return ("1기 고혈압", "고혈압입니다. 전문가 상담을 권장합니다.", "#e74c3c")
        else:
            return ("2기 고혈압", "심한 고혈압입니다. 즉시 치료가 필요합니다.", "#8e44ad")
    
    def calculate_risk_score(self):
        """
        심혈관 질환 위험도 점수 계산
        
        Returns:
            tuple: (점수, 등급, 설명, 색상 코드)
        """
        score = 0
        
        # 나이에 따른 점수
        if self.age >= 60:
            score += 20
        elif self.age >= 50:
            score += 15
        elif self.age >= 40:
            score += 10
        
        # BMI에 따른 점수
        bmi_value, _, _ = self.calculate_bmi()
        if bmi_value >= 30:
            score += 20
        elif bmi_value >= 25:
            score += 15
        elif bmi_value >= 23:
            score += 5
        
        # 혈압에 따른 점수
        bp_status, _, _ = self.analyze_blood_pressure()
        if bp_status == "2기 고혈압":
            score += 25
        elif bp_status == "1기 고혈압":
            score += 15
        elif bp_status == "고혈압 전단계":
            score += 10
        elif bp_status == "주의":
            score += 5
        
        # 콜레스테롤에 따른 점수
        if self.cholesterol == 3:
            score += 20
        elif self.cholesterol == 2:
            score += 10
        
        # 혈당에 따른 점수
        if self.gluc == 3:
            score += 15
        elif self.gluc == 2:
            score += 10
        
        # 생활습관에 따른 점수
        if self.smoke == 1:
            score += 15
        if self.alco == 1:
            score += 5
        if self.active == 0:
            score += 10
        
        # 등급 판정
        if score <= 20:
            return (score, "낮음", "건강한 상태입니다. 현재 생활습관을 유지하세요.", "#2ecc71")
        elif score <= 40:
            return (score, "보통", "주의가 필요합니다. 정기적인 건강검진을 권장합니다.", "#f1c40f")
        elif score <= 60:
            return (score, "높음", "관리가 필요합니다. 생활습관 개선이 필요합니다.", "#f39c12")
        elif score <= 80:
            return (score, "매우 높음", "전문가 상담을 권장합니다. 적극적인 관리가 필요합니다.", "#e74c3c")
        else:
            return (score, "위험", "즉각적인 조치가 필요합니다. 의사와 상담하세요.", "#8e44ad")
    
    def get_health_advice(self):
        """
        종합 건강 조언 생성
        
        Returns:
            list: 건강 조언 리스트
        """
        advice_list = []
        
        # BMI 관련 조언
        bmi_value, bmi_status, _ = self.calculate_bmi()
        if bmi_status == "저체중":
            advice_list.append("🍽️ 영양가 있는 식사를 규칙적으로 하세요.")
        elif bmi_status in ["과체중", "비만", "고도비만"]:
            advice_list.append("🏃 규칙적인 운동과 식이조절을 권장합니다.")
        
        # 혈압 관련 조언
        bp_status, _, _ = self.analyze_blood_pressure()
        if "고혈압" in bp_status:
            advice_list.append("🧂 저염식 식단을 실천하세요.")
            advice_list.append("☕ 카페인 섭취를 줄이세요.")
        
        # 콜레스테롤 관련 조언
        if self.cholesterol >= 2:
            advice_list.append("🥗 포화지방 섭취를 줄이고 채소를 많이 드세요.")
        
        # 혈당 관련 조언
        if self.gluc >= 2:
            advice_list.append("🍬 당분 섭취를 제한하세요.")
        
        # 생활습관 관련 조언
        if self.smoke == 1:
            advice_list.append("🚭 금연을 강력히 권장합니다.")
        if self.alco == 1:
            advice_list.append("🍺 음주량을 줄이세요.")
        if self.active == 0:
            advice_list.append("🚶 하루 30분 이상 걷기 운동을 시작하세요.")
        
        # 기본 조언
        if len(advice_list) == 0:
            advice_list.append("✅ 현재 건강 상태가 양호합니다!")
            advice_list.append("💪 꾸준한 운동과 균형 잡힌 식단을 유지하세요.")
        
        return advice_list
    
    def to_dict(self):
        """
        객체를 딕셔너리로 변환
        
        Returns:
            dict: 건강 데이터 딕셔너리
        """
        bmi_value, _, _ = self.calculate_bmi()
        risk_score, _, _, _ = self.calculate_risk_score()
        
        return {
            "age": self.age,
            "gender": self.gender,
            "height": self.height,
            "weight": self.weight,
            "ap_hi": self.ap_hi,
            "ap_lo": self.ap_lo,
            "cholesterol": self.cholesterol,
            "gluc": self.gluc,
            "smoke": self.smoke,
            "alco": self.alco,
            "active": self.active,
            "bmi": bmi_value,
            "risk_score": risk_score
        }


# 테스트 코드
if __name__ == "__main__":
    # 테스트용 인스턴스 생성
    checker = HealthChecker(
        age=45,
        gender="남성",
        height=175,
        weight=80,
        ap_hi=135,
        ap_lo=88,
        cholesterol=2,
        gluc=1,
        smoke=0,
        alco=1,
        active=1
    )
    
    print("=" * 50)
    print("건강 분석 결과")
    print("=" * 50)
    
    # BMI 분석
    bmi, bmi_status, _ = checker.calculate_bmi()
    print(f"\n📊 BMI: {bmi} ({bmi_status})")
    
    # 혈압 분석
    bp_status, bp_desc, _ = checker.analyze_blood_pressure()
    print(f"🩺 혈압: {bp_status}")
    print(f"   {bp_desc}")
    
    # 위험도 분석
    score, grade, desc, _ = checker.calculate_risk_score()
    print(f"\n⚠️ 심혈관 위험도: {grade} ({score}점)")
    print(f"   {desc}")
    
    # 건강 조언
    print(f"\n💬 건강 조언:")
    for advice in checker.get_health_advice():
        print(f"   {advice}")
