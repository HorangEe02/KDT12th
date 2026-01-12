"""
health_gui.py
건강 상태 체크 시스템 GUI (환자 관리 시스템 연동)

Author: KDT12 Python Project
Date: 2026-01-09
"""

from tkinter import *
from tkinter import ttk, messagebox
from .health_checker import HealthChecker
from .data_manager import HealthDataManager


class HealthCheckApp(Toplevel):
    """건강 상태 체크 시스템 GUI (Toplevel 기반)"""
    
    def __init__(self, parent=None, base_path=None):
        """생성자: GUI 초기화"""
        super().__init__(parent)
        
        self.title("💓 건강 상태 체크 시스템")
        self.geometry("950x750")
        self.resizable(True, True)
        self.minsize(900, 700)
        
        self.base_path = base_path
        
        # 색상 테마
        self.colors = {
            "bg": "#f0f4f8",
            "header": "#27ae60",
            "primary": "#2ecc71",
            "secondary": "#3498db",
            "dark": "#2c3e50",
            "light": "#ecf0f1",
            "white": "#ffffff",
            "danger": "#e74c3c",
            "warning": "#f39c12",
            "purple": "#9b59b6"
        }
        
        self.configure(bg=self.colors["bg"])
        
        # 데이터 매니저 초기화
        self.data_manager = HealthDataManager(base_path)
        
        # 연동 매니저 초기화 (환자 시스템 연동)
        self.integration_manager = None
        self.patient_list = []
        self.selected_patient_id = None
        self._init_integration()
        
        # 위젯 생성
        self.create_widgets()
        
        # 창 닫기 이벤트
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def _init_integration(self):
        """환자 관리 시스템 연동 초기화"""
        try:
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from integration import IntegrationManager
            self.integration_manager = IntegrationManager(self.base_path)
            self.patient_list = self.integration_manager.get_patient_list()
        except Exception as e:
            print(f"[HealthCheckApp] 연동 초기화 오류: {e}")
            self.integration_manager = None
            self.patient_list = []
    
    def on_close(self):
        """창 닫기"""
        self.destroy()
    
    def create_widgets(self):
        """모든 위젯 생성"""
        # 헤더
        header = Frame(self, bg=self.colors["header"], height=60)
        header.pack(fill=X)
        header.pack_propagate(False)
        
        Label(
            header,
            text="💓 건강 상태 체크 시스템",
            font=("맑은 고딕", 16, "bold"),
            fg=self.colors["white"],
            bg=self.colors["header"]
        ).pack(side=LEFT, padx=20, pady=15)
        
        # 연동 상태 표시
        integration_status = "🔗 환자연동" if self.integration_manager else "⚠️ 단독모드"
        Label(
            header,
            text=integration_status,
            font=("맑은 고딕", 9),
            fg=self.colors["light"],
            bg=self.colors["header"]
        ).pack(side=LEFT, padx=10)
        
        Button(
            header,
            text="✕ 닫기",
            font=("맑은 고딕", 10),
            bg=self.colors["header"],
            fg=self.colors["white"],
            relief=FLAT,
            cursor="hand2",
            command=self.on_close
        ).pack(side=RIGHT, padx=20)
        
        # 메인 컨텐츠
        main_frame = Frame(self, bg=self.colors["bg"])
        main_frame.pack(fill=BOTH, expand=True, padx=15, pady=10)
        
        # 좌측: 입력 폼
        left_frame = Frame(main_frame, bg=self.colors["white"], relief=GROOVE, bd=1)
        left_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 5))
        self.create_input_form(left_frame)
        
        # 우측: 결과
        right_frame = Frame(main_frame, bg=self.colors["white"], relief=GROOVE, bd=1)
        right_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=(5, 0))
        self.create_result_panel(right_frame)
        
        # 하단 버튼
        btn_frame = Frame(self, bg=self.colors["bg"], pady=10)
        btn_frame.pack(fill=X, padx=15)
        
        Button(
            btn_frame, text="🔍 분석하기", font=("맑은 고딕", 10),
            bg=self.colors["primary"], fg=self.colors["white"],
            relief=FLAT, cursor="hand2", command=lambda: self.analyze()
        ).pack(side=LEFT, padx=5, ipadx=12, ipady=5)
        
        Button(
            btn_frame, text="💾 기록 저장", font=("맑은 고딕", 10),
            bg=self.colors["secondary"], fg=self.colors["white"],
            relief=FLAT, cursor="hand2", command=lambda: self.save_record()
        ).pack(side=LEFT, padx=5, ipadx=12, ipady=5)
        
        # 환자로 등록 버튼 (연동 시에만)
        if self.integration_manager:
            Button(
                btn_frame, text="📋 환자로 등록", font=("맑은 고딕", 10),
                bg=self.colors["purple"], fg=self.colors["white"],
                relief=FLAT, cursor="hand2", command=lambda: self.register_as_patient()
            ).pack(side=LEFT, padx=5, ipadx=12, ipady=5)
        
        Button(
            btn_frame, text="📜 기록 보기", font=("맑은 고딕", 10),
            bg="#9b59b6", fg=self.colors["white"],
            relief=FLAT, cursor="hand2", command=lambda: self.show_history()
        ).pack(side=LEFT, padx=5, ipadx=12, ipady=5)
        
        Button(
            btn_frame, text="📊 통계 보기", font=("맑은 고딕", 10),
            bg=self.colors["dark"], fg=self.colors["white"],
            relief=FLAT, cursor="hand2", command=lambda: self.show_statistics()
        ).pack(side=LEFT, padx=5, ipadx=12, ipady=5)
        
        Button(
            btn_frame, text="🔄 초기화", font=("맑은 고딕", 10),
            bg=self.colors["light"], fg=self.colors["dark"],
            relief=FLAT, cursor="hand2", command=lambda: self.reset()
        ).pack(side=LEFT, padx=5, ipadx=12, ipady=5)
    
    def create_input_form(self, parent):
        """입력 폼 생성"""
        Label(
            parent,
            text="📝 건강 정보 입력",
            font=("맑은 고딕", 14, "bold"),
            bg=self.colors["white"],
            fg=self.colors["dark"]
        ).pack(pady=(15, 5))
        
        # 환자 선택 영역 (연동 시에만)
        if self.integration_manager and self.patient_list:
            self.create_patient_selector(parent)
        
        form_frame = Frame(parent, bg=self.colors["white"])
        form_frame.pack(fill=X, padx=20)
        
        # 이름
        Label(form_frame, text="이름:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=0, column=0, pady=5, sticky=E)
        self.name_entry = Entry(form_frame, font=("맑은 고딕", 10), width=18)
        self.name_entry.grid(row=0, column=1, pady=5, padx=5, sticky=W)
        
        # 나이
        Label(form_frame, text="나이:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=1, column=0, pady=5, sticky=E)
        self.age_entry = Entry(form_frame, font=("맑은 고딕", 10), width=8)
        self.age_entry.grid(row=1, column=1, pady=5, padx=5, sticky=W)
        Label(form_frame, text="세", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=1, column=2, sticky=W)
        
        # 성별
        Label(form_frame, text="성별:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=2, column=0, pady=5, sticky=E)
        self.gender_var = StringVar(value="남성")
        gender_frame = Frame(form_frame, bg=self.colors["white"])
        gender_frame.grid(row=2, column=1, pady=5, sticky=W)
        Radiobutton(gender_frame, text="남성", variable=self.gender_var, value="남성", bg=self.colors["white"]).pack(side=LEFT)
        Radiobutton(gender_frame, text="여성", variable=self.gender_var, value="여성", bg=self.colors["white"]).pack(side=LEFT)
        
        # 키
        Label(form_frame, text="키:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=3, column=0, pady=5, sticky=E)
        self.height_entry = Entry(form_frame, font=("맑은 고딕", 10), width=8)
        self.height_entry.grid(row=3, column=1, pady=5, padx=5, sticky=W)
        Label(form_frame, text="cm", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=3, column=2, sticky=W)
        
        # 몸무게
        Label(form_frame, text="몸무게:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=4, column=0, pady=5, sticky=E)
        self.weight_entry = Entry(form_frame, font=("맑은 고딕", 10), width=8)
        self.weight_entry.grid(row=4, column=1, pady=5, padx=5, sticky=W)
        Label(form_frame, text="kg", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=4, column=2, sticky=W)
        
        # 혈압
        Label(form_frame, text="수축기 혈압:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=5, column=0, pady=5, sticky=E)
        self.ap_hi_entry = Entry(form_frame, font=("맑은 고딕", 10), width=8)
        self.ap_hi_entry.grid(row=5, column=1, pady=5, padx=5, sticky=W)
        Label(form_frame, text="mmHg", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=5, column=2, sticky=W)
        
        Label(form_frame, text="이완기 혈압:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=6, column=0, pady=5, sticky=E)
        self.ap_lo_entry = Entry(form_frame, font=("맑은 고딕", 10), width=8)
        self.ap_lo_entry.grid(row=6, column=1, pady=5, padx=5, sticky=W)
        Label(form_frame, text="mmHg", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=6, column=2, sticky=W)
        
        # 콜레스테롤
        Label(form_frame, text="콜레스테롤:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=7, column=0, pady=5, sticky=E)
        self.chol_var = StringVar(value="정상")
        chol_combo = ttk.Combobox(form_frame, textvariable=self.chol_var, values=["정상", "높음", "매우 높음"], width=10, state="readonly")
        chol_combo.grid(row=7, column=1, pady=5, padx=5, sticky=W)
        
        # 혈당
        Label(form_frame, text="혈당:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=8, column=0, pady=5, sticky=E)
        self.gluc_var = StringVar(value="정상")
        gluc_combo = ttk.Combobox(form_frame, textvariable=self.gluc_var, values=["정상", "높음", "매우 높음"], width=10, state="readonly")
        gluc_combo.grid(row=8, column=1, pady=5, padx=5, sticky=W)
        
        # 생활 습관
        Label(form_frame, text="─── 생활 습관 ───", font=("맑은 고딕", 9), bg=self.colors["white"], fg="#666").grid(row=9, column=0, columnspan=3, pady=(10, 5))

        self.smoke_var = IntVar(value=0)
        self.alco_var = IntVar(value=0)
        self.active_var = IntVar(value=1)

        Checkbutton(form_frame, text="흡연", variable=self.smoke_var, bg=self.colors["white"]).grid(row=10, column=0, columnspan=2, sticky=W, padx=20)
        Checkbutton(form_frame, text="음주", variable=self.alco_var, bg=self.colors["white"]).grid(row=11, column=0, columnspan=2, sticky=W, padx=20)
        Checkbutton(form_frame, text="규칙적 운동", variable=self.active_var, bg=self.colors["white"]).grid(row=12, column=0, columnspan=2, sticky=W, padx=20)

        # 의료 정보
        Label(form_frame, text="─── 의료 정보 ───", font=("맑은 고딕", 9), bg=self.colors["white"], fg="#666").grid(row=13, column=0, columnspan=3, pady=(10, 5))

        # 담당의
        Label(form_frame, text="담당의:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=14, column=0, pady=5, sticky=E)
        self.doctor_entry = Entry(form_frame, font=("맑은 고딕", 10), width=18)
        self.doctor_entry.grid(row=14, column=1, pady=5, padx=5, sticky=W)

        # 병원
        Label(form_frame, text="병원:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=15, column=0, pady=5, sticky=E)
        self.hospital_entry = Entry(form_frame, font=("맑은 고딕", 10), width=18)
        self.hospital_entry.grid(row=15, column=1, pady=5, padx=5, sticky=W)

        # 병실
        Label(form_frame, text="병실:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=16, column=0, pady=5, sticky=E)
        self.room_entry = Entry(form_frame, font=("맑은 고딕", 10), width=8)
        self.room_entry.grid(row=16, column=1, pady=5, padx=5, sticky=W)
        Label(form_frame, text="호", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=16, column=2, sticky=W)

        # 입원 유형
        Label(form_frame, text="입원유형:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=17, column=0, pady=5, sticky=E)
        self.admission_var = StringVar(value="Elective")
        admission_combo = ttk.Combobox(form_frame, textvariable=self.admission_var, values=["Emergency", "Elective", "Urgent"], width=10, state="readonly")
        admission_combo.grid(row=17, column=1, pady=5, padx=5, sticky=W)

        # 검사 결과
        Label(form_frame, text="검사결과:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=18, column=0, pady=5, sticky=E)
        self.test_var = StringVar(value="Normal")
        test_combo = ttk.Combobox(form_frame, textvariable=self.test_var, values=["Normal", "Abnormal", "Inconclusive"], width=10, state="readonly")
        test_combo.grid(row=18, column=1, pady=5, padx=5, sticky=W)

        # 청구 금액
        Label(form_frame, text="청구금액:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=19, column=0, pady=5, sticky=E)
        self.billing_entry = Entry(form_frame, font=("맑은 고딕", 10), width=12)
        self.billing_entry.grid(row=19, column=1, pady=5, padx=5, sticky=W)
        Label(form_frame, text="원", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=19, column=2, sticky=W)
    
    def create_patient_selector(self, parent):
        """환자 선택 영역 생성"""
        selector_frame = Frame(parent, bg=self.colors["light"], relief=GROOVE, bd=1)
        selector_frame.pack(fill=X, padx=20, pady=(0, 10))
        
        Label(
            selector_frame,
            text="🔗 환자 연동",
            font=("맑은 고딕", 10, "bold"),
            bg=self.colors["light"]
        ).pack(side=LEFT, padx=10, pady=8)
        
        # 환자 목록 콤보박스
        patient_options = ["신규 입력"] + [
            f"{p[0]} - {p[1]} ({p[2]}세, {'남' if p[3]=='Male' else '여'})"
            for p in self.patient_list
        ]
        
        self.patient_combo_var = StringVar(value="신규 입력")
        self.patient_combo = ttk.Combobox(
            selector_frame,
            textvariable=self.patient_combo_var,
            values=patient_options,
            width=30,
            state="readonly"
        )
        self.patient_combo.pack(side=LEFT, padx=5, pady=8)
        self.patient_combo.bind("<<ComboboxSelected>>", self.on_patient_selected)
        
        Button(
            selector_frame,
            text="불러오기",
            font=("맑은 고딕", 9),
            bg=self.colors["secondary"],
            fg=self.colors["white"],
            relief=FLAT,
            command=lambda: self.load_patient_info()
        ).pack(side=LEFT, padx=5, pady=8)
    
    def on_patient_selected(self, event=None):
        """환자 선택 시 호출"""
        selection = self.patient_combo_var.get()
        if selection == "신규 입력":
            self.selected_patient_id = None
        else:
            # "P001 - 김민수 (45세, 남)" 형식에서 ID 추출
            self.selected_patient_id = selection.split(" - ")[0]
    
    def load_patient_info(self):
        """선택된 환자 정보 불러오기"""
        if not self.selected_patient_id:
            return
        
        patient = self.integration_manager.get_patient_by_id(self.selected_patient_id)
        if patient:
            # 기존 입력 지우기
            self.name_entry.delete(0, END)
            self.age_entry.delete(0, END)
            
            # 환자 정보 채우기
            self.name_entry.insert(0, patient.name)
            self.age_entry.insert(0, str(patient.age))
            self.gender_var.set("남성" if patient.gender == "Male" else "여성")
            
            messagebox.showinfo("불러오기 완료", f"{patient.name} 환자 정보를 불러왔습니다.")
    
    def create_result_panel(self, parent):
        """결과 패널 생성"""
        Label(
            parent,
            text="📊 분석 결과",
            font=("맑은 고딕", 14, "bold"),
            bg=self.colors["white"],
            fg=self.colors["dark"]
        ).pack(pady=(15, 10))
        
        result_frame = Frame(parent, bg=self.colors["white"])
        result_frame.pack(fill=BOTH, expand=True, padx=15)
        
        # BMI 카드
        self.bmi_frame = self.create_result_card(result_frame, "🏋️ BMI")
        self.bmi_frame.pack(fill=X, pady=5)
        
        # 혈압 카드
        self.bp_frame = self.create_result_card(result_frame, "❤️ 혈압")
        self.bp_frame.pack(fill=X, pady=5)
        
        # 위험도 카드
        self.risk_frame = self.create_result_card(result_frame, "⚠️ 심혈관 위험도")
        self.risk_frame.pack(fill=X, pady=5)
        
        # 추천 진단명 (연동 시에만)
        if self.integration_manager:
            self.condition_frame = Frame(result_frame, bg=self.colors["light"], relief=RIDGE, bd=1)
            self.condition_frame.pack(fill=X, pady=5)
            
            Label(
                self.condition_frame,
                text="🩺 추천 진단명",
                font=("맑은 고딕", 10, "bold"),
                bg=self.colors["light"]
            ).pack(side=LEFT, padx=10, pady=8)
            
            self.condition_label = Label(
                self.condition_frame,
                text="-",
                font=("맑은 고딕", 10),
                bg=self.colors["light"],
                fg=self.colors["purple"]
            )
            self.condition_label.pack(side=LEFT, padx=10, pady=8)
        
        # 성별 비교
        Label(
            result_frame,
            text="📈 성별 평균 비교",
            font=("맑은 고딕", 11, "bold"),
            bg=self.colors["white"]
        ).pack(pady=(10, 5), anchor=W)
        
        self.comparison_label = Label(
            result_frame,
            text="분석 후 표시됩니다",
            font=("맑은 고딕", 9),
            bg=self.colors["white"],
            fg="#666",
            justify=LEFT
        )
        self.comparison_label.pack(anchor=W)
        
        # 건강 조언
        Label(
            result_frame,
            text="💡 건강 조언",
            font=("맑은 고딕", 11, "bold"),
            bg=self.colors["white"]
        ).pack(pady=(10, 5), anchor=W)
        
        self.advice_text = Text(
            result_frame,
            font=("맑은 고딕", 9),
            height=5,
            wrap=WORD,
            state=DISABLED,
            bg=self.colors["light"]
        )
        self.advice_text.pack(fill=X, pady=5)
    
    def create_result_card(self, parent, title):
        """결과 카드 생성"""
        card = Frame(parent, bg=self.colors["light"], relief=RIDGE, bd=1)
        
        Label(
            card,
            text=title,
            font=("맑은 고딕", 10, "bold"),
            bg=self.colors["light"]
        ).pack(side=LEFT, padx=10, pady=8)
        
        card.value_label = Label(
            card,
            text="-",
            font=("맑은 고딕", 10),
            bg=self.colors["light"]
        )
        card.value_label.pack(side=LEFT, padx=5, pady=8)
        
        card.status_label = Label(
            card,
            text="",
            font=("맑은 고딕", 10, "bold"),
            bg=self.colors["light"]
        )
        card.status_label.pack(side=RIGHT, padx=10, pady=8)
        
        return card
    
    def get_chol_value(self):
        """콜레스테롤 값 변환"""
        mapping = {"정상": 1, "높음": 2, "매우 높음": 3}
        return mapping.get(self.chol_var.get(), 1)
    
    def get_gluc_value(self):
        """혈당 값 변환"""
        mapping = {"정상": 1, "높음": 2, "매우 높음": 3}
        return mapping.get(self.gluc_var.get(), 1)
    
    def validate_inputs(self):
        """입력 검증"""
        try:
            if not self.name_entry.get().strip():
                raise ValueError("이름을 입력하세요.")
            int(self.age_entry.get())
            float(self.height_entry.get())
            float(self.weight_entry.get())
            int(self.ap_hi_entry.get())
            int(self.ap_lo_entry.get())
            return True
        except ValueError as e:
            messagebox.showerror("입력 오류", f"올바른 값을 입력하세요.\n{str(e)}")
            return False
    
    def analyze(self):
        """건강 분석"""
        if not self.validate_inputs():
            return
        
        checker = HealthChecker(
            age=int(self.age_entry.get()),
            gender=self.gender_var.get(),
            height=float(self.height_entry.get()),
            weight=float(self.weight_entry.get()),
            ap_hi=int(self.ap_hi_entry.get()),
            ap_lo=int(self.ap_lo_entry.get()),
            cholesterol=self.get_chol_value(),
            gluc=self.get_gluc_value(),
            smoke=self.smoke_var.get(),
            alco=self.alco_var.get(),
            active=self.active_var.get()
        )
        
        # BMI 분석
        bmi_value, bmi_status, bmi_color = checker.calculate_bmi()
        self.bmi_frame.status_label.config(text=bmi_status, fg=bmi_color)
        self.bmi_frame.value_label.config(text=f"BMI: {bmi_value}", fg=self.colors["dark"])
        
        # 혈압 분석
        bp_status, bp_desc, bp_color = checker.analyze_blood_pressure()
        self.bp_frame.status_label.config(text=bp_status, fg=bp_color)
        self.bp_frame.value_label.config(
            text=f"{self.ap_hi_entry.get()}/{self.ap_lo_entry.get()} mmHg",
            fg=self.colors["dark"]
        )
        
        # 위험도 분석
        risk_score, risk_grade, risk_desc, risk_color = checker.calculate_risk_score()
        self.risk_frame.status_label.config(text=f"{risk_grade} ({risk_score}점)", fg=risk_color)
        self.risk_frame.value_label.config(text=risk_desc, fg=self.colors["dark"])
        
        # 추천 진단명 (연동 시)
        if self.integration_manager:
            user_data = checker.to_dict()
            condition, reason = self.integration_manager.suggest_condition(user_data)
            self.condition_label.config(text=f"{condition} - {reason}")
            self.suggested_condition = condition
        
        # 성별 평균 비교
        user_data = checker.to_dict()
        gender = self.gender_var.get()
        comparison = self.data_manager.compare_with_gender_average(user_data, gender)
        
        if comparison:
            comparison_text = f"📊 {gender} 평균 대비 (샘플 {comparison['sample_count']}명)\n\n"
            
            bmi_comp = comparison["bmi"]
            bmi_icon = "🔴" if bmi_comp["status"] == "higher" and bmi_comp["diff"] > 2 else "🟢" if bmi_comp["status"] == "lower" else "🟡"
            comparison_text += f"{bmi_icon} BMI: {bmi_comp['user']} (평균 {bmi_comp['avg']}) → {bmi_comp['text']}\n"
            
            height_comp = comparison["height"]
            comparison_text += f"📏 키: {height_comp['user']}cm (평균 {height_comp['avg']}cm) → {height_comp['text']}\n"
            
            weight_comp = comparison["weight"]
            weight_icon = "🔴" if weight_comp["status"] == "higher" and weight_comp["diff"] > 5 else "🟢" if weight_comp["status"] == "lower" else "🟡"
            comparison_text += f"{weight_icon} 몸무게: {weight_comp['user']}kg (평균 {weight_comp['avg']}kg) → {weight_comp['text']}\n"
            
            bp_comp = comparison["ap_hi"]
            bp_icon = "🔴" if bp_comp["status"] == "higher" and bp_comp["diff"] > 10 else "🟢" if bp_comp["status"] == "lower" else "🟡"
            comparison_text += f"{bp_icon} 수축기 혈압: {bp_comp['user']}mmHg (평균 {bp_comp['avg']}mmHg) → {bp_comp['text']}\n"
            
            comparison_text += f"\n⚠️ {gender} 심혈관 질환 비율: {comparison['cardio_rate']}%"
            
            self.comparison_label.config(text=comparison_text, fg=self.colors["dark"])
        
        # 건강 조언
        advice_list = checker.get_health_advice()
        self.advice_text.config(state=NORMAL)
        self.advice_text.delete(1.0, END)
        for advice in advice_list:
            self.advice_text.insert(END, f"• {advice}\n")
        self.advice_text.config(state=DISABLED)
        
        self.current_checker = checker
    
    def save_record(self):
        """기록 저장"""
        if not hasattr(self, "current_checker"):
            messagebox.showwarning("경고", "먼저 분석을 실행하세요.")
            return

        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("경고", "이름을 입력하세요.")
            return

        data = self.current_checker.to_dict()

        # 추가 의료 정보 포함
        data["doctor"] = self.doctor_entry.get().strip()
        data["hospital"] = self.hospital_entry.get().strip()
        data["room_number"] = self.room_entry.get().strip() if self.room_entry.get().strip() else "0"
        data["admission_type"] = self.admission_var.get()
        data["test_results"] = self.test_var.get()
        data["billing_amount"] = self.billing_entry.get().strip() if self.billing_entry.get().strip() else "0"

        patient_id = self.selected_patient_id if hasattr(self, 'selected_patient_id') else ""

        if self.data_manager.save_record_with_patient_id(patient_id or "", name, data):
            link_msg = f" (환자 ID: {patient_id})" if patient_id else ""
            messagebox.showinfo("저장 완료", f"{name}님의 건강 기록이 저장되었습니다.{link_msg}")
        else:
            messagebox.showerror("저장 실패", "기록 저장에 실패했습니다.")
    
    def register_as_patient(self):
        """건강 체크 결과로 환자 등록"""
        if not hasattr(self, "current_checker"):
            messagebox.showwarning("경고", "먼저 분석을 실행하세요.")
            return
        
        if not self.integration_manager:
            messagebox.showerror("오류", "환자 관리 시스템과 연동되지 않았습니다.")
            return
        
        # 등록 다이얼로그
        dialog = Toplevel(self)
        dialog.title("📋 환자 등록")
        dialog.geometry("450x620")
        dialog.resizable(False, False)
        dialog.configure(bg=self.colors["white"])
        dialog.transient(self)
        dialog.grab_set()
        
        Label(
            dialog,
            text="📋 건강 체크 결과로 환자 등록",
            font=("맑은 고딕", 12, "bold"),
            bg=self.colors["white"]
        ).pack(pady=15)
        
        # 스크롤 가능한 폼
        canvas = Canvas(dialog, bg=self.colors["white"], highlightthickness=0)
        scrollbar = Scrollbar(dialog, orient=VERTICAL, command=canvas.yview)
        form = Frame(canvas, bg=self.colors["white"])
        
        form.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=form, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=LEFT, fill=BOTH, expand=True, padx=30)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # 기본 정보 표시
        name = self.name_entry.get().strip()
        age = self.age_entry.get()
        gender = self.gender_var.get()
        
        Label(form, text=f"이름: {name}", font=("맑은 고딕", 10), bg=self.colors["white"]).pack(anchor=W, pady=2)
        Label(form, text=f"나이: {age}세", font=("맑은 고딕", 10), bg=self.colors["white"]).pack(anchor=W, pady=2)
        Label(form, text=f"성별: {gender}", font=("맑은 고딕", 10), bg=self.colors["white"]).pack(anchor=W, pady=2)
        
        # 추천 진단명
        suggested = getattr(self, 'suggested_condition', 'Asthma')
        Label(form, text=f"추천 진단명: {suggested}", font=("맑은 고딕", 10, "bold"), bg=self.colors["white"], fg=self.colors["purple"]).pack(anchor=W, pady=5)
        
        Label(form, text="─── 추가 정보 입력 ───", font=("맑은 고딕", 9), bg=self.colors["white"], fg="#666").pack(pady=10)
        
        entries = {}
        
        # 혈액형
        row1 = Frame(form, bg=self.colors["white"])
        row1.pack(fill=X, pady=3)
        Label(row1, text="혈액형:", font=("맑은 고딕", 10), bg=self.colors["white"], width=10, anchor=E).pack(side=LEFT)
        blood_var = StringVar(value="A+")
        ttk.Combobox(row1, textvariable=blood_var, values=["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"], width=15, state="readonly").pack(side=LEFT, padx=5)
        entries["blood_type"] = blood_var
        
        # 담당의
        row2 = Frame(form, bg=self.colors["white"])
        row2.pack(fill=X, pady=3)
        Label(row2, text="담당의:", font=("맑은 고딕", 10), bg=self.colors["white"], width=10, anchor=E).pack(side=LEFT)
        entries["doctor"] = Entry(row2, font=("맑은 고딕", 10), width=18)
        entries["doctor"].pack(side=LEFT, padx=5)
        
        # 병원
        row3 = Frame(form, bg=self.colors["white"])
        row3.pack(fill=X, pady=3)
        Label(row3, text="병원:", font=("맑은 고딕", 10), bg=self.colors["white"], width=10, anchor=E).pack(side=LEFT)
        entries["hospital"] = Entry(row3, font=("맑은 고딕", 10), width=18)
        entries["hospital"].pack(side=LEFT, padx=5)
        
        # 병실
        row4 = Frame(form, bg=self.colors["white"])
        row4.pack(fill=X, pady=3)
        Label(row4, text="병실:", font=("맑은 고딕", 10), bg=self.colors["white"], width=10, anchor=E).pack(side=LEFT)
        entries["room_number"] = Entry(row4, font=("맑은 고딕", 10), width=8)
        entries["room_number"].pack(side=LEFT, padx=5)
        Label(row4, text="호", font=("맑은 고딕", 10), bg=self.colors["white"]).pack(side=LEFT)
        
        # 입원유형
        row5 = Frame(form, bg=self.colors["white"])
        row5.pack(fill=X, pady=3)
        Label(row5, text="입원유형:", font=("맑은 고딕", 10), bg=self.colors["white"], width=10, anchor=E).pack(side=LEFT)
        admission_var = StringVar(value="Elective")
        ttk.Combobox(row5, textvariable=admission_var, values=["Emergency", "Elective", "Urgent"], width=15, state="readonly").pack(side=LEFT, padx=5)
        entries["admission_type"] = admission_var
        
        # 검사결과
        row6 = Frame(form, bg=self.colors["white"])
        row6.pack(fill=X, pady=3)
        Label(row6, text="검사결과:", font=("맑은 고딕", 10), bg=self.colors["white"], width=10, anchor=E).pack(side=LEFT)
        test_var = StringVar(value="Normal")
        ttk.Combobox(row6, textvariable=test_var, values=["Normal", "Abnormal", "Inconclusive"], width=15, state="readonly").pack(side=LEFT, padx=5)
        entries["test_results"] = test_var
        
        # 청구금액
        row7 = Frame(form, bg=self.colors["white"])
        row7.pack(fill=X, pady=3)
        Label(row7, text="청구금액:", font=("맑은 고딕", 10), bg=self.colors["white"], width=10, anchor=E).pack(side=LEFT)
        entries["billing_amount"] = Entry(row7, font=("맑은 고딕", 10), width=12)
        entries["billing_amount"].pack(side=LEFT, padx=5)
        Label(row7, text="원", font=("맑은 고딕", 10), bg=self.colors["white"]).pack(side=LEFT)
        
        # 보험사
        row8 = Frame(form, bg=self.colors["white"])
        row8.pack(fill=X, pady=3)
        Label(row8, text="보험사:", font=("맑은 고딕", 10), bg=self.colors["white"], width=10, anchor=E).pack(side=LEFT)
        entries["insurance_provider"] = Entry(row8, font=("맑은 고딕", 10), width=18)
        entries["insurance_provider"].pack(side=LEFT, padx=5)
        
        # 처방약
        row9 = Frame(form, bg=self.colors["white"])
        row9.pack(fill=X, pady=3)
        Label(row9, text="처방약:", font=("맑은 고딕", 10), bg=self.colors["white"], width=10, anchor=E).pack(side=LEFT)
        entries["medication"] = Entry(row9, font=("맑은 고딕", 10), width=18)
        entries["medication"].pack(side=LEFT, padx=5)
        
        def do_register():
            health_data = self.current_checker.to_dict()
            health_data["name"] = name
            
            extra_info = {
                "blood_type": entries["blood_type"].get(),
                "medical_condition": suggested,
                "doctor": entries["doctor"].get().strip(),
                "hospital": entries["hospital"].get().strip(),
                "room_number": int(entries["room_number"].get()) if entries["room_number"].get().strip() else 0,
                "admission_type": entries["admission_type"].get(),
                "test_results": entries["test_results"].get(),
                "billing_amount": float(entries["billing_amount"].get()) if entries["billing_amount"].get().strip() else 0,
                "insurance_provider": entries["insurance_provider"].get().strip(),
                "medication": entries["medication"].get().strip()
            }
            
            success, result = self.integration_manager.register_patient_from_health(health_data, extra_info)
            
            if success:
                messagebox.showinfo("등록 완료", f"환자가 등록되었습니다.\n환자 ID: {result}")
                # 환자 목록 갱신
                self.patient_list = self.integration_manager.get_patient_list()
                dialog.destroy()
            else:
                messagebox.showerror("등록 실패", result)
        
        btn_frame = Frame(dialog, bg=self.colors["white"])
        btn_frame.pack(pady=20)
        
        Button(
            btn_frame, text="등록", font=("맑은 고딕", 10),
            bg=self.colors["primary"], fg=self.colors["white"],
            relief=FLAT, command=do_register
        ).pack(side=LEFT, padx=10, ipadx=15, ipady=3)
        
        Button(
            btn_frame, text="취소", font=("맑은 고딕", 10),
            bg=self.colors["light"], fg=self.colors["dark"],
            relief=FLAT, command=dialog.destroy
        ).pack(side=LEFT, padx=10, ipadx=15, ipady=3)
    
    def show_history(self):
        """기록 보기"""
        records = self.data_manager.load_records()
        
        if not records:
            messagebox.showinfo("기록 없음", "저장된 기록이 없습니다.")
            return
        
        popup = Toplevel(self)
        popup.title("📋 건강 기록")
        popup.geometry("800x400")
        popup.transient(self)
        
        columns = ("date", "patient_id", "name", "age", "gender", "bmi", "ap", "risk")
        tree = ttk.Treeview(popup, columns=columns, show="headings", height=15)
        
        tree.heading("date", text="날짜")
        tree.heading("patient_id", text="환자ID")
        tree.heading("name", text="이름")
        tree.heading("age", text="나이")
        tree.heading("gender", text="성별")
        tree.heading("bmi", text="BMI")
        tree.heading("ap", text="혈압")
        tree.heading("risk", text="위험도")
        
        tree.column("date", width=120)
        tree.column("patient_id", width=70)
        tree.column("name", width=80)
        tree.column("age", width=50)
        tree.column("gender", width=50)
        tree.column("bmi", width=60)
        tree.column("ap", width=80)
        tree.column("risk", width=60)
        
        for r in records:
            tree.insert("", END, values=(
                r.get("date", ""),
                r.get("patient_id", "-"),
                r.get("name", ""),
                r.get("age", ""),
                r.get("gender", ""),
                r.get("bmi", ""),
                f"{r.get('ap_hi', '')}/{r.get('ap_lo', '')}",
                r.get("risk_score", "")
            ))
        
        scrollbar = Scrollbar(popup, orient=VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
    
    def show_statistics(self):
        """통계 보기 (표 형태)"""
        stats = self.data_manager.get_gender_statistics()
        
        popup = Toplevel(self)
        popup.title("📊 건강 통계")
        popup.geometry("750x500")
        popup.configure(bg=self.colors["white"])
        popup.transient(self)
        
        Label(
            popup,
            text="📊 성별 건강 통계 (Kaggle 데이터 기반)",
            font=("맑은 고딕", 14, "bold"),
            bg=self.colors["white"]
        ).pack(pady=15)
        
        # 표 프레임
        table_frame = Frame(popup, bg=self.colors["white"])
        table_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
        
        # Treeview로 표 생성
        columns = ("category", "male", "female", "total")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        
        tree.heading("category", text="항목")
        tree.heading("male", text="👨 남성")
        tree.heading("female", text="👩 여성")
        tree.heading("total", text="👥 전체")
        
        tree.column("category", width=150, anchor=W)
        tree.column("male", width=120, anchor=CENTER)
        tree.column("female", width=120, anchor=CENTER)
        tree.column("total", width=120, anchor=CENTER)
        
        # 데이터 추출
        male = stats.get("male", {})
        female = stats.get("female", {})
        total = stats.get("total", {})
        
        # 표 데이터 구성
        rows = [
            ("📊 샘플 수", f"{male.get('total_samples', 0)}명", f"{female.get('total_samples', 0)}명", f"{total.get('total_samples', 0)}명"),
            ("📅 평균 나이", f"{male.get('avg_age', 0)}세", f"{female.get('avg_age', 0)}세", f"{total.get('avg_age', 0)}세"),
            ("📏 평균 키", f"{male.get('avg_height', 0)}cm", f"{female.get('avg_height', 0)}cm", f"{total.get('avg_height', 0)}cm"),
            ("⚖️ 평균 몸무게", f"{male.get('avg_weight', 0)}kg", f"{female.get('avg_weight', 0)}kg", f"{total.get('avg_weight', 0)}kg"),
            ("🏋️ 평균 BMI", f"{male.get('avg_bmi', 0)}", f"{female.get('avg_bmi', 0)}", f"{total.get('avg_bmi', 0)}"),
            ("❤️ 평균 수축기 혈압", f"{male.get('avg_ap_hi', 0)}mmHg", f"{female.get('avg_ap_hi', 0)}mmHg", f"{total.get('avg_ap_hi', 0)}mmHg"),
            ("💜 평균 이완기 혈압", f"{male.get('avg_ap_lo', 0)}mmHg", f"{female.get('avg_ap_lo', 0)}mmHg", f"{total.get('avg_ap_lo', 0)}mmHg"),
            ("─" * 15, "─" * 10, "─" * 10, "─" * 10),
            ("🫀 심혈관 질환율", f"{male.get('cardio_rate', 0)}%", f"{female.get('cardio_rate', 0)}%", f"{total.get('cardio_rate', 0)}%"),
            ("🚬 흡연율", f"{male.get('smoke_rate', 0)}%", f"{female.get('smoke_rate', 0)}%", f"{total.get('smoke_rate', 0)}%"),
            ("🧪 고콜레스테롤율", f"{male.get('high_chol_rate', 0)}%", f"{female.get('high_chol_rate', 0)}%", f"{total.get('high_chol_rate', 0)}%"),
        ]
        
        for row in rows:
            tree.insert("", END, values=row)
        
        # 스크롤바
        scrollbar = Scrollbar(table_frame, orient=VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # 안내 문구
        Label(
            popup,
            text="※ 위 통계는 Kaggle 심혈관 질환 데이터셋 기반입니다.",
            font=("맑은 고딕", 9),
            bg=self.colors["white"],
            fg="#666"
        ).pack(pady=5)
        
        Button(
            popup, text="닫기", font=("맑은 고딕", 10),
            bg=self.colors["light"], fg=self.colors["dark"],
            relief=FLAT, command=popup.destroy
        ).pack(pady=10, ipadx=20)
    
    def reset(self):
        """입력 초기화"""
        self.name_entry.delete(0, END)
        self.age_entry.delete(0, END)
        self.height_entry.delete(0, END)
        self.weight_entry.delete(0, END)
        self.ap_hi_entry.delete(0, END)
        self.ap_lo_entry.delete(0, END)
        self.gender_var.set("남성")
        self.chol_var.set("정상")
        self.gluc_var.set("정상")
        self.smoke_var.set(0)
        self.alco_var.set(0)
        self.active_var.set(1)

        # 추가 필드 초기화
        self.doctor_entry.delete(0, END)
        self.hospital_entry.delete(0, END)
        self.room_entry.delete(0, END)
        self.admission_var.set("Elective")
        self.test_var.set("Normal")
        self.billing_entry.delete(0, END)

        if hasattr(self, 'patient_combo_var'):
            self.patient_combo_var.set("신규 입력")
        self.selected_patient_id = None

        self.bmi_frame.value_label.config(text="-")
        self.bmi_frame.status_label.config(text="")
        self.bp_frame.value_label.config(text="-")
        self.bp_frame.status_label.config(text="")
        self.risk_frame.value_label.config(text="-")
        self.risk_frame.status_label.config(text="")

        if hasattr(self, 'condition_label'):
            self.condition_label.config(text="-")

        self.comparison_label.config(text="분석 후 표시됩니다", fg="#666")

        self.advice_text.config(state=NORMAL)
        self.advice_text.delete(1.0, END)
        self.advice_text.config(state=DISABLED)

        if hasattr(self, "current_checker"):
            delattr(self, "current_checker")
