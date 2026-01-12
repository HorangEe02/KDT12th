"""
health_checker.py
건강 상태 분석 클래스

Author: KDT12 Python Project
Date: 2026-01-09
"""


class HealthChecker:
    """
    건강 상태를 분석하는 클래스
    
    BMI, 혈압, 심혈관 위험도를 계산하고 건강 조언을 제공
    """
    
    def __init__(self, age, gender, height, weight, ap_hi, ap_lo,
                 cholesterol=1, gluc=1, smoke=0, alco=0, active=1):
        """생성자: 건강 데이터 초기화"""
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
        """BMI 계산 및 판정"""
        if self.height <= 0:
            return (0, "측정 불가", "#95a5a6")
        
        height_m = self.height / 100
        bmi = self.weight / (height_m ** 2)
        
        # 아시아-태평양 기준
        if bmi < 18.5:
            status = "저체중"
            color = "#3498db"
        elif bmi < 23:
            status = "정상"
            color = "#27ae60"
        elif bmi < 25:
            status = "과체중"
            color = "#f39c12"
        elif bmi < 30:
            status = "비만"
            color = "#e74c3c"
        else:
            status = "고도비만"
            color = "#8e44ad"
        
        return (round(bmi, 1), status, color)
    
    def analyze_blood_pressure(self):
        """혈압 분석"""
        ap_hi = self.ap_hi
        ap_lo = self.ap_lo
        
        if ap_hi < 90 or ap_lo < 60:
            return ("저혈압", "혈압이 낮습니다", "#3498db")
        elif ap_hi < 120 and ap_lo < 80:
            return ("정상", "정상 혈압입니다", "#27ae60")
        elif ap_hi < 130 and ap_lo < 80:
            return ("주의", "혈압 상승 경향", "#2ecc71")
        elif ap_hi < 140 or ap_lo < 90:
            return ("고혈압 전단계", "관리가 필요합니다", "#f39c12")
        elif ap_hi < 160 or ap_lo < 100:
            return ("고혈압 1기", "의료 상담 권장", "#e67e22")
        else:
            return ("고혈압 2기", "즉시 의료 상담 필요", "#e74c3c")
    
    def calculate_risk_score(self):
        """심혈관 위험도 점수 계산 (100점 만점)"""
        score = 0
        
        # 나이 (최대 20점)
        if self.age >= 70:
            score += 20
        elif self.age >= 60:
            score += 15
        elif self.age >= 50:
            score += 10
        elif self.age >= 40:
            score += 5
        
        # BMI (최대 20점)
        bmi, _, _ = self.calculate_bmi()
        if bmi >= 30:
            score += 20
        elif bmi >= 25:
            score += 15
        elif bmi >= 23:
            score += 10
        elif bmi < 18.5:
            score += 5
        
        # 혈압 (최대 25점)
        if self.ap_hi >= 160 or self.ap_lo >= 100:
            score += 25
        elif self.ap_hi >= 140 or self.ap_lo >= 90:
            score += 20
        elif self.ap_hi >= 130:
            score += 15
        elif self.ap_hi >= 120:
            score += 10
        
        # 콜레스테롤 (최대 15점)
        if self.cholesterol == 3:
            score += 15
        elif self.cholesterol == 2:
            score += 10
        
        # 혈당 (최대 10점)
        if self.gluc == 3:
            score += 10
        elif self.gluc == 2:
            score += 5
        
        # 흡연 (15점)
        if self.smoke:
            score += 15
        
        # 음주 (5점)
        if self.alco:
            score += 5
        
        # 운동 부족 (10점)
        if not self.active:
            score += 10
        
        # 등급 판정
        if score <= 20:
            grade = "낮음"
            desc = "심혈관 건강이 양호합니다"
            color = "#27ae60"
        elif score <= 40:
            grade = "보통"
            desc = "생활 습관 개선을 권장합니다"
            color = "#2ecc71"
        elif score <= 60:
            grade = "높음"
            desc = "적극적인 건강 관리가 필요합니다"
            color = "#f39c12"
        elif score <= 80:
            grade = "매우 높음"
            desc = "의료 상담을 권장합니다"
            color = "#e67e22"
        else:
            grade = "위험"
            desc = "즉시 의료 상담이 필요합니다"
            color = "#e74c3c"
        
        return (score, grade, desc, color)
    
    def get_health_advice(self):
        """건강 조언 생성"""
        advice = []
        
        bmi, bmi_status, _ = self.calculate_bmi()
        bp_status, _, _ = self.analyze_blood_pressure()
        
        # BMI 관련 조언
        if bmi >= 25:
            advice.append("규칙적인 운동으로 체중 관리를 시작하세요.")
            advice.append("식이 조절을 통해 칼로리 섭취를 줄여보세요.")
        elif bmi < 18.5:
            advice.append("균형 잡힌 영양 섭취로 건강한 체중을 유지하세요.")
        
        # 혈압 관련 조언
        if "고혈압" in bp_status:
            advice.append("저염식을 실천하세요.")
            advice.append("카페인 섭취를 줄여보세요.")
        
        # 콜레스테롤 관련
        if self.cholesterol >= 2:
            advice.append("포화지방 섭취를 줄이세요.")
        
        # 혈당 관련
        if self.gluc >= 2:
            advice.append("당분 섭취를 줄이고 식이섬유를 늘리세요.")
        
        # 생활 습관 관련
        if self.smoke:
            advice.append("금연은 심혈관 건강에 가장 효과적입니다.")
        
        if self.alco:
            advice.append("음주량을 줄여보세요.")
        
        if not self.active:
            advice.append("하루 30분 이상 걷기를 시작해보세요.")
        
        if not advice:
            advice.append("현재 건강 상태를 잘 유지하고 계십니다!")
            advice.append("정기적인 건강 검진을 권장합니다.")
        
        return advice
    
    def to_dict(self):
        """딕셔너리로 변환"""
        bmi, _, _ = self.calculate_bmi()
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
            "bmi": bmi,
            "risk_score": risk_score
        }
