"""
main.py
건강 상태 체크 & 관리 시스템 - 메인 GUI

Author: KDT12 Python Project
Date: 2026-01-08
데이터 출처: Kaggle - Cardiovascular Disease Dataset
"""

import os
import sys

# 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tkinter import *
from tkinter import ttk, messagebox
from health_checker import HealthChecker
from data_manager import DataManager


class HealthCheckApp:
    """
    건강 상태 체크 GUI 애플리케이션
    
    tkinter를 사용한 건강 관리 시스템
    - BMI 계산
    - 혈압 분석
    - 심혈관 질환 위험도 평가
    - 기록 저장/조회
    """
    
    def __init__(self):
        """생성자: GUI 초기화"""
        self.window = Tk()
        self.window.title("🏥 건강 상태 체크 시스템")
        self.window.geometry("900x700")
        self.window.resizable(False, False)
        self.window.configure(bg="#f5f6fa")
        
        # 데이터 매니저 초기화
        self.data_manager = DataManager()
        
        # 색상 테마
        self.colors = {
            "bg": "#f5f6fa",
            "primary": "#3498db",
            "success": "#2ecc71",
            "warning": "#f39c12",
            "danger": "#e74c3c",
            "dark": "#2c3e50",
            "light": "#ecf0f1",
            "white": "#ffffff"
        }
        
        # 위젯 생성
        self.create_widgets()
    
    def create_widgets(self):
        """모든 위젯 생성"""
        # 제목 프레임
        self.create_header()
        
        # 메인 컨테이너
        main_frame = Frame(self.window, bg=self.colors["bg"])
        main_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
        
        # 왼쪽: 입력 폼
        left_frame = Frame(main_frame, bg=self.colors["white"], relief=RIDGE, bd=2)
        left_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))
        self.create_input_form(left_frame)
        
        # 오른쪽: 결과 표시
        right_frame = Frame(main_frame, bg=self.colors["white"], relief=RIDGE, bd=2)
        right_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=(10, 0))
        self.create_result_panel(right_frame)
        
        # 하단 버튼
        self.create_bottom_buttons()
    
    def create_header(self):
        """상단 헤더 생성"""
        header = Frame(self.window, bg=self.colors["primary"], height=60)
        header.pack(fill=X)
        header.pack_propagate(False)
        
        title_label = Label(
            header,
            text="🏥 건강 상태 체크 & 관리 시스템",
            font=("맑은 고딕", 18, "bold"),
            fg=self.colors["white"],
            bg=self.colors["primary"]
        )
        title_label.pack(expand=True)
    
    def create_input_form(self, parent):
        """입력 폼 생성"""
        # 제목
        Label(
            parent,
            text="📋 기본 정보 입력",
            font=("맑은 고딕", 14, "bold"),
            bg=self.colors["white"],
            fg=self.colors["dark"]
        ).pack(pady=(15, 10))
        
        # 입력 영역 프레임
        input_frame = Frame(parent, bg=self.colors["white"])
        input_frame.pack(fill=X, padx=20)
        
        # 이름
        self.create_input_row(input_frame, "이름:", 0)
        self.name_entry = Entry(input_frame, font=("맑은 고딕", 11), width=15)
        self.name_entry.grid(row=0, column=1, pady=5, sticky=W)
        
        # 나이
        self.create_input_row(input_frame, "나이:", 1)
        self.age_entry = Entry(input_frame, font=("맑은 고딕", 11), width=8)
        self.age_entry.grid(row=1, column=1, pady=5, sticky=W)
        Label(input_frame, text="세", bg=self.colors["white"]).grid(row=1, column=2, sticky=W)
        
        # 성별
        self.create_input_row(input_frame, "성별:", 2)
        self.gender_var = StringVar(value="남성")
        gender_frame = Frame(input_frame, bg=self.colors["white"])
        gender_frame.grid(row=2, column=1, columnspan=2, sticky=W)
        Radiobutton(gender_frame, text="남성", variable=self.gender_var, value="남성", bg=self.colors["white"]).pack(side=LEFT)
        Radiobutton(gender_frame, text="여성", variable=self.gender_var, value="여성", bg=self.colors["white"]).pack(side=LEFT)
        
        # 키
        self.create_input_row(input_frame, "키:", 3)
        self.height_entry = Entry(input_frame, font=("맑은 고딕", 11), width=8)
        self.height_entry.grid(row=3, column=1, pady=5, sticky=W)
        Label(input_frame, text="cm", bg=self.colors["white"]).grid(row=3, column=2, sticky=W)
        
        # 몸무게
        self.create_input_row(input_frame, "몸무게:", 4)
        self.weight_entry = Entry(input_frame, font=("맑은 고딕", 11), width=8)
        self.weight_entry.grid(row=4, column=1, pady=5, sticky=W)
        Label(input_frame, text="kg", bg=self.colors["white"]).grid(row=4, column=2, sticky=W)
        
        # 구분선
        ttk.Separator(parent, orient=HORIZONTAL).pack(fill=X, padx=20, pady=15)
        
        # 건강 지표 제목
        Label(
            parent,
            text="🩺 건강 지표",
            font=("맑은 고딕", 14, "bold"),
            bg=self.colors["white"],
            fg=self.colors["dark"]
        ).pack(pady=(0, 10))
        
        # 건강 지표 프레임
        health_frame = Frame(parent, bg=self.colors["white"])
        health_frame.pack(fill=X, padx=20)
        
        # 수축기 혈압
        self.create_input_row(health_frame, "수축기 혈압:", 0)
        self.ap_hi_entry = Entry(health_frame, font=("맑은 고딕", 11), width=8)
        self.ap_hi_entry.grid(row=0, column=1, pady=5, sticky=W)
        Label(health_frame, text="mmHg", bg=self.colors["white"]).grid(row=0, column=2, sticky=W)
        
        # 이완기 혈압
        self.create_input_row(health_frame, "이완기 혈압:", 1)
        self.ap_lo_entry = Entry(health_frame, font=("맑은 고딕", 11), width=8)
        self.ap_lo_entry.grid(row=1, column=1, pady=5, sticky=W)
        Label(health_frame, text="mmHg", bg=self.colors["white"]).grid(row=1, column=2, sticky=W)
        
        # 콜레스테롤
        self.create_input_row(health_frame, "콜레스테롤:", 2)
        self.chol_var = StringVar(value="정상")
        chol_combo = ttk.Combobox(health_frame, textvariable=self.chol_var, values=["정상", "높음", "매우 높음"], width=10, state="readonly")
        chol_combo.grid(row=2, column=1, columnspan=2, pady=5, sticky=W)
        
        # 혈당
        self.create_input_row(health_frame, "혈당:", 3)
        self.gluc_var = StringVar(value="정상")
        gluc_combo = ttk.Combobox(health_frame, textvariable=self.gluc_var, values=["정상", "높음", "매우 높음"], width=10, state="readonly")
        gluc_combo.grid(row=3, column=1, columnspan=2, pady=5, sticky=W)
        
        # 생활습관 체크박스
        lifestyle_frame = Frame(parent, bg=self.colors["white"])
        lifestyle_frame.pack(fill=X, padx=20, pady=10)
        
        self.smoke_var = IntVar()
        self.alco_var = IntVar()
        self.active_var = IntVar(value=1)
        
        Checkbutton(lifestyle_frame, text="흡연", variable=self.smoke_var, bg=self.colors["white"]).pack(side=LEFT, padx=10)
        Checkbutton(lifestyle_frame, text="음주", variable=self.alco_var, bg=self.colors["white"]).pack(side=LEFT, padx=10)
        Checkbutton(lifestyle_frame, text="신체활동", variable=self.active_var, bg=self.colors["white"]).pack(side=LEFT, padx=10)
        
        # 분석 버튼
        analyze_btn = Button(
            parent,
            text="🔍 분석하기",
            font=("맑은 고딕", 12, "bold"),
            bg=self.colors["primary"],
            fg=self.colors["white"],
            activebackground="#2980b9",
            activeforeground=self.colors["white"],
            relief=FLAT,
            cursor="hand2",
            command=self.analyze
        )
        analyze_btn.pack(pady=20, ipadx=30, ipady=8)
    
    def create_input_row(self, parent, label_text, row):
        """입력 행 레이블 생성"""
        Label(
            parent,
            text=label_text,
            font=("맑은 고딕", 11),
            bg=self.colors["white"],
            width=12,
            anchor=E
        ).grid(row=row, column=0, pady=5, padx=(0, 10), sticky=E)
    
    def create_result_panel(self, parent):
        """결과 패널 생성"""
        # 제목
        Label(
            parent,
            text="📊 분석 결과",
            font=("맑은 고딕", 14, "bold"),
            bg=self.colors["white"],
            fg=self.colors["dark"]
        ).pack(pady=(15, 10))
        
        # 결과 표시 영역
        result_frame = Frame(parent, bg=self.colors["white"])
        result_frame.pack(fill=BOTH, expand=True, padx=15)
        
        # BMI 결과
        self.bmi_frame = self.create_result_card(result_frame, "BMI", "체질량지수")
        self.bmi_frame.pack(fill=X, pady=5)
        
        # 혈압 결과
        self.bp_frame = self.create_result_card(result_frame, "혈압", "혈압 상태")
        self.bp_frame.pack(fill=X, pady=5)
        
        # 위험도 결과
        self.risk_frame = self.create_result_card(result_frame, "위험도", "심혈관 질환 위험도")
        self.risk_frame.pack(fill=X, pady=5)
        
        # 구분선
        ttk.Separator(parent, orient=HORIZONTAL).pack(fill=X, padx=15, pady=10)
        
        # 성별 평균 비교 섹션
        Label(
            parent,
            text="📈 성별 평균 비교",
            font=("맑은 고딕", 12, "bold"),
            bg=self.colors["white"],
            fg=self.colors["dark"]
        ).pack(anchor=W, padx=15)
        
        self.comparison_frame = Frame(parent, bg=self.colors["light"], relief=GROOVE, bd=1)
        self.comparison_frame.pack(fill=X, padx=15, pady=5)
        
        self.comparison_label = Label(
            self.comparison_frame,
            text="분석 후 성별 평균과 비교 결과가 표시됩니다.",
            font=("맑은 고딕", 9),
            bg=self.colors["light"],
            fg="#7f8c8d",
            justify=LEFT,
            wraplength=350
        )
        self.comparison_label.pack(padx=10, pady=10, anchor=W)
        
        # 구분선
        ttk.Separator(parent, orient=HORIZONTAL).pack(fill=X, padx=15, pady=5)
        
        # 건강 조언
        Label(
            parent,
            text="💬 건강 조언",
            font=("맑은 고딕", 12, "bold"),
            bg=self.colors["white"],
            fg=self.colors["dark"]
        ).pack(anchor=W, padx=15)
        
        self.advice_text = Text(
            parent,
            height=5,
            font=("맑은 고딕", 10),
            bg=self.colors["light"],
            relief=FLAT,
            wrap=WORD,
            state=DISABLED
        )
        self.advice_text.pack(fill=X, padx=15, pady=10)
    
    def create_result_card(self, parent, title, subtitle):
        """결과 카드 위젯 생성"""
        card = Frame(parent, bg=self.colors["light"], relief=GROOVE, bd=1)
        
        # 헤더
        header = Frame(card, bg=self.colors["light"])
        header.pack(fill=X, padx=10, pady=(10, 5))
        
        Label(
            header,
            text=title,
            font=("맑은 고딕", 11, "bold"),
            bg=self.colors["light"]
        ).pack(side=LEFT)
        
        # 상태 라벨 (동적으로 업데이트)
        status_label = Label(
            header,
            text="--",
            font=("맑은 고딕", 11, "bold"),
            bg=self.colors["light"],
            fg=self.colors["dark"]
        )
        status_label.pack(side=RIGHT)
        card.status_label = status_label
        
        # 값 표시
        value_label = Label(
            card,
            text="분석 대기 중...",
            font=("맑은 고딕", 10),
            bg=self.colors["light"],
            fg="#7f8c8d"
        )
        value_label.pack(anchor=W, padx=10, pady=(0, 10))
        card.value_label = value_label
        
        return card
    
    def create_bottom_buttons(self):
        """하단 버튼 생성"""
        btn_frame = Frame(self.window, bg=self.colors["bg"])
        btn_frame.pack(fill=X, padx=20, pady=15)
        
        buttons = [
            ("💾 기록 저장", self.save_record, self.colors["success"]),
            ("📋 기록 조회", self.show_history, self.colors["primary"]),
            ("📊 통계 보기", self.show_statistics, self.colors["warning"]),
            ("🔄 초기화", self.reset, "#95a5a6")
        ]
        
        for text, command, color in buttons:
            btn = Button(
                btn_frame,
                text=text,
                font=("맑은 고딕", 10),
                bg=color,
                fg=self.colors["white"],
                activebackground=color,
                activeforeground=self.colors["white"],
                relief=FLAT,
                cursor="hand2",
                command=command
            )
            btn.pack(side=LEFT, padx=5, ipadx=15, ipady=5)
    
    def get_chol_value(self):
        """콜레스테롤 텍스트를 숫자로 변환"""
        mapping = {"정상": 1, "높음": 2, "매우 높음": 3}
        return mapping.get(self.chol_var.get(), 1)
    
    def get_gluc_value(self):
        """혈당 텍스트를 숫자로 변환"""
        mapping = {"정상": 1, "높음": 2, "매우 높음": 3}
        return mapping.get(self.gluc_var.get(), 1)
    
    def validate_inputs(self):
        """입력값 검증"""
        try:
            age = int(self.age_entry.get())
            height = int(self.height_entry.get())
            weight = float(self.weight_entry.get())
            ap_hi = int(self.ap_hi_entry.get())
            ap_lo = int(self.ap_lo_entry.get())
            
            if age < 1 or age > 120:
                raise ValueError("나이는 1~120 사이여야 합니다.")
            if height < 50 or height > 250:
                raise ValueError("키는 50~250 사이여야 합니다.")
            if weight < 20 or weight > 300:
                raise ValueError("몸무게는 20~300 사이여야 합니다.")
            if ap_hi < 50 or ap_hi > 250:
                raise ValueError("수축기 혈압은 50~250 사이여야 합니다.")
            if ap_lo < 30 or ap_lo > 150:
                raise ValueError("이완기 혈압은 30~150 사이여야 합니다.")
            
            return True
        except ValueError as e:
            messagebox.showerror("입력 오류", f"올바른 값을 입력하세요.\n{e}")
            return False
    
    def analyze(self):
        """건강 분석 실행"""
        if not self.validate_inputs():
            return
        
        # HealthChecker 인스턴스 생성
        checker = HealthChecker(
            age=int(self.age_entry.get()),
            gender=self.gender_var.get(),
            height=int(self.height_entry.get()),
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
        
        # 성별 평균 비교
        user_data = checker.to_dict()
        gender = self.gender_var.get()
        comparison = self.data_manager.compare_with_gender_average(user_data, gender)
        
        if comparison:
            comparison_text = f"📊 {gender} 평균 대비 (샘플 {comparison['sample_count']}명)\n\n"
            
            # BMI 비교
            bmi_comp = comparison["bmi"]
            bmi_icon = "🔴" if bmi_comp["status"] == "higher" and bmi_comp["diff"] > 2 else "🟢" if bmi_comp["status"] == "lower" else "🟡"
            comparison_text += f"{bmi_icon} BMI: {bmi_comp['user']} (평균 {bmi_comp['avg']}) → {bmi_comp['text']}\n"
            
            # 키 비교
            height_comp = comparison["height"]
            comparison_text += f"📏 키: {height_comp['user']}cm (평균 {height_comp['avg']}cm) → {height_comp['text']}\n"
            
            # 몸무게 비교
            weight_comp = comparison["weight"]
            weight_icon = "🔴" if weight_comp["status"] == "higher" and weight_comp["diff"] > 5 else "🟢" if weight_comp["status"] == "lower" else "🟡"
            comparison_text += f"{weight_icon} 몸무게: {weight_comp['user']}kg (평균 {weight_comp['avg']}kg) → {weight_comp['text']}\n"
            
            # 혈압 비교
            bp_comp = comparison["ap_hi"]
            bp_icon = "🔴" if bp_comp["status"] == "higher" and bp_comp["diff"] > 10 else "🟢" if bp_comp["status"] == "lower" else "🟡"
            comparison_text += f"{bp_icon} 수축기 혈압: {bp_comp['user']}mmHg (평균 {bp_comp['avg']}mmHg) → {bp_comp['text']}\n"
            
            # 심혈관 질환 비율 정보
            comparison_text += f"\n⚠️ {gender} 심혈관 질환 비율: {comparison['cardio_rate']}%"
            
            self.comparison_label.config(text=comparison_text, fg=self.colors["dark"])
        
        # 건강 조언
        advice_list = checker.get_health_advice()
        self.advice_text.config(state=NORMAL)
        self.advice_text.delete(1.0, END)
        for advice in advice_list:
            self.advice_text.insert(END, f"• {advice}\n")
        self.advice_text.config(state=DISABLED)
        
        # 현재 체커 저장 (기록용)
        self.current_checker = checker
    
    def save_record(self):
        """현재 분석 결과 저장"""
        name = self.name_entry.get().strip()
        
        if not name:
            messagebox.showwarning("입력 필요", "이름을 입력하세요.")
            return
        
        if not hasattr(self, "current_checker"):
            messagebox.showwarning("분석 필요", "먼저 '분석하기'를 실행하세요.")
            return
        
        data = self.current_checker.to_dict()
        
        if self.data_manager.save_record(name, data):
            messagebox.showinfo("저장 완료", f"{name}님의 건강 기록이 저장되었습니다.")
        else:
            messagebox.showerror("저장 실패", "기록 저장에 실패했습니다.")
    
    def show_history(self):
        """기록 조회 팝업"""
        records = self.data_manager.load_records()
        
        if not records:
            messagebox.showinfo("기록 없음", "저장된 기록이 없습니다.")
            return
        
        # 팝업 창
        popup = Toplevel(self.window)
        popup.title("📋 기록 조회")
        popup.geometry("700x400")
        popup.resizable(False, False)
        
        # 트리뷰
        columns = ("날짜", "이름", "나이", "BMI", "혈압", "위험도")
        tree = ttk.Treeview(popup, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor=CENTER)
        
        tree.column("날짜", width=150)
        
        for record in records:
            tree.insert("", END, values=(
                record.get("date", ""),
                record.get("name", ""),
                record.get("age", ""),
                record.get("bmi", ""),
                f"{record.get('ap_hi', '')}/{record.get('ap_lo', '')}",
                record.get("risk_score", "")
            ))
        
        tree.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(popup, orient=VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
    
    def show_statistics(self):
        """통계 팝업 - 성별별 비교"""
        gender_stats = self.data_manager.get_gender_statistics()
        
        if not gender_stats or not gender_stats["total"]:
            messagebox.showinfo("통계 없음", "샘플 데이터가 없습니다.")
            return
        
        # 팝업 창
        popup = Toplevel(self.window)
        popup.title("📊 Kaggle 데이터 성별 통계")
        popup.geometry("650x450")
        popup.resizable(False, False)
        popup.configure(bg=self.colors["white"])
        
        Label(
            popup,
            text="📊 Kaggle 심혈관 데이터 - 성별별 통계",
            font=("맑은 고딕", 14, "bold"),
            bg=self.colors["white"]
        ).pack(pady=15)
        
        # 테이블 프레임
        table_frame = Frame(popup, bg=self.colors["white"])
        table_frame.pack(fill=BOTH, expand=True, padx=20)
        
        # 헤더
        headers = ["항목", "👨 남성", "👩 여성", "전체"]
        for col, header in enumerate(headers):
            Label(
                table_frame,
                text=header,
                font=("맑은 고딕", 11, "bold"),
                bg=self.colors["primary"] if col > 0 else self.colors["light"],
                fg=self.colors["white"] if col > 0 else self.colors["dark"],
                width=12,
                relief=RIDGE,
                padx=10,
                pady=8
            ).grid(row=0, column=col, sticky="nsew")
        
        # 데이터 항목
        male = gender_stats["male"]
        female = gender_stats["female"]
        total = gender_stats["total"]
        
        stat_items = [
            ("샘플 수", f"{male['total_samples']}명", f"{female['total_samples']}명", f"{total['total_samples']}명"),
            ("평균 나이", f"{male['avg_age']}세", f"{female['avg_age']}세", f"{total['avg_age']}세"),
            ("평균 키", f"{male['avg_height']}cm", f"{female['avg_height']}cm", f"{total['avg_height']}cm"),
            ("평균 몸무게", f"{male['avg_weight']}kg", f"{female['avg_weight']}kg", f"{total['avg_weight']}kg"),
            ("평균 BMI", f"{male['avg_bmi']}", f"{female['avg_bmi']}", f"{total['avg_bmi']}"),
            ("평균 수축기 혈압", f"{male['avg_ap_hi']}mmHg", f"{female['avg_ap_hi']}mmHg", f"{total['avg_ap_hi']}mmHg"),
            ("평균 이완기 혈압", f"{male['avg_ap_lo']}mmHg", f"{female['avg_ap_lo']}mmHg", f"{total['avg_ap_lo']}mmHg"),
            ("심혈관 질환율", f"{male['cardio_rate']}%", f"{female['cardio_rate']}%", f"{total['cardio_rate']}%"),
            ("흡연율", f"{male['smoke_rate']}%", f"{female['smoke_rate']}%", f"{total['smoke_rate']}%"),
            ("고콜레스테롤율", f"{male['high_chol_rate']}%", f"{female['high_chol_rate']}%", f"{total['high_chol_rate']}%"),
        ]
        
        for row, (label, m_val, f_val, t_val) in enumerate(stat_items, start=1):
            # 항목명
            Label(
                table_frame,
                text=label,
                font=("맑은 고딕", 10),
                bg=self.colors["light"],
                width=12,
                relief=RIDGE,
                padx=5,
                pady=5
            ).grid(row=row, column=0, sticky="nsew")
            
            # 남성 값
            Label(
                table_frame,
                text=m_val,
                font=("맑은 고딕", 10),
                bg="#e3f2fd",
                fg=self.colors["dark"],
                width=12,
                relief=RIDGE,
                padx=5,
                pady=5
            ).grid(row=row, column=1, sticky="nsew")
            
            # 여성 값
            Label(
                table_frame,
                text=f_val,
                font=("맑은 고딕", 10),
                bg="#fce4ec",
                fg=self.colors["dark"],
                width=12,
                relief=RIDGE,
                padx=5,
                pady=5
            ).grid(row=row, column=2, sticky="nsew")
            
            # 전체 값
            Label(
                table_frame,
                text=t_val,
                font=("맑은 고딕", 10),
                bg=self.colors["white"],
                fg=self.colors["dark"],
                width=12,
                relief=RIDGE,
                padx=5,
                pady=5
            ).grid(row=row, column=3, sticky="nsew")
        
        # 안내 문구
        Label(
            popup,
            text="💡 분석 시 선택한 성별의 평균값과 비교됩니다.",
            font=("맑은 고딕", 9),
            bg=self.colors["white"],
            fg="#7f8c8d"
        ).pack(pady=10)
    
    def reset(self):
        """입력 폼 초기화"""
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
        
        # 결과 초기화
        self.bmi_frame.status_label.config(text="--", fg=self.colors["dark"])
        self.bmi_frame.value_label.config(text="분석 대기 중...", fg="#7f8c8d")
        
        self.bp_frame.status_label.config(text="--", fg=self.colors["dark"])
        self.bp_frame.value_label.config(text="분석 대기 중...", fg="#7f8c8d")
        
        self.risk_frame.status_label.config(text="--", fg=self.colors["dark"])
        self.risk_frame.value_label.config(text="분석 대기 중...", fg="#7f8c8d")
        
        # 성별 비교 초기화
        self.comparison_label.config(
            text="분석 후 성별 평균과 비교 결과가 표시됩니다.",
            fg="#7f8c8d"
        )
        
        self.advice_text.config(state=NORMAL)
        self.advice_text.delete(1.0, END)
        self.advice_text.config(state=DISABLED)
        
        # 현재 체커 삭제
        if hasattr(self, "current_checker"):
            del self.current_checker
    
    def run(self):
        """애플리케이션 실행"""
        self.window.mainloop()


# 메인 실행
if __name__ == "__main__":
    app = HealthCheckApp()
    app.run()
