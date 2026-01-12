"""
main.py
🏥 의료 종합 관리 시스템 - 메인 런처

Author: KDT12 Python Project
Date: 2026-01-09

통합 대상:
- ⚕️ 건강 상태 체크 시스템 (BMI, 혈압, 심혈관 위험도)
- 📋 환자 정보 관리 시스템 (CRUD)
"""

import os
import sys
from tkinter import *
from tkinter import ttk

# 모듈 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 기본 경로 설정
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class MedicalSystemApp:
    """
    의료 종합 관리 시스템 - 메인 런처
    
    두 개의 시스템을 통합하여 메인 메뉴에서 선택할 수 있도록 제공
    """
    
    def __init__(self):
        """생성자: 메인 GUI 초기화"""
        self.window = Tk()
        self.window.title("🏥 의료 종합 관리 시스템")
        self.window.geometry("700x700")
        self.window.resizable(True, True)
        
        # 색상 테마
        self.colors = {
            "bg": "#f0f4f8",
            "header": "#1e3a5f",
            "health": "#27ae60",
            "health_light": "#2ecc71",
            "patient": "#9b59b6",
            "patient_light": "#a569bd",
            "dark": "#2c3e50",
            "light": "#ecf0f1",
            "white": "#ffffff"
        }
        
        self.window.configure(bg=self.colors["bg"])
        
        # 위젯 생성
        self.create_widgets()
        
        # 창 닫기 이벤트
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def on_close(self):
        """프로그램 종료"""
        self.window.destroy()
    
    def create_widgets(self):
        """모든 위젯 생성"""
        # 상단 헤더
        self.create_header()
        
        # 메인 컨텐츠
        self.create_main_content()
        
        # 하단 푸터
        self.create_footer()
    
    def create_header(self):
        """상단 헤더 생성"""
        header = Frame(self.window, bg=self.colors["header"], height=100)
        header.pack(fill=X)
        header.pack_propagate(False)
        
        # 타이틀
        Label(
            header,
            text="🏥",
            font=("맑은 고딕", 36),
            fg=self.colors["white"],
            bg=self.colors["header"]
        ).pack(pady=(15, 0))
        
        Label(
            header,
            text="의료 종합 관리 시스템",
            font=("맑은 고딕", 20, "bold"),
            fg=self.colors["white"],
            bg=self.colors["header"]
        ).pack()
        
        Label(
            header,
            text="Medical Management System",
            font=("맑은 고딕", 10),
            fg=self.colors["light"],
            bg=self.colors["header"]
        ).pack()
    
    def create_main_content(self):
        """메인 컨텐츠 영역 생성"""
        main_frame = Frame(self.window, bg=self.colors["bg"])
        main_frame.pack(fill=BOTH, expand=True, padx=40, pady=30)
        
        # 안내 문구
        Label(
            main_frame,
            text="사용할 시스템을 선택하세요",
            font=("맑은 고딕", 12),
            fg=self.colors["dark"],
            bg=self.colors["bg"]
        ).pack(pady=(0, 20))
        
        # ===== 건강 체크 시스템 카드 =====
        health_card = Frame(
            main_frame,
            bg=self.colors["white"],
            relief=RAISED,
            bd=1
        )
        health_card.pack(fill=X, pady=10, ipady=15)
        
        # 아이콘 & 제목
        health_header = Frame(health_card, bg=self.colors["health"])
        health_header.pack(fill=X)
        
        Label(
            health_header,
            text="⚕️ 건강 상태 체크 시스템",
            font=("맑은 고딕", 16, "bold"),
            fg=self.colors["white"],
            bg=self.colors["health"],
            pady=12
        ).pack()
        
        # 설명
        health_content = Frame(health_card, bg=self.colors["white"])
        health_content.pack(fill=X, padx=20, pady=15)
        
        Label(
            health_content,
            text="BMI 분석 | 혈압 분석 | 심혈관 위험도 평가",
            font=("맑은 고딕", 11),
            fg=self.colors["dark"],
            bg=self.colors["white"]
        ).pack()
        
        Label(
            health_content,
            text="성별 평균 비교 | 건강 조언 제공",
            font=("맑은 고딕", 11),
            fg=self.colors["dark"],
            bg=self.colors["white"]
        ).pack()
        
        Label(
            health_content,
            text="📊 Kaggle Cardiovascular Disease Dataset 기반",
            font=("맑은 고딕", 9),
            fg="#7f8c8d",
            bg=self.colors["white"]
        ).pack(pady=(10, 0))
        
        # 시작 버튼
        Button(
            health_card,
            text="▶ 시작하기",
            font=("맑은 고딕", 12, "bold"),
            bg=self.colors["health"],
            fg="#000000",
            activebackground=self.colors["health_light"],
            activeforeground="#000000",
            relief=FLAT,
            cursor="hand2",
            command=self.open_health_app
        ).pack(pady=(0, 15), ipadx=30, ipady=8)
        
        # ===== 환자 관리 시스템 카드 =====
        patient_card = Frame(
            main_frame,
            bg=self.colors["white"],
            relief=RAISED,
            bd=1
        )
        patient_card.pack(fill=X, pady=10, ipady=15)
        
        # 아이콘 & 제목
        patient_header = Frame(patient_card, bg=self.colors["patient"])
        patient_header.pack(fill=X)
        
        Label(
            patient_header,
            text="📋 환자 정보 관리 시스템",
            font=("맑은 고딕", 16, "bold"),
            fg=self.colors["white"],
            bg=self.colors["patient"],
            pady=12
        ).pack()
        
        # 설명
        patient_content = Frame(patient_card, bg=self.colors["white"])
        patient_content.pack(fill=X, padx=20, pady=15)
        
        Label(
            patient_content,
            text="환자 등록 | 조회 | 수정 | 삭제 (CRUD)",
            font=("맑은 고딕", 11),
            fg=self.colors["dark"],
            bg=self.colors["white"]
        ).pack()
        
        Label(
            patient_content,
            text="검색 | 퇴원 처리 | 통계 분석",
            font=("맑은 고딕", 11),
            fg=self.colors["dark"],
            bg=self.colors["white"]
        ).pack()
        
        Label(
            patient_content,
            text="📊 Kaggle Healthcare Dataset 기반",
            font=("맑은 고딕", 9),
            fg="#7f8c8d",
            bg=self.colors["white"]
        ).pack(pady=(10, 0))
        
        # 시작 버튼
        Button(
            patient_card,
            text="▶ 시작하기",
            font=("맑은 고딕", 12, "bold"),
            bg=self.colors["patient"],
            fg="#000000",
            activebackground=self.colors["patient_light"],
            activeforeground="#000000",
            relief=FLAT,
            cursor="hand2",
            command=self.open_patient_app
        ).pack(pady=(0, 15), ipadx=30, ipady=8)
    
    def create_footer(self):
        """하단 푸터 생성"""
        footer = Frame(self.window, bg=self.colors["header"], height=40)
        footer.pack(fill=X, side=BOTTOM)
        footer.pack_propagate(False)
        
        Label(
            footer,
            text="KDT12 Python 통합 프로젝트 | Kaggle 데이터 기반 | v1.0",
            font=("맑은 고딕", 9),
            fg=self.colors["light"],
            bg=self.colors["header"]
        ).pack(pady=10)
    
    def open_health_app(self):
        """건강 체크 시스템 열기"""
        try:
            from health_app.health_gui import HealthCheckApp
            app = HealthCheckApp(self.window, BASE_PATH)
            app.focus_set()
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("오류", f"건강 체크 시스템을 열 수 없습니다.\n{str(e)}")
    
    def open_patient_app(self):
        """환자 관리 시스템 열기"""
        try:
            from patient_app.patient_gui import PatientManagementApp
            app = PatientManagementApp(self.window, BASE_PATH)
            app.focus_set()
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("오류", f"환자 관리 시스템을 열 수 없습니다.\n{str(e)}")
    
    def run(self):
        """애플리케이션 실행"""
        # 윈도우 중앙 배치
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
        self.window.mainloop()


# 메인 실행
if __name__ == "__main__":
    app = MedicalSystemApp()
    app.run()
