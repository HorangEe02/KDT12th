"""
main.py
환자 정보 관리 시스템 - 메인 GUI

Author: KDT12 Python Project
Date: 2026-01-09
데이터 출처: Kaggle - Healthcare Dataset
"""

import os
import sys

# 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tkinter import *
from tkinter import ttk, messagebox
from patient import Patient
from patient_manager import PatientManager


class PatientManagementApp:
    """
    환자 정보 관리 GUI 애플리케이션
    
    CRUD 기능을 제공하는 tkinter 기반 인터페이스
    """
    
    def __init__(self):
        """생성자: GUI 초기화"""
        self.window = Tk()
        self.window.title("🏥 환자 정보 관리 시스템")
        self.window.geometry("1100x700")
        self.window.resizable(True, True)
        self.window.minsize(900, 600)
        
        # 색상 테마
        self.colors = {
            "bg": "#f0f4f8",
            "header": "#1e3a5f",
            "primary": "#3498db",
            "success": "#27ae60",
            "warning": "#f39c12",
            "danger": "#e74c3c",
            "dark": "#2c3e50",
            "light": "#ecf0f1",
            "white": "#ffffff",
            "table_header": "#34495e",
            "table_odd": "#ffffff",
            "table_even": "#f8f9fa"
        }
        
        self.window.configure(bg=self.colors["bg"])
        
        # 데이터 매니저 초기화
        self.manager = PatientManager()
        
        # 위젯 생성
        self.create_widgets()
        
        # 테이블 데이터 로드
        self.refresh_table()
        
        # 키보드 단축키 바인딩
        self.bind_shortcuts()
    
    def create_widgets(self):
        """모든 위젯 생성"""
        # 헤더
        self.create_header()
        
        # 검색바
        self.create_search_bar()
        
        # 테이블
        self.create_table()
        
        # 버튼 영역
        self.create_buttons()
        
        # 상태바
        self.create_status_bar()
    
    def create_header(self):
        """상단 헤더 생성"""
        header = Frame(self.window, bg=self.colors["header"], height=60)
        header.pack(fill=X)
        header.pack_propagate(False)
        
        Label(
            header,
            text="🏥 환자 정보 관리 시스템 (CRUD)",
            font=("맑은 고딕", 18, "bold"),
            fg=self.colors["white"],
            bg=self.colors["header"]
        ).pack(side=LEFT, padx=20)
        
        Label(
            header,
            text="Kaggle Healthcare Dataset 기반",
            font=("맑은 고딕", 10),
            fg=self.colors["light"],
            bg=self.colors["header"]
        ).pack(side=RIGHT, padx=20)
    
    def create_search_bar(self):
        """검색바 생성"""
        search_frame = Frame(self.window, bg=self.colors["bg"], pady=10)
        search_frame.pack(fill=X, padx=20)
        
        Label(
            search_frame,
            text="🔍 검색:",
            font=("맑은 고딕", 11),
            bg=self.colors["bg"]
        ).pack(side=LEFT)
        
        self.search_entry = Entry(
            search_frame,
            font=("맑은 고딕", 11),
            width=30
        )
        self.search_entry.pack(side=LEFT, padx=5)
        self.search_entry.bind("<Return>", lambda e: self.search_patients())
        
        # 검색 필드 선택
        self.search_field = StringVar(value="all")
        field_combo = ttk.Combobox(
            search_frame,
            textvariable=self.search_field,
            values=["all", "name", "medical_condition", "doctor", "hospital"],
            width=15,
            state="readonly"
        )
        field_combo.pack(side=LEFT, padx=5)
        
        Button(
            search_frame,
            text="검색",
            font=("맑은 고딕", 10),
            bg=self.colors["primary"],
            fg=self.colors["white"],
            relief=FLAT,
            cursor="hand2",
            command=self.search_patients
        ).pack(side=LEFT, padx=5, ipadx=10)
        
        Button(
            search_frame,
            text="초기화",
            font=("맑은 고딕", 10),
            bg=self.colors["light"],
            fg=self.colors["dark"],
            relief=FLAT,
            cursor="hand2",
            command=self.reset_search
        ).pack(side=LEFT, padx=5, ipadx=10)
    
    def create_table(self):
        """환자 목록 테이블 생성"""
        table_frame = Frame(self.window, bg=self.colors["bg"])
        table_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
        
        # 스크롤바
        y_scroll = Scrollbar(table_frame, orient=VERTICAL)
        y_scroll.pack(side=RIGHT, fill=Y)
        
        x_scroll = Scrollbar(table_frame, orient=HORIZONTAL)
        x_scroll.pack(side=BOTTOM, fill=X)
        
        # 트리뷰 (테이블)
        columns = (
            "patient_id", "name", "age", "gender", "blood_type",
            "medical_condition", "doctor", "hospital", "room_number",
            "admission_type", "test_results", "billing_amount"
        )
        
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set,
            height=20
        )
        
        y_scroll.config(command=self.tree.yview)
        x_scroll.config(command=self.tree.xview)
        
        # 컬럼 설정
        column_configs = {
            "patient_id": ("ID", 60),
            "name": ("이름", 80),
            "age": ("나이", 50),
            "gender": ("성별", 50),
            "blood_type": ("혈액형", 60),
            "medical_condition": ("진단명", 100),
            "doctor": ("담당의", 100),
            "hospital": ("병원", 120),
            "room_number": ("병실", 50),
            "admission_type": ("입원유형", 80),
            "test_results": ("검사결과", 80),
            "billing_amount": ("청구금액", 100)
        }
        
        for col, (heading, width) in column_configs.items():
            self.tree.heading(col, text=heading, anchor=CENTER)
            self.tree.column(col, width=width, anchor=CENTER)
        
        self.tree.pack(fill=BOTH, expand=True)
        
        # 스타일 설정
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("맑은 고딕", 10, "bold"))
        style.configure("Treeview", font=("맑은 고딕", 10), rowheight=28)
        
        # 더블클릭 이벤트
        self.tree.bind("<Double-1>", lambda e: self.show_detail_dialog())
    
    def create_buttons(self):
        """하단 버튼 영역 생성"""
        btn_frame = Frame(self.window, bg=self.colors["bg"], pady=10)
        btn_frame.pack(fill=X, padx=20)
        
        buttons = [
            ("➕ 환자 등록", self.show_create_dialog, self.colors["success"]),
            ("📝 정보 수정", self.show_update_dialog, self.colors["warning"]),
            ("🗑️ 삭제", self.delete_selected, self.colors["danger"]),
            ("📋 상세보기", self.show_detail_dialog, self.colors["primary"]),
            ("🏥 퇴원처리", self.discharge_patient, "#9b59b6"),
            ("📊 통계", self.show_statistics, self.colors["dark"]),
            ("🔄 새로고침", self.refresh_table, self.colors["light"])
        ]
        
        for text, command, color in buttons:
            fg = self.colors["dark"] if color == self.colors["light"] else self.colors["white"]
            Button(
                btn_frame,
                text=text,
                font=("맑은 고딕", 10),
                bg=color,
                fg=fg,
                activebackground=color,
                activeforeground=fg,
                relief=FLAT,
                cursor="hand2",
                command=command
            ).pack(side=LEFT, padx=5, ipadx=12, ipady=5)
    
    def create_status_bar(self):
        """상태바 생성"""
        self.status_frame = Frame(self.window, bg=self.colors["header"], height=30)
        self.status_frame.pack(fill=X, side=BOTTOM)
        self.status_frame.pack_propagate(False)
        
        self.status_label = Label(
            self.status_frame,
            text="",
            font=("맑은 고딕", 9),
            fg=self.colors["light"],
            bg=self.colors["header"]
        )
        self.status_label.pack(side=LEFT, padx=20)
        
        self.update_status_bar()
    
    def update_status_bar(self):
        """상태바 업데이트"""
        total = len(self.manager.patients)
        hospitalized = sum(1 for p in self.manager.patients if p.is_hospitalized())
        today = self.manager.get_today_admissions()
        
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M:%S")
        
        self.status_label.config(
            text=f"총 환자: {total}명 | 입원 중: {hospitalized}명 | 오늘 입원: {today}명 | 마지막 업데이트: {current_time}"
        )
    
    def bind_shortcuts(self):
        """키보드 단축키 바인딩"""
        self.window.bind("<Control-n>", lambda e: self.show_create_dialog())
        self.window.bind("<Control-f>", lambda e: self.search_entry.focus())
        self.window.bind("<Control-e>", lambda e: self.show_update_dialog())
        self.window.bind("<Delete>", lambda e: self.delete_selected())
        self.window.bind("<F5>", lambda e: self.refresh_table())
    
    # ==================== 테이블 관련 메서드 ====================
    
    def refresh_table(self, patients=None):
        """테이블 데이터 새로고침"""
        # 기존 데이터 삭제
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 데이터 로드
        if patients is None:
            self.manager.load_from_file()
            patients = self.manager.read_all()
        
        # 데이터 삽입
        for patient in patients:
            values = (
                patient.patient_id,
                patient.name,
                patient.age,
                patient.get_gender_korean(),
                patient.blood_type,
                patient.medical_condition,
                patient.doctor,
                patient.hospital,
                patient.room_number if patient.room_number else "-",
                patient.get_admission_type_korean(),
                patient.get_test_results_korean(),
                patient.get_billing_formatted()
            )
            self.tree.insert("", END, values=values)
        
        self.update_status_bar()
    
    def get_selected_patient_id(self):
        """선택된 환자 ID 반환"""
        selected = self.tree.selection()
        if not selected:
            return None
        item = self.tree.item(selected[0])
        return item["values"][0]
    
    def search_patients(self):
        """환자 검색"""
        keyword = self.search_entry.get().strip()
        field = self.search_field.get()
        
        if not keyword:
            self.refresh_table()
            return
        
        results = self.manager.search(keyword, field)
        self.refresh_table(results)
        
        messagebox.showinfo("검색 결과", f"{len(results)}명의 환자를 찾았습니다.")
    
    def reset_search(self):
        """검색 초기화"""
        self.search_entry.delete(0, END)
        self.search_field.set("all")
        self.refresh_table()
    
    # ==================== CRUD 다이얼로그 ====================
    
    def show_create_dialog(self):
        """환자 등록 다이얼로그"""
        dialog = Toplevel(self.window)
        dialog.title("➕ 새 환자 등록")
        dialog.geometry("450x650")
        dialog.resizable(False, False)
        dialog.configure(bg=self.colors["white"])
        dialog.transient(self.window)
        dialog.grab_set()
        
        # 제목
        Label(
            dialog,
            text="➕ 새 환자 등록",
            font=("맑은 고딕", 14, "bold"),
            bg=self.colors["white"]
        ).pack(pady=15)
        
        # 폼 프레임
        form_frame = Frame(dialog, bg=self.colors["white"])
        form_frame.pack(fill=X, padx=30)
        
        # 입력 필드들
        entries = {}
        
        # 기본 정보
        Label(form_frame, text="─── 기본 정보 ───", font=("맑은 고딕", 10, "bold"), bg=self.colors["white"]).grid(row=0, column=0, columnspan=2, pady=(10, 5), sticky=W)
        
        fields_basic = [
            ("이름:", "name", Entry),
            ("나이:", "age", Entry),
        ]
        
        for i, (label, key, widget_type) in enumerate(fields_basic, start=1):
            Label(form_frame, text=label, font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=i, column=0, pady=5, sticky=E, padx=(0, 10))
            entry = widget_type(form_frame, font=("맑은 고딕", 10), width=25)
            entry.grid(row=i, column=1, pady=5, sticky=W)
            entries[key] = entry
        
        # 성별
        Label(form_frame, text="성별:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=3, column=0, pady=5, sticky=E, padx=(0, 10))
        gender_var = StringVar(value="Male")
        gender_frame = Frame(form_frame, bg=self.colors["white"])
        gender_frame.grid(row=3, column=1, pady=5, sticky=W)
        Radiobutton(gender_frame, text="남성", variable=gender_var, value="Male", bg=self.colors["white"]).pack(side=LEFT)
        Radiobutton(gender_frame, text="여성", variable=gender_var, value="Female", bg=self.colors["white"]).pack(side=LEFT)
        entries["gender"] = gender_var
        
        # 혈액형
        Label(form_frame, text="혈액형:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=4, column=0, pady=5, sticky=E, padx=(0, 10))
        blood_var = StringVar(value="A+")
        blood_combo = ttk.Combobox(form_frame, textvariable=blood_var, values=Patient.VALID_BLOOD_TYPES, width=22, state="readonly")
        blood_combo.grid(row=4, column=1, pady=5, sticky=W)
        entries["blood_type"] = blood_var
        
        # 의료 정보
        Label(form_frame, text="─── 의료 정보 ───", font=("맑은 고딕", 10, "bold"), bg=self.colors["white"]).grid(row=5, column=0, columnspan=2, pady=(15, 5), sticky=W)
        
        # 진단명
        Label(form_frame, text="진단명:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=6, column=0, pady=5, sticky=E, padx=(0, 10))
        condition_var = StringVar(value="Diabetes")
        condition_combo = ttk.Combobox(form_frame, textvariable=condition_var, values=Patient.VALID_CONDITIONS, width=22, state="readonly")
        condition_combo.grid(row=6, column=1, pady=5, sticky=W)
        entries["medical_condition"] = condition_var
        
        fields_medical = [
            ("담당의:", "doctor"),
            ("병원:", "hospital"),
            ("병실:", "room_number"),
        ]
        
        for i, (label, key) in enumerate(fields_medical, start=7):
            Label(form_frame, text=label, font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=i, column=0, pady=5, sticky=E, padx=(0, 10))
            entry = Entry(form_frame, font=("맑은 고딕", 10), width=25)
            entry.grid(row=i, column=1, pady=5, sticky=W)
            entries[key] = entry
        
        # 입원유형
        Label(form_frame, text="입원유형:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=10, column=0, pady=5, sticky=E, padx=(0, 10))
        admission_var = StringVar(value="Elective")
        admission_combo = ttk.Combobox(form_frame, textvariable=admission_var, values=Patient.VALID_ADMISSION_TYPES, width=22, state="readonly")
        admission_combo.grid(row=10, column=1, pady=5, sticky=W)
        entries["admission_type"] = admission_var
        
        # 기타 정보
        Label(form_frame, text="─── 기타 정보 ───", font=("맑은 고딕", 10, "bold"), bg=self.colors["white"]).grid(row=11, column=0, columnspan=2, pady=(15, 5), sticky=W)
        
        fields_other = [
            ("보험사:", "insurance_provider"),
            ("처방약:", "medication"),
            ("청구금액:", "billing_amount"),
        ]
        
        for i, (label, key) in enumerate(fields_other, start=12):
            Label(form_frame, text=label, font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=i, column=0, pady=5, sticky=E, padx=(0, 10))
            entry = Entry(form_frame, font=("맑은 고딕", 10), width=25)
            entry.grid(row=i, column=1, pady=5, sticky=W)
            entries[key] = entry
        
        # 검사결과
        Label(form_frame, text="검사결과:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=15, column=0, pady=5, sticky=E, padx=(0, 10))
        test_var = StringVar(value="Normal")
        test_combo = ttk.Combobox(form_frame, textvariable=test_var, values=Patient.VALID_TEST_RESULTS, width=22, state="readonly")
        test_combo.grid(row=15, column=1, pady=5, sticky=W)
        entries["test_results"] = test_var
        
        # 버튼
        btn_frame = Frame(dialog, bg=self.colors["white"])
        btn_frame.pack(pady=20)
        
        def save_patient():
            try:
                data = {
                    "name": entries["name"].get().strip(),
                    "age": int(entries["age"].get()) if entries["age"].get() else 0,
                    "gender": entries["gender"].get(),
                    "blood_type": entries["blood_type"].get(),
                    "medical_condition": entries["medical_condition"].get(),
                    "doctor": entries["doctor"].get().strip(),
                    "hospital": entries["hospital"].get().strip(),
                    "room_number": int(entries["room_number"].get()) if entries["room_number"].get() else 0,
                    "admission_type": entries["admission_type"].get(),
                    "insurance_provider": entries["insurance_provider"].get().strip(),
                    "medication": entries["medication"].get().strip(),
                    "billing_amount": float(entries["billing_amount"].get()) if entries["billing_amount"].get() else 0,
                    "test_results": entries["test_results"].get()
                }
                
                success, result = self.manager.create(data)
                
                if success:
                    messagebox.showinfo("등록 완료", f"환자가 등록되었습니다.\n환자 ID: {result}")
                    dialog.destroy()
                    self.refresh_table()
                else:
                    messagebox.showerror("등록 실패", result)
            except ValueError as e:
                messagebox.showerror("입력 오류", "숫자 필드에 올바른 값을 입력하세요.")
        
        Button(
            btn_frame,
            text="등록",
            font=("맑은 고딕", 11),
            bg=self.colors["success"],
            fg=self.colors["white"],
            relief=FLAT,
            command=save_patient
        ).pack(side=LEFT, padx=10, ipadx=20, ipady=5)
        
        Button(
            btn_frame,
            text="취소",
            font=("맑은 고딕", 11),
            bg=self.colors["light"],
            fg=self.colors["dark"],
            relief=FLAT,
            command=dialog.destroy
        ).pack(side=LEFT, padx=10, ipadx=20, ipady=5)
    
    def show_update_dialog(self):
        """환자 정보 수정 다이얼로그"""
        patient_id = self.get_selected_patient_id()
        if not patient_id:
            messagebox.showwarning("선택 필요", "수정할 환자를 선택하세요.")
            return
        
        patient = self.manager.read_by_id(patient_id)
        if not patient:
            messagebox.showerror("오류", "환자 정보를 찾을 수 없습니다.")
            return
        
        dialog = Toplevel(self.window)
        dialog.title(f"📝 환자 정보 수정 - {patient_id}")
        dialog.geometry("450x650")
        dialog.resizable(False, False)
        dialog.configure(bg=self.colors["white"])
        dialog.transient(self.window)
        dialog.grab_set()
        
        # 제목
        Label(
            dialog,
            text=f"📝 환자 정보 수정 ({patient_id})",
            font=("맑은 고딕", 14, "bold"),
            bg=self.colors["white"]
        ).pack(pady=15)
        
        # 폼 프레임
        form_frame = Frame(dialog, bg=self.colors["white"])
        form_frame.pack(fill=X, padx=30)
        
        entries = {}
        
        # 기본 정보
        Label(form_frame, text="─── 기본 정보 ───", font=("맑은 고딕", 10, "bold"), bg=self.colors["white"]).grid(row=0, column=0, columnspan=2, pady=(10, 5), sticky=W)
        
        # 이름
        Label(form_frame, text="이름:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=1, column=0, pady=5, sticky=E, padx=(0, 10))
        name_entry = Entry(form_frame, font=("맑은 고딕", 10), width=25)
        name_entry.insert(0, patient.name)
        name_entry.grid(row=1, column=1, pady=5, sticky=W)
        entries["name"] = name_entry
        
        # 나이
        Label(form_frame, text="나이:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=2, column=0, pady=5, sticky=E, padx=(0, 10))
        age_entry = Entry(form_frame, font=("맑은 고딕", 10), width=25)
        age_entry.insert(0, str(patient.age))
        age_entry.grid(row=2, column=1, pady=5, sticky=W)
        entries["age"] = age_entry
        
        # 성별
        Label(form_frame, text="성별:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=3, column=0, pady=5, sticky=E, padx=(0, 10))
        gender_var = StringVar(value=patient.gender)
        gender_frame = Frame(form_frame, bg=self.colors["white"])
        gender_frame.grid(row=3, column=1, pady=5, sticky=W)
        Radiobutton(gender_frame, text="남성", variable=gender_var, value="Male", bg=self.colors["white"]).pack(side=LEFT)
        Radiobutton(gender_frame, text="여성", variable=gender_var, value="Female", bg=self.colors["white"]).pack(side=LEFT)
        entries["gender"] = gender_var
        
        # 혈액형
        Label(form_frame, text="혈액형:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=4, column=0, pady=5, sticky=E, padx=(0, 10))
        blood_var = StringVar(value=patient.blood_type)
        blood_combo = ttk.Combobox(form_frame, textvariable=blood_var, values=Patient.VALID_BLOOD_TYPES, width=22, state="readonly")
        blood_combo.grid(row=4, column=1, pady=5, sticky=W)
        entries["blood_type"] = blood_var
        
        # 의료 정보
        Label(form_frame, text="─── 의료 정보 ───", font=("맑은 고딕", 10, "bold"), bg=self.colors["white"]).grid(row=5, column=0, columnspan=2, pady=(15, 5), sticky=W)
        
        # 진단명
        Label(form_frame, text="진단명:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=6, column=0, pady=5, sticky=E, padx=(0, 10))
        condition_var = StringVar(value=patient.medical_condition)
        condition_combo = ttk.Combobox(form_frame, textvariable=condition_var, values=Patient.VALID_CONDITIONS, width=22, state="readonly")
        condition_combo.grid(row=6, column=1, pady=5, sticky=W)
        entries["medical_condition"] = condition_var
        
        # 담당의
        Label(form_frame, text="담당의:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=7, column=0, pady=5, sticky=E, padx=(0, 10))
        doctor_entry = Entry(form_frame, font=("맑은 고딕", 10), width=25)
        doctor_entry.insert(0, patient.doctor)
        doctor_entry.grid(row=7, column=1, pady=5, sticky=W)
        entries["doctor"] = doctor_entry
        
        # 병원
        Label(form_frame, text="병원:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=8, column=0, pady=5, sticky=E, padx=(0, 10))
        hospital_entry = Entry(form_frame, font=("맑은 고딕", 10), width=25)
        hospital_entry.insert(0, patient.hospital)
        hospital_entry.grid(row=8, column=1, pady=5, sticky=W)
        entries["hospital"] = hospital_entry
        
        # 병실
        Label(form_frame, text="병실:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=9, column=0, pady=5, sticky=E, padx=(0, 10))
        room_entry = Entry(form_frame, font=("맑은 고딕", 10), width=25)
        room_entry.insert(0, str(patient.room_number) if patient.room_number else "")
        room_entry.grid(row=9, column=1, pady=5, sticky=W)
        entries["room_number"] = room_entry
        
        # 처방약
        Label(form_frame, text="처방약:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=10, column=0, pady=5, sticky=E, padx=(0, 10))
        med_entry = Entry(form_frame, font=("맑은 고딕", 10), width=25)
        med_entry.insert(0, patient.medication)
        med_entry.grid(row=10, column=1, pady=5, sticky=W)
        entries["medication"] = med_entry
        
        # 검사결과
        Label(form_frame, text="검사결과:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=11, column=0, pady=5, sticky=E, padx=(0, 10))
        test_var = StringVar(value=patient.test_results)
        test_combo = ttk.Combobox(form_frame, textvariable=test_var, values=Patient.VALID_TEST_RESULTS, width=22, state="readonly")
        test_combo.grid(row=11, column=1, pady=5, sticky=W)
        entries["test_results"] = test_var
        
        # 기타 정보
        Label(form_frame, text="─── 기타 정보 ───", font=("맑은 고딕", 10, "bold"), bg=self.colors["white"]).grid(row=12, column=0, columnspan=2, pady=(15, 5), sticky=W)
        
        # 보험사
        Label(form_frame, text="보험사:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=13, column=0, pady=5, sticky=E, padx=(0, 10))
        insurance_entry = Entry(form_frame, font=("맑은 고딕", 10), width=25)
        insurance_entry.insert(0, patient.insurance_provider)
        insurance_entry.grid(row=13, column=1, pady=5, sticky=W)
        entries["insurance_provider"] = insurance_entry
        
        # 청구금액
        Label(form_frame, text="청구금액:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=14, column=0, pady=5, sticky=E, padx=(0, 10))
        billing_entry = Entry(form_frame, font=("맑은 고딕", 10), width=25)
        billing_entry.insert(0, str(int(patient.billing_amount)))
        billing_entry.grid(row=14, column=1, pady=5, sticky=W)
        entries["billing_amount"] = billing_entry
        
        # 버튼
        btn_frame = Frame(dialog, bg=self.colors["white"])
        btn_frame.pack(pady=20)
        
        def update_patient():
            try:
                data = {
                    "name": entries["name"].get().strip(),
                    "age": int(entries["age"].get()) if entries["age"].get() else 0,
                    "gender": entries["gender"].get(),
                    "blood_type": entries["blood_type"].get(),
                    "medical_condition": entries["medical_condition"].get(),
                    "doctor": entries["doctor"].get().strip(),
                    "hospital": entries["hospital"].get().strip(),
                    "room_number": int(entries["room_number"].get()) if entries["room_number"].get() else 0,
                    "medication": entries["medication"].get().strip(),
                    "test_results": entries["test_results"].get(),
                    "insurance_provider": entries["insurance_provider"].get().strip(),
                    "billing_amount": float(entries["billing_amount"].get()) if entries["billing_amount"].get() else 0
                }
                
                success, msg = self.manager.update(patient_id, data)
                
                if success:
                    messagebox.showinfo("수정 완료", msg)
                    dialog.destroy()
                    self.refresh_table()
                else:
                    messagebox.showerror("수정 실패", msg)
            except ValueError as e:
                messagebox.showerror("입력 오류", "숫자 필드에 올바른 값을 입력하세요.")
        
        Button(
            btn_frame,
            text="수정",
            font=("맑은 고딕", 11),
            bg=self.colors["warning"],
            fg=self.colors["white"],
            relief=FLAT,
            command=update_patient
        ).pack(side=LEFT, padx=10, ipadx=20, ipady=5)
        
        Button(
            btn_frame,
            text="취소",
            font=("맑은 고딕", 11),
            bg=self.colors["light"],
            fg=self.colors["dark"],
            relief=FLAT,
            command=dialog.destroy
        ).pack(side=LEFT, padx=10, ipadx=20, ipady=5)
    
    def show_detail_dialog(self):
        """환자 상세 정보 다이얼로그"""
        patient_id = self.get_selected_patient_id()
        if not patient_id:
            messagebox.showwarning("선택 필요", "조회할 환자를 선택하세요.")
            return
        
        patient = self.manager.read_by_id(patient_id)
        if not patient:
            messagebox.showerror("오류", "환자 정보를 찾을 수 없습니다.")
            return
        
        dialog = Toplevel(self.window)
        dialog.title(f"📋 환자 상세 정보 - {patient_id}")
        dialog.geometry("400x550")
        dialog.resizable(False, False)
        dialog.configure(bg=self.colors["white"])
        dialog.transient(self.window)
        
        # 환자 기본 정보 헤더
        header_frame = Frame(dialog, bg=self.colors["primary"], pady=15)
        header_frame.pack(fill=X)
        
        status_icon = "🏥" if patient.is_hospitalized() else "✅"
        status_text = "입원중" if patient.is_hospitalized() else "퇴원"
        
        Label(
            header_frame,
            text=f"👤 {patient.name} ({patient.age}세, {patient.get_gender_korean()})",
            font=("맑은 고딕", 14, "bold"),
            fg=self.colors["white"],
            bg=self.colors["primary"]
        ).pack()
        
        Label(
            header_frame,
            text=f"혈액형: {patient.blood_type} | {status_icon} {status_text}",
            font=("맑은 고딕", 10),
            fg=self.colors["light"],
            bg=self.colors["primary"]
        ).pack()
        
        # 상세 정보
        info_frame = Frame(dialog, bg=self.colors["white"])
        info_frame.pack(fill=BOTH, expand=True, padx=20, pady=15)
        
        sections = [
            ("📅 입원 정보", [
                ("입원일", patient.date_of_admission),
                ("퇴원일", patient.discharge_date if patient.discharge_date else "-"),
                ("입원유형", patient.get_admission_type_korean()),
                ("병실", f"{patient.room_number}호" if patient.room_number else "-")
            ]),
            ("🩺 의료 정보", [
                ("진단명", f"{patient.get_condition_korean()} ({patient.medical_condition})"),
                ("담당의", patient.doctor),
                ("병원", patient.hospital),
                ("처방약", patient.medication if patient.medication else "-"),
                ("검사결과", patient.get_test_results_korean())
            ]),
            ("💰 비용 정보", [
                ("보험사", patient.insurance_provider if patient.insurance_provider else "-"),
                ("청구금액", patient.get_billing_formatted())
            ])
        ]
        
        for section_title, items in sections:
            Label(
                info_frame,
                text=section_title,
                font=("맑은 고딕", 11, "bold"),
                bg=self.colors["white"],
                fg=self.colors["dark"]
            ).pack(anchor=W, pady=(10, 5))
            
            for label, value in items:
                row_frame = Frame(info_frame, bg=self.colors["light"])
                row_frame.pack(fill=X, pady=2)
                
                Label(
                    row_frame,
                    text=f"  {label}:",
                    font=("맑은 고딕", 10),
                    bg=self.colors["light"],
                    width=12,
                    anchor=E
                ).pack(side=LEFT)
                
                Label(
                    row_frame,
                    text=f"  {value}",
                    font=("맑은 고딕", 10),
                    bg=self.colors["light"],
                    anchor=W
                ).pack(side=LEFT, fill=X, expand=True)
        
        # 버튼
        btn_frame = Frame(dialog, bg=self.colors["white"])
        btn_frame.pack(pady=15)
        
        Button(
            btn_frame,
            text="수정",
            font=("맑은 고딕", 10),
            bg=self.colors["warning"],
            fg=self.colors["white"],
            relief=FLAT,
            command=lambda: [dialog.destroy(), self.show_update_dialog()]
        ).pack(side=LEFT, padx=5, ipadx=15)
        
        Button(
            btn_frame,
            text="닫기",
            font=("맑은 고딕", 10),
            bg=self.colors["light"],
            fg=self.colors["dark"],
            relief=FLAT,
            command=dialog.destroy
        ).pack(side=LEFT, padx=5, ipadx=15)
    
    def delete_selected(self):
        """선택된 환자 삭제"""
        patient_id = self.get_selected_patient_id()
        if not patient_id:
            messagebox.showwarning("선택 필요", "삭제할 환자를 선택하세요.")
            return
        
        patient = self.manager.read_by_id(patient_id)
        if not patient:
            messagebox.showerror("오류", "환자 정보를 찾을 수 없습니다.")
            return
        
        # 확인 다이얼로그
        confirm = messagebox.askyesno(
            "삭제 확인",
            f"정말 삭제하시겠습니까?\n\n환자: {patient.name} ({patient_id})\n진단: {patient.medical_condition}"
        )
        
        if confirm:
            success, msg = self.manager.delete(patient_id)
            if success:
                messagebox.showinfo("삭제 완료", msg)
                self.refresh_table()
            else:
                messagebox.showerror("삭제 실패", msg)
    
    def discharge_patient(self):
        """환자 퇴원 처리"""
        patient_id = self.get_selected_patient_id()
        if not patient_id:
            messagebox.showwarning("선택 필요", "퇴원 처리할 환자를 선택하세요.")
            return
        
        patient = self.manager.read_by_id(patient_id)
        if not patient:
            messagebox.showerror("오류", "환자 정보를 찾을 수 없습니다.")
            return
        
        if not patient.is_hospitalized():
            messagebox.showinfo("알림", f"{patient.name} 환자는 이미 퇴원했습니다.\n퇴원일: {patient.discharge_date}")
            return
        
        confirm = messagebox.askyesno(
            "퇴원 확인",
            f"{patient.name} 환자를 퇴원 처리하시겠습니까?"
        )
        
        if confirm:
            success, msg = self.manager.discharge_patient(patient_id)
            if success:
                messagebox.showinfo("퇴원 완료", f"{patient.name} 환자가 퇴원 처리되었습니다.")
                self.refresh_table()
            else:
                messagebox.showerror("퇴원 처리 실패", msg)
    
    def show_statistics(self):
        """통계 다이얼로그"""
        stats = self.manager.get_statistics()
        
        if not stats:
            messagebox.showinfo("통계 없음", "환자 데이터가 없습니다.")
            return
        
        dialog = Toplevel(self.window)
        dialog.title("📊 환자 통계")
        dialog.geometry("500x550")
        dialog.resizable(False, False)
        dialog.configure(bg=self.colors["white"])
        dialog.transient(self.window)
        
        # 제목
        Label(
            dialog,
            text="📊 환자 통계 현황",
            font=("맑은 고딕", 14, "bold"),
            bg=self.colors["white"]
        ).pack(pady=15)
        
        # 통계 프레임
        stats_frame = Frame(dialog, bg=self.colors["white"])
        stats_frame.pack(fill=BOTH, expand=True, padx=20)
        
        # 기본 통계
        Label(stats_frame, text="─── 기본 통계 ───", font=("맑은 고딕", 11, "bold"), bg=self.colors["white"]).pack(anchor=W, pady=(10, 5))
        
        basic_stats = [
            ("총 환자 수", f"{stats['total_patients']}명"),
            ("남성", f"{stats['male_count']}명 ({stats['male_ratio']}%)"),
            ("여성", f"{stats['female_count']}명 ({stats['female_ratio']}%)"),
            ("평균 나이", f"{stats['avg_age']}세"),
            ("입원 중", f"{stats['hospitalized_count']}명"),
            ("퇴원", f"{stats['discharged_count']}명"),
        ]
        
        for label, value in basic_stats:
            row = Frame(stats_frame, bg=self.colors["light"])
            row.pack(fill=X, pady=2)
            Label(row, text=label, font=("맑은 고딕", 10), bg=self.colors["light"], width=15, anchor=E).pack(side=LEFT)
            Label(row, text=value, font=("맑은 고딕", 10, "bold"), bg=self.colors["light"], fg=self.colors["primary"]).pack(side=LEFT, padx=10)
        
        # 진단명별 통계
        Label(stats_frame, text="─── 진단명별 분포 ───", font=("맑은 고딕", 11, "bold"), bg=self.colors["white"]).pack(anchor=W, pady=(15, 5))
        
        for condition, count in sorted(stats['conditions'].items(), key=lambda x: x[1], reverse=True):
            row = Frame(stats_frame, bg=self.colors["light"])
            row.pack(fill=X, pady=2)
            Label(row, text=condition, font=("맑은 고딕", 10), bg=self.colors["light"], width=15, anchor=E).pack(side=LEFT)
            Label(row, text=f"{count}명", font=("맑은 고딕", 10, "bold"), bg=self.colors["light"], fg=self.colors["dark"]).pack(side=LEFT, padx=10)
        
        # 금액 통계
        Label(stats_frame, text="─── 비용 통계 ───", font=("맑은 고딕", 11, "bold"), bg=self.colors["white"]).pack(anchor=W, pady=(15, 5))
        
        billing_stats = [
            ("평균 청구금액", f"₩{stats['avg_billing']:,.0f}"),
            ("총 청구금액", f"₩{stats['total_billing']:,.0f}"),
        ]
        
        for label, value in billing_stats:
            row = Frame(stats_frame, bg=self.colors["light"])
            row.pack(fill=X, pady=2)
            Label(row, text=label, font=("맑은 고딕", 10), bg=self.colors["light"], width=15, anchor=E).pack(side=LEFT)
            Label(row, text=value, font=("맑은 고딕", 10, "bold"), bg=self.colors["light"], fg=self.colors["success"]).pack(side=LEFT, padx=10)
        
        # 닫기 버튼
        Button(
            dialog,
            text="닫기",
            font=("맑은 고딕", 10),
            bg=self.colors["light"],
            fg=self.colors["dark"],
            relief=FLAT,
            command=dialog.destroy
        ).pack(pady=15, ipadx=20)
    
    def run(self):
        """애플리케이션 실행"""
        self.window.mainloop()


# 메인 실행
if __name__ == "__main__":
    app = PatientManagementApp()
    app.run()
